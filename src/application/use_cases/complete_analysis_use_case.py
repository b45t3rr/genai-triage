"""Caso de uso para análisis completo de seguridad."""

from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime
from pathlib import Path

from ...domain.interfaces import ReportExporterInterface
from .read_pdf_use_case import ReadPDFUseCase
from .triage_vulnerabilities_use_case import TriageVulnerabilitiesUseCase


class CompleteSecurityAnalysisUseCase:
    """Caso de uso para análisis completo de seguridad.
    
    Responsabilidades:
    - Orquestar el flujo completo de análisis
    - Coordinar lectura de PDF y triage
    - Generar reportes consolidados
    - Manejar exportación de resultados
    """
    
    def __init__(
        self,
        pdf_use_case: ReadPDFUseCase,
        triage_use_case: TriageVulnerabilitiesUseCase,
        report_exporter: Optional[ReportExporterInterface] = None
    ):
        self._pdf_use_case = pdf_use_case
        self._triage_use_case = triage_use_case
        self._report_exporter = report_exporter
    
    def execute(self, pdf_path: str, include_suggestions: bool = True) -> Dict[str, Any]:
        """Ejecuta análisis completo: PDF + Triage.
        
        Args:
            pdf_path: Ruta al archivo PDF
            include_suggestions: Si incluir sugerencias de mejora
            
        Returns:
            Dict con análisis completo consolidado
            
        Raises:
            Exception: Si hay errores en cualquier paso del análisis
        """
        analysis_start_time = datetime.now()
        
        try:
            # Paso 1: Analizar PDF
            print("📄 Analizando reporte PDF...")
            pdf_analysis = self._pdf_use_case.execute(pdf_path)
            
            # Paso 2: Realizar triage de vulnerabilidades
            print("🎯 Realizando triage de vulnerabilidades...")
            triage_analysis = self._triage_use_case.execute(pdf_analysis["security_report"])
            
            # Paso 3: Consolidar resultados
            print("📊 Consolidando análisis...")
            complete_analysis = self._consolidate_analysis(
                pdf_analysis, 
                triage_analysis, 
                analysis_start_time,
                include_suggestions
            )
            
            print("✅ Análisis completo finalizado")
            return complete_analysis
            
        except Exception as e:
            raise Exception(f"Error en análisis completo de seguridad: {str(e)}")
    
    def execute_with_export(
        self, 
        pdf_path: str, 
        output_dir: str, 
        export_format: str = "json"
    ) -> Dict[str, Any]:
        """Ejecuta análisis completo y exporta los resultados.
        
        Args:
            pdf_path: Ruta al archivo PDF
            output_dir: Directorio de salida
            export_format: Formato de exportación (json, html, pdf)
            
        Returns:
            Dict con rutas de archivos exportados y resumen
        """
        try:
            # Ejecutar análisis completo
            complete_analysis = self.execute(pdf_path)
            
            # Exportar resultados
            export_paths = self._export_analysis_results(
                complete_analysis, 
                output_dir, 
                pdf_path,
                export_format
            )
            
            return {
                "analysis_summary": self._get_analysis_summary(complete_analysis),
                "export_paths": export_paths,
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "export_format": export_format,
                    "output_directory": output_dir
                }
            }
            
        except Exception as e:
            raise Exception(f"Error exportando análisis completo: {str(e)}")
    
    def execute_quick_analysis(self, pdf_path: str) -> Dict[str, Any]:
        """Ejecuta un análisis rápido sin triage completo.
        
        Útil para evaluaciones preliminares o cuando se necesita velocidad.
        """
        try:
            # Solo análisis básico de PDF
            pdf_summary = self._pdf_use_case.get_quick_summary(pdf_path)
            
            # Triage básico solo si el PDF es válido
            triage_summary = None
            if pdf_summary.get("is_valid", False):
                try:
                    # Obtener reporte completo para triage
                    pdf_analysis = self._pdf_use_case.execute_with_validation_only(pdf_path)
                    if pdf_analysis["is_valid"]:
                        # Ejecutar análisis completo para obtener el security_report
                        full_pdf_analysis = self._pdf_use_case.execute(pdf_path)
                        triage_summary = self._triage_use_case.get_triage_summary(
                            full_pdf_analysis["security_report"]
                        )
                except Exception:
                    # Si falla el triage, continuar solo con PDF
                    triage_summary = {"error": "No se pudo realizar triage rápido"}
            
            return {
                "pdf_summary": pdf_summary,
                "triage_summary": triage_summary,
                "analysis_type": "quick",
                "metadata": {
                    "analysis_date": datetime.now().isoformat(),
                    "file_path": pdf_path
                }
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "analysis_type": "quick",
                "metadata": {
                    "analysis_date": datetime.now().isoformat(),
                    "file_path": pdf_path
                }
            }
    
    def _consolidate_analysis(
        self, 
        pdf_analysis: Dict[str, Any], 
        triage_analysis: Dict[str, Any],
        start_time: datetime,
        include_suggestions: bool
    ) -> Dict[str, Any]:
        """Consolida los resultados de PDF y triage en un análisis unificado."""
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Extraer métricas clave
        pdf_metrics = pdf_analysis.get("quality_metrics", {})
        triage_metrics = triage_analysis.get("quality_metrics", {})
        risk_analysis = triage_analysis.get("risk_analysis", {})
        
        # Consolidar métricas de calidad
        consolidated_quality = {
            "pdf_analysis": {
                "is_valid": pdf_metrics.get("is_valid", False),
                "validation_score": pdf_metrics.get("validation_score", 0.0),
                "coverage_score": pdf_metrics.get("coverage_score", 0.0),
                "validation_errors": len(pdf_metrics.get("validation_errors", []))
            },
            "triage_analysis": {
                "is_valid": triage_metrics.get("is_valid", False),
                "total_vulnerabilities": triage_metrics.get("total_vulnerabilities", 0),
                "avg_severity_score": triage_metrics.get("avg_severity_score", 0.0),
                "avg_confidence_score": triage_metrics.get("avg_confidence_score", 0.0)
            },
            "overall_quality_score": self._calculate_overall_quality_score(pdf_metrics, triage_metrics)
        }
        
        # Estructura del análisis consolidado
        consolidated = {
            "executive_summary": self._generate_executive_summary(pdf_analysis, triage_analysis),
            "detailed_analysis": {
                "security_report": pdf_analysis["security_report"],
                "triage_report": triage_analysis["triage_report"]
            },
            "quality_assessment": consolidated_quality,
            "risk_assessment": risk_analysis,
            "metadata": {
                "analysis_date": end_time.isoformat(),
                "processing_time_seconds": round(processing_time, 2),
                "pipeline_version": "2.0.0",
                "analysis_type": "complete"
            }
        }
        
        # Agregar recomendaciones si se solicita
        if include_suggestions:
            consolidated["recommendations"] = {
                "pdf_improvements": pdf_analysis.get("recommendations", {}),
                "security_priorities": self._generate_security_priorities(triage_analysis),
                "next_steps": self._generate_next_steps(pdf_analysis, triage_analysis)
            }
        
        return consolidated
    
    def _generate_executive_summary(self, pdf_analysis: Dict[str, Any], triage_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un resumen ejecutivo del análisis."""
        security_report = pdf_analysis["security_report"]
        triage_report = triage_analysis["triage_report"]
        risk_analysis = triage_analysis.get("risk_analysis", {})
        
        return {
            "document_title": security_report["documento"]["titulo"],
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_findings": len(security_report["hallazgos_principales"]),
            "critical_vulnerabilities": risk_analysis.get("critical_vulnerabilities", 0),
            "overall_risk_score": risk_analysis.get("overall_risk_score", 0.0),
            "avg_confidence": risk_analysis.get("avg_confidence_score", 0.0),
            "severity_breakdown": risk_analysis.get("severity_distribution", {}),
            "key_recommendations_count": len(triage_report.get("vulnerabilities", [])),
            "quality_indicators": {
                "pdf_valid": pdf_analysis["quality_metrics"]["is_valid"],
                "triage_valid": triage_analysis["quality_metrics"]["is_valid"],
                "coverage_score": pdf_analysis["quality_metrics"].get("coverage_score", 0.0)
            }
        }
    
    def _calculate_overall_quality_score(self, pdf_metrics: Dict[str, Any], triage_metrics: Dict[str, Any]) -> float:
        """Calcula un score general de calidad del análisis."""
        pdf_score = pdf_metrics.get("validation_score", 0.0) * 0.4
        coverage_score = pdf_metrics.get("coverage_score", 0.0) * 0.3
        confidence_score = triage_metrics.get("avg_confidence_score", 0.0) * 10 * 0.3  # Convertir a escala 0-10
        
        return round(pdf_score + coverage_score + confidence_score, 2)
    
    def _generate_security_priorities(self, triage_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Genera prioridades de seguridad basadas en el triage."""
        vulnerabilities = triage_analysis["triage_report"].get("vulnerabilities", [])
        
        # Ordenar por severidad y confianza
        sorted_vulns = sorted(
            vulnerabilities,
            key=lambda v: (v["analysis"]["severity_score"], v["analysis"]["confidence_score"]),
            reverse=True
        )
        
        priorities = []
        for i, vuln in enumerate(sorted_vulns[:5]):  # Top 5 prioridades
            priorities.append({
                "rank": i + 1,
                "vulnerability": vuln["original_finding"]["nombre"],
                "severity": vuln["analysis"]["final_severity"],
                "priority": vuln["analysis"]["final_priority"],
                "confidence": vuln["analysis"]["confidence_score"],
                "key_recommendation": vuln["recommendations"][0]["description"] if vuln["recommendations"] else "No disponible"
            })
        
        return priorities
    
    def _generate_next_steps(self, pdf_analysis: Dict[str, Any], triage_analysis: Dict[str, Any]) -> List[str]:
        """Genera pasos siguientes recomendados."""
        next_steps = []
        
        # Basado en calidad del PDF
        if not pdf_analysis["quality_metrics"]["is_valid"]:
            next_steps.append("Revisar y corregir errores en el reporte original")
        
        # Basado en cobertura
        coverage_score = pdf_analysis["quality_metrics"].get("coverage_score", 0.0)
        if coverage_score < 7.0:
            next_steps.append("Ampliar el alcance de las pruebas de seguridad")
        
        # Basado en vulnerabilidades críticas
        critical_count = triage_analysis["risk_analysis"].get("critical_vulnerabilities", 0)
        if critical_count > 0:
            next_steps.append(f"Remediar inmediatamente {critical_count} vulnerabilidades críticas")
        
        # Basado en confianza promedio
        avg_confidence = triage_analysis["risk_analysis"].get("avg_confidence_score", 0.0)
        if avg_confidence < 0.7:
            next_steps.append("Realizar validación adicional de vulnerabilidades con baja confianza")
        
        # Sugerencias adicionales del análisis de PDF
        additional_tests = pdf_analysis.get("recommendations", {}).get("additional_tests", [])
        if additional_tests:
            next_steps.append(f"Considerar {len(additional_tests)} tipos de pruebas adicionales identificadas")
        
        return next_steps
    
    def _export_analysis_results(
        self, 
        complete_analysis: Dict[str, Any], 
        output_dir: str, 
        original_pdf_path: str,
        export_format: str
    ) -> Dict[str, str]:
        """Exporta los resultados del análisis en el formato especificado."""
        # Crear directorio de salida
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generar timestamp para nombres únicos
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(original_pdf_path).stem
        
        export_paths = {}
        
        if export_format.lower() in ["json", "all"]:
            # Exportar análisis completo
            complete_path = os.path.join(output_dir, f"{base_name}_complete_analysis_{timestamp}.json")
            with open(complete_path, 'w', encoding='utf-8') as f:
                json.dump(complete_analysis, f, indent=2, ensure_ascii=False, default=str)
            export_paths["complete_analysis"] = complete_path
            
            # Exportar solo resumen ejecutivo
            summary_path = os.path.join(output_dir, f"{base_name}_executive_summary_{timestamp}.json")
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(complete_analysis["executive_summary"], f, indent=2, ensure_ascii=False, default=str)
            export_paths["executive_summary"] = summary_path
        
        # Si hay un exportador disponible, usarlo para otros formatos
        if self._report_exporter and export_format.lower() in ["html", "pdf", "all"]:
            try:
                additional_exports = self._report_exporter.export_complete_analysis(
                    complete_analysis, output_dir, base_name, timestamp
                )
                export_paths.update(additional_exports)
            except Exception as e:
                print(f"⚠️  Advertencia: No se pudo exportar en formato {export_format}: {str(e)}")
        
        return export_paths
    
    def _get_analysis_summary(self, complete_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae un resumen del análisis para respuesta rápida."""
        exec_summary = complete_analysis["executive_summary"]
        quality = complete_analysis["quality_assessment"]
        
        return {
            "document_title": exec_summary["document_title"],
            "total_findings": exec_summary["total_findings"],
            "critical_vulnerabilities": exec_summary["critical_vulnerabilities"],
            "overall_risk_score": exec_summary["overall_risk_score"],
            "overall_quality_score": quality["overall_quality_score"],
            "analysis_valid": quality["pdf_analysis"]["is_valid"] and quality["triage_analysis"]["is_valid"],
            "processing_time": complete_analysis["metadata"]["processing_time_seconds"]
        }