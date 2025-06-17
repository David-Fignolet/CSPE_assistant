import json
import logging
import requests
from datetime import datetime
from typing import Dict, Optional, List, Any
from ..config import config

class CSPEClassifier:
    """
    Classifieur pour l'analyse des dossiers CSPE utilisant un modèle LLM.
    
    Utilise Ollama avec le modèle Mistral 7B pour effectuer la classification
    des dossiers selon les critères de recevabilité.
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialise le classifieur avec le modèle spécifié.
        
        Args:
            model_name: Nom du modèle Ollama à utiliser (par défaut: valeur de la config)
        """
        self.model_name = model_name or config.DEFAULT_MODEL
        self.ollama_url = f"{config.OLLAMA_URL}/api/generate"  # Utilisation de /api/generate
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialisation du classifieur avec le modèle: {self.model_name}")
    
    def analyze_document(self, text: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Analyse un document CSPE et retourne les résultats de classification.
        
        Args:
            text: Texte du document à analyser
            metadata: Métadonnées optionnelles
            
        Returns:
            Dictionnaire contenant les résultats de l'analyse
        """
        self.logger.info("Début de l'analyse du document")
        
        try:
            # Préparation du prompt
            prompt = self._prepare_prompt(text, metadata or {})
            
            # Appel au modèle Ollama
            raw_response = self._call_ollama(prompt)
            
            # Traitement de la réponse
            result = self._process_response(raw_response, metadata or {})
            
            self.logger.info("Analyse du document terminée avec succès")
            return result
            
        except Exception as e:
            error_msg = f"Erreur lors de l'analyse du document: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return self._create_error_response(error_msg, metadata or {})
    
    def _prepare_prompt(self, text: str, metadata: Dict) -> str:
        """Prépare le prompt pour le LLM."""
        return f"""
        Tu es un expert en analyse de dossiers CSPE (Contribution au Service Public de l'Électricité).
        
        Analyse le dossier suivant et détermine s'il est recevable selon ces critères :
        1. Délai de dépôt respecté (dans les 18 mois suivant la décision)
        2. Qualité du demandeur (exploitant d'installation électrique)
        3. Objet de la demande valide (frais liés à la CSPE)
        4. Pièces justificatives complètes
        
        Texte du dossier :
        {text[:4000]}  # Limite de contexte
        
        Format de réponse attendu (JSON) :
        {{
            "classification": "RECEVABLE" ou "IRRECEVABLE",
            "score_confidence": nombre entre 0 et 1,
            "critères_manquants": ["liste", "des", "critères", "manquants"],
            "raison": "Explication détaillée de la décision"
        }}
        """
    
    def _call_ollama(self, prompt: str) -> str:
        """
        Appelle l'API Ollama avec le prompt fourni.
        
        Args:
            prompt: Le prompt à envoyer au modèle
            
        Returns:
            La réponse brute du modèle
            
        Raises:
            Exception: En cas d'erreur lors de l'appel API
        """
        self.logger.debug("Appel à l'API Ollama")
        
        try:
            # Préparation du prompt complet avec les instructions
            full_prompt = f"""
            Tu es un expert en analyse de dossiers CSPE (Contribution au Service Public de l'Électricité).
            Analyse le document suivant et réponds au format JSON avec les champs demandés.
            
            Document à analyser :
            {prompt}
            
            Réponds UNIQUEMENT avec un objet JSON valide contenant ces champs :
            - classification (RECEVABLE, IRRECEVABLE ou INSTRUCTION)
            - score_confidence (nombre entre 0 et 1)
            - critères_manquants (liste des critères manquants)
            - raison (explication détaillée de la décision)
            """
            
            # Préparation des données pour la requête
            data = {
                "model": self.model_name,
                "prompt": full_prompt.strip(),
                "stream": False,
                "format": "json"
            }
            
            self.logger.debug(f"Envoi de la requête à {self.ollama_url}")
            self.logger.debug(f"Données de la requête: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # Envoi de la requête
            response = requests.post(
                self.ollama_url,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=60  # Timeout de 60 secondes
            )
            
            self.logger.debug(f"Réponse reçue - Statut: {response.status_code}")
            self.logger.debug(f"En-têtes de la réponse: {response.headers}")
            
            # Vérification du code de statut HTTP
            response.raise_for_status()
            
            # Traitement de la réponse
            response_data = response.json()
            self.logger.debug(f"Corps de la réponse: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            
            if 'response' not in response_data:
                self.logger.warning("La réponse ne contient pas de clé 'response'")
                return json.dumps({
                    "classification": "INSTRUCTION",
                    "score_confidence": 0.0,
                    "critères_manquants": ["erreur_technique"],
                    "raison": "Format de réponse inattendu du service d'IA"
                })
            
            return response_data['response']
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Erreur lors de l'appel à l'API Ollama: {str(e)}"
            self.logger.error(error_msg)
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Détails de l'erreur: {e.response.text}")
            
            # Retourne une réponse par défaut en cas d'erreur
            return json.dumps({
                "classification": "INSTRUCTION",
                "score_confidence": 0.0,
                "critères_manquants": ["erreur_technique"],
                "raison": f"Erreur de communication avec le service d'IA: {str(e)}"
            })
    
    def _process_response(self, raw_response: str, metadata: Dict) -> Dict:
        """
        Traite la réponse brute du modèle.
        
        Args:
            raw_response: Réponse brute du modèle
            metadata: Métadonnées à inclure dans la réponse
            
        Returns:
            Dictionnaire structuré avec les résultats de l'analyse
        """
        try:
            # Nettoyage de la réponse (parfois le modèle ajoute du texte autour du JSON)
            json_str = raw_response.strip()
            if '```json' in json_str:
                json_str = json_str.split('```json')[1].split('```')[0].strip()
            
            # Décodage du JSON
            result = json.loads(json_str)
            
            # Validation de la structure
            required_fields = ['classification', 'score_confidence', 'critères_manquants', 'raison']
            if not all(field in result for field in required_fields):
                raise ValueError("Format de réponse invalide")
            
            # Construction de la réponse standardisée
            return {
                "classification": result['classification'],
                "confidence": float(result['score_confidence']),
                "missing_criteria": result['critères_manquants'],
                "reason": result['raison'],
                "metadata": metadata,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            error_msg = f"Erreur lors du traitement de la réponse du modèle: {str(e)}"
            self.logger.error(f"{error_msg}. Réponse reçue: {raw_response}")
            return self._create_error_response(error_msg, metadata)
    
    def _create_error_response(self, error_msg: str, metadata: Dict) -> Dict:
        """Crée une réponse d'erreur standardisée."""
        return {
            "status": "error",
            "error": error_msg,
            "classification": "ERREUR",
            "confidence": 0.0,
            "missing_criteria": [],
            "reason": "Une erreur est survenue lors de l'analyse du document.",
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }

# Instance du classifieur
classifier = CSPEClassifier()
