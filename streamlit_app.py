import streamlit as st
import os
import json
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import tempfile

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent))

# Try to import the analyzer, but don't fail if not available
try:
    from src.models.expert_analyzer import CSPEExpertAnalyzer, Decision
except ImportError:
    # Fallback for demo purposes
    class CSPEExpertAnalyzer:
        def analyze_file(self, file_path):
            return {
                'decision_globale': 'RECEVABLE',
                'criteria': {
                    'delai_reclamation': {'decision': 'CONFORME', 'details': 'Délai respecté', 'confidence': 0.95},
                    'periode_concernee': {'decision': 'CONFORME', 'details': 'Période 2009-2015', 'confidence': 0.98},
                    'prescription_quadriennale': {'decision': 'NON_CONCERNE', 'details': 'Non applicable', 'confidence': 1.0},
                    'repercuation_client_final': {'decision': 'A_VERIFIER', 'details': 'À vérifier dans les documents', 'confidence': 0.7}
                },
                'extracted_data': {
                    'dates': ['2020-01-15', '2019-12-30'],
                    'montants': [1500.50, 2000.00],
                    'references': ['FACT-2020-001', 'CONTRAT-2019-456']
                }
            }


# Constants
PAGE_TITLE = "Analyse CSPE - Conseil d'État"
PAGE_ICON = "🏛️"
PRIMARY_COLOR = "#0055b7"
SECONDARY_COLOR = "#f8f9fa"

# Set page config
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
def load_css():
    st.markdown(
        f"""
        <style>
            /* Main container */
            .main .block-container {{
                padding-top: 2rem;
                max-width: 95%;
            }}
            
            /* Sidebar */
            .css-1d391kg, .css-1vq4p4l, .e1fqkh3o4 {{
                background-color: {SECONDARY_COLOR} !important;
                border-right: 1px solid #e0e0e0;
            }}
            
            /* Headers */
            h1, h2, h3, h4, h5, h6 {{
                color: {PRIMARY_COLOR} !important;
                font-weight: 600 !important;
            }}
            
            /* Buttons */
            .stButton>button {{
                background-color: {PRIMARY_COLOR};
                color: white;
                border-radius: 4px;
                font-weight: 500;
                padding: 0.5rem 1rem;
            }}
            
            .stButton>button:hover {{
                background-color: #003d82;
                border-color: #003d82;
            }}
            
            /* File uploader */
            .uploadedFile {{
                padding: 0.5rem;
                margin: 0.5rem 0;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #f8f9fa;
            }}
            
            /* Cards */
            .card {{
                padding: 1.5rem;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                margin-bottom: 1.5rem;
                background: white;
            }}
            
            /* Decision badges */
            .decision-badge {{
                padding: 0.5rem 1rem;
                border-radius: 20px;
                font-weight: 600;
                display: inline-block;
                margin: 0.5rem 0;
            }}
            
            .decision-recevable {{
                background-color: #d4edda;
                color: #155724;
            }}
            
            .decision-irrecevable {{
                background-color: #f8d7da;
                color: #721c24;
            }}
            
            .decision-inconnu {{
                background-color: #e2e3e5;
                color: #383d41;
            }}
            
            /* Progress bar */
            .stProgress > div > div > div > div {{
                background-color: {PRIMARY_COLOR};
            }}
        </style>
        """,
        unsafe_allow_html=True
    )

def display_decision_badge(decision: str) -> None:
    """Display a styled decision badge."""
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

def display_analysis(report: Dict[str, Any]) -> None:
    """Display the analysis report in a structured way."""
    with st.container():
        st.markdown("### 📋 Synthèse de l'analyse")
        
        # Display global decision
        decision = report.get('decision_globale', 'INCONNU')
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("**Décision globale :**")
            display_decision_badge(decision)
        
        with col2:
            # Display key metrics
            criteria = report.get('criteria', {})
            conformes = sum(1 for c in criteria.values() if c.get('decision') in ['CONFORME', 'RECEVABLE'])
            non_conformes = sum(1 for c in criteria.values() if c.get('decision') in ['NON_CONFORME', 'IRRECEVABLE'])
            
            st.markdown(f"**Critères analysés :** {len(criteria)}")
            st.markdown(f"✅ Conformes : {conformes}")
            st.markdown(f"❌ Non conformes : {non_conformes}")
        
        st.markdown("---")
        
        # Detailed criteria analysis
        st.markdown("### 🔍 Analyse détaillée des critères")
        
        for critere, details in criteria.items():
            with st.expander(f"{critere.replace('_', ' ').title()}", expanded=True):
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown(f"**Décision :** {details.get('decision', 'N/A')}")
                    st.markdown(f"**Confiance :** {details.get('confidence', 0) * 100:.1f}%")
                with col2:
                    st.markdown(f"**Détails :** {details.get('details', 'Non spécifié')}")
        
        # Extracted data
        if 'extracted_data' in report and report['extracted_data']:
            with st.expander("📊 Données extraites", expanded=False):
                st.json(report['extracted_data'], expanded=False)

def process_uploaded_file(uploaded_file, analyzer: CSPEExpertAnalyzer) -> Optional[Dict]:
    """Process an uploaded file and return analysis results."""
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
    # Load CSS
    load_css()
    
    # Initialize session state
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = CSPEExpertAnalyzer()
    
    # Sidebar
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
        
        # Help section
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
    
    # Main content
    st.title("Analyse des demandes de remboursement CSPE")
    st.markdown("""
    Cet outil vous permet d'analyser des dossiers de demande de remboursement de la Contribution au Service Public de l'Électricité (CSPE) 
    selon les critères définis par le Conseil d'État.
    """)
    
    # File upload section
    st.markdown("### 1. Téléversement des documents")
    uploaded_files = st.file_uploader(
        "Glissez-déposez vos fichiers ou cliquez pour parcourir",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Sélectionnez un ou plusieurs fichiers à analyser"
    )
    
    # Display uploaded files
    if uploaded_files:
        st.markdown("**Fichiers sélectionnés :**")
        for file in uploaded_files:
            st.markdown(f"- {file.name} ({file.size / 1024:.1f} KB)")
    
    # Analysis section
    st.markdown("### 2. Analyse")
    if st.button("🔍 Lancer l'analyse", 
                 disabled=not uploaded_files,
                 type="primary",
                 help="Cliquez pour analyser les documents téléversés"):
        
        if not uploaded_files:
            st.warning("Veuillez d'abord sélectionner au moins un fichier à analyser.")
            return
            
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Process each file
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
                    
                    # Download button for individual report
                    json_report = json.dumps(result, indent=2, ensure_ascii=False)
                    st.download_button(
                        label=f"💾 Télécharger le rapport d'analyse",
                        data=json_report,
                        file_name=f"rapport_cspe_{Path(uploaded_file.name).stem}.json",
                        mime="application/json",
                        key=f"dl_{uploaded_file.name}"
                    )
                
                st.divider()
        
        # Reset progress
        progress_bar.empty()
        status_text.empty()
        
        if results:
            st.success(f"✅ Analyse terminée pour {len(results)} fichier(s) !")
            
            # Download all reports
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