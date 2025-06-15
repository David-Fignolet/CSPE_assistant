# tests/test_document_processor.py
import pytest
from document_processor import DocumentProcessor
from datetime import datetime

@pytest.fixture
def processor():
    return DocumentProcessor()

def test_extract_text_from_pdf(processor):
    # Test avec un PDF de test
    test_pdf = "tests/data/test_dossier.pdf"
    text = processor.extract_text_from_file(test_pdf)
    assert len(text) > 0
    assert "CSPE" in text

def test_extract_text_from_image(processor):
    # Test avec une image de test
    test_image = "tests/data/test_dossier.jpg"
    text = processor.extract_text_from_file(test_image)
    assert len(text) > 0
    assert "CSPE" in text

def test_extract_date(processor):
    test_text = "Date de réclamation : 15/06/2025"
    date = processor.extract_date(test_text)
    assert date.year == 2025
    assert date.month == 6
    assert date.day == 15

def test_check_period(processor):
    test_text = "Période CSPE 2010-2012"
    result = processor.check_period(test_text)
    assert result['status'] == "✅ Couverte"
    assert result['details'] == "Période couverte : 2010-2012"

def test_check_delay(processor):
    test_text = "Date de réclamation : 31/12/2016"
    result = processor.check_delay(test_text)
    assert result['status'] == "✅ Respecté"
    assert result['deadline'] == "31/12/2015"