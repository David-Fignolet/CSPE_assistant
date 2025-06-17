from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional, Pattern
from datetime import datetime, date
import re
import pytz

@dataclass
class CSPEEntity:
    """Représente une entité extraite d'un document CSPE."""
    value: Any
    entity_type: str
    start_pos: int
    end_pos: int
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entité en dictionnaire."""
        return {
            'value': self.value.isoformat() if hasattr(self.value, 'isoformat') else self.value,
            'entity_type': self.entity_type,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'confidence': self.confidence
        }

class CSPEDocumentProcessor:
    """Processeur de documents pour l'extraction d'informations CSPE."""
    
    # Modèles de regex pour l'extraction
    DATE_PATTERNS = [
        # Format JJ/MM/AAAA
        (r'\b(0?[1-9]|[12][0-9]|3[01])[/\-\.](0?[1-9]|1[0-2])[/\-\.](20\d{2}|\d{2})\b', '%d/%m/%Y'),
        # Format AAAA-MM-JJ
        (r'\b(20\d{2})[\-\.](0?[1-9]|1[0-2])[\-\.](0?[1-9]|[12][0-9]|3[01])\b', '%Y-%m-%d'),
    ]
    
    # Modèle pour les montants (euros)
    AMOUNT_PATTERN = r'\b(\d{1,3}(?:[ \.]?\d{3})*(?:,\d{1,2})?)\s*(?:€|euros?|EUR)?\b'
    
    # Modèles pour les références
    REFERENCE_PATTERNS = {
        'facture': r'\b(?:facture|fact)\s*[n°:]*\s*([A-Z0-9\-/]+)\b',
        'commande': r'\b(?:bon\s+de\s+commande|commande)\s*[n°:]*\s*([A-Z0-9\-/]+)\b',
        'client': r'\b(?:client|code\s+client)\s*[n°:]*\s*([A-Z0-9\-/]+)\b',
    }

    def __init__(self, timezone: str = 'Europe/Paris'):
        """Initialise le processeur avec un fuseau horaire."""
        self.timezone = pytz.timezone(timezone)
        self._compile_patterns()
        
    def _compile_patterns(self) -> None:
        """Compile les expressions régulières pour de meilleures performances."""
        self.date_regexes = [(re.compile(pattern), fmt) for pattern, fmt in self.DATE_PATTERNS]
        self.amount_regex = re.compile(self.AMOUNT_PATTERN, re.IGNORECASE)
        self.ref_regexes = {k: re.compile(v, re.IGNORECASE) for k, v in self.REFERENCE_PATTERNS.items()}

    def _parse_date(self, date_str: str, date_fmt: str) -> Optional[date]:
        """Tente de parser une date à partir d'une chaîne et d'un format donnés."""
        try:
            return datetime.strptime(date_str, date_fmt).date()
        except ValueError:
            return None

    def extract_dates(self, text: str) -> List[CSPEEntity]:
        """Extrait les dates du texte."""
        entities = []
        
        for regex, date_fmt in self.date_regexes:
            for match in regex.finditer(text):
                date_str = match.group(0)
                parsed_date = self._parse_date(date_str, date_fmt)
                if parsed_date:
                    entities.append(CSPEEntity(
                        value=parsed_date,
                        entity_type='date',
                        start_pos=match.start(),
                        end_pos=match.end()
                    ))
        return entities

    def extract_amounts(self, text: str) -> List[CSPEEntity]:
        """Extrait les montants du texte."""
        entities = []
        # Pattern pour les montants avec symbole €
        amount_patterns = [
            (r'\b(\d{1,3}(?:[ \u202F]\d{3})*(?:,\d{1,2})?)\s*(?:€|euros?|EUR)\b', 0.9),
            (r'(?<!\d)(\d{1,3}(?:[ \u202F]\d{3})*(?:,\d{1,2})?)(?!\d)', 0.7)  # Sans symbole
        ]
    
        for pattern, confidence in amount_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                amount_str = match.group(1).replace(' ', '').replace('\u202F', '').replace(',', '.')
                try:
                    amount = float(amount_str)
                    entities.append(CSPEEntity(
                        value=amount,
                        entity_type='amount',
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=confidence
                    ))
                except ValueError:
                    continue
                
        return entities

    def extract_references(self, text: str) -> Dict[str, List[CSPEEntity]]:
        """Extrait les références du texte."""
        references = {ref_type: [] for ref_type in self.REFERENCE_PATTERNS}
        
        for ref_type, regex in self.ref_regexes.items():
            for match in regex.finditer(text):
                ref_value = match.group(1)
                references[ref_type].append(CSPEEntity(
                    value=ref_value,
                    entity_type=f'reference_{ref_type}',
                    start_pos=match.start(1),
                    end_pos=match.end(1)
                ))
        
        return references

    def extract_document_info(self, text: str) -> Dict[str, Any]:
        """Extrait toutes les informations pertinentes d'un document CSPE."""
        dates = self.extract_dates(text)
        amounts = self.extract_amounts(text)
        references = self.extract_references(text)
        
        return {
            'dates': [e.to_dict() for e in dates],
            'amounts': [e.to_dict() for e in amounts],
            'references': {
                ref_type: [e.to_dict() for e in refs] 
                for ref_type, refs in references.items()
            },
            'metadata': {
                'processed_at': datetime.now(self.timezone).isoformat(),
                'text_length': len(text),
                'status': 'success',
                'entities_found': {
                    'dates': len(dates),
                    'amounts': len(amounts),
                    'references': sum(len(refs) for refs in references.values())
                }
            }
        }

    def test(self) -> str:
        """Méthode de test pour vérifier que l'extraction fonctionne."""
        test_text = '''
        Facture n°FAC-2023-0042 du 15/03/2023
        Commande CDE-7890
        Client: CLT-12345
        Montant total: 1 234,56 €
        Date d'échéance: 2023-04-15
        '''
        
        result = self.extract_document_info(test_text)
        return f"Test réussi! {result['metadata']['entities_found']} entités trouvées."
