#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour le moteur d'analyse CSPE.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from src.processing.analysis_engine import CSPEAnalysisEngine

def main():
    """Fonction principale."""
    if len(sys.argv) != 2:
        print("Utilisation: python test_analysis_engine.py <chemin_du_dossier>")
        print("Exemple: python test_analysis_engine.py test_cases/001_CAS_RECEVABLE")
        return 1
    
    folder_path = Path(sys.argv[1])
    if not folder_path.exists():
        print(f"Erreur: Le dossier {folder_path} n'existe pas.")
        return 1
    
    print(f"Démarrage de l'analyse du dossier: {folder_path}")
    
    # Initialiser le moteur d'analyse
    engine = CSPEAnalysisEngine()
    
    # Analyser le dossier
    start_time = datetime.now()
    result = engine.analyze_folder(str(folder_path))
    analysis_time = (datetime.now() - start_time).total_seconds()
    
    # Afficher un résumé
    print(f"\n=== RÉSULTATS DE L'ANALYSE ===")
    print(f"Dossier analysé: {result.get('folder_name')}")
    print(f"Type de cas: {result.get('case_type')}")
    print(f"Documents analysés: {result.get('documents_analyzed')}")
    print(f"Temps d'analyse: {analysis_time:.2f} secondes")
    
    # Afficher les incohérences détectées
    if result.get('inconsistencies'):
        print("\n=== INCOHÉRENCES DÉTECTÉES ===")
        for inc in result.get('inconsistencies', []):
            print(f"- {inc.get('message')} (Sévérité: {inc.get('severity')})")
    
    # Afficher les dates clés
    if result.get('dates_found'):
        print("\n=== DATES IMPORTANTES ===")
        for date_info in result.get('dates_found', [])[-5:]:  # 5 dates les plus récentes
            print(f"- {date_info.get('value')} (source: {date_info.get('source_file', 'inconnue')})")
    
    # Afficher les montants clés
    if result.get('amounts_found'):
        print("\n=== MONTANTS IMPORTANTS ===")
        for amount_info in sorted(
            result.get('amounts_found', []), 
            key=lambda x: float(x.get('value', 0)),
            reverse=True
        )[:5]:  # 5 montants les plus élevés
            print(f"- {amount_info.get('value')} € (source: {amount_info.get('source_file', 'inconnue')})")
    
    # Sauvegarder le rapport complet
    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"analyse_{folder_path.name}_{timestamp}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nRapport complet enregistré dans: {report_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
