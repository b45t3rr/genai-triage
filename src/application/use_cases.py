from typing import Dict, Any
import json
from ..domain.interfaces import PDFReaderInterface, ReportAnalyzerInterface
from ..domain.entities import SecurityReport


class ReadPDFReportUseCase:
    """Caso de uso para leer y analizar reportes PDF."""
    
    def __init__(
        self,
        pdf_reader: PDFReaderInterface,
        report_analyzer: ReportAnalyzerInterface
    ):
        self._pdf_reader = pdf_reader
        self._report_analyzer = report_analyzer
    
    def execute(self, file_path: str) -> Dict[str, Any]:
        """Ejecuta el caso de uso completo."""
        try:
            # Leer el PDF
            pdf_document = self._pdf_reader.read_pdf(file_path)
            
            # Analizar el contenido
            security_report = self._report_analyzer.analyze_report(pdf_document.content)
            
            # Convertir a diccionario para serialización JSON
            return security_report.model_dump()
            
        except Exception as e:
            raise Exception(f"Error procesando el archivo PDF: {str(e)}")
    
    def execute_as_json(self, file_path: str) -> str:
        """Ejecuta el caso de uso y retorna JSON formateado."""
        result = self.execute(file_path)
        return json.dumps(result, indent=2, ensure_ascii=False)