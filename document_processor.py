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

    def extract_amounts(self, text: str) -> List[ExtractedEntity]:
        """Extract amounts from text."""
        amounts = []

        # Format français : 1 234,56 €
        fr_amount_pattern = r'(\d{1,3}(?:\s\d{3})*(?:,\d{2}))\s*(?:€|\$\|euro|dollar)?'
        for match in re.finditer(fr_amount_pattern, text):
            try:
                amount_str = match.group(1).replace(' ', '').replace(',', '.')
                # Vérifier que nous avons bien un nombre avec 2 décimales
                if re.match(r'^\d+\.\d{2}$', amount_str):
                    amounts.append(ExtractedEntity(
                        type="amount",
                        value=amount_str,
                        confidence=0.9,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        source="regex"
                    ))
            except Exception as e:
                print(f"Erreur lors de l'extraction du montant: {e}")

        # Format international : 1,234.56 € ou 1234.56
        int_amount_pattern = r'(\d{1,3}(?:,\d{3})*\.\d{2}|\d+\.\d{2})\s*(?:€|\$\|euro|dollar)?'
        for match in re.finditer(int_amount_pattern, text):
            try:
                amount_str = match.group(1).replace(',', '')
                # Vérifier que nous avons bien un nombre avec 2 décimales
                if re.match(r'^\d+\.\d{2}$', amount_str):
                    amounts.append(ExtractedEntity(
                        type="amount",
                        value=amount_str,
                        confidence=0.9,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        source="regex"
                    ))
            except Exception as e:
                print(f"Erreur lors de l'extraction du montant: {e}")

        return amounts

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
