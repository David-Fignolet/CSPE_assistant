#!/usr/bin/env python3
"""
Script d'exécution des tests d'intégration pour l'assistant CSPE.

Ce script exécute les tests d'intégration sur les dossiers de test
et génère des rapports détaillés.
"""

import sys
import os
import argparse
from pathlib import Path
from tests.integration.test_examples import IntegrationTest

def main():
    # Configuration des arguments en ligne de commande
    parser = argparse.ArgumentParser(description='Exécute les tests d\'intégration CSPE')
    parser.add_argument('--test-dir', type=str, default='test_cases',
                       help='Répertoire contenant les dossiers de test')
    parser.add_argument('--output-dir', type=str, default='reports',
                       help='Répertoire de sortie pour les rapports')
    
    args = parser.parse_args()
    
    # Vérification des répertoires
    test_dir = Path(args.test_dir)
    if not test_dir.exists():
        print(f"Erreur: Le répertoire de test {test_dir} n'existe pas.")
        return 1
    
    # Création du répertoire de sortie si nécessaire
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("  TESTS D'INTÉGRATION - ASSISTANT CSPE")
    print("=" * 80)
    print(f"Répertoire de test : {test_dir.absolute()}")
    print(f"Répertoire des rapports : {output_dir.absolute()}")
    print("-" * 80)
    
    try:
        # Exécution des tests
        tester = IntegrationTest()
        tester.base_dir = test_dir  # Surcharge du répertoire de test
        results = tester.run_tests()
        
        # Affichage du résumé
        print("\n" + "=" * 80)
        print("  RÉSUMÉ DES TESTS")
        print("=" * 80)
        
        for result in results:
            print(f"\n{result['dossier']} - {result['type_cas']}")
            print(f"  Décision: {result['evaluation']['decision']}")
            print(f"  Documents traités: {result['statistiques']['documents_traites']}/{result['statistiques']['total_documents']}")
            print(f"  Erreurs: {result['statistiques']['erreurs']}")
            print(f"  Commentaire: {result['evaluation']['commentaire']}")
        
        print("\n" + "=" * 80)
        print("  RAPPORTS GÉNÉRÉS")
        print("=" * 80)
        print(f"- Rapport complet : {output_dir / 'integration_test_results.json'}")
        print(f"- Synthèse CSV : {output_dir / 'integration_test_summary.csv'}")
        print("\nTests d'intégration terminés avec succès !")
        
        return 0
        
    except Exception as e:
        print(f"\nERREUR lors de l'exécution des tests: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
