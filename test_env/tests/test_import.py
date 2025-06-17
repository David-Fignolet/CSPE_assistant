import sys
import os
import unittest

# Ajouter le répertoire racine au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processing.document_processor import CSPEDocumentProcessor

class TestSimple(unittest.TestCase):
    def test_import(self):
        processor = CSPEDocumentProcessor()
        self.assertIsNotNone(processor)
        print("Test d'importation réussi !")

if __name__ == '__main__':
    unittest.main()
