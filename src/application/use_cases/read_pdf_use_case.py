"""Caso de uso para lectura y análisis de reportes PDF."""

from typing import Dict, Any
import json
from datetime import datetime

from ...domain.interfaces import DocumentReaderInterface, SecurityAnalyzerInterface
from ...domain.models import SecurityReport
from ...domain.services import SecurityAnalysisService, ReportValidationService


class ReadPDFUseCase:
    """Caso de uso para leer y analizar reportes PDF de seguridad.
    
    Responsabilidades:
    - Leer documentos PDF
    - Analizar contenido de seguridad
    - Validar la calidad del reporte
    - Proporcionar métricas de análisis
    """
    
    def __init__(
        self,
        pdf_reader: DocumentReaderInterface,
        security_analyzer: SecurityAnalyzerInterface,
        analysis_service: SecurityAnalysisService,
        validation_service: ReportValidationService
    ):
        self._pdf_reader = pdf_reader
        self._security_analyzer = security_analyzer
        self._analysis_service = analysis_service
        self._validation_service = validation_service
    
    def execute(self, file_path: str) -> Dict[str, Any]:
        """Ejecuta el caso de uso de lectura y análisis de PDF.
        
        Args:
            file_path: Ruta al archivo PDF
            
        Returns:
            Dict con el reporte de seguridad y métricas de calidad
            
        Raises:
            Exception: Si hay errores en la lectura o análisis
        """
        try:
            # Paso 1: Leer el documento PDF
            pdf_document = self._pdf_reader.read_pdf(file_path)
            
            # Paso 2: Analizar el contenido de seguridad
            security_report = self._security_analyzer.analyze_security_content(pdf_document.content)
            
            # Paso 3: Validar la calidad del reporte
            is_valid, validation_errors = self._validation_service.validate_security_report(security_report)
            
            # Paso 4: Extraer indicadores técnicos
            technical_indicators = self._analysis_service.extract_technical_indicators(security_report)
            
            # Paso 5: Calcular score de cobertura
            coverage_score = self._analysis_service.calculate_testing_coverage_score(security_report)
            
            # Paso 6: Obtener sugerencias de mejora
            improvement_suggestions = self._validation_service.suggest_improvements(security_report)
            
            return {
                "security_report": security_report.model_dump(),
                "quality_metrics": {
                    "is_valid": is_valid,
                    "validation_errors": validation_errors,
                    "validation_score": self._validation_service.get_validation_score(security_report),
                    "coverage_score": coverage_score,
                    "technical_indicators": technical_indicators
                },
                "recommendations": {
                    "improvement_suggestions": improvement_suggestions,
                    "additional_tests": self._analysis_service.suggest_additional_tests(security_report)
                },
                "metadata": {
                    "analysis_date": datetime.now().isoformat(),
                    "file_path": file_path,
                    "document_info": pdf_document.metadata.model_dump() if pdf_document.metadata else None
                }
            }
            
        except Exception as e:
            raise Exception(f"Error procesando el archivo PDF '{file_path}': {str(e)}")
    
    def execute_with_validation_only(self, file_path: str) -> Dict[str, Any]:
        """Ejecuta solo la lectura y validación básica del PDF.
        
        Útil para verificaciones rápidas de formato y estructura.
        """
        try:
            # Leer el documento
            pdf_document = self._pdf_reader.read_pdf(file_path)
            
            # Análisis básico
            security_report = self._security_analyzer.analyze_security_content(pdf_document.content)
            
            # Solo validación
            is_valid, validation_errors = self._validation_service.validate_security_report(security_report)
            
            return {
                "is_valid": is_valid,
                "validation_errors": validation_errors,
                "basic_info": {
                    "title": security_report.documento.titulo,
                    "author": security_report.documento.autor,
                    "findings_count": len(security_report.hallazgos_principales),
                    "recommendations_count": len(security_report.recomendaciones)
                },
                "metadata": {
                    "analysis_date": datetime.now().isoformat(),
                    "file_path": file_path
                }
            }
            
        except Exception as e:
            raise Exception(f"Error validando el archivo PDF '{file_path}': {str(e)}")
    
    def execute_as_json(self, file_path: str, pretty: bool = True) -> str:
        """Ejecuta el caso de uso y retorna el resultado como JSON.
        
        Args:
            file_path: Ruta al archivo PDF
            pretty: Si formatear el JSON de manera legible
            
        Returns:
            String JSON con el resultado del análisis
        """
        result = self.execute(file_path)
        
        if pretty:
            return json.dumps(result, indent=2, ensure_ascii=False, default=str)
        else:
            return json.dumps(result, ensure_ascii=False, default=str)
    
    def get_quick_summary(self, file_path: str) -> Dict[str, Any]:
        """Obtiene un resumen rápido del reporte sin análisis completo.
        
        Útil para dashboards o vistas previas.
        """
        try:
            validation_result = self.execute_with_validation_only(file_path)
            
            return {
                "file_name": file_path.split('/')[-1],
                "is_valid": validation_result["is_valid"],
                "error_count": len(validation_result["validation_errors"]),
                "findings_count": validation_result["basic_info"]["findings_count"],
                "title": validation_result["basic_info"]["title"],
                "author": validation_result["basic_info"]["author"],
                "analysis_date": validation_result["metadata"]["analysis_date"]
            }
            
        except Exception as e:
            return {
                "file_name": file_path.split('/')[-1],
                "is_valid": False,
                "error": str(e),
                "analysis_date": datetime.now().isoformat()
            }