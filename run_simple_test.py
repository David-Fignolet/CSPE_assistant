#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test simplifié pour analyser les dossiers de test CSPE.
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import re

# Configuration des chemins
BASE_DIR = Path(__file__).parent.absolute()
TEST_CASES_DIR = BASE_DIR / "test_cases"
REPORTS_DIR = BASE_DIR / "reports"

# Créer le répertoire de rapports si nécessaire
REPORTS_DIR.mkdir(exist_ok=True)

def clean_text(text: str) -> str:
    """Nettoie le texte des caractères problématiques."""
    if not isinstance(text, str):
        return ""
    # Supprimer les caractères nuls et autres caractères de contrôle
    return ''.join(char for char in text if 31 < ord(char) < 127 or char in '\n\r\t ')

def load_document(file_path: Path) -> str:
    """Charge le contenu d'un fichier avec gestion d'erreur d'encodage."""
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        return clean_text(content)
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            return clean_text(content)
        except Exception as e:
            print(f"Erreur lors de la lecture de {file_path}: {e}")
            return ""

def analyze_document_content(content: str) -> Dict[str, Any]:
    """Analyse le contenu d'un document pour détecter des motifs spécifiques."""
    content_upper = content.upper()
    
    # Détection des motifs d'irrecevabilité
    motifs = {
        'delai_depasse': any(term in content_upper for term in [
            'DÉLAI DÉPASSÉ', 'DÉLAI DE RÉCLAMATION', 'TARDIVE', 'HORS DÉLAI'
        ]),
        'periode_non_couverte': any(term in content_upper for term in [
            '2009-2015', 'PÉRIODE NON COUVERTE', 'HORS PÉRIODE', 'HORS 2009-2015'
        ]),
        'prescription_quadriennale': any(term in content_upper for term in [
            'PRESCRIPTION', 'QUADRENNALE', '4 ANS', 'QUATRE ANS', 'DÉLAI DE PRESCRIPTION'
        ]),
        'repercussion_client': any(term in content_upper for term in [
            'RÉPERCUTÉ', 'FACTURÉ AU CLIENT', 'REPORTÉ SUR LE CLIENT', 'CLIENT FINAL'
        ]),
        'fusion_acquisition': any(term in content_upper for term in [
            'FUSION', 'ACQUISITION', 'RACHAT', 'REPRISE', 'CESSION', 'TRANSFERT'
        ])
    }
    
    # Détection des montants et dates
    montants = re.findall(r'\b(\d{1,3}(?:[\s\u202F]?\d{3})*(?:[,\.]\d{1,2})?)\s*(?:€|EUROS?|EUR)?\b', content_upper)
    dates = re.findall(r'\b(?:0?[1-9]|[12][0-9]|3[01])[/\-\.](?:0?[1-9]|1[0-2])[/\-\.](?:20\d{2}|\d{2})\b', content_upper)
    
    return {
        'motifs_irrecevabilite': {k: v for k, v in motifs.items() if v},
        'montants_trouves': [m.replace(',', '.') for m in montants][:5],  # Limiter à 5 résultats
        'dates_trouvees': dates[:5],  # Limiter à 5 résultats
        'mots_cles_trouves': [
            term for term in [
                'CSPE', 'RÉCLAMATION', 'RESTITUTION', 'FACTURE', 'CONSOMMATION',
                'KWH', 'ÉLECTRICITÉ', 'GAZ', 'FOURNISSEUR', 'CLIENT'
            ] if term in content_upper
        ]
    }

def analyze_test_cases() -> List[Dict[str, Any]]:
    """Analyse les dossiers de test et génère un rapport."""
    results = []
    
    # Vérifier que le répertoire de test existe
    if not TEST_CASES_DIR.exists():
        print(f"Erreur: Le répertoire {TEST_CASES_DIR} n'existe pas.")
        return results
    
    # Parcourir les dossiers de test
    for case_dir in sorted(TEST_CASES_DIR.glob('*')):
        if not case_dir.is_dir() or case_dir.name.startswith('.'):
            continue
            
        print(f"\nAnalyse du dossier: {case_dir.name}")
        
        # Détecter le type de cas
        case_type = "Inconnu"
        dir_name_upper = case_dir.name.upper()
        
        if "RECEVABLE" in dir_name_upper and "IRRECEVABLE" not in dir_name_upper:
            case_type = "Recevable"
        elif "IRRECEVABLE" in dir_name_upper:
            if "DELAI" in dir_name_upper:
                case_type = "Irrecevable (Délai dépassé)"
            elif "PERIODE" in dir_name_upper or "NON_COUVERTE" in dir_name_upper:
                case_type = "Irrecevable (Période non couverte)"
            elif "PRESCRIPTION" in dir_name_upper:
                case_type = "Irrecevable (Prescription quadriennale)"
            elif "REPERCUSSION" in dir_name_upper:
                case_type = "Irrecevable (Répercussion client)"
            else:
                case_type = "Irrecevable (Autre motif)"
        elif "COMPLEXE" in dir_name_upper:
            case_type = "Complexe (Analyse experte requise)"
        elif "FUSION" in dir_name_upper or "ACQUISITION" in dir_name_upper:
            case_type = "Fusion/Acquisition"
        
        print(f"Type détecté: {case_type}")
        
        # Analyser les fichiers du dossier
        files_info = []
        for file_path in sorted(case_dir.glob('*')):
            if file_path.is_file():
                content = load_document(file_path)
                file_info = {
                    'nom': file_path.name,
                    'taille_ko': round(os.path.getsize(file_path) / 1024, 2),
                    'lignes': len(content.splitlines())
                }
                
                # Analyser le contenu du fichier
                if content:
                    file_info['analyse'] = analyze_document_content(content)
                
                files_info.append(file_info)
        
        # Ajouter les résultats
        results.append({
            'dossier': case_dir.name,
            'type': case_type,
            'nb_fichiers': len(files_info),
            'fichiers': files_info
        })
    
    return results

def generate_report(results: List[Dict[str, Any]]) -> None:
    """Génère un rapport d'analyse."""
    # Générer un rapport JSON
    report_path = REPORTS_DIR / 'analyse_dossiers.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'date_analyse': str(datetime.now()),
            'nb_dossiers': len(results),
            'resultats': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\nRapport généré : {report_path}")

def main() -> int:
    """Fonction principale."""
    print("Démarrage de l'analyse des dossiers de test...")
    results = analyze_test_cases()
    
    if results:
        generate_report(results)
        print("\nRésumé de l'analyse :")
        for result in results:
            print(f"\n- {result['dossier']} ({result['type']}): {result['nb_fichiers']} fichiers")
    else:
        print("Aucun dossier de test trouvé.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
