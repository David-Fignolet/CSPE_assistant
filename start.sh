#!/bin/bash

# Vérifier Docker
docker --version > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Docker n'est pas installé"
    echo "📥 Téléchargez Docker Desktop : https://docker.com/get-started"
    exit 1
fi

echo "✅ Docker détecté"

echo "🔧 Construction des containers..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ Échec de la construction"
    exit 1
fi

echo "🚀 Démarrage des services..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Échec du démarrage"
    exit 1
fi

echo "⏳ Attente démarrage des services..."
sleep 10

echo "📥 Téléchargement du modèle..."
docker exec cspe_ollama ollama pull ${DEFAULT_MODEL:-mistral:latest}

if [ $? -ne 0 ]; then
    echo "⚠️ Échec téléchargement modèle"
else
    echo "✅ Modèle téléchargé"
fi

echo ""
echo "✅ Système démarré avec succès !"
echo ""
echo "🌐 Interface web : http://localhost:8501"
echo "🤖 API Ollama : http://localhost:11434"
echo ""
echo "📋 Commandes utiles :"
echo "  - Arrêter : docker-compose down"
echo "  - Logs app : docker-compose logs cspe_app"
echo "  - Logs LLM : docker-compose logs ollama"
