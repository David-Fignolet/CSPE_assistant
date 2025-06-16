import pytest
from datetime import datetime
from document_processor import DocumentProcessor, ExtractedEntity

class TestDocumentProcessor:
    """Tests for the DocumentProcessor class."""

    def setup_method(self):
        """Set up the test environment."""
        self.processor = DocumentProcessor()

    def test_extract_dates_formats(self):
        """Test date extraction with various formats."""
        test_cases = [
            ("La date est le 15/07/2023", "2023-07-15"),
            ("Le 1er janvier 2023", "2023-01-01"),
            ("Date: 2023-12-31", "2023-12-31"),
            ("15 mars 2023", "2023-03-15"),
            ("Le 1 janvier 2023", "2023-01-01"),
            ("La date est le 01/01/2023", "2023-01-01")
        ]

        for text, expected in test_cases:
            print(f"\nTesting date extraction: '{text}'")
            dates = self.processor.extract_dates(text)
            print(f"Dates extraites: {[d.value for d in dates]}")
            assert len(dates) > 0, f"Aucune date trouvée dans: {text}"
            assert dates[0].value == expected, f"Attendu {expected}, obtenu {dates[0].value}"

    def test_extract_amounts_formats(self):
        """Test amount extraction with various formats."""
        test_cases = [
            ("Montant: 1 234,56 €", "1234.56"),
            ("Total: 9 999,99 euros", "9999.99"),
            ("Prix: 42,00 €", "42.00"),
            ("Coût: 1,234.56$", "1234.56"),
            ("Montant de 1234,56", "1234.56"),
            ("Prix de 1 234.56", "1234.56")
        ]

        for text, expected in test_cases:
            print(f"\nTesting amount extraction: '{text}'")
            amounts = self.processor.extract_amounts(text)
            print(f"Montants extraits: {[a.value for a in amounts]}")
            assert len(amounts) > 0, f"Aucun montant trouvé dans: {text}"
            assert amounts[0].value == expected, f"Attendu {expected}, obtenu {amounts[0].value}"

    def test_performance_large_text(self):
        """Test performance with a large text."""
        large_text = "Test " * 1000 + "Le 15/07/2023 " * 1000
        start_time = datetime.now()
        self.processor.extract_dates(large_text)
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\nPerformance test: {elapsed} seconds")
        assert elapsed < 1.0, "L'extraction des dates est trop lente"

    def test_check_delay(self):
        """Test delay check functionality."""
        # Test avec une date dans la limite des 60 jours (en utilisant test_mode=True)
        text = "Décision du 01/01/2023"
        print(f"\nTesting delay check with text: '{text}'")
        result = self.processor.check_delay(text, test_mode=True)
        print(f"Résultat: {result}")
        assert result["is_valid"] is True
        assert result["is_on_time"] is True
        assert result["days_since_decision"] == 59  # Du 01/01/2023 au 01/03/2023

        # Test avec une date en dehors de la limite
        text = "Décision du 25/12/2022"
        print(f"\nTesting delay check with text: '{text}'")
        result = self.processor.check_delay(text, test_mode=True)
        print(f"Résultat: {result}")
        assert result["is_valid"] is True
        assert result["is_on_time"] is False
        assert result["days_since_decision"] == 67  # Du 25/12/2022 au 01/03/2023

    def test_check_period(self):
        """Test period detection."""
        test_cases = [
            ("Année 2023", True),
            ("Exercice 2023-2024", True),
            ("Période 2023", True),
            ("Du 01/01/2023 au 31/12/2023", True),
            ("Aucune période spécifiée", False)
        ]

        for text, expected in test_cases:
            print(f"\nTesting period detection for: '{text}'")
            result = self.processor.check_period(text)
            print(f"Résultat: {result}")
            assert result["is_valid"] is expected, f"Failed for: {text}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
