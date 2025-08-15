"""Entidades del dominio - Archivo de compatibilidad.

Este archivo mantiene las importaciones para compatibilidad con código existente.
Los modelos han sido reorganizados en el paquete models/ para mejor organización.
"""

# Importaciones desde los nuevos modelos organizados
from .models import (
    # Modelos de documento
    DocumentMetadata as DocumentInfo,  # Alias para compatibilidad
    PDFDocument,
    
    # Modelos de seguridad
    Finding,
    Recommendation,
    Credentials,
    TechnicalData,
    AdditionalInfo,
    SecurityReport,
    
    # Modelos de triage
    TriageEvidence,
    TriageRecommendation,
    TriagedVulnerability,
    TriageReport,
    
    # Enums para mejor tipado
    SeverityLevel,
    PriorityLevel,
    EvidenceType,
    RecommendationType,
    ImpactLevel,
    ExploitProbability
)

# Re-exportar todo para mantener compatibilidad
__all__ = [
    "DocumentInfo",  # Alias de DocumentMetadata
    "PDFDocument",
    "Finding",
    "Recommendation",
    "Credentials",
    "TechnicalData",
    "AdditionalInfo",
    "SecurityReport",
    "TriageEvidence",
    "TriageRecommendation",
    "TriagedVulnerability",
    "TriageReport",
    "SeverityLevel",
    "PriorityLevel",
    "EvidenceType",
    "RecommendationType",
    "ImpactLevel",
    "ExploitProbability"
]