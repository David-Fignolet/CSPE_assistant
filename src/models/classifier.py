"""
Module de classification des documents CSPE.

Ce module contient la classe CSPEClassifier qui permet de classifier les documents
selon les critères de la Contribution au Service Public de l'Électricité (CSPE).
"""

import json
import logging
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Union
from enum import Enum, auto
import ollama  # Import du client Ollama

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Decision(str, Enum):
    """Énumération des décisions possibles."""
    RECEVABLE = "recevable"
    IRRECEVABLE = "irrecevable"
    INDETERMINE = "indéterminé"
    A_COMPLETER = "à compléter"

@dataclass
class ClassificationResult:
    """Résultat de la classification d'un document."""
    decision: Decision
    confiance: float
    criteres: Dict[str, Dict[str, Any]]
    document_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        result = asdict(self)
        result['decision'] = self.decision.value
        return result
    
    def to_json(self) -> str:
        """Sérialise l'objet en JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

class CSPEClassifier:
    """
    Classe principale pour la classification des documents CSPE.
    
    Cette classe utilise un modèle de langage pour analyser les documents
    et déterminer s'ils sont recevables ou non selon les critères CSPE.
    """
    
    def __init__(self, model_name: str = "mistral:7b"):
        """
        Initialise le classifieur.
        
        Args:
            model_name: Nom du modèle à utiliser (par défaut: "mistral:7b")
        """
        self.model_name = model_name
        self.llm = None
        self._setup_model()
    
    def _setup_model(self):
        """Configure le modèle de classification avec Ollama."""
        try:
            # Vérifier que le modèle est disponible
            models = ollama.list()
            model_names = [m['name'] for m in models.get('models', [])]
            
            if self.model_name not in model_names:
                logger.info(f"Modèle {self.model_name} non trouvé, tentative de téléchargement...")
                ollama.pull(self.model_name)
            
            self.llm = ollama
            logger.info(f"Modèle {self.model_name} chargé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle {self.model_name}: {str(e)}")
            raise RuntimeError(f"Impossible de charger le modèle: {str(e)}")
    
    def _generate_prompt(self, texte: str) -> str:
        """Génère le prompt pour l'analyse du document."""
        return f"""
        Vous êtes un expert juridique spécialisé dans l'analyse des dossiers de contestation de la CSPE (Contribution au Service Public de l'Électricité).
        
        Veuillez analyser le document suivant et déterminer s'il est recevable ou irrecevable selon les critères suivants :
        1. Le délai de réclamation (avant le 31/12/N+1)
        2. La période couverte (entre 2009 et 2015)
        3. La prescription quadriennale
        4. La répercussion sur le client final
        
        Document à analyser :
        {texte}
        
        Répondez au format JSON avec la structure suivante :
        {{
            "decision": "recevable" | "irrecevable" | "à compléter",
            "confiance": nombre_entre_0_et_1,
            "raisonnement": "Explication détaillée de la décision",
            "criteres": {{
                "delai_reclamation": {{
                    "verdict": "respecté" | "non_respecté" | "indéterminé",
                    "explication": "..."
                }},
                "periode_couverte": {{
                    "verdict": "respecté" | "non_respecté" | "indéterminé",
                    "explication": "..."
                }},
                "prescription_quadriennale": {{
                    "verdict": "respecté" | "non_respecté" | "indéterminé",
                    "explication": "..."
                }},
                "repercussion_client_final": {{
                    "verdict": "respecté" | "non_respecté" | "indéterminé",
                    "explication": "..."
                }}
            }}
        }}
        """
    
    def classify(
        self,
        texte: str,
        document_id: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """
        Classe un document selon les critères CSPE en utilisant le LLM.
        
        Args:
            texte: Contenu textuel du document à classifier
            document_id: Identifiant unique du document (optionnel)
            metadata: Métadonnées supplémentaires (optionnel)
            
        Returns:
            Un objet ClassificationResult contenant la décision et les détails
        """
        if not texte or not texte.strip():
            return ClassificationResult(
                decision=Decision.INDETERMINE,
                confiance=0.0,
                criteres={"erreur": {"message": "Document vide"}},
                document_id=document_id,
                metadata=metadata or {}
            )
        
        try:
            # Générer le prompt
            prompt = self._generate_prompt(texte)
            
            # Appeler le modèle
            response = self.llm.generate(
                model=self.model_name,
                prompt=prompt,
                format="json",
                options={"temperature": 0.2}
            )
            
            # Parser la réponse
            result = json.loads(response['response'])
            
            # Convertir la décision en énumération
            decision_map = {
                "recevable": Decision.RECEVABLE,
                "irrecevable": Decision.IRRECEVABLE,
                "à compléter": Decision.A_COMPLETER,
                "indéterminé": Decision.INDETERMINE
            }
            
            decision = decision_map.get(
                result.get("decision", "").lower(),
                Decision.INDETERMINE
            )
            
            # Créer le résultat de classification
            return ClassificationResult(
                decision=decision,
                confiance=float(result.get("confiance", 0.5)),
                criteres=result.get("criteres", {}),
                document_id=document_id,
                metadata=metadata or {}
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de décodage JSON de la réponse du modèle: {str(e)}")
            return self._fallback_classification(texte, document_id, metadata)
            
        except Exception as e:
            logger.error(f"Erreur lors de la classification: {str(e)}")
            return self._fallback_classification(texte, document_id, metadata)
    
    def _fallback_classification(
        self,
        texte: str,
        document_id: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """Méthode de secours en cas d'échec de la classification LLM."""
        # Logique de secours basée sur des mots-clés
        texte = texte.lower()
        mots_cles_irrecevable = [
            "irrecevable", "rejet", "refus", "non recevable",
            "hors délai", "périmé", "prescrit", "trop tard"
        ]
        
        if any(mot in texte for mot in mots_cles_irrecevable):
            decision = Decision.IRRECEVABLE
            confiance = 0.8
        else:
            decision = Decision.INDETERMINE
            confiance = 0.5
            
        return ClassificationResult(
            decision=decision,
            confiance=confiance,
            criteres={
                "fallback": {
                    "message": "Classification de secours utilisée",
                    "details": "Le modèle LLM n'a pas pu être utilisé"
                }
            },
            document_id=document_id,
            metadata=metadata or {}
        )
