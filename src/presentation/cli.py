import typer
import os
import time
import threading
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from ..infrastructure.utils.factory import get_factory
from ..infrastructure.utils.config import validate_environment, get_available_providers
from ..infrastructure.utils.llm_adapters import LLMFactory
from ..infrastructure.utils.mongodb_client import MongoDBClient
from ..domain.exceptions import (
    PDFAnalyzerException, PDFNotFoundError, InvalidPDFError, 
    PDFReadError, ReportAnalysisError, LLMConnectionError, JSONParsingError
)

app = typer.Typer(
    name="pdf-analyzer",
    help="Analizador de reportes PDF usando LangChain",
    add_completion=False
)
console = Console()


class LoadingSpinner:
    """Animación de carga personalizada con símbolos giratorios."""
    
    def __init__(self, message: str = "Procesando..."):
        self.message = message
        self.spinner_chars = ['|', '/', '—', '\\']
        self.running = False
        self.thread = None
        self.current_char_index = 0
    
    def _spin(self):
        """Ejecuta la animación en un hilo separado."""
        while self.running:
            char = self.spinner_chars[self.current_char_index]
            # Usar print estándar para evitar problemas con Rich markup
            print(f"\r\033[1;34m{char}\033[0m {self.message}", end="", flush=True)
            self.current_char_index = (self.current_char_index + 1) % len(self.spinner_chars)
            time.sleep(0.2)
    
    def start(self):
        """Inicia la animación."""
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Detiene la animación."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)
        # Limpiar la línea
        print("\r" + " " * (len(self.message) + 10), end="")
        print("\r", end="", flush=True)
    
    def update_message(self, new_message: str):
        """Actualiza el mensaje de la animación."""
        self.message = new_message
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


