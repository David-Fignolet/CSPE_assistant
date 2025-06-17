#!/usr/bin/env python3
"""
Script de test complet pour le classifieur CSPE.

Ce script permet de tester le classifieur LLM avec différents types de documents
et de visualiser les résultats de classification.
"""

import os
import sys
import json
import logging
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Ajout du répertoire racine au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.classifier import CSPEClassifier, classifier

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('classifier_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Données de test
SAMPLE_DOCUMENTS = {
    "recevable_complet": {
        "text": """
        DEMANDE DE REMBOURSEMENT CSPE
        
        Société: ELECTROTECH INDUSTRIES
        SIRET: 12345678900012
        
        Objet: Demande de remboursement CSPE pour l'année 2023
        Montant réclamé: 12 450,00 €
        
        Pièces jointes:
        - Factures d'électricité 2023
        - Attestation d'éligibilité
        - RIB
        
        Date de la décision: 15/01/2023
        Date de dépôt: 10/02/2023
        """,
        "expected": {
            "classification": "RECEVABLE",
            "score_confidence": 0.95,
            "critères_manquants": [],
            "raison": "Tous les critères sont remplis"
        }
    },
    
    "irrecevable_delai_depasse": {
        "text": """
        DEMANDE DE REMBOURSEMENT CSPE
        
        Société: ANCIENNE ENTREPRISE
        SIRET: 98765432100012
        
        Objet: Demande de remboursement CSPE 2020
        Montant: 8 760,00 €
        
        Date de la décision: 10/01/2020
        Date de dépôt: 15/09/2023  # Délai dépassé
        """,
        "expected": {
            "classification": "IRRECEVABLE",
            "score_confidence": 0.9,
            "critères_manquants": ["délai"],
            "raison": "Délai de dépôt dépassé (plus de 18 mois après la décision)"
        }
    },
    
    "incomplet_manque_pieces": {
        "text": """
        DEMANDE DE REMBOURSEMENT
        
        Société: NOUVELLE ENTREPRISE
        
        Objet: Remboursement CSPE
        Montant: 5 000 €
        
        Pièces jointes: Aucune
        """,
        "expected": {
            "classification": "INCOMPLET",
            "score_confidence": 0.85,
            "critères_manquants": ["pièces justificatives"],
            "raison": "Pièces justificatives manquantes"
        }
    }
}

class TestCSPEClassifier(unittest.TestCase):
    """Tests unitaires pour le classifieur CSPE."""
    
    def setUp(self):
        """Initialisation avant chaque test."""
        self.classifier = CSPEClassifier(model_name="mock-model")
    
    def _mock_ollama_response(self, expected):
        """Crée une réponse simulée d'Ollama."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": json.dumps(expected)}
        mock_response.raise_for_status.return_value = None
        return mock_response
    
    @patch('requests.post')
    def test_analyze_document_recevable(self, mock_post):
        """Test d'analyse d'un document recevable."""
        doc = SAMPLE_DOCUMENTS["recevable_complet"]
        mock_post.return_value = self._mock_ollama_response(doc["expected"])
        
        result = self.classifier.analyze_document(doc["text"].strip(), {})
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["classification"], "RECEVABLE")
        self.assertEqual(result["confidence"], 0.95)
    
    @patch('requests.post')
    def test_analyze_document_irrecevable(self, mock_post):
        """Test d'analyse d'un document irrecevable."""
        doc = SAMPLE_DOCUMENTS["irrecevable_delai_depasse"]
        mock_post.return_value = self._mock_ollama_response(doc["expected"])
        
        result = self.classifier.analyze_document(doc["text"].strip(), {})
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["classification"], "IRRECEVABLE")
        self.assertIn("délai", result["missing_criteria"])


def run_demo():
    """Exécute une démonstration du classifieur sur des exemples."""
    print("\n" + "="*80)
    print("DÉMONSTRATION DU CLASSIFIEUR CSPE (MODE SIMULATION)")
    print("="*80)
    
    for doc_name, doc_data in SAMPLE_DOCUMENTS.items():
        doc_text = doc_data["text"].strip()
        expected = doc_data["expected"]
        
        print(f"\n{'='*40}")
        print(f"TEST: {doc_name.upper()}")
        print(f"{'='*40}")
        print("Document d'entrée :")
        print("-"*40)
        print(doc_text)
        
        # Création d'un mock pour la requête API
        with patch('requests.post') as mock_post:
            # Configuration du mock pour retourner la réponse attendue
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": json.dumps(expected)}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Appel du classifieur
            try:
                result = classifier.analyze_document(
                    doc_text,
                    {"source": "demo", "test_case": doc_name}
                )
                
                # Affichage formaté des résultats
                print("\nRésultat de l'analyse :")
                print("-"*40)
                print(f"Statut: {result.get('status', 'N/A')}")
                print(f"Classification: {result.get('classification', 'N/A')}")
                print(f"Confiance: {result.get('confidence', 0)*100:.1f}%")
                
                if result.get('missing_criteria'):
                    print("\nCritères manquants:")
                    for critere in result['missing_criteria']:
                        print(f"- {critere}")
                        
                print(f"\nRaison: {result.get('reason', 'N/A')}")
                
                # Vérification des résultats attendus
                if result.get('status') == 'success':
                    assert result['classification'] == expected['classification'], \
                        f"Classification attendue: {expected['classification']}, obtenue: {result['classification']}"
                    assert abs(result['confidence'] - expected['score_confidence']) < 0.01, \
                        f"Confiance attendue: {expected['score_confidence']}, obtenue: {result['confidence']}"
                
            except Exception as e:
                print(f"\nERREUR: {str(e)}")
        
        input("\nAppuyez sur Entrée pour continuer...")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test du classifieur CSPE")
    parser.add_argument("--test", action="store_true", help="Exécuter les tests unitaires")
    parser.add_argument("--demo", action="store_true", help="Lancer la démonstration")
    args = parser.parse_args()
    
    if args.test:
        print("Exécution des tests unitaires...")
        unittest.main(argv=['first-arg-is-ignored'], exit=False)
    elif args.demo:
        run_demo()
    else:
        parser.print_help()
        print("\nVeuillez spécifier --test ou --demo")
