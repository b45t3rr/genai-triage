"""Servicio de dominio para análisis de seguridad."""

from typing import Dict, Any, List, Optional
import re
from datetime import datetime

from ..models import Finding, SecurityReport, SeverityLevel


class SecurityAnalysisService:
    """Servicio de dominio para lógica de análisis de seguridad.
    
    Encapsula las reglas de negocio para:
    - Validación de hallazgos de seguridad
    - Normalización de datos de seguridad
    - Clasificación de vulnerabilidades
    - Extracción de información técnica
    """
    
    # Patrones comunes de vulnerabilidades
    VULNERABILITY_PATTERNS = {
        "sql_injection": ["sql injection", "sqli", "union select", "' or 1=1"],
        "xss": ["cross-site scripting", "xss", "<script>", "javascript:"],
        "csrf": ["cross-site request forgery", "csrf", "token"],
        "lfi": ["local file inclusion", "lfi", "../", "directory traversal"],
        "rfi": ["remote file inclusion", "rfi", "include"],
        "command_injection": ["command injection", "code execution", "system()"],
        "authentication": ["authentication", "login", "password", "session"],
        "authorization": ["authorization", "access control", "privilege"],
        "information_disclosure": ["information disclosure", "sensitive data", "exposure"]
    }
    
    # Mapeo de severidades comunes
    SEVERITY_MAPPING = {
        "crítica": SeverityLevel.CRITICAL,
        "critical": SeverityLevel.CRITICAL,
        "alta": SeverityLevel.HIGH,
        "high": SeverityLevel.HIGH,
        "media": SeverityLevel.MEDIUM,
        "medium": SeverityLevel.MEDIUM,
        "baja": SeverityLevel.LOW,
        "low": SeverityLevel.LOW,
        "informativa": SeverityLevel.INFO,
        "info": SeverityLevel.INFO,
        "informational": SeverityLevel.INFO
    }
    
    def normalize_finding(self, finding_data: Dict[str, Any]) -> Finding:
        """Normaliza y valida un hallazgo de seguridad."""
        # Normalizar severidad
        severity = self._normalize_severity(finding_data.get("severidad", "media"))
        
        # Clasificar categoría automáticamente si no está presente
        category = finding_data.get("categoria")
        if not category:
            category = self._classify_vulnerability_category(
                finding_data.get("nombre", ""),
                finding_data.get("descripcion", "")
            )
        
        return Finding(
            nombre=finding_data.get("nombre", "Vulnerabilidad sin nombre"),
            categoria=category,
            descripcion=finding_data.get("descripcion", ""),
            severidad=severity,
            impacto=finding_data.get("impacto", "No especificado"),
            detailed_proof_of_concept=finding_data.get("detailed_proof_of_concept")
        )
    
    def _normalize_severity(self, severity_str: str) -> str:
        """Normaliza el string de severidad a valores estándar."""
        severity_clean = severity_str.lower().strip()
        
        # Buscar coincidencias exactas primero
        for key, enum_val in self.SEVERITY_MAPPING.items():
            if key in severity_clean:
                return enum_val.value
        
        # Si no encuentra coincidencia, usar "media" como default
        return SeverityLevel.MEDIUM.value
    
    def _classify_vulnerability_category(self, name: str, description: str) -> str:
        """Clasifica automáticamente la categoría de vulnerabilidad."""
        text_to_analyze = f"{name} {description}".lower()
        
        # Buscar patrones conocidos
        for category, patterns in self.VULNERABILITY_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_to_analyze:
                    return category.replace("_", " ").title()
        
        return "Otros"
    
    def validate_security_report(self, report: SecurityReport) -> List[str]:
        """Valida un reporte de seguridad y retorna lista de errores/advertencias."""
        issues = []
        
        # Validar documento
        if not report.documento.titulo.strip():
            issues.append("El título del documento está vacío")
        
        if not report.documento.autor.strip():
            issues.append("El autor del documento no está especificado")
        
        # Validar hallazgos
        if not report.hallazgos_principales:
            issues.append("No se encontraron hallazgos de seguridad")
        else:
            for i, finding in enumerate(report.hallazgos_principales):
                if not finding.nombre.strip():
                    issues.append(f"Hallazgo {i+1}: Nombre vacío")
                
                if not finding.descripcion.strip():
                    issues.append(f"Hallazgo {i+1}: Descripción vacía")
                
                if len(finding.descripcion) < 20:
                    issues.append(f"Hallazgo {i+1}: Descripción muy corta (< 20 caracteres)")
        
        # Validar recomendaciones
        if not report.recomendaciones:
            issues.append("No se encontraron recomendaciones")
        
        # Validar datos técnicos
        if not report.datos_tecnicos.endpoints_pruebas:
            issues.append("No se especificaron endpoints de prueba")
        
        return issues
    
    def extract_technical_indicators(self, report: SecurityReport) -> Dict[str, Any]:
        """Extrae indicadores técnicos del reporte para análisis posterior."""
        indicators = {
            "total_findings": len(report.hallazgos_principales),
            "severity_distribution": self._calculate_severity_distribution(report.hallazgos_principales),
            "category_distribution": self._calculate_category_distribution(report.hallazgos_principales),
            "has_proof_of_concept": self._count_findings_with_poc(report.hallazgos_principales),
            "endpoints_tested": len(report.datos_tecnicos.endpoints_pruebas),
            "credentials_used": len(report.datos_tecnicos.credenciales_utilizadas),
            "open_observations": len(report.datos_tecnicos.observaciones_abiertas)
        }
        
        return indicators
    
    def _calculate_severity_distribution(self, findings: List[Finding]) -> Dict[str, int]:
        """Calcula la distribución de severidades."""
        distribution = {
            "crítica": 0,
            "alta": 0,
            "media": 0,
            "baja": 0,
            "informativa": 0
        }
        
        for finding in findings:
            severity = finding.severidad.lower()
            if severity in distribution:
                distribution[severity] += 1
            else:
                distribution["media"] += 1  # Default para severidades no reconocidas
        
        return distribution
    
    def _calculate_category_distribution(self, findings: List[Finding]) -> Dict[str, int]:
        """Calcula la distribución de categorías."""
        distribution = {}
        
        for finding in findings:
            category = finding.categoria
            distribution[category] = distribution.get(category, 0) + 1
        
        return distribution
    
    def _count_findings_with_poc(self, findings: List[Finding]) -> int:
        """Cuenta hallazgos que tienen proof of concept."""
        return sum(1 for finding in findings if finding.detailed_proof_of_concept)
    
    def suggest_additional_tests(self, report: SecurityReport) -> List[str]:
        """Sugiere pruebas adicionales basadas en los hallazgos encontrados."""
        suggestions = []
        
        # Analizar hallazgos para sugerir pruebas relacionadas
        categories_found = {finding.categoria.lower() for finding in report.hallazgos_principales}
        
        if "sql injection" in categories_found:
            suggestions.append("Realizar pruebas de blind SQL injection")
            suggestions.append("Verificar protecciones contra NoSQL injection")
        
        if "xss" in categories_found:
            suggestions.append("Probar XSS en diferentes contextos (atributos, JavaScript)")
            suggestions.append("Verificar Content Security Policy (CSP)")
        
        if "authentication" in categories_found:
            suggestions.append("Probar ataques de fuerza bruta")
            suggestions.append("Verificar políticas de contraseñas")
            suggestions.append("Probar bypass de autenticación")
        
        if "authorization" in categories_found:
            suggestions.append("Probar escalación de privilegios")
            suggestions.append("Verificar controles de acceso horizontal")
        
        # Sugerencias generales si hay pocos hallazgos
        if len(report.hallazgos_principales) < 3:
            suggestions.append("Realizar análisis de código estático")
            suggestions.append("Probar configuraciones de seguridad del servidor")
            suggestions.append("Verificar manejo de errores y información sensible")
        
        return suggestions
    
    def calculate_testing_coverage_score(self, report: SecurityReport) -> float:
        """Calcula un score de cobertura de las pruebas realizadas."""
        score = 0.0
        max_score = 10.0
        
        # Puntos por número de hallazgos (máximo 3 puntos)
        findings_score = min(len(report.hallazgos_principales) * 0.5, 3.0)
        score += findings_score
        
        # Puntos por diversidad de categorías (máximo 2 puntos)
        unique_categories = len(set(finding.categoria for finding in report.hallazgos_principales))
        category_score = min(unique_categories * 0.4, 2.0)
        score += category_score
        
        # Puntos por endpoints probados (máximo 2 puntos)
        endpoints_score = min(len(report.datos_tecnicos.endpoints_pruebas) * 0.2, 2.0)
        score += endpoints_score
        
        # Puntos por evidencia técnica (máximo 2 puntos)
        poc_count = self._count_findings_with_poc(report.hallazgos_principales)
        evidence_score = min(poc_count * 0.5, 2.0)
        score += evidence_score
        
        # Puntos por completitud de recomendaciones (máximo 1 punto)
        rec_score = min(len(report.recomendaciones) * 0.2, 1.0)
        score += rec_score
        
        return min(score, max_score)