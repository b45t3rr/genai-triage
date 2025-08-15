"""Modelos relacionados con seguridad y vulnerabilidades."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    """Niveles de severidad estandarizados."""
    CRITICAL = "crítica"
    HIGH = "alta"
    MEDIUM = "media"
    LOW = "baja"
    INFO = "informativa"


class PriorityLevel(str, Enum):
    """Niveles de prioridad para remediación."""
    P0 = "P0"  # Crítico - < 24h
    P1 = "P1"  # Alto - < 1 semana
    P2 = "P2"  # Medio - < 1 mes
    P3 = "P3"  # Bajo - < 3 meses
    P4 = "P4"  # Informativo


class Finding(BaseModel):
    """Representa un hallazgo de seguridad básico."""
    nombre: str
    categoria: str
    descripcion: str
    severidad: str
    impacto: str
    detailed_proof_of_concept: Optional[str] = None


class Recommendation(BaseModel):
    """Representa una recomendación de seguridad."""
    prioridad: str
    accion: str
    descripcion: str


class Credentials(BaseModel):
    """Credenciales utilizadas en las pruebas."""
    usuario: str
    contrasena: str


class TechnicalData(BaseModel):
    """Datos técnicos del análisis."""
    entorno: str
    endpoints_pruebas: List[str]
    credenciales_utilizadas: Dict[str, Credentials]
    observaciones_abiertas: List[str]


class AdditionalInfo(BaseModel):
    """Información adicional del reporte."""
    nota: str
    recomendaciones_adicionales: List[str]


class SecurityReport(BaseModel):
    """Modelo principal del reporte de seguridad."""
    documento: 'DocumentMetadata'  # Forward reference
    resumen_ejecutivo: str
    hallazgos_principales: List[Finding]
    recomendaciones: List[Recommendation]
    datos_tecnicos: TechnicalData
    conclusiones: str
    informacion_adicional: AdditionalInfo
    
    class Config:
        """Configuración del modelo."""
        use_enum_values = True


# Rebuild model after DocumentMetadata is imported
# This is needed because SecurityReport uses a forward reference to DocumentMetadata
def rebuild_security_models():
    """Rebuild models with forward references after all models are loaded."""
    from .document import DocumentMetadata
    # Add DocumentMetadata to the global namespace for the rebuild
    globals()['DocumentMetadata'] = DocumentMetadata
    SecurityReport.model_rebuild()