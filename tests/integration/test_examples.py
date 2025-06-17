"""
Tests d'intégration pour le classifieur CSPE avec des exemples concrets.
"""

import sys
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

class IntegrationTest:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent / "examples"
        self.results = []

    def load_document(self, file_path: Path) -> str:
        """
        Charge le contenu d'un fichier texte.
        
        Args:
            file_path: Chemin vers le fichier à charger
            
        Returns:
            Contenu du fichier en tant que chaîne de caractères
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception as e:
            print(f"Erreur lors de la lecture de {file_path}: {e}")
            return ""

    def process_directory(self, dir_path: Path) -> Dict[str, Any]:
        """
        Traite tous les fichiers texte d'un répertoire.
        
        Args:
            dir_path: Chemin vers le répertoire à traiter
            
        Returns:
            Dictionnaire contenant les résultats pour ce répertoire
        """
        dir_results = {
            'dossier': dir_path.name,
            'type_cas': self.detect_case_type(dir_path.name),
            'documents': [],
            'date_analyse': datetime.now().isoformat(),
            'statistiques': {
                'total_documents': 0,
                'documents_traites': 0,
                'erreurs': 0
            }
        }
        
        # Parcourir tous les fichiers texte du dossier
        for file_path in dir_path.glob('*.txt'):
            dir_results['statistiques']['total_documents'] += 1
            
            try:
                # Charger le document
                content = self.load_document(file_path)
                if not content.strip():
                    print(f"  - {file_path.name}: Fichier vide ou erreur de lecture")
                    continue
                
                # Pour l'instant, on se contente d'afficher les premières lignes
                preview = ' '.join(content.split()[:20]) + '...' if len(content.split()) > 20 else content
                print(f"  - {file_path.name}: {preview}")
                
                # TODO: Ajouter la classification ici
                
                dir_results['statistiques']['documents_traites'] += 1
                
            except Exception as e:
                print(f"  - {file_path.name}: ERREUR - {str(e)}")
                dir_results['statistiques']['erreurs'] += 1
        
        return dir_results
    
    def detect_case_type(self, dir_name: str) -> str:
        # TODO: Implémenter la détection du type de cas
        return "Type de cas inconnu"

    def run_tests(self):
        """Exécute les tests sur tous les dossiers d'exemples."""
        print(f"Démarrage des tests d'intégration dans {self.base_dir}")
        
        # Vérifier que le répertoire de base existe
        if not self.base_dir.exists():
            print(f"Erreur: Le répertoire {self.base_dir} n'existe pas.")
            return
            
        # Créer le répertoire de sortie
        output_dir = Path(__file__).resolve().parent / "integration_results"
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Parcourir les sous-dossiers
        for dir_path in sorted(self.base_dir.glob('*')):
            if dir_path.is_dir():
                print(f"\nTraitement du dossier: {dir_path.name}")
                print(f"Type détecté: {self.detect_case_type(dir_path.name)}")
                
                # Traiter le dossier
                result = self.process_directory(dir_path)
                self.results.append(result)
                
                # Sauvegarder les résultats pour ce dossier
                output_file = output_dir / f"resultat_{dir_path.name}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"  Résultats sauvegardés dans {output_file}")
                
        print("\nTraitement terminé.")

def main():
    test = IntegrationTest()
    test.run_tests()
    return 0

if __name__ == "__main__":
    sys.exit(main())