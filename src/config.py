import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Config:
    # Configuration de l'application
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    SECRET_KEY = os.getenv("SECRET_KEY", "secret-key-pour-le-developpement")
    
    # Configuration de la base de données
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///cspe.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuration du modèle
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "mistral:latest")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    
    # Chemins
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Instance de configuration
config = Config()
