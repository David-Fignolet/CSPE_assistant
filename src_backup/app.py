import streamlit as st
from models.classifier import classifier
from datetime import datetime
import json

def display_analysis_result(result):
    """Affiche les résultats de l'analyse de manière élégante"""
    st.subheader("Résultats de l'analyse")
    
    # Affichage de la classification
    if result["classification"] == "RECEVABLE":
        st.success("✅ Dossier RECEVABLE", icon="✅")
    else:
        st.error("❌ Dossier IRRECEVABLE", icon="❌")
    
    # Niveau de confiance
    st.metric("Niveau de confiance", f"{result['confidence']*100:.1f}%")
    
    # Détails des critères
    st.subheader("Détail des critères")
    for critere, details in result["criteria"].items():
        status_emoji = "✅" if details["status"] else "❌"
        st.write(f"{status_emoji} {critere.capitalize()}: {details['details']}")

def main():
    st.set_page_config(
        page_title="Assistant CSPE - Conseil d'État",
        page_icon="⚖️",
        layout="wide"
    )
    
    # Style CSS personnalisé
    st.markdown("""
        <style>
        .stTextArea [data-baseweb=base-input] {
            background-color: #f8f9fa;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            border: none;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("Assistant CSPE - Conseil d'État")
    st.markdown("""
    Cet outil permet d'analyser automatiquement les dossiers CSPE et de vérifier leur recevabilité 
    selon les critères légaux en vigueur.
    """)
    
    # Onglets
    tab1, tab2 = st.tabs(["Analyse de texte", "Téléversement de fichier"])
    
    with tab1:
        st.header("Analyse de texte")
        user_input = st.text_area(
            "Collez le texte du dossier CSPE à analyser :", 
            height=300,
            placeholder="Copiez-collez ici le contenu du dossier..."
        )
        
        if st.button("Lancer l'analyse", type="primary"):
            if user_input.strip():
                with st.spinner("Analyse en cours... Cette opération peut prendre quelques instants."):
                    try:
                        # Appel au classifieur
                        result = classifier.analyze_document(user_input)
                        display_analysis_result(result)
                        
                        # Bouton pour afficher les données brutes
                        if st.checkbox("Afficher les données brutes"):
                            st.json(result)
                            
                    except Exception as e:
                        st.error(f"Une erreur est survenue lors de l'analyse : {str(e)}")
            else:
                st.warning("Veuillez saisir un texte à analyser.")
    
    with tab2:
        st.header("Téléversement de fichier")
        uploaded_file = st.file_uploader(
            "Téléversez un document (PDF, DOCX, TXT)", 
            type=["pdf", "docx", "txt"]
        )
        
        if uploaded_file is not None:
            st.warning("La fonctionnalité de téléversement sera implémentée dans une prochaine version.")

    # Pied de page
    st.markdown("---")
    st.caption(f"© {datetime.now().year} Conseil d'État - Version 0.1.0")

if __name__ == "__main__":
    main()
