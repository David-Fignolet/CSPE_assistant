import unittest
from datetime import date
from src.processing.document_processor import CSPEDocumentProcessor, CSPEEntity

class TestCSPEDocumentProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = CSPEDocumentProcessor()
        
    def test_extract_dates(self):
        text = "Date: 15/03/2023 ou 2023-04-15"
        dates = self.processor.extract_dates(text)
        self.assertEqual(len(dates), 2)
        self.assertEqual(dates[0].value, date(2023, 3, 15))
        self.assertEqual(dates[1].value, date(2023, 4, 15))
        
    def test_extract_amounts(self):
        text = "Montants: 1 234,56 € ou 42.00 ou 999,99"
        amounts = self.processor.extract_amounts(text)
        self.assertEqual(len(amounts), 3)
        self.assertIn(1234.56, [a.value for a in amounts])
        self.assertIn(42.0, [a.value for a in amounts])
        
    def test_extract_references(self):
        text = "Facture FAC-123, Commande CDE-456, Client: CLT-789"
        refs = self.processor.extract_references(text)
        self.assertEqual(len(refs['facture']), 1)
        self.assertEqual(refs['facture'][0].value, 'FAC-123')
        self.assertEqual(refs['commande'][0].value, 'CDE-456')
        self.assertEqual(refs['client'][0].value, 'CLT-789')
        
    def test_integration(self):
        text = '''Facture FAC-2023-0042 du 15/03/2023
                Montant: 1 234,56 €
                Client: CLT-12345'''
                
        result = self.processor.extract_document_info(text)
        self.assertEqual(len(result['dates']), 1)
        self.assertEqual(len(result['amounts']), 1)
        self.assertEqual(len(result['references']['facture']), 1)

if __name__ == '__main__':
    unittest.main()
