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
from urllib.parse import urlparse
from src.domain.interfaces import LLMInterface
from src.domain.exceptions import LLMConnectionError, ReportAnalysisError, JSONParsingError
from ...adapters.external.tools.network_tool import NetworkTool
from .pdf_analyzer_agent import LangChainReportAnalyzer


class DynamicAnalysisAgent:
    """Agente para validación de vulnerabilidades mediante análisis dinámico y explotación."""
    
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self.pdf_analyzer = LangChainReportAnalyzer(llm)
        self.react_prompt = self._create_react_prompt()
    
    def _create_react_prompt(self) -> str:
        """Crea el prompt para el método ReACT de análisis dinámico."""
        return """Eres un experto en pentesting y seguridad de aplicaciones que valida vulnerabilidades mediante explotación en vivo.

Tu tarea es intentar replicar las vulnerabilidades reportadas usando las mismas técnicas de explotación descritas en el reporte.

IMPORTANTE: Debes responder SIEMPRE con el siguiente formato JSON exacto:

```json
{{
  "id": "ID de la vulnerabilidad (ej: VULN-001)",
  "nombre": "Nombre de la vulnerabilidad",
  "estado": "vulnerable" | "no_vulnerable",
  "evidencia": "Descripción específica de la evidencia encontrada durante la explotación o razón por la cual no es vulnerable",
  "payload_usado": "El payload o técnica específica que confirmó la vulnerabilidad",
  "respuesta_servidor": "Fragmento relevante de la respuesta del servidor que confirma la explotación"
}}
```

HERRAMIENTAS DISPONIBLES:
- curl_request: Para peticiones HTTP usando sintaxis nativa de curl. Pasa los argumentos como string (ej: '-X POST -H "Content-Type: application/json" -d "{{{{\"test\":\"data\"}}}}" /api/endpoint' o simplemente '/api/endpoint' para GET)
- wget_download: Para descargar archivos y probar directory traversal
- nmap_scan: Para escaneo de puertos y detección de vulnerabilidades
- telnet_connect: Para conectar a puertos específicos
- netcat_connect: Para conexiones de red avanzadas
- check_service_availability: Para verificar disponibilidad del servicio

METODOLOGÍA DE EXPLOTACIÓN:
1. Analiza el reporte PDF para obtener informacion util
2. Analiza el tipo de vulnerabilidad reportada y diseña tu estrategia de explotación en base a los detalles del reporte
3. Usa las herramientas de red disponibles para replicar los ataques
4. IMPORTANTE: Si curl_request devuelve Status Code 3, significa error de conexión - intenta diferentes enfoques
5. Analiza cuidadosamente las respuestas para identificar indicadores de explotación exitosa
6. Marca como "vulnerable" solo si obtienes evidencia clara de explotación

INTERPRETACIÓN DE RESPUESTAS:
- Status Code 0: Éxito
- Status Code 3: Error de conexión/DNS - el endpoint puede no existir
- Status Code 200: Respuesta HTTP exitosa
- Busca patrones específicos en STDOUT que indiquen explotación exitosa

Sé creativo y adapta tu enfoque según el tipo de vulnerabilidad. Las herramientas son genéricas y flexibles - úsalas de manera inteligente para construir tus propios tests de explotación.

Comienza tu análisis dinámico ahora usando las herramientas de red disponibles.
"""
    
    def validate_vulnerabilities(self, pdf_path: str, target_url: str) -> Dict[str, Any]:
        """Valida vulnerabilidades usando análisis dinámico y explotación."""
        try:
            # 1. Analizar PDF
            print("📋 Analizando reporte PDF...")
            pdf_analysis = self._analyze_pdf_report(pdf_path)
            print(f"✅ PDF analizado: {len(pdf_analysis.get('hallazgos_principales', []))} vulnerabilidades encontradas")
            
            # 2. Verificar disponibilidad del objetivo
            print(f"🌐 Verificando disponibilidad del objetivo: {target_url}")
            availability_check = self._check_target_availability(target_url)
            if not availability_check['available']:
                raise ReportAnalysisError(f"❌ El objetivo {target_url} no está disponible: {availability_check['error']}")
            print("✅ Objetivo disponible y accesible")
            
            # 3. Validar con ReACT y explotación
            print("🎯 Iniciando validación con explotación dinámica...")
            validated_vulnerabilities = self._validate_with_dynamic_react(
                pdf_analysis, target_url
            )
            print(f"✅ Validación completada: {len(validated_vulnerabilities)} vulnerabilidades procesadas")
            
            # 4. Generar resultado final
            print("📊 Generando reporte final...")
            return self._generate_final_result(pdf_analysis, validated_vulnerabilities)
            
        except Exception as e:
            raise ReportAnalysisError(f"Error en validación dinámica de vulnerabilidades: {str(e)}")
    
    def _analyze_pdf_report(self, pdf_path: str) -> Dict[str, Any]:
        """Analiza el reporte PDF usando el agente existente."""
        from ...adapters.external.tools.pdf_reader import PyPDF2Reader
        
        pdf_reader = PyPDF2Reader()
        pdf_document = pdf_reader.read_pdf(pdf_path)
        security_report = self.pdf_analyzer.analyze_content(pdf_document.content)
        
        return security_report.model_dump()
    
    def _check_target_availability(self, target_url: str) -> Dict[str, Any]:
        """Verifica si el objetivo está disponible para las pruebas."""
        try:
            network_tool = NetworkTool(target_url)
            result = network_tool.check_service_availability()
            
            # Analizar resultado para determinar disponibilidad
            if "DISPONIBLE" in result:
                return {'available': True, 'response': result}
            else:
                return {'available': False, 'error': result}
                
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    def _validate_with_dynamic_react(self, pdf_analysis: Dict, target_url: str) -> List[Dict[str, Any]]:
        """Valida vulnerabilidades usando agente ReACT con herramientas de red."""
        validated_vulnerabilities = []
        
        # Obtener vulnerabilidades del reporte PDF
        hallazgos = pdf_analysis.get('hallazgos_principales', [])
        total_vulns = len(hallazgos)
        
        # Verificar conectividad una sola vez al inicio
        print(f"🔍 Verificando conectividad con el objetivo...")
        network_tool = NetworkTool(target_url)
        ping_result = network_tool.ping_host()
        if "0% packet loss" in ping_result or "packets transmitted" in ping_result:
            print(f"✅ Conectividad confirmada")
        else:
            print(f"⚠️ Problemas de conectividad detectados")
        
        # Crear agente ReACT con herramientas de red
        agent_executor = self._create_dynamic_react_agent(target_url)
        
        for i, hallazgo in enumerate(hallazgos):
            vuln_name = hallazgo.get('categoria', f'Vulnerabilidad {i+1}')
            print(f"🎯 Validando vulnerabilidad {i+1}/{total_vulns}: {vuln_name}")
            
            try:
                # Usar el agente ReACT para validar la vulnerabilidad mediante explotación
                validation_query = self._create_dynamic_validation_query(hallazgo, i + 1, target_url, pdf_analysis)
                print(f"    🤖 Ejecutando agente de explotación dinámica...")
                
                agent_response = agent_executor.invoke({"input": validation_query})
                validation_result = self._parse_dynamic_agent_response(agent_response, hallazgo)
                
                print(f"    🔍 Resultado de parsing - Estado: '{validation_result['estado']}'")
                status_emoji = "✅" if validation_result['estado'] == 'vulnerable' else "❌"
                print(f"  {status_emoji} {vuln_name}: {validation_result['estado']}")
                validated_vulnerabilities.append(validation_result)
                
            except Exception as e:
                print(f"  ⚠️  Error validando {vuln_name}: {str(e)}")
                # Si falla la validación, marcar como no validada
                validated_vulnerabilities.append({
                    'nombre': hallazgo.get('categoria', f'Vulnerabilidad {i+1}'),
                    'estado': 'error',
                    'detalles': f'Error en validación dinámica: {str(e)}',
                    'evidencia': 'No se pudo validar mediante explotación'
                })
        
        return validated_vulnerabilities
    
    def _create_dynamic_react_agent(self, target_url: str) -> AgentExecutor:
        """Crea un agente ReACT con herramientas de red para explotación."""
        from langchain_openai import ChatOpenAI
        
        # Crear herramientas de red genéricas
        network_tool = NetworkTool(target_url)
        
        tools = [
            Tool(
                name="curl_request",
                description="""Realiza peticiones HTTP usando curl con argumentos nativos.
                
                Parámetros:
                - curl_args: Argumentos de curl como string (ej: '-X POST -H "Content-Type: application/json" -d "{{\"user\":\"admin\"}}" /api/login')
                
                La herramienta automáticamente construye la URL completa si solo proporcionas el endpoint.
                
                Ejemplos:
                - curl_request('/api/login')
                - curl_request('-X POST -H "Content-Type: application/json" -d "{{\"user\":\"admin\"}}" /api/login')
                - curl_request('-H "Cookie: session=abc123" /admin.php')
                - curl_request('-X PUT -d "data=test" /api/update')
                - curl_request('-v /debug')
                
                Usa la sintaxis estándar de curl que ya conoces.
                """,
                func=network_tool.curl_request
            ),
            Tool(
                name="wget_download",
                description="Descarga archivos o prueba endpoints usando wget. Útil para probar directory traversal, descargas de archivos, etc. Ejemplo: '/etc/passwd' o '../../etc/passwd'",
                func=network_tool.wget_download
            ),
            Tool(
                name="nmap_scan",
                description="Realiza escaneos de puertos y detección de servicios con nmap. Tipos disponibles: 'basic', 'fast', 'comprehensive', 'vuln'. Ejemplo: 'basic' o 'vuln -p 80,443'",
                func=network_tool.nmap_scan
            ),
            Tool(
                name="ping_host",
                description="Verifica conectividad básica con el host objetivo usando ping",
                func=network_tool.ping_host
            ),
            Tool(
                name="telnet_connect",
                description="Conecta a un puerto específico usando telnet para probar servicios. Ejemplo: '80' o '22'",
                func=network_tool.telnet_connect
            ),
            Tool(
                name="netcat_connect",
                description="Conecta usando netcat para pruebas de red avanzadas. Ejemplo: '80' o '443'",
                func=network_tool.netcat_connect
            ),
            Tool(
                name="check_service_availability",
                description="Verifica si el servicio objetivo está disponible y responde correctamente",
                func=network_tool.check_service_availability
            )
        ]
        
        # Crear prompt mejorado para el agente dinámico
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.react_prompt),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Usar el LLM pasado como parámetro
        llm = self.llm.llm
        
        # Crear agente
        agent = create_openai_tools_agent(llm, tools, prompt)
        
        # Crear el agente ReACT
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=15,
            return_intermediate_steps=True,
            handle_parsing_errors=True
        )
        
        return agent_executor
    

    
    def _create_dynamic_validation_query(self, hallazgo: Dict, vuln_number: int, target_url: str, pdf_analysis: Dict = None) -> str:
        """Crea la consulta para el agente ReACT dinámico."""
        
        # Extraer credenciales del análisis PDF si están disponibles
        credenciales_info = ""
        if pdf_analysis and 'datos_tecnicos' in pdf_analysis:
            datos_tecnicos = pdf_analysis['datos_tecnicos']
            if 'credenciales_utilizadas' in datos_tecnicos and datos_tecnicos['credenciales_utilizadas']:
                credenciales_info = "\n\n🔐 CREDENCIALES DISPONIBLES DEL REPORTE:\n"
                for nombre_cred, cred_data in datos_tecnicos['credenciales_utilizadas'].items():
                    if isinstance(cred_data, dict) and 'usuario' in cred_data and 'contrasena' in cred_data:
                        credenciales_info += f"- {nombre_cred}: {cred_data['usuario']}:{cred_data['contrasena']}\n"
                credenciales_info += "\nPuedes usar estas credenciales para autenticarte si la vulnerabilidad requiere acceso autenticado.\n"
        
        return f"""
VALIDA MEDIANTE EXPLOTACIÓN LA SIGUIENTE VULNERABILIDAD #{vuln_number}:

🎯 OBJETIVO: {target_url}
ID: {hallazgo.get('id', f'VULN-{vuln_number:03d}')}
Nombre: {hallazgo.get('nombre', 'Vulnerabilidad sin nombre')}
Categoría: {hallazgo.get('categoria', 'Desconocida')}
Descripción: {hallazgo.get('descripcion', 'Sin descripción')}
Severidad reportada: {hallazgo.get('severidad', 'Desconocida')}
Impacto: {hallazgo.get('impacto', 'Sin impacto definido')}
PoC: {hallazgo.get('detailed_proof_of_concept', 'Sin PoC proporcionado')}{credenciales_info}

CONTEXTO IMPORTANTE:
- Esta vulnerabilidad fue reportada en un análisis de seguridad
- El objetivo a probar es: {target_url}
- La conectividad ya fue verificada previamente - NO hagas ping
- Debes intentar replicar la explotación usando las técnicas descritas en el PoC
- Tu trabajo es confirmar si la vulnerabilidad existe y es explotable en el sistema en vivo

USA LA METODOLOGÍA ReACT PARA EXPLOTACIÓN DINÁMICA:
1. THOUGHT: Analiza el tipo de vulnerabilidad y las técnicas de explotación necesarias
2. ACTION: Usa las herramientas de red para intentar explotar la vulnerabilidad contra {target_url}
3. OBSERVATION: Documenta exactamente qué respuestas obtienes del servidor
4. CONCLUSION: Determina VULNERABLE o NO_VULNERABLE basado en la explotación exitosa

INSTRUCCIONES ESPECÍFICAS:
- Usa el mismo payload que se usó en el PoC, la idea es que repliques la explotación
- Si obtienes Status Code 0 y contenido en STDOUT, analiza el contenido para buscar indicadores de explotación
- Analiza las respuestas del servidor para buscar indicadores de explotación exitosa
- Si la explotación es exitosa, marca como VULNERABLE
- Solo marca NO_VULNERABLE si las pruebas de explotación fallan consistentemente
- IMPORTANTE: Todas las pruebas deben realizarse contra {target_url}

Comienza tu análisis de explotación ahora usando las herramientas de red disponibles.
"""
    
    def _parse_dynamic_agent_response(self, agent_response: Dict, hallazgo: Dict) -> Dict[str, Any]:
        """Parsea la respuesta del agente ReACT dinámico que debe estar en formato JSON."""
        output = agent_response.get('output', '')
        intermediate_steps = agent_response.get('intermediate_steps', [])
        
        # Mostrar los pasos intermedios para debugging
        print(f"    🔍 Pasos del agente:")
        for i, (action, observation) in enumerate(intermediate_steps):
            tool_name = getattr(action, 'tool', 'unknown')
            tool_input = getattr(action, 'tool_input', 'unknown')
            print(f"      Paso {i+1}: {tool_name} -> {str(observation)[:100]}...")
        
        # Valores por defecto
        estado = "no vulnerable"
        evidencia = "Sin evidencia de explotación exitosa encontrada"
        payload_usado = "No se pudo determinar"
        respuesta_servidor = "No se obtuvo respuesta relevante"
        nombre = hallazgo.get('categoria', 'Vulnerabilidad desconocida')  # Valor por defecto
        vuln_id = hallazgo.get('id', 'VULN-UNKNOWN')  # ID por defecto
        
        # Analizar si todas las peticiones curl fallaron con Status Code 3
        all_curl_failed = True
        successful_requests = 0
        
        for action, observation in intermediate_steps:
            if hasattr(action, 'tool') and action.tool == 'curl_request':
                obs_str = str(observation)
                if "Status Code: 0" in obs_str or "Status Code: 200" in obs_str:
                    all_curl_failed = False
                    successful_requests += 1
                elif "Status Code: 3" not in obs_str:
                    all_curl_failed = False
        
        try:
            # Buscar el JSON en la respuesta
            import re
            # Buscar JSON con o sin bloques de código
            json_match = re.search(r'```json\s*({.*?})\s*```', output, re.DOTALL)
            if not json_match:
                # Buscar JSON sin bloques de código - mejorado para capturar JSON completo
                # Buscar desde la primera llave hasta la llave de cierre balanceada
                start_pos = output.find('{')
                if start_pos != -1:
                    brace_count = 0
                    end_pos = start_pos
                    for i, char in enumerate(output[start_pos:], start_pos):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_pos = i + 1
                                break
                    if brace_count == 0:
                        json_str = output[start_pos:end_pos]
                        # Crear un match object simulado
                        class MockMatch:
                            def __init__(self, text):
                                self.text = text
                            def group(self, n):
                                return self.text
                        json_match = MockMatch(json_str)
            
            if json_match:
                json_str = json_match.group(1)
                print(f"    🔍 JSON encontrado: {json_str[:100]}...")
                try:
                    result = json.loads(json_str)
                    print(f"    🔍 JSON parseado exitosamente")
                except json.JSONDecodeError as e:
                    print(f"    ❌ Error parseando JSON: {e}")
                    print(f"    🔍 JSON completo: {json_str}")
                    raise
                
                # Extraer información del JSON
                estado = result.get('estado', 'no_vulnerable')
                print(f"    🔍 Estado extraído del JSON: '{estado}'")
                if estado == 'no_vulnerable':
                    estado = 'no vulnerable'
                elif estado == 'vulnerable':
                    estado = 'vulnerable'
                print(f"    🔍 Estado final después del procesamiento: '{estado}'")
                    
                evidencia = result.get('evidencia', evidencia)
                payload_usado = result.get('payload_usado', payload_usado)
                respuesta_servidor = result.get('respuesta_servidor', respuesta_servidor)
                # Extraer el nombre real de la vulnerabilidad del JSON de respuesta
                nombre = result.get('nombre', nombre)
                # Extraer el ID de la vulnerabilidad del JSON de respuesta
                vuln_id = result.get('id', vuln_id)
            else:
                print(f"    🔍 No se encontró JSON válido, usando lógica de fallback")
                # Si no hay JSON, analizar los pasos intermedios
                if all_curl_failed and len(intermediate_steps) > 0:
                    evidencia = "Todas las peticiones curl fallaron con Status Code 3 (error de conexión/DNS). El endpoint puede no existir o no estar accesible."
                    estado = "no vulnerable"
                    print(f"    🔍 Todos los curl fallaron, estado: '{estado}'")
                else:
                    # Fallback: buscar patrones simples si no hay JSON
                    output_lower = output.lower()
                    # Solo marcar como vulnerable si hay evidencia clara de explotación exitosa
                    # y NO hay indicadores de que no es vulnerable
                    if any(pattern in output_lower for pattern in ['explotación exitosa', 'exploit successful', 'vulnerability confirmed']):
                        if not any(pattern in output_lower for pattern in ['no vulnerable', 'no es vulnerable', 'exploit failed', 'not vulnerable']):
                            estado = "vulnerable"
                            print(f"    🔍 Patrón de éxito encontrado, estado: '{estado}'")
                    # Por defecto, mantener como no vulnerable si no hay evidencia clara
                    else:
                        estado = "no vulnerable"
                        print(f"    🔍 Sin evidencia clara, estado por defecto: '{estado}'")
                            
                    # Extraer evidencia de la respuesta completa como fallback
                    evidencia = output[:300] + "..." if len(output) > 300 else output
                
        except (json.JSONDecodeError, AttributeError) as e:
            # Si falla el parsing JSON, usar la respuesta completa como evidencia
            evidencia = f"Error parsing JSON response: {str(e)}. Raw output: {output[:300]}..."
        
        print(f"    🔍 Estado final antes del return: '{estado}'")
        return {
            "id": vuln_id,
            "nombre": nombre,
            "estado": estado,
            "severidad": hallazgo.get('severidad', 'media'),
            "detalles": output,
            "evidencia": evidencia,
            "payload_usado": payload_usado,
            "respuesta_servidor": respuesta_servidor
        }
    
    def _generate_final_result(self, pdf_analysis: Dict, validated_vulnerabilities: List[Dict]) -> Dict[str, Any]:
        """Genera el resultado final en el formato requerido."""
        
        vulnerables_count = sum(1 for v in validated_vulnerabilities if v['estado'] == 'vulnerable')
        total_reportadas = len(validated_vulnerabilities)
        
        return {
            'vulnerabilidades_reportadas': total_reportadas,
            'vulnerabilidades_vulnerables': vulnerables_count,
            'timestamp': datetime.now().isoformat(),
            'tipo_analisis': 'dinamico',
            'vulnerabilidades': validated_vulnerabilities
        }