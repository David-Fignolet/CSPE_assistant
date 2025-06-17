import re
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

@dataclass
class ExtractedEntity:
    """Structure for an extracted entity."""
    type: str
    value: str
    confidence: float = 1.0
    start_pos: int = 0
    end_pos: int = 0
    source: str = "regex"

class SmartEntityExtractor:
    """Smart entity extractor for CSPE documents."""

    def __init__(self):
        # Mapping des mois français vers leurs numéros
        self.month_map = {
            'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
            'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
            'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
        }

    def _parse_french_date(self, date_str: str) -> str:
        """Parse une date française du type '1er janvier 2023' ou '1 janvier 2023'"""
        try:
            # Supprimer le 'er' si présent
            date_str = re.sub(r'(\d+)er\b', r'\1', date_str)
            # Diviser en parties
            parts = date_str.split()
            if len(parts) != 3:
                return None

            day = parts[0].zfill(2)
            month = self.month_map.get(parts[1].lower())
            year = parts[2]

            if not month:
                return None

            return f"{year}-{month}-{day}"
        except Exception:
            return None

    def extract_dates(self, text: str) -> List[ExtractedEntity]:
        """Extract dates from text."""
        results = []

        # 1. Format français avec "1er janvier 2023"
        fr_pattern = r'\b(\d{1,2}(?:er)?\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\b'
        for match in re.finditer(fr_pattern, text, re.IGNORECASE):
            date_str = match.group(1)
            formatted_date = self._parse_french_date(date_str)
            if formatted_date:
                results.append(ExtractedEntity(
                    type="date",
                    value=formatted_date,
                    confidence=0.9,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    source="regex"
                ))

        # 2. Format JJ/MM/AAAA ou JJ-MM-AAAA
        day_month_pattern = r'\b(0?[1-9]|[12][0-9]|3[01])[/-](0?[1-9]|1[0-2])[/-](\d{4})\b'
        for match in re.finditer(day_month_pattern, text):
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)
            formatted_date = f"{year}-{month}-{day}"
            results.append(ExtractedEntity(
                type="date",
                value=formatted_date,
                confidence=0.9,
                start_pos=match.start(),
                end_pos=match.end(),
                source="regex"
            ))

        # 3. Format AAAA-MM-JJ (ISO)
        iso_pattern = r'\b(\d{4})[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12][0-9]|3[01])\b'
        for match in re.finditer(iso_pattern, text):
            year = match.group(1)
            month = match.group(2).zfill(2)
            day = match.group(3).zfill(2)
            formatted_date = f"{year}-{month}-{day}"
            results.append(ExtractedEntity(
                type="date",
                value=formatted_date,
                confidence=0.9,
                start_pos=match.start(),
                end_pos=match.end(),
                source="regex"
            ))

        return results

    def _is_false_positive(self, match: re.Match, text: str) -> bool:
        """Vérifie si la correspondance est un faux positif."""
        matched_text = match.group(0).lower()
        context_window = 50
        start = max(0, match.start() - context_window)
        end = min(len(text), match.end() + context_window)
        context = text[start:end].lower()
        
        # Mots-clés indiquant un faux positif
        blacklist = [
            'page', 'n°', '°', 'numéro', 'article', 'paragraphe', 'chapitre', 
            'annexe', 'téléphone', 'tél', 'fax', 'portable', 'mobile', 
            'code postal', 'cp', 'siret', 'siren', 'tva', 'ht', 'ttc', 'tac',
            'facturé', 'payé', 'régler', 'dépense', 'coût', 'prix', 'tarif',
            'facturation', 'devis', 'tarification', 'rémunération', 'honoraire',
            'escompte', 'majoration', 'pénalité', 'intérêt', 'frais', 'solde'
        ]
        
        # Vérifier les motifs de faux positifs
        for item in blacklist:
            if item in context:
                return True
        
        # Vérifier les formats de date
        if re.search(r'\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?', matched_text):
            return True
            
        # Vérifier les numéros de téléphone
        phone_patterns = [
            r'\b0[1-9](?:[\s.-]?\d{2}){4}\b',  # 01 23 45 67 89
            r'\+33[\s.-]?[1-9](?:[\s.-]?\d{2}){4}\b'  # +33 1 23 45 67 89
        ]
        for pattern in phone_patterns:
            if re.search(pattern, matched_text):
                return True
                
        # Vérifier les numéros de page
        if re.search(r'page\s+\d+', context, re.IGNORECASE):
            return True
            
        # Vérifier les références d'article
        if re.search(r'article\s+\d+', context, re.IGNORECASE):
            return True
            
        # Vérifier les numéros de version
        if re.search(r'version\s+\d+\.\d+', context, re.IGNORECASE):
            return True
                
        return False

    def _is_currency_context(self, match: re.Match, text: str) -> bool:
        """Vérifie si le montant est dans un contexte monétaire."""
        context_window = 50
        start = max(0, match.start() - context_window)
        end = min(len(text), match.end() + context_window)
        context = text[start:end].lower()
        
        # Mots-clés indiquant un contexte monétaire
        currency_indicators = [
            '€', 'euro', 'eur', 'prix', 'coût', 'montant', 'total', 'facture',
            'somme', 'dû', 'du', 'payer', 'paiement', 'règlement', 'chèque',
            'virement', 'remboursement', 'indemnité', 'tva', 'ht', 'ttc', 'tac',
            'facturé', 'payé', 'régler', 'dépense', 'coût', 'prix', 'tarif',
            'facturation', 'devis', 'tarification', 'rémunération', 'honoraire',
            'escompte', 'majoration', 'pénalité', 'intérêt', 'frais', 'solde'
        ]
        
        # Vérifier la présence de mots-clés monétaires autour du montant
        for indicator in currency_indicators:
            if indicator in context:
                # Vérifier la proximité du mot-clé avec le montant
                indicator_pos = context.find(indicator)
                if indicator_pos != -1 and abs(indicator_pos - (match.start() - start)) < 30:
                    return True
        
        return False

    def _normalize_amount(self, amount_str: str) -> float:
        """Normalise une chaîne de montant en nombre flottant."""
        # Supprimer les espaces et caractères spéciaux
        amount_str = amount_str.strip().replace(' ', '').replace('\u202F', '')
        
        # Gérer le cas où le point est un séparateur de milliers
        if '.' in amount_str and ',' in amount_str:
            # Si la virgule est avant le point, c'est la décimale
            if amount_str.find(',') < amount_str.find('.'):
                amount_str = amount_str.replace(',', '')
            # Sinon, le point est le séparateur de milliers
            else:
                amount_str = amount_str.replace('.', '').replace(',', '.')
        # Si on a une virgule et pas de point, c'est la décimale
        elif ',' in amount_str:
            amount_str = amount_str.replace(',', '.')
        
        try:
            return float(amount_str)
        except ValueError:
            return None

    def extract_amounts(self, text: str) -> List[ExtractedEntity]:
        """Extrait les montants du texte avec une meilleure précision."""
        entities = []
        seen_positions = set()  # Pour éviter les doublons
        
        # Normalisation du texte
        text = self._normalize_text(text)
        
        # Patterns améliorés avec contexte et priorité
        amount_patterns = [
            # 1. Montants avec symbole € (haute confiance)
            (r'(?<!\d)([1-9]\d{0,2}(?:[ \u202F]\d{3})*(?:[.,]\d{1,2})?)\s*[€$]', 0.98, 1),
            # 2. Montants avec devise en toutes lettres (haute confiance)
            (r'(?<!\d)([1-9]\d{0,2}(?:[ \u202F]\d{3})*(?:[.,]\d{1,2})?)\s+(?:euros?|EUR)\b', 0.98, 1),
            # 3. Montants avec symbole € collé (haute confiance)
            (r'(?<!\d)([1-9]\d{0,2}(?:[ \u202F]\d{3})*(?:[.,]\d{1,2})?)€', 0.98, 1),
            # 4. Montants dans un contexte financier (moyenne confiance)
            (r'\b(?:montant|total|facture|règlement|à payer|d[ûu]|co[ûu]t|prix|somme)[^\d€$]{0,20}?([1-9]\d{0,2}(?:[ \u202F]\d{3})*(?:[.,]\d{1,2})?)(?:\s|$)', 0.90, 1),
            # 5. Montants avec séparateur de milliers
            (r'(?<!\d)([1-9]\d{0,2}(?:[ \u202F]\d{3})+(?:[.,]\d{1,2})?)(?![€\d.,])', 0.80, 1),
            # 6. Montants simples sans séparateur
            (r'(?<!\d)([1-9]\d{2,})(?![€\d.,])', 0.60, 1),
        ]
        
        # Extraction avec validation contextuelle
        for pattern, confidence, group_idx in amount_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Vérifier si cette position a déjà été traitée
                start_pos = match.start(group_idx)
                end_pos = match.end(group_idx)
                if (start_pos, end_pos) in seen_positions:
                    continue
                    
                amount_str = match.group(group_idx)
                amount = self._normalize_amount(amount_str)
                
                if amount is None or amount <= 0:
                    continue
                    
                # Vérifier si c'est un faux positif
                if self._is_false_positive(match, text):
                    continue
                    
                # Ajuster la confiance en fonction du contexte
                current_confidence = confidence
                
                # Pour les montants sans contexte monétaire explicite
                if group_idx == 1 and not self._is_currency_context(match, text):
                    # Réduire la confiance pour les petits montants sans contexte
                    if amount < 10:
                        current_confidence = max(0.3, confidence - 0.4)
                    # Réduire légèrement pour les montants moyens
                    elif amount < 100:
                        current_confidence = max(0.5, confidence - 0.2)
                
                # Seuil de confiance minimum
                if current_confidence < 0.7 and amount < 1000:
                    continue
                    
                # Création de l'entité
                entity = ExtractedEntity(
                    type="amount",
                    value=amount,
                    confidence=current_confidence,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    source="regex"
                )
                
                entities.append(entity)
                seen_positions.add((start_pos, end_pos))
        
        # Trier par position dans le texte
        entities.sort(key=lambda x: x.start_pos)
        
        return entities

    def _normalize_text(self, text: str) -> str:
        """Normalise le texte pour une meilleure extraction."""
        # Remplace les espaces insécables par des espaces normaux
        text = text.replace('\xa0', ' ')
        # Normalise les espaces
        text = ' '.join(text.split())
        return text

