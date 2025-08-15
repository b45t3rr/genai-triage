import json
import os
import subprocess
import tempfile
from typing import Dict, Any, List, Optional
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from datetime import datetime
from src.domain.interfaces import LLMInterface
from src.domain.exceptions import LLMConnectionError, ReportAnalysisError, JSONParsingError
from ...adapters.external.tools.file_reader_tool import FileReaderTool
from ...adapters.external.tools.semgrep_analyzer_tool import SemgrepAnalyzerTool
from .pdf_analyzer_agent import LangChainReportAnalyzer


class StaticAnalysisAgent:
    """Agente para validación de vulnerabilidades mediante análisis estático."""
    
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self.pdf_analyzer = LangChainReportAnalyzer(llm)
        self.react_prompt = self._create_react_prompt()
    
    def _create_react_prompt(self) -> str:
        """Crea el prompt para el método ReACT."""
        return """Eres un experto en seguridad de aplicaciones que valida vulnerabilidades encontradas en reportes de seguridad.

Tu tarea es analizar el código fuente para confirmar si las vulnerabilidades reportadas realmente existen.

IMPORTANTE: Debes responder SIEMPRE con el siguiente formato JSON exacto:

```json
{{
  "id": "ID de la vulnerabilidad (ej: VULN-001)",
  "nombre": "nombre de la vulnerabilidad",
  "estado": "vulnerable" | "no_vulnerable",
  "evidencia": "Descripción específica de la evidencia encontrada o razón por la cual no es vulnerable"
}}
```

Reglas de análisis:
- Analiza el flujo de datos desde la entrada del usuario hasta su uso
- Verifica si existen controles de seguridad apropiados
- Considera el contexto completo de la aplicación
- Si encuentras código que podría ser problemático, marca como "vulnerable"
- Solo marca "no_vulnerable" si estás seguro de que la vulnerabilidad no existe
- Proporciona evidencia específica con nombres de archivos y líneas cuando sea posible

Comienza tu análisis ahora usando las herramientas disponibles.
"""
    
    def validate_vulnerabilities(self, pdf_path: str, source_path: str) -> Dict[str, Any]:
        """Valida vulnerabilidades usando análisis estático."""
        try:
            # 1. Analizar PDF
            print("📋 Analizando reporte PDF...")
            pdf_analysis = self._analyze_pdf_report(pdf_path)
            print(f"✅ PDF analizado: {len(pdf_analysis.get('hallazgos_principales', []))} vulnerabilidades encontradas")
            
            # 2. Ejecutar Semgrep
            print("🔍 Ejecutando análisis estático con Semgrep...")
            semgrep_results = self._run_semgrep_scan(source_path)
            print(f"✅ Semgrep completado: {len(semgrep_results)} hallazgos detectados")
            
            # 3. Validar con ReACT
            print("🤖 Iniciando validación con metodología ReACT...")
            validated_vulnerabilities = self._validate_with_react(
                pdf_analysis, semgrep_results, source_path
            )
            
            # 4. Generar resultado final
            print("📊 Generando reporte final...")
            return self._generate_final_result(pdf_analysis, validated_vulnerabilities)
            
        except Exception as e:
            raise ReportAnalysisError(f"Error en validación de vulnerabilidades: {str(e)}")
    
    def _analyze_pdf_report(self, pdf_path: str) -> Dict[str, Any]:
        """Analiza el reporte PDF usando el agente existente."""
        from ...adapters.external.tools.pdf_reader import PyPDF2Reader
        
        pdf_reader = PyPDF2Reader()
        pdf_document = pdf_reader.read_pdf(pdf_path)
        security_report = self.pdf_analyzer.analyze_content(pdf_document.content)
        
        return security_report.model_dump()
    
    def _run_semgrep_scan(self, source_path: str) -> List[Dict[str, Any]]:
        """Ejecuta semgrep en el código fuente."""
        try:
            # Crear archivo temporal para resultados
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Ejecutar semgrep
            cmd = [
                'semgrep',
                '--config=auto',  # Usar reglas automáticas
                '--json',
                '--output', temp_path,
                source_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Leer resultados
            if os.path.exists(temp_path):
                with open(temp_path, 'r') as f:
                    semgrep_data = json.load(f)
                os.unlink(temp_path)  # Limpiar archivo temporal
                return semgrep_data.get('results', [])
            else:
                return []
                
        except subprocess.TimeoutExpired:
            raise ReportAnalysisError("Timeout ejecutando semgrep")
        except Exception as e:
            raise ReportAnalysisError(f"Error ejecutando semgrep: {str(e)}")
    
    def _validate_with_react(self, pdf_analysis: Dict, semgrep_results: List[Dict], source_path: str) -> List[Dict[str, Any]]:
        """Valida vulnerabilidades usando agente ReACT de LangChain."""
        validated_vulnerabilities = []
        
        # Obtener vulnerabilidades del reporte PDF
        hallazgos = pdf_analysis.get('hallazgos_principales', [])
        total_vulns = len(hallazgos)
        
        # Crear agente ReACT con herramientas
        agent_executor = self._create_react_agent(source_path, semgrep_results)
        
        for i, hallazgo in enumerate(hallazgos):
            vuln_name = hallazgo.get('categoria', f'Vulnerabilidad {i+1}')
            print(f"🔎 Validando vulnerabilidad {i+1}/{total_vulns}: {vuln_name}")
            
            try:
                # Usar el agente ReACT para validar la vulnerabilidad
                validation_query = self._create_validation_query(hallazgo, i + 1)
                print(f"    🤖 Ejecutando agente ReACT...")
                
                agent_response = agent_executor.invoke({"input": validation_query})
                validation_result = self._parse_agent_response(agent_response, hallazgo)
                
                status_emoji = "✅" if validation_result['estado'] == 'vulnerable' else "❌"
                print(f"  {status_emoji} {vuln_name}: {validation_result['estado']} (severidad: {validation_result['severidad']})")
                validated_vulnerabilities.append(validation_result)
                
            except Exception as e:
                print(f"  ⚠️  Error validando {vuln_name}: {str(e)}")
                # Si falla la validación, marcar como no validada
                validated_vulnerabilities.append({
                    'nombre': hallazgo.get('categoria', f'Vulnerabilidad {i+1}'),
                    'estado': 'error',
                    'severidad': 'desconocida',
                    'detalles': f'Error en validación: {str(e)}',
                    'evidencia': 'No se pudo validar'
                })
        
        return validated_vulnerabilities
    
    def _create_react_agent(self, source_path: str, semgrep_results: List[Dict]) -> AgentExecutor:
        """Crea un agente ReACT con herramientas para análisis de código."""
        from langchain_openai import ChatOpenAI
        
        # Crear herramientas especializadas
        file_reader = FileReaderTool(source_path)
        semgrep_analyzer = SemgrepAnalyzerTool(source_path)
        
        tools = [
            Tool(
                name="read_source_file",
                description="Lee archivos de código fuente completos o rangos específicos de líneas. Uso: 'archivo.py' o 'archivo.py,10,20' para líneas 10-20",
                func=file_reader.read_file_smart
            ),
            Tool(
                name="run_security_scan",
                description="Ejecuta un escaneo de seguridad completo usando Semgrep con reglas predefinidas",
                func=lambda _: semgrep_analyzer.run_security_scan()
            ),
            Tool(
                name="find_files_by_pattern",
                description="Encuentra archivos en el código fuente que coincidan con patrones específicos (ej: 'auth', 'login', 'database')",
                func=lambda pattern: file_reader.find_files_by_pattern(pattern)
            ),
            Tool(
                name="analyze_code_pattern",
                description="Analiza patrones específicos de código usando Semgrep. Formato: 'patrón,lenguaje' (ej: 'eval(...),python')",
                func=lambda pattern: semgrep_analyzer.analyze_code_pattern(pattern)
            )
        ]
        
        # Crear prompt mejorado para el agente
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.react_prompt),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Usar el LLM pasado como parámetro
        llm = self.llm.llm
        
        # Crear agente
        agent = create_openai_tools_agent(llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=10)
    
    def _create_validation_query(self, hallazgo: Dict, vuln_number: int) -> str:
        """Crea la consulta para el agente ReACT."""
        return f"""
VALIDA LA SIGUIENTE VULNERABILIDAD #{vuln_number}:

ID: {hallazgo.get('id', f'VULN-{vuln_number:03d}')}
Nombre: {hallazgo.get('nombre', 'Vulnerabilidad sin nombre')}
Categoría: {hallazgo.get('categoria', 'Desconocida')}
Descripción: {hallazgo.get('descripcion', 'Sin descripción')}
Severidad reportada: {hallazgo.get('severidad', 'Desconocida')}
Impacto: {hallazgo.get('impacto', 'Sin impacto definido')}
PoC: {hallazgo.get('detailed_proof_of_concept', 'Sin PoC proporcionado')}

CONTEXTO IMPORTANTE:
- Esta vulnerabilidad fue reportada en un análisis de seguridad
- Semgrep ya encontró patrones sospechosos en el código
- Tu trabajo es confirmar si la vulnerabilidad existe y es explotable

USA LA METODOLOGÍA ReACT:
1. THOUGHT: Analiza qué tipo de vulnerabilidad es y qué patrones específicos buscar
2. ACTION: Usa las herramientas para examinar el código fuente y resultados de Semgrep
3. OBSERVATION: Documenta exactamente qué código problemático encuentras
4. CONCLUSION: Determina VULNERABLE o NO_VULNERABLE con evidencia específica

INSTRUCCIONES ESPECÍFICAS:
- Entiende primero el tipo de vulnerabilidad y su impacto, y el PoC de la vulnerabilidad
- Busca primero en los resultados de Semgrep patrones relacionados con esta vulnerabilidad
- Examina los archivos identificados línea por línea
- Busca patrones de código inseguro, validación faltante, o configuraciones débiles
- Si encuentras código que podría ser problemático, márca como VULNERABLE
- Solo marca NO_VULNERABLE si estás seguro de que la vulnerabilidad no existe

Comienza tu análisis ahora usando las herramientas disponibles.
"""
    
    def _parse_agent_response(self, agent_response: Dict, hallazgo: Dict) -> Dict[str, Any]:
        """Parsea la respuesta del agente ReACT que debe estar en formato JSON."""
        output = agent_response.get('output', '')
        
        # Valores por defecto
        estado = "no vulnerable"
        severidad = hallazgo.get('severidad', 'media')
        evidencia = "Sin evidencia específica encontrada"
        nombre = hallazgo.get('categoria', 'Vulnerabilidad desconocida')  # Valor por defecto
        vuln_id = hallazgo.get('id', 'VULN-UNKNOWN')  # ID por defecto
        
        try:
            # Buscar el JSON en la respuesta
            import re
            json_match = re.search(r'```json\s*({.*?})\s*```', output, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                result = json.loads(json_str)
                
                # Extraer información del JSON
                estado = result.get('estado', 'no_vulnerable')
                if estado == 'no_vulnerable':
                    estado = 'no vulnerable'
                    
                severidad = result.get('severidad', severidad)
                evidencia = result.get('evidencia', evidencia)
                # Extraer el nombre real de la vulnerabilidad del JSON de respuesta
                nombre = result.get('nombre', nombre)
                # Extraer el ID de la vulnerabilidad del JSON de respuesta
                vuln_id = result.get('id', vuln_id)
            else:
                # Fallback: buscar patrones simples si no hay JSON
                output_lower = output.lower()
                if any(pattern in output_lower for pattern in ['vulnerable', 'es vulnerable', 'sí es vulnerable']):
                    if not any(pattern in output_lower for pattern in ['no vulnerable', 'no es vulnerable']):
                        estado = "vulnerable"
                        
                # Extraer evidencia de la respuesta completa como fallback
                evidencia = output[:200] + "..." if len(output) > 200 else output
                
        except (json.JSONDecodeError, AttributeError) as e:
            # Si falla el parsing JSON, usar la respuesta completa como evidencia
            evidencia = f"Error parsing JSON response: {str(e)}. Raw output: {output[:200]}..."
        
        return {
            "id": vuln_id,
            "nombre": nombre,
            "estado": estado,
            "severidad": severidad,
            "detalles": output,
            "evidencia": evidencia
        }
    
    def _filter_relevant_semgrep_results(self, hallazgo: Dict, semgrep_results: List[Dict]) -> str:
        """Filtra resultados de semgrep relevantes para la vulnerabilidad."""
        categoria = hallazgo.get('categoria', '').lower()
        descripcion = hallazgo.get('descripcion', '').lower()
        
        relevant_results = []
        
        for result in semgrep_results[:10]:  # Limitar a 10 resultados más relevantes
            check_id = result.get('check_id', '').lower()
            message = result.get('message', '').lower()
            
            # Buscar coincidencias por palabras clave
            if any(keyword in check_id or keyword in message 
                   for keyword in [categoria, 'sql', 'xss', 'csrf', 'injection', 'auth', 'path traversal']):
                relevant_results.append({
                    'file': result.get('path', 'Desconocido'),
                    'line': result.get('start', {}).get('line', 0),
                    'rule': result.get('check_id', 'Desconocido'),
                    'message': result.get('message', 'Sin mensaje'),
                    'severity': result.get('extra', {}).get('severity', 'INFO')
                })
        
        if not relevant_results:
            return "No se encontraron resultados de semgrep directamente relacionados."
        
        return json.dumps(relevant_results, indent=2)
    

    
    def _generate_final_result(self, pdf_analysis: Dict, validated_vulnerabilities: List[Dict]) -> Dict[str, Any]:
        """Genera el resultado final en el formato requerido."""
        
        vulnerables_count = sum(1 for v in validated_vulnerabilities if v['estado'] == 'vulnerable')
        total_reportadas = len(validated_vulnerabilities)
        
        return {
            'vulnerabilidades_reportadas': total_reportadas,
            'vulnerabilidades_vulnerables': vulnerables_count,
            'timestamp': datetime.now().isoformat(),
            'vulnerabilidades': validated_vulnerabilities
        }








def create_static_analysis_agent(pdf_path: str, source_path: str, llm: ChatOpenAI) -> AgentExecutor:
    """Crea un agente de análisis estático con herramientas ReACT."""
    
    # Crear herramientas
    file_reader = FileReaderTool(source_path)
    semgrep_analyzer = SemgrepAnalyzerTool(source_path)
    
    tools = [
        Tool(
            name="read_source_file",
            description="Lee archivos de código fuente. Parámetros: file_path (requerido), start_line (opcional), end_line (opcional)",
            func=lambda query: file_reader.read_file_smart(query)
        ),
        Tool(
            name="analyze_code_pattern",
            description="Analiza patrones de código usando Semgrep. Formato: 'patrón,lenguaje' (ej: 'eval(...),python')",
            func=lambda pattern: semgrep_analyzer.analyze_code_pattern(pattern)
        )
    ]
    
    # Crear prompt del agente
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Eres un experto en análisis estático de seguridad que usa metodología ReACT para validar vulnerabilidades."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    # Crear agente
    agent = create_openai_tools_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor