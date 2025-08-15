"""Modelos específicos para el proceso de triage de vulnerabilidades."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from .security import SeverityLevel, PriorityLevel


class EvidenceType(str, Enum):
    """Tipos de evidencia para vulnerabilidades."""
    CODE = "código"
    HTTP_RESPONSE = "respuesta_http"
    FILE = "archivo"
    CONFIGURATION = "configuración"
    DATABASE = "base_datos"


class RecommendationType(str, Enum):
    """Tipos de recomendaciones de triage."""
    IMMEDIATE = "inmediata"
    CORRECTIVE = "correctiva"
    PREVENTIVE = "preventiva"
    MITIGATION = "mitigación"


class ImpactLevel(str, Enum):
    """Niveles de impacto."""
    HIGH = "alto"
    MEDIUM = "medio"
    LOW = "bajo"


class ExploitProbability(str, Enum):
    """Probabilidad de explotación."""
    HIGH = "alta"
    MEDIUM = "media"
    LOW = "baja"


class TriageEvidence(BaseModel):
    """Evidencia específica de una vulnerabilidad para triage."""
    tipo_evidencia: EvidenceType
    descripcion: str
    contenido: str
    ubicacion: Optional[str] = None
    criticidad_evidencia: ImpactLevel


class TriageRecommendation(BaseModel):
    """Recomendación específica de triage con detalles técnicos."""
    tipo: RecommendationType
    descripcion: str
    pasos_implementacion: List[str]
    recursos_necesarios: List[str]
    impacto_implementacion: ImpactLevel


class TriagedVulnerability(BaseModel):
    """Vulnerabilidad procesada por el agente de triage."""
    id_vulnerabilidad: str = Field(default_factory=lambda: f"vuln_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    nombre: str
    descripcion_original: str
    
    # Análisis de severidad basado en evidencia
    severidad_original: str
    severidad_triage: SeverityLevel
    justificacion_severidad: str
    
    # Análisis de prioridad
    prioridad: PriorityLevel
    justificacion_prioridad: str
    
    # Evidencias y análisis
    evidencias: List[TriageEvidence]
    impacto_real: str
    probabilidad_explotacion: ExploitProbability
    
    # Recomendaciones específicas
    recomendaciones: List[TriageRecommendation]
    
    # Metadatos del triage
    fecha_triage: datetime = Field(default_factory=datetime.now)
    confianza_analisis: float = Field(ge=0.0, le=1.0, default=0.8)
    requiere_validacion_manual: bool = False
    notas_adicionales: Optional[str] = None
    
    class Config:
        """Configuración del modelo."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TriageReport(BaseModel):
    """Reporte completo de triage de vulnerabilidades."""
    id_reporte: str = Field(default_factory=lambda: f"triage_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    fecha_generacion: datetime = Field(default_factory=datetime.now)
    reporte_origen: str
    
    # Resumen del triage
    resumen_triage: str
    total_vulnerabilidades: int
    distribucion_severidad: Dict[str, int]
    distribucion_prioridad: Dict[str, int]
    
    # Vulnerabilidades procesadas
    vulnerabilidades: List[TriagedVulnerability]
    
    # Recomendaciones y plan
    recomendaciones_generales: List[str]
    plan_remediacion: List[Dict[str, Any]]
    
    # Evaluación de riesgo general
    riesgo_general: ImpactLevel
    score_riesgo: float = Field(ge=0.0, le=10.0)
    
    # Metadatos del agente
    version_agente: str = "1.0.0"
    configuracion_triage: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Configuración del modelo."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }