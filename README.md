# CSPE Assistant - Assistant CSPE - Conseil d'État

Système d'aide à l'instruction des réclamations CSPE (Contribution au Service Public de l'Électricité) pour le Conseil d'État.

## Fonctionnalités

- 🤖 Analyse automatique des dossiers CSPE avec extraction intelligente
- ✅ Vérification automatisée des critères légaux
- 💰 Extraction des montants par société et période
- 📊 Génération de rapports professionnels
- 📱 Interface utilisateur Streamlit moderne
- 🤖 Intégration avec LLM local (Ollama)
- 🤔 Système d'extraction automatique des métadonnées
- 📋 Interface experte avec validation et complément d'instruction

## Nouveautés

### Extraction Automatique des Métadonnées
- Détection automatique des numéros de dossier
- Extraction intelligente du nom du demandeur
- Détection automatique de l'activité
- Extraction de la période couverte
- Suggestions automatiques dans le formulaire

### Interface Expertisée
- Validation et complément d'instruction
- Génération de rapports PDF
- Interface adaptée aux experts CSPE
- Indicateurs de confiance pour les extractions

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
- `database_memory.py` : Gestion de la base de données
- `document_processor.py` : Traitement des documents
- `diagnostic.py` : Outil de diagnostic système
- `tests/` : Tests unitaires et validation
- `Dockerfile` : Configuration Docker
- `docker-compose.yml` : Configuration des services
- `requirements.txt` : Dépendances Python
- `start.bat` : Script de démarrage Windows
- `start.sh` : Script de démarrage Linux/Mac

## Utilisation

1. Importer les documents (PDF, DOCX, TXT, images)
2. Lancer l'analyse
3. Vérifier les suggestions automatiques
4. Valider ou compléter les métadonnées
5. Générer le rapport final

## Tests et Validation

1. Lancer les tests unitaires :
```bash
python -m pytest tests
```

2. Vérifier la conformité avec les dossiers de test :
```bash
python tests/validation.py
```

3. Lancer le diagnostic système :
```bash
python diagnostic.py
```

## Dépannage

1. Vérifier les logs de l'application :
```bash
tail -f logs/app.log
```

2. Vérifier les logs Docker :
```bash
docker-compose logs
```

3. Vérifier le diagnostic système :
```bash
python diagnostic.py
```

## Prérequis Techniques

- Python 3.8+
- PostgreSQL 13+
- Polices Marianne et Lato installées
- Tesseract-OCR (optionnel pour OCR)
- OpenCV (optionnel pour traitement d'images)
- Docker et Docker Compose

## Configuration

1. Créer un fichier `.env` avec les variables suivantes :
```env
DATABASE_URL=sqlite:///cspe.db
OLLAMA_URL=http://localhost:11434
DEFAULT_MODEL=mistral
```

2. Configurer la base de données :
```bash
python database_memory.py init
```

## Sécurité

- Le système utilise uniquement des modèles LLM locaux (Mistral via Ollama)
- Les données restent sur site
- Conformité avec les normes de sécurité du Conseil d'État

## Support

Pour toute question ou problème, contacter le support technique du Conseil d'État.