#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DÉMO RAPIDE ET SÛRE POUR L'ENTRETIEN
Assistant CSPE - Conseil d'État

Ce script lance une version ultra-simplifiée garantie sans erreur
pour la présentation devant le jury.
"""

import sys
import subprocess
import os

def check_minimal_requirements():
    """Vérifie les dépendances minimales"""
    required = ['streamlit', 'pandas']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return missing

def install_missing(packages):
    """Installe les packages manquants"""
    for package in packages:
        print(f"📦 Installation de {package}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def main():
    """Lancement principal"""
    print("🏛️ ASSISTANT CSPE - DÉMO ENTRETIEN CONSEIL D'ÉTAT")
    print("=" * 60)
    print("Version ultra-sûre pour présentation")
    print("=" * 60)
    
    # Vérifications
    print("🔍 Vérification de l'environnement...")
    
    # Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ requis")
        input("Appuyez sur Entrée pour fermer...")
        return 1
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Dépendances
    missing = check_minimal_requirements()
    if missing:
        print(f"📦 Installation des dépendances: {', '.join(missing)}")
        try:
            install_missing(missing)
        except Exception as e:
            print(f"❌ Erreur installation: {e}")
            input("Appuyez sur Entrée pour fermer...")
            return 1
    
    print("✅ Dépendances OK")
    
    # Vérifier fichier démo
    if not os.path.exists('demo_entretien.py'):
        print("❌ Fichier demo_entretien.py manquant")
        print("💡 Assurez-vous d'être dans le bon répertoire")
        input("Appuyez sur Entrée pour fermer...")
        return 1
    
    print("✅ Fichier démo trouvé")
    
    # Lancement
    print("\n🚀 LANCEMENT DE LA DÉMO...")
    print("📱 L'interface va s'ouvrir dans votre navigateur")
    print("\n⚠️ IMPORTANT: Gardez cette fenêtre ouverte pendant la démo")
    print("✋ Pour arrêter: Ctrl+C dans cette fenêtre")
    print("\n" + "="*60)
    
    try:
        # Lancement sécurisé avec gestion des ports
        ports = [8501, 8502, 8503]  # Liste des ports à tester
        for port in ports:
            try:
                print(f"\nEssayage le port {port}...")
                # Lancement sécurisé
                print("\nDémarrage du serveur Streamlit...")
                
                # Ajout de redirection de la sortie pour voir les logs
                with open('streamlit.log', 'w') as log_file:
                    process = subprocess.Popen([
                        sys.executable, '-m', 'streamlit', 'run',
                        'demo_entretien.py',
                        '--server.port', str(port),
                        '--server.address', '0.0.0.0',
                        '--browser.gatherUsageStats', 'false',
                        '--server.headless', 'false'
                    ],
                    stdout=log_file,
                    stderr=log_file
                    )
                    
                    # Attendre quelques secondes pour que le serveur démarre
                    print("\nAttente du démarrage du serveur (5 secondes)...")
                    import time
                    time.sleep(5)
                    
                    # Vérifier si le processus est toujours en cours
                    if process.poll() is None:
                        print(f"\n🌐 URL: http://localhost:{port}")
                        print("\nServeur démarré avec succès !")
                        break  # Si le serveur démarre, on sort de la boucle
                    else:
                        print(f"❌ Le serveur n'a pas démarré sur le port {port}")
                        continue
            except subprocess.CalledProcessError as e:
                if "Port" in str(e):
                    print(f"⚠️ Le port {port} est déjà utilisé, essayons le suivant...")
                    continue
                else:
                    raise
            except Exception as e:
                print(f"❌ Erreur lors du démarrage sur le port {port}: {e}")
                continue
    except KeyboardInterrupt:
        print("\n\n✅ Démo fermée par l'utilisateur")
        print("🎯 Bonne chance pour votre entretien !")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        print("\n💡 Solutions:")
        print("1. Vérifiez que Streamlit est installé: pip install streamlit")
        print("2. Vérifiez que vous êtes dans le bon dossier")
        print("3. Essayez: python -m streamlit run demo_entretien.py")
    
    input("\nAppuyez sur Entrée pour fermer...")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)