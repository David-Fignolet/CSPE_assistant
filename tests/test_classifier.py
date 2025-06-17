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


def load_text_file(file_path):
    """Charge le contenu d'un fichier texte."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {file_path}: {str(e)}")
        return None

def run_demo():
    """Exécute une démonstration du classifieur sur des exemples."""
    print("\n" + "="*80)
    print("DÉMONSTRATION DU CLASSIFIEUR CSPE (MODE SIMULATION)")
    print("="*80)
    
    while True:
        print("\nOptions :")
        print("1. Tester un document exemple")
        print("2. Charger un fichier texte personnalisé")
        print("3. Quitter")
        
        choice = input("\nVotre choix (1-3): ").strip()
        
        if choice == '3':
            break
            
        if choice == '1':
            # Afficher la liste des documents exemples
            print("\nDocuments exemples disponibles :")
            for i, doc_name in enumerate(SAMPLE_DOCUMENTS.keys(), 1):
                print(f"{i}. {doc_name.replace('_', ' ').title()}")
            
            doc_choice = input("\nChoisissez un numéro de document (ou Entrée pour annuler): ").strip()
            if not doc_choice or not doc_choice.isdigit():
                continue
                
            doc_index = int(doc_choice) - 1
            doc_list = list(SAMPLE_DOCUMENTS.items())
            
            if 0 <= doc_index < len(doc_list):
                doc_name, doc_data = doc_list[doc_index]
                doc_text = doc_data["text"].strip()
                expected = doc_data["expected"]
                process_document(doc_text, expected, doc_name)
                
        elif choice == '2':
            file_path = input("\nEntrez le chemin du fichier texte: ").strip('"')
            if not file_path:
                continue
                
            doc_text = load_text_file(file_path)
            if doc_text:
                # Utiliser des valeurs par défaut pour les documents personnalisés
                expected = {
                    "classification": "INCONNU",
                    "score_confidence": 0.0,
                    "critères_manquants": [],
                    "raison": "Document personnalisé - analyse en cours"
                }
                process_document(doc_text, expected, os.path.basename(file_path))

def process_document(doc_text, expected, doc_name):
    """Traite un document et affiche les résultats."""
    print(f"\n{'='*40}")
    print(f"DOCUMENT: {doc_name.upper()}")
    print(f"{'='*40}")
    print("Contenu du document :")
    print("-"*40)
    print(doc_text[:500] + ("..." if len(doc_text) > 500 else ""))
    
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
            
        except Exception as e:
            print(f"\nERREUR lors de l'analyse: {str(e)}")
    
    input("\nAppuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test du classifieur CSPE")
    parser.add_argument("--test", action="store_true", help="Exécuter les tests unitaires")
    parser.add_argument("--demo", action="store_true", help="Lancer la démonstration interactive")
    parser.add_argument("--file", type=str, help="Analyser un fichier texte spécifique")
    args = parser.parse_args()
    
    if args.test:
        print("Exécution des tests unitaires...")
        unittest.main(argv=['first-arg-is-ignored'], exit=False)
    elif args.demo:
        run_demo()
    elif args.file:
        doc_text = load_text_file(args.file)
        if doc_text:
            expected = {
                "classification": "INCONNU",
                "score_confidence": 0.0,
                "critères_manquants": [],
                "raison": "Document personnalisé - analyse en cours"
            }
            process_document(doc_text, expected, os.path.basename(args.file))
    else:
        parser.print_help()
        print("\nVeuillez spécifier --test, --demo ou --file <fichier>")
