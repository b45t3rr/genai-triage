from typing import Dict, Any
import json
from datetime import datetime
from ..domain.interfaces import PDFReaderInterface, ReportAnalyzerInterface, LLMInterface
from ..domain.entities import SecurityReport, TriageReport
from ..infrastructure.agents.triage_agent import TriageAgent


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


class TriageVulnerabilitiesUseCase:
    """Caso de uso para realizar triage de vulnerabilidades."""
    
    def __init__(self, llm: LLMInterface):
        self._llm = llm
        self._triage_agent = TriageAgent(llm)
    
    def execute(self, security_report: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta el análisis de triage sobre un reporte de seguridad."""
        try:
            # Realizar triage usando el agente especializado
            triage_report = self._triage_agent.analyze_vulnerabilities(security_report)
            
            # Convertir a diccionario para serialización JSON
            return triage_report.model_dump()
            
        except Exception as e:
            raise Exception(f"Error realizando triage de vulnerabilidades: {str(e)}")
    
    def execute_as_json(self, security_report: Dict[str, Any]) -> str:
        """Ejecuta el caso de uso y retorna JSON formateado."""
        result = self.execute(security_report)
        return json.dumps(result, indent=2, ensure_ascii=False, default=str)
    
    def execute_and_export(self, security_report: Dict[str, Any], output_path: str) -> str:
        """Ejecuta el triage y exporta el resultado a un archivo."""
        try:
            # Realizar triage
            triage_report = self._triage_agent.analyze_vulnerabilities(security_report)
            
            # Exportar a archivo
            exported_path = self._triage_agent.export_triage_report(triage_report, output_path)
            
            return exported_path
            
        except Exception as e:
            raise Exception(f"Error ejecutando y exportando triage: {str(e)}")


class CompleteSecurityAnalysisUseCase:
    """Caso de uso completo que incluye análisis de PDF y triage."""
    
    def __init__(
        self,
        pdf_reader: PDFReaderInterface,
        report_analyzer: ReportAnalyzerInterface,
        llm: LLMInterface
    ):
        self._pdf_use_case = ReadPDFReportUseCase(pdf_reader, report_analyzer)
        self._triage_use_case = TriageVulnerabilitiesUseCase(llm)
    
    def execute(self, pdf_path: str) -> Dict[str, Any]:
        """Ejecuta análisis completo: PDF + Triage."""
        try:
            # Paso 1: Analizar PDF
            print("📄 Analizando reporte PDF...")
            security_report = self._pdf_use_case.execute(pdf_path)
            
            # Paso 2: Realizar triage
            print("🎯 Realizando triage de vulnerabilidades...")
            triage_report = self._triage_use_case.execute(security_report)
            
            # Combinar resultados
            complete_analysis = {
                "reporte_original": security_report,
                "triage_analysis": triage_report,
                "metadata": {
                    "fecha_analisis_completo": json.dumps(datetime.now(), default=str),
                    "version_pipeline": "1.0.0"
                }
            }
            
            return complete_analysis
            
        except Exception as e:
            raise Exception(f"Error en análisis completo de seguridad: {str(e)}")
    
    def execute_and_export(self, pdf_path: str, output_dir: str) -> Dict[str, str]:
        """Ejecuta análisis completo y exporta ambos reportes."""
        try:
            import os
            from datetime import datetime
            
            # Ejecutar análisis completo
            complete_analysis = self.execute(pdf_path)
            
            # Generar nombres de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_report_path = os.path.join(output_dir, f"security_report_{timestamp}.json")
            triage_report_path = os.path.join(output_dir, f"triage_report_{timestamp}.json")
            complete_report_path = os.path.join(output_dir, f"complete_analysis_{timestamp}.json")
            
            # Crear directorio si no existe
            os.makedirs(output_dir, exist_ok=True)
            
            # Exportar reporte original
            with open(original_report_path, 'w', encoding='utf-8') as f:
                json.dump(complete_analysis["reporte_original"], f, indent=2, ensure_ascii=False, default=str)
            
            # Exportar reporte de triage
            with open(triage_report_path, 'w', encoding='utf-8') as f:
                json.dump(complete_analysis["triage_analysis"], f, indent=2, ensure_ascii=False, default=str)
            
            # Exportar análisis completo
            with open(complete_report_path, 'w', encoding='utf-8') as f:
                json.dump(complete_analysis, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"📊 Análisis completo exportado:")
            print(f"   - Reporte original: {original_report_path}")
            print(f"   - Reporte de triage: {triage_report_path}")
            print(f"   - Análisis completo: {complete_report_path}")
            
            return {
                "original_report": original_report_path,
                "triage_report": triage_report_path,
                "complete_analysis": complete_report_path
            }
            
        except Exception as e:
            raise Exception(f"Error exportando análisis completo: {str(e)}")