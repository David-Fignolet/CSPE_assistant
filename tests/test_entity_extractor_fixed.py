import pytest
from document_processor import SmartEntityExtractor, ExtractedEntity

class TestSmartEntityExtractor:
    """Tests for the SmartEntityExtractor class."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.extractor = SmartEntityExtractor()

    def test_extract_dates_basic(self):
        """Test basic date extraction."""
        text = "La date est le 15/07/2023"
        dates = self.extractor.extract_dates(text)
        assert len(dates) > 0, "Aucune date n'a été extraite"
        assert dates[0].value == "2023-07-15"
        assert dates[0].confidence == 0.9

    def test_extract_amounts_basic(self):
        """Test basic amount extraction."""
        text = "Le montant est de 1 234,56 €"
        amounts = self.extractor.extract_amounts(text)
        assert len(amounts) > 0, "Aucun montant n'a été extrait"
        assert amounts[0].value == "1234.56"
        assert amounts[0].confidence == 0.95

class TestDocumentProcessor:
    """Tests for the DocumentProcessor class."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        from document_processor import DocumentProcessor
        self.processor = DocumentProcessor()

    def test_check_delay(self):
        """Test delay check functionality."""
        # Test avec une date dans la limite des 60 jours
        text = "Décision du 01/01/2023"
        result = self.processor.check_delay(text, test_mode=True)
        assert result["is_on_time"] is True
        assert result["days_since_decision"] == 59  # Du 01/01/2023 au 01/03/2023

        # Test avec une date en dehors de la limite
        text = "Décision du 25/12/2022"
        result = self.processor.check_delay(text, test_mode=True)
        assert result["is_on_time"] is False
        assert result["days_since_decision"] == 66  # Du 25/12/2022 au 01/03/2023
