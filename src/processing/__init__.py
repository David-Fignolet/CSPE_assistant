"""
Module de traitement des documents CSPE.

Ce module fournit des fonctionnalités pour extraire et traiter les informations
des documents liés à la Contribution au Service Public de l'Électricité (CSPE).
"""

from .document_processor import CSPEDocumentProcessor, CSPEEntity

__all__ = ['CSPEDocumentProcessor', 'CSPEEntity']
