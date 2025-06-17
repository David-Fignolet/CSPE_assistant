import streamlit as st
from pathlib import Path
import sys

def main():
    st.set_page_config(
        page_title="Debug Uploader",
        page_icon="🐞"
    )
    
    st.title("🐞 Débogage du téléversement multiple")
    
    # Zone de dépôt de fichiers simplifiée
    uploaded_files = st.file_uploader(
        "Sélectionnez un ou plusieurs fichiers",
        type=["txt", "pdf"],
        accept_multiple_files=True
    )
    
    # Affichage des informations de débogage
    st.write("### Informations de débogage")
    st.write(f"Nombre de fichiers : {len(uploaded_files) if uploaded_files else 0}")
    
    # Afficher les détails des fichiers
    if uploaded_files:
        for i, uploaded_file in enumerate(uploaded_files, 1):
            with st.expander(f"Fichier {i}: {uploaded_file.name}"):
                st.write(f"Type: {uploaded_file.type}")
                st.write(f"Taille: {len(uploaded_file.getvalue())} octets")
                
                # Afficher le contenu des fichiers texte
                if uploaded_file.type == "text/plain":
                    st.text_area("Contenu", uploaded_file.getvalue().decode("utf-8"), height=100)

if __name__ == "__main__":
    main()