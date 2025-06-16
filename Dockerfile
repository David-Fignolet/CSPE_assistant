FROM python:3.11-slim

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    tesseract-ocr-fra \
    && rm -rf /var/lib/apt/lists/*

# Création des dossiers nécessaires
WORKDIR /app

# Installation des dépendances Python
COPY requirements/requirements.txt requirements/constraints.txt ./

# Installer les dépendances principales
RUN pip install --no-cache-dir --ignore-installed -r requirements.txt -c constraints.txt

# Copie du code de l'application
COPY . .

# Configuration de l'environnement
ENV PYTHONPATH=/app

# Exposition des ports
EXPOSE 8501

# Commande de démarrage
CMD ["streamlit", "run", "src/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]