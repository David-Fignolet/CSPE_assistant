#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic du Système Assistant CSPE
Conseil d'État - Cellule IA et Innovation

Auteur: David Michel-Larrieux
Date: Décembre 2024
"""

import streamlit as st
import os
import sys
import platform
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import json

# Configuration de la page
st.set_page_config(
    page_title="🔍 Diagnostic Système CSPE",
    page_icon="🔍",
    layout="wide"
)

def check_python_version():
    """Vérifie la version de Python"""
    version = sys.version_info
    return {
        'version': f"{version.major}.{version.minor}.{version.micro}",
        'compatible': version.major == 3 and version.minor >= 8,
        'details': sys.version
    }

def check_dependencies():
    """Vérifie les dépendances Python importantes"""
    dependencies = {
        'streamlit': {'required': True, 'installed': False, 'version': None},
        'pandas': {'required': True, 'installed': False, 'version': None},
        'sqlalchemy': {'required': True, 'installed': False, 'version': None},
        'PyPDF2': {'required': True, 'installed': False, 'version': None},
        'pillow': {'required': True, 'installed': False, 'version': None},
        'ollama': {'required': False, 'installed': False, 'version': None},
        'pytesseract': {'required': False, 'installed': False, 'version': None},
        'opencv-python': {'required': False, 'installed': False, 'version': None},
        'fpdf2': {'required': False, 'installed': False, 'version': None}
    }
    
    for dep_name in dependencies:
        try:
            module = __import__(dep_name.replace('-', '_').lower())
            dependencies[dep_name]['installed'] = True
            if hasattr(module, '__version__'):
                dependencies[dep_name]['version'] = module.__version__
            elif hasattr(module, 'VERSION'):
                dependencies[dep_name]['version'] = str(module.VERSION)
            else:
                dependencies[dep_name]['version'] = 'Unknown'
        except ImportError:
            dependencies[dep_name]['installed'] = False
    
    return dependencies

def check_system_resources():
    """Vérifie les ressources système"""
    try:
        import psutil
        
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_count': cpu_count,
            'cpu_percent': cpu_percent,
            'memory_total_gb': round(memory.total / (1024**3), 2),
            'memory_available_gb': round(memory.available / (1024**3), 2),
            'memory_percent': memory.percent,
            'disk_total_gb': round(disk.total / (1024**3), 2),
            'disk_free_gb': round(disk.free / (1024**3), 2),
            'disk_percent': round((disk.used / disk.total) * 100, 1)
        }
    except ImportError:
        return {
            'error': 'psutil non disponible',
            'cpu_count': 'Unknown',
            'memory_total_gb': 'Unknown',
            'disk_free_gb': 'Unknown'
        }

def check_database_connection():
    """Vérifie la connexion à la base de données"""
    try:
        from database_memory import DatabaseManager
        
        # Test avec SQLite par défaut
        db = DatabaseManager("sqlite:///test_diagnostic.db")
        db.init_db()
        
        # Test d'écriture/lecture
        test_data = {
            'numero_dossier': 'TEST-DIAG-001',
            'demandeur': 'Test Diagnostic',
            'activite': 'Test',
            'date_reclamation': datetime.now().date(),
            'periode_debut': 2010,
            'periode_fin': 2012,
            'montant_reclame': 100.0,
            'statut': 'TEST',
            'analyste': 'Diagnostic'
        }
        
        dossier_id = db.add_dossier(test_data)
        if dossier_id:
            # Nettoyer le test
            db.delete_dossier(dossier_id)
            # Supprimer le fichier de test
            if os.path.exists("test_diagnostic.db"):
                os.remove("test_diagnostic.db")
            
            return {'status': 'OK', 'message': 'Base de données fonctionnelle'}
        else:
            return {'status': 'ERROR', 'message': 'Échec écriture base de données'}
            
    except Exception as e:
        return {'status': 'ERROR', 'message': f'Erreur base de données: {str(e)}'}

def check_ollama_service():
    """Vérifie la disponibilité du service Ollama"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/version', timeout=5)
        if response.status_code == 200:
            version_info = response.json()
            return {
                'status': 'AVAILABLE',
                'version': version_info.get('version', 'Unknown'),
                'message': 'Service Ollama disponible'
            }
        else:
            return {
                'status': 'ERROR',
                'message': f'Service Ollama répond avec code {response.status_code}'
            }
    except requests.exceptions.ConnectionError:
        return {
            'status': 'UNAVAILABLE',
            'message': 'Service Ollama non démarré (normal pour la démo)'
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'message': f'Erreur vérification Ollama: {str(e)}'
        }

