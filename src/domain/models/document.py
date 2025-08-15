"""Modelos relacionados con documentos."""

from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime


class DocumentMetadata(BaseModel):
    """Metadatos básicos de un documento."""
    titulo: str
    fecha: str
    autor: str
    tipo_documento: str
    numero_paginas: int


class PDFDocument(BaseModel):
    """Representa un documento PDF procesado."""
    file_path: str
    content: str
    metadata: Dict[str, Any]
    extracted_at: datetime = datetime.now()
    
    class Config:
        """Configuración del modelo."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }