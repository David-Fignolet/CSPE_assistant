import streamlit as st
import os
from document_processor import DocumentProcessor
from database_memory import DatabaseManager, DossierCSPE, CritereAnalyse
from dotenv import load_dotenv
import io
import pandas as pd
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Assistant CSPE - Conseil d'État",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    try:
        # Chargement des variables d'environnement
        load_dotenv()
        DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://cspe_user:cspe_password@localhost:5432/cspe_db')
        
        # Initialisation
        processor = DocumentProcessor()
        db_manager = DatabaseManager(DATABASE_URL)
        
        # Sidebar - Navigation
        page = st.sidebar.selectbox(
            "Navigation",
            ["🏠 Accueil", "📝 Nouvelle Analyse", "🔍 Historique", "📊 Statistiques", "⚙️ Administration"],
            index=0
        )
        
        # Fonction pour gérer les erreurs
        def handle_error(e, message):
            st.error(f"⚠️ {message}: {str(e)}")
            st.stop()
        
        # Fonction pour afficher les résultats d'analyse
        def display_analysis_results(results):
            st.header("📊 Résultats d'Analyse")
            
            # Synthèse
            st.subheader("SYNTHÈSE")
            
            # Décision
            decision = results.get('decision', 'INSTRUCTION')
            if decision == 'RECEVABLE':
                st.success("RECEVABLE ☑")
            elif decision == 'IRRECEVABLE':
                st.error("IRRECEVABLE ☑")
            else:
                st.warning("COMPLÉMENT D'INSTRUCTION ☑")
            
            # Détail par société/période
            st.subheader("DÉTAIL PAR SOCIÉTÉ/PÉRIODE")
            if 'analysis_by_company' in results:
                analysis_by_company = results['analysis_by_company']
                for company, periods in analysis_by_company.items():
                    with st.expander(f"{company}"):
                        for year, amount in periods.items():
                            status = "✅" if amount > 0 else "❌"
                            st.write(f"- {year} : {amount} € {status}")
            
            # Critères
            st.subheader("CRITÈRES")
            if 'criteria' in results:
                for criterion, status in results['criteria'].items():
                    st.write(f"- {criterion} : {status}")
            
            # Observations
            st.subheader("OBSERVATIONS")
            observations = results.get('observations', "Aucune observation disponible")
            st.write(observations)
        
        if page == "🏠 Accueil":
            try:
                st.title("Assistant CSPE - Conseil d'État")
                st.markdown("""
                Fonctionnalités principales :
                - 📝 Analyse automatique des dossiers
                - 🔍 Historique complet des analyses
                - 📊 Statistiques détaillées
                - ⚙️ Interface d'administration
                - 📄 Export des rapports
                """)
            except Exception as e:
                handle_error(e, "Erreur sur la page d'accueil")
        
        elif page == "📝 Nouvelle Analyse":
            try:
                st.title("📝 Nouvelle Analyse")
                
                # Upload de fichiers
                uploaded_files = st.file_uploader(
                    "Choisissez des fichiers (PDF, PNG, JPG)",
                    type=['pdf', 'png', 'jpg', 'jpeg'],
                    accept_multiple_files=True,
                    help="Formats acceptés : PDF, PNG, JPG"
                )
                
                if uploaded_files:
                    # Formulaire de dossier
                    with st.form("dossier_form"):
                        dossier_data = {
                            'numero_dossier': st.text_input("Numéro de dossier"),
                            'demandeur': st.text_input("Nom du demandeur"),
                            'activite': st.text_input("Activité"),
                            'date_reclamation': st.date_input("Date de réclamation"),
                            'periode_debut': st.number_input("Période début", min_value=2009, max_value=2015, value=2009),
                            'periode_fin': st.number_input("Période fin", min_value=2009, max_value=2015, value=2015),
                            'montant_reclame': st.number_input("Montant réclamé (€)", min_value=0.0)
                        }
                        
                        if st.form_submit_button("🔍 ANALYSER", type="primary"):
                            with st.spinner("Analyse en cours..."):
                                try:
                                    # Extraction du texte
                                    combined_text = ""
                                    for file in uploaded_files:
                                        text = processor.extract_text_from_file(file)
                                        combined_text += f"\n=== {file.name} ===\n{text}\n"
                                    
                                    # Analyse avec LLM
                                    results = analyze_with_llm(combined_text)
                                    
                                    # Sauvegarde dans la base
                                    dossier_id = db_manager.add_dossier(dossier_data)
                                    for critere, details in results['criteria'].items():
                                        db_manager.add_critere({
                                            'dossier_id': dossier_id,
                                            'critere': critere,
                                            'statut': details['status'] == '✅',
                                            'detail': details['details']
                                        })
                                    
                                    # Affichage des résultats
                                    st.success("Analyse terminée !")
                                    display_analysis_results(results)
                                    
                                    # Boutons d'export
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("📄 Export PDF", type="primary"):
                                            pdf_path = db_manager.generate_pdf_report(dossier_id)
                                            if pdf_path:
                                                with open(pdf_path, 'rb') as f:
                                                    st.download_button(
                                                        "Télécharger PDF",
                                                        f.read(),
                                                        f"rapport_{dossier_data['numero_dossier']}.pdf",
                                                        "application/pdf"
                                                    )
                                    with col2:
                                        if st.button("📊 Export CSV", type="primary"):
                                            csv_path = db_manager.generate_csv_report(dossier_id)
                                            if csv_path:
                                                with open(csv_path, 'rb') as f:
                                                    st.download_button(
                                                        "Télécharger CSV",
                                                        f.read(),
                                                        f"rapport_{dossier_data['numero_dossier']}.csv",
                                                        "text/csv"
                                                    )
                                except Exception as e:
                                    handle_error(e, "Erreur lors de l'analyse du dossier")
            except Exception as e:
                handle_error(e, "Erreur dans l'onglet Nouvelle Analyse")
        
        elif page == "🔍 Historique":
            try:
                st.title("🔍 Historique des Analyses")
                
                # Filtres
                col1, col2, col3 = st.columns(3)
                with col1:
                    date_debut = st.date_input("Date début", value=datetime.now())
                with col2:
                    date_fin = st.date_input("Date fin", value=datetime.now())
                with col3:
                    statut = st.selectbox("Statut", ['Tous', 'RECEVABLE', 'IRRECEVABLE'])
                
                try:
                    # Recherche
                    dossiers = db_manager.get_all_dossiers()
                    if statut != 'Tous':
                        dossiers = [d for d in dossiers if d.statut == statut]
                    
                    # Affichage des résultats
                    if not dossiers:
                        st.info("Aucun dossier trouvé")
                    else:
                        for dossier in dossiers:
                            with st.expander(f"Dossier {dossier.numero_dossier} - {dossier.statut}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"Demandeur: {dossier.demandeur}")
                                    st.write(f"Activité: {dossier.activite}")
                                    st.write(f"Date: {dossier.date_reclamation}")
                                                                        st.write(f"Période: {dossier.periode_debut} - {dossier.periode_fin}")
                                    st.write(f"Montant réclamé: {dossier.montant_reclame} €")
                                with col2:
                                    st.write(f"Statut: {dossier.statut}")
                                    st.write(f"Decision: {dossier.decision}")
                                    st.write(f"Observations: {dossier.observations}")
            except Exception as e:
                handle_error(e, "Erreur dans l'onglet Historique")

        elif page == "📊 Statistiques":
            try:
                st.title("📊 Statistiques")

                # Sélection de période
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Date de début", value=datetime.now())
                with col2:
                    end_date = st.date_input("Date de fin", value=datetime.now())

                try:
                    # Statistiques
                    stats = db_manager.get_statistics({
                        'start': start_date.strftime('%Y-%m-%d'),
                        'end': end_date.strftime('%Y-%m-%d')
                    })

                    st.metric("Total dossiers", stats['total'])
                    st.metric("Dossiers recevables", stats['recevables'])
                    st.metric("Dossiers irrecevables", stats['irrecevables'])
                    st.metric("Taux de recevabilité", f"{stats['taux_recevabilite']:.2f}%")

                    # Graphiques
                    st.subheader("Répartition par statut")
                    data = {
                        'Statut': ['RECEVABLE', 'IRRECEVABLE'],
                        'Nombre': [stats['recevables'], stats['irrecevables']]
                    }
                    df = pd.DataFrame(data)
                    st.bar_chart(df, x='Statut', y='Nombre')

                    # Répartition par activité
                    st.subheader("Répartition par activité")
                    activity_stats = db_manager.get_activity_stats()
                    st.bar_chart(activity_stats)

                    # Répartition par montant
                    st.subheader("Répartition des montants")
                    amount_stats = db_manager.get_amount_stats()
                    st.bar_chart(amount_stats)

                except Exception as e:
                    handle_error(e, "Erreur dans l'onglet Statistiques")

        elif page == "⚙️ Administration":
            try:
                st.title("⚙️ Administration")

                # Gestion des dossiers
                dossiers = db_manager.get_all_dossiers()
                selected_dossier = st.selectbox("Sélectionner un dossier", 
                                              [f"{d.numero_dossier} - {d.demandeur}" for d in dossiers])

                if selected_dossier:
                    dossier = dossiers[[str(d.numero_dossier) for d in dossiers].index(selected_dossier.split(" - ")[0])]
                    with st.form("update_form"):
                        st.write("Mise à jour du dossier")
                        numero = st.text_input("Numéro de dossier", dossier.numero_dossier)
                        demandeur = st.text_input("Demandeur", dossier.demandeur)
                        activite = st.text_input("Activité", dossier.activite)
                        date_reclamation = st.date_input("Date de réclamation", dossier.date_reclamation)
                        periode_debut = st.number_input("Période début", min_value=2009, max_value=2015, value=dossier.periode_debut)
                        periode_fin = st.number_input("Période fin", min_value=2009, max_value=2015, value=dossier.periode_fin)
                        montant_reclame = st.number_input("Montant réclamé (€)", min_value=0.0, value=dossier.montant_reclame)
                        statut = st.selectbox("Statut", ['RECEVABLE', 'IRRECEVABLE'], index=0 if dossier.statut == 'RECEVABLE' else 1)
                        decision = st.text_input("Decision", dossier.decision)
                        observations = st.text_area("Observations", dossier.observations)

                        if st.form_submit_button("Mettre à jour", type="primary"):
                            try:
                                db_manager.update_dossier({
                                    'id': dossier.id,
                                    'numero_dossier': numero,
                                    'demandeur': demandeur,
                                    'activite': activite,
                                    'date_reclamation': date_reclamation,
                                    'periode_debut': periode_debut,
                                    'periode_fin': periode_fin,
                                    'montant_reclame': montant_reclame,
                                    'statut': statut,
                                    'decision': decision,
                                    'observations': observations
                                })
                                st.success("Dossier mis à jour avec succès !")
                            except Exception as e:
                                handle_error(e, "Erreur lors de la mise à jour du dossier")

            except Exception as e:
                handle_error(e, "Erreur dans l'onglet Administration")

    except Exception as e:
        st.error(f"Une erreur est survenue : {str(e)}")
        st.stop()

if __name__ == "__main__":
    main()