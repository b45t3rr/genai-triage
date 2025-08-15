"""Interfaces del dominio siguiendo el principio de segregación de interfaces.

Cada interface tiene una responsabilidad específica y bien definida.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from .models import PDFDocument, SecurityReport, TriageReport


# === INTERFACES PARA LECTURA DE DOCUMENTOS ===

class DocumentReaderInterface(ABC):
    """Interface base para lectores de documentos."""
    
    @abstractmethod
    def can_read(self, file_path: str) -> bool:
        """Verifica si puede leer el tipo de archivo."""
        pass
    
    @abstractmethod
    def read_document(self, file_path: str) -> Dict[str, Any]:
        """Lee un documento y retorna su contenido estructurado."""
        pass


class PDFReaderInterface(DocumentReaderInterface):
    """Interface específica para leer documentos PDF."""
    
    @abstractmethod
    def read_pdf(self, file_path: str) -> PDFDocument:
        """Lee un archivo PDF y retorna su contenido estructurado."""
        pass


# === INTERFACES PARA ANÁLISIS ===

class SecurityAnalyzerInterface(ABC):
    """Interface para análisis de seguridad."""
    
    @abstractmethod
    def analyze_content(self, content: str) -> SecurityReport:
        """Analiza contenido y genera un reporte de seguridad."""
        pass


class TriageAnalyzerInterface(ABC):
    """Interface para análisis de triage de vulnerabilidades."""
    
    @abstractmethod
    def analyze_vulnerabilities(self, security_report: Dict[str, Any]) -> TriageReport:
        """Realiza triage de vulnerabilidades y genera reporte especializado."""
        pass


# === INTERFACES PARA LLM ===

class LLMInterface(ABC):
    """Interface base para modelos de lenguaje."""
    
    @abstractmethod
    def generate_response(self, prompt: str, content: str = "") -> str:
        """Genera una respuesta basada en el prompt y contenido opcional."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Verifica si el LLM está disponible para uso."""
        pass


class StructuredLLMInterface(LLMInterface):
    """Interface para LLMs que pueden generar respuestas estructuradas."""
    
    @abstractmethod
    def generate_structured_response(self, prompt: str, content: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Genera una respuesta estructurada siguiendo un schema específico."""
        pass


# === INTERFACES PARA PERSISTENCIA ===

class ReportRepositoryInterface(ABC):
    """Interface para persistencia de reportes."""
    
    @abstractmethod
    def save_security_report(self, report: SecurityReport) -> str:
        """Guarda un reporte de seguridad y retorna su ID."""
        pass
    
    @abstractmethod
    def save_triage_report(self, report: TriageReport) -> str:
        """Guarda un reporte de triage y retorna su ID."""
        pass
    
    @abstractmethod
    def get_report_by_id(self, report_id: str) -> Dict[str, Any]:
        """Obtiene un reporte por su ID."""
        pass


# === INTERFACES PARA EXPORTACIÓN ===

class ReportExporterInterface(ABC):
    """Interface para exportar reportes en diferentes formatos."""
    
    @abstractmethod
    def export_to_json(self, report: Dict[str, Any], file_path: str) -> str:
        """Exporta un reporte a formato JSON."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Retorna los formatos de exportación soportados."""
        pass