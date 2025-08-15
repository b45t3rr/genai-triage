"""Modelos del dominio."""

# Modelos de documento
from .document import DocumentMetadata, PDFDocument

# Modelos de seguridad
from .security import (
    SeverityLevel,
    PriorityLevel,
    Finding,
    Recommendation,
    Credentials,
    TechnicalData,
    AdditionalInfo,
    SecurityReport,
    rebuild_security_models
)

# Modelos de triage
from .triage import (
    EvidenceType,
    RecommendationType,
    ImpactLevel,
    ExploitProbability,
    TriageEvidence,
    TriageRecommendation,
    TriagedVulnerability,
    TriageReport
)

__all__ = [
    # Document models
    "DocumentMetadata",
    "PDFDocument",
    
    # Security models
    "SeverityLevel",
    "PriorityLevel",
    "Finding",
    "Recommendation",
    "Credentials",
    "TechnicalData",
    "AdditionalInfo",
    "SecurityReport",
    
    # Triage models
    "EvidenceType",
    "RecommendationType",
    "ImpactLevel",
    "ExploitProbability",
    "TriageEvidence",
    "TriageRecommendation",
    "TriagedVulnerability",
    "TriageReport"
]

# Rebuild models with forward references after all imports are complete
rebuild_security_models()