#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier l'extraction d'entités CSPE.
"""

import sys
from pathlib import Path
from datetime import datetime
from src.processing.document_processor import CSPEDocumentProcessor

def main():
    """Fonction principale."""
    if len(sys.argv) != 2:
        print("Utilisation: python test_extraction.py <chemin_du_dossier>")
        print("Exemple: python test_extraction.py test_cases/001_CAS_RECEVABLE")
        return 1
    
    folder_path = Path(sys.argv[1])
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Erreur: Le dossier {folder_path} n'existe pas ou n'est pas un dossier.")
        return 1
    
    print(f"Démarrage du test d'extraction sur le dossier: {folder_path}")
    print("-" * 80)
    
    # Initialiser le processeur de documents
    processor = CSPEDocumentProcessor()
    
    # Analyser chaque fichier du dossier
    for file_path in sorted(folder_path.glob('*')):
        if file_path.is_file() and file_path.suffix in ['.txt', '.md']:
            print(f"\nAnalyse du fichier: {file_path.name}")
            print("=" * 60)
            
            try:
                # Lire le contenu du fichier
                content = file_path.read_text(encoding='utf-8')
                
                # Extraire les entités
                dates = processor.extract_dates(content)
                amounts = processor.extract_amounts(content)
                references = processor.extract_references(content)
                
                # Afficher les résultats
                print(f"\nDates trouvées ({len(dates)}):")
                for date_entity in dates:
                    print(f"  - {date_entity.value} (ligne ~{content.count('\n', 0, date_entity.start_pos) + 1})")
                
                print(f"\nMontants trouvés ({len(amounts)}):")
                for amount_entity in amounts:
                    print(f"  - {amount_entity.value} € (confiance: {amount_entity.confidence:.1f})")
                
                print(f"\nRéférences trouvées (total: {sum(len(refs) for refs in references.values())}):")
                for ref_type, refs in references.items():
                    if refs:
                        print(f"  - {ref_type}: {', '.join(str(r.value) for r in refs)}")
                
            except Exception as e:
                print(f"Erreur lors du traitement du fichier {file_path.name}: {str(e)}")
            
            print("\n" + "-" * 60)
    
    print("\nTest d'extraction terminé avec succès!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
