"""
Moteur d'analyse unifié pour les dossiers CSPE.

Ce module fournit une interface unifiée pour l'analyse des dossiers CSPE
en combinant les fonctionnalités de CSPEDocumentProcessor et CSPEExpertAnalyzer.
"""

from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json
import logging

from .document_processor import CSPEDocumentProcessor, CSPEEntity
from ..models.expert_analyzer import CSPEExpertAnalyzer, Decision

logger = logging.getLogger(__name__)

class CSPEAnalysisEngine:
    """Moteur d'analyse unifié pour les dossiers CSPE."""
    
    def __init__(self, llm_client=None):
        """Initialise le moteur d'analyse.
        
        Args:
            llm_client: Client pour les appels au modèle de langage (optionnel)
        """
        self.document_processor = CSPEDocumentProcessor()
        self.expert_analyzer = CSPEExpertAnalyzer(llm_client=llm_client)
        self.analysis_cache = {}
    
    def analyze_document(self, file_path: str) -> Dict[str, Any]:
        """Analyse un document unique.
        
        Args:
            file_path: Chemin vers le fichier à analyser
            
        Returns:
            Dictionnaire contenant les résultats de l'analyse
        """
        try:
            # Vérifier si l'analyse est en cache
            if file_path in self.analysis_cache:
                return self.analysis_cache[file_path]
            
            # Analyser avec le processeur de document
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            doc_analysis = {
                'file_path': str(file_path),
                'file_name': Path(file_path).name,
                'file_size': Path(file_path).stat().st_size,
                'analysis_date': datetime.now().isoformat(),
                'entities': {},
                'expert_analysis': None,
                'warnings': []
            }
            
            # Extraire les entités avec le processeur de document
            try:
                # Remplacer l'appel à extract_entities par les méthodes spécifiques
                dates = self.document_processor.extract_dates(content)
                amounts = self.document_processor.extract_amounts(content)
                references = self.document_processor.extract_references(content)
                
                # Combiner les références en une seule liste plate
                all_references = []
                for ref_list in references.values():
                    all_references.extend(ref_list)
                
                doc_analysis['entities'] = {
                    'dates': [e.to_dict() for e in dates],
                    'amounts': [e.to_dict() for e in amounts],
                    'references': [e.to_dict() for e in all_references]
                }
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction des entités: {e}")
                doc_analysis['warnings'].append(f"Erreur d'extraction des entités: {str(e)}")
            
            # Analyser avec l'expert
            try:
                expert_result = self.expert_analyzer.analyze_file(file_path)
                doc_analysis['expert_analysis'] = expert_result
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse experte: {e}")
                doc_analysis['warnings'].append(f"Erreur d'analyse experte: {str(e)}")
            
            # Mettre en cache les résultats
            self.analysis_cache[file_path] = doc_analysis
            return doc_analysis
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'analyse du document {file_path}")
            return {
                'file_path': str(file_path),
                'error': str(e),
                'analysis_date': datetime.now().isoformat()
            }
    
    def analyze_folder(self, folder_path: str) -> Dict[str, Any]:
        """Analyse un dossier contenant plusieurs documents.
        
        Args:
            folder_path: Chemin vers le dossier à analyser
            
        Returns:
            Dictionnaire contenant les résultats de l'analyse du dossier
        """
        try:
            folder_path = Path(folder_path)
            if not folder_path.is_dir():
                raise ValueError(f"Le chemin spécifié n'est pas un dossier: {folder_path}")
            
            # Analyser chaque fichier du dossier
            documents = []
            for file_path in folder_path.glob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    doc_analysis = self.analyze_document(str(file_path))
                    documents.append(doc_analysis)
            
            # Générer un rapport consolidé
            return self._generate_folder_report(documents, str(folder_path))
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'analyse du dossier {folder_path}")
            return {
                'folder_path': str(folder_path),
                'error': str(e),
                'analysis_date': datetime.now().isoformat()
            }
    
    def _generate_folder_report(self, documents: List[Dict], folder_path: str) -> Dict[str, Any]:
        """Génère un rapport consolidé pour un dossier.
        
        Args:
            documents: Liste des analyses de documents
            folder_path: Chemin du dossier analysé
            
        Returns:
            Dictionnaire contenant le rapport consolidé
        """
        # Détecter le type de dossier
        folder_name = Path(folder_path).name.upper()
        case_type = self._detect_case_type(folder_name)
        
        # Extraire les métriques globales
        total_docs = len(documents)
        total_warnings = sum(len(doc.get('warnings', [])) for doc in documents)
        
        # Compiler les entités trouvées
        all_dates = []
        all_amounts = []
        for doc in documents:
            all_dates.extend(doc.get('entities', {}).get('dates', []))
            all_amounts.extend(doc.get('entities', {}).get('amounts', []))
        
        # Trier les dates et montants
        all_dates.sort(key=lambda x: x.get('value', ''))
        all_amounts.sort(key=lambda x: float(x.get('value', 0)))
        
        # Détecter les incohérences
        inconsistencies = self._detect_inconsistencies(documents)
        
        return {
            'folder_path': folder_path,
            'folder_name': Path(folder_path).name,
            'case_type': case_type,
            'analysis_date': datetime.now().isoformat(),
            'documents_analyzed': total_docs,
            'total_warnings': total_warnings,
            'dates_found': all_dates[-5:] if all_dates else [],  # 5 dates les plus récentes
            'amounts_found': all_amounts[-5:] if all_amounts else [],  # 5 montants les plus élevés
            'inconsistencies': inconsistencies,
            'documents': documents
        }
    
    def _detect_case_type(self, folder_name: str) -> str:
        """Détecte le type de cas à partir du nom du dossier."""
        if "RECEVABLE" in folder_name and "IRRECEVABLE" not in folder_name:
            return "Recevable"
        elif "IRRECEVABLE" in folder_name:
            if "DELAI" in folder_name:
                return "Irrecevable (Délai dépassé)"
            elif "PERIODE" in folder_name or "NON_COUVERTE" in folder_name:
                return "Irrecevable (Période non couverte)"
            elif "PRESCRIPTION" in folder_name:
                return "Irrecevable (Prescription quadriennale)"
            elif "REPERCUSSION" in folder_name:
                return "Irrecevable (Répercussion client)"
            return "Irrecevable (Autre motif)"
        elif "COMPLEXE" in folder_name:
            return "Complexe (Analyse experte requise)"
        elif "FUSION" in folder_name or "ACQUISITION" in folder_name:
            return "Fusion/Acquisition"
        return "Inconnu"
    
    def _detect_inconsistencies(self, documents: List[Dict]) -> List[Dict]:
        """Détecte les incohérences entre les documents."""
        inconsistencies = []
        
        # Vérifier les dates incohérentes
        dates = []
        for doc in documents:
            for date_entity in doc.get('entities', {}).get('dates', []):
                try:
                    date_str = date_entity.get('value')
                    if date_str and len(date_str) == 10:  # Format YYYY-MM-DD
                        dates.append((date_str, doc['file_name']))
                except:
                    continue
        
        # Vérifier les doublons de documents
        seen_docs = {}
        for doc in documents:
            content = open(doc['file_path'], 'r', encoding='utf-8', errors='ignore').read()
            content_hash = hash(content[:1000])  # Prendre un hash du début du contenu
            if content_hash in seen_docs:
                inconsistencies.append({
                    'type': 'document_duplicate',
                    'severity': 'medium',
                    'message': f"Document similaire à {seen_docs[content_hash]}",
                    'files': [doc['file_name'], seen_docs[content_hash]]
                })
            else:
                seen_docs[content_hash] = doc['file_name']
        
        return inconsistencies
