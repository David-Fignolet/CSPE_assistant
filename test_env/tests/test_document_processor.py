import sys
import os
import unittest
from datetime import date

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from processing.document_processor import CSPEDocumentProcessor, CSPEEntity

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

if __name__ == '__main__':
    unittest.main(verbosity=2)