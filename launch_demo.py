#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de lancement simplifié pour la démo entretien
Assistant CSPE - Conseil d'État

Usage: python launch_demo.py [--mode=demo|full|diagnostic]
"""

import sys
import subprocess
import os
import argparse
from pathlib import Path

def check_dependencies():
    """Vérifie les dépendances minimales"""
    required_packages = ['streamlit', 'pandas', 'plotly']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Packages manquants: {', '.join(missing_packages)}")
        print("📦 Installation automatique...")
        
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ {package} installé")
            except subprocess.CalledProcessError:
                print(f"❌ Échec installation {package}")
                return False
    
    return True

def launch_demo():
    """Lance la version démo pour l'entretien"""
    print("🚀 Lancement de la démo entretien...")
    print("🌐 Ouverture de l'interface dans votre navigateur...")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            'demo_entretien.py',
            '--server.port', '8501',
            '--server.address', '0.0.0.0',
            '--browser.gatherUsageStats', 'false'
        ])
    except KeyboardInterrupt:
        print("\n✅ Démo fermée par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {e}")

def launch_full():
    """Lance l'application complète"""
    print("🚀 Lancement de l'application complète...")
    print("🌐 Ouverture de l'interface dans votre navigateur...")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            'app.py',
            '--server.port', '8501',
            '--server.address', '0.0.0.0',
            '--browser.gatherUsageStats', 'false'
        ])
    except KeyboardInterrupt:
        print("\n✅ Application fermée par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {e}")

def launch_diagnostic():
    """Lance le diagnostic système"""
    print("🔍 Lancement du diagnostic système...")
    print("🌐 Ouverture du diagnostic dans votre navigateur...")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            'diagnostic.py',
            '--server.port', '8502',
            '--server.address', '0.0.0.0',
            '--browser.gatherUsageStats', 'false'
        ])
    except KeyboardInterrupt:
        print("\n✅ Diagnostic fermé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {e}")

def show_help():
    """Affiche l'aide"""
    print("""
🏛️ Assistant CSPE - Conseil d'État
Système de Classification Intelligente avec LLM

🚀 MODES DE LANCEMENT :

1. 🎯 DÉMO ENTRETIEN (recommandé pour la présentation)
   python launch_demo.py --mode=demo
   
   ✨ Version simplifiée avec données de démonstration
   ✨ Parfait pour présenter les fonctionnalités
   ✨ Ne nécessite pas Ollama/Docker

2. 🏭 APPLICATION COMPLÈTE
   python launch_demo.py --mode=full
   
   ✨ Version complète avec base de données
   ✨ Toutes les fonctionnalités disponibles
   ✨ Nécessite configuration complète

3. 🔍 DIAGNOSTIC SYSTÈME
   python launch_demo.py --mode=diagnostic
   
   ✨ Vérification de l'environnement
   ✨ Test des dépendances
   ✨ Recommandations de configuration

📋 EXEMPLES :
python launch_demo.py                    # Mode démo par défaut
python launch_demo.py --mode=demo        # Mode démo explicite
python launch_demo.py --mode=full        # Application complète
python launch_demo.py --mode=diagnostic  # Diagnostic

🆘 AIDE :
python launch_demo.py --help

📧 Support : david.michel-larrieux@conseil-etat.fr
""")

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description='Lanceur Assistant CSPE - Conseil d\'État',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--mode', 
        choices=['demo', 'full', 'diagnostic'], 
        default='demo',
        help='Mode de lancement (demo par défaut)'
    )
    
    parser.add_argument(
        '--help-extended', 
        action='store_true',
        help='Affiche l\'aide détaillée'
    )
    
    # Traitement spécial pour --help-extended
    if '--help-extended' in sys.argv:
        show_help()
        return
    
    args = parser.parse_args()
    
    # En-tête
    print("=" * 60)
    print("🏛️  ASSISTANT CSPE - CONSEIL D'ÉTAT")
    print("    Système de Classification Intelligente avec LLM")
    print("    Développé par David Michel-Larrieux")
    print("=" * 60)
    
    # Vérification de l'environnement
    print("🔍 Vérification de l'environnement...")
    
    # Vérifier Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ requis")
        print(f"   Version actuelle: {sys.version}")
        return 1
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Vérifier le répertoire
    required_files = {
        'demo': ['demo_entretien.py'],
        'full': ['app.py', 'document_processor.py', 'database_memory.py'],
        'diagnostic': ['diagnostic.py']
    }
    
    missing_files = []
    for file in required_files[args.mode]:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Fichiers manquants: {', '.join(missing_files)}")
        print("   Vérifiez que vous êtes dans le bon répertoire")
        return 1
    
    # Vérifier les dépendances
    if not check_dependencies():
        print("❌ Impossible d'installer les dépendances requises")
        return 1
    
    print("✅ Environnement OK")
    print()
    
    # Lancement selon le mode
    if args.mode == 'demo':
        print("🎯 MODE DÉMO ENTRETIEN")
        print("   Interface simplifiée avec données de démonstration")
        print("   Parfait pour présenter les fonctionnalités clés")
        print()
        launch_demo()
        
    elif args.mode == 'full':
        print("🏭 MODE APPLICATION COMPLÈTE") 
        print("   Toutes les fonctionnalités disponibles")
        print("   Base de données et intégrations complètes")
        print()
        launch_full()
        
    elif args.mode == 'diagnostic':
        print("🔍 MODE DIAGNOSTIC SYSTÈME")
        print("   Vérification complète de l'environnement")
        print("   Recommandations de configuration")
        print()
        launch_diagnostic()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Au revoir !")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1)