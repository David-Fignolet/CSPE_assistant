"""
Script d'import par lot pour le classifieur CSPE.

Ce script permet d'importer des documents depuis un dossier local ou une archive ZIP,
et de générer des rapports de classification.

Exemples d'utilisation:
    # Importer depuis un dossier
    python -m src.batch_import --input D:\chemin\vers\dossier --output rapports
    
    # Importer depuis une archive ZIP
    python -m src.batch_import --input archive.zip --output rapports --zip
    
    # Afficher l'aide
    python -m src.batch_import --help
"""

import sys
import os
import zipfile
import argparse
import tempfile
import shutil
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

# Ajout du répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Avertissement: pandas n'est pas installé. Un rapport simplifié sera généré.")

try:
    from models.classifier import CSPEClassifier
except ImportError as e:
    print(f"Erreur: Impossible d'importer CSPEClassifier: {e}")
    print("Assurez-vous que le module 'models' est dans le PYTHONPATH")
    sys.exit(1)

class BatchImporter:
    """Classe pour l'import par lot de documents."""
    
    def __init__(self):
        """Initialise l'importateur avec le classifieur."""
        self.classifier = CSPEClassifier()
        self.results: List[Dict[str, Any]] = []
    
    def process_file(self, file_path: Path, category: str = None) -> Optional[Dict[str, Any]]:
        """Traite un fichier et retourne le résultat de la classification."""
        try:
            # Lire le contenu du fichier
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Si aucune catégorie n'est fournie, essayer de la détecter
            if category is None:
                # Essayer de détecter la catégorie à partir du nom du dossier parent
                parent_dir = file_path.parent.name
                category = self._detect_category(parent_dir)
            
            # Classer le document
            result = self.classifier.classify(content)
            
            # Créer le résultat final
            return {
                'fichier': file_path.name,
                'chemin': str(file_path),
                'categorie': category,
                'decision': result.decision,
                'confiance': result.confidence,
                'criteres': {
                    'delai': {
                        'valide': result.criteria_met.get('delai', False),
                        'details': result.criteria_details.get('delai', '')
                    },
                    'periode': {
                        'valide': result.criteria_met.get('periode', False),
                        'details': result.criteria_details.get('periode', '')
                    },
                    'prescription': {
                        'valide': result.criteria_met.get('prescription', False),
                        'details': result.criteria_details.get('prescription', '')
                    },
                    'repercussion': {
                        'valide': result.criteria_met.get('repercussion', False),
                        'details': result.criteria_details.get('repercussion', '')
                    }
                },
                'date_traitement': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Erreur lors du traitement du fichier {file_path}: {e}")
            return None
    
    def process_directory(self, input_dir: Path, output_dir: Path, category: str = None):
        """Traite tous les fichiers d'un répertoire et de ses sous-répertoires."""
        print(f"\nTraitement du répertoire: {input_dir}")
        
        # Détecter la catégorie à partir du nom du dossier si non spécifiée
        if category is None:
            category = self._detect_category(input_dir.name)
        
        # Parcourir tous les fichiers .txt dans le répertoire et ses sous-répertoires
        for file_path in input_dir.rglob('*.txt'):
            # Ne traiter que les fichiers, pas les dossiers
            if file_path.is_file():
                print(f"Traitement du fichier: {file_path}")
                result = self.process_file(file_path, category)
                if result:
                    self.results.append(result)
                    print(f"  - Décision: {result['decision']} (Confiance: {result['confiance']:.2f})")
    
    def process_zip(self, zip_path: Path, output_dir: Path):
        """
        Traite une archive ZIP contenant des documents.
        
        Args:
            zip_path: Chemin vers l'archive ZIP
            output_dir: Répertoire de sortie pour les rapports
        """
        print(f"\nTraitement de l'archive: {zip_path}")
        
        # Créer un répertoire temporaire
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extraire l'archive
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)
            
            # Traiter les dossiers extraits
            for item in temp_path.glob('*'):
                if item.is_dir():
                    self.process_directory(item, output_dir)
    
    def generate_reports(self, output_dir: Path):
        """
        Génère les rapports de résultats.
        
        Args:
            output_dir: Répertoire de sortie pour les rapports
        """
        if not self.results:
            print("Aucun résultat à rapporter.")
            return
        
        # Créer le répertoire de sortie
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Générer le rapport JSON
        json_path = output_dir / 'rapport_complet.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\nRapport JSON généré: {json_path}")
        
        # Générer le rapport CSV si pandas est disponible
        if PANDAS_AVAILABLE and self.results:
            try:
                df = pd.DataFrame(self.results)
                csv_path = output_dir / 'synthese_resultats.csv'
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                print(f"Rapport CSV généré: {csv_path}")
            except Exception as e:
                print(f"Erreur lors de la génération du rapport CSV: {e}")
    
    def _detect_category(self, dir_name: str) -> str:
        """Détecte la catégorie à partir du nom du dossier."""
        dir_name = dir_name.lower()
        if 'recev' in dir_name:
            return 'recevable'
        elif 'irrecev' in dir_name:
            return 'irrecevable'
        return 'inconnu'

def parse_args():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(description="Import par lot pour le classifieur CSPE")
    parser.add_argument(
        '--input', 
        type=str, 
        required=True,
        help="Chemin vers le dossier ou l'archive ZIP à importer"
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default="rapports",
        help="Dossier de sortie pour les rapports (défaut: 'rapports')"
    )
    parser.add_argument(
        '--zip', 
        action='store_true',
        help="Indique que l'entrée est une archive ZIP"
    )
    return parser.parse_args()

def main():
    """Fonction principale."""
    try:
        # Parser les arguments
        args = parse_args()
        
        # Vérifier que le fichier/dossier source existe
        input_path = Path(args.input).resolve()
        if not input_path.exists():
            print(f"Erreur: Le chemin source {input_path} n'existe pas.")
            return 1
        
        # Préparer le répertoire de sortie
        output_dir = Path(args.output).resolve()
        
        # Initialiser l'importateur
        importer = BatchImporter()
        
        # Lancer l'import
        if args.zip:
            if not zipfile.is_zipfile(input_path):
                print(f"Erreur: {input_path} n'est pas une archive ZIP valide.")
                return 1
            importer.process_zip(input_path, output_dir)
        else:
            if not input_path.is_dir():
                print(f"Erreur: {input_path} n'est pas un répertoire valide.")
                return 1
            importer.process_directory(input_path, output_dir)
        
        # Générer les rapports
        importer.generate_reports(output_dir)
        
        print("\nTraitement terminé avec succès !")
        return 0
        
    except Exception as e:
        print(f"\nErreur lors de l'exécution: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
