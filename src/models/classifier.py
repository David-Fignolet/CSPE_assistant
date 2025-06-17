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
        self._setup_model()
    
    def _setup_model(self):
        """Configure le modèle de classification."""
        # Cette méthode sera implémentée plus tard
        # pour charger le modèle spécifié
        pass
    
    def classifier_document(
        self,
        texte: str,
        document_id: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """
        Classe un document selon les critères CSPE.
        
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
        
        # Simulation de la classification
        # À remplacer par l'appel réel au modèle
        try:
            # Exemple de logique de classification simplifiée
            decision = self._simuler_classification(texte)
            return ClassificationResult(
                decision=decision,
                confiance=0.9,  # Valeur de confiance simulée
                criteres={
                    "delai": {"valide": True, "details": "Délai respecté"},
                    "periode": {"valide": True, "details": "Période 2009-2015"},
                    "prescription": {"valide": True, "details": "Prescription quadriennale respectée"},
                    "repercussion": {"valide": True, "details": "Répercussion client final démontrée"}
                },
                document_id=document_id,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error(f"Erreur lors de la classification: {e}")
            return ClassificationResult(
                decision=Decision.INDETERMINE,
                confiance=0.0,
                criteres={"erreur": {"message": str(e)}},
                document_id=document_id,
                metadata=metadata or {}
            )
    
    def _simuler_classification(self, texte: str) -> Decision:
        """
        Simule la classification d'un document (pour les tests).
        
        Args:
            texte: Contenu textuel du document
            
        Returns:
            Une décision simulée
        """
        texte = texte.lower()
        mots_cles_irrecevable = [
            "irrecevable", "rejet", "refus", "non recevable",
            "hors délai", "périmé", "prescrit", "trop tard"
        ]
        
        if any(mot in texte for mot in mots_cles_irrecevable):
            return Decision.IRRECEVABLE
        
        return Decision.RECEVABLE
