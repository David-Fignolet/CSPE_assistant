import PyPDF2
import io
import re
from typing import Dict, List, Tuple
from datetime import datetime

class DocumentProcessor:
    def __init__(self):
        # Mode démo : OCR désactivé pour éviter les dépendances complexes
        self.ocr_enabled = False
        print("ℹ️ Mode démo : OCR désactivé. Traitement PDF uniquement.")

    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extrait le texte d'un fichier PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            print(f"Erreur lors de l'extraction PDF: {str(e)}")
            return ""

    def extract_text_from_image(self, file_content: bytes) -> str:
        """Simulation d'extraction OCR pour la démo"""
        # Pour la démo, retourner un texte d'exemple CSPE réaliste
        return """
CONSEIL D'ÉTAT
Contentieux administratif

REQUÊTE EN ANNULATION

Objet : Contestation décision CRE n° 2024-0156 relative à la CSPE

Monsieur le Président du Conseil d'État,

J'ai l'honneur de contester par la présente la décision de la Commission de Régulation de l'Énergie 
en date du 15 mars 2024, enregistrée sous le numéro CRE-2024-0156, concernant l'application de la 
Contribution au Service Public de l'Électricité (CSPE) sur ma facture d'électricité.

IDENTIFICATION DU DEMANDEUR :
- Nom : MARTIN Jean-Pierre
- Qualité : Consommateur final d'électricité  
- Adresse : 15 rue de la République, 75011 Paris
- N° de contrat EDF : 17429856234
- Numéro de facture contestée : FAC-2024-03-001547

OBJET DE LA CONTESTATION :
La décision attaquée impose une CSPE d'un montant de 1 247,50 € sur ma consommation électrique 
annuelle, soit une augmentation de 34% par rapport à l'année précédente, sans justification claire.

DÉLAI DE RECOURS :
La présente requête est formée le 12 avril 2024, soit 28 jours après notification de la décision 
le 15 mars 2024, dans le respect du délai de recours de deux mois prévu par l'article R. 421-1 
du code de justice administrative.

MOYENS INVOQUÉS :
1. Erreur de calcul dans l'application du tarif CSPE
2. Non-respect de la procédure de notification préalable
3. Violation du principe de proportionnalité

PIÈCES JOINTES :
- Pièce n°1 : Copie de la décision contestée du 15 mars 2024
- Pièce n°2 : Facture d'électricité complète avec détail CSPE
- Pièce n°3 : Relevé de compteur certifié
- Pièce n°4 : Justificatif de domicile (taxe foncière 2023)
- Pièce n°5 : Correspondance préalable avec la CRE

Par ces motifs, je sollicite respectueusement l'annulation de la décision attaquée et la 
restitution des sommes indûment perçues.

Je demeure à votre disposition pour tout complément d'information.

Fait à Paris, le 12 avril 2024

Jean-Pierre MARTIN
[Signature]
        """

    def extract_text_from_file(self, file) -> str:
        """Extrait le texte d'un fichier selon son type"""
        if not file:
            return ""
        
        if hasattr(file, 'type'):
            # Streamlit file object
            if file.type == 'application/pdf':
                return self.extract_text_from_pdf(file.getvalue())
            elif file.type in ['image/png', 'image/jpeg', 'image/jpg']:
                # Mode démo : retourner texte d'exemple pour les images
                print("ℹ️ Mode démo : Utilisation d'un exemple de document CSPE pour les images")
                return self.extract_text_from_image(file.getvalue())
            elif file.type == 'text/plain':
                # Support des fichiers texte
                return file.getvalue().decode('utf-8')
            else:
                return f"Format {file.type} non supporté en mode démo. Utilisez PDF avec texte."
        else:
            # File path (pour les tests)
            if file.endswith('.pdf'):
                with open(file, 'rb') as f:
                    return self.extract_text_from_pdf(f.read())
            elif file.lower().endswith(('.png', '.jpg', '.jpeg')):
                # Mode démo : retourner texte d'exemple
                print("ℹ️ Mode démo : Utilisation d'un exemple de document CSPE pour les images")
                return self.extract_text_from_image(b"")
            elif file.endswith('.txt'):
                with open(file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return "Format non supporté"

    def extract_date(self, text: str) -> datetime:
        """Extrait une date du texte"""
        # Patterns pour dates françaises
        date_patterns = [
            r'(\d{1,2})\s+(\w+)\s+(\d{4})',  # 15 mars 2024
            r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})',  # 15/03/2024 ou 15-03-2024
            r'(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})',  # 2024/03/15 ou 2024-03-15
        ]
        
        # Mapping des mois français
        months_fr = {
            'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6,
            'juillet': 7, 'août': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
        }
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        if groups[1].isdigit():  # Format numérique
                            if len(groups[0]) == 4:  # YYYY/MM/DD
                                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                            else:  # DD/MM/YYYY
                                day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                        else:  # Format avec nom de mois
                            day = int(groups[0])
                            month_name = groups[1].lower()
                            year = int(groups[2])
                            month = months_fr.get(month_name, 1)
                        
                        return datetime(year, month, day)
                except (ValueError, KeyError):
                    continue
        
        # Fallback : date actuelle
        return datetime.now()

    def check_period(self, text: str) -> dict:
        """Vérifie si la période CSPE est couverte (2009-2015)"""
        # Recherche de période dans le texte
        period_patterns = [
            r'période\s+(\d{4})\s*[-à]\s*(\d{4})',
            r'(\d{4})\s*[-à]\s*(\d{4})',
            r'années?\s+(\d{4})',
        ]
        
        for pattern in period_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    try:
                        start_year = int(groups[0])
                        end_year = int(groups[1])
                        
                        # Période CSPE couverte : 2009-2015
                        if 2009 <= start_year <= 2015 and 2009 <= end_year <= 2015:
                            return {
                                'status': '✅ Couverte',
                                'details': f'Période couverte : {start_year}-{end_year}'
                            }
                        else:
                            return {
                                'status': '❌ Non couverte',
                                'details': f'Période {start_year}-{end_year} hors couverture (2009-2015)'
                            }
                    except ValueError:
                        continue
                elif len(groups) == 1:
                    try:
                        year = int(groups[0])
                        if 2009 <= year <= 2015:
                            return {
                                'status': '✅ Couverte',
                                'details': f'Année {year} dans la période couverte'
                            }
                        else:
                            return {
                                'status': '❌ Non couverte',
                                'details': f'Année {year} hors période couverte (2009-2015)'
                            }
                    except ValueError:
                        continue
        
        return {
            'status': '⚠️ Indéterminée',
            'details': 'Période non détectée dans le document'
        }

    def check_delay(self, text: str) -> dict:
        """Vérifie le délai de recours (2 mois pour CSPE)"""
        # Recherche des dates de décision et de recours
        decision_patterns = [
            r'décision.{0,50}(\d{1,2}\s+\w+\s+\d{4})',
            r'en date du\s+(\d{1,2}\s+\w+\s+\d{4})',
            r'notification.{0,20}(\d{1,2}\s+\w+\s+\d{4})',
        ]
        
        recours_patterns = [
            r'requête.{0,50}formée.{0,20}(\d{1,2}\s+\w+\s+\d{4})',
            r'présente.{0,20}(\d{1,2}\s+\w+\s+\d{4})',
            r'fait à.{0,50}(\d{1,2}\s+\w+\s+\d{4})',
        ]
        
        decision_date = None
        recours_date = None
        
        # Extraire la date de décision
        for pattern in decision_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                decision_date = self.extract_date(match.group(1))
                break
        
        # Extraire la date de recours
        for pattern in recours_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                recours_date = self.extract_date(match.group(1))
                break
        
        if decision_date and recours_date:
            # Calculer la différence en jours
            delta = recours_date - decision_date
            days_elapsed = delta.days
            
            # Délai légal : 2 mois = 60 jours
            if days_elapsed <= 60:
                return {
                    'status': '✅ Respecté',
                    'details': f'Recours formé {days_elapsed} jours après la décision (≤ 60 jours)',
                    'decision_date': decision_date.strftime('%d/%m/%Y'),
                    'recours_date': recours_date.strftime('%d/%m/%Y'),
                    'days_elapsed': days_elapsed
                }
            else:
                return {
                    'status': '❌ Dépassé',
                    'details': f'Recours formé {days_elapsed} jours après la décision (> 60 jours)',
                    'decision_date': decision_date.strftime('%d/%m/%Y'),
                    'recours_date': recours_date.strftime('%d/%m/%Y'),
                    'days_elapsed': days_elapsed
                }
        else:
            return {
                'status': '⚠️ Indéterminé',
                'details': 'Dates de décision et/ou de recours non détectées clairement',
                'decision_date': decision_date.strftime('%d/%m/%Y') if decision_date else 'Non détectée',
                'recours_date': recours_date.strftime('%d/%m/%Y') if recours_date else 'Non détectée'
            }

    def check_demandeur_quality(self, text: str) -> dict:
        """Vérifie la qualité du demandeur"""
        # Indicateurs de qualité du demandeur
        quality_indicators = [
            r'consommateur\s+(final|d\'électricité)',
            r'client\s+EDF',
            r'abonné',
            r'titulaire\s+du\s+contrat',
            r'propriétaire',
            r'locataire',
            r'gestionnaire',
        ]
        
        # Éléments d'identification
        identification_elements = [
            r'nom\s*:\s*[\w\s\-]+',
            r'adresse\s*:\s*[\w\s\-,]+',
            r'contrat\s+(EDF|n°|numéro)',
            r'facture.{0,20}n°',
        ]
        
        quality_found = False
        identification_found = False
        
        for pattern in quality_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                quality_found = True
                break
        
        for pattern in identification_elements:
            if re.search(pattern, text, re.IGNORECASE):
                identification_found = True
                break
        
        if quality_found and identification_found:
            return {
                'status': '✅ Conforme',
                'details': 'Demandeur identifié et qualifié (consommateur concerné)'
            }
        elif quality_found:
            return {
                'status': '⚠️ Partiel',
                'details': 'Qualité du demandeur indiquée mais identification incomplète'
            }
        elif identification_found:
            return {
                'status': '⚠️ Partiel',
                'details': 'Demandeur identifié mais qualité à vérifier'
            }
        else:
            return {
                'status': '❌ Insuffisant',
                'details': 'Qualité et identification du demandeur non établies'
            }

    def check_pieces_jointes(self, text: str) -> dict:
        """Vérifie la présence des pièces justificatives"""
        # Pièces essentielles pour CSPE
        required_pieces = {
            'décision_contestée': [r'décision.{0,30}contestée', r'copie.{0,20}décision'],
            'facture': [r'facture', r'facture.{0,20}électricité'],
            'relevé_compteur': [r'relevé.{0,20}compteur', r'compteur'],
            'justificatif_domicile': [r'justificatif.{0,20}domicile', r'taxe.{0,20}foncière'],
        }
        
        pieces_found = {}
        total_pieces = 0
        
        # Compter les pièces mentionnées
        pieces_pattern = r'pièce.{0,20}n°\s*\d+'
        total_pieces = len(re.findall(pieces_pattern, text, re.IGNORECASE))
        
        # Vérifier chaque type de pièce
        for piece_type, patterns in required_pieces.items():
            found = False
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    found = True
                    break
            pieces_found[piece_type] = found
        
        # Évaluation globale
        pieces_ok = sum(pieces_found.values())
        total_required = len(required_pieces)
        
        if pieces_ok >= 3:  # Au moins 3 des 4 pièces essentielles
            return {
                'status': '✅ Complètes',
                'details': f'{pieces_ok}/{total_required} pièces essentielles détectées ({total_pieces} pièces au total)',
                'pieces_found': pieces_found
            }
        elif pieces_ok >= 2:
            return {
                'status': '⚠️ Partielles',
                'details': f'{pieces_ok}/{total_required} pièces essentielles détectées - Compléments nécessaires',
                'pieces_found': pieces_found
            }
        else:
            return {
                'status': '❌ Insuffisantes',
                'details': f'Seulement {pieces_ok}/{total_required} pièces essentielles détectées',
                'pieces_found': pieces_found
            }

    def analyze_text(self, text: str) -> dict:
        """Analyse complète du texte selon les 4 critères CSPE"""
        return {
            'period_check': self.check_period(text),
            'delay_check': self.check_delay(text),
            'demandeur_quality': self.check_demandeur_quality(text),
            'pieces_jointes': self.check_pieces_jointes(text),
            'date_extraction': self.extract_date(text),
            'text_length': len(text),
            'contains_cspe': 'CSPE' in text.upper(),
            'contains_cre': 'CRE' in text.upper() or 'Commission de Régulation' in text,
            'contains_conseil_etat': 'Conseil d\'État' in text or 'CONSEIL D\'ÉTAT' in text
        }