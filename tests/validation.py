# tests/validation.py
import os
import pytest
from document_processor import DocumentProcessor
from database_memory import DatabaseManager

def validate_system():
    # Configuration
    processor = DocumentProcessor()
    db_manager = DatabaseManager()
    
    # Dossiers types à tester
    test_cases = [
        {
            "name": "Dossier complet et recevable",
            "files": ["tests/data/dossier_complet.pdf"],
            "expected": {
                "statut": "RECEVABLE",
                "periode": "2009-2015",
                "montant": 10000
            }
        },
        {
            "name": "Dossier hors période",
            "files": ["tests/data/dossier_hors_periode.pdf"],
            "expected": {
                "statut": "IRRECEVABLE",
                "reason": "Période non couverte"
            }
        },
        # Ajouter les autres cas de test...
    ]
    
    results = []
    for case in test_cases:
        try:
            print(f"\nTestant {case['name']}...")
            text = ""
            for file in case["files"]:
                text += processor.extract_text_from_file(file)
            
            analysis = processor.analyze_text(text)
            
            # Vérifier les résultats
            passed = True
            for key, expected in case["expected"].items():
                if analysis.get(key) != expected:
                    passed = False
                    break
            
            results.append({
                "test": case["name"],
                "passed": passed,
                "details": analysis
            })
            
        except Exception as e:
            results.append({
                "test": case["name"],
                "passed": False,
                "details": str(e)
            })
    
    # Rapport de validation
    print("\n=== RAPPORT DE VALIDATION ===")
    for result in results:
        status = "✅" if result["passed"] else "❌"
        print(f"\n{status} {result['test']}")
        if not result["passed"]:
            print(f"Erreur: {result['details']}")
    
    # Statistiques
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\nRésultat final: {passed}/{total} tests réussis ({passed/total*100:.1f}%)")
    
    return all(r["passed"] for r in results)

if __name__ == "__main__":
    if validate_system():
        print("\n✅ Validation réussie !")
    else:
        print("\n❌ Erreurs de validation détectées")