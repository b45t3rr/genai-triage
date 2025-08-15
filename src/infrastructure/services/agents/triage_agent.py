import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage

from src.domain.interfaces import LLMInterface
from src.domain.entities import (
    TriageReport, 
    TriagedVulnerability, 
    TriageEvidence, 
    TriageRecommendation,
    SecurityReport
)
from src.domain.exceptions import LLMConnectionError, ReportAnalysisError, JSONParsingError


class TriageAgent:
    """Agente especializado en triage de vulnerabilidades.
    
    Este agente analiza vulnerabilidades de seguridad y:
    1. Asigna severidad basada en evidencia real
    2. Establece prioridades de remediación
    3. Proporciona recomendaciones específicas
    4. Genera un plan de remediación ordenado
    """
    
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self.version = "1.0.0"
        self.triage_prompt = self._create_triage_prompt()
        
    def _create_triage_prompt(self) -> str:
        """Crea el prompt especializado para análisis de triage."""
        return """Eres un experto analista de seguridad especializado en triage de vulnerabilidades.

Tu tarea es analizar vulnerabilidades de seguridad y realizar un triage completo que incluya:

1. **ANÁLISIS DE SEVERIDAD BASADO EN EVIDENCIA:**
   - Evalúa la evidencia real disponible (código, respuestas HTTP, archivos, configuraciones)
   - Asigna severidad basada en impacto real, no solo teórico
   - Considera el contexto del entorno y la aplicación
   - Escalas: "crítica", "alta", "media", "baja", "informativa"

2. **ASIGNACIÓN DE PRIORIDAD:**
   - P0: Crítico - Requiere acción inmediata (< 24h)
   - P1: Alto - Requiere acción urgente (< 1 semana)
   - P2: Medio - Requiere acción pronta (< 1 mes)
   - P3: Bajo - Puede programarse (< 3 meses)
   - P4: Informativo - Para conocimiento

3. **CRITERIOS DE EVALUACIÓN:**
   - **Impacto Real:** ¿Qué tan grave es el daño potencial?
   - **Probabilidad de Explotación:** ¿Qué tan fácil es explotar?
   - **Evidencia Disponible:** ¿Qué tan sólida es la evidencia?
   - **Contexto del Negocio:** ¿Qué tan crítico es el sistema afectado?
   - **Facilidad de Remediación:** ¿Qué tan fácil es corregir?

4. **TIPOS DE EVIDENCIA A EVALUAR:**
   - **Código:** Fragmentos de código vulnerable
   - **Respuesta HTTP:** Respuestas que confirman la vulnerabilidad
   - **Archivo:** Archivos sensibles expuestos
   - **Configuración:** Configuraciones inseguras
   - **Base de datos:** Datos expuestos o manipulables

5. **RECOMENDACIONES ESPECÍFICAS:**
   - **Inmediata:** Acciones que deben tomarse de inmediato
   - **Correctiva:** Correcciones del código/configuración
   - **Preventiva:** Medidas para prevenir recurrencia
   - **Mitigación:** Medidas temporales mientras se corrige

6. **FORMATO DE RESPUESTA:**
Debes responder SIEMPRE en formato JSON válido con la siguiente estructura:

```json
{
  "vulnerabilidad_id": "ID único",
  "nombre": "Nombre de la vulnerabilidad",
  "severidad_original": "Severidad del reporte original",
  "severidad_triage": "crítica|alta|media|baja|informativa",
  "justificacion_severidad": "Explicación detallada del por qué de la severidad asignada",
  "prioridad": "P0|P1|P2|P3|P4",
  "justificacion_prioridad": "Explicación de la prioridad asignada",
  "impacto_real": "Descripción del impacto real basado en evidencia",
  "probabilidad_explotacion": "alta|media|baja",
  "evidencias": [
    {
      "tipo_evidencia": "código|respuesta_http|archivo|configuración|base_datos",
      "descripcion": "Descripción de la evidencia",
      "contenido": "Contenido específico de la evidencia",
      "ubicacion": "Ubicación específica (archivo:línea, endpoint, etc.)",
      "criticidad_evidencia": "alto|medio|bajo"
    }
  ],
  "recomendaciones": [
    {
      "tipo": "inmediata|correctiva|preventiva|mitigación",
      "descripcion": "Descripción de la recomendación",
      "pasos_implementacion": ["Paso 1", "Paso 2", "..."],
      "impacto_implementacion": "alto|medio|bajo"
    }
  ],
  "confianza_analisis": 0.95,
  "requiere_validacion_manual": false,
  "notas_adicionales": "Notas adicionales si las hay"
}
```

**IMPORTANTE:**
- Sé riguroso en el análisis de evidencia
- No asignes severidades altas sin evidencia sólida
- Considera el contexto real del entorno
- Proporciona recomendaciones accionables y específicas
- Justifica todas tus decisiones con evidencia

Comienza tu análisis de triage ahora."""
    
    def analyze_vulnerabilities(self, security_report: Dict[str, Any]) -> TriageReport:
        """Analiza las vulnerabilidades del reporte y genera un triage completo."""
        try:
            print("🔍 Iniciando análisis de triage de vulnerabilidades...")
            
            # Extraer vulnerabilidades del reporte (soportar múltiples formatos)
            hallazgos = security_report.get('hallazgos_principales', [])
            if not hallazgos:
                # Intentar con formato de análisis PDF
                analisis_pdf = security_report.get('analisis_pdf', {})
                hallazgos = analisis_pdf.get('hallazgos_principales', [])
            if not hallazgos:
                # Intentar con formato de análisis dinámico
                hallazgos = security_report.get('vulnerabilidades', [])
            if not hallazgos:
                # Intentar con formato de findings
                hallazgos = security_report.get('findings', [])
            
            if not hallazgos:
                raise ReportAnalysisError("No se encontraron vulnerabilidades en el reporte. Formatos soportados: 'hallazgos_principales', 'vulnerabilidades', 'findings'")
            
            print(f"📊 Analizando {len(hallazgos)} vulnerabilidades...")
            
            # Procesar cada vulnerabilidad
            triaged_vulnerabilities = []
            for i, hallazgo in enumerate(hallazgos):
                print(f"🎯 Procesando vulnerabilidad {i+1}/{len(hallazgos)}: {hallazgo.get('nombre', hallazgo.get('categoria', 'Sin nombre'))}")
                
                triaged_vuln = self._triage_single_vulnerability(hallazgo, i+1)
                triaged_vulnerabilities.append(triaged_vuln)
            
            # Generar reporte de triage completo
            triage_report = self._generate_triage_report(
                security_report, 
                triaged_vulnerabilities
            )
            
            print("✅ Análisis de triage completado")
            return triage_report
            
        except Exception as e:
            print(f"❌ Error en análisis de triage: {str(e)}")
            raise ReportAnalysisError(f"Error en análisis de triage: {str(e)}")
    
    def _triage_single_vulnerability(self, hallazgo: Dict[str, Any], vuln_number: int) -> TriagedVulnerability:
        """Realiza triage de una vulnerabilidad individual."""
        try:
            # Crear query para el agente
            triage_query = self._create_triage_query(hallazgo, vuln_number)
            
            # Usar el LLM para análisis
            response = self.llm.generate_response(self.triage_prompt, triage_query)
            
            # Parsear respuesta JSON
            triage_data = self._parse_triage_response(response)
            
            # Crear objeto TriagedVulnerability
            return self._create_triaged_vulnerability(triage_data, hallazgo)
            
        except Exception as e:
            print(f"⚠️ Error procesando vulnerabilidad {vuln_number}: {str(e)}")
            # Crear vulnerabilidad con datos mínimos en caso de error
            return self._create_fallback_vulnerability(hallazgo, vuln_number)
    
    def _create_triage_query(self, hallazgo: Dict[str, Any], vuln_number: int) -> str:
        """Crea la query específica para el triage de una vulnerabilidad."""
        # Extraer información con soporte para múltiples formatos
        nombre = hallazgo.get('nombre', hallazgo.get('categoria', 'No especificada'))
        descripcion = hallazgo.get('descripcion', hallazgo.get('detalles', 'No disponible'))
        severidad = hallazgo.get('severidad', 'No especificada')
        impacto = hallazgo.get('impacto', 'No especificado')
        
        # Evidencia puede estar en diferentes campos
        evidencia = (
            hallazgo.get('detailed_proof_of_concept') or 
            hallazgo.get('evidencia') or 
            hallazgo.get('detalles') or 
            'No se proporcionó evidencia detallada'
        )
        
        # Información adicional para análisis dinámico
        payload_usado = hallazgo.get('payload_usado', '')
        respuesta_servidor = hallazgo.get('respuesta_servidor', '')
        estado = hallazgo.get('estado', '')
        
        query = f"""VULNERABILIDAD #{vuln_number} PARA TRIAGE:

**INFORMACIÓN BÁSICA:**
- Nombre/Categoría: {nombre}
- Descripción: {descripcion}
- Severidad Original: {severidad}
- Impacto Reportado: {impacto}
- Estado: {estado}

**EVIDENCIA DISPONIBLE:**
{evidencia}"""
        
        # Agregar información específica de análisis dinámico si está disponible
        if payload_usado:
            query += f"\n\n**PAYLOAD UTILIZADO:**\n{payload_usado}"
        
        if respuesta_servidor:
            query += f"\n\n**RESPUESTA DEL SERVIDOR:**\n{respuesta_servidor}"
        
        query += """\n\n**INSTRUCCIONES:**
Realiza un análisis completo de triage para esta vulnerabilidad. Evalúa:
1. La calidad y solidez de la evidencia proporcionada
2. El impacto real basado en la evidencia
3. La facilidad de explotación
4. El contexto y las condiciones necesarias para la explotación

Proporciona una respuesta en formato JSON con la estructura especificada."""
        
        return query
    
    def _parse_triage_response(self, response: str) -> Dict[str, Any]:
        """Parsea la respuesta JSON del agente de triage."""
        try:
            # Buscar JSON en la respuesta
            import re
            
            # Buscar JSON con bloques de código
            json_match = re.search(r'```json\s*({.*?})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Buscar JSON sin bloques de código
                start_pos = response.find('{')
                if start_pos != -1:
                    brace_count = 0
                    end_pos = start_pos
                    for i, char in enumerate(response[start_pos:], start_pos):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_pos = i + 1
                                break
                    json_str = response[start_pos:end_pos]
                else:
                    raise JSONParsingError("No se encontró JSON válido en la respuesta")
            
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            print(f"❌ Error de JSON: {str(e)}")
            print(f"📄 Respuesta del LLM (primeros 500 chars): {response[:500]}")
            print(f"🔍 JSON extraído: {json_str[:300] if 'json_str' in locals() else 'No se pudo extraer'}")
            raise JSONParsingError(f"Error parseando JSON: {str(e)}")
        except Exception as e:
            print(f"❌ Error general: {str(e)}")
            print(f"📄 Respuesta del LLM (primeros 500 chars): {response[:500]}")
            raise JSONParsingError(f"Error procesando respuesta: {str(e)}")
    
    def _create_triaged_vulnerability(self, triage_data: Dict[str, Any], original_hallazgo: Dict[str, Any]) -> TriagedVulnerability:
        """Crea un objeto TriagedVulnerability a partir de los datos de triage."""
        
        # Crear evidencias
        evidencias = []
        for ev_data in triage_data.get('evidencias', []):
            evidencia = TriageEvidence(
                tipo_evidencia=ev_data.get('tipo_evidencia', 'desconocido'),
                descripcion=ev_data.get('descripcion', ''),
                contenido=ev_data.get('contenido', ''),
                ubicacion=ev_data.get('ubicacion'),
                criticidad_evidencia=ev_data.get('criticidad_evidencia', 'media')
            )
            evidencias.append(evidencia)
        
        # Crear recomendaciones
        recomendaciones = []
        for rec_data in triage_data.get('recomendaciones', []):
            recomendacion = TriageRecommendation(
                tipo=rec_data.get('tipo', 'correctiva'),
                descripcion=rec_data.get('descripcion', ''),
                pasos_implementacion=rec_data.get('pasos_implementacion', []),
                recursos_necesarios=rec_data.get('recursos_necesarios', []),
                impacto_implementacion=rec_data.get('impacto_implementacion', 'medio')
            )
            recomendaciones.append(recomendacion)
        
        # Crear vulnerabilidad triageada
        # Priorizar el ID de la vulnerabilidad original del PDF, luego el del triage, y finalmente generar uno
        vuln_id = (
            original_hallazgo.get('id') or 
            triage_data.get('vulnerabilidad_id') or 
            str(uuid.uuid4())
        )
        
        return TriagedVulnerability(
            id_vulnerabilidad=vuln_id,
            nombre=triage_data.get('nombre', original_hallazgo.get('nombre', original_hallazgo.get('categoria', 'Vulnerabilidad sin nombre'))),
            descripcion_original=original_hallazgo.get('descripcion', ''),
            severidad_original=original_hallazgo.get('severidad', 'No especificada'),
            severidad_triage=triage_data.get('severidad_triage', 'media'),
            justificacion_severidad=triage_data.get('justificacion_severidad', ''),
            prioridad=triage_data.get('prioridad', 'P2'),
            justificacion_prioridad=triage_data.get('justificacion_prioridad', ''),
            evidencias=evidencias,
            impacto_real=triage_data.get('impacto_real', ''),
            probabilidad_explotacion=triage_data.get('probabilidad_explotacion', 'media'),
            recomendaciones=recomendaciones,
            fecha_triage=datetime.now(),
            confianza_analisis=triage_data.get('confianza_analisis', 0.8),
            requiere_validacion_manual=triage_data.get('requiere_validacion_manual', False),
            notas_adicionales=triage_data.get('notas_adicionales')
        )
    
    def _create_fallback_vulnerability(self, hallazgo: Dict[str, Any], vuln_number: int) -> TriagedVulnerability:
        """Crea una vulnerabilidad con datos mínimos en caso de error."""
        # Extraer información con soporte para múltiples formatos
        nombre = hallazgo.get('nombre', hallazgo.get('categoria', f'Vulnerabilidad {vuln_number}'))
        descripcion = hallazgo.get('descripcion', hallazgo.get('detalles', ''))
        severidad = hallazgo.get('severidad', 'No especificada')
        
        # Priorizar el ID de la vulnerabilidad original del PDF, o generar uno de fallback
        vuln_id = hallazgo.get('id') or f"vuln_{vuln_number}_{uuid.uuid4().hex[:8]}"
        
        return TriagedVulnerability(
            id_vulnerabilidad=vuln_id,
            nombre=nombre,
            descripcion_original=descripcion,
            severidad_original=severidad,
            severidad_triage='media',  # Severidad por defecto
            justificacion_severidad='Análisis automático falló, requiere revisión manual',
            prioridad='P2',  # Prioridad por defecto
            justificacion_prioridad='Prioridad asignada por defecto debido a error en análisis',
            evidencias=[],
            impacto_real='Requiere análisis manual',
            probabilidad_explotacion='media',
            recomendaciones=[],
            fecha_triage=datetime.now(),
            confianza_analisis=0.1,  # Baja confianza
            requiere_validacion_manual=True,
            notas_adicionales='Error en análisis automático, requiere revisión manual'
        )
    
    def _generate_triage_report(self, security_report: Dict[str, Any], vulnerabilities: List[TriagedVulnerability]) -> TriageReport:
        """Genera el reporte completo de triage."""
        
        # Calcular distribuciones
        severidad_dist = {"crítica": 0, "alta": 0, "media": 0, "baja": 0, "informativa": 0}
        prioridad_dist = {"P0": 0, "P1": 0, "P2": 0, "P3": 0, "P4": 0}
        
        for vuln in vulnerabilities:
            severidad_dist[vuln.severidad_triage] = severidad_dist.get(vuln.severidad_triage, 0) + 1
            prioridad_dist[vuln.prioridad] = prioridad_dist.get(vuln.prioridad, 0) + 1
        
        # Calcular score de riesgo (0-10)
        risk_score = self._calculate_risk_score(vulnerabilities)
        
        # Determinar riesgo general
        if risk_score >= 8.0:
            riesgo_general = "crítico"
        elif risk_score >= 6.0:
            riesgo_general = "alto"
        elif risk_score >= 4.0:
            riesgo_general = "medio"
        else:
            riesgo_general = "bajo"
        
        # Generar resumen ejecutivo
        resumen_triage = self._generate_executive_summary(vulnerabilities, severidad_dist, prioridad_dist)
        
        # Generar plan de remediación
        plan_remediacion = self._generate_remediation_plan(vulnerabilities)
        
        # Generar recomendaciones generales
        recomendaciones_generales = self._generate_general_recommendations(vulnerabilities)
        
        return TriageReport(
            id_reporte=f"triage_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
            fecha_generacion=datetime.now(),
            reporte_origen=security_report.get('documento', {}).get('titulo', 'Reporte desconocido'),
            resumen_triage=resumen_triage,
            total_vulnerabilidades=len(vulnerabilities),
            distribucion_severidad=severidad_dist,
            distribucion_prioridad=prioridad_dist,
            vulnerabilidades=vulnerabilities,
            recomendaciones_generales=recomendaciones_generales,
            plan_remediacion=plan_remediacion,
            riesgo_general=riesgo_general,
            score_riesgo=risk_score,
            version_agente=self.version,
            configuracion_triage={
                "criterios_severidad": "Basado en evidencia real e impacto",
                "criterios_prioridad": "P0-P4 basado en urgencia y impacto",
                "fecha_analisis": datetime.now().isoformat()
            }
        )
    
    def _calculate_risk_score(self, vulnerabilities: List[TriagedVulnerability]) -> float:
        """Calcula un score de riesgo general (0-10)."""
        if not vulnerabilities:
            return 0.0
        
        severity_weights = {
            "crítica": 10.0,
            "alta": 7.5,
            "media": 5.0,
            "baja": 2.5,
            "informativa": 1.0
        }
        
        total_score = 0.0
        for vuln in vulnerabilities:
            base_score = severity_weights.get(vuln.severidad_triage, 5.0)
            confidence_factor = vuln.confianza_analisis
            total_score += base_score * confidence_factor
        
        # Normalizar por número de vulnerabilidades
        avg_score = total_score / len(vulnerabilities)
        return min(10.0, avg_score)
    
    def _generate_executive_summary(self, vulnerabilities: List[TriagedVulnerability], 
                                  severidad_dist: Dict[str, int], 
                                  prioridad_dist: Dict[str, int]) -> str:
        """Genera un resumen ejecutivo del triage."""
        total = len(vulnerabilities)
        criticas = severidad_dist.get("crítica", 0)
        altas = severidad_dist.get("alta", 0)
        p0_p1 = prioridad_dist.get("P0", 0) + prioridad_dist.get("P1", 0)
        
        return f"""Análisis de triage completado para {total} vulnerabilidades identificadas. 
Se encontraron {criticas} vulnerabilidades críticas y {altas} de severidad alta. 
{p0_p1} vulnerabilidades requieren atención inmediata o urgente (P0-P1). 
El análisis se basó en evidencia real y contexto del entorno para asignar severidades y prioridades precisas."""
    
    def _generate_remediation_plan(self, vulnerabilities: List[TriagedVulnerability]) -> List[Dict[str, Any]]:
        """Genera un plan de remediación ordenado por prioridad."""
        # Ordenar por prioridad
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
        sorted_vulns = sorted(vulnerabilities, key=lambda v: priority_order.get(v.prioridad, 5))
        
        plan = []
        for i, vuln in enumerate(sorted_vulns):
            plan_item = {
                "orden": i + 1,
                "vulnerabilidad": vuln.nombre,
                "prioridad": vuln.prioridad,
                "severidad": vuln.severidad_triage,
                "acciones_principales": [rec.descripcion for rec in vuln.recomendaciones[:3]],  # Top 3
                "requiere_validacion": vuln.requiere_validacion_manual
            }
            plan.append(plan_item)
        
        return plan
    
    def _generate_general_recommendations(self, vulnerabilities: List[TriagedVulnerability]) -> List[str]:
        """Genera recomendaciones generales basadas en el análisis."""
        recommendations = [
            "Implementar un proceso de revisión de seguridad en el ciclo de desarrollo",
            "Establecer monitoreo continuo de vulnerabilidades",
            "Capacitar al equipo de desarrollo en prácticas de codificación segura"
        ]
        
        # Agregar recomendaciones específicas basadas en patrones
        critical_count = sum(1 for v in vulnerabilities if v.severidad_triage == "crítica")
        if critical_count > 0:
            recommendations.insert(0, f"URGENTE: Abordar inmediatamente las {critical_count} vulnerabilidades críticas identificadas")
        
        manual_validation_count = sum(1 for v in vulnerabilities if v.requiere_validacion_manual)
        if manual_validation_count > 0:
            recommendations.append(f"Realizar validación manual de {manual_validation_count} vulnerabilidades que requieren revisión adicional")
        
        return recommendations
    
    def _estimate_remediation_time(self, vulnerabilities: List[TriagedVulnerability]) -> str:
        """Estima el tiempo total de remediación."""
        time_mapping = {
            "P0": 1,   # días
            "P1": 7,   # días  
            "P2": 30,  # días
            "P3": 90,  # días
            "P4": 180  # días
        }
        
        max_time = 0
        for vuln in vulnerabilities:
            time_days = time_mapping.get(vuln.prioridad, 30)
            max_time = max(max_time, time_days)
        
        if max_time <= 7:
            return "1 semana"
        elif max_time <= 30:
            return "1 mes"
        elif max_time <= 90:
            return "3 meses"
        else:
            return "6 meses"
    
    def _get_estimated_time_for_priority(self, priority: str) -> str:
        """Obtiene el tiempo estimado para una prioridad específica."""
        time_mapping = {
            "P0": "< 24 horas",
            "P1": "< 1 semana",
            "P2": "< 1 mes",
            "P3": "< 3 meses",
            "P4": "< 6 meses"
        }
        return time_mapping.get(priority, "Tiempo no determinado")
    
    def export_triage_report(self, triage_report: TriageReport, output_path: str) -> str:
        """Exporta el reporte de triage a un archivo JSON."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(triage_report.model_dump(), f, indent=2, ensure_ascii=False, default=str)
            
            print(f"📄 Reporte de triage exportado a: {output_path}")
            return output_path
            
        except Exception as e:
            raise Exception(f"Error exportando reporte de triage: {str(e)}")