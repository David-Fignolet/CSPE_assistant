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
