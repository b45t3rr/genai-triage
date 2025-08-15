import json
import os
from typing import Dict, Any
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from src.domain.interfaces import SecurityAnalyzerInterface, LLMInterface
from src.domain.entities import SecurityReport
from src.domain.exceptions import LLMConnectionError, ReportAnalysisError, JSONParsingError


class LangChainReportAnalyzer(SecurityAnalyzerInterface):
    """Analizador de reportes usando LangChain."""
    
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self.analysis_prompt = self._create_analysis_prompt()
    
    def _create_analysis_prompt(self) -> str:
        """Crea el prompt para analizar reportes de seguridad."""
        return """
Eres un experto analista de seguridad. Tu tarea es analizar el contenido de un reporte de vulnerabilidades y estructurarlo en formato JSON.

Debes extraer y organizar la información siguiendo exactamente este esquema JSON:

{
    "documento": {
        "titulo": "string",
        "fecha": "string",
        "autor": "string",
        "tipo_documento": "string",
        "numero_paginas": number
    },
    "resumen_ejecutivo": "string",
    "hallazgos_principales": [
        {
            "id": "string (ID único de la vulnerabilidad, ej: VULN-001, VULN-002, etc.)",
            "nombre": "string",
            "categoria": "string",
            "descripcion": "string",
            "severidad": "string",
            "impacto": "string",
            "detailed_proof_of_concept": "string (opcional)"
        }
    ],
    "recomendaciones": [
        {
            "prioridad": "string",
            "accion": "string",
            "descripcion": "string"
        }
    ],
    "datos_tecnicos": {
        "entorno": "string",
        "endpoints_pruebas": ["string"],
        "credenciales_utilizadas": {
            "nombre_usuario": {
                "usuario": "string",
                "contrasena": "string"
            }
        },
        "observaciones_abiertas": ["string"]
    },
    "conclusiones": "string",
    "informacion_adicional": {
        "nota": "string",
        "recomendaciones_adicionales": ["string"]
    }
}

Instrucciones:
1. Analiza cuidadosamente todo el contenido del reporte
2. Extrae la información relevante y organízala según el esquema
3. Si algún campo no está disponible, usa valores por defecto apropiados ("Desconocido", "No especificado", etc.)
4. Mantén la información técnica precisa y detallada
5. Para cada vulnerabilidad:
   - "id": ID único y secuencial para la vulnerabilidad (ej: "VULN-001", "VULN-002", "VULN-003", etc.)
   - "nombre": Nombre específico de la vulnerabilidad (ej: "SQL Injection", "Cross-Site Scripting", "Server-Side Request Forgery")
   - "categoria": Tipo o categoría de la vulnerabilidad (ej: "Injection", "Broken Authentication", "Security Misconfiguration")
   - "severidad": Nivel de severidad (Crítico, Alto, Medio, Bajo)
6. Prioriza las recomendaciones (Alta, Media, Baja)
7. Responde ÚNICAMENTE con el JSON válido, sin texto adicional

Contenido del reporte a analizar:
"""

    def analyze_content(self, content: str) -> SecurityReport:
        """Analiza el contenido del PDF y genera un reporte estructurado."""
        try:
            # Generar análisis usando el LLM
            full_prompt = self.analysis_prompt + "\n\n" + content
            response = self.llm.generate_response(self.analysis_prompt, content)
            
            # Limpiar la respuesta para asegurar que sea JSON válido
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()
            
            # Parsear JSON
            try:
                report_data = json.loads(response)
            except json.JSONDecodeError as e:
                raise JSONParsingError(f"Error parseando JSON del LLM: {str(e)}. Respuesta: {response[:500]}...")
            
            # Validar y crear el objeto SecurityReport
            security_report = SecurityReport(**report_data)
            return security_report
            
        except (JSONParsingError, LLMConnectionError):
            raise
        except Exception as e:
            raise ReportAnalysisError(f"Error analizando el reporte: {str(e)}")


class PDFAnalysisTool:
    """Tool para LangChain que analiza PDFs."""
    
    def __init__(self, pdf_content: str):
        self.pdf_content = pdf_content
    
    def analyze_content(self, query: str) -> str:
        """Analiza el contenido del PDF basado en la consulta."""
        return f"Analizando: {query}\n\nContenido del PDF:\n{self.pdf_content[:1000]}..."


def create_pdf_analysis_agent(pdf_content: str, llm: ChatOpenAI) -> AgentExecutor:
    """Crea un agente de LangChain para analizar PDFs."""
    
    # Crear herramienta de análisis
    pdf_tool = PDFAnalysisTool(pdf_content)
    
    tools = [
        Tool(
            name="analyze_pdf_content",
            description="Analiza el contenido de un PDF de reporte de seguridad",
            func=pdf_tool.analyze_content
        )
    ]
    
    # Crear prompt del agente
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Eres un experto analista de seguridad que estructura reportes en JSON."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    # Crear agente
    agent = create_openai_tools_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor