#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test rapide des corrections apportées
Assistant CSPE - Conseil d'État

Pour vérifier que les erreurs sont corrigées
"""

import sys
import subprocess
import time

def test_imports():
    """Teste les imports principaux"""
    try:
        print("🔍 Test des imports...")
        
        # Import streamlit
        import streamlit as st
        print("✅ Streamlit OK")
        
        # Import pandas  
        import pandas as pd
        print("✅ Pandas OK")
        
        # Import des modules locaux
        from document_processor import DocumentProcessor
        print("✅ DocumentProcessor OK")
        
        from database_memory import DatabaseManager
        print("✅ DatabaseManager OK")
        
        # Test de création des objets
        processor = DocumentProcessor()
        print("✅ DocumentProcessor instancié")
        
        db = DatabaseManager("sqlite:///test.db")
        print("✅ DatabaseManager instancié")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur import: {e}")
        return False

def test_demo_analysis():
    """Teste la fonction d'analyse démo"""
    try:
        print("\n🧪 Test analyse démo...")
        
        # Import de la fonction
        from app import get_demo_analysis
        
        # Test avec texte simple
        text_test = """
        Monsieur le Président,
        
        Je conteste la décision de la CRE du 15/03/2025 concernant ma CSPE.
        
        Cette réclamation est formée le 10/04/2025.
        
        Montant: 1500€
        
        Ci-joint les pièces justificatives requises.
        
        Cordialement,
        Monsieur MARTIN
        """
        
        result = get_demo_analysis(text_test)
        
        # Vérifications
        assert 'decision' in result
        assert 'criteria' in result
        assert 'confidence_score' in result
        
        print(f"✅ Classification: {result['decision']}")
        print(f"✅ Confiance: {result['confidence_score']:.1%}")
        print(f"✅ Critères analysés: {len(result['criteria'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test analyse: {e}")
        return False

def test_document_processor():
    """Teste le traitement de documents"""
    try:
        print("\n📄 Test traitement documents...")
        
        from document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        
        # Test avec texte simple
        test_text = "Ceci est un test de document CSPE avec une date 15/03/2025 et un montant 1500€"
        
        # Test extraction entités
        entities = processor.extract_entities(test_text)
        print(f"✅ Entités extraites: {len(entities)} types")
        
        # Test extraction critères CSPE
        criteria = processor.extract_cspe_criteria(test_text)
        print(f"✅ Critères CSPE: {len(criteria)} critères")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test processor: {e}")
        return False

def test_database():
    """Teste la base de données"""
    try:
        print("\n🗄️ Test base de données...")
        
        from database_memory import DatabaseManager
        import os
        
        # Base de test
        test_db = "test_corrections.db"
        
        # Nettoyer si existe
        if os.path.exists(test_db):
            os.remove(test_db)
        
        db = DatabaseManager(f"sqlite:///{test_db}")
        db.init_db()
        print("✅ Base initialisée")
        
        # Test ajout dossier
        dossier_data = {
            'numero_dossier': 'TEST-001',
            'demandeur': 'Test User',
            'activite': 'Test',
            'date_reclamation': '2024-12-15',
            'periode_debut': 2010,
            'periode_fin': 2012,
            'montant_reclame': 1000.0,
            'statut': 'TEST',
            'analyste': 'Test'
        }
        
        dossier_id = db.add_dossier(dossier_data)
        if dossier_id:
            print("✅ Dossier ajouté")
        
        # Test statistiques
        stats = db.get_statistics()
        print(f"✅ Statistiques: {stats['total']} dossiers")
        
        # Nettoyage
        if os.path.exists(test_db):
            os.remove(test_db)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test database: {e}")
        return False

def run_quick_app_test():
    """Lance l'app rapidement pour tester"""
    try:
        print("\n🚀 Test lancement application (5 secondes)...")
        
        # Lance streamlit en arrière-plan
        process = subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run', 
            'app.py', '--server.port', '8503', 
            '--server.headless', 'true'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Attendre 5 secondes
        time.sleep(5)
        
        # Vérifier que le processus est toujours en vie
        if process.poll() is None:
            print("✅ Application démarrée avec succès")
            process.terminate()
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Application crashée: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test app: {e}")
        return False

def main():
    """Test principal"""
    print("🔧 TEST DES CORRECTIONS - Assistant CSPE")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Analyse démo", test_demo_analysis), 
        ("Document processor", test_document_processor),
        ("Base de données", test_database),
        ("Lancement app", run_quick_app_test)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name.upper()}")
        print("-" * 30)
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:20} : {status}")
        if success:
            passed += 1
    
    print(f"\nRésultat global: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 TOUS LES TESTS PASSENT - Application prête pour l'entretien !")
        return 0
    else:
        print("⚠️ Certains tests échouent - Vérifications nécessaires")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)