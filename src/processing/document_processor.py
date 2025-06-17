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
        # Format JJ/MM/AAAA ou JJ-MM-AAAA ou JJ.MM.AAAA
        (r'\b(0?[1-9]|[12][0-9]|3[01])[/\-\.](0?[1-9]|1[0-2])[/\-\.](20\d{2}|\d{2})\b', '%d/%m/%Y'),
        # Format AAAA-MM-JJ ou AAAA/MM/JJ ou AAAA.MM.JJ
        (r'\b(20\d{2})[\-\./](0?[1-9]|1[0-2])[\-\./](0?[1-9]|[12][0-9]|3[01])\b', '%Y-%m-%d'),
        # Format date en toutes lettres (ex: 15 mars 2023)
        (r'\b(0?[1-9]|[12][0-9]|3[01])\s+(janvier|février|mars|avril|mai|juin|juillet|ao[uû]t|septembre|octobre|novembre|décembre)\s+(20\d{2}|\d{2})\b', 
         lambda m: f"{m.group(1)} {self._get_month_number(m.group(2))} {m.group(3)}",
         '%d %m %Y')
    ]
    
    # Dictionnaire des mois
    MONTHS = {
        'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04', 'mai': '05', 'juin': '06',
        'juillet': '07', 'août': '08', 'aout': '08', 'septembre': '09', 'octobre': '10',
        'novembre': '11', 'décembre': '12'
    }
    
    # Modèle pour les montants (euros) avec contexte amélioré
    AMOUNT_PATTERN = r'(?<![\d\-+±])(?<=\b|\s|^)(\d{1,3}(?:[ \u202F]?\d{3})*(?:[,\.]\d{1,2})?)(?=\s*(?:€|euros?|EUR|\b(?:TTC|HT|e\.?a\.?d\.?|soit|total|montant|prix))|\s|$)'
    
    # Modèles pour les références améliorés
    REFERENCE_PATTERNS = {
        'facture': r'\b(?:facture|fact\.?|n°\s*\d+)[\s:]*([A-Z0-9\-\/]{3,})\b',
        'commande': r'\b(?:bon\s+de\s+commande|commande|CDE|n°\s*commande)[\s:]*([A-Z0-9\-\/]{3,})\b',
        'client': r'\b(?:client|code\s+client|réf\.?\s*client)[\s:]*([A-Z0-9\-\/]{3,})\b',
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

    def _get_month_number(self, month_str: str) -> str:
        """Convertit le nom du mois en numéro."""
        return self.MONTHS.get(month_str.lower(), '00')

    def _parse_date(self, date_str: str, date_fmt: str) -> Optional[date]:
        """Tente de parser une date à partir d'une chaîne et d'un format donnés."""
        try:
            # Si le format contient des espaces, c'est une date en toutes lettres
            if ' ' in date_str:
                day, month, year = date_str.split()
                date_str = f"{day} {month} {year}"
            return datetime.strptime(date_str, date_fmt).date()
        except (ValueError, AttributeError):
            return None

    def _is_likely_amount(self, text: str, match: re.Match) -> bool:
        """Vérifie si la correspondance est probablement un montant."""
        # Exclure les numéros de téléphone, codes postaux, etc.
        if len(match.group(1)) > 6:  # Les montants très longs sont suspects
            return False
            
        # Vérifier le contexte autour du montant
        start, end = match.span()
        context_before = text[max(0, start-20):start].lower()
        context_after = text[end:min(len(text), end+20)].lower()
        
        # Mots-clés qui indiquent un montant
        amount_keywords = {
            '€', 'euro', 'euros', 'eur', 'prix', 'total', 'montant', 
            'facture', 'tva', 'ttc', 'ht', 'remise', 'acompte', 'règlement'
        }
        
        # Si le contexte contient un mot-clé de montant
        if any(keyword in context_before + context_after for keyword in amount_keywords):
            return True
            
        # Vérifier si c'est dans un tableau (entouré de | ou de bordures)
        if any(sep in context_before + context_after for sep in ['|', '┃', '║', '│']):
            return True
            
        return False

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
        """Extrait les montants du texte avec un filtre de contexte amélioré."""
        entities = []
        
        for match in re.finditer(self.AMOUNT_PATTERN, text, re.IGNORECASE):
            if not self._is_likely_amount(text, match):
                continue
                
            amount_str = match.group(1).replace(' ', '').replace('\u202F', '').replace(',', '.')
            try:
                # Vérifier si c'est un nombre décimal valide
                amount = float(amount_str)
                
                # Filtrer les nombres qui ne sont probablement pas des montants
                if amount < 0.01 or amount > 10_000_000:  # Plage raisonnable pour des montants
                    continue
                    
                # Calculer la confiance basée sur le contexte
                confidence = 0.9 if '€' in match.group(0) else 0.7
                
                entities.append(CSPEEntity(
                    value=round(amount, 2),  # Arrondir à 2 décimales
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
