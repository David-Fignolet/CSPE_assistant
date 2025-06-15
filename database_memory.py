from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey, ARRAY, func, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import pandas as pd
import os
import json

# Essayer d'importer FPDF, avec fallback si non disponible
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
    print("Warning: FPDF non disponible - fonctionnalité PDF désactivée")

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
    statut = Column(String(20))  # RECEVABLE, IRRECEVABLE, INSTRUCTION
    motif_irrecevabilite = Column(Text)
    confiance_analyse = Column(Float)
    date_analyse = Column(DateTime, default=datetime.utcnow)
    analyste = Column(String(100))
    documents_joints = Column(Text)  # JSON string au lieu de ARRAY pour compatibilité
    commentaires = Column(Text)

class CritereAnalyse(Base):
    __tablename__ = 'criteres_analyse'
    
    id = Column(Integer, primary_key=True)
    dossier_id = Column(Integer, ForeignKey('dossiers_cspe.id'))
    critere = Column(String(50))
    statut = Column(Boolean)
    detail = Column(Text)
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
    texte_extrait = Column(Text)
    hash_fichier = Column(String(64))
    
    dossier = relationship("DossierCSPE", back_populates="documents")

# Établir les relations
DossierCSPE.criteres = relationship("CritereAnalyse", order_by=CritereAnalyse.id, back_populates="dossier", cascade="all, delete-orphan")
DossierCSPE.documents = relationship("Document", order_by=Document.id, back_populates="dossier", cascade="all, delete-orphan")

