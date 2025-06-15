@echo off
chcp 65001 >nul

pushd %~dp0
echo ==============================================
echo 🏛️ Démarrage Assistant CSPE - Conseil d'État
echo ==============================================

docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker n'est pas installé
    echo 📥 Téléchargez Docker Desktop : https://docker.com/get-started
    pause
    exit /b 1
)

echo ✅ Docker détecté

echo 🔧 Construction des containers...
docker-compose build
if %errorlevel% neq 0 (
    echo ❌ Échec de la construction
    pause
    exit /b 1
)

echo 🚀 Démarrage des services...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ❌ Échec du démarrage
    pause
    exit /b 1
)

echo ⏳ Attente démarrage des services...
timeout /t 10 /nobreak >nul

echo 📥 Téléchargement du modèle Mistral...
docker exec cspe_ollama ollama pull mistral:7b
if %errorlevel% neq 0 (
    echo ⚠️ Échec téléchargement modèle
) else (
    echo ✅ Modèle Mistral téléchargé
)

echo.
echo ✅ Système démarré avec succès !
echo.
echo 🌐 Interface web : http://localhost:8501
echo 🤖 API Ollama : http://localhost:11434
echo.
echo 📋 Commandes utiles :
echo   - Arrêter : docker-compose down
echo   - Logs app : docker-compose logs cspe_app
echo   - Logs LLM : docker-compose logs ollama

echo.
echo 📖 Ouverture de l'interface web dans votre navigateur par défaut...
start http://localhost:8501

echo.
echo Appuyez sur une touche pour fermer cette fenêtre...
pause >nul

popd
