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

    def test_check_prescription_quadriennale(self):
        """Teste la détection de la prescription quadriennale."""
        processor = DocumentProcessor()
        
        # Cas 1: Date de fait ancienne (plus de 4 ans) - prescription acquise
        text1 = "La facture date du 15 janvier 2018. Nous demandons le remboursement."
        result1 = processor.check_prescription_quadriennale(text1, "2023-01-16")  # 5 ans après
        assert result1["is_prescrit"] is True
        assert "prescrite" in result1["message"].lower()
        
        # Cas 2: Date de fait récente (moins de 4 ans) - non prescrite
        text2 = "La facture date du 15 janvier 2022. Nous demandons le remboursement."
        result2 = processor.check_prescription_quadriennale(text2, "2023-01-16")  # 1 an après
        assert result2["is_prescrit"] is False
        
        # Cas 3: Plusieurs dates - doit prendre la plus ancienne
        text3 = "La facture initiale date du 10 mars 2018. Le complément est du 15 janvier 2022."
        result3 = processor.check_prescription_quadriennale(text3, "2023-01-16")  # Doit prendre 2018
        assert result3["is_prescrit"] is True
        
        # Cas 4: Pas de date détectée
        text4 = "Ce document ne contient pas de date explicite."
        result4 = processor.check_prescription_quadriennale(text4)
        assert result4["is_prescrit"] is False
        assert "aucune date" in result4["message"].lower()
        
        # Cas 5: Date limite pile poil (jour J)
        text5 = "La facture date du 15 janvier 2019."
        result5 = processor.check_prescription_quadriennale(text5, "2023-01-15")  # Exactement 4 ans après
        assert result5["is_prescrit"] is False  # Le jour même n'est pas encore prescrit

    def test_check_repercussion_client_final(self):
        """Teste la détection de la répercussion sur le client final."""
        processor = DocumentProcessor()
        
        # Cas 1: Répercussion clairement mentionnée
        text1 = "Le surcoût a été intégralement répercuté sur le client final."
        result1 = processor.check_repercussion_client_final(text1)
        assert result1["repercussion_detectee"] is True
        assert result1["confiance"] >= 0.8
        assert len(result1["elements_pertinents"]) > 0
        
        # Cas 2: Répercussion avec une formulation différente
        text2 = "Les montants ont été facturés au client final dans le cadre de la tarification."
        result2 = processor.check_repercussion_client_final(text2)
        assert result2["repercussion_detectee"] is True
        
        # Cas 3: Absence de répercussion mentionnée explicitement
        text3 = "Le surcoût n'a pas été répercuté sur nos clients."
        result3 = processor.check_repercussion_client_final(text3)
        assert result3["repercussion_detectee"] is False
        assert "absence" in result3["message"].lower()
        
        # Cas 4: Aucune mention de répercussion
        text4 = "Ce document ne mentionne rien à propos des clients."
        result4 = processor.check_repercussion_client_final(text4)
        assert result4["repercussion_detectee"] is False
        assert result4["confiance"] < 0.8  # Confiance plus faible car absence de preuve
        
        # Cas 5: Terme positif mais annulé par un négatif
        text5 = "Bien que nous ayons initialement répercuté le coût, nous l'avons finalement supporté."
        result5 = processor.check_repercussion_client_final(text5)
        assert result5["repercussion_detectee"] is False
        assert "supporté" in result5["message"]

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
