import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
from typing import Dict, List, Tuple
import base64
import PyPDF2
from docx import Document
import io
import requests
import json
from dotenv import load_dotenv
import os

# Configuration de la page
st.set_page_config(
    page_title="Assistant CSPE - Conseil d'État",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Chargement des variables d'environnement
load_dotenv()
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'mistral:7b')

# CSS personnalisé pour style administratif
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
    padding: 2rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}

.criteria-section {
    background: #f8fafc;
    padding: 1.5rem;
    border-radius: 10px;
    border-left: 5px solid #3b82f6;
    margin: 1rem 0;
}

.recevable {
    background: #f0fdf4;
    border-left: 5px solid #22c55e;
    padding: 1rem;
    border-radius: 5px;
}

.irrecevable {
    background: #fef2f2;
    border-left: 5px solid #ef4444;
    padding: 1rem;
    border-radius: 5px;
}

.instruction-complementaire {
    background: #fffbeb;
    border-left: 5px solid #f59e0b;
    padding: 1rem;
    border-radius: 5px;
}

.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: center;
}

.upload-area {
    background: #f8fafc;
    padding: 2rem;
    border-radius: 10px;
    border: 1px dashed #3b82f6;
    margin: 1rem 0;
}

.document-list {
    background: #f8fafc;
    padding: 1rem;
    border-radius: 10px;
    margin: 1rem 0;
}

.document-item {
    background: white;
    padding: 0.5rem;
    border-radius: 5px;
    margin: 0.5rem 0;
    border: 1px solid #e2e8f0;
}
</style>
""", unsafe_allow_html=True)

def extract_date(text: str) -> datetime:
    """Extrait la date du document"""
    date_patterns = [
        r"(\d{1,2})\s*(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s*(\d{4})",
        r"(\d{1,2})/(\d{1,2})/(\d{4})",
        r"(\d{4})-(\d{2})-(\d{2})"
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                if len(match.groups()) == 3:
                    day, month, year = match.groups()
                    return datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y")
                elif len(match.groups()) == 2:
                    month, year = match.groups()
                    return datetime.strptime(f"1/{month}/{year}", "%d/%m/%Y")
            except ValueError:
                continue
    return None

def extract_cspe_years(text: str) -> List[int]:
    """Extrait les années CSPE mentionnées"""
    years = re.findall(r'\b(?:200[9-9]|201[0-5])\b', text)
    return list(set(int(year) for year in years))

def extract_company_and_years(text: str) -> Dict:
    """Extrait les informations sur les sociétés et les années concernées"""
    # Extraction des noms de sociétés (peut être amélioré avec des patterns plus sophistiqués)
    company_patterns = [
        r'(?i)(?:société|entreprise|sas|sa|sarl|eurl)\s+(\w+(?:\s+\w+)*)',
        r'(\w+(?:\s+\w+)*)\s+(?:fonderie|usine|usinage|martin|dupont)'
    ]
    companies = []
    for pattern in company_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            company = match.group(1).strip()
            if company not in companies:
                companies.append(company)
    
    # Extraction des années avec leurs montants
    years = {}
    amount_patterns = [
        r'(?i)(?:20\d{2})\s*:?\s*(?:\d{1,3}(?:\.|,)?\d{3}(?:\.|,)?\d{2}?)',
        r'(?i)(?:\d{1,3}(?:\.|,)?\d{3}(?:\.|,)?\d{2}?)\s*(?:€|euros)?\s*(?:pour\s*|de\s*)?(?:20\d{2})'
    ]
    
    for pattern in amount_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            text = match.group(0)
            year = re.search(r'20\d{2}', text)
            amount = re.search(r'\d{1,3}(?:\.|,)?\d{3}(?:\.|,)?\d{2}?', text)
            if year and amount:
                year = year.group(0)
                amount = float(amount.group(0).replace(',', '.').replace(' ', ''))
                if year not in years:
                    years[year] = amount
                else:
                    years[year] += amount
    
    return {
        'companies': companies,
        'years': years
    }

def check_delay(text: str) -> Dict:
    """Vérifie le délai de réclamation"""
    date = extract_date(text)
    if not date:
        return {
            'status': '⚠️ À vérifier',
            'details': 'Date non trouvée dans le document'
        }
    
    cspe_years = extract_cspe_years(text)
    if not cspe_years:
        return {
            'status': '⚠️ À vérifier',
            'details': 'Années CSPE non trouvées'
        }
    
    latest_year = max(cspe_years)
    deadline = datetime(latest_year + 1, 12, 31)
    
    return {
        'status': '✅ Respecté' if date <= deadline else '❌ Dépassé',
        'details': f"Date réclamation : {date.strftime('%d/%m/%Y')} - Délai : {deadline.strftime('%d/%m/%Y')}",
        'deadline': deadline.strftime('%d/%m/%Y')
    }

def check_period(text: str) -> Dict:
    """Vérifie la période couverte"""
    years = extract_cspe_years(text)
    valid_years = [year for year in years if 2009 <= year <= 2015]
    
    if not valid_years:
        return {
            'status': '❌ Hors période',
            'details': 'Aucune année dans la période 2009-2015'
        }
    
    return {
        'status': '✅ Couverte',
        'details': f'Période couverte : {min(valid_years)}-{max(valid_years)}'
    }

def check_prescription(text: str) -> Dict:
    """Vérifie la prescription quadriennale"""
    date = extract_date(text)
    if not date:
        return {
            'status': '⚠️ À vérifier',
            'details': 'Date non trouvée pour calcul prescription'
        }
    
    cspe_years = extract_cspe_years(text)
    if not cspe_years:
        return {
            'status': '⚠️ À vérifier',
            'details': 'Années CSPE non trouvées'
        }
    
    latest_year = max(cspe_years)
    prescription_date = datetime(latest_year + 4, 1, 1)
    
    return {
        'status': '✅ Non prescrit' if date <= prescription_date else '❌ Prescrit',
        'details': f"Date réclamation : {date.strftime('%d/%m/%Y')} - Prescription : {prescription_date.strftime('%d/%m/%Y')}",
        'prescription_date': prescription_date.strftime('%d/%m/%Y')
    }

def check_repercussion(text: str) -> Dict:
    """Vérifie la répercussion de la CSPE"""
    keywords = [
        "répercutée", "charges communes", "délibération AG", "syndic",
        "copropriétaires", "gestionnaire", "clients", "revente",
        "négoce", "distribution", "revendeur", "distributeur"
    ]
    
    lower_text = text.lower()
    found_keywords = []
    for keyword in keywords:
        if keyword in lower_text:
            found_keywords.append(keyword)
    
    if found_keywords:
        return {
            'status': '❌ Répercutée',
            'details': f"Mots-clés trouvés : {', '.join(found_keywords)}"
        }
    
    return {
        'status': '✅ Pas de répercussion',
        'details': 'Aucun indice de répercussion détecté'
    }

def extract_text_from_file(file) -> str:
    """Extrait le texte d'un fichier selon son type"""
    if not file:
        return ""
    
    if file.type == 'application/pdf':
        return extract_text_from_pdf(file.getvalue())
    elif file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return extract_text_from_docx(file.getvalue())
    elif file.type in ['image/png', 'image/jpeg', 'image/jpg']:
        return extract_text_from_image(file.getvalue())
    elif file.type == 'text/plain':
        return file.getvalue().decode('utf-8')
    return ""

def clean_text(text: str) -> str:
    """Nettoie le texte pour l'analyse"""
    # Supprime les caractères spéciaux et les espaces multiples
    text = re.sub(r'\s+', ' ', text)
    # Supprime les caractères de contrôle
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', ' ', text)
    # Supprime les lignes vides
    text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
    return text

def analyze_document(text: str) -> Dict:
    """Analyse complète du dossier CSPE"""
    # Nettoyage du texte
    text = clean_text(text)
    
    # Extraction des informations de base
    company_data = extract_company_and_years(text)
    
    # Vérification des critères
    criteria = {
        'délai': check_delay(text),
        'période': check_period(text),
        'prescription': check_prescription(text),
        'répercussion': check_repercussion(text)
    }
    
    # Calcul du montant recevable
    total_claimed = sum(company_data['years'].values())
    receivable_amount = 0
    
    # Analyse par société et période
    analysis_by_company = {}
    
    # Extraction des dates de réclamation
    dates = extract_dates(text)
    latest_date = max(dates) if dates else None
    
    for company in company_data['companies']:
        analysis_by_company[company] = {}
        
        # Pour chaque année de la période 2009-2015
        for year in range(2009, 2016):
            if str(year) in company_data['years']:
                amount = company_data['years'][str(year)]
                
                # Vérification du délai pour cette année
                year_date = datetime(year, 12, 31)
                deadline = datetime(year + 1, 12, 31)
                
                # Si on a une date de réclamation, on l'utilise
                if latest_date and latest_date <= deadline:
                    status = "✅" if amount > 0 else "❌"
                    receivable_amount += amount
                else:
                    status = f'❌ IRRECEVABLE (délai dépassé {deadline.strftime("%d/%m/%Y")})'
                
                analysis_by_company[company][year] = {
                    'status': status,
                    'amount': f"{amount:.2f} €"
                }
    
    # Décision finale
    if all(crit['status'].startswith('✅') for crit in criteria.values()):
        decision = 'RECEVABLE'
    elif any(crit['status'].startswith('❌') for crit in criteria.values()):
        decision = 'IRRECEVABLE majoritairement'
    else:
        decision = 'RECEVABLE partiellement'
    
    return {
        'decision': decision,
        'criteria': criteria,
        'analysis_by_company': analysis_by_company,
        'total_claimed': f"{total_claimed:.2f} €",
        'receivable_amount': f"{receivable_amount:.2f} €",
        'confidence': 'Élevée' if all(crit['status'].startswith('✅') for crit in criteria.values()) else 'Moyenne'
    }