def check_docker_availability():
    """Vérifie la disponibilité de Docker"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.strip()
            return {'status': 'AVAILABLE', 'version': version}
        else:
            return {'status': 'ERROR', 'message': 'Docker installé mais non fonctionnel'}
    except subprocess.TimeoutExpired:
        return {'status': 'ERROR', 'message': 'Docker timeout'}
    except FileNotFoundError:
        return {'status': 'NOT_INSTALLED', 'message': 'Docker non installé'}
    except Exception as e:
        return {'status': 'ERROR', 'message': f'Erreur Docker: {str(e)}'}

def check_file_permissions():
    """Vérifie les permissions de fichiers"""
    current_dir = Path.cwd()
    checks = {
        'read_current_dir': os.access(current_dir, os.R_OK),
        'write_current_dir': os.access(current_dir, os.W_OK),
        'execute_current_dir': os.access(current_dir, os.X_OK)
    }
    
    # Vérifier quelques dossiers importants
    important_dirs = ['data', 'logs', 'uploads']
    for dir_name in important_dirs:
        dir_path = current_dir / dir_name
        if dir_path.exists():
            checks[f'read_{dir_name}'] = os.access(dir_path, os.R_OK)
            checks[f'write_{dir_name}'] = os.access(dir_path, os.W_OK)
        else:
            checks[f'{dir_name}_exists'] = False
    
    return checks

def run_comprehensive_diagnostic():
    """Lance un diagnostic complet du système"""
    st.title("🔍 Diagnostic Système Assistant CSPE")
    st.markdown("### Analyse complète de l'environnement")
    
    # Informations système
    st.subheader("🖥️ Informations Système")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Système d'exploitation:** {platform.system()} {platform.release()}")
        st.write(f"**Architecture:** {platform.machine()}")
        st.write(f"**Processeur:** {platform.processor()}")
        st.write(f"**Nom de machine:** {platform.node()}")
    
    with col2:
        python_info = check_python_version()
        if python_info['compatible']:
            st.success(f"**Python:** {python_info['version']} ✅")
        else:
            st.error(f"**Python:** {python_info['version']} ❌ (Requis: 3.8+)")
        
        st.write(f"**Dossier de travail:** {Path.cwd()}")
        st.write(f"**Date du diagnostic:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Ressources système
    st.subheader("⚡ Ressources Système")
    resources = check_system_resources()
    
    if 'error' not in resources:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🔥 CPU", f"{resources['cpu_count']} cœurs", f"{resources['cpu_percent']}%")
        with col2:
            st.metric("🧠 RAM Total", f"{resources['memory_total_gb']} GB")
        with col3:
            st.metric("💾 RAM Libre", f"{resources['memory_available_gb']} GB", 
                     f"-{resources['memory_percent']}%")
        with col4:
            st.metric("💿 Disque Libre", f"{resources['disk_free_gb']} GB", 
                     f"-{resources['disk_percent']}%")
        
        # Alertes ressources
        if resources['memory_percent'] > 80:
            st.warning("⚠️ Utilisation mémoire élevée")
        if resources['disk_percent'] > 90:
            st.error("❌ Espace disque critique")
        if resources['disk_free_gb'] < 1:
            st.error("❌ Moins de 1 GB d'espace libre")
    else:
        st.warning("⚠️ Impossible de récupérer les informations ressources")
    
    # Dépendances Python
    st.subheader("🐍 Dépendances Python")
    deps = check_dependencies()
    
    required_ok = 0
    required_total = 0
    optional_ok = 0
    optional_total = 0
    
    for dep_name, info in deps.items():
        if info['required']:
            required_total += 1
            if info['installed']:
                required_ok += 1
        else:
            optional_total += 1
            if info['installed']:
                optional_ok += 1
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📦 Dépendances Requises**")
        for dep_name, info in deps.items():
            if info['required']:
                if info['installed']:
                    st.success(f"✅ {dep_name} ({info['version']})")
                else:
                    st.error(f"❌ {dep_name} - Non installé")
    
    with col2:
        st.markdown("**🔧 Dépendances Optionnelles**")
        for dep_name, info in deps.items():
            if not info['required']:
                if info['installed']:
                    st.success(f"✅ {dep_name} ({info['version']})")
                else:
                    st.warning(f"⚠️ {dep_name} - Non installé (optionnel)")
    
    # Résumé dépendances
    st.info(f"**Résumé:** {required_ok}/{required_total} dépendances requises ✅ | "
            f"{optional_ok}/{optional_total} optionnelles ✅")
    
    # Base de données
    st.subheader("🗄️ Base de Données")
    db_status = check_database_connection()
    
    if db_status['status'] == 'OK':
        st.success(f"✅ {db_status['message']}")
    else:
        st.error(f"❌ {db_status['message']}")
    
    # Service LLM (Ollama)
    st.subheader("🤖 Service LLM (Ollama)")
    ollama_status = check_ollama_service()
    
    if ollama_status['status'] == 'AVAILABLE':
        st.success(f"✅ {ollama_status['message']} - Version: {ollama_status.get('version', 'Unknown')}")
    elif ollama_status['status'] == 'UNAVAILABLE':
        st.info(f"ℹ️ {ollama_status['message']}")
    else:
        st.warning(f"⚠️ {ollama_status['message']}")
    
    # Docker
    st.subheader("🐳 Docker")
    docker_status = check_docker_availability()
    
    if docker_status['status'] == 'AVAILABLE':
        st.success(f"✅ Docker disponible - {docker_status['version']}")
    elif docker_status['status'] == 'NOT_INSTALLED':
        st.warning("⚠️ Docker non installé (optionnel pour développement)")
    else:
        st.error(f"❌ {docker_status['message']}")
    
    # Permissions fichiers
    st.subheader("🔐 Permissions et Accès")
    perms = check_file_permissions()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Permissions Dossier Courant**")
        if perms.get('read_current_dir', False):
            st.success("✅ Lecture")
        else:
            st.error("❌ Lecture")
        
        if perms.get('write_current_dir', False):
            st.success("✅ Écriture")
        else:
            st.error("❌ Écriture")
    
    with col2:
        st.markdown("**Dossiers Spéciaux**")
        special_dirs = ['data', 'logs', 'uploads']
        for dir_name in special_dirs:
            if perms.get(f'{dir_name}_exists', True):
                if perms.get(f'write_{dir_name}', False):
                    st.success(f"✅ {dir_name}/")
                else:
                    st.warning(f"⚠️ {dir_name}/ (lecture seule)")
            else:
                st.info(f"ℹ️ {dir_name}/ (à créer)")
    
    # Résumé global
    st.subheader("📊 Résumé du Diagnostic")
    
    # Calcul du score global
    score_components = [
        python_info['compatible'],  # Python OK
        required_ok == required_total,  # Toutes les dépendances requises
        db_status['status'] == 'OK',  # Base de données OK
        perms.get('read_current_dir', False) and perms.get('write_current_dir', False),  # Permissions OK
    ]
    
    score = sum(score_components) / len(score_components) * 100
    
    if score >= 90:
        st.success(f"🎉 Système excellent ! Score: {score:.0f}%")
        st.balloons()
    elif score >= 70:
        st.info(f"✅ Système fonctionnel. Score: {score:.0f}%")
    else:
        st.warning(f"⚠️ Système nécessite des corrections. Score: {score:.0f}%")
    
    # Actions recommandées
    st.subheader("🛠️ Actions Recommandées")
    
    recommendations = []
    
    if not python_info['compatible']:
        recommendations.append("🔴 **Critique:** Mettre à jour Python vers la version 3.8+")
    
    if required_ok < required_total:
        missing_deps = [name for name, info in deps.items() 
                       if info['required'] and not info['installed']]
        recommendations.append(f"🔴 **Critique:** Installer les dépendances manquantes: {', '.join(missing_deps)}")
    
    if db_status['status'] != 'OK':
        recommendations.append("🟡 **Important:** Vérifier la configuration de la base de données")
    
    if ollama_status['status'] not in ['AVAILABLE', 'UNAVAILABLE']:
        recommendations.append("🟡 **Optionnel:** Configurer le service Ollama pour l'IA")
    
    if not perms.get('write_current_dir', False):
        recommendations.append("🔴 **Critique:** Résoudre les problèmes de permissions d'écriture")
    
    if docker_status['status'] == 'NOT_INSTALLED':
        recommendations.append("🔵 **Optionnel:** Installer Docker pour le déploiement containerisé")
    
    if not recommendations:
        st.success("✅ Aucune action requise - Le système est prêt !")
    else:
        for rec in recommendations:
            if "Critique" in rec:
                st.error(rec)
            elif "Important" in rec:
                st.warning(rec)
            else:
                st.info(rec)
    
    # Export du diagnostic
    st.subheader("💾 Export du Diagnostic")
    
    diagnostic_data = {
        'timestamp': datetime.now().isoformat(),
        'system': {
            'os': f"{platform.system()} {platform.release()}",
            'architecture': platform.machine(),
            'python_version': python_info['version'],
            'python_compatible': python_info['compatible']
        },
        'resources': resources,
        'dependencies': deps,
        'database': db_status,
        'ollama': ollama_status,
        'docker': docker_status,
        'permissions': perms,
        'score': score,
        'recommendations': recommendations
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Copier Diagnostic", type="secondary"):
            diagnostic_text = json.dumps(diagnostic_data, indent=2, ensure_ascii=False)
            st.code(diagnostic_text, language='json')
    
    with col2:
        diagnostic_json = json.dumps(diagnostic_data, indent=2, ensure_ascii=False)
        st.download_button(
            "💾 Télécharger Diagnostic",
            diagnostic_json.encode('utf-8'),
            f"diagnostic_cspe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json"
        )

def main():
    """Fonction principale"""
    try:
        run_comprehensive_diagnostic()
    except Exception as e:
        st.error(f"❌ Erreur durant le diagnostic: {str(e)}")
        st.info("💡 Le diagnostic peut être partiellement incomplet")

if __name__ == "__main__":
    main()