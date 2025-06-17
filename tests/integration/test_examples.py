"""
Tests d'intégration pour le classifieur CSPE avec les dossiers de test.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import re

class IntegrationTest:
    """Classe pour exécuter les tests d'intégration sur les dossiers de test."""
    
    def __init__(self):
        # Chemin vers le répertoire racine du projet
        self.base_dir = Path(__file__).resolve().parent.parent.parent / "test_cases"
        self.results = []
        self.case_types = {
            'RECEVABLE': 'Cas recevable',
            'IRRECEVABLE_DELAI_DEPASSE': 'Délai de réclamation dépassé',
            'IRRECEVABLE_PERIODE_NON_COUVERTE': 'Période non couverte (2009-2015)',
            'IRRECEVABLE_PRESCRIPTION': 'Prescription quadriennale dépassée',
            'IRRECEVABLE_REPERCUSSION_CLIENT': 'CSPE répercutée au client final',
            'CAS_COMPLEXE': 'Cas complexe nécessitant expertise',
            'FUSION_ACQUISITION': 'Cas de fusion-acquisition'
        }

    def load_document(self, file_path: Path) -> str:
        """
        Charge le contenu d'un fichier texte avec gestion d'erreur d'encodage.
        """
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                return f.read()
        except Exception as e:
            print(f"Erreur lors de la lecture de {file_path}: {e}")
            return ""

    def detect_case_type(self, dir_name: str) -> str:
        """Détecte le type de cas à partir du nom du dossier."""
        for key, value in self.case_types.items():
            if key in dir_name.upper():
                return value
        return "Type inconnu"

    def extract_claim_details(self, text: str) -> Dict[str, Any]:
        """Extrait les détails de la réclamation depuis le texte."""
        details = {
            'montant': None,
            'periode': None,
            'date_reclamation': None
        }
        
        # Extraction du montant
        montant_match = re.search(r'(\d{1,3}(?:[\s\u202F]?\d{3})*(?:,\d+)\s*€)', text)
        if montant_match:
            details['montant'] = montant_match.group(1)
            
        # Extraction de la période
        periode_match = re.search(r'(?:période|année[s]?)\s*:?\s*(\d{4}(?:\s*[-/]\s*\d{4}|\s*à\s*\d{4})?)', 
                                text, re.IGNORECASE)
        if not periode_match:
            periode_match = re.search(r'20\d{2}.*20\d{2}', text)
        if periode_match:
            details['periode'] = periode_match.group(1) if periode_match.group(1) else periode_match.group(0)
            
        # Extraction de la date de réclamation
        date_match = re.search(r'(?:le\s+)?(\d{1,2}\s+[a-zéû]+\s+\d{4})', text, re.IGNORECASE)
        if date_match:
            details['date_reclamation'] = date_match.group(1)
            
        return details

    def process_directory(self, dir_path: Path) -> Dict[str, Any]:
        """Traite tous les fichiers d'un répertoire de test."""
        if not dir_path.is_dir():
            print(f"Le répertoire {dir_path} n'existe pas")
            return {}
            
        case_type = self.detect_case_type(dir_path.name)
        print(f"\nTraitement du dossier : {dir_path.name} - {case_type}")
        
        result = {
            'dossier': dir_path.name,
            'type_cas': case_type,
            'documents': [],
            'date_analyse': datetime.now().isoformat(),
            'statistiques': {
                'total_documents': 0,
                'documents_traites': 0,
                'erreurs': 0
            },
            'extractions': {}
        }
        
        # Traiter chaque fichier du dossier
        for file_path in sorted(dir_path.glob('*.*')):
            if file_path.suffix.lower() in ['.txt', '.pdf', '.doc', '.docx']:
                result['statistiques']['total_documents'] += 1
                try:
                    content = self.load_document(file_path)
                    if content:
                        doc_result = {
                            'fichier': file_path.name,
                            'taille_ko': file_path.stat().st_size / 1024,
                            'extrait': content[:500] + ('...' if len(content) > 500 else '')
                        }
                        
                        # Extraction des informations si c'est le fichier de réclamation
                        if 'reclamation' in file_path.name.lower() or 'réclamation' in file_path.name.lower():
                            result['extractions'] = self.extract_claim_details(content)
                            
                        result['documents'].append(doc_result)
                        result['statistiques']['documents_traites'] += 1
                except Exception as e:
                    print(f"Erreur lors du traitement de {file_path}: {e}")
                    result['statistiques']['erreurs'] += 1
        
        # Évaluation automatique basée sur le type de cas
        self.evaluate_case(result)
        
        return result
    
    def evaluate_case(self, case: Dict[str, Any]) -> None:
        """Évalue automatiquement le cas en fonction de son type."""
        case_type = case['type_cas']
        
        # Initialisation du résultat
        case['evaluation'] = {
            'decision': 'À instruire',
            'critères': {},
            'commentaire': ''
        }
        
        # Logique d'évaluation basée sur le type de cas
        if 'recevable' in case_type.lower():
            case['evaluation']['decision'] = 'Recevable'
            case['evaluation']['commentaire'] = 'Cas conforme aux critères de recevabilité'
            
        elif 'délai dépassé' in case_type.lower():
            case['evaluation']['decision'] = 'Irrecevable'
            case['evaluation']['commentaire'] = 'Délai de réclamation dépassé (18 mois après la période de consommation)'
            
        elif 'période non couverte' in case_type.lower():
            case['evaluation']['decision'] = 'Irrecevable'
            case['evaluation']['commentaire'] = 'Période de consommation en dehors de la plage 2009-2015'
            
        elif 'prescription' in case_type.lower():
            case['evaluation']['decision'] = 'Irrecevable'
            case['evaluation']['commentaire'] = 'Prescription quadriennale dépassée'
            
        elif 'répercussion client' in case_type.lower():
            case['evaluation']['decision'] = 'Irrecevable'
            case['evaluation']['commentaire'] = 'La CSPE a été répercutée sur le client final'
            
        elif 'complexe' in case_type.lower() or 'fusion' in case_type.lower():
            case['evaluation']['decision'] = 'À expertiser'
            case['evaluation']['commentaire'] = 'Cas complexe nécessitant une analyse approfondie'
    
    def run_tests(self) -> List[Dict[str, Any]]:
        """Exécute les tests sur tous les dossiers de test."""
        print(f"Démarrage des tests d'intégration dans {self.base_dir}")
        
        # Créer le répertoire de sortie s'il n'existe pas
        output_dir = Path(__file__).parent.parent.parent / 'reports'
        output_dir.mkdir(exist_ok=True)
        
        # Parcourir tous les dossiers de test
        for case_dir in sorted(self.base_dir.glob('*')):
            if case_dir.is_dir():
                result = self.process_directory(case_dir)
                if result:
                    self.results.append(result)
        
        # Générer les rapports
        self.generate_reports(output_dir)
        
        return self.results
    
    def generate_reports(self, output_dir: Path) -> None:
        """Génère les rapports de test."""
        # Rapport JSON complet
        json_report = {
            'date_generation': datetime.now().isoformat(),
            'nombre_cas_traites': len(self.results),
            'resultats': self.results
        }
        
        with open(output_dir / 'integration_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(json_report, f, ensure_ascii=False, indent=2)
        
        # Rapport CSV sommaire
        csv_lines = [
            'Dossier;Type de cas;Décision;Documents;Erreurs;Montant;Période;Date réclamation',
        ]
        
        for result in self.results:
            extractions = result.get('extractions', {})
            csv_lines.append(
                f"{result['dossier']};"
                f"{result['type_cas']};"
                f"{result['evaluation']['decision']};"
                f"{result['statistiques']['documents_traites']};"
                f"{result['statistiques']['erreurs']};"
                f"{extractions.get('montant', 'N/A')};"
                f"{extractions.get('periode', 'N/A')};"
                f"{extractions.get('date_reclamation', 'N/A')}"
            )
        
        with open(output_dir / 'integration_test_summary.csv', 'w', encoding='utf-8-sig') as f:
            f.write('\n'.join(csv_lines))
        
        print(f"\nRapports générés dans {output_dir}:")
        print(f"- integration_test_results.json : Rapport complet au format JSON")
        print(f"- integration_test_summary.csv : Synthèse au format CSV")

def main() -> int:
    """Fonction principale pour exécuter les tests d'intégration."""
    tester = IntegrationTest()
    results = tester.run_tests()
    
    # Afficher un résumé
    print("\nRésumé des tests :")
    for result in results:
        print(f"\n{result['dossier']} - {result['type_cas']} : {result['evaluation']['decision']}")
        print(f"  Documents: {result['statistiques']['documents_traites']}/{result['statistiques']['total_documents']}")
        print(f"  Décision: {result['evaluation']['decision']}")
        print(f"  Commentaire: {result['evaluation']['commentaire']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())