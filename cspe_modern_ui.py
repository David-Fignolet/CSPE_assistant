import streamlit as st
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import tempfile

# Configuration de la page
st.set_page_config(
    page_title="CSPE - Analyse des contestations",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
def load_css():
    st.markdown("""
    <style>
        /* Police et couleurs principales */
        :root {
            --primary: #0055b7;
            --secondary: #f8f9fa;
            --success: #28a745;
            --danger: #dc3545;
            --warning: #ffc107;
            --light: #f8f9fa;
            --dark: #212529;
        }
        
        /* En-tête */
        .main-header {
            color: var(--primary);
            border-bottom: 2px solid var(--primary);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        
        /* Cartes */
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        /* Boutons */
        .stButton>button {
            background-color: var(--primary);
            color: white;
            border-radius: 4px;
            font-weight: 500;
            padding: 0.5rem 1rem;
            transition: all 0.2s;
        }
        
        .stButton>button:hover {
            background-color: #003d82;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Zone de dépôt */
        .upload-area {
            border: 2px dashed #ccc;
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
            margin: 1rem 0;
            background: #f8f9fa;
            transition: all 0.3s;
        }
        
        .upload-area:hover {
            border-color: var(--primary);
            background: #f1f7ff;
        }
        
        /* Badges de décision */
        .decision-badge {
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 600;
            margin: 0.5rem 0;
        }
        
        .decision-recevable {
            background-color: #d4edda;
            color: #155724;
        }
        
        .decision-irrecevable {
            background-color: #f8d7da;
            color: #721c24;
        }
        
        .decision-inconnu {
            background-color: #e2e3e5;
            color: #383d41;
        }
    </style>
    """, unsafe_allow_html=True)

# Classe d'analyse factice pour la démo
class CSPEAnalyzer:
    def analyze_file(self, file_path):
        # Simulation d'analyse
        return {
            'decision_globale': 'RECEVABLE',
            'criteria': {
                'delai_reclamation': {
                    'decision': 'CONFORME',
                    'details': 'Le délai de réclamation est respecté',
                    'confidence': 0.95
                },
                'periode_concernee': {
                    'decision': 'CONFORME',
                    'details': 'La période concernée est entre 2009 et 2015',
                    'confidence': 0.98
                },
                'prescription_quadriennale': {
                    'decision': 'NON_CONCERNE',
                    'details': 'La prescription quadriennale ne s\'applique pas',
                    'confidence': 0.99
                },
                'repercussion_client_final': {
                    'decision': 'A_VERIFIER',
                    'details': 'La répercussion au client final doit être vérifiée',
                    'confidence': 0.7
                }
            },
            'extracted_data': {
                'dates': ['2020-01-15', '2019-12-30'],
                'montants': [1500.50, 2000.00],
                'references': ['FACT-2020-001', 'CONTRAT-2019-456']
            }
        }

def display_decision_badge(decision):
    """Affiche un badge de décision stylisé"""
    decision = decision.upper()
    if decision == 'RECEVABLE':
        st.markdown(
            f'<div class="decision-badge decision-recevable">✅ {decision}</div>',
            unsafe_allow_html=True
        )
    elif decision == 'IRRECEVABLE':
        st.markdown(
            f'<div class="decision-badge decision-irrecevable">❌ {decision}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="decision-badge decision-inconnu">❓ {decision}</div>',
            unsafe_allow_html=True
        )

def display_analysis(report):
    """Affiche les résultats de l'analyse"""
    with st.container():
        st.markdown("### 📋 Synthèse de l'analyse")
        
        # Décision globale
        decision = report.get('decision_globale', 'INCONNU')
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("**Décision globale :**")
            display_decision_badge(decision)
        
        with col2:
            # Métriques clés
            criteria = report.get('criteria', {})
            conformes = sum(1 for c in criteria.values() if c.get('decision') in ['CONFORME', 'RECEVABLE'])
            non_conformes = sum(1 for c in criteria.values() if c.get('decision') in ['NON_CONFORME', 'IRRECEVABLE'])
            
            st.metric("Critères analysés", len(criteria))
            st.metric("✅ Conformes", conformes)
            st.metric("❌ Non conformes", non_conformes)
        
        st.markdown("---")
        
        # Analyse détaillée des critères
        st.markdown("### 🔍 Analyse détaillée des critères")
        
        for critere, details in criteria.items():
            with st.expander(f"{critere.replace('_', ' ').title()}", expanded=True):
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown(f"**Décision :** {details.get('decision', 'N/A')}")
                    st.markdown(f"**Confiance :** {details.get('confidence', 0) * 100:.1f}%")
                with col2:
                    st.markdown(f"**Détails :** {details.get('details', 'Non spécifié')}")
        
        # Données extraites
        if 'extracted_data' in report and report['extracted_data']:
            with st.expander("📊 Données extraites", expanded=False):
                st.json(report['extracted_data'], expanded=False)

def process_uploaded_file(uploaded_file, analyzer):
    """Traite un fichier téléversé et retourne le résultat de l'analyse"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            with st.spinner(f"Analyse de {uploaded_file.name}..."):
                result = analyzer.analyze_file(tmp_path)
                return result
        finally:
            try:
                os.unlink(tmp_path)
            except Exception as e:
                st.warning(f"Attention : impossible de supprimer le fichier temporaire : {e}")
    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier {uploaded_file.name} : {str(e)}")
    return None

def main():
    # Chargement du CSS
    load_css()
    
    # Initialisation de l'analyseur
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = CSPEAnalyzer()
    
    # Barre latérale
    with st.sidebar:
        st.image("https://www.conseil-etat.fr/var/ce/storage/static-assets/logo-marianne/logo-marianne.svg", 
                width=200, use_column_width=True)
        st.title("Analyse CSPE")
        st.markdown("---")
        
        # Navigation
        st.markdown("### Navigation")
        page = st.radio(
            "",
            ["Accueil", "Analyser des documents", "Historique", "Aide"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Section d'aide
        with st.expander("ℹ️ Aide"):
            st.markdown("""
            **Comment utiliser cet outil :**
            1. Téléversez vos documents CSPE
            2. Lancez l'analyse
            3. Consultez les résultats détaillés
            4. Téléchargez les rapports
            
            **Formats supportés :**
            - PDF, DOCX, TXT
            - Images (PNG, JPG, JPEG)
            """)
    
    # Contenu principal
    st.markdown("<h1 class='main-header'>Analyse des contestations CSPE</h1>", unsafe_allow_html=True)
    st.markdown("""
    Cet outil vous permet d'analyser des dossiers de contestation de la Contribution au Service Public de l'Électricité (CSPE) 
    selon les critères définis par le Conseil d'État.
    """)
    
    # Section de téléversement
    st.markdown("### 1. Téléversement des documents")
    
    # Zone de dépôt personnalisée
    st.markdown("""
    <div class="upload-area" onclick="document.querySelector('input[type=file]').click()">
        <p style="font-size: 1.1rem; margin: 0 0 0.5rem 0; color: #333;">
            Glissez-déposez vos fichiers ici ou <span style="color: var(--primary); font-weight: 500; cursor: pointer;">parcourir</span>
        </p>
        <p style="font-size: 0.9rem; color: #666; margin: 0;">
            Formats supportés : PDF, DOCX, TXT, images (max 20 Mo par fichier)
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Sélectionnez vos fichiers",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    # Affichage des fichiers sélectionnés
    if uploaded_files:
        st.markdown("**Fichiers sélectionnés :**")
        for file in uploaded_files:
            st.markdown(f"- {file.name} ({file.size / 1024:.1f} KB)")
    
    # Section d'analyse
    st.markdown("### 2. Analyse")
    
    if st.button("🔍 Lancer l'analyse", 
                 type="primary",
                 disabled=not uploaded_files,
                 help="Cliquez pour analyser les documents téléversés"):
        
        if not uploaded_files:
            st.warning("Veuillez d'abord sélectionner au moins un fichier à analyser.")
            return
            
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Traitement de chaque fichier
        results = []
        for i, uploaded_file in enumerate(uploaded_files):
            progress = int((i / len(uploaded_files)) * 100)
            progress_bar.progress(progress)
            status_text.text(f"Traitement en cours : {i+1}/{len(uploaded_files)} - {uploaded_file.name}")
            
            with st.expander(f"📄 {uploaded_file.name}", expanded=True):
                result = process_uploaded_file(uploaded_file, st.session_state.analyzer)
                
                if result:
                    results.append((uploaded_file.name, result))
                    display_analysis(result)
                    
                    # Bouton de téléchargement
                    json_report = json.dumps(result, indent=2, ensure_ascii=False)
                    st.download_button(
                        label=f"💾 Télécharger le rapport d'analyse",
                        data=json_report,
                        file_name=f"rapport_cspe_{Path(uploaded_file.name).stem}.json",
                        mime="application/json",
                        key=f"dl_{uploaded_file.name}"
                    )
                
                st.divider()
        
        # Réinitialisation de la barre de progression
        progress_bar.empty()
        status_text.empty()
        
        if results:
            st.success(f"✅ Analyse terminée pour {len(results)} fichier(s) !")
            
            # Téléchargement de tous les rapports
            if len(results) > 1:
                all_reports = {name: result for name, result in results}
                st.download_button(
                    label="📥 Télécharger tous les rapports (JSON)",
                    data=json.dumps(all_reports, indent=2, ensure_ascii=False),
                    file_name=f"rapports_cspe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

if __name__ == "__main__":
    main()
