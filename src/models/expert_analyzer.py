from datetime import datetime, date, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import re
import json
from dateutil.parser import parse as parse_date

class Decision(Enum):
    RECEVABLE = "recevable"
    IRRECEVABLE = "irrecevable"
    A_COMPLETER = "à compléter"

class CSPEExpertAnalyzer:
    """
    Analyseur expert des dossiers CSPE selon les critères du Conseil d'État.
    """
    
    def __init__(self, llm_client=None):
        """
        Initialise l'analyseur expert.
        
        Args:
            llm_client: Client pour les appels au modèle de langage (optionnel)
        """
        self.llm = llm_client
        
        # Expressions régulières pour l'extraction des entités
        self.date_pattern = re.compile(
            r'\b(0?[1-9]|[12][0-9]|3[01])[/\-](0?[1-9]|1[0-2])[/\-](20\d{2}|\d{2})\b|'  # DD/MM/YYYY ou DD-MM-YYYY
            r'\b(20\d{2})[/\-](0?[1-9]|1[0-2])[/\-](0?[1-9]|[12][0-9]|3[01])\b'  # YYYY-MM-DD ou YYYY/MM/DD
        )
        self.amount_pattern = re.compile(
            r'\b(\d{1,3}(?:[\s.]?\d{3})*(?:[.,]\d{1,2})?)\s*(?:€|euros?|EUR)?\b',
            re.IGNORECASE
        )
        self.siret_pattern = re.compile(r'\b\d{3}[ .]?\d{3}[ .]?\d{3}[ .]?\d{5}\b')
    
    def analyze_file(self, file_path: str) -> Dict:
        """
        Analyse un fichier et retourne un rapport d'analyse.
        
        Args:
            file_path: Chemin vers le fichier à analyser
            
        Returns:
            Dictionnaire contenant le rapport d'analyse
        """
        try:
            # Lire le contenu du fichier
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Extraire les entités clés
            extracted_data = self._extract_entities(content)
            
            # Évaluer les critères
            criteria = self._evaluate_criteria(extracted_data)
            
            # Générer le rapport
            report = self._generate_report(criteria, extracted_data)
            
            return report
            
        except Exception as e:
            return {
                'error': f"Erreur lors de l'analyse du fichier : {str(e)}",
                'file': str(file_path)
            }
    
    def _extract_entities(self, text: str) -> Dict:
        """
        Extrait les entités clés du texte.
        
        Args:
            text: Texte à analyser
            
        Returns:
            Dictionnaire contenant les entités extraites
        """
        # Extraire les dates
        dates = []
        for match in self.date_pattern.finditer(text):
            try:
                date_str = match.group()
                # Essayer de parser la date
                date_obj = parse_date(date_str, dayfirst=True, yearfirst=False, fuzzy=True)
                dates.append(date_obj.strftime('%d/%m/%Y'))
            except (ValueError, OverflowError):
                continue
        
        # Extraire les montants
        amounts = []
        for match in self.amount_pattern.finditer(text):
            try:
                amount_str = match.group(1).replace(' ', '').replace(',', '.')
                amount = float(amount_str)
                amounts.append(amount)
            except (ValueError, AttributeError):
                continue
        
        # Extraire les SIRET
        sirets = [match.group().replace(' ', '') for match in self.siret_pattern.finditer(text)]
        
        return {
            'dates': sorted(list(set(dates))),
            'montants': sorted(list(set(amounts))),
            'sirets': sirets,
            'text_length': len(text),
            'extract': text[:500] + '...' if len(text) > 500 else text
        }
    
    def _evaluate_criteria(self, data: Dict) -> Dict:
        """
        Évalue les critères d'éligibilité CSPE.
        
        Args:
            data: Données extraites du document
            
        Returns:
            Dictionnaire contenant l'évaluation des critères
        """
        return {
            'delai_reclamation': self._check_delai_reclamation(data),
            'periode_couverte': self._check_periode_couverte(data),
            'prescription_quadriennale': self._check_prescription_quadriennale(data),
            'repercussion_client_final': self._check_repercussion_client_final(data)
        }
    
    def _check_delai_reclamation(self, data: Dict) -> Dict:
        """
        Vérifie si la réclamation a été faite dans les délais (avant le 31/12/N+1).
        
        Args:
            data: Données extraites
            
        Returns:
            Dictionnaire contenant la décision et les détails
        """
        dates = [datetime.strptime(d, '%d/%m/%Y').date() for d in data.get('dates', [])]
        
        if not dates:
            return {
                'decision': Decision.A_COMPLETER,
                'details': 'Aucune date trouvée dans le document',
                'confidence': 0.0
            }
        
        # Prendre la date la plus récente comme date de référence
        latest_date = max(dates)
        annee_reference = latest_date.year
        delai_limite = date(annee_reference + 1, 12, 31)
        
        # Vérifier si on est dans les délais
        est_dans_les_delais = latest_date <= delai_limite
        
        return {
            'decision': Decision.RECEVABLE if est_dans_les_delais else Decision.IRRECEVABLE,
            'details': f"Date de référence: {latest_date.strftime('%d/%m/%Y')}, "
                      f"Délai: 31/12/{annee_reference + 1}",
            'confidence': 0.9
        }
    
    def _check_periode_couverte(self, data: Dict) -> Dict:
        """
        Vérifie si la période est couverte (2009-2015).
        
        Args:
            data: Données extraites
            
        Returns:
            Dictionnaire contenant la décision et les détails
        """
        annees = []
        for d in data.get('dates', []):
            try:
                dt = datetime.strptime(d, '%d/%m/%Y')
                annees.append(dt.year)
            except (ValueError, TypeError):
                continue
        
        if not annees:
            return {
                'decision': Decision.A_COMPLETER,
                'details': 'Aucune date valide trouvée',
                'confidence': 0.0
            }
        
        # Vérifier si au moins une année est dans la période 2009-2015
        annees_dans_periode = [a for a in annees if 2009 <= a <= 2015]
        
        if not annees_dans_periode:
            return {
                'decision': Decision.IRRECEVABLE,
                'details': f'Aucune date dans la période 2009-2015. Périodes trouvées: {min(annees)}-{max(annees)}',
                'confidence': 0.95
            }
        
        return {
            'decision': Decision.RECEVABLE,
            'details': f'Période couverte: {min(annees_dans_periode)}-{max(annees_dans_periode)}',
            'confidence': 0.9
        }
    
    def _check_prescription_quadriennale(self, data: Dict) -> Dict:
        """
        Vérifie si la réclamation est prescrite (délai de 4 ans).
        
        Args:
            data: Données extraites
            
        Returns:
            Dictionnaire contenant la décision et les détails
        """
        dates = [datetime.strptime(d, '%d/%m/%Y').date() for d in data.get('dates', [])]
        
        if not dates:
            return {
                'decision': Decision.A_COMPLETER,
                'details': 'Aucune date trouvée pour vérifier la prescription',
                'confidence': 0.0
            }
        
        # Prendre la date la plus ancienne comme date de référence
        oldest_date = min(dates)
        date_prescription = oldest_date + timedelta(days=4*365)  # Approximation simple
        
        # Vérifier si le délai de prescription est dépassé
        est_prescrit = date.today() > date_prescription
        
        return {
            'decision': Decision.IRRECEVABLE if est_prescrit else Decision.RECEVABLE,
            'details': f'Date de référence: {oldest_date.strftime("%d/%m/%Y")}, Prescription: {date_prescription.strftime("%d/%m/%Y")}',
            'confidence': 0.85
        }
    
    def _check_repercussion_client_final(self, data: Dict) -> Dict:
        """
        Vérifie si la CSPE a été répercutée sur le client final.
        
        Args:
            data: Données extraites
            
        Returns:
            Dictionnaire contenant la décision et les détails
        """
        # Cette analyse nécessiterait une analyse sémantique plus poussée
        # On retourne une décision neutre par défaut
        return {
            'decision': Decision.A_COMPLETER,
            'details': 'Analyse de la répercussion non implémentée',
            'confidence': 0.5
        }
    
    def _generate_report(self, criteria: Dict, extracted_data: Dict) -> Dict:
        """
        Génère un rapport d'analyse à partir des critères évalués.
        
        Args:
            criteria: Résultats de l'évaluation des critères
            extracted_data: Données extraites du document
            
        Returns:
            Dictionnaire contenant le rapport complet
        """
        # Déterminer la décision globale
        decisions = [c['decision'] for c in criteria.values()]
        
        if Decision.IRRECEVABLE in decisions:
            decision_globale = Decision.IRRECEVABLE
        elif all(d == Decision.RECEVABLE for d in decisions):
            decision_globale = Decision.RECEVABLE
        else:
            decision_globale = Decision.A_COMPLETER
        
        return {
            'decision_globale': decision_globale.value,
            'criteria': {
                'delai_reclamation': {
                    'decision': criteria['delai_reclamation']['decision'].value,
                    'details': criteria['delai_reclamation']['details'],
                    'confiance': criteria['delai_reclamation'].get('confidence', 0.0)
                },
                'periode_couverte': {
                    'decision': criteria['periode_couverte']['decision'].value,
                    'details': criteria['periode_couverte']['details'],
                    'confiance': criteria['periode_couverte'].get('confidence', 0.0)
                },
                'prescription_quadriennale': {
                    'decision': criteria['prescription_quadriennale']['decision'].value,
                    'details': criteria['prescription_quadriennale']['details'],
                    'confiance': criteria['prescription_quadriennale'].get('confidence', 0.0)
                },
                'repercussion_client_final': {
                    'decision': criteria['repercussion_client_final']['decision'].value,
                    'details': criteria['repercussion_client_final']['details'],
                    'confiance': criteria['repercussion_client_final'].get('confidence', 0.0)
                }
            },
            'extracted_data': {
                'dates': extracted_data.get('dates', []),
                'montants': extracted_data.get('montants', []),
                'sirets': extracted_data.get('sirets', [])
            },
            'metadata': {
                'date_analyse': datetime.now().isoformat(),
                'version': '1.0.0'
            }
        }

# Exemple d'utilisation
if __name__ == "__main__":
    analyzer = CSPEExpertAnalyzer()
    result = analyzer.analyze_file("chemin/vers/document.txt")
    print(json.dumps(result, indent=2, ensure_ascii=False))
