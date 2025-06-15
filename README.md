# CSPE Assistant - Assistant CSPE - Conseil d'État

Système d'aide à l'instruction des réclamations CSPE (Contribution au Service Public de l'Électricité) pour le Conseil d'État.

## Fonctionnalités

- Analyse automatique des dossiers CSPE
- Vérification des critères légaux
- Extraction des montants par société et période
- Génération de rapports professionnels
- Interface utilisateur Streamlit
- Intégration avec LLM local (Ollama)

## Installation

1. Cloner le dépôt
2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurer Docker :
```bash
docker-compose up -d
```

4. Lancer l'application :
```bash
python app.py
```

## Structure du Projet

- `app.py` : Application Streamlit principale
- `Dockerfile` : Configuration Docker
- `docker-compose.yml` : Configuration des services
- `requirements.txt` : Dépendances Python
- `start.bat` : Script de démarrage Windows
- `start.sh` : Script de démarrage Linux/Mac

## Utilisation

1. Importer les documents (PDF, DOCX, TXT, images)
2. Lancer l'analyse
3. Vérifier les résultats d'analyse
4. Générer le rapport final

## Tests

1. Lancer les tests :
```bash
python -m pytest tests
```

2. Lancer le diagnostic :
```bash
python diagnostic.py
```

## Dépannage

1. Vérifier les logs :
```bash
tail -f logs/app.log
```

2. Vérifier les logs Docker :
```bash
docker-compose logs
```

# Assistant CSPE - Conseil d'État

## Description
Système d'aide à l'instruction des réclamations CSPE pour le Conseil d'État.

## Installation

### Prérequis
- Python 3.8+
- PostgreSQL 13+
- Polices Marianne et Lato installées
- Tesseract-OCR
- OpenCV