class DocumentProcessor:
    """CSPE document processor."""

    def __init__(self):
        self.entity_extractor = SmartEntityExtractor()

    def extract_dates(self, text: str) -> List[ExtractedEntity]:
        """Extract dates from text."""
        return self.entity_extractor.extract_dates(text)

    def extract_amounts(self, text: str) -> List[ExtractedEntity]:
        """Extract amounts from text."""
        return self.entity_extractor.extract_amounts(text)

    def check_period(self, text: str) -> dict:
        """Check if a valid period is mentioned."""
        patterns = [
            r'(?:année|exercice)\s+(\d{4})',
            r'période\s+(\d{4}(?:\s*-\s*\d{2,4})?)',
            r'(?:du|depuis)\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}(?:\s*au\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4})?'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {
                    "is_valid": True,
                    "message": "Période valide détectée",
                    "period": match.group(0)
                }

        return {
            "is_valid": False,
            "message": "Aucune période valide détectée",
            "period": None
        }

    def check_delay(self, text: str, test_mode: bool = False) -> dict:
        """Vérifie si le délai de recours est respecté"""
        try:
            dates = self.extract_dates(text)
            if not dates:
                return {
                    "is_valid": False,
                    "message": "Aucune date trouvée",
                    "is_on_time": False
                }

            dated_entities = []
            for date_entity in dates:
                try:
                    dt = datetime.strptime(date_entity.value, '%Y-%m-%d')
                    dated_entities.append((dt, date_entity))
                except ValueError:
                    continue

            if not dated_entities:
                return {
                    "is_valid": False,
                    "message": "Aucune date valide trouvée",
                    "is_on_time": False
                }

            # Trier par date (la plus récente en premier)
            dated_entities.sort(reverse=True, key=lambda x: x[0])
            latest_date_dt, latest_date_entity = dated_entities[0]

            # Date de référence pour le test (1er mars 2023)
            if test_mode:
                today = datetime.strptime("2023-03-01", "%Y-%m-%d")
            else:
                today = datetime.now()

            # Calculer la différence en jours
            delta = (today - latest_date_dt).days

            # Vérifier si le délai est respecté (60 jours inclus)
            is_on_time = delta <= 60

            return {
                "is_valid": True,  # La vérification a pu être faite
                "message": "Délai respecté" if is_on_time else "Délai dépassé",
                "decision_date": latest_date_entity.value,
                "days_since_decision": delta,
                "is_on_time": is_on_time
            }
        except Exception as e:
            return {
                "is_valid": False,
                "message": f"Erreur: {str(e)}",
                "is_on_time": False
            }

    def check_prescription_quadriennale(self, text: str, reference_date: str = None) -> dict:
        """
        Vérifie si la réclamation est prescrite (délai de 4 ans).
        
        Args:
            text: Texte à analyser
            reference_date: Date de référence pour le calcul (format 'YYYY-MM-DD'). 
                         Si None, utilise la date actuelle.
        
        Returns:
            Dictionnaire contenant:
            - is_prescrit: bool - True si la réclamation est prescrite
            - message: str - Message explicatif
            - date_limite: str - Date limite de prescription (format 'YYYY-MM-DD')
            - date_reference: str - Date de référence utilisée pour le calcul
        """
        try:
            # Obtenir la date de référence
            if reference_date:
                ref_date = datetime.strptime(reference_date, '%Y-%m-%d').date()
            else:
                ref_date = datetime.now().date()
            
            # Extraire toutes les dates du texte
            dates = self.extract_dates(text)
            if not dates:
                return {
                    "is_prescrit": False,
                    "message": "Aucune date trouvée pour vérifier la prescription",
                    "date_limite": None,
                    "date_reference": ref_date.isoformat()
                }
            
            # Trier les dates par ordre chronologique (plus ancienne d'abord)
            sorted_dates = sorted([d for d in dates if d.value], 
                                key=lambda x: x.value)
            
            if not sorted_dates:
                return {
                    "is_prescrit": False,
                    "message": "Aucune date valide trouvée",
                    "date_limite": None,
                    "date_reference": ref_date.isoformat()
                }
            
            # Prendre la date la plus ancienne comme date de fait générateur
            date_fait = datetime.strptime(sorted_dates[0].value, '%Y-%m-%d').date()
            
            # Calculer la date limite de prescription (4 ans après la date du fait)
            from datetime import timedelta
            date_limite = date_fait + timedelta(days=4*365 + 1)  # +1 pour l'année bissextile
            
            # Vérifier si la date de référence est postérieure à la date limite
            is_prescrit = ref_date > date_limite
            
            return {
                "is_prescrit": is_prescrit,
                "message": f"La réclamation est {'prescrite' if is_prescrit else 'non prescrite'}",
                "date_limite": date_limite.isoformat(),
                "date_reference": ref_date.isoformat(),
                "date_fait_genérateur": date_fait.isoformat()
            }
            
        except Exception as e:
            return {
                "is_prescrit": False,
                "message": f"Erreur lors de la vérification de la prescription: {str(e)}",
                "date_limite": None,
                "date_reference": ref_date.isoformat() if 'ref_date' in locals() else None
            }

    def check_repercussion_client_final(self, text: str) -> dict:
        """
        Vérifie si le surcoût a été répercuté sur le client final.
        
        Args:
            text: Texte à analyser
            
        Returns:
            Dictionnaire contenant:
            - repercussion_detectee: bool - True si répercussion détectée
            - message: str - Message explicatif
            - confiance: float - Niveau de confiance de la détection (0.0 à 1.0)
            - elements_pertinents: List[str] - Éléments de texte pertinents trouvés
        """
        # Mots-clés indiquant une répercussion sur le client final
        indicateurs_positifs = [
            ("répercuté sur le client final", 0.9),
            ("répercutée sur le client final", 0.9),
            ("facturé au client final", 0.9),
            ("facturée au client final", 0.9),
            ("répercuté dans le prix de vente", 0.8),
            ("répercutée dans le prix de vente", 0.8),
            ("intégré dans le prix de vente", 0.7),
            ("intégrée dans le prix de vente", 0.7),
            ("reporté sur le client", 0.8),
            ("reportée sur le client", 0.8),
            ("répercuté intégralement", 0.7),
            ("répercutée intégralement", 0.7)
        ]
        
        # Mots-clés indiquant une absence de répercussion
        indicateurs_negatifs = [
            "non répercuté",
            "non répercutée",
            "sans répercussion",
            "à notre charge",
            "supporté par l'entreprise",
            "non facturé",
            "non facturée",
            "non reporté",
            "non reportée"
        ]
        
        # Normalisation du texte pour une recherche insensible à la casse
        text_lower = text.lower()
        
        # Vérifier d'abord les indicateurs négatifs (qui annulent la répercussion)
        for indicateur in indicateurs_negatifs:
            if indicateur in text_lower:
                return {
                    "repercussion_detectee": False,
                    "message": f"Indicateur d'absence de répercussion détecté: '{indicateur}'",
                    "confiance": 0.9,
                    "elements_pertinents": [indicateur]
                }
        
        # Rechercher les indicateurs positifs
        elements_trouves = []
        confiance_totale = 0.0
        
        for motif, confiance in indicateurs_positifs:
            if motif in text_lower:
                elements_trouves.append(motif)
                confiance_totale = max(confiance_totale, confiance)
        
        # Si on a trouvé au moins un indicateur positif
        if elements_trouves:
            return {
                "repercussion_detectee": True,
                "message": f"Répercussion sur le client final détectée: {', '.join(elements_trouves)}",
                "confiance": min(confiance_totale, 0.95),  # Ne pas dépasser 0.95 pour laisser de la place à la confirmation manuelle
                "elements_pertinents": elements_trouves
            }
        
        # Si aucun indicateur n'est trouvé, on considère qu'il n'y a pas de répercussion
        return {
            "repercussion_detectee": False,
            "message": "Aucun indicateur de répercussion sur le client final détecté",
            "confiance": 0.7,  # Confiance moyenne car absence de preuve n'est pas preuve d'absence
            "elements_pertinents": []
        }

# Exemple d'utilisation
if __name__ == "__main__":
    processor = DocumentProcessor()

    # Test extraction de dates
    text = "Le 1er janvier 2023, une réunion a eu lieu. La prochaine est prévue pour 01/02/2023."
    print("\nTest extraction de dates:")
    dates = processor.extract_dates(text)
    for date in dates:
        print(f"Date: {date.value}, Confidence: {date.confidence}")

    # Test extraction de montants
    amounts_text = "Les montants sont 1 234,56 € et 1,234.56 €."
    print("\nTest extraction de montants:")
    amounts = processor.extract_amounts(amounts_text)
    for amount in amounts:
        print(f"Amount: {amount.value}")

    # Test vérification de délai
    print("\nTest vérification de délai:")
    delay_text = "Décision du 01/01/2023"
    result = processor.check_delay(delay_text, test_mode=True)
    print(f"Résultat vérification délai: {result}")
