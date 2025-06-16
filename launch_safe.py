#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de lancement sécurisé pour l'Assistant CSPE
Garantit un démarrage sans erreur même avec des dépendances manquantes
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def check_python_version():
    """Vérifie la version de Python"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ requis")
        print(f"   Version actuelle: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_and_install_minimal():
    """Vérifie et installe les dépendances minimales"""
    essential_packages = ['streamlit', 'pandas']
    missing = []
    
    for package in essential_packages:
        try:
            __import__(package)
            print(f"✅ {package} installé")
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"\n📦 Installation des packages essentiels: {', '.join(missing)}")
        for package in missing:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '--quiet'])
                print(f"   ✅ {package} installé avec succès")
            except Exception as e:
                print(f"   ❌ Erreur installation {package}: {e}")
                return False
    
    return True

def find_free_port(start_port=8501, max_attempts=10):
    """Trouve un port libre pour Streamlit"""
    import socket
    
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except:
            continue
    return None

def launch_app(mode='demo'):
    """Lance l'application dans le mode spécifié"""
    # Déterminer quel fichier lancer
    if mode == 'demo':
        app_file = 'demo_entretien.py'
    elif mode == 'full':
        app_file = 'app.py'
    elif mode == 'diagnostic':
        app_file = 'diagnostic.py'
    else:
        app_file = 'demo_entretien.py'
    
    # Vérifier que le fichier existe
    if not Path(app_file).exists():
        print(f"❌ Fichier {app_file} introuvable")
        
        # Chercher des alternatives
        alternatives = []
        for file in ['demo_entretien.py', 'app.py', 'diagnostic.py']:
            if Path(file).exists():
                alternatives.append(file)
        
        if alternatives:
            app_file = alternatives[0]
            print(f"   ✅ Utilisation de {app_file} à la place")
        else:
            print("   ❌ Aucun fichier d'application trouvé")
            return False
    
    # Trouver un port libre
    port = find_free_port()
    if not port:
        print("❌ Aucun port libre trouvé")
        return False
    
    print(f"\n🚀 Lancement de l'application sur le port {port}...")
    print(f"📁 Fichier: {app_file}")
    print(f"🌐 URL: http://localhost:{port}")
    print("\n⚠️  Gardez cette fenêtre ouverte")
    print("✋ Pour arrêter: Ctrl+C\n")
    
    # Lancement avec gestion d'erreur
    try:
        # Créer le processus
        process = subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run',
            app_file,
            '--server.port', str(port),
            '--server.address', '0.0.0.0',
            '--browser.gatherUsageStats', 'false',
            '--logger.level', 'error'  # Réduire les logs
        ])
        
        # Attendre que l'utilisateur arrête
        process.wait()
        
    except KeyboardInterrupt:
        print("\n\n✅ Application fermée par l'utilisateur")
        return True
    except Exception as e:
        print(f"\n❌ Erreur lors du lancement: {e}")
        return False
    
    return True

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🏛️  ASSISTANT CSPE - LANCEMENT SÉCURISÉ")
    print("    Système de Classification Intelligente")
    print("=" * 60)
    
    # Étape 1: Vérifier Python
    if not check_python_version():
        input("\nAppuyez sur Entrée pour fermer...")
        return 1
    
    # Étape 2: Vérifier/Installer dépendances minimales
    print("\n🔍 Vérification des dépendances...")
    if not check_and_install_minimal():
        print("\n❌ Impossible d'installer les dépendances requises")
        print("💡 Essayez: pip install streamlit pandas")
        input("\nAppuyez sur Entrée pour fermer...")
        return 1
    
    # Étape 3: Déterminer le mode
    if len(sys.argv) > 1:
        mode = sys.argv[1].replace('--mode=', '')
    else:
        print("\n📋 Modes disponibles:")
        print("1. demo    - Démonstration (recommandé)")
        print("2. full    - Application complète")
        print("3. diagnostic - Diagnostic système")
        
        choice = input("\nChoisissez un mode (1/2/3) [défaut: 1]: ").strip()
        
        mode_map = {'1': 'demo', '2': 'full', '3': 'diagnostic'}
        mode = mode_map.get(choice, 'demo')
    
    print(f"\n🎯 Mode sélectionné: {mode}")
    
    # Étape 4: Vérifier les fichiers optionnels
    optional_files = {
        'document_processor.py': 'Traitement de documents',
        'database_memory.py': 'Gestion base de données',
        '.env': 'Configuration environnement'
    }
    
    print("\n📂 Vérification des fichiers optionnels:")
    for file, desc in optional_files.items():
        if Path(file).exists():
            print(f"   ✅ {file} - {desc}")
        else:
            print(f"   ⚠️  {file} - {desc} (non trouvé)")
    
    # Étape 5: Lancer l'application
    if not launch_app(mode):
        print("\n❌ Échec du lancement")
        input("\nAppuyez sur Entrée pour fermer...")
        return 1
    
    print("\n✅ Application fermée normalement")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        input("\nAppuyez sur Entrée pour fermer...")
        sys.exit(1)