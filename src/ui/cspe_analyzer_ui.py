import streamlit as st
from pathlib import Path
import tempfile
import json
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

# Ajout du répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from models.expert_analyzer import CSPEExpertAnalyzer, Decision

def display_analysis(report: Dict[str, Any]) -> None:
    """Affiche le rapport d'analyse de manière interactive."""
    st.header("📋 Rapport d'analyse CSPE")
    
    # Affichage de la décision globale
    decision = report.get('decision_globale', 'inconnu').upper()
    if decision == 'RECEVABLE':
        st.success(f"## Décision : {decision} ✅")
    elif decision == 'IRRECEVABLE':
        st.error(f"## Décision : {decision} ❌")
    else:
        st.warning(f"## Décision : {decision} ⚠️")
    
    # Détails des critères
    st.subheader("Analyse détaillée des critères")
    
    criteria = report.get('criteria', {})
    for critere, details in criteria.items():
        # Utilisation de st.container() au lieu de st.expander pour éviter l'imbrication
        with st.container():
            st.markdown(f"**{critere.replace('_', ' ').title()}**")
            st.write(f"**Décision :** {details.get('decision', 'N/A')}")
            st.write(f"**Détails :** {details.get('details', 'Non spécifié')}")
            st.write(f"**Niveau de confiance :** {details.get('confidence', 0) * 100:.1f}%")
            st.markdown("---")  # Ligne de séparation
    
    # Données extraites
    if 'extracted_data' in report and report['extracted_data']:
        with st.expander("🔍 Données extraites (cliquez pour afficher)"):
            st.json(report['extracted_data'], expanded=False)

def process_uploaded_file(uploaded_file, analyzer: CSPEExpertAnalyzer) -> Optional[Dict]:
    """Traite un fichier uploadé et retourne le résultat de l'analyse."""
    try:
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            # Écrire le contenu du fichier uploadé
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            # Analyser le fichier
            with st.spinner(f"Analyse de {uploaded_file.name}..."):
                result = analyzer.analyze_file(tmp_path)
                return result
        finally:
            # Nettoyer le fichier temporaire
            try:
                os.unlink(tmp_path)
            except Exception as e:
                st.warning(f"Attention : impossible de supprimer le fichier temporaire : {e}")
    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier {uploaded_file.name} : {str(e)}")
    return None

def main():
    st.set_page_config(
        page_title="Analyse CSPE - Expert Conseil d'État",
        page_icon="🏛️",
        layout="wide"
    )
    
    st.title("🏛️ Analyse Expert CSPE - Conseil d'État")
    
    # Style personnalisé
    st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stButton>button {
        background-color: #0055b7;
        color: white;
    }
    .stButton>button:hover {
        background-color: #003d82;
    }
    .file-uploader {
        border: 2px dashed #4CAF50;
        border-radius: 5px;
        padding: 20px;
        text-align: center;
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialisation de l'analyseur
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = CSPEExpertAnalyzer()
    
    # En-tête avec description
    st.markdown("""
    ### Bienvenue sur l'outil d'analyse des dossiers CSPE
    
    Cet outil vous permet d'analyser des documents liés aux demandes de remboursement de la CSPE 
    selon les critères du Conseil d'État. Téléversez un ou plusieurs documents pour commencer.
    """)
    
    # Zone de dépôt de fichiers
    st.markdown("<div class='file-uploader'>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "📤 Téléversez vos documents CSPE (PDF, DOCX, TXT, images)",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="file_uploader"
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Bouton d'analyse
    if st.button("🔍 Lancer l'analyse", disabled=not uploaded_files, key="analyze_btn"):
        if not uploaded_files:
            st.warning("Veuillez d'abord sélectionner au moins un fichier à analyser.")
            return
            
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Traitement de chaque fichier
        results = []
        for i, uploaded_file in enumerate(uploaded_files):
            # Mise à jour de la progression
            progress = int((i / len(uploaded_files)) * 100)
            progress_bar.progress(progress)
            status_text.text(f"Traitement du fichier {i+1}/{len(uploaded_files)} : {uploaded_file.name}")
            
            # Traitement du fichier
            with st.expander(f"📄 {uploaded_file.name}", expanded=True):
                result = process_uploaded_file(uploaded_file, st.session_state.analyzer)
                
                if result:
                    results.append((uploaded_file.name, result))
                    display_analysis(result)
                    
                    # Bouton de téléchargement
                    json_report = json.dumps(result, indent=2, ensure_ascii=False)
                    st.download_button(
                        label=f"💾 Télécharger l'analyse de {uploaded_file.name}",
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
            
            # Option pour télécharger tous les rapports en un seul fichier
            if len(results) > 1:
                all_reports = {name: result for name, result in results}
                st.download_button(
                    label="📥 Télécharger tous les rapports (ZIP)",
                    data=json.dumps(all_reports, indent=2, ensure_ascii=False),
                    file_name=f"rapports_cspe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/zip",
                    key="dl_all_reports"
                )
    
    # Section d'aide
    with st.expander("ℹ️ Comment utiliser cette application"):
        st.markdown("""
        ### Guide d'utilisation
        
        1. **Téléversez** un ou plusieurs documents CSPE (factures, contrats, etc.)
           - Cliquez sur "Parcourir les fichiers" ou glissez-déposez les fichiers
           - Formats supportés : PDF, DOCX, TXT, images (PNG, JPG, JPEG)
        
        2. Cliquez sur **"Lancer l'analyse"** pour commencer le traitement
        
        3. Consultez les résultats détaillés pour chaque critère
           - ✅ Recevable : Le critère est respecté
           - ❌ Irrecevable : Le critère n'est pas respecté
           - ⚠️ À compléter : Informations manquantes pour statuer
        
        4. Téléchargez les rapports d'analyse au format JSON
        
        ### Critères d'analyse
        - **Délai de réclamation** : Vérifie si la réclamation a été faite dans les délais (avant le 31/12/N+1)
        - **Période couverte** : Vérifie si la période est comprise entre 2009 et 2015
        - **Prescription quadriennale** : Vérifie si la réclamation est prescrite (délai de 4 ans)
        - **Répercussion client final** : Vérifie si la CSPE a été répercutée sur le client final
        
        ### Besoin d'aide ?
        Pour toute question ou problème technique, veuillez contacter l'équipe support.
        """)

if __name__ == "__main__":
    main()
