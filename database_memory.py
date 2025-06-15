from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import os

Base = declarative_base()

class DossierCSPE(Base):
    __tablename__ = 'dossiers_cspe'
    
    id = Column(Integer, primary_key=True)
    numero_dossier = Column(String(50), unique=True)
    demandeur = Column(String(255))
    activite = Column(String(255))
    date_reclamation = Column(Date)
    periode_debut = Column(Integer)
    periode_fin = Column(Integer)
    montant_reclame = Column(Float)
    statut = Column(String(20))
    motif_irrecevabilite = Column(String)
    confiance_analyse = Column(Float)
    date_analyse = Column(DateTime, default=datetime.utcnow)
    analyste = Column(String(100))
    documents_joints = Column(ARRAY(String))
    commentaires = Column(String)

class CritereAnalyse(Base):
    __tablename__ = 'criteres_analyse'
    
    id = Column(Integer, primary_key=True)
    dossier_id = Column(Integer, ForeignKey('dossiers_cspe.id'))
    critere = Column(String(50))
    statut = Column(Boolean)
    detail = Column(String)
    date_verification = Column(DateTime, default=datetime.utcnow)
    
    dossier = relationship("DossierCSPE", back_populates="criteres")

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    dossier_id = Column(Integer, ForeignKey('dossiers_cspe.id'))
    nom_fichier = Column(String(255))
    type_document = Column(String(50))
    chemin_fichier = Column(String(500))
    taille_fichier = Column(Integer)
    date_upload = Column(DateTime, default=datetime.utcnow)
    texte_extrait = Column(String)
    hash_fichier = Column(String(64))
    
    dossier = relationship("DossierCSPE", back_populates="documents")

DossierCSPE.criteres = relationship("CritereAnalyse", order_by=CritereAnalyse.id, back_populates="dossier")
DossierCSPE.documents = relationship("Document", order_by=Document.id, back_populates="dossier")

class DatabaseManager:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
    def init_db(self):
        Base.metadata.create_all(self.engine)
    
    def add_dossier(self, dossier_data):
        session = self.Session()
        try:
            dossier = DossierCSPE(**dossier_data)
            session.add(dossier)
            session.commit()
            return dossier.id
        finally:
            session.close()
    
    def add_critere(self, critere_data):
        session = self.Session()
        try:
            critere = CritereAnalyse(**critere_data)
            session.add(critere)
            session.commit()
            return critere.id
        finally:
            session.close()
    
    def add_document(self, document_data):
        session = self.Session()
        try:
            document = Document(**document_data)
            session.add(document)
            session.commit()
            return document.id
        finally:
            session.close()
    
    def get_dossier(self, dossier_id):
        session = self.Session()
        try:
            return session.query(DossierCSPE).filter_by(id=dossier_id).first()
        finally:
            session.close()
    
    def get_all_dossiers(self, filters=None):
        session = self.Session()
        try:
            query = session.query(DossierCSPE)
            if filters:
                for key, value in filters.items():
                    query = query.filter(getattr(DossierCSPE, key) == value)
            return query.all()
        finally:
            session.close()
    
    def generate_pdf_report(self, dossier_id):
        dossier = self.get_dossier(dossier_id)
        if not dossier:
            return None
        
        pdf = FPDF()
        pdf.add_page()
        
        # En-tête
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Rapport d'Analyse CSPE", 0, 1, 'C')
        pdf.ln(10)
        
        # Informations de base
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Numéro de dossier : {dossier.numero_dossier}", 0, 1)
        pdf.cell(0, 10, f"Demandeur : {dossier.demandeur}", 0, 1)
        pdf.cell(0, 10, f"Activité : {dossier.activite}", 0, 1)
        pdf.cell(0, 10, f"Date de réclamation : {dossier.date_reclamation}", 0, 1)
        
        # Critères
        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Critères d'Analyse", 0, 1)
        pdf.set_font("Arial", "", 12)
        for critere in dossier.criteres:
            status = "✅" if critere.statut else "❌"
            pdf.cell(0, 10, f"- {critere.critere}: {status} ({critere.detail})", 0, 1)
        
        # Statut et montants
        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Statut et Montants", 0, 1)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Statut : {dossier.statut}", 0, 1)
        pdf.cell(0, 10, f"Montant réclamé : {dossier.montant_reclame} €", 0, 1)
        
        # Sauvegarde
        filename = f"rapport_dossier_{dossier.numero_dossier}.pdf"
        pdf.output(filename)
        return filename
    
    def generate_csv_report(self, dossier_id):
        dossier = self.get_dossier(dossier_id)
        if not dossier:
            return None
        
        data = {
            'Numéro de dossier': [dossier.numero_dossier],
            'Demandeur': [dossier.demandeur],
            'Activité': [dossier.activite],
            'Date de réclamation': [str(dossier.date_reclamation)],
            'Statut': [dossier.statut],
            'Montant réclamé': [dossier.montant_reclame],
            'Critères': [', '.join([c.critere for c in dossier.criteres])]
        }
        
        filename = f"rapport_dossier_{dossier.numero_dossier}.csv"
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')
        return filename
    
    def get_statistics(self, period=None):
        session = self.Session()
        try:
            query = session.query(DossierCSPE)
            if period:
                start_date = datetime.strptime(period['start'], '%Y-%m-%d')
                end_date = datetime.strptime(period['end'], '%Y-%m-%d')
                query = query.filter(DossierCSPE.date_analyse.between(start_date, end_date))
            
            total = query.count()
            recevables = query.filter(DossierCSPE.statut == 'RECEVABLE').count()
            irrecevables = query.filter(DossierCSPE.statut == 'IRRECEVABLE').count()
            
            return {
                'total': total,
                'recevables': recevables,
                'irrecevables': irrecevables,
                'taux_recevabilite': (recevables / total * 100) if total > 0 else 0
            }
        finally:
            session.close()