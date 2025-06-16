import pytest
from document_processor import SmartEntityExtractor, DocumentProcessor

@pytest.fixture(scope='module')
def entity_extractor():
    return SmartEntityExtractor()

@pytest.fixture(scope='module')
def document_processor():
    return DocumentProcessor()
