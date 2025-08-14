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