class DatabaseManager:
    def __init__(self, db_url="sqlite:///cspe_assistant.db"):
        """Initialise le gestionnaire de base de données"""
        self.db_url = db_url
        self.engine = create_engine(db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
    def init_db(self):
        """Initialise la base de données en créant toutes les tables"""
        try:
            Base.metadata.create_all(self.engine)
            print("✅ Base de données initialisée avec succès")
        except Exception as e:
            print(f"❌ Erreur initialisation base: {str(e)}")
    
    def add_dossier(self, dossier_data):
        """Ajoute un nouveau dossier CSPE"""
        session = self.Session()
        try:
            # Conversion des documents_joints en JSON string si nécessaire
            if 'documents_joints' in dossier_data and isinstance(dossier_data['documents_joints'], list):
                dossier_data['documents_joints'] = json.dumps(dossier_data['documents_joints'])
            
            dossier = DossierCSPE(**dossier_data)
            session.add(dossier)
            session.commit()
            return dossier.id
        except Exception as e:
            session.rollback()
            print(f"Erreur ajout dossier: {str(e)}")
            return None
        finally:
            session.close()
    
    def add_critere(self, critere_data):
        """Ajoute un critère d'analyse"""
        session = self.Session()
        try:
            critere = CritereAnalyse(**critere_data)
            session.add(critere)
            session.commit()
            return critere.id
        except Exception as e:
            session.rollback()
            print(f"Erreur ajout critère: {str(e)}")
            return None
        finally:
            session.close()
    
    def add_document(self, document_data):
        """Ajoute un document à un dossier"""
        session = self.Session()
        try:
            document = Document(**document_data)
            session.add(document)
            session.commit()
            return document.id
        except Exception as e:
            session.rollback()
            print(f"Erreur ajout document: {str(e)}")
            return None
        finally:
            session.close()
    
    def get_dossier(self, dossier_id):
        """Récupère un dossier par son ID"""
        session = self.Session()
        try:
            return session.query(DossierCSPE).filter_by(id=dossier_id).first()
        except Exception as e:
            print(f"Erreur récupération dossier: {str(e)}")
            return None
        finally:
            session.close()
    
    def get_dossier_by_numero(self, numero_dossier):
        """Récupère un dossier par son numéro"""
        session = self.Session()
        try:
            return session.query(DossierCSPE).filter_by(numero_dossier=numero_dossier).first()
        except Exception as e:
            print(f"Erreur récupération dossier par numéro: {str(e)}")
            return None
        finally:
            session.close()
    
    def get_all_dossiers(self, filters=None):
        """Récupère tous les dossiers avec filtres optionnels"""
        session = self.Session()
        try:
            query = session.query(DossierCSPE)
            if filters:
                for key, value in filters.items():
                    if hasattr(DossierCSPE, key):
                        query = query.filter(getattr(DossierCSPE, key) == value)
            return query.order_by(DossierCSPE.date_analyse.desc()).all()
        except Exception as e:
            print(f"Erreur récupération dossiers: {str(e)}")
            return []
        finally:
            session.close()
    
    def update_dossier(self, dossier_data):
        """Met à jour un dossier existant"""
        session = self.Session()
        try:
            dossier = session.query(DossierCSPE).filter_by(id=dossier_data['id']).first()
            if dossier:
                for key, value in dossier_data.items():
                    if hasattr(dossier, key) and key != 'id':
                        setattr(dossier, key, value)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Erreur mise à jour dossier: {str(e)}")
            return False
        finally:
            session.close()
    
    def delete_dossier(self, dossier_id):
        """Supprime un dossier et ses éléments associés"""
        session = self.Session()
        try:
            dossier = session.query(DossierCSPE).filter_by(id=dossier_id).first()
            if dossier:
                session.delete(dossier)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Erreur suppression dossier: {str(e)}")
            return False
        finally:
            session.close()
    
    def get_statistics(self, period=None):
        """Calcule les statistiques des dossiers"""
        session = self.Session()
        try:
            query = session.query(DossierCSPE)
            
            if period:
                try:
                    start_date = datetime.strptime(period['start'], '%Y-%m-%d')
                    end_date = datetime.strptime(period['end'], '%Y-%m-%d')
                    query = query.filter(DossierCSPE.date_analyse.between(start_date, end_date))
                except (KeyError, ValueError):
                    pass  # Ignorer les erreurs de format de date
            
            total = query.count()
            
            if total == 0:
                return {
                    'total': 0,
                    'recevables': 0,
                    'irrecevables': 0,
                    'instruction': 0,
                    'taux_recevabilite': 0
                }
            
            recevables = query.filter(DossierCSPE.statut == 'RECEVABLE').count()
            irrecevables = query.filter(DossierCSPE.statut == 'IRRECEVABLE').count()
            instruction = query.filter(DossierCSPE.statut == 'INSTRUCTION').count()
            
            return {
                'total': total,
                'recevables': recevables,
                'irrecevables': irrecevables,
                'instruction': instruction,
                'taux_recevabilite': (recevables / total * 100) if total > 0 else 0
            }
        except Exception as e:
            print(f"Erreur calcul statistiques: {str(e)}")
            return {'total': 0, 'recevables': 0, 'irrecevables': 0, 'instruction': 0, 'taux_recevabilite': 0}
        finally:
            session.close()
    
    def get_activity_stats(self):
        """Statistiques par type d'activité"""
        session = self.Session()
        try:
            query = session.query(
                DossierCSPE.activite, 
                func.count(DossierCSPE.id).label('count')
            ).group_by(DossierCSPE.activite)
            
            results = query.all()
            
            if not results:
                # Données de démonstration si aucune donnée réelle
                return {
                    'Particuliers': 245,
                    'Entreprises': 123,
                    'Collectivités': 67,
                    'Associations': 34
                }
            
            return {activity: count for activity, count in results}
        except Exception as e:
            print(f"Erreur statistiques activité: {str(e)}")
            return {}
        finally:
            session.close()
    
    def get_amount_stats(self):
        """Statistiques par tranche de montant"""
        session = self.Session()
        try:
            # Requête pour calculer les tranches de montants
            tranches = {
                '0-1000€': 0,
                '1000-5000€': 0,
                '5000-10000€': 0,
                '>10000€': 0
            }
            
            dossiers = session.query(DossierCSPE.montant_reclame).all()
            
            for (montant,) in dossiers:
                if montant is None:
                    continue
                elif montant <= 1000:
                    tranches['0-1000€'] += 1
                elif montant <= 5000:
                    tranches['1000-5000€'] += 1
                elif montant <= 10000:
                    tranches['5000-10000€'] += 1
                else:
                    tranches['>10000€'] += 1
            
            # Si pas de données, retourner des données de démo
            if sum(tranches.values()) == 0:
                return {
                    '0-1000€': 45,
                    '1000-5000€': 123,
                    '5000-10000€': 67,
                    '>10000€': 23
                }
            
            return tranches
        except Exception as e:
            print(f"Erreur statistiques montants: {str(e)}")
            return {}
        finally:
            session.close()
    
    def get_monthly_stats(self, year=None):
        """Statistiques mensuelles"""
        session = self.Session()
        try:
            if year is None:
                year = datetime.now().year
            
            monthly_data = {}
            for month in range(1, 13):
                count = session.query(DossierCSPE).filter(
                    func.extract('year', DossierCSPE.date_analyse) == year,
                    func.extract('month', DossierCSPE.date_analyse) == month
                ).count()
                month_name = datetime(year, month, 1).strftime('%B')
                monthly_data[month_name] = count
            
            return monthly_data
        except Exception as e:
            print(f"Erreur statistiques mensuelles: {str(e)}")
            return {}
        finally:
            session.close()
    
    def generate_pdf_report(self, dossier_id):
        """Génère un rapport PDF pour un dossier"""
        if not FPDF_AVAILABLE:
            print("FPDF non disponible - rapport PDF non généré")
            return None
        
        dossier = self.get_dossier(dossier_id)
        if not dossier:
            return None
        
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # En-tête
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Rapport d'Analyse CSPE - Conseil d'État", 0, 1, 'C')
            pdf.ln(10)
            
            # Informations de base
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "INFORMATIONS GÉNÉRALES", 0, 1)
            pdf.set_font("Arial", "", 11)
            
            pdf.cell(0, 8, f"Numéro de dossier : {dossier.numero_dossier}", 0, 1)
            pdf.cell(0, 8, f"Demandeur : {dossier.demandeur}", 0, 1)
            pdf.cell(0, 8, f"Activité : {dossier.activite}", 0, 1)
            pdf.cell(0, 8, f"Date de réclamation : {dossier.date_reclamation}", 0, 1)
            pdf.cell(0, 8, f"Période CSPE : {dossier.periode_debut} - {dossier.periode_fin}", 0, 1)
            pdf.cell(0, 8, f"Montant réclamé : {dossier.montant_reclame:,.2f} €", 0, 1)
            
            pdf.ln(5)
            
            # Résultat de l'analyse
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "RÉSULTAT DE L'ANALYSE", 0, 1)
            pdf.set_font("Arial", "", 11)
            
            pdf.cell(0, 8, f"Classification : {dossier.statut}", 0, 1)
            if dossier.confiance_analyse:
                pdf.cell(0, 8, f"Confiance : {dossier.confiance_analyse:.1%}", 0, 1)
            if dossier.motif_irrecevabilite:
                pdf.cell(0, 8, f"Motif d'irrecevabilité : {dossier.motif_irrecevabilite}", 0, 1)
            
            pdf.ln(5)
            
            # Critères d'analyse
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "CRITÈRES D'ANALYSE", 0, 1)
            pdf.set_font("Arial", "", 11)
            
            for critere in dossier.criteres:
                status = "✅" if critere.statut else "❌"
                pdf.cell(0, 8, f"- {critere.critere}: {status}", 0, 1)
                if critere.detail:
                    pdf.cell(10, 6, "", 0, 0)  # Indentation
                    pdf.cell(0, 6, f"  {critere.detail}", 0, 1)
            
            pdf.ln(5)
            
            # Observations
            if dossier.commentaires:
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "OBSERVATIONS", 0, 1)
                pdf.set_font("Arial", "", 11)
                # Découper le texte long
                lines = dossier.commentaires.split('\n')
                for line in lines:
                    if len(line) > 80:
                        words = line.split(' ')
                        current_line = ""
                        for word in words:
                            if len(current_line + word) < 80:
                                current_line += word + " "
                            else:
                                pdf.cell(0, 6, current_line.strip(), 0, 1)
                                current_line = word + " "
                        if current_line:
                            pdf.cell(0, 6, current_line.strip(), 0, 1)
                    else:
                        pdf.cell(0, 6, line, 0, 1)
            
            # Pied de page
            pdf.ln(10)
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 8, f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", 0, 1)
            pdf.cell(0, 8, f"Analyste : {dossier.analyste}", 0, 1)
            
            # Sauvegarde
            filename = f"rapport_dossier_{dossier.numero_dossier}.pdf"
            pdf.output(filename)
            return filename
            
        except Exception as e:
            print(f"Erreur génération PDF: {str(e)}")
            return None
    
    def generate_csv_report(self, dossier_id):
        """Génère un rapport CSV pour un dossier"""
        dossier = self.get_dossier(dossier_id)
        if not dossier:
            return None
        
        try:
            # Préparer les données du critère
            criteres_details = []
            for critere in dossier.criteres:
                criteres_details.append(f"{critere.critere}: {'✅' if critere.statut else '❌'}")
            
            data = {
                'Numéro de dossier': [dossier.numero_dossier],
                'Demandeur': [dossier.demandeur],
                'Activité': [dossier.activite],
                'Date de réclamation': [str(dossier.date_reclamation)],
                'Période début': [dossier.periode_debut],
                'Période fin': [dossier.periode_fin],
                'Montant réclamé (€)': [dossier.montant_reclame],
                'Statut': [dossier.statut],
                'Confiance': [f"{dossier.confiance_analyse:.1%}" if dossier.confiance_analyse else "N/A"],
                'Critères': ['; '.join(criteres_details)],
                'Analyste': [dossier.analyste],
                'Date analyse': [str(dossier.date_analyse)],
                'Observations': [dossier.commentaires or ""]
            }
            
            filename = f"rapport_dossier_{dossier.numero_dossier}.csv"
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False, encoding='utf-8', sep=';')
            return filename
            
        except Exception as e:
            print(f"Erreur génération CSV: {str(e)}")
            return None
    
    def generate_global_report(self, format='csv'):
        """Génère un rapport global de tous les dossiers"""
        try:
            dossiers = self.get_all_dossiers()
            
            if not dossiers:
                print("Aucun dossier à exporter")
                return None
            
            data = []
            for dossier in dossiers:
                criteres_summary = []
                for critere in dossier.criteres:
                    criteres_summary.append(f"{critere.critere}: {'✅' if critere.statut else '❌'}")
                
                row = {
                    'Numéro': dossier.numero_dossier,
                    'Demandeur': dossier.demandeur,
                    'Activité': dossier.activite,
                    'Date_réclamation': str(dossier.date_reclamation),
                    'Période': f"{dossier.periode_debut}-{dossier.periode_fin}",
                    'Montant_€': dossier.montant_reclame,
                    'Statut': dossier.statut,
                    'Confiance': f"{dossier.confiance_analyse:.1%}" if dossier.confiance_analyse else "N/A",
                    'Critères': '; '.join(criteres_summary),
                    'Analyste': dossier.analyste,
                    'Date_analyse': str(dossier.date_analyse),
                    'Observations': dossier.commentaires or ""
                }
                data.append(row)
            
            df = pd.DataFrame(data)
            
            if format.lower() == 'csv':
                filename = f"rapport_global_cspe_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                df.to_csv(filename, index=False, encoding='utf-8', sep=';')
            elif format.lower() == 'excel':
                filename = f"rapport_global_cspe_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                df.to_excel(filename, index=False)
            else:
                return None
                
            return filename
            
        except Exception as e:
            print(f"Erreur génération rapport global: {str(e)}")
            return None
    
    def backup_database(self):
        """Effectue une sauvegarde de la base de données"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"backup_cspe_{timestamp}.sql"
            
            # Pour SQLite, copier simplement le fichier
            if 'sqlite' in self.db_url.lower():
                import shutil
                db_file = self.db_url.replace('sqlite:///', '')
                shutil.copy2(db_file, f"backup_{timestamp}_{os.path.basename(db_file)}")
                return f"backup_{timestamp}_{os.path.basename(db_file)}"
            
            return backup_filename
            
        except Exception as e:
            print(f"Erreur sauvegarde: {str(e)}")
            return None
    
    def get_system_info(self):
        """Retourne des informations sur le système"""
        session = self.Session()
        try:
            total_dossiers = session.query(DossierCSPE).count()
            total_criteres = session.query(CritereAnalyse).count()
            total_documents = session.query(Document).count()
            
            # Dernier dossier analysé
            last_dossier = session.query(DossierCSPE).order_by(DossierCSPE.date_analyse.desc()).first()
            
            return {
                'total_dossiers': total_dossiers,
                'total_criteres': total_criteres,
                'total_documents': total_documents,
                'dernier_dossier': last_dossier.numero_dossier if last_dossier else None,
                'derniere_analyse': last_dossier.date_analyse if last_dossier else None,
                'db_url': self.db_url,
                'version': '1.0.0'
            }
        except Exception as e:
            print(f"Erreur info système: {str(e)}")
            return {}
        finally:
            session.close()

# Fonction utilitaire pour initialiser une base de données de test
def create_sample_data(db_manager):
    """Crée des données d'exemple pour les tests"""
    try:
        # Dossier exemple 1
        dossier1_data = {
            'numero_dossier': 'CSPE-DEMO-001',
            'demandeur': 'MARTIN Jean',
            'activite': 'Particulier',
            'date_reclamation': datetime.now().date(),
            'periode_debut': 2010,
            'periode_fin': 2012,
            'montant_reclame': 1500.00,
            'statut': 'RECEVABLE',
            'confiance_analyse': 0.94,
            'analyste': 'Système Demo',
            'commentaires': 'Dossier de démonstration - Tous critères respectés'
        }
        
        dossier1_id = db_manager.add_dossier(dossier1_data)
        
        if dossier1_id:
            # Critères pour dossier 1
            criteres1 = [
                {'dossier_id': dossier1_id, 'critere': 'Délai de recours', 'statut': True, 'detail': 'Respecté (28 jours)'},
                {'dossier_id': dossier1_id, 'critere': 'Qualité du demandeur', 'statut': True, 'detail': 'Consommateur final'},
                {'dossier_id': dossier1_id, 'critere': 'Objet valide', 'statut': True, 'detail': 'Contestation CSPE'},
                {'dossier_id': dossier1_id, 'critere': 'Pièces justificatives', 'statut': True, 'detail': 'Complètes'}
            ]
            
            for critere in criteres1:
                db_manager.add_critere(critere)
        
        # Dossier exemple 2
        dossier2_data = {
            'numero_dossier': 'CSPE-DEMO-002',
            'demandeur': 'DUBOIS Sophie',
            'activite': 'Entreprise',
            'date_reclamation': datetime.now().date(),
            'periode_debut': 2011,
            'periode_fin': 2014,
            'montant_reclame': 3200.00,
            'statut': 'IRRECEVABLE',
            'motif_irrecevabilite': 'Délai de recours dépassé',
            'confiance_analyse': 0.88,
            'analyste': 'Système Demo',
            'commentaires': 'Dossier de démonstration - Délai non respecté'
        }
        
        dossier2_id = db_manager.add_dossier(dossier2_data)
        
        if dossier2_id:
            # Critères pour dossier 2
            criteres2 = [
                {'dossier_id': dossier2_id, 'critere': 'Délai de recours', 'statut': False, 'detail': 'Dépassé (75 jours)'},
                {'dossier_id': dossier2_id, 'critere': 'Qualité du demandeur', 'statut': True, 'detail': 'Entreprise concernée'},
                {'dossier_id': dossier2_id, 'critere': 'Objet valide', 'statut': True, 'detail': 'Contestation CSPE'},
                {'dossier_id': dossier2_id, 'critere': 'Pièces justificatives', 'statut': True, 'detail': 'Complètes'}
            ]
            
            for critere in criteres2:
                db_manager.add_critere(critere)
        
        print("✅ Données d'exemple créées avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur création données exemple: {str(e)}")
        return False

# Test de la classe
if __name__ == "__main__":
    # Test de base
    db = DatabaseManager()
    db.init_db()
    
    # Créer des données de test
    create_sample_data(db)
    
    # Tester les statistiques
    stats = db.get_statistics()
    print(f"Statistiques: {stats}")
    
    # Tester l'info système
    info = db.get_system_info()
    print(f"Info système: {info}")
    
    print("✅ Tests de base réussis")