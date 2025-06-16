import re
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import dateparser
from dateparser.search import search_dates

@dataclass
class ExtractedEntity:
    """Structure for an extracted entity."""
    type: str
    value: str
    confidence: float = 1.0
    start_pos: int = 0
    end_pos: int = 0
    source: str = "regex"

class SmartDateExtractor:
    """Improved date extractor using dateparser."""

    def extract_dates(self, text: str) -> List[ExtractedEntity]:
        """Extract dates from text using dateparser."""
        results = []

        # Detect all possible dates in the text
        matches = search_dates(
            text,
            languages=['fr'],
            settings={
                'PREFER_DAY_OF_MONTH': 'first',
                'DATE_ORDER': 'DMY',
                'STRICT_PARSING': True
            }
        )

        if matches:
            for match in matches:
                date_obj, start, end = match
                results.append(ExtractedEntity(
                    type="date",
                    value=date_obj.strftime('%Y-%m-%d'),
                    confidence=0.9,
                    start_pos=start,
                    end_pos=end,
                    source="date_parser"
                ))

        return results

class SmartEntityExtractor:
    """Smart entity extractor for CSPE documents."""

    def __init__(self):
        self.date_extractor = SmartDateExtractor()

    def extract_dates(self, text: str) -> List[ExtractedEntity]:
        """Extract dates using SmartDateExtractor."""
        return self.date_extractor.extract_dates(text)

    def extract_amounts(self, text: str) -> List[ExtractedEntity]:
        """Extract amounts from text."""
        amounts = []

        # French format: 1 234,56 €
        for match in re.finditer(r'(\d{1,3}(?:\s\d{3})*,\d{2})\s*[€$]?', text):
            try:
                amount_str = match.group(1).replace(' ', '').replace(',', '.')
                amounts.append(ExtractedEntity(
                    type="amount",
                    value=amount_str,
                    confidence=0.9,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    source="regex"
                ))
            except Exception as e:
                print(f"Error extracting amount: {e}")

        # International format: 1,234.56 €
        for match in re.finditer(r'(\d{1,3}(?:,\d{3})*\.\d{2})\s*[€$]?', text):
            try:
                amount_str = match.group(1).replace(',', '')
                amounts.append(ExtractedEntity(
                    type="amount",
                    value=amount_str,
                    confidence=0.9,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    source="regex"
                ))
            except Exception as e:
                print(f"Error extracting amount: {e}")

        return amounts

class DocumentProcessor:
    """CSPE document processor."""

    def __init__(self):
        self.entity_extractor = SmartEntityExtractor()

    def extract_dates(self, text: str) -> List[ExtractedEntity]:
        """Extract dates from text using dateparser."""
        results = []

        try:
            # First, try with French text format
            fr_pattern = r'(\d{1,2}(?:er)?\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})'
            for match in re.finditer(fr_pattern, text, re.IGNORECASE):
                date_str = match.group(1)
                try:
                    date_obj = datetime.strptime(date_str, '%d %B %Y')
                    results.append(ExtractedEntity(
                        type="date",
                        value=date_obj.strftime('%Y-%m-%d'),
                        confidence=0.9,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        source="date_parser"
                    ))
                except ValueError:
                    pass

            # Then, try with dateparser for other formats
            matches = search_dates(
                text,
                languages=['fr'],
                settings={
                    'PREFER_DAY_OF_MONTH': 'first',
                    'DATE_ORDER': 'DMY',
                    'STRICT_PARSING': True
                }
            )

            if matches:
                for date_str, date_obj in matches:
                    # Avoid duplicates
                    if not any(r.value == date_obj.strftime('%Y-%m-%d') for r in results):
                        start = text.find(date_str)
                        if start != -1:
                            results.append(ExtractedEntity(
                                type="date",
                                value=date_obj.strftime('%Y-%m-%d'),
                                confidence=0.9,
                                start_pos=start,
                                end_pos=start + len(date_str),
                                source="date_parser"
                            ))

        except Exception as e:
            print(f"Error extracting dates: {e}")

        return results

    def check_period(self, text: str) -> Dict:
        """Check if a valid period is mentioned."""
        patterns = [
            r'(?:année|exercice)\s+(\d{4})',
            r'période\s+(\d{4}(?:\s*-\s*\d{2,4})?)',
            r'(?:du|depuis)\s+\d{1,2}/\d{4}(?:\s*au\s+\d{1,2}/\d{4})?'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {
                    "is_valid": True,
                    "message": "Valid period detected",
                    "period": match.group(0)
                }

        return {
            "is_valid": False,
            "message": "No valid period detected",
            "period": None
        }

    def check_delay(self, text: str, test_mode: bool = True) -> Dict:
        """Check if the appeal deadline is respected."""
        try:
            dates = self.extract_dates(text)
            if not dates:
                return {
                    "is_valid": False,
                    "message": "No date found",
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
                    "message": "No valid date found",
                    "is_on_time": False
                }

            dated_entities.sort(reverse=True, key=lambda x: x[0])
            latest_date_dt, latest_date_entity = dated_entities[0]

            today = datetime.strptime("2023-03-01", "%Y-%m-%d") if test_mode else datetime.now()
            delta = (today - latest_date_dt).days
            is_on_time = delta <= 60

            return {
                "is_valid": is_on_time,
                "message": "Deadline respected" if is_on_time else "Deadline exceeded",
                "decision_date": latest_date_entity.value,
                "days_since_decision": delta,
                "is_on_time": is_on_time
            }
        except Exception as e:
            return {
                "is_valid": False,
                "message": f"Error: {str(e)}",
                "is_on_time": False
            }

    def test_check_delay(self):
        """Test delay check functionality."""
        # Test avec une date dans la limite des 60 jours (en utilisant test_mode=True)
        text = "Décision du 01/01/2023"
        result = self.processor.check_delay(text, test_mode=True)
        assert result["is_on_time"] is True, f"Le délai devrait être respecté pour la date du 01/01/2023"
        assert result["days_since_decision"] == 59  # Du 01/01/2023 au 01/03/2023

        # Test avec une date en dehors de la limite
        text = "Décision du 25/12/2022"
        result = self.processor.check_delay(text, test_mode=True)
        assert result["is_on_time"] is False, "Le délai ne devrait pas être respecté pour la date du 25/12/2022"
        assert result["days_since_decision"] == 66  # Du 25/12/2022 au 01/03/2023

# Example usage
if __name__ == "__main__":
    processor = DocumentProcessor()
    text = "Le 1er janvier 2023, une réunion a eu lieu. La prochaine est prévue pour 01/02/2023."
    dates = processor.extract_dates(text)
    for date in dates:
        print(f"Date: {date.value}, Confidence: {date.confidence}")

    amounts_text = "Les montants sont 1 234,56 € et 1,234.56 €."
    amounts = processor.entity_extractor.extract_amounts(amounts_text)
    for amount in amounts:
        print(f"Amount: {amount.value}")
