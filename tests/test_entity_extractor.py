import unittest
from datetime import datetime
from document_processor import EntityExtractor

class TestEntityExtractor(unittest.TestCase):
    
    def setUp(self):
        self.extractor = EntityExtractor()
    
    def test_extract_dates(self):
        """Test de l'extraction des dates"""
        test_text = """
        Le 15/07/2024
        1er janvier 2023
        décembre 2022
        """
        
        dates = self.extractor.extract_dates(test_text)
        self.assertEqual(len(dates), 3)
        self.assertIn(datetime(2024, 7, 15), dates)
        self.assertIn(datetime(2023, 1, 1), dates)
        self.assertIn(datetime(2022, 12, 1), dates)
    
    def test_extract_amounts(self):
        """Test de l'extraction des montants"""
        test_text = """
        Montant de 1 234,56 €
        Somme de 999,99 euros
        42,00 €
        """
        
        amounts = self.extractor.extract_amounts(test_text)
        self.assertEqual(len(amounts), 3)
        self.assertIn(1234.56, amounts)
        self.assertIn(999.99, amounts)
        self.assertIn(42.00, amounts)
    
    def test_extract_entities(self):
        """Test de l'extraction complète des entités"""
        test_text = """
        Le 15/07/2024, montant de 1 234,56 €
        1er janvier 2023, somme de 999,99 euros
        """
        
        entities = self.extractor.extract_entities(test_text)
        self.assertIn('dates', entities)
        self.assertIn('amounts', entities)
        self.assertEqual(len(entities['dates']), 2)
        self.assertEqual(len(entities['amounts']), 2)
    
    def test_get_latest_date(self):
        """Test de la sélection de la date la plus récente"""
        dates = [
            datetime(2022, 1, 1),
            datetime(2023, 12, 31),
            datetime(2024, 6, 15)
        ]
        
        latest = self.extractor.get_latest_date(dates)
        self.assertEqual(latest, datetime(2024, 6, 15))
    
    def test_get_total_amount(self):
        """Test du calcul du montant total"""
        amounts = [100.0, 200.50, 300.75]
        total = self.extractor.get_total_amount(amounts)
        self.assertEqual(total, 601.25)

if __name__ == '__main__':
    unittest.main()
