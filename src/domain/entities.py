from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class DocumentInfo(BaseModel):
    """Información básica del documento."""
    titulo: str
    fecha: str
    autor: str
    tipo_documento: str
    numero_paginas: int


class Finding(BaseModel):
    """Representa un hallazgo de seguridad."""
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
    documento: DocumentInfo
    resumen_ejecutivo: str
    hallazgos_principales: List[Finding]
    recomendaciones: List[Recommendation]
    datos_tecnicos: TechnicalData
    conclusiones: str
    informacion_adicional: AdditionalInfo


class PDFDocument(BaseModel):
    """Representa un documento PDF."""
    file_path: str
    content: str
    metadata: Dict[str, Any]


class TriageEvidence(BaseModel):
    """Evidencia específica de una vulnerabilidad para triage."""
    tipo_evidencia: str  # "código", "respuesta_http", "archivo", "configuración", etc.
    descripcion: str
    contenido: str
    ubicacion: Optional[str] = None  # archivo, línea, endpoint, etc.
    criticidad_evidencia: str  # "alta", "media", "baja"


class TriageRecommendation(BaseModel):
    """Recomendación específica de triage con detalles técnicos."""
    tipo: str  # "inmediata", "correctiva", "preventiva", "mitigación"
    descripcion: str
    pasos_implementacion: List[str]
    recursos_necesarios: List[str]
    impacto_implementacion: str  # "alto", "medio", "bajo"


class TriagedVulnerability(BaseModel):
    """Vulnerabilidad procesada por el agente de triage."""
    id_vulnerabilidad: str
    nombre: str
    descripcion_original: str
    
    # Análisis de severidad basado en evidencia
    severidad_original: str
    severidad_triage: str  # "crítica", "alta", "media", "baja", "informativa"
    justificacion_severidad: str
    
    # Análisis de prioridad
    prioridad: str  # "P0", "P1", "P2", "P3", "P4"
    justificacion_prioridad: str
    
    # Evidencia analizada
    evidencias: List[TriageEvidence]
    impacto_real: str
    probabilidad_explotacion: str  # "alta", "media", "baja"
    
    # Recomendaciones específicas
    recomendaciones: List[TriageRecommendation]
    
    # Metadatos del triage
    fecha_triage: datetime
    confianza_analisis: float  # 0.0 a 1.0
    requiere_validacion_manual: bool
    notas_adicionales: Optional[str] = None


class TriageReport(BaseModel):
    """Reporte completo del análisis de triage."""
    id_reporte: str
    fecha_generacion: datetime
    reporte_origen: str  # referencia al reporte original
    
    # Resumen ejecutivo del triage
    resumen_triage: str
    total_vulnerabilidades: int
    distribucion_severidad: Dict[str, int]  # {"crítica": 2, "alta": 5, ...}
    distribucion_prioridad: Dict[str, int]  # {"P0": 1, "P1": 3, ...}
    
    # Vulnerabilidades triageadas
    vulnerabilidades: List[TriagedVulnerability]
    
    # Recomendaciones generales
    recomendaciones_generales: List[str]
    plan_remediacion: List[Dict[str, Any]]  # Plan ordenado por prioridad
    
    # Métricas del triage
    riesgo_general: str  # "crítico", "alto", "medio", "bajo"
    score_riesgo: float  # 0.0 a 10.0
    
    # Metadatos
    version_agente: str
    configuracion_triage: Dict[str, Any]