import sys
import os
import unittest
from datetime import date

# Add the root directory to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processing.document_processor import CSPEDocumentProcessor, CSPEEntity

class TestCSPEDocumentProcessor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = CSPEDocumentProcessor()        
        cls.test_text = """
        FACTURE N°FAC-2023-0042
        Date: 15/03/2023
        Client: CLIENT-12345
        Commande: CDE-7890

        Détail des prestations:
        - Prestation 1: 1 234,56 €
        - Prestation 2: 789,00 €
        - Remise: 100,00 €

        Total TTC: 1 923,56 €
        Date de paiement: 2023-04-15
        """

    def test_extract_dates(self):
        """Test date extraction"""
        dates = self.processor.extract_dates(self.test_text)
        date_values = [d.value for d in dates]
        self.assertIn(date(2023, 3, 15), date_values)
        self.assertIn(date(2023, 4, 15), date_values)

    def test_extract_amounts(self):
        """Test amount extraction"""
        amounts = self.processor.extract_amounts(self.test_text)
        amount_values = [a.value for a in amounts]
        expected_amounts = [1234.56, 789.0, 100.0, 1923.56]

        print(f"\nMontants détectés: {amount_values}")

        for amount in expected_amounts:
            self.assertIn(amount, amount_values,
                         f"Le montant {amount} n'a pas été trouvé dans {amount_values}")

    def test_extract_amounts_improved(self):
        """Test amélioré de l'extraction des montants avec différents formats."""
        test_cases = [
            # Montants avec symbole €
            ("Prix: 1 234,56 €", [1234.56]),
            ("Total: 99,99 euros", [99.99]),
            ("Montant: 1 000 000,50 EUR", [1000000.50]),
            
            # Montants sans symbole mais dans un contexte financier
            ("Le montant est de 1500,50", [1500.50]),
            ("Coût total 2500", [2500.0]),
            ("Facture n°123 pour un montant de 750,00", [750.0]),
            
            # Faux positifs à éviter
            ("Page 1 sur 10", []),  # Numéro de page
            ("Tél: 01 23 45 67 89", []),  # Numéro de téléphone
            ("Code postal 75001", []),  # Code postal
            ("Article 12 du code", []),  # Référence d'article
            ("Voir paragraphe 3.4", []),  # Référence de paragraphe
            
            # Cas limites
            ("Prix: 9,99 € (petit montant)", [9.99]),
            ("Montant: 1 234 567,89 €", [1234567.89]),
            ("Total: 1.50 (sans contexte monétaire)", []),  # Trop petit sans contexte
            ("Le code est 12345", []),  # Code numérique
            
            # Multiples montants
            ("Prix: 100,50 € et 200,75 € pour la livraison", [100.50, 200.75]),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                amounts = self.processor.extract_amounts(text)
                amount_values = [a.value for a in amounts]
                self.assertEqual(amount_values, expected, 
                               f"Échec pour le texte: '{text}'. Obtenu: {amount_values}, Attendu: {expected}")

    def test_extract_references(self):
        """Test reference extraction"""
        refs = self.processor.extract_references(self.test_text)
        self.assertEqual(refs['facture'][0].value, 'FAC-2023-0042')
        self.assertEqual(refs['client'][0].value, 'CLIENT-12345')
        self.assertEqual(refs['commande'][0].value, 'CDE-7890')

    def test_integration(self):
        """Test full document processing"""
        result = self.processor.extract_document_info(self.test_text)
        self.assertEqual(result['metadata']['status'], 'success')

        # Check that we have the expected number of entities
        self.assertGreaterEqual(len(result['dates']), 2)
        self.assertGreaterEqual(len(result['amounts']), 3)  # At least 3 amounts expected
        self.assertGreaterEqual(len(result['references']['facture']), 1)
        self.assertGreaterEqual(len(result['references']['client']), 1)
        self.assertGreaterEqual(len(result['references']['commande']), 1)

if __name__ == '__main__':
    unittest.main(verbosity=2)