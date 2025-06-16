import unittest
from document_processor import SmartEntityExtractor

class TestSmartEntityExtractor(unittest.TestCase):
    """Tests pour SmartEntityExtractor"""
    
    def setUp(self):
        self.extractor = SmartEntityExtractor()
    
    def test_extract_dates_basic(self):
        """Test basique d'extraction de dates"""
        text = "Date de la décision : 15/06/2025"
        dates = self.extractor.extract_dates(text)
        print(f"Dates extraites : {dates}")  # Debug
        self.assertGreater(len(dates), 0, "Aucune date n'a été extraite")
        self.assertEqual(dates[0].value, "2025-06-15")
    
    def test_extract_amounts_basic(self):
        """Test basique d'extraction de montants"""
        text = "Montant total : 1 234,56 €"
        amounts = self.extractor.extract_amounts(text)
        print(f"Montants extraits : {amounts}")  # Debug
        self.assertGreater(len(amounts), 0, "Aucun montant n'a été extrait")
        self.assertEqual(amounts[0].value, "1234.56")

if __name__ == '__main__':
    unittest.main(verbosity=2)
