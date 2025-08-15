"""Servicio de dominio para validación de reportes."""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re

from ..models import SecurityReport, TriageReport, Finding, TriagedVulnerability


class ReportValidationService:
    """Servicio de dominio para validación de reportes de seguridad.
    
    Encapsula las reglas de negocio para:
    - Validación de integridad de datos
    - Verificación de completitud de reportes
    - Validación de formatos y estándares
    - Detección de inconsistencias
    """
    
    # Patrones de validación
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    URL_PATTERN = re.compile(r'^https?://[\w\.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&\'\(\)\*\+,;=.]*$')
    IP_PATTERN = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    
    # Campos obligatorios por tipo de reporte
    REQUIRED_SECURITY_REPORT_FIELDS = [
        'documento.titulo',
        'documento.autor',
        'documento.fecha_creacion',
        'hallazgos_principales',
        'recomendaciones'
    ]
    
    REQUIRED_TRIAGE_REPORT_FIELDS = [
        'vulnerabilities',
        'summary.total_vulnerabilities',
        'summary.critical_count',
        'summary.high_count',
        'metadata.analysis_date'
    ]
    
    def validate_security_report(self, report: SecurityReport) -> Tuple[bool, List[str]]:
        """Valida un reporte de seguridad completo.
        
        Returns:
            Tuple[bool, List[str]]: (es_válido, lista_de_errores)
        """
        errors = []
        
        # Validaciones básicas
        errors.extend(self._validate_document_metadata(report))
        errors.extend(self._validate_findings(report.hallazgos_principales))
        errors.extend(self._validate_recommendations(report.recomendaciones))
        errors.extend(self._validate_technical_data(report.datos_tecnicos))
        
        # Validaciones de consistencia
        errors.extend(self._validate_report_consistency(report))
        
        return len(errors) == 0, errors
    
    def validate_triage_report(self, report: TriageReport) -> Tuple[bool, List[str]]:
        """Valida un reporte de triage.
        
        Returns:
            Tuple[bool, List[str]]: (es_válido, lista_de_errores)
        """
        errors = []
        
        # Validaciones básicas
        errors.extend(self._validate_triaged_vulnerabilities(report.vulnerabilities))
        errors.extend(self._validate_triage_summary(report.summary))
        errors.extend(self._validate_triage_metadata(report.metadata))
        
        # Validaciones de consistencia
        errors.extend(self._validate_triage_consistency(report))
        
        return len(errors) == 0, errors
    
    def _validate_document_metadata(self, report: SecurityReport) -> List[str]:
        """Valida los metadatos del documento."""
        errors = []
        
        # Título
        if not report.documento.titulo or not report.documento.titulo.strip():
            errors.append("El título del documento es obligatorio")
        elif len(report.documento.titulo.strip()) < 5:
            errors.append("El título del documento debe tener al menos 5 caracteres")
        
        # Autor
        if not report.documento.autor or not report.documento.autor.strip():
            errors.append("El autor del documento es obligatorio")
        
        # Fecha de creación
        if not report.documento.fecha_creacion:
            errors.append("La fecha de creación es obligatoria")
        elif report.documento.fecha_creacion > datetime.now():
            errors.append("La fecha de creación no puede ser futura")
        
        # Validar email del autor si parece ser un email
        if '@' in report.documento.autor and not self.EMAIL_PATTERN.match(report.documento.autor):
            errors.append("El formato del email del autor no es válido")
        
        return errors
    
    def _validate_findings(self, findings: List[Finding]) -> List[str]:
        """Valida los hallazgos de seguridad."""
        errors = []
        
        if not findings:
            errors.append("El reporte debe contener al menos un hallazgo")
            return errors
        
        for i, finding in enumerate(findings, 1):
            # Nombre del hallazgo
            if not finding.nombre or not finding.nombre.strip():
                errors.append(f"Hallazgo {i}: El nombre es obligatorio")
            elif len(finding.nombre.strip()) < 3:
                errors.append(f"Hallazgo {i}: El nombre debe tener al menos 3 caracteres")
            
            # Descripción
            if not finding.descripcion or not finding.descripcion.strip():
                errors.append(f"Hallazgo {i}: La descripción es obligatoria")
            elif len(finding.descripcion.strip()) < 20:
                errors.append(f"Hallazgo {i}: La descripción debe tener al menos 20 caracteres")
            
            # Categoría
            if not finding.categoria or not finding.categoria.strip():
                errors.append(f"Hallazgo {i}: La categoría es obligatoria")
            
            # Severidad
            valid_severities = ['crítica', 'alta', 'media', 'baja', 'informativa']
            if finding.severidad.lower() not in valid_severities:
                errors.append(f"Hallazgo {i}: Severidad '{finding.severidad}' no es válida. Debe ser una de: {', '.join(valid_severities)}")
            
            # Impacto
            if not finding.impacto or not finding.impacto.strip():
                errors.append(f"Hallazgo {i}: El impacto es obligatorio")
        
        return errors
    
    def _validate_recommendations(self, recommendations: List[str]) -> List[str]:
        """Valida las recomendaciones."""
        errors = []
        
        if not recommendations:
            errors.append("El reporte debe contener al menos una recomendación")
            return errors
        
        for i, rec in enumerate(recommendations, 1):
            if not rec or not rec.strip():
                errors.append(f"Recomendación {i}: No puede estar vacía")
            elif len(rec.strip()) < 10:
                errors.append(f"Recomendación {i}: Debe tener al menos 10 caracteres")
        
        return errors
    
    def _validate_technical_data(self, technical_data) -> List[str]:
        """Valida los datos técnicos."""
        errors = []
        
        # Endpoints de pruebas
        if not technical_data.endpoints_pruebas:
            errors.append("Debe especificar al menos un endpoint de prueba")
        else:
            for i, endpoint in enumerate(technical_data.endpoints_pruebas, 1):
                if not endpoint.strip():
                    errors.append(f"Endpoint {i}: No puede estar vacío")
                elif not (self.URL_PATTERN.match(endpoint) or self.IP_PATTERN.match(endpoint.split(':')[0])):
                    errors.append(f"Endpoint {i}: '{endpoint}' no tiene un formato válido de URL o IP")
        
        # Herramientas utilizadas
        if not technical_data.herramientas_utilizadas:
            errors.append("Debe especificar al menos una herramienta utilizada")
        
        return errors
    
    def _validate_triaged_vulnerabilities(self, vulnerabilities: List[TriagedVulnerability]) -> List[str]:
        """Valida las vulnerabilidades triadas."""
        errors = []
        
        if not vulnerabilities:
            errors.append("El reporte de triage debe contener al menos una vulnerabilidad")
            return errors
        
        for i, vuln in enumerate(vulnerabilities, 1):
            # Validar campos obligatorios
            if not vuln.original_finding.nombre:
                errors.append(f"Vulnerabilidad {i}: El nombre del hallazgo original es obligatorio")
            
            if not vuln.analysis.severity_score or vuln.analysis.severity_score < 0 or vuln.analysis.severity_score > 10:
                errors.append(f"Vulnerabilidad {i}: El score de severidad debe estar entre 0 y 10")
            
            if not vuln.analysis.confidence_score or vuln.analysis.confidence_score < 0 or vuln.analysis.confidence_score > 1:
                errors.append(f"Vulnerabilidad {i}: El score de confianza debe estar entre 0 y 1")
            
            # Validar que tenga al menos una recomendación
            if not vuln.recommendations:
                errors.append(f"Vulnerabilidad {i}: Debe tener al menos una recomendación")
            
            # Validar evidencia si existe
            if vuln.evidence:
                for j, evidence in enumerate(vuln.evidence, 1):
                    if not evidence.description:
                        errors.append(f"Vulnerabilidad {i}, Evidencia {j}: La descripción es obligatoria")
        
        return errors
    
    def _validate_triage_summary(self, summary) -> List[str]:
        """Valida el resumen del triage."""
        errors = []
        
        # Validar que los conteos sean consistentes
        total_calculated = (summary.critical_count + summary.high_count + 
                          summary.medium_count + summary.low_count + summary.info_count)
        
        if summary.total_vulnerabilities != total_calculated:
            errors.append(f"Inconsistencia en conteos: total ({summary.total_vulnerabilities}) != suma de severidades ({total_calculated})")
        
        # Validar que los conteos no sean negativos
        counts = {
            'total': summary.total_vulnerabilities,
            'críticas': summary.critical_count,
            'altas': summary.high_count,
            'medias': summary.medium_count,
            'bajas': summary.low_count,
            'informativas': summary.info_count
        }
        
        for name, count in counts.items():
            if count < 0:
                errors.append(f"El conteo de vulnerabilidades {name} no puede ser negativo")
        
        return errors
    
    def _validate_triage_metadata(self, metadata) -> List[str]:
        """Valida los metadatos del triage."""
        errors = []
        
        # Fecha de análisis
        if not metadata.analysis_date:
            errors.append("La fecha de análisis es obligatoria")
        elif metadata.analysis_date > datetime.now():
            errors.append("La fecha de análisis no puede ser futura")
        
        # Analista
        if not metadata.analyst or not metadata.analyst.strip():
            errors.append("El analista es obligatorio")
        
        return errors
    
    def _validate_report_consistency(self, report: SecurityReport) -> List[str]:
        """Valida la consistencia interna del reporte de seguridad."""
        errors = []
        
        # Verificar que el número de recomendaciones sea proporcional a los hallazgos
        findings_count = len(report.hallazgos_principales)
        recommendations_count = len(report.recomendaciones)
        
        if recommendations_count < findings_count * 0.5:
            errors.append(f"Pocas recomendaciones ({recommendations_count}) para la cantidad de hallazgos ({findings_count})")
        
        # Verificar que hallazgos críticos tengan recomendaciones específicas
        critical_findings = [f for f in report.hallazgos_principales if f.severidad.lower() == 'crítica']
        if critical_findings and recommendations_count < len(critical_findings):
            errors.append("Los hallazgos críticos requieren recomendaciones específicas")
        
        return errors
    
    def _validate_triage_consistency(self, report: TriageReport) -> List[str]:
        """Valida la consistencia interna del reporte de triage."""
        errors = []
        
        # Verificar que el resumen coincida con las vulnerabilidades
        actual_counts = self._count_vulnerabilities_by_severity(report.vulnerabilities)
        
        if actual_counts['critical'] != report.summary.critical_count:
            errors.append(f"Conteo de vulnerabilidades críticas inconsistente: esperado {report.summary.critical_count}, actual {actual_counts['critical']}")
        
        if actual_counts['high'] != report.summary.high_count:
            errors.append(f"Conteo de vulnerabilidades altas inconsistente: esperado {report.summary.high_count}, actual {actual_counts['high']}")
        
        if actual_counts['medium'] != report.summary.medium_count:
            errors.append(f"Conteo de vulnerabilidades medias inconsistente: esperado {report.summary.medium_count}, actual {actual_counts['medium']}")
        
        if actual_counts['low'] != report.summary.low_count:
            errors.append(f"Conteo de vulnerabilidades bajas inconsistente: esperado {report.summary.low_count}, actual {actual_counts['low']}")
        
        if actual_counts['info'] != report.summary.info_count:
            errors.append(f"Conteo de vulnerabilidades informativas inconsistente: esperado {report.summary.info_count}, actual {actual_counts['info']}")
        
        return errors
    
    def _count_vulnerabilities_by_severity(self, vulnerabilities: List[TriagedVulnerability]) -> Dict[str, int]:
        """Cuenta vulnerabilidades por severidad."""
        counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
        
        for vuln in vulnerabilities:
            severity = vuln.analysis.final_severity.lower()
            if severity in ['crítica', 'critical']:
                counts['critical'] += 1
            elif severity in ['alta', 'high']:
                counts['high'] += 1
            elif severity in ['media', 'medium']:
                counts['medium'] += 1
            elif severity in ['baja', 'low']:
                counts['low'] += 1
            elif severity in ['informativa', 'info', 'informational']:
                counts['info'] += 1
        
        return counts
    
    def get_validation_score(self, report: SecurityReport) -> float:
        """Calcula un score de calidad del reporte (0-10)."""
        is_valid, errors = self.validate_security_report(report)
        
        if not is_valid:
            # Penalizar por errores
            penalty = min(len(errors) * 0.5, 8.0)
            return max(10.0 - penalty, 0.0)
        
        # Bonificaciones por calidad adicional
        score = 8.0  # Base para reportes válidos
        
        # Bonificar por completitud
        if len(report.hallazgos_principales) >= 5:
            score += 0.5
        
        if len(report.recomendaciones) >= len(report.hallazgos_principales):
            score += 0.5
        
        # Bonificar por evidencia técnica
        findings_with_poc = sum(1 for f in report.hallazgos_principales if f.detailed_proof_of_concept)
        if findings_with_poc >= len(report.hallazgos_principales) * 0.5:
            score += 0.5
        
        # Bonificar por diversidad de categorías
        unique_categories = len(set(f.categoria for f in report.hallazgos_principales))
        if unique_categories >= 3:
            score += 0.5
        
        return min(score, 10.0)
    
    def suggest_improvements(self, report: SecurityReport) -> List[str]:
        """Sugiere mejoras para el reporte."""
        suggestions = []
        
        # Analizar completitud
        if len(report.hallazgos_principales) < 3:
            suggestions.append("Considerar realizar pruebas adicionales para identificar más vulnerabilidades")
        
        # Analizar evidencia
        findings_with_poc = sum(1 for f in report.hallazgos_principales if f.detailed_proof_of_concept)
        if findings_with_poc < len(report.hallazgos_principales) * 0.7:
            suggestions.append("Agregar más evidencia técnica (proof of concept) a los hallazgos")
        
        # Analizar recomendaciones
        if len(report.recomendaciones) < len(report.hallazgos_principales):
            suggestions.append("Agregar recomendaciones específicas para cada hallazgo identificado")
        
        # Analizar diversidad
        unique_categories = len(set(f.categoria for f in report.hallazgos_principales))
        if unique_categories < 3:
            suggestions.append("Ampliar el alcance de las pruebas para cubrir más categorías de vulnerabilidades")
        
        # Analizar severidades
        critical_count = sum(1 for f in report.hallazgos_principales if f.severidad.lower() == 'crítica')
        if critical_count == 0:
            suggestions.append("Verificar si existen vulnerabilidades críticas que puedan haberse pasado por alto")
        
        return suggestions