def display_analysis_results(results: Dict):
    """Affiche les résultats de l'analyse"""
    try:
        st.header("📊 Résultats d'Analyse")
        
        # Synthèse
        st.subheader("SYNTHÈSE")
        
        # Décision
        decision = results.get('decision', 'INSTRUCTION')
        if decision == 'RECEVABLE':
            st.success("RECEVABLE ☑")
            st.checkbox("IRRECEVABLE", value=False, disabled=True)
            st.checkbox("COMPLÉMENT D'INSTRUCTION", value=False, disabled=True)
        elif decision == 'IRRECEVABLE':
            st.checkbox("RECEVABLE", value=False, disabled=True)
            st.error("IRRECEVABLE ☑")
            st.checkbox("COMPLÉMENT D'INSTRUCTION", value=False, disabled=True)
        else:
            st.checkbox("RECEVABLE", value=False, disabled=True)
            st.checkbox("IRRECEVABLE", value=False, disabled=True)
            st.warning("COMPLÉMENT D'INSTRUCTION ☑")
        
        # Détail par société/période
        st.subheader("DÉTAIL PAR SOCIÉTÉ/PÉRIODE")
        
        # Vérification de la clé analysis_by_company
        if 'analysis_by_company' not in results:
            st.warning("⚠️ Aucune analyse détaillée disponible")
            return
            
        analysis_by_company = results['analysis_by_company']
        
        if not analysis_by_company:
            st.warning("⚠️ Aucune société trouvée dans l'analyse")
            return
            
        # Affichage des résultats par société
        for company, periods in analysis_by_company.items():
            with st.expander(f"{company}"):
                for year, amount in periods.items():
                    # Calcul du statut en fonction du montant
                    status = "✅" if amount > 0 else "❌"
                    st.write(f"- {year} : {amount} € {status}")
        
        # Critères
        st.subheader("CRITÈRES")
        criteria = results.get('critères', {})
        for criterion, status in criteria.items():
            st.write(f"- {criterion} : {status}")
        
        # Observations
        st.subheader("OBSERVATIONS")
        observations = results.get('observations', "Aucune observation disponible")
        st.write(observations)
        
    except Exception as e:
        st.error(f"Erreur lors de l'affichage des résultats : {str(e)}")

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extrait le texte d'un fichier PDF"""
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file_content: bytes) -> str:
    """Extrait le texte d'un fichier Word"""
    doc = Document(io.BytesIO(file_content))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_text_from_image(file_content: bytes) -> str:
    """Extrait le texte d'une image (TODO: OCR)"""
    return "TODO: OCR - Extraction de texte depuis image"

def combine_documents(documents: List[Dict]) -> str:
    """Combine le contenu de plusieurs documents"""
    combined_text = ""
    for doc in documents:
        text = extract_text_from_file(doc['file'])
        if text:
            combined_text += f"\n\n=== DOCUMENT : {doc['name']} ===\n\n{text}\n\n"
    return combined_text

def display_document_list(documents: List[Dict]):
    """Affiche la liste des documents chargés"""
    if not documents:
        st.info("Aucun document chargé")
        return
    
    st.markdown("""
    <div class="document-list">
        <h3>Documents chargés</h3>
        <div class="document-items">
    """, unsafe_allow_html=True)
    
    for doc in documents:
        st.markdown(f"""
        <div class="document-item">
            <strong>{doc['name']}</strong>
            <p>Type: {doc['type']}</p>
            <p>Taille: {doc['size'] / 1024:.1f} KB</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

def extract_dates(text: str) -> List[datetime]:
    """Extrait toutes les dates du texte dans différents formats"""
    date_patterns = [
        r'\b(\d{1,2})\s*(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s*(\d{4})\b',
        r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',
        r'\b(\d{4})-(\d{2})-(\d{2})\b',
        r'\b(\d{1,2})\s*(?:jan|fév|mar|avr|mai|juin|juil|août|sep|oct|nov|déc)\s*(\d{4})\b',
        r'\b(\d{1,2})\s*(?:jan.|fév.|mar.|avr.|mai|juin|juil.|août|sep.|oct.|nov.|déc.)\s*(\d{4})\b'
    ]
    
    dates = []
    for pattern in date_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                if len(match.groups()) == 3:
                    day, month, year = match.groups()
                    date_str = f"{day}/{month}/{year}"
                elif len(match.groups()) == 2:
                    month, year = match.groups()
                    date_str = f"1/{month}/{year}"
                else:
                    continue
                
                date = datetime.strptime(date_str, "%d/%m/%Y")
                dates.append(date)
            except (ValueError, IndexError):
                continue
    
    return sorted(set(dates))

def test_llm_connection():
    """Teste la connexion au LLM"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        if response.status_code == 200:
            return True, "🟢 Connexion réussie"
        return False, f"🟡 Connexion échouée : {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"🔴 Erreur : {str(e)}"

def get_available_models():
    """Récupère la liste des modèles disponibles"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def validate_llm_response(response: Dict) -> Dict:
    """Valide la réponse du LLM et renvoie une réponse par défaut si le format n'est pas correct"""
    try:
        # Vérification du format de base
        if not isinstance(response, dict):
            raise ValueError("Réponse non valide")
            
        # Vérification des clés requises
        required_keys = ['decision', 'critères', 'observations']
        if not all(key in response for key in required_keys):
            raise ValueError("Clés manquantes dans la réponse")
            
        # Vérification des valeurs des critères
        criteria = response.get('critères', {})
        if not all(key in ['délai', 'période', 'prescription', 'répercussion'] for key in criteria):
            raise ValueError("Critères invalides")
            
        return response
    except Exception as e:
        # Retourne une réponse par défaut en cas d'erreur
        return {
            'decision': 'INSTRUCTION',
            'critères': {
                'délai': '⚠️ À vérifier',
                'période': '⚠️ À vérifier',
                'prescription': '⚠️ À vérifier',
                'répercussion': '⚠️ À vérifier'
            },
            'observations': f"Erreur de format dans la réponse LLM : {str(e)}"
        }

def extract_company_data(text: str) -> Dict:
    """Extrait les données par société et période à partir du texte"""
    # Extraction des noms de sociétés plus précise
    companies = []
    # Recherche des formes juridiques suivies par un nom
    patterns = [
        r'(?:Société|SAS|SA|SARL|EURL|SNC|SARL\s+Unipersonnelle)\s+([\w\s-]+)',
        r'(?:NOUVELLE\s+)?SOCIÉTÉ\s+INDUSTRIELLE\s+RÉUNI(?:E)?',
        r'MARTIN',
        r'DUPONT',
        r'FONDERIE\s+DUPONT'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        companies.extend(matches)
    
    # Suppression des doublons et des entrées vides
    companies = list(set([c.strip() for c in companies if c.strip()]))
    
    # Filtrer les noms de sociétés pour éviter les faux positifs
    valid_companies = []
    seen_names = set()
    for company in companies:
        # Ignorer les mots courants et les termes non pertinents
        if any(term.lower() in company.lower() for term in ['absorbante', 'absorbée', 'contrat', 'note', 'confidentielle', 'siret', 'nsir', 'greffier', 'fiscal', 'sociale']):
            continue
            
        # Nettoyer le nom de la société
        clean_company = company.strip().upper()
        
        # Ignorer les doublons (par exemple "SOCIETE" et "SOCIÉTÉ")
        if clean_company not in seen_names:
            seen_names.add(clean_company)
            valid_companies.append(company)
    
    # Extraction des montants avec unité (€)
    amounts = re.findall(r'(?i)(\d+(?:,\d{2})?\s*€|\d+(?:\.\d{2})?\s*€)', text)
    
    # Extraction des années (2009-2015)
    years = re.findall(r'\b(?:200[9-9]|201[0-5])\b', text)
    
    # Création de la structure de données
    analysis_by_company = {}
    
    # Initialiser avec les noms de sociétés valides
    for company in valid_companies:
        analysis_by_company[company] = {}
        for year in years:
            analysis_by_company[company][year] = 0.0
    
    # Si on a des montants et des années, distribuer les montants
    if amounts and years:
        # Convertir les montants en float et les sommer
        amounts_float = []
        for amount in amounts:
            try:
                clean_amount = float(amount.replace('€', '').replace(',', '.').strip())
                if clean_amount > 0:  # Ignorer les montants négatifs ou nuls
                    amounts_float.append(clean_amount)
            except ValueError:
                continue
        
        if amounts_float:  # Vérifier qu'on a au moins un montant valide
            total_amount = sum(amounts_float)
            # Distribuer le montant total de manière égale sur les années
            amount_per_year = total_amount / len(years)
            
            # Distribuer le montant sur chaque société
            for company in analysis_by_company:
                for year in years:
                    analysis_by_company[company][year] = amount_per_year / len(analysis_by_company)
    
    return analysis_by_company

def analyze_with_llm(text: str, model: str = DEFAULT_MODEL) -> Dict:
    """Analyse le texte avec le LLM"""
    prompt = """
    # 🏛️ PROMPT SYSTÈME : EXPERT INSTRUCTION DOSSIERS CSPE - CONSEIL D'ÉTAT

    ## ANALYSE DOSSIER CSPE
    
    Texte à analyser : {text}
    
    ## CRITÈRES D'ANALYSE
    1. **Délai de réclamation :**
    - CSPE 2013 → Réclamation avant 31/12/2014
    - CSPE 2014 → Réclamation avant 31/12/2015
    
    2. **Période couverte :**
    - Seules les années 2009-2015 sont éligibles
    
    3. **Prescription :**
    - Réclamation valable 4 ans
    - Renouvellement ou recours nécessaire
    
    4. **Répercussion :**
    - CSPE non répercutée aux clients finaux
    - Vérification activité et comptabilité
    
    ## FORMAT DE RÉPONSE
    {
        "decision": "RECEVABLE/IRRECEVABLE/INSTRUCTION",
        "critères": {
            "délai": "✅/❌",
            "période": "✅/❌",
            "prescription": "✅/❌",
            "répercussion": "✅/❌"
        },
        "observations": "Détails de l'analyse",
        "analysis_by_company": {
            "NOM SOCIÉTÉ": {
                "2009": 0.0,
                "2010": 0.0,
                "2011": 0.0,
                "2012": 0.0,
                "2013": 0.0,
                "2014": 0.0,
                "2015": 0.0
            }
        }
    }
    """
    
    try:
        # Appel à l'API Ollama
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt.format(text=text),
                "stream": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            # Nettoyage de la réponse pour extraire le JSON
            response_text = result['response'].strip()
            # Suppression des caractères non valides
            response_text = re.sub(r'[^\{\}\[\]\:\,\w\s"\-\.]', '', response_text)
            try:
                response_dict = json.loads(response_text)
                # Vérifier et compléter la structure si nécessaire
                if 'analysis_by_company' not in response_dict:
                    response_dict['analysis_by_company'] = extract_company_data(text)
                return validate_llm_response(response_dict)
            except json.JSONDecodeError:
                # Si le JSON est invalide, utiliser l'extraction directe
                return validate_llm_response({
                    'decision': 'INSTRUCTION',
                    'critères': {
                        'délai': '⚠️ À vérifier',
                        'période': '⚠️ À vérifier',
                        'prescription': '⚠️ À vérifier',
                        'répercussion': '⚠️ À vérifier'
                    },
                    'observations': "Réponse LLM invalide, analyse par extraction directe",
                    'analysis_by_company': extract_company_data(text)
                })
        return validate_llm_response({
            'decision': 'INSTRUCTION',
            'critères': {
                'délai': '⚠️ À vérifier',
                'période': '⚠️ À vérifier',
                'prescription': '⚠️ À vérifier',
                'répercussion': '⚠️ À vérifier'
            },
            'observations': "Erreur lors de l'appel à l'API LLM",
            'analysis_by_company': extract_company_data(text)
        })
    except Exception as e:
        st.error(f"Erreur lors de l'analyse : {str(e)}")
        return validate_llm_response({
            'decision': 'INSTRUCTION',
            'critères': {
                'délai': '⚠️ À vérifier',
                'période': '⚠️ À vérifier',
                'prescription': '⚠️ À vérifier',
                'répercussion': '⚠️ À vérifier'
            },
            'observations': f"Erreur technique : {str(e)}",
            'analysis_by_company': extract_company_data(text)
        })

def main():
    """Fonction principale"""
    # Test de la connexion au LLM
    llm_status, llm_message = test_llm_connection()
    st.sidebar.markdown(f"**Statut LLM :** {llm_message}")
    
    # Sélection du modèle
    available_models = get_available_models()
    selected_model = st.sidebar.selectbox(
        "Sélection du modèle LLM",
        available_models,
        index=available_models.index(DEFAULT_MODEL) if DEFAULT_MODEL in available_models else 0
    )
    
    # En-tête principal
    st.markdown("""
    <div class="main-header">
        <h1>🏛️ Assistant CSPE - Conseil d'État</h1>
        <p>Système d'aide à l'instruction des réclamations CSPE</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar avec informations système
    with st.sidebar:
        st.header("📋 Informations Système")
        st.info("**Version :** 1.0.0")
        st.info("**Base légale :** Code de l'énergie")
        
        st.header("📊 Statistiques")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Dossiers traités", "0")
        with col2:
            st.metric("Taux recevabilité", "-%")
        
        st.header("🔍 Critères CSPE")
        st.markdown("""
        1. **Délai de réclamation :**
        - CSPE 2013 → Réclamation avant 31/12/2014
        - CSPE 2014 → Réclamation avant 31/12/2015
        
        2. **Période couverte :**
        - Seules les années 2009-2015 sont éligibles
        
        3. **Prescription :**
        - Réclamation valable 4 ans
        - Renouvellement ou recours nécessaire
        
        4. **Répercussion :**
        - CSPE non répercutée aux clients finaux
        - Vérification activité et comptabilité
        """)

    # Interface principale
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📁 Analyse de Dossier")
        
        # Zone d'upload
        st.markdown("""
        <div class="upload-area">
            <h3>📁 Importez vos documents</h3>
            <p>Choisissez plusieurs fichiers (PDF, DOCX, TXT, PNG, JPG)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Upload de plusieurs fichiers
        uploaded_files = st.file_uploader(
            "",
            type=['pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="Formats acceptés : PDF, DOCX, TXT, PNG, JPG"
        )
        
        # Affichage de la liste des documents
        documents = []
        if uploaded_files:
            for file in uploaded_files:
                documents.append({
                    'file': file,
                    'name': file.name,
                    'type': file.type,
                    'size': file.size
                })
        
        display_document_list(documents)
        
        # Zone de saisie de texte
        st.markdown("""
        <div class="criteria-section">
            <h3>✏️ Saisie directe</h3>
            <p>Collez le contenu du dossier CSPE ici</p>
        </div>
        """, unsafe_allow_html=True)
        
        document_text = st.text_area(
            "",
            height=200,
            placeholder="Collez le contenu du dossier CSPE ici..."
        )
        
        # Bouton d'analyse
        if st.button("🔍 ANALYSER LE DOSSIER", type="primary", use_container_width=True):
            with st.spinner("Analyse en cours..."):
                if documents:
                    combined_text = combine_documents(documents)
                else:
                    combined_text = document_text
                
                if combined_text:
                    results = analyze_with_llm(combined_text, selected_model)
                    if results:
                        display_analysis_results(results)
                    else:
                        st.error("Erreur lors de l'analyse")
                else:
                    st.error("Aucun texte à analyser")
    
    with col2:
        st.header("📊 Résultats d'Analyse")
        
        # Zone d'affichage des résultats
        if not uploaded_files and not document_text:
            st.info("👆 Importez des documents ou saisissez du texte pour commencer l'analyse")
        else:
            st.empty()
        
        # Aide contextuelle
        with st.expander("❓ Guide des critères CSPE"):
            st.markdown("""
            **Critère 1 - Délai de réclamation :**
            - CSPE 2013 → Réclamation avant 31/12/2014
            - CSPE 2014 → Réclamation avant 31/12/2015
            
            **Critère 2 - Période couverte :**
            - Seules les années 2009-2015 sont éligibles
            
            **Critère 3 - Prescription :**
            - Réclamation valable 4 ans
            - Renouvellement ou recours nécessaire
            
            **Critère 4 - Répercussion :**
            - CSPE non répercutée aux clients finaux
            - Vérification activité et comptabilité
            """)

if __name__ == "__main__":
    main()
