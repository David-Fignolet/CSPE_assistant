# 🚀 Guide de Démarrage Rapide - Assistant CSPE

## 🎯 Démarrage en 3 étapes

### 1️⃣ **Installation Minimale** (2 minutes)
```bash
# Cloner le projet
git clone [URL_DU_REPO]
cd assistant-cspe

# Installer les dépendances minimales
pip install -r requirements_minimal.txt
```

### 2️⃣ **Lancement Sécurisé** (30 secondes)
```bash
# Lancement avec script sécurisé
python launch_safe.py

# OU directement en mode démo
python launch_demo.py --mode=demo
```

### 3️⃣ **Accès à l'Interface**
- Ouvrez votre navigateur à l'adresse affichée (généralement http://localhost:8501)
- L'interface se lance automatiquement

---

## 🛠️ Résolution des Problèmes Courants

### ❌ **"ModuleNotFoundError: No module named 'streamlit'"**
```bash
# Solution
pip install streamlit pandas plotly
```

### ❌ **"Port 8501 already in use"**
```bash
# Le script trouve automatiquement un port libre
# OU forcer un port spécifique
streamlit run demo_entretien.py --server.port 8502
```

### ❌ **"LLM/Ollama non disponible"**
- ✅ **Normal en mode démo** - L'application bascule automatiquement sur des données simulées
- Pour activer Ollama (optionnel):
  ```bash
  # Installer Ollama
  curl -fsSL https://ollama.ai/install.sh | sh
  
  # Télécharger Mistral
  ollama pull mistral:7b
  ```

### ❌ **"Erreur base de données"**
```bash
# Créer les dossiers nécessaires
mkdir -p data logs uploads temp

# Réinitialiser la base
rm -f cspe_local.db
python -c "from database_memory import DatabaseManager; db = DatabaseManager(); db.init_db()"
```

---

## 📋 Modes de Fonctionnement

### 🎯 **Mode Démo** (Recommandé pour commencer)
```bash
python launch_safe.py  # Choisir option 1
```
- ✅ Aucune dépendance externe
- ✅ Données de démonstration incluses
- ✅ Parfait pour les présentations
- ⚠️ Pas de persistance des données

### 🏭 **Mode Complet**
```bash
python launch_safe.py  # Choisir option 2
```
- ✅ Toutes les fonctionnalités
- ✅ Base de données SQLite locale
- ✅ Export PDF/CSV
- ⚠️ Nécessite plus de dépendances

### 🔍 **Mode Diagnostic**
```bash
python launch_safe.py  # Choisir option 3
```
- ✅ Vérifie l'environnement
- ✅ Identifie les problèmes
- ✅ Propose des solutions

---

## 🐳 Avec Docker (Alternative)

### Installation complète avec Docker
```bash
# Construire et lancer
docker-compose up -d

# Vérifier les logs
docker-compose logs -f

# Arrêter
docker-compose down
```

---

## 💡 Conseils pour la Démonstration

1. **Utilisez le mode démo** - Plus stable et sans dépendances
2. **Préparez des documents exemples** - Utilisez ceux fournis dans l'interface
3. **Testez avant** - Lancez l'application 5 minutes avant la démo
4. **Ayez un plan B** - Screenshots ou vidéo de secours

---

## 🆘 Support Rapide

### Commandes de Diagnostic
```bash
# Vérifier Python
python --version

# Vérifier les packages installés
pip list | grep -E "streamlit|pandas|plotly"

# Tester l'import des modules
python -c "import streamlit; print('✅ Streamlit OK')"
python -c "import pandas; print('✅ Pandas OK')"

# Nettoyer l'installation
pip cache purge
pip install --upgrade --force-reinstall streamlit
```

### Réinstallation Complète
```bash
# Créer un environnement virtuel propre
python -m venv venv_cspe
source venv_cspe/bin/activate  # Linux/Mac
# OU
venv_cspe\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements_minimal.txt
```

---

## ✅ Checklist Avant Démonstration

- [ ] Python 3.7+ installé
- [ ] Streamlit fonctionne (`streamlit hello`)
- [ ] Mode démo testé
- [ ] Port 8501 libre
- [ ] Navigateur moderne (Chrome/Firefox/Edge)
- [ ] Documents de test prêts
- [ ] Plan de secours (screenshots)

---

## 📞 Contact

En cas de problème urgent:
- 📧 Email: [michellarrieuxd@gmail.com]


**Bon courage pour votre démonstration ! 🎉**