@app.command("read")
def read_pdf(
    pdf: str = typer.Option(
        ..., 
        "--pdf", 
        "-p", 
        help="Ruta al archivo PDF a analizar"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Archivo de salida para guardar el JSON (opcional)"
    ),
    model: str = typer.Option(
        "openai",
        "--model",
        "-m",
        help="Proveedor de LLM a utilizar (openai, xai, gemini, deepseek, anthropic) o formato 'proveedor:modelo'"
    ),
    temperature: float = typer.Option(
        0.1,
        "--temperature",
        "-t",
        help="Temperatura para el modelo (0.0 - 1.0)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Mostrar información detallada del proceso"
    ),
    mongodb: bool = typer.Option(
        False,
        "--mongodb",
        help="Guardar el resultado en MongoDB (requiere configuración en .env)"
    )
):
    """Lee y analiza un reporte PDF, generando un JSON estructurado."""
    
    try:
        # Validar que existe el archivo
        if not os.path.exists(pdf):
            console.print(f"[red]Error: El archivo {pdf} no existe[/red]")
            raise typer.Exit(1)
        
        # Parsear modelo
        try:
            provider, model_name = LLMFactory.parse_model_string(model)
        except Exception:
            console.print(f"[red]Error: Formato de modelo inválido: {model}[/red]")
            console.print("[yellow]Formato válido: 'proveedor' o 'proveedor:modelo'[/yellow]")
            console.print(f"[yellow]Proveedores soportados: {', '.join(LLMFactory.get_supported_providers())}[/yellow]")
            raise typer.Exit(1)
        
        # Validar configuración
        if not validate_environment(provider):
            available = get_available_providers()
            console.print(f"[red]Error: API key para {provider} no está configurada[/red]")
            console.print(f"[yellow]Formato usado: {model}[/yellow]")
            console.print(f"[yellow]Formato correcto: 'proveedor:modelo' (ej: openai:gpt-5-nano)[/yellow]")
            if available:
                console.print(f"[yellow]Proveedores disponibles: {', '.join(available)}[/yellow]")
            else:
                console.print("[yellow]Configure al menos una API key en el archivo .env[/yellow]")
            raise typer.Exit(1)
        
        if verbose:
            console.print(f"[blue]Procesando archivo: {pdf}[/blue]")
            console.print(f"[blue]Proveedor: {provider}[/blue]")
            console.print(f"[blue]Modelo: {model_name or 'por defecto'}[/blue]")
            console.print(f"[blue]Temperatura: {temperature}[/blue]")
        
        # Crear dependencias usando el factory
        with LoadingSpinner("Inicializando componentes...") as spinner:
            factory = get_factory()
            use_case = factory.create_read_pdf_use_case(
                provider=provider,
                model_name=model_name,
                temperature=temperature
            )
        
        console.print("[green]✓[/green] Componentes inicializados")
        
        # Ejecutar análisis con animación
        with LoadingSpinner("Leyendo archivo PDF...") as spinner:
            time.sleep(0.5)  # Simular tiempo de lectura
            spinner.update_message("Enviando contenido al modelo de IA...")
            time.sleep(0.5)
            spinner.update_message("Analizando estructura del reporte...")
            time.sleep(0.5)
            spinner.update_message("Generando JSON estructurado...")
            
            # Ejecutar análisis
            result_json = use_case.execute_as_json(pdf)
        
        console.print("[green]✓[/green] Análisis completado")
        
        # Guardar en MongoDB si se especifica
        if mongodb:
            try:
                with LoadingSpinner("Guardando en MongoDB...") as spinner:
                    mongo_client = MongoDBClient()
                    mongo_client.connect()
                    
                    # Crear metadatos adicionales
                    metadata = {
                        'provider': provider,
                        'model': model_name or 'default',
                        'temperature': temperature,
                        'analysis_version': '1.0.0'
                    }
                    
                    document_id = mongo_client.save_report(pdf, result_json, metadata)
                    mongo_client.disconnect()
                    
                console.print(f"[green]✓ Resultado guardado en MongoDB con ID: {document_id}[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠ Error guardando en MongoDB: {str(e)}[/yellow]")
                console.print("[yellow]Continuando con el procesamiento normal...[/yellow]")
        
        # Mostrar resultado
        if output:
            # Guardar en archivo
            with open(output, 'w', encoding='utf-8') as f:
                f.write(result_json)
            console.print(f"[green]✓ Resultado guardado en: {output}[/green]")
            
            if verbose:
                # Mostrar preview del JSON
                syntax = Syntax(result_json[:500] + "...", "json", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title="Preview del resultado", border_style="green"))
        else:
            # Mostrar en consola
            syntax = Syntax(result_json, "json", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title="Resultado del análisis", border_style="green"))
        
        console.print("[green]✓ Análisis completado exitosamente[/green]")
        
    except PDFNotFoundError as e:
        console.print(f"[red]Archivo no encontrado: {str(e)}[/red]")
        raise typer.Exit(1)
    except InvalidPDFError as e:
        console.print(f"[red]Archivo PDF inválido: {str(e)}[/red]")
        raise typer.Exit(1)
    except PDFReadError as e:
        console.print(f"[red]Error leyendo PDF: {str(e)}[/red]")
        raise typer.Exit(1)
    except LLMConnectionError as e:
        console.print(f"[red]Error de conexión con OpenAI: {str(e)}[/red]")
        console.print("[yellow]Verifica tu API key y conexión a internet[/yellow]")
        raise typer.Exit(1)
    except JSONParsingError as e:
        console.print(f"[red]Error procesando respuesta: {str(e)}[/red]")
        console.print("[yellow]El modelo puede haber generado una respuesta inválida[/yellow]")
        raise typer.Exit(1)
    except ReportAnalysisError as e:
        console.print(f"[red]Error analizando reporte: {str(e)}[/red]")
        raise typer.Exit(1)
    except PDFAnalyzerException as e:
        console.print(f"[red]Error de la aplicación: {str(e)}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error inesperado: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command("version")
def version():
    """Muestra la versión de la aplicación."""
    console.print("[blue]PDF Analyzer v1.0.0[/blue]")
    console.print("[dim]Analizador de reportes PDF usando LangChain y OpenAI[/dim]")


@app.command("test")
def test_connection(
    model: str = typer.Option(
        "openai",
        "--model",
        "-m",
        help="Proveedor de LLM a probar (openai, xai, gemini, deepseek, anthropic) o formato 'proveedor:modelo'"
    )
):
    """Prueba la conexión con el proveedor de LLM especificado."""
    try:
        # Parsear modelo
        try:
            provider, model_name = LLMFactory.parse_model_string(model)
        except Exception:
            console.print(f"[red]Error: Formato de modelo inválido: {model}[/red]")
            console.print("[yellow]Formato válido: 'proveedor' o 'proveedor:modelo'[/yellow]")
            console.print(f"[yellow]Proveedores soportados: {', '.join(LLMFactory.get_supported_providers())}[/yellow]")
            raise typer.Exit(1)
        
        # Validar configuración
        if not validate_environment(provider):
            available = get_available_providers()
            console.print(f"[red]Error: API key para {provider} no está configurada[/red]")
            console.print(f"[yellow]Formato usado: {model}[/yellow]")
            console.print(f"[yellow]Formato correcto: 'proveedor:modelo' (ej: openai:gpt-4o-mini)[/yellow]")
            if available:
                console.print(f"[yellow]Proveedores disponibles: {', '.join(available)}[/yellow]")
            else:
                console.print("[yellow]Configure al menos una API key en el archivo .env[/yellow]")
            raise typer.Exit(1)
        
        with LoadingSpinner(f"Probando conexión con {provider}...") as spinner:
            factory = get_factory()
            llm = factory.create_llm(provider=provider, model_name=model_name)
            display_model = model_name or f"{provider} (modelo por defecto)"
            spinner.update_message(f"Enviando mensaje de prueba a {display_model}...")
            response = llm.generate_response(
                "Responde únicamente con 'OK' si puedes procesar este mensaje.",
                "Test de conexión"
            )
        
        if "OK" in response.upper():
            console.print(f"[green]✓ Conexión exitosa con {display_model}[/green]")
        else:
            console.print(f"[yellow]⚠ Respuesta inesperada: {response}[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error de conexión: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command("static-scan")
def static_scan(
    pdf: str = typer.Option(
        ..., 
        "--pdf", 
        "-p", 
        help="Ruta al archivo PDF del reporte a validar"
    ),
    source: str = typer.Option(
        ...,
        "--source",
        "-s",
        help="Ruta al código fuente a analizar"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Archivo de salida para guardar el JSON (opcional)"
    ),
    model: str = typer.Option(
        "openai",
        "--model",
        "-m",
        help="Proveedor de LLM a utilizar (openai, xai, gemini, deepseek, anthropic) o formato 'proveedor:modelo'"
    ),
    temperature: float = typer.Option(
        0.1,
        "--temperature",
        "-t",
        help="Temperatura para el modelo (0.0 - 1.0)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Mostrar información detallada del proceso"
    ),
    mongodb: bool = typer.Option(
        False,
        "--mongodb",
        help="Guardar el resultado en MongoDB (requiere configuración en .env)"
    )
):
    """Valida vulnerabilidades de un reporte PDF mediante análisis estático con semgrep."""
    
    try:
        # Validar que existen los archivos/directorios
        if not os.path.exists(pdf):
            console.print(f"[red]Error: El archivo PDF {pdf} no existe[/red]")
            raise typer.Exit(1)
        
        if not os.path.exists(source):
            console.print(f"[red]Error: El directorio de código fuente {source} no existe[/red]")
            raise typer.Exit(1)
        
        # Parsear modelo
        try:
            provider, model_name = LLMFactory.parse_model_string(model)
        except Exception:
            console.print(f"[red]Error: Formato de modelo inválido: {model}[/red]")
            raise typer.Exit(1)
        
        # Validar que el proveedor está disponible
        available_providers = get_available_providers()
        if provider not in available_providers:
            console.print(f"[red]Error: Proveedor {provider} no está configurado[/red]")
            console.print(f"[yellow]Proveedores disponibles: {', '.join(available_providers)}[/yellow]")
            raise typer.Exit(1)
        
        if verbose:
            console.print(f"[blue]📄 Archivo PDF: {pdf}[/blue]")
            console.print(f"[blue]📁 Código fuente: {source}[/blue]")
            console.print(f"[blue]🤖 Modelo: {provider}:{model_name}[/blue]")
            console.print(f"[blue]🌡️  Temperatura: {temperature}[/blue]")
        
        # Crear agente de análisis estático
        factory = get_factory()
        
        with LoadingSpinner("Inicializando agente de análisis estático...") as spinner:
            llm = factory.create_llm(provider, model_name, temperature)
            static_agent = factory.create_static_analysis_agent(llm)
            
            spinner.update_message("Validando vulnerabilidades...")
            result = static_agent.validate_vulnerabilities(pdf, source)
        
        # Mostrar resumen
        console.print("\n[green]✓ Análisis estático completado[/green]")
        console.print(f"[blue]📊 Vulnerabilidades reportadas: {result['vulnerabilidades_reportadas']}[/blue]")
        console.print(f"[blue]🔍 Vulnerabilidades confirmadas: {result['vulnerabilidades_vulnerables']}[/blue]")
        console.print(f"[blue]⏰ Timestamp: {result['timestamp']}[/blue]")
        
        # Mostrar detalles de vulnerabilidades si es verbose
        if verbose:
            console.print("\n[yellow]📋 Detalles de vulnerabilidades:[/yellow]")
            for i, vuln in enumerate(result['vulnerabilidades'], 1):
                estado_color = "red" if vuln['estado'] == 'vulnerable' else "green"
                console.print(f"\n{i}. [bold]{vuln['nombre']}[/bold]")
                console.print(f"   Estado: [{estado_color}]{vuln['estado']}[/{estado_color}]")
                console.print(f"   Severidad: {vuln['severidad']}")
                if vuln['evidencia'] != 'No disponible' and vuln['evidencia'] != 'No se encontró evidencia':
                    console.print(f"   Evidencia: {vuln['evidencia'][:100]}...")
        
        # Guardar resultado en archivo si se especifica
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                import json
                json.dump(result, f, indent=2, ensure_ascii=False)
            console.print(f"[green]💾 Resultado guardado en: {output}[/green]")
        
        # Guardar en MongoDB si se especifica
        if mongodb:
            try:
                with LoadingSpinner("Guardando en MongoDB...") as spinner:
                    mongo_client = MongoDBClient()
                    mongo_client.connect()
                    import json
                    result_json = json.dumps(result, indent=2, ensure_ascii=False)
                    document_id = mongo_client.save_report(
                        pdf, 
                        result_json,
                        {
                            'pdf_file': pdf,
                            'source_path': source,
                            'model': f"{provider}:{model_name}",
                            'temperature': temperature,
                            'analysis_type': 'static_scan'
                        }
                    )
                    mongo_client.disconnect()
                console.print(f"[green]💾 Resultado guardado en MongoDB con ID: {document_id}[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️  Error guardando en MongoDB: {str(e)}[/yellow]")
        
        # Mostrar resultado en formato JSON si no es verbose
        if not verbose and not output:
            import json
            syntax = Syntax(json.dumps(result, indent=2, ensure_ascii=False), "json", theme="monokai")
            console.print("\n[yellow]📄 Resultado del análisis:[/yellow]")
            console.print(syntax)
            
    except (PDFNotFoundError, InvalidPDFError, PDFReadError, ReportAnalysisError, LLMConnectionError, JSONParsingError) as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operación cancelada por el usuario[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error inesperado: {str(e)}[/red]")
        if verbose:
            import traceback
            console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
        raise typer.Exit(1)


@app.command("dynamic-scan")
def dynamic_scan(
    pdf: str = typer.Option(
        ..., 
        "--pdf", 
        "-p", 
        help="Ruta al archivo PDF del reporte a validar"
    ),
    url: str = typer.Option(
        ...,
        "--url",
        "-u",
        help="URL del objetivo a probar (ej: http://localhost:8080)"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Archivo de salida para guardar el JSON (opcional)"
    ),
    model: str = typer.Option(
        "openai",
        "--model",
        "-m",
        help="Proveedor de LLM a utilizar (openai, xai, gemini, deepseek, anthropic) o formato 'proveedor:modelo'"
    ),
    temperature: float = typer.Option(
        0.1,
        "--temperature",
        "-t",
        help="Temperatura para el modelo (0.0 - 1.0)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Mostrar información detallada del proceso"
    ),
    mongodb: bool = typer.Option(
        False,
        "--mongodb",
        help="Guardar el resultado en MongoDB (requiere configuración en .env)"
    )
):
    """Valida vulnerabilidades mediante análisis dinámico y explotación en vivo."""
    
    try:
        # Validar que existe el archivo PDF
        if not os.path.exists(pdf):
            console.print(f"[red]Error: El archivo {pdf} no existe[/red]")
            raise typer.Exit(1)
        
        # Validar formato de URL
        if not url.startswith(('http://', 'https://')):
            console.print(f"[red]Error: La URL debe comenzar con http:// o https://[/red]")
            raise typer.Exit(1)
        
        # Parsear modelo
        try:
            provider, model_name = LLMFactory.parse_model_string(model)
        except Exception:
            console.print(f"[red]Error: Formato de modelo inválido: {model}[/red]")
            console.print("[yellow]Formato válido: 'proveedor' o 'proveedor:modelo'[/yellow]")
            console.print(f"[yellow]Proveedores soportados: {', '.join(LLMFactory.get_supported_providers())}[/yellow]")
            raise typer.Exit(1)
        
        # Validar configuración
        if not validate_environment(provider):
            available = get_available_providers()
            console.print(f"[red]Error: API key para {provider} no está configurada[/red]")
            console.print(f"[yellow]Formato usado: {model}[/yellow]")
            console.print(f"[yellow]Formato correcto: 'proveedor:modelo' (ej: openai:gpt-4)[/yellow]")
            if available:
                console.print(f"[yellow]Proveedores disponibles: {', '.join(available)}[/yellow]")
            else:
                console.print("[yellow]Configure al menos una API key en el archivo .env[/yellow]")
            raise typer.Exit(1)
        
        if verbose:
            console.print(f"[blue]📄 Archivo PDF: {pdf}[/blue]")
            console.print(f"[blue]🌐 Objetivo: {url}[/blue]")
            console.print(f"[blue]🤖 Modelo: {provider}:{model_name or 'por defecto'}[/blue]")
            console.print(f"[blue]🌡️  Temperatura: {temperature}[/blue]")
        
        # Crear dependencias usando el factory
        with LoadingSpinner("Inicializando agente dinámico...") as spinner:
            factory = get_factory()
            llm = factory.create_llm(
                provider=provider,
                model_name=model_name,
                temperature=temperature
            )
            
            # Importar y crear el agente dinámico
            from ..infrastructure.agents.dynamic_agent import DynamicAnalysisAgent
            dynamic_agent = DynamicAnalysisAgent(llm)
            
            spinner.update_message("Ejecutando análisis dinámico...")
        
        # Ejecutar validación dinámica
        result = dynamic_agent.validate_vulnerabilities(pdf, url)
        
        # Mostrar resumen
        console.print("\n[green]✓ Análisis dinámico completado[/green]")
        console.print(f"[blue]📊 Vulnerabilidades reportadas: {result['vulnerabilidades_reportadas']}[/blue]")
        console.print(f"[blue]🔍 Vulnerabilidades confirmadas: {result['vulnerabilidades_vulnerables']}[/blue]")
        console.print(f"[blue]⏰ Timestamp: {result['timestamp']}[/blue]")
        
        # Mostrar detalles de vulnerabilidades si es verbose
        if verbose:
            console.print("\n[yellow]📋 Detalles de vulnerabilidades:[/yellow]")
            for i, vuln in enumerate(result['vulnerabilidades'], 1):
                estado_color = "red" if vuln['estado'] == 'vulnerable' else "green"
                console.print(f"\n{i}. [bold]{vuln['nombre']}[/bold]")
                console.print(f"   Estado: [{estado_color}]{vuln['estado']}[/{estado_color}]")
                console.print(f"   Severidad: {vuln['severidad']}")
                if vuln.get('evidencia') and vuln['evidencia'] not in ['No disponible', 'No se encontró evidencia']:
                    console.print(f"   Evidencia: {vuln['evidencia'][:100]}...")
                if vuln.get('payload_usado'):
                    console.print(f"   Payload usado: {vuln['payload_usado']}")
                if vuln.get('respuesta_servidor'):
                    console.print(f"   Respuesta del servidor: {vuln['respuesta_servidor'][:100]}...")
        
        # Guardar en archivo si se especifica
        if output:
            import json
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            console.print(f"[green]Resultado guardado en: {output}[/green]")
        
        # Guardar en MongoDB si se especifica
        if mongodb:
            try:
                with LoadingSpinner("Guardando en MongoDB...") as spinner:
                    client = MongoDBClient()
                    doc_id = client.save_analysis_result(
                        result, 
                        {
                            'tipo_analisis': 'dinamico',
                            'pdf_path': pdf,
                            'target_url': url,
                            'model': model,
                            'temperature': temperature
                        }
                    )
                console.print(f"[green]Resultado guardado en MongoDB con ID: {doc_id}[/green]")
            except Exception as e:
                console.print(f"[yellow]Advertencia: No se pudo guardar en MongoDB: {str(e)}[/yellow]")
        
        
    except PDFAnalyzerException as e:
        console.print(f"[red]Error del analizador: {str(e)}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error inesperado: {str(e)}[/red]")
        if verbose:
            import traceback
            console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
        raise typer.Exit(1)


@app.command("test-mongodb")
def test_mongodb():
    """Prueba la conexión con MongoDB."""
    try:
        with LoadingSpinner("Probando conexión con MongoDB...") as spinner:
            mongo_client = MongoDBClient()
            success = mongo_client.test_connection()
            
        if success:
            console.print("[green]✓ Conexión exitosa con MongoDB[/green]")
            console.print(f"[blue]Base de datos: {mongo_client.database_name}[/blue]")
            console.print(f"[blue]Colección: {mongo_client.collection_name}[/blue]")
        else:
            console.print("[red]✗ Error conectando con MongoDB[/red]")
            console.print("[yellow]Verifica la configuración en .env y que MongoDB esté ejecutándose[/yellow]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error de conexión con MongoDB: {str(e)}[/red]")
        console.print("[yellow]Verifica que MongoDB esté ejecutándose y la configuración en .env[/yellow]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()