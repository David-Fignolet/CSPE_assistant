import PyPDF2
import pytesseract
import cv2
import numpy as np
import io
import re
from PIL import Image
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import json
import hashlib
from dataclasses import dataclass

# Essayer d'importer spaCy avec fallback gracieux
try:
    import spacy
    from spacy import displacy
    SPACY_AVAILABLE = True
    # Essayer de charger le modèle français
    try:
        nlp_fr = spacy.load("fr_core_news_sm")
    except OSError:
        try:
            nlp_fr = spacy.load("fr_core_news_md")
        except OSError:
            nlp_fr = None
            print("⚠️ Modèle spaCy français non trouvé - Utilisation des patterns regex")
except ImportError:
    SPACY_AVAILABLE = False
    nlp_fr = None
    print("⚠️ spaCy non disponible - Utilisation des patterns regex")

@dataclass
class ExtractedEntity:
    """Structure pour une entité extraite"""
    type: str
    value: str
    confidence: float
    start_pos: int = 0
    end_pos: int = 0
    source: str = "regex"

@dataclass
class CSPEDocument:
    """Structure complète d'un document CSPE analysé"""
    text: str
    entities: Dict[str, List[ExtractedEntity]]
    demandeur: Optional[str] = None
    dates: List[datetime] = None
    montants: List[float] = None
    references: List[str] = None
    quality_score: float = 0.0

class SmartEntityExtractor:
    """
    Extracteur d'entités intelligent avec fallback et cache
    Conçu spécifiquement pour les documents juridiques CSPE
    """
    
    def __init__(self):
        self.cache = {}
        self.spacy_model = nlp_fr
        self._init_patterns()
        
    def _init_patterns(self):
        """Initialise les patterns regex optimisés pour CSPE"""
        
        # Patterns pour les noms de personnes (français)
        self.name_patterns = [
            # Format officiel : Nom Prénom
            r'(?:demandeur|requérant)\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # Monsieur/Madame + Nom
            r'(?:monsieur|madame|m\.|mme)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # Signature en fin de document
            r'(?:cordialement|salutations),\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # Format "Fait à [ville], le [date], [Nom]"
            r'fait\s+à\s+[^,]+,.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # Nom en début de ligne suivi d'une adresse
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\n.*?(?:\d{5}|rue|avenue)',
            # Format juridique : "Par la présente, je soussigné [Nom]"
            r'je\s+soussign[ée]?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        # Patterns pour les dates (formats français)
        self.date_patterns = [
            # DD/MM/YYYY ou DD-MM-YYYY ou DD.MM.YYYY
            r'(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})',
            # DD mois YYYY
            r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
            # mois YYYY
            r'(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
            # Format ISO YYYY-MM-DD
            r'(\d{4})[/.\-](\d{1,2})[/.\-](\d{1,2})',
        ]
        
        # Patterns pour les montants
        self.amount_patterns = [
            # Montant avec €
            r'(\d+(?:\s?\d{3})*(?:[.,]\d{1,2})?)\s*€',
            # Montant avec "euros"
            r'(\d+(?:\s?\d{3})*(?:[.,]\d{1,2})?)\s*euros?',
            # "montant de X"
            r'montant\s+(?:de\s+|réclamé\s+)?(\d+(?:\s?\d{3})*(?:[.,]\d{1,2})?)',
            # "somme de X"
            r'somme\s+(?:de\s+)?(\d+(?:\s?\d{3})*(?:[.,]\d{1,2})?)',
            # CSPE d'un montant de X
            r'cspe\s+d\'un\s+montant\s+de\s+(\d+(?:\s?\d{3})*(?:[.,]\d{1,2})?)',
        ]
        
        # Patterns pour les références juridiques
        self.reference_patterns = [
            # Décision CRE
            r'(CRE[-\s]?\d{4}[-\s]?\d+)',
            r'(décision\s+(?:de\s+la\s+)?CRE[^.]{0,50})',
            # Références Conseil d'État
            r'(CE\s+\d+/\d+/\d+)',
            r'(Conseil\s+d\'État[^.]{0,50})',
            # Numéros de dossier
            r'(dossier\s+n°?\s*[\w\-/]+)',
            # Articles de loi
            r'(article\s+[A-Z]?\d+(?:\-\d+)*)',
        ]
        
        # Dictionnaire des mois français
        self.months_fr = {
            'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
            'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
            'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
        }

    def _get_cache_key(self, text: str) -> str:
        """Génère une clé de cache pour le texte"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()[:16]

    def extract_names(self, text: str) -> List[ExtractedEntity]:
        """Extrait les noms de personnes avec intelligence contextuelle"""
        names = []
        text_lower = text.lower()
        
        # Utiliser spaCy si disponible
        if self.spacy_model:
            try:
                doc = self.spacy_model(text)
                for ent in doc.ents:
                    if ent.label_ == "PER":  # Personne
                        names.append(ExtractedEntity(
                            type="person",
                            value=ent.text.strip(),
                            confidence=0.85,
                            start_pos=ent.start_char,
                            end_pos=ent.end_char,
                            source="spacy"
                        ))
            except Exception as e:
                print(f"⚠️ Erreur spaCy pour noms: {e}")
        
        # Fallback avec patterns regex améliorés
        for pattern in self.name_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                name = match.group(1).strip()
                # Filtrer les faux positifs
                if self._is_valid_name(name):
                    confidence = self._calculate_name_confidence(name, text_lower, match)
                    names.append(ExtractedEntity(
                        type="person",
                        value=name,
                        confidence=confidence,
                        start_pos=match.start(1),
                        end_pos=match.end(1),
                        source="regex"
                    ))
        
        # Déduplication et tri par confiance
        unique_names = {}
        for name_entity in names:
            key = name_entity.value.lower().strip()
            if key not in unique_names or name_entity.confidence > unique_names[key].confidence:
                unique_names[key] = name_entity
        
        return sorted(unique_names.values(), key=lambda x: x.confidence, reverse=True)

    def _is_valid_name(self, name: str) -> bool:
        """Valide qu'une chaîne est un nom plausible"""
        if not name or len(name) < 2:
            return False
        
        # Filtrer les mots qui ne sont pas des noms
        invalid_words = {
            'président', 'conseil', 'état', 'monsieur', 'madame',
            'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
            'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
            'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche',
            'france', 'paris', 'lyon', 'marseille', 'toulouse', 'nice',
            'cspe', 'cre', 'edf', 'enedis', 'tarif', 'facture'
        }
        
        name_lower = name.lower()
        return not any(word in name_lower for word in invalid_words)

    def _calculate_name_confidence(self, name: str, text_lower: str, match) -> float:
        """Calcule un score de confiance pour un nom extrait"""
        confidence = 0.5  # Base
        
        # Bonus si le nom apparaît dans un contexte officiel
        context_start = max(0, match.start() - 50)
        context_end = min(len(text_lower), match.end() + 50)
        context = text_lower[context_start:context_end]
        
        if any(word in context for word in ['demandeur', 'requérant', 'soussigné']):
            confidence += 0.3
        if any(word in context for word in ['monsieur', 'madame']):
            confidence += 0.2
        if 'cordialement' in context or 'salutations' in context:
            confidence += 0.2
        
        # Bonus pour format "Prénom NOM"
        parts = name.split()
        if len(parts) == 2:
            confidence += 0.1
        
        return min(confidence, 0.95)

    def extract_dates(self, text: str) -> List[ExtractedEntity]:
        """Extrait les dates avec reconnaissance contextuelle"""
        dates = []
        
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    date_obj = self._parse_date_match(match)
                    if date_obj:
                        # Calculer la confiance basée sur le contexte
                        confidence = self._calculate_date_confidence(match, text)
                        
                        dates.append(ExtractedEntity(
                            type="date",
                            value=date_obj.strftime('%Y-%m-%d'),
                            confidence=confidence,
                            start_pos=match.start(),
                            end_pos=match.end(),
                            source="regex"
                        ))
                except ValueError:
                    continue
        
        return sorted(dates, key=lambda x: x.confidence, reverse=True)

    def _parse_date_match(self, match) -> Optional[datetime]:
        """Parse une correspondance de date en objet datetime"""
        groups = match.groups()
        
        try:
            if len(groups) == 3:
                if groups[1].isdigit():  # Format DD/MM/YYYY
                    day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                    return datetime(year, month, day)
                elif groups[1].lower() in self.months_fr:  # Format DD mois YYYY
                    day = int(groups[0])
                    month = self.months_fr[groups[1].lower()]
                    year = int(groups[2])
                    return datetime(year, month, day)
            elif len(groups) == 2 and groups[0].lower() in self.months_fr:  # Format mois YYYY
                month = self.months_fr[groups[0].lower()]
                year = int(groups[1])
                return datetime(year, month, 1)
        except (ValueError, KeyError):
            pass
        
        return None

    def _calculate_date_confidence(self, match, text: str) -> float:
        """Calcule la confiance pour une date basée sur le contexte"""
        confidence = 0.7  # Base
        
        # Contexte autour de la date
        start = max(0, match.start() - 30)
        end = min(len(text), match.end() + 30)
        context = text[start:end].lower()
        
        # Bonus pour contextes juridiques
        legal_contexts = ['décision', 'réclamation', 'demande', 'fait', 'date']
        for ctx in legal_contexts:
            if ctx in context:
                confidence += 0.1
                break
        
        # Vérifier la plausibilité de la date (période CSPE 2009-2025)
        date_str = match.group(0)
        if any(year in date_str for year in ['2009', '2010', '2011', '2012', '2013', '2014', '2015', '2020', '2021', '2022', '2023', '2024', '2025']):
            confidence += 0.15
        
        return min(confidence, 0.95)

    def extract_amounts(self, text: str) -> List[ExtractedEntity]:
        """Extrait les montants monétaires"""
        amounts = []
        
        for pattern in self.amount_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount_str = match.group(1)
                    # Normaliser le montant
                    normalized_amount = amount_str.replace(' ', '').replace(',', '.')
                    amount_value = float(normalized_amount)
                    
                    # Filtrer les montants non plausibles
                    if 1 <= amount_value <= 1000000:  # Entre 1€ et 1M€
                        confidence = self._calculate_amount_confidence(match, text, amount_value)
                        
                        amounts.append(ExtractedEntity(
                            type="amount",
                            value=str(amount_value),
                            confidence=confidence,
                            start_pos=match.start(),
                            end_pos=match.end(),
                            source="regex"
                        ))
                except ValueError:
                    continue
        
        return sorted(amounts, key=lambda x: x.confidence, reverse=True)

    def _calculate_amount_confidence(self, match, text: str, amount: float) -> float:
        """Calcule la confiance pour un montant"""
        confidence = 0.6  # Base
        
        # Contexte
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        context = text[start:end].lower()
        
        # Bonus pour contextes CSPE
        if any(word in context for word in ['cspe', 'réclamé', 'montant', 'facture']):
            confidence += 0.2
        
        # Bonus pour montants plausibles CSPE (100€ - 50k€)
        if 100 <= amount <= 50000:
            confidence += 0.15
        
        return min(confidence, 0.95)

    def extract_references(self, text: str) -> List[ExtractedEntity]:
        """Extrait les références juridiques"""
        references = []
        
        for pattern in self.reference_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                ref_text = match.group(0).strip()
                confidence = 0.8 if 'CRE' in ref_text or 'CE' in ref_text else 0.6
                
                references.append(ExtractedEntity(
                    type="reference",
                    value=ref_text,
                    confidence=confidence,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    source="regex"
                ))
        
        return references

    def extract_all_entities(self, text: str) -> Dict[str, List[ExtractedEntity]]:
        """Extrait toutes les entités du texte"""
        cache_key = self._get_cache_key(text)
        
        # Vérifier le cache
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Extraction complète
        entities = {
            'persons': self.extract_names(text),
            'dates': self.extract_dates(text),
            'amounts': self.extract_amounts(text),
            'references': self.extract_references(text)
        }
        
        # Mise en cache
        self.cache[cache_key] = entities
        
        return entities

    def get_best_demandeur(self, text: str) -> Optional[str]:
        """Retourne le demandeur le plus probable"""
        persons = self.extract_names(text)
        return persons[0].value if persons else None

    def get_best_amount(self, text: str) -> Optional[float]:
        """Retourne le montant principal le plus probable"""
        amounts = self.extract_amounts(text)
        if amounts:
            try:
                return float(amounts[0].value)
            except ValueError:
                pass
        return None

    def get_all_dates(self, text: str) -> List[datetime]:
        """Retourne toutes les dates trouvées, triées"""
        dates = self.extract_dates(text)
        date_objects = []
        for date_entity in dates:
            try:
                date_obj = datetime.strptime(date_entity.value, '%Y-%m-%d')
                date_objects.append(date_obj)
            except ValueError:
                continue
        return sorted(date_objects)


class DocumentProcessor:
    """Processeur de documents amélioré avec extraction d'entités intelligente"""
    
    def __init__(self):
        self.ocr_config = '--psm 6 --oem 3 -l fra'
        self.entity_extractor = SmartEntityExtractor()

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
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=40)
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            kernel = np.ones((1, 1), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            return binary
        except Exception as e:
            print(f"Erreur prétraitement image: {str(e)}")
            return image

    def extract_text_from_image(self, file_content: bytes) -> str:
        """Extrait le texte d'une image avec OCR"""
        try:
            image = Image.open(io.BytesIO(file_content))
            image_np = np.array(image)
            processed = self.preprocess_image(image_np)
            
            text = pytesseract.image_to_string(processed, config=self.ocr_config)
            return text.strip()
        except Exception as e:
            print(f"Erreur lors de l'extraction OCR: {str(e)}")
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
                    if file_name.lower().endswith('.txt'):
                        return file_content.decode('utf-8', errors='ignore')
                    elif file_name.lower().endswith('.pdf'):
                        return self.extract_text_from_pdf(file_content)
                    elif file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                        return self.extract_text_from_image(file_content)
                    else:
                        return f"Format non supporté: {file_type} (fichier: {file_name})"
            
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

    def analyze_cspe_document(self, text: str) -> CSPEDocument:
        """Analyse complète d'un document CSPE avec extraction d'entités"""
        entities = self.entity_extractor.extract_all_entities(text)
        
        # Extraire les informations clés
        demandeur = self.entity_extractor.get_best_demandeur(text)
        montant_principal = self.entity_extractor.get_best_amount(text)
        dates = self.entity_extractor.get_all_dates(text)
        
        # Calculer un score de qualité
        quality_score = self._calculate_document_quality(text, entities)
        
        return CSPEDocument(
            text=text,
            entities=entities,
            demandeur=demandeur,
            dates=dates,
            montants=[montant_principal] if montant_principal else [],
            references=[ref.value for ref in entities.get('references', [])],
            quality_score=quality_score
        )

    def _calculate_document_quality(self, text: str, entities: Dict) -> float:
        """Calcule un score de qualité pour le document"""
        score = 0.0
        
        # Longueur du document
        if len(text) > 100:
            score += 0.2
        
        # Présence d'entités clés
        if entities.get('persons'):
            score += 0.3
        if entities.get('dates'):
            score += 0.2
        if entities.get('amounts'):
            score += 0.2
        
        # Mots-clés CSPE
        text_lower = text.lower()
        if 'cspe' in text_lower:
            score += 0.1
        if any(word in text_lower for word in ['cre', 'conseil d\'état', 'réclamation']):
            score += 0.1
        
        return min(score, 1.0)

    # Méthodes de compatibilité avec l'ancien code
    def extract_entities(self, text: str) -> Dict:
        """Méthode de compatibilité - retourne le format ancien"""
        entities = self.entity_extractor.extract_all_entities(text)
        
        # Conversion au format attendu
        return {
            'dates': [entity.value for entity in entities.get('dates', [])],
            'amounts': [float(entity.value) for entity in entities.get('amounts', [])],
            'names': [entity.value for entity in entities.get('persons', [])],
            'references': [entity.value for entity in entities.get('references', [])],
            'periods': []  # À implémenter si nécessaire
        }

    def extract_cspe_criteria(self, text: str) -> Dict:
        """Analyse les 4 critères CSPE avec la nouvelle logique"""
        doc = self.analyze_cspe_document(text)
        
        criteria = {
            'delai_recours': {'status': '⚠️', 'details': 'Non déterminé'},
            'qualite_demandeur': {'status': '⚠️', 'details': 'Non déterminé'},
            'objet_valide': {'status': '⚠️', 'details': 'Non déterminé'},
            'pieces_justificatives': {'status': '⚠️', 'details': 'Non déterminé'}
        }
        
        # Critère 1: Délai de recours
        if len(doc.dates) >= 2:
            dates_sorted = sorted(doc.dates)
            decision_date = dates_sorted[0]
            request_date = dates_sorted[-1]
            
            delta = (request_date - decision_date).days
            if delta <= 60:
                criteria['delai_recours'] = {
                    'status': '✅',
                    'details': f'Respecté ({delta} jours vs 60 max)'
                }
            else:
                criteria['delai_recours'] = {
                    'status': '❌',
                    'details': f'Dépassé ({delta} jours vs 60 max)'
                }
        
        # Critère 2: Qualité du demandeur
        if doc.demandeur:
            criteria['qualite_demandeur'] = {
                'status': '✅',
                'details': f'Demandeur identifié: {doc.demandeur}'
            }
        
        # Critère 3: Objet valide
        text_lower = text.lower()
        if 'cspe' in text_lower and any(word in text_lower for word in ['conteste', 'contestation', 'réclamation']):
            criteria['objet_valide'] = {
                'status': '✅',
                'details': 'Contestation CSPE explicite'
            }
        
        # Critère 4: Pièces justificatives
        pieces_keywords = ['pièce', 'document', 'facture', 'justificatif', 'copie', 'ci-joint']
        pieces_found = sum(1 for keyword in pieces_keywords if keyword in text_lower)
        
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


# Fonctions utilitaires pour la compatibilité
def process_uploaded_file(uploaded_file):
    """Traite un fichier uploadé via Streamlit"""
    processor = DocumentProcessor()
    return processor.extract_text_from_file(uploaded_file)

def analyze_cspe_document(text: str):
    """Analyse complète d'un document CSPE"""
    processor = DocumentProcessor()
    return processor.analyze_cspe_document(text)