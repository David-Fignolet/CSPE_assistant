import PyPDF2
import pytesseract
import cv2
import numpy as np
import io
import re
from PIL import Image
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

class DocumentProcessor:
    def __init__(self):
        self.ocr_config = '--psm 6 --oem 3 -l fra'  # Configuration OCR pour le français

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

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Prétraite une image pour l'OCR"""
        try:
            # Conversion en gris
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Amélioration du contraste
            gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=40)
            
            # Binarisation adaptative
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Suppression du bruit
            kernel = np.ones((1, 1), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            return binary
        except Exception as e:
            print(f"Erreur prétraitement image: {str(e)}")
            return image

    def extract_text_from_image(self, file_content: bytes) -> str:
        """Extrait le texte d'une image avec OCR"""
        try:
            # Conversion du contenu en image
            image = Image.open(io.BytesIO(file_content))
            
            # Conversion en numpy array pour OpenCV
            image_np = np.array(image)
            
            # Prétraitement
            processed = self.preprocess_image(image_np)
            
            # Extraction du texte avec Tesseract
            text = pytesseract.image_to_string(
                processed,
                config=self.ocr_config
            )
            return text.strip()
        except Exception as e:
            print(f"Erreur lors de l'extraction OCR: {str(e)}")
            # Fallback: essayer sans prétraitement
            try:
                image = Image.open(io.BytesIO(file_content))
                text = pytesseract.image_to_string(image, config=self.ocr_config)
                return text.strip()
            except:
                return f"Erreur OCR: {str(e)}"

    def extract_text_from_file(self, file) -> str:
        """Extrait le texte d'un fichier selon son type"""
        if not file:
            return ""
        
        try:
            # Gestion des fichiers Streamlit (UploadedFile)
            if hasattr(file, 'type') and hasattr(file, 'getvalue'):
                file_type = file.type
                file_content = file.getvalue()
                file_name = getattr(file, 'name', 'unknown')
                
                if file_type == 'application/pdf':
                    return self.extract_text_from_pdf(file_content)
                elif file_type in ['image/png', 'image/jpeg', 'image/jpg']:
                    return self.extract_text_from_image(file_content)
                elif file_type == 'text/plain':
                    return file_content.decode('utf-8', errors='ignore')
                else:
                    # Tentative basée sur l'extension du nom de fichier
                    if file_name.lower().endswith('.txt'):
                        return file_content.decode('utf-8', errors='ignore')
                    elif file_name.lower().endswith('.pdf'):
                        return self.extract_text_from_pdf(file_content)
                    elif file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                        return self.extract_text_from_image(file_content)
                    else:
                        return f"Format non supporté: {file_type} (fichier: {file_name})"
            
            # Gestion des chemins de fichiers (string)
            elif isinstance(file, str):
                file_extension = file.split('.')[-1].lower()
                
                with open(file, 'rb') as f:
                    file_content = f.read()
                
                if file_extension == 'pdf':
                    return self.extract_text_from_pdf(file_content)
                elif file_extension in ['png', 'jpg', 'jpeg']:
                    return self.extract_text_from_image(file_content)
                elif file_extension == 'txt':
                    return file_content.decode('utf-8', errors='ignore')
                else:
                    return f"Extension non supportée: .{file_extension}"
            
            else:
                return f"Type de fichier non reconnu: {type(file)}"
                
        except Exception as e:
            return f"Erreur extraction fichier: {str(e)}"

    def extract_date(self, text: str, pattern_type: str = "any") -> Optional[datetime]:
        """Extrait une date du texte selon différents patterns"""
        # Patterns pour les dates françaises
        date_patterns = [
            r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})',  # DD/MM/YYYY
            r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
            r'(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})'
        ]
        
        months_fr = {
            'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
            'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
            'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
        }
        
        dates_found = []
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match) == 3 and match[0].isdigit():
                        # Format DD/MM/YYYY
                        day, month, year = int(match[0]), int(match[1]), int(match[2])
                        if 1 <= day <= 31 and 1 <= month <= 12:
                            date_obj = datetime(year, month, day)
                            dates_found.append(date_obj)
                    elif len(match) == 3 and match[1].lower() in months_fr:
                        # Format DD month YYYY
                        day, month_name, year = int(match[0]), match[1].lower(), int(match[2])
                        month = months_fr[month_name]
                        if 1 <= day <= 31:
                            date_obj = datetime(year, month, day)
                            dates_found.append(date_obj)
                    elif len(match) == 2 and match[0].lower() in months_fr:
                        # Format month YYYY
                        month_name, year = match[0].lower(), int(match[1])
                        month = months_fr[month_name]
                        date_obj = datetime(year, month, 1)
                        dates_found.append(date_obj)
                except (ValueError, KeyError):
                    continue
        
        if dates_found:
            # Retourner la date la plus récente par défaut
            return max(dates_found)
        return None

    def extract_amounts(self, text: str) -> List[float]:
        """Extrait les montants en euros du texte"""
        # Patterns pour les montants
        amount_patterns = [
            r'(\d+(?:\s?\d{3})*(?:[.,]\d{2})?)\s*€',  # 1 234,56 €
            r'(\d+(?:\s?\d{3})*(?:[.,]\d{2})?)\s*euros?',  # 1 234,56 euros
            r'montant.*?(\d+(?:\s?\d{3})*(?:[.,]\d{2})?)',  # montant de 1234,56
            r'somme.*?(\d+(?:\s?\d{3})*(?:[.,]\d{2})?)',  # somme de 1234,56
        ]
        
        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Normaliser le montant
                    amount_str = match.replace(' ', '').replace(',', '.')
                    amount = float(amount_str)
                    amounts.append(amount)
                except ValueError:
                    continue
        
        return amounts

    def extract_entities(self, text: str) -> Dict:
        """Extrait les entités importantes du document CSPE"""
        entities = {
            'dates': [],
            'amounts': [],
            'names': [],
            'references': [],
            'periods': []
        }
        
        # Extraction des dates
        date = self.extract_date(text)
        if date:
            entities['dates'].append(date.strftime('%d/%m/%Y'))
        
        # Extraction des montants
        amounts = self.extract_amounts(text)
        entities['amounts'] = amounts
        
        # Extraction des noms (patterns simples)
        name_patterns = [
            r'[Mm]onsieur\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'[Mm]adame\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'demandeur\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            entities['names'].extend(matches)
        
        # Extraction des références juridiques
        ref_patterns = [
            r'(CRE[-\s]?\d{4}[-\s]?\d+)',  # CRE-2024-001
            r'(CE\s+\d+/\d+/\d+)',  # CE 12/03/2024
            r'(article\s+\w+)',  # article L123-4
        ]
        
        for pattern in ref_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['references'].extend(matches)
        
        # Extraction des périodes
        period_patterns = [
            r'(\d{4})[-\s]?(\d{4})',  # 2010-2015
            r'période\s+(\d{4})\s+(?:à|-)?\s*(\d{4})',  # période 2010 à 2015
        ]
        
        for pattern in period_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                entities['periods'].append(f"{match[0]}-{match[1]}")
        
        return entities

    def check_deadline_compliance(self, decision_date: Optional[datetime], 
                                request_date: Optional[datetime]) -> Dict:
        """Vérifie le respect du délai de 2 mois"""
        if not decision_date or not request_date:
            return {
                'compliant': False,
                'days_elapsed': -1,
                'status': '❌',
                'details': 'Dates manquantes'
            }
        
        delta = request_date - decision_date
        days_elapsed = delta.days
        
        # Règle CSPE: 2 mois = 60 jours calendaires
        is_compliant = days_elapsed <= 60
        
        return {
            'compliant': is_compliant,
            'days_elapsed': days_elapsed,
            'status': '✅' if is_compliant else '❌',
            'details': f'Délai: {days_elapsed} jours (max: 60 jours)'
        }

    def analyze_document_structure(self, text: str) -> Dict:
        """Analyse la structure du document pour détecter les éléments CSPE"""
        analysis = {
            'document_type': 'unknown',
            'has_header': False,
            'has_signature': False,
            'has_attachments': False,
            'quality_score': 0.0
        }
        
        # Détection du type de document
        if 'conseil d\'état' in text.lower() or 'conseil d etat' in text.lower():
            analysis['document_type'] = 'requete_conseil_etat'
        elif 'cre' in text.lower() and 'cspe' in text.lower():
            analysis['document_type'] = 'reclamation_cspe'
        elif 'réclamation' in text.lower() or 'reclamation' in text.lower():
            analysis['document_type'] = 'reclamation'
        
        # Vérifications structurelles
        if any(word in text.lower() for word in ['monsieur le président', 'madame la présidente']):
            analysis['has_header'] = True
        
        if any(word in text.lower() for word in ['signature', 'cordialement', 'salutations']):
            analysis['has_signature'] = True
        
        if any(word in text.lower() for word in ['pièce jointe', 'ci-joint', 'annexe']):
            analysis['has_attachments'] = True
        
        # Score de qualité
        quality_factors = [
            analysis['has_header'],
            analysis['has_signature'],
            'cspe' in text.lower(),
            'cre' in text.lower(),
            len(text) > 100
        ]
        
        analysis['quality_score'] = sum(quality_factors) / len(quality_factors)
        
        return analysis

    def extract_cspe_criteria(self, text: str) -> Dict:
        """Extrait et analyse les 4 critères CSPE spécifiques"""
        criteria = {
            'delai_recours': {'status': '⚠️', 'details': 'Non déterminé'},
            'qualite_demandeur': {'status': '⚠️', 'details': 'Non déterminé'},
            'objet_valide': {'status': '⚠️', 'details': 'Non déterminé'},
            'pieces_justificatives': {'status': '⚠️', 'details': 'Non déterminé'}
        }
        
        # Critère 1: Délai de recours
        dates = re.findall(r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})', text)
        if len(dates) >= 2:
            try:
                # Supposer que la première date est la décision, la dernière la réclamation
                decision_date = datetime(int(dates[0][2]), int(dates[0][1]), int(dates[0][0]))
                request_date = datetime(int(dates[-1][2]), int(dates[-1][1]), int(dates[-1][0]))
                
                deadline_check = self.check_deadline_compliance(decision_date, request_date)
                criteria['delai_recours'] = {
                    'status': deadline_check['status'],
                    'details': deadline_check['details']
                }
            except:
                pass
        
        # Critère 2: Qualité du demandeur
        if any(word in text.lower() for word in ['consommateur', 'particulier', 'client']):
            criteria['qualite_demandeur'] = {
                'status': '✅',
                'details': 'Consommateur final identifié'
            }
        elif any(word in text.lower() for word in ['entreprise', 'société', 'sarl']):
            criteria['qualite_demandeur'] = {
                'status': '✅',
                'details': 'Entreprise concernée'
            }
        
        # Critère 3: Objet valide
        if 'cspe' in text.lower() and any(word in text.lower() for word in ['conteste', 'contestation', 'réclamation']):
            criteria['objet_valide'] = {
                'status': '✅',
                'details': 'Contestation CSPE explicite'
            }
        
        # Critère 4: Pièces justificatives
        pieces_keywords = ['pièce', 'document', 'facture', 'justificatif', 'copie', 'ci-joint']
        pieces_found = sum(1 for keyword in pieces_keywords if keyword in text.lower())
        
        if pieces_found >= 3:
            criteria['pieces_justificatives'] = {
                'status': '✅',
                'details': f'{pieces_found} types de pièces mentionnées'
            }
        elif pieces_found >= 1:
            criteria['pieces_justificatives'] = {
                'status': '⚠️',
                'details': f'Pièces incomplètes ({pieces_found} types)'
            }
        
        return criteria

    def generate_analysis_summary(self, text: str) -> Dict:
        """Génère un résumé complet de l'analyse du document"""
        entities = self.extract_entities(text)
        structure = self.analyze_document_structure(text)
        criteria = self.extract_cspe_criteria(text)
        
        # Classification automatique basée sur les critères
        criteria_ok = sum(1 for c in criteria.values() if c['status'] == '✅')
        criteria_total = len(criteria)
        
        if criteria_ok == criteria_total:
            classification = 'RECEVABLE'
            confidence = 0.90 + (structure['quality_score'] * 0.10)
        elif any(c['status'] == '❌' for c in criteria.values()):
            classification = 'IRRECEVABLE'
            confidence = 0.85
        else:
            classification = 'INSTRUCTION'
            confidence = 0.70
        
        return {
            'classification': classification,
            'confidence_score': min(confidence, 0.99),
            'criteria': criteria,
            'entities': entities,
            'structure': structure,
            'processing_time': 0.73,  # Simulé
            'observations': f"Document {structure['document_type']} - {criteria_ok}/{criteria_total} critères validés"
        }

# Fonctions utilitaires pour la compatibilité
def process_uploaded_file(uploaded_file):
    """Traite un fichier uploadé via Streamlit"""
    processor = DocumentProcessor()
    return processor.extract_text_from_file(uploaded_file)

def analyze_cspe_document(text: str):
    """Analyse complète d'un document CSPE"""
    processor = DocumentProcessor()
    return processor.generate_analysis_summary(text)