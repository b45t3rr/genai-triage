from abc import ABC, abstractmethod
from typing import Optional
from .entities import PDFDocument, SecurityReport


class PDFReaderInterface(ABC):
    """Interface para leer documentos PDF."""
    
    @abstractmethod
    def read_pdf(self, file_path: str) -> PDFDocument:
        """Lee un archivo PDF y retorna su contenido."""
        pass


class ReportAnalyzerInterface(ABC):
    """Interface para analizar reportes de seguridad."""
    
    @abstractmethod
    def analyze_report(self, pdf_content: str) -> SecurityReport:
        """Analiza el contenido de un PDF y genera un reporte estructurado."""
        pass


class LLMInterface(ABC):
    """Interface para interactuar con modelos de lenguaje."""
    
    @abstractmethod
    def generate_response(self, prompt: str, content: str) -> str:
        """Genera una respuesta basada en el prompt y contenido."""
        pass