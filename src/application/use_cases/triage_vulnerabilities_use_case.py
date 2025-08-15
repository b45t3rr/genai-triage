"""Caso de uso para triage de vulnerabilidades."""

from typing import Dict, Any, List
import json
from datetime import datetime

from ...domain.interfaces import TriageAnalyzerInterface, ReportRepositoryInterface
from ...domain.models import SecurityReport, TriageReport, TriagedVulnerability
from ...domain.services import TriageService, ReportValidationService


class TriageVulnerabilitiesUseCase:
    """Caso de uso para realizar triage de vulnerabilidades.
    
    Responsabilidades:
    - Analizar vulnerabilidades con IA
    - Aplicar lógica de negocio de triage
    - Validar resultados del triage
    - Generar reportes de triage
    """
    
    def __init__(
        self,
        triage_analyzer: TriageAnalyzerInterface,
        triage_service: TriageService,
        validation_service: ReportValidationService,
        repository: ReportRepositoryInterface = None
    ):
        self._triage_analyzer = triage_analyzer
        self._triage_service = triage_service
        self._validation_service = validation_service
        self._repository = repository
    
    def execute(self, security_report: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta el análisis de triage sobre un reporte de seguridad.
        
        Args:
            security_report: Diccionario con el reporte de seguridad
            
        Returns:
            Dict con el reporte de triage y métricas
            
        Raises:
            Exception: Si hay errores en el análisis de triage
        """
        try:
            # Paso 1: Convertir a modelo de dominio si es necesario
            if isinstance(security_report, dict):
                security_report_obj = SecurityReport.model_validate(security_report)
            else:
                security_report_obj = security_report
            
            # Paso 2: Realizar análisis de triage con IA
            triage_report = self._triage_analyzer.analyze_vulnerabilities(security_report_obj)
            
            # Paso 3: Aplicar lógica de negocio adicional
            enhanced_vulnerabilities = []
            for vuln in triage_report.vulnerabilities:
                enhanced_vuln = self._enhance_vulnerability_analysis(vuln)
                enhanced_vulnerabilities.append(enhanced_vuln)
            
            # Paso 4: Recalcular resumen con lógica de negocio
            updated_summary = self._triage_service.calculate_summary_statistics(enhanced_vulnerabilities)
            
            # Paso 5: Crear reporte final
            final_triage_report = TriageReport(
                vulnerabilities=enhanced_vulnerabilities,
                summary=updated_summary,
                metadata=triage_report.metadata
            )
            
            # Paso 6: Validar el reporte de triage
            is_valid, validation_errors = self._validation_service.validate_triage_report(final_triage_report)
            
            # Paso 7: Calcular métricas adicionales
            risk_metrics = self._calculate_risk_metrics(enhanced_vulnerabilities)
            
            result = {
                "triage_report": final_triage_report.model_dump(),
                "quality_metrics": {
                    "is_valid": is_valid,
                    "validation_errors": validation_errors,
                    "total_vulnerabilities": len(enhanced_vulnerabilities),
                    "avg_severity_score": risk_metrics["avg_severity_score"],
                    "avg_confidence_score": risk_metrics["avg_confidence_score"]
                },
                "risk_analysis": risk_metrics,
                "metadata": {
                    "triage_date": datetime.now().isoformat(),
                    "processing_time_seconds": None  # Se puede agregar medición de tiempo
                }
            }
            
            # Paso 8: Guardar en repositorio si está disponible
            if self._repository:
                self._repository.save_triage_report(final_triage_report)
            
            return result
            
        except Exception as e:
            raise Exception(f"Error realizando triage de vulnerabilidades: {str(e)}")
    
    def execute_for_specific_vulnerabilities(
        self, 
        security_report: Dict[str, Any], 
        vulnerability_indices: List[int]
    ) -> Dict[str, Any]:
        """Ejecuta triage solo para vulnerabilidades específicas.
        
        Args:
            security_report: Reporte de seguridad
            vulnerability_indices: Índices de las vulnerabilidades a analizar
            
        Returns:
            Dict con el triage de las vulnerabilidades seleccionadas
        """
        try:
            # Filtrar vulnerabilidades específicas
            if isinstance(security_report, dict):
                security_report_obj = SecurityReport.model_validate(security_report)
            else:
                security_report_obj = security_report
            
            selected_findings = []
            for idx in vulnerability_indices:
                if 0 <= idx < len(security_report_obj.hallazgos_principales):
                    selected_findings.append(security_report_obj.hallazgos_principales[idx])
            
            if not selected_findings:
                raise ValueError("No se encontraron vulnerabilidades válidas con los índices proporcionados")
            
            # Crear reporte temporal con solo las vulnerabilidades seleccionadas
            temp_report = SecurityReport(
                documento=security_report_obj.documento,
                hallazgos_principales=selected_findings,
                recomendaciones=security_report_obj.recomendaciones,
                datos_tecnicos=security_report_obj.datos_tecnicos,
                informacion_adicional=security_report_obj.informacion_adicional
            )
            
            # Ejecutar triage normal
            return self.execute(temp_report.model_dump())
            
        except Exception as e:
            raise Exception(f"Error en triage de vulnerabilidades específicas: {str(e)}")
    
    def _enhance_vulnerability_analysis(self, vulnerability: TriagedVulnerability) -> TriagedVulnerability:
        """Mejora el análisis de una vulnerabilidad con lógica de negocio."""
        # Recalcular severidad con lógica de dominio
        enhanced_severity = self._triage_service.calculate_severity_level(
            vulnerability.analysis.severity_score,
            vulnerability.analysis.impact_level,
            vulnerability.analysis.exploit_probability
        )
        
        # Recalcular prioridad
        enhanced_priority = self._triage_service.calculate_priority_level(
            enhanced_severity,
            vulnerability.analysis.confidence_score,
            vulnerability.evidence
        )
        
        # Calcular score de confianza mejorado
        enhanced_confidence = self._triage_service.calculate_confidence_score(
            vulnerability.evidence,
            vulnerability.original_finding.detailed_proof_of_concept is not None
        )
        
        # Generar plan de remediación
        remediation_plan = self._triage_service.generate_remediation_plan(
            vulnerability.original_finding,
            enhanced_severity,
            enhanced_priority
        )
        
        # Crear análisis mejorado
        enhanced_analysis = vulnerability.analysis.model_copy(update={
            "final_severity": enhanced_severity,
            "final_priority": enhanced_priority,
            "confidence_score": enhanced_confidence
        })
        
        # Agregar recomendación de remediación si no existe
        enhanced_recommendations = list(vulnerability.recommendations)
        if remediation_plan and remediation_plan not in [rec.description for rec in enhanced_recommendations]:
            from ...domain.models.triage import TriageRecommendation, RecommendationType
            remediation_rec = TriageRecommendation(
                type=RecommendationType.REMEDIATION,
                description=remediation_plan,
                priority="alta" if enhanced_priority in ["crítica", "alta"] else "media"
            )
            enhanced_recommendations.append(remediation_rec)
        
        return vulnerability.model_copy(update={
            "analysis": enhanced_analysis,
            "recommendations": enhanced_recommendations
        })
    
    def _calculate_risk_metrics(self, vulnerabilities: List[TriagedVulnerability]) -> Dict[str, Any]:
        """Calcula métricas de riesgo para el conjunto de vulnerabilidades."""
        if not vulnerabilities:
            return {
                "avg_severity_score": 0.0,
                "avg_confidence_score": 0.0,
                "overall_risk_score": 0.0,
                "critical_vulnerabilities": 0,
                "high_confidence_vulnerabilities": 0
            }
        
        # Calcular promedios
        total_severity = sum(vuln.analysis.severity_score for vuln in vulnerabilities)
        total_confidence = sum(vuln.analysis.confidence_score for vuln in vulnerabilities)
        
        avg_severity = total_severity / len(vulnerabilities)
        avg_confidence = total_confidence / len(vulnerabilities)
        
        # Calcular riesgo general usando el servicio de dominio
        overall_risk = self._triage_service.assess_overall_risk(vulnerabilities)
        
        # Contar vulnerabilidades críticas
        critical_count = sum(
            1 for vuln in vulnerabilities 
            if vuln.analysis.final_severity.lower() in ['crítica', 'critical']
        )
        
        # Contar vulnerabilidades con alta confianza
        high_confidence_count = sum(
            1 for vuln in vulnerabilities 
            if vuln.analysis.confidence_score >= 0.8
        )
        
        return {
            "avg_severity_score": round(avg_severity, 2),
            "avg_confidence_score": round(avg_confidence, 2),
            "overall_risk_score": round(overall_risk, 2),
            "critical_vulnerabilities": critical_count,
            "high_confidence_vulnerabilities": high_confidence_count,
            "severity_distribution": self._get_severity_distribution(vulnerabilities),
            "priority_distribution": self._get_priority_distribution(vulnerabilities)
        }
    
    def _get_severity_distribution(self, vulnerabilities: List[TriagedVulnerability]) -> Dict[str, int]:
        """Obtiene la distribución de severidades."""
        distribution = {"crítica": 0, "alta": 0, "media": 0, "baja": 0, "informativa": 0}
        
        for vuln in vulnerabilities:
            severity = vuln.analysis.final_severity.lower()
            if severity in distribution:
                distribution[severity] += 1
            elif severity in ['critical']:
                distribution['crítica'] += 1
            elif severity in ['high']:
                distribution['alta'] += 1
            elif severity in ['medium']:
                distribution['media'] += 1
            elif severity in ['low']:
                distribution['baja'] += 1
            elif severity in ['info', 'informational']:
                distribution['informativa'] += 1
        
        return distribution
    
    def _get_priority_distribution(self, vulnerabilities: List[TriagedVulnerability]) -> Dict[str, int]:
        """Obtiene la distribución de prioridades."""
        distribution = {"crítica": 0, "alta": 0, "media": 0, "baja": 0}
        
        for vuln in vulnerabilities:
            priority = vuln.analysis.final_priority.lower()
            if priority in distribution:
                distribution[priority] += 1
            elif priority in ['critical']:
                distribution['crítica'] += 1
            elif priority in ['high']:
                distribution['alta'] += 1
            elif priority in ['medium']:
                distribution['media'] += 1
            elif priority in ['low']:
                distribution['baja'] += 1
        
        return distribution
    
    def execute_as_json(self, security_report: Dict[str, Any], pretty: bool = True) -> str:
        """Ejecuta el caso de uso y retorna JSON formateado."""
        result = self.execute(security_report)
        
        if pretty:
            return json.dumps(result, indent=2, ensure_ascii=False, default=str)
        else:
            return json.dumps(result, ensure_ascii=False, default=str)
    
    def get_triage_summary(self, security_report: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene solo un resumen del triage sin el análisis completo.
        
        Útil para dashboards o vistas rápidas.
        """
        try:
            full_result = self.execute(security_report)
            
            return {
                "total_vulnerabilities": full_result["quality_metrics"]["total_vulnerabilities"],
                "avg_severity_score": full_result["quality_metrics"]["avg_severity_score"],
                "avg_confidence_score": full_result["quality_metrics"]["avg_confidence_score"],
                "overall_risk_score": full_result["risk_analysis"]["overall_risk_score"],
                "critical_vulnerabilities": full_result["risk_analysis"]["critical_vulnerabilities"],
                "severity_distribution": full_result["risk_analysis"]["severity_distribution"],
                "is_valid": full_result["quality_metrics"]["is_valid"],
                "triage_date": full_result["metadata"]["triage_date"]
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "triage_date": datetime.now().isoformat()
            }