"""Servicio de dominio para lógica de triage de vulnerabilidades."""

from typing import Dict, Any, List
from datetime import datetime

from ..models import (
    TriagedVulnerability,
    TriageReport,
    SeverityLevel,
    PriorityLevel,
    ImpactLevel,
    ExploitProbability
)


class TriageService:
    """Servicio de dominio para lógica de triage de vulnerabilidades.
    
    Encapsula las reglas de negocio para:
    - Cálculo de severidad basado en evidencia
    - Asignación de prioridades
    - Evaluación de riesgo general
    - Generación de planes de remediación
    """
    
    def calculate_severity_score(self, vulnerability: Dict[str, Any]) -> float:
        """Calcula un score numérico de severidad basado en múltiples factores.
        
        Args:
            vulnerability: Datos de la vulnerabilidad
            
        Returns:
            Score de 0.0 a 10.0
        """
        base_score = 0.0
        
        # Factor de impacto (40% del score)
        impact_weights = {
            "crítico": 4.0,
            "alto": 3.0,
            "medio": 2.0,
            "bajo": 1.0
        }
        impact = vulnerability.get("impacto", "bajo").lower()
        base_score += impact_weights.get(impact, 1.0)
        
        # Factor de probabilidad de explotación (30% del score)
        exploit_weights = {
            "alta": 3.0,
            "media": 2.0,
            "baja": 1.0
        }
        exploit_prob = vulnerability.get("probabilidad_explotacion", "baja").lower()
        base_score += exploit_weights.get(exploit_prob, 1.0)
        
        # Factor de evidencia disponible (20% del score)
        evidences = vulnerability.get("evidencias", [])
        if evidences:
            evidence_score = min(len(evidences) * 0.5, 2.0)
            base_score += evidence_score
        
        # Factor de facilidad de explotación (10% del score)
        if "proof_of_concept" in vulnerability:
            base_score += 1.0
            
        return min(base_score, 10.0)
    
    def determine_severity_level(self, score: float) -> SeverityLevel:
        """Determina el nivel de severidad basado en el score calculado."""
        if score >= 9.0:
            return SeverityLevel.CRITICAL
        elif score >= 7.0:
            return SeverityLevel.HIGH
        elif score >= 4.0:
            return SeverityLevel.MEDIUM
        elif score >= 2.0:
            return SeverityLevel.LOW
        else:
            return SeverityLevel.INFO
    
    def determine_priority_level(self, severity: SeverityLevel, business_impact: str = "medio") -> PriorityLevel:
        """Determina la prioridad basada en severidad e impacto de negocio."""
        # Matriz de prioridad: Severidad x Impacto de Negocio
        priority_matrix = {
            (SeverityLevel.CRITICAL, "alto"): PriorityLevel.P0,
            (SeverityLevel.CRITICAL, "medio"): PriorityLevel.P0,
            (SeverityLevel.CRITICAL, "bajo"): PriorityLevel.P1,
            
            (SeverityLevel.HIGH, "alto"): PriorityLevel.P0,
            (SeverityLevel.HIGH, "medio"): PriorityLevel.P1,
            (SeverityLevel.HIGH, "bajo"): PriorityLevel.P1,
            
            (SeverityLevel.MEDIUM, "alto"): PriorityLevel.P1,
            (SeverityLevel.MEDIUM, "medio"): PriorityLevel.P2,
            (SeverityLevel.MEDIUM, "bajo"): PriorityLevel.P2,
            
            (SeverityLevel.LOW, "alto"): PriorityLevel.P2,
            (SeverityLevel.LOW, "medio"): PriorityLevel.P3,
            (SeverityLevel.LOW, "bajo"): PriorityLevel.P3,
            
            (SeverityLevel.INFO, "alto"): PriorityLevel.P3,
            (SeverityLevel.INFO, "medio"): PriorityLevel.P4,
            (SeverityLevel.INFO, "bajo"): PriorityLevel.P4,
        }
        
        return priority_matrix.get((severity, business_impact.lower()), PriorityLevel.P3)
    
    def calculate_confidence_score(self, evidences: List[Dict[str, Any]]) -> float:
        """Calcula el nivel de confianza del análisis basado en la evidencia."""
        if not evidences:
            return 0.3
        
        confidence = 0.5  # Base confidence
        
        # Incrementar confianza por tipo y calidad de evidencia
        evidence_weights = {
            "código": 0.3,
            "respuesta_http": 0.2,
            "archivo": 0.15,
            "configuración": 0.1,
            "base_datos": 0.25
        }
        
        for evidence in evidences:
            evidence_type = evidence.get("tipo_evidencia", "")
            weight = evidence_weights.get(evidence_type, 0.05)
            
            # Ajustar por criticidad de la evidencia
            criticality = evidence.get("criticidad_evidencia", "bajo")
            if criticality == "alto":
                weight *= 1.5
            elif criticality == "medio":
                weight *= 1.2
            
            confidence += weight
        
        return min(confidence, 1.0)
    
    def calculate_overall_risk_score(self, vulnerabilities: List[TriagedVulnerability]) -> float:
        """Calcula el score de riesgo general del reporte."""
        if not vulnerabilities:
            return 0.0
        
        # Peso por severidad
        severity_weights = {
            SeverityLevel.CRITICAL: 10.0,
            SeverityLevel.HIGH: 7.0,
            SeverityLevel.MEDIUM: 4.0,
            SeverityLevel.LOW: 2.0,
            SeverityLevel.INFO: 0.5
        }
        
        total_score = 0.0
        for vuln in vulnerabilities:
            weight = severity_weights.get(vuln.severidad_triage, 1.0)
            confidence = vuln.confianza_analisis
            total_score += weight * confidence
        
        # Normalizar por número de vulnerabilidades
        avg_score = total_score / len(vulnerabilities)
        
        return min(avg_score, 10.0)
    
    def determine_overall_risk_level(self, risk_score: float) -> ImpactLevel:
        """Determina el nivel de riesgo general."""
        if risk_score >= 9.0:
            return ImpactLevel.CRITICAL
        elif risk_score >= 7.0:
            return ImpactLevel.HIGH
        elif risk_score >= 4.0:
            return ImpactLevel.MEDIUM
        else:
            return ImpactLevel.LOW
    
    def generate_remediation_plan(self, vulnerabilities: List[TriagedVulnerability]) -> List[Dict[str, Any]]:
        """Genera un plan de remediación ordenado por prioridad."""
        # Ordenar vulnerabilidades por prioridad
        priority_order = [PriorityLevel.P0, PriorityLevel.P1, PriorityLevel.P2, PriorityLevel.P3, PriorityLevel.P4]
        
        sorted_vulns = sorted(
            vulnerabilities,
            key=lambda v: priority_order.index(v.prioridad)
        )
        
        plan = []
        for i, vuln in enumerate(sorted_vulns, 1):
            plan_item = {
                "orden": i,
                "vulnerabilidad_id": vuln.id_vulnerabilidad,
                "nombre": vuln.nombre,
                "prioridad": vuln.prioridad.value,
                "severidad": vuln.severidad_triage.value,
                "tiempo_estimado": self._estimate_remediation_time(vuln.prioridad),
                "recursos_necesarios": self._extract_resources_from_recommendations(vuln.recomendaciones),
                "acciones_principales": self._extract_main_actions(vuln.recomendaciones)
            }
            plan.append(plan_item)
        
        return plan
    
    def _estimate_remediation_time(self, priority: PriorityLevel) -> str:
        """Estima el tiempo de remediación basado en la prioridad."""
        time_estimates = {
            PriorityLevel.P0: "< 24 horas",
            PriorityLevel.P1: "< 1 semana",
            PriorityLevel.P2: "< 1 mes",
            PriorityLevel.P3: "< 3 meses",
            PriorityLevel.P4: "Cuando sea posible"
        }
        return time_estimates.get(priority, "No definido")
    
    def _extract_resources_from_recommendations(self, recommendations: List[Any]) -> List[str]:
        """Extrae recursos necesarios de las recomendaciones."""
        resources = set()
        for rec in recommendations:
            if hasattr(rec, 'recursos_necesarios'):
                resources.update(rec.recursos_necesarios)
        return list(resources)
    
    def _extract_main_actions(self, recommendations: List[Any]) -> List[str]:
        """Extrae las acciones principales de las recomendaciones."""
        actions = []
        for rec in recommendations:
            if hasattr(rec, 'descripcion'):
                actions.append(rec.descripcion)
        return actions[:3]  # Máximo 3 acciones principales