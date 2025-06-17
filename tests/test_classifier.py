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

"""
Tests unitaires pour le module classifier.py
"""

import pytest
import json
from datetime import datetime, timedelta
from ..classifier import CSPEClassifier, ClassificationResult
from ..document_processor import DocumentProcessor


class TestCSPEClassifier:
    """Tests pour la classe CSPEClassifier."""
    
    @pytest.fixture
    def classifier(self):
        """Fixture pour créer une instance de CSPEClassifier pour les tests."""
        return CSPEClassifier()
    
    def test_classification_result_serialization(self):
        """Teste la sérialisation de ClassificationResult."""
        # Créer un résultat de test
        result = ClassificationResult(
            document_id="test_123",
            timestamp="2023-01-01T12:00:00",
            criteres={"test": {"est_valide": True, "message": "Test"}},
            decision="RECEVABLE",
            confiance=0.9,
            raison="Test de sérialisation",
            metadata={"source": "test"}
        )
        
        # Vérifier la conversion en dictionnaire
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["document_id"] == "test_123"
        assert result_dict["decision"] == "RECEVABLE"
        
        # Vérifier la sérialisation JSON
        json_str = result.to_json()
        assert isinstance(json_str, str)
        assert "test_123" in json_str
        
        # Vérifier que le JSON peut être désérialisé
        loaded = json.loads(json_str)
        assert loaded["document_id"] == "test_123"
    
    def test_classifier_initialization(self):
        """Teste l'initialisation du classifieur."""
        # Test avec processeur par défaut
        classifier1 = CSPEClassifier()
        assert isinstance(classifier1.processor, DocumentProcessor)
        
        # Test avec processeur personnalisé
        custom_processor = DocumentProcessor()
        classifier2 = CSPEClassifier(processor=custom_processor)
        assert classifier2.processor is custom_processor
    
    def test_classifier_document_recevable(self, classifier):
        """Teste la classification d'un document recevable."""
        # Document qui répond à tous les critères
        texte = """
        Par la présente, je sollicite le remboursement de la CSPE pour la période 2010-2014.
        Le montant total s'élève à 1500,50 euros.
        Cette demande est faite dans les délais légaux.
        Le surcoût n'a pas été répercuté sur nos clients finaux.
        """
        
        result = classifier.classifier_document(texte, document_id="test_recevable")
        
        # Vérifications de base
        assert isinstance(result, ClassificationResult)
        assert result.document_id == "test_recevable"
        assert result.decision in ["RECEVABLE", "A_VERIFIER"]
        assert result.confiance >= 0.7
        
        # Vérifier que tous les critères sont présents
        assert all(critere in result.criteres for critere in [
            'delai_reclamation', 
            'periode_2009_2015', 
            'prescription_quadriennale', 
            'repercussion_client_final'
        ])
    
    def test_classifier_document_irrecevable(self, classifier):
        """Teste la classification d'un document irrecevable."""
        # Document qui ne répond à aucun critère
        texte = """
        Je demande le remboursement de la CSPE pour 2022.
        Le montant est de 1000 euros.
        Le surcoût a été intégralement répercuté sur nos clients.
        """
        
        result = classifier.classifier_document(texte, document_id="test_irrecevable")
        
        # Vérifications
        assert result.decision in ["IRRECEVABLE", "A_VERIFIER"]
        
        # Vérifier que plusieurs critères ne sont pas respectés
        criteres_invalides = sum(
            1 for critere in result.criteres.values() 
            if not critere.get('est_valide', True)
        )
        assert criteres_invalides >= 2
    
    def test_classifier_document_avec_metadonnees(self, classifier):
        """Teste la classification avec des métadonnées supplémentaires."""
        metadata = {
            "source": "test",
            "utilisateur": "user123",
            "date_creation": "2023-01-01"
        }
        
        texte = "Document de test avec métadonnées."
        result = classifier.classifier_document(
            texte, 
            document_id="test_metadata",
            metadata=metadata
        )
        
        assert result.metadata == metadata
    
    def test_classifier_texte_vide(self, classifier):
        """Teste le comportement avec un texte vide."""
        with pytest.raises(ValueError):
            classifier.classifier_document("")
        
        with pytest.raises(ValueError):
            classifier.classifier_document(None)
    
    def test_classifier_decision_seuils(self, classifier, mocker):
        """Teste les seuils de décision du classifieur."""
        # Mock des méthodes de vérification pour contrôler les scores
        def mock_verifier(*args, **kwargs):
            return {
                'est_valide': True,
                'message': 'Test',
                'details': {},
                'confiance': 0.9
            }
        
        # Appliquer les mocks
        mocker.patch.object(classifier, '_verifier_delai_reclamation', mock_verifier)
        mocker.patch.object(classifier, '_verifier_periode_2009_2015', mock_verifier)
        mocker.patch.object(classifier, '_verifier_prescription_quadriennale', mock_verifier)
        mocker.patch.object(classifier, '_verifier_repercussion_client_final', mock_verifier)
        
        # Tester avec un score élevé (devrait être RECEVABLE)
        classifier.seuils['confiance_min'] = 0.8
        result = classifier.classifier_document("Test")
        assert result.decision == "RECEVABLE"
        assert result.confiance >= 0.8
        
        # Tester avec un score moyen (devrait être A_VERIFIER)
        classifier.seuils['confiance_min'] = 0.9  # Augmenter le seuil pour forcer A_VERIFIER
        result = classifier.classifier_document("Test")
        assert result.decision == "A_VERIFIER"
        
        # Tester avec un score bas (devrait être IRRECEVABLE)
        classifier.seuils['confiance_moyenne'] = 0.9  # Augmenter le seuil moyen
        result = classifier.classifier_document("Test")
        assert result.decision == "IRRECEVABLE"
