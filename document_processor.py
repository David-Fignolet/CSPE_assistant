import PyPDF2
import pytesseract
import cv2
import numpy as np
from PIL import Image
from typing import Dict, List, Tuple

class DocumentProcessor:
    def __init__(self):
        self.ocr_config = '--psm 6 --oem 3 -l fra'  # Configuration OCR pour le français

    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extrait le texte d'un fichier PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            print(f"Erreur lors de l'extraction PDF: {str(e)}")
            return ""

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Prétraite une image pour l'OCR"""
        # Conversion en gris
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Amélioration du contraste
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=40)
        
        # Binarisation
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Suppression du bruit
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        return binary

    def extract_text_from_image(self, file_content: bytes) -> str:
        """Extrait le texte d'une image avec OCR"""
        try:
            # Conversion du contenu en image
            image = Image.open(io.BytesIO(file_content))
            # Conversion en numpy array pour OpenCV
            image_np = np.array(image)
            
            # Prétraitement
            processed = self.preprocess_image(image_np)
            
            # Extraction du texte
            text = pytesseract.image_to_string(
                processed,
                config=self.ocr_config
            )
            return text.strip()
        except Exception as e:
            print(f"Erreur lors de l'extraction OCR: {str(e)}")
            return ""

    def extract_text_from_file(self, file) -> str:
        """Extrait le texte d'un fichier selon son type"""
        if not file:
            return ""
        
        if file.type == 'application/pdf':
            return self.extract_text_from_pdf(file.getvalue())
        elif file.type in ['image/png', 'image/jpeg', 'image/jpg']:
            return self.extract_text_from_image(file.getvalue())
        else:
            return "Format non supporté"