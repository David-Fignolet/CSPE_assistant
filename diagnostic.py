# diagnostic.py
import streamlit as st
import os
import shutil
from dotenv import load_dotenv
import psycopg2
import pandas as pd

def check_environment():
    st.header("🔍 Diagnostic du Système")
    
    # Vérification des dépendances
    st.subheader("Dépendances")
    try:
        import PyPDF2
        import pytesseract
        import cv2
        st.success("✅ Dépendances installées")
    except Exception as e:
        st.error(f"❌ Erreur dépendances: {str(e)}")
    
    # Vérification de l'environnement
    st.subheader("Variables d'environnement")
    load_dotenv()
    if not os.getenv('DATABASE_URL'):
        st.error("❌ DATABASE_URL non configuré")
    
    # Vérification de la base de données
    st.subheader("Base de données")
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        st.success("✅ Connexion DB réussie")
    except Exception as e:
        st.error(f"❌ Erreur DB: {str(e)}")
    
    # Vérification des polices
    st.subheader("Polices")
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("Marianne-Regular.ttf", 12)
        st.success("✅ Polices disponibles")
    except Exception as e:
        st.error(f"❌ Erreur polices: {str(e)}")
    
    # Vérification de l'espace disque
    st.subheader("Espace disque")
    total, used, free = shutil.disk_usage("/")
    st.write(f"Espace libre: {free // (2**30)} Go")
    if free // (2**30) < 1:
        st.warning("⚠️ Espace disque faible")
    
    # Statistiques système
    st.subheader("Statistiques")
    try:
        stats = pd.read_sql("SELECT COUNT(*) as total, SUM(montant_reclame) as total_montant FROM dossiers", conn)
        st.dataframe(stats)
    except Exception as e:
        st.error(f"❌ Erreur stats: {str(e)}")
        
    conn.close()

if __name__ == "__main__":
    check_environment()