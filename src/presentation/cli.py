import typer
import os
import time
import threading
import json
from typing import Optional
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
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
        
        # Mostrar información del reporte y modelo
        console.print(f"📄 Reporte: {pdf}")
        console.print(f"🤖 Modelo: {model_name or 'por defecto'}")
        
        if verbose:
            console.print(f"[blue]📄 Procesando archivo: {pdf}[/blue]")
            console.print(f"[blue]🤖 Modelo: {model_name or 'por defecto'}[/blue]")
            console.print(f"[blue]🌡️ Temperatura: {temperature}[/blue]")
        
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
            from ..infrastructure.services.agents.dynamic_agent import DynamicAnalysisAgent
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
                    client.connect()
                    doc_id = client.save_report(
                        pdf,
                        json.dumps(result, ensure_ascii=False),
                        {
                            'tipo_analisis': 'dinamico',
                            'pdf_path': pdf,
                            'target_url': url,
                            'model': model,
                            'temperature': temperature
                        }
                    )
                    client.disconnect()
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


def _display_complete_analysis_report(complete_analysis: dict):
    """Muestra el reporte completo de análisis con formato bonito para triage_final."""
    
    # Título principal
    console.print("\n[bold green]🎯 ANÁLISIS COMPLETO DE SEGURIDAD[/bold green]")
    console.print("=" * 70)
    
    # Información del triage final
    triage_final = complete_analysis.get('triage_final', {})
    
    if triage_final:
        # Header del triage
        console.print(f"\n[bold blue]📊 TRIAGE FINAL DE VULNERABILIDADES[/bold blue]")
        console.print(f"[dim]ID Reporte: {triage_final.get('id_reporte', 'N/A')}[/dim]")
        console.print(f"[dim]Fecha: {triage_final.get('fecha_generacion', 'N/A')}[/dim]")
        console.print(f"[dim]Origen: {triage_final.get('reporte_origen', 'N/A')}[/dim]")
        
        # Resumen ejecutivo
        if triage_final.get('resumen_triage'):
            console.print(f"\n[bold cyan]📋 Resumen Ejecutivo[/bold cyan]")
            resumen_lines = triage_final['resumen_triage'].split('\n')
            for line in resumen_lines:
                if line.strip():
                    console.print(f"  {line.strip()}")
        
        # Estadísticas en tabla
        console.print(f"\n[bold cyan]📈 Estadísticas de Vulnerabilidades[/bold cyan]")
        
        # Tabla de distribución por severidad
        severity_table = Table(title="Distribución por Severidad", show_header=True, header_style="bold magenta")
        severity_table.add_column("Severidad", style="bold")
        severity_table.add_column("Cantidad", justify="center")
        severity_table.add_column("Porcentaje", justify="center")
        
        dist_sev = triage_final.get('distribucion_severidad', {})
        total_vulns = triage_final.get('total_vulnerabilidades', 0)
        
        severity_colors = {
            'crítica': 'red',
            'alta': 'orange1',
            'media': 'yellow',
            'baja': 'green',
            'informativa': 'blue'
        }
        
        for sev, count in dist_sev.items():
            if count > 0:
                percentage = (count / total_vulns * 100) if total_vulns > 0 else 0
                color = severity_colors.get(sev, 'white')
                severity_table.add_row(
                    f"[{color}]{sev.upper()}[/{color}]",
                    f"[{color}]{count}[/{color}]",
                    f"[{color}]{percentage:.1f}%[/{color}]"
                )
        
        console.print(severity_table)
        
        # Tabla de distribución por prioridad
        priority_table = Table(title="Distribución por Prioridad", show_header=True, header_style="bold magenta")
        priority_table.add_column("Prioridad", style="bold")
        priority_table.add_column("Cantidad", justify="center")
        priority_table.add_column("Descripción", style="dim")
        
        dist_pri = triage_final.get('distribucion_prioridad', {})
        priority_descriptions = {
            'P0': 'Crítica - Acción inmediata',
            'P1': 'Urgente - Resolver en 24h',
            'P2': 'Alta - Resolver en 1 semana',
            'P3': 'Media - Resolver en 1 mes',
            'P4': 'Baja - Resolver cuando sea posible'
        }
        
        priority_colors = {
            'P0': 'red',
            'P1': 'orange1',
            'P2': 'yellow',
            'P3': 'green',
            'P4': 'blue'
        }
        
        for pri, count in dist_pri.items():
            if count > 0:
                color = priority_colors.get(pri, 'white')
                desc = priority_descriptions.get(pri, 'N/A')
                priority_table.add_row(
                    f"[{color}]{pri}[/{color}]",
                    f"[{color}]{count}[/{color}]",
                    f"[dim]{desc}[/dim]"
                )
        
        console.print(priority_table)
        
        # Vulnerabilidades detalladas
        vulnerabilidades = triage_final.get('vulnerabilidades', [])
        if vulnerabilidades:
            console.print(f"\n[bold cyan]🔍 Vulnerabilidades Detalladas[/bold cyan]")
            
            # Ordenar vulnerabilidades por prioridad (P0, P1, P2, etc.)
            priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4}
            vulnerabilidades_ordenadas = sorted(
                vulnerabilidades, 
                key=lambda v: priority_order.get(v.get('prioridad', 'P4'), 999)
            )
            
            for i, vuln in enumerate(vulnerabilidades_ordenadas, 1):
                # Panel para cada vulnerabilidad
                severity = vuln.get('severidad_triage', 'N/A')
                priority = vuln.get('prioridad', 'N/A')
                estado = vuln.get('estado_vulnerabilidad', 'N/A')
                
                # Colores según severidad
                severity_color = severity_colors.get(severity, 'white')
                priority_color = priority_colors.get(priority, 'white')
                estado_color = 'red' if estado == 'vulnerable' else 'green' if estado == 'no_vulnerable' else 'yellow'
                
                # Crear panel para cada vulnerabilidad
                vuln_content = f"""[bold]ID:[/bold] {vuln.get('id_vulnerabilidad', 'N/A')}
[bold]Severidad:[/bold] [{severity_color}]{severity.upper()}[/{severity_color}] | [bold]Prioridad:[/bold] [{priority_color}]{priority}[/{priority_color}] | [bold]Estado:[/bold] [{estado_color}]{estado.upper()}[/{estado_color}]

[bold]Descripción:[/bold]
{vuln.get('descripcion_original', 'N/A')}

[bold]Justificación de Severidad:[/bold]
{vuln.get('justificacion_severidad', 'N/A')}

[bold]Impacto Real:[/bold]
{vuln.get('impacto_real', 'N/A')}"""
                
                if vuln.get('explicacion_estado'):
                    vuln_content += f"\n\n[bold]Explicación del Estado:[/bold]\n{vuln.get('explicacion_estado', '')}"
                
                # Evidencias
                evidencias = vuln.get('evidencias', [])
                if evidencias:
                    vuln_content += "\n\n[bold]Evidencias:[/bold]"
                    for j, evidencia in enumerate(evidencias[:2], 1):  # Mostrar máximo 2 evidencias
                        vuln_content += f"\n  {j}. {evidencia.get('descripcion', 'N/A')}"
                        if evidencia.get('ubicacion'):
                            vuln_content += f" ([dim]{evidencia.get('ubicacion')}[/dim])"
                
                # Recomendaciones
                recomendaciones = vuln.get('recomendaciones', [])
                if recomendaciones:
                    vuln_content += "\n\n[bold]Recomendaciones:[/bold]"
                    for j, rec in enumerate(recomendaciones[:2], 1):  # Mostrar máximo 2 recomendaciones
                        vuln_content += f"\n  {j}. [{rec.get('tipo', 'general').upper()}] {rec.get('descripcion', 'N/A')}"
                
                panel = Panel(
                    vuln_content,
                    title=f"[bold]{i}. {vuln.get('nombre', 'Vulnerabilidad sin nombre')}[/bold]",
                    border_style=severity_color,
                    padding=(1, 2)
                )
                console.print(panel)
    
    # Información adicional
    metadata = complete_analysis.get('metadata', {})
    if metadata:
        console.print(f"\n[bold cyan]ℹ️  Información del Análisis[/bold cyan]")
        console.print(f"[dim]• Fecha: {metadata.get('fecha_analisis', 'N/A')}[/dim]")
        console.print(f"[dim]• Versión: {metadata.get('version_pipeline', 'N/A')}[/dim]")
        console.print(f"[dim]• Modelo: {metadata.get('modelo_usado', 'N/A')}[/dim]")
        console.print(f"[dim]• Temperatura: {metadata.get('temperatura', 'N/A')}[/dim]")
        
        archivos = metadata.get('archivos_analizados', {})
        if archivos:
            console.print(f"[dim]• PDF: {archivos.get('pdf', 'N/A')}[/dim]")
            console.print(f"[dim]• Código fuente: {archivos.get('codigo_fuente', 'N/A')}[/dim]")
            console.print(f"[dim]• URL objetivo: {archivos.get('url_objetivo', 'N/A')}[/dim]")
    
    console.print(f"\n[dim]💡 Tip: Use --output para guardar el reporte completo en un archivo JSON[/dim]")


def _display_triage_report(json_result: str):
    """Muestra el reporte de triage de manera formateada y legible (función legacy)."""
    import json
    
    try:
        data = json.loads(json_result)
        
        # Título principal
        console.print("\n[bold green]📊 REPORTE DE TRIAGE DE VULNERABILIDADES[/bold green]")
        console.print("=" * 60)
        
        # Información general
        if 'resumen' in data:
            resumen = data['resumen']
            console.print(f"\n[bold blue]📋 Resumen General[/bold blue]")
            console.print(f"• Total de vulnerabilidades: [yellow]{resumen.get('total_vulnerabilidades', 'N/A')}[/yellow]")
            console.print(f"• Críticas: [red]{resumen.get('criticas', 0)}[/red]")
            console.print(f"• Altas: [orange1]{resumen.get('altas', 0)}[/orange1]")
            console.print(f"• Medias: [yellow]{resumen.get('medias', 0)}[/yellow]")
            console.print(f"• Bajas: [green]{resumen.get('bajas', 0)}[/green]")
            console.print(f"• Informativas: [blue]{resumen.get('informativas', 0)}[/blue]")
        
        # Vulnerabilidades detalladas
        if 'vulnerabilidades' in data:
            console.print(f"\n[bold blue]🔍 Vulnerabilidades Analizadas[/bold blue]")
            
            for i, vuln in enumerate(data['vulnerabilidades'], 1):
                # Panel para cada vulnerabilidad
                severity = vuln.get('severidad_triage', vuln.get('severidad', 'N/A'))
                priority = vuln.get('prioridad', 'N/A')
                
                # Colores según severidad
                severity_colors = {
                    'Critical': 'red',
                    'High': 'orange1', 
                    'Medium': 'yellow',
                    'Low': 'green',
                    'Informational': 'blue'
                }
                severity_color = severity_colors.get(severity, 'white')
                
                console.print(f"\n[bold]{i}. {vuln.get('nombre', 'Sin nombre')}[/bold]")
                console.print(f"   [bold]Severidad:[/bold] [{severity_color}]{severity}[/{severity_color}] | [bold]Prioridad:[/bold] [cyan]{priority}[/cyan]")
                
                if vuln.get('descripcion'):
                    console.print(f"   [bold]Descripción:[/bold] {vuln['descripcion'][:100]}{'...' if len(vuln['descripcion']) > 100 else ''}")
                
                if vuln.get('evidencia'):
                    console.print(f"   [bold]Evidencia:[/bold] {vuln['evidencia'][:100]}{'...' if len(vuln['evidencia']) > 100 else ''}")
                
                if vuln.get('recomendaciones'):
                    console.print(f"   [bold]Recomendaciones:[/bold] {vuln['recomendaciones'][:100]}{'...' if len(vuln['recomendaciones']) > 100 else ''}")
                
                console.print("   " + "-" * 50)
        
        # Mostrar JSON completo si se desea (opcional)
        console.print(f"\n[dim]💡 Tip: Use --output para guardar el reporte completo en un archivo[/dim]")
        
    except json.JSONDecodeError:
        console.print("[red]❌ Error: No se pudo parsear el JSON del reporte[/red]")
        # Fallback al formato original
        syntax = Syntax(json_result, "json", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="📊 Reporte de Triage (JSON)", border_style="green"))
    except Exception as e:
        console.print(f"[red]❌ Error mostrando el reporte: {str(e)}[/red]")
        # Fallback al formato original
        syntax = Syntax(json_result, "json", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="📊 Reporte de Triage (JSON)", border_style="green"))


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


@app.command("triage")
def triage_vulnerabilities(
    report: str = typer.Option(
        ..., 
        "--report", 
        "-r", 
        help="Ruta al archivo JSON del reporte de seguridad a procesar"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Archivo de salida para guardar el reporte de triage (opcional)"
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
    """Realiza triage de vulnerabilidades desde un reporte JSON."""
    try:
        # Verificar que el archivo existe
        if not os.path.exists(report):
            console.print(f"[red]❌ El archivo {report} no existe[/red]")
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
            if available:
                console.print(f"[yellow]Proveedores disponibles: {', '.join(available)}[/yellow]")
            else:
                console.print("[yellow]Configure al menos una API key en el archivo .env[/yellow]")
            raise typer.Exit(1)
        
        console.print(f"[blue]🎯 Iniciando triage de vulnerabilidades...[/blue]")
        console.print(f"[blue]📄 Archivo: {report}[/blue]")
        console.print(f"[blue]🤖 Modelo: {model}[/blue]")
        
        with LoadingSpinner("Cargando reporte de seguridad..."):
            # Cargar reporte JSON
            import json
            with open(report, 'r', encoding='utf-8') as f:
                security_report = json.load(f)
        
        with LoadingSpinner("Inicializando agente de triage..."):
            # Crear factory y obtener LLM
            factory = get_factory()
            llm_adapter = factory.create_llm(provider, model_name, temperature)
            
            # Crear caso de uso de triage
            from ..application.use_cases import TriageVulnerabilitiesUseCase
            triage_use_case = TriageVulnerabilitiesUseCase(llm_adapter)
        
        with LoadingSpinner("Realizando análisis de triage..."):
            # Ejecutar triage
            if output:
                result_path = triage_use_case.execute_and_export(security_report, output)
                console.print(f"[green]✅ Triage completado y guardado en: {result_path}[/green]")
            else:
                result = triage_use_case.execute_as_json(security_report)
                console.print("[green]✅ Triage completado[/green]")
                
                # Mostrar resultado formateado
                _display_triage_report(result)
        
        # Guardar en MongoDB si se solicita
        if mongodb:
            try:
                with LoadingSpinner("Guardando en MongoDB..."):
                    client = MongoDBClient()
                    client.connect()
                    triage_data = triage_use_case.execute(security_report)
                    
                    import json
                    result_json = json.dumps(triage_data, indent=2, ensure_ascii=False)
                    document_id = client.save_report(
                        report, 
                        result_json,
                        {
                            'report_file': report,
                            'model': f"{provider}:{model_name}",
                            'temperature': temperature,
                            'analysis_type': 'triage'
                        }
                    )
                    client.disconnect()
                    console.print(f"[green]✅ Guardado en MongoDB con ID: {document_id}[/green]")
                    
            except Exception as e:
                console.print(f"[yellow]⚠️ Error guardando en MongoDB: {str(e)}[/yellow]")
        
    except (ReportAnalysisError, LLMConnectionError, JSONParsingError) as e:
        console.print(f"[red]❌ Error de análisis: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error inesperado: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command("complete-analysis")
def complete_analysis(
    pdf: str = typer.Option(
        ..., 
        "--pdf", 
        "-p", 
        help="Ruta al archivo PDF del reporte a analizar"
    ),
    source: str = typer.Option(
        ...,
        "--source",
        "-s",
        help="Ruta al código fuente a analizar"
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
    """Realiza análisis completo: PDF + Análisis Estático + Análisis Dinámico + Triage de vulnerabilidades."""
    try:
        # Verificar que los archivos y directorios existen
        if not os.path.exists(pdf):
            console.print(f"[red]❌ El archivo PDF {pdf} no existe[/red]")
            raise typer.Exit(1)
        
        if not os.path.exists(source):
            console.print(f"[red]❌ El directorio de código fuente {source} no existe[/red]")
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
            if available:
                console.print(f"[yellow]Proveedores disponibles: {', '.join(available)}[/yellow]")
            else:
                console.print("[yellow]Configure al menos una API key en el archivo .env[/yellow]")
            raise typer.Exit(1)
        
        console.print(f"[blue]🔍 Iniciando análisis completo de seguridad...[/blue]")
        console.print(f"[blue]📄 PDF: {pdf}[/blue]")
        console.print(f"[blue]📁 Código fuente: {source}[/blue]")
        console.print(f"[blue]🌐 URL objetivo: {url}[/blue]")
        console.print(f"[blue]🤖 Modelo: {model}[/blue]")
        
        with LoadingSpinner("Inicializando componentes..."):
            # Crear factory y componentes
            factory = get_factory()
            llm_adapter = factory.create_llm(provider, model_name, temperature)
            
            # Importar agentes
            from ..infrastructure.services.agents.static_agent import StaticAnalysisAgent
            from ..infrastructure.services.agents.dynamic_agent import DynamicAnalysisAgent
            from ..infrastructure.services.agents.triage_agent import TriageAgent
        
        # Paso 1: Análisis del PDF
        console.print("[blue]📄 Paso 1: Analizando reporte PDF...[/blue]")
        with LoadingSpinner("Analizando PDF..."):
            pdf_reader = factory.create_pdf_reader()
            report_analyzer = factory.create_report_analyzer(llm_adapter)
            pdf_document = pdf_reader.read_pdf(pdf)
            pdf_analysis = report_analyzer.analyze_content(pdf_document.content)
            pdf_result = pdf_analysis.model_dump()
        
        console.print(f"[green]✅ PDF analizado: {len(pdf_result.get('hallazgos_principales', []))} vulnerabilidades encontradas[/green]")
        
        # Paso 2: Análisis Estático
        console.print("[blue]🔍 Paso 2: Ejecutando análisis estático...[/blue]")
        with LoadingSpinner("Ejecutando análisis estático..."):
            static_agent = StaticAnalysisAgent(llm_adapter)
            static_result = static_agent.validate_vulnerabilities(pdf, source)
        
        console.print(f"[green]✅ Análisis estático completado: {static_result.get('vulnerabilidades_vulnerables', 0)}/{static_result.get('vulnerabilidades_reportadas', 0)} vulnerabilidades confirmadas[/green]")
        
        # Paso 3: Análisis Dinámico
        console.print("[blue]🎯 Paso 3: Ejecutando análisis dinámico...[/blue]")
        with LoadingSpinner("Ejecutando análisis dinámico..."):
            dynamic_agent = DynamicAnalysisAgent(llm_adapter)
            dynamic_result = dynamic_agent.validate_vulnerabilities(pdf, url)
        
        console.print(f"[green]✅ Análisis dinámico completado: {dynamic_result.get('vulnerabilidades_vulnerables', 0)}/{dynamic_result.get('vulnerabilidades_reportadas', 0)} vulnerabilidades confirmadas[/green]")
        
        # Paso 4: Triage de vulnerabilidades
        console.print("[blue]⚖️ Paso 4: Realizando triage de vulnerabilidades...[/blue]")
        with LoadingSpinner("Realizando triage..."):
            triage_agent = TriageAgent(llm_adapter)
            
            # Combinar evidencias de análisis estático y dinámico
            enhanced_report = pdf_result.copy()
            
            # Enriquecer vulnerabilidades con evidencia de análisis estático y dinámico
            for i, hallazgo in enumerate(enhanced_report.get('hallazgos_principales', [])):
                # Buscar evidencia en análisis estático
                static_evidence = None
                for static_vuln in static_result.get('vulnerabilidades', []):
                    if static_vuln.get('nombre', '').lower() in hallazgo.get('titulo', '').lower():
                        static_evidence = {
                            'tipo': 'analisis_estatico',
                            'estado': static_vuln.get('estado'),
                            'evidencia': static_vuln.get('evidencia')
                        }
                        break
                
                # Buscar evidencia en análisis dinámico
                dynamic_evidence = None
                for dynamic_vuln in dynamic_result.get('vulnerabilidades', []):
                    if dynamic_vuln.get('nombre', '').lower() in hallazgo.get('titulo', '').lower():
                        dynamic_evidence = {
                            'tipo': 'analisis_dinamico',
                            'estado': dynamic_vuln.get('estado'),
                            'evidencia': dynamic_vuln.get('evidencia'),
                            'payload_usado': dynamic_vuln.get('payload_usado'),
                            'respuesta_servidor': dynamic_vuln.get('respuesta_servidor')
                        }
                        break
                
                # Agregar evidencias al hallazgo
                if 'evidencias_adicionales' not in hallazgo:
                    hallazgo['evidencias_adicionales'] = []
                
                if static_evidence:
                    hallazgo['evidencias_adicionales'].append(static_evidence)
                if dynamic_evidence:
                    hallazgo['evidencias_adicionales'].append(dynamic_evidence)
            
            # Realizar triage con el reporte enriquecido
            triage_result = triage_agent.analyze_vulnerabilities(enhanced_report)
        
        console.print(f"[green]✅ Triage completado: {len(triage_result.vulnerabilidades)} vulnerabilidades procesadas[/green]")
        
        # Determinar estado de vulnerabilidades basado en análisis estático y dinámico
        vulnerabilidades_con_estado = []
        
        if verbose:
            console.print("[blue]🔍 Debug: Comparando IDs y nombres de vulnerabilidades...[/blue]")
            console.print(f"[dim]Vulnerabilidades del triage: {[(getattr(v, 'id', 'Sin ID'), v.nombre) for v in triage_result.vulnerabilidades]}[/dim]")
            console.print(f"[dim]Vulnerabilidades del análisis estático: {[(v.get('id', 'Sin ID'), v.get('nombre', 'Sin nombre')) for v in static_result.get('vulnerabilidades', [])]}[/dim]")
            console.print(f"[dim]Vulnerabilidades del análisis dinámico: {[(v.get('id', 'Sin ID'), v.get('nombre', 'Sin nombre')) for v in dynamic_result.get('vulnerabilidades', [])]}[/dim]")
        
        for vuln in triage_result.vulnerabilidades:
            # Buscar si la vulnerabilidad fue confirmada por análisis estático
            static_vulnerable = False
            static_details = None
            for static_vuln in static_result.get('vulnerabilidades', []):
                # Primero intentar comparar por ID si ambos tienen ID
                vuln_id = getattr(vuln, 'id', None)
                static_id = static_vuln.get('id', None)
                
                match_found = False
                if vuln_id and static_id and vuln_id == static_id:
                    match_found = True
                    if verbose:
                        console.print(f"[green]✅ Coincidencia estática por ID: '{vuln_id}' (Estado: {static_vuln.get('estado', 'desconocido')})[/green]")
                else:
                    # Fallback: comparar nombres de vulnerabilidades de forma más flexible
                    vuln_name_lower = vuln.nombre.lower().strip()
                    static_name_lower = static_vuln.get('nombre', '').lower().strip()
                    
                    # Intentar múltiples formas de coincidencia
                    if (vuln_name_lower == static_name_lower or 
                        vuln_name_lower in static_name_lower or 
                        static_name_lower in vuln_name_lower or
                        # Comparar sin espacios y caracteres especiales
                        vuln_name_lower.replace(' ', '').replace('-', '').replace('_', '') == 
                        static_name_lower.replace(' ', '').replace('-', '').replace('_', '')):
                        match_found = True
                        if verbose:
                            console.print(f"[green]✅ Coincidencia estática por nombre: '{vuln.nombre}' <-> '{static_vuln.get('nombre', '')}' (Estado: {static_vuln.get('estado', 'desconocido')})[/green]")
                
                if match_found:
                    static_vulnerable = static_vuln.get('estado') == 'vulnerable'
                    if not static_vulnerable:
                        static_details = static_vuln.get('evidencia', 'No se encontró evidencia de vulnerabilidad en el análisis estático')
                    break
        
            # Buscar si la vulnerabilidad fue confirmada por análisis dinámico
            dynamic_vulnerable = False
            dynamic_details = None
            for dynamic_vuln in dynamic_result.get('vulnerabilidades', []):
                # Primero intentar comparar por ID si ambos tienen ID
                vuln_id = getattr(vuln, 'id', None)
                dynamic_id = dynamic_vuln.get('id', None)
                
                match_found = False
                if vuln_id and dynamic_id and vuln_id == dynamic_id:
                    match_found = True
                    if verbose:
                        console.print(f"[green]✅ Coincidencia dinámica por ID: '{vuln_id}' (Estado: {dynamic_vuln.get('estado', 'desconocido')})[/green]")
                else:
                    # Fallback: comparar nombres de vulnerabilidades de forma más flexible
                    vuln_name_lower = vuln.nombre.lower().strip()
                    dynamic_name_lower = dynamic_vuln.get('nombre', '').lower().strip()
                    
                    # Intentar múltiples formas de coincidencia
                    if (vuln_name_lower == dynamic_name_lower or 
                        vuln_name_lower in dynamic_name_lower or 
                        dynamic_name_lower in vuln_name_lower or
                        # Comparar sin espacios y caracteres especiales
                        vuln_name_lower.replace(' ', '').replace('-', '').replace('_', '') == 
                        dynamic_name_lower.replace(' ', '').replace('-', '').replace('_', '')):
                        match_found = True
                        if verbose:
                            console.print(f"[green]✅ Coincidencia dinámica por nombre: '{vuln.nombre}' <-> '{dynamic_vuln.get('nombre', '')}' (Estado: {dynamic_vuln.get('estado', 'desconocido')})[/green]")
                
                if match_found:
                    dynamic_vulnerable = dynamic_vuln.get('estado') == 'vulnerable'
                    if not dynamic_vulnerable:
                        dynamic_details = dynamic_vuln.get('evidencia', 'No se encontró evidencia de vulnerabilidad en el análisis dinámico')
                    break
            
            # Determinar estado final
            if static_vulnerable or dynamic_vulnerable:
                estado_final = 'vulnerable'
                explicacion_estado = 'Vulnerabilidad confirmada por '
                if static_vulnerable and dynamic_vulnerable:
                    explicacion_estado += 'análisis estático y dinámico'
                elif static_vulnerable:
                    explicacion_estado += 'análisis estático'
                else:
                    explicacion_estado += 'análisis dinámico'
            else:
                estado_final = 'no_vulnerable'
                explicacion_estado = 'Vulnerabilidad no confirmada por ningún análisis. '
                if static_details and dynamic_details:
                    explicacion_estado += f'Análisis estático: {static_details}. Análisis dinámico: {dynamic_details}'
                elif static_details:
                    explicacion_estado += f'Análisis estático: {static_details}'
                elif dynamic_details:
                    explicacion_estado += f'Análisis dinámico: {dynamic_details}'
                else:
                    explicacion_estado += 'No se encontraron evidencias en ninguno de los análisis'
            
            if verbose:
                console.print(f"[blue]📋 Estado final para '{vuln.nombre}': {estado_final} (Estático: {static_vulnerable}, Dinámico: {dynamic_vulnerable})[/blue]")
            
            # Crear vulnerabilidad con estado
            vuln_dict = vuln.model_dump()
            vuln_dict['estado_vulnerabilidad'] = estado_final
            vuln_dict['explicacion_estado'] = explicacion_estado
            vulnerabilidades_con_estado.append(vuln_dict)
    
        # Actualizar el resultado del triage con los estados
        triage_final_con_estados = triage_result.model_dump()
        triage_final_con_estados['vulnerabilidades'] = vulnerabilidades_con_estado
        
        # Generar resultado final combinado
        complete_analysis = {
            "analisis_pdf": pdf_result,
            "analisis_estatico": static_result,
            "analisis_dinamico": dynamic_result,
            "triage_final": triage_final_con_estados,
            "metadata": {
                "fecha_analisis": datetime.now().isoformat(),
                "version_pipeline": "2.0.0",
                "modelo_usado": f"{provider}:{model_name}",
                "temperatura": temperature,
                "archivos_analizados": {
                    "pdf": pdf,
                    "codigo_fuente": source,
                    "url_objetivo": url
                }
            }
        }
        
        # Mostrar resumen final
        console.print("[green]✅ Análisis completo finalizado[/green]")
        console.print("[blue]📊 Resumen del análisis:[/blue]")
        console.print(f"  [dim]• Vulnerabilidades en PDF: {len(pdf_result.get('hallazgos_principales', []))}[/dim]")
        console.print(f"  [dim]• Confirmadas por análisis estático: {static_result.get('vulnerabilidades_vulnerables', 0)}[/dim]")
        console.print(f"  [dim]• Confirmadas por análisis dinámico: {dynamic_result.get('vulnerabilidades_vulnerables', 0)}[/dim]")
        console.print(f"  [dim]• Vulnerabilidades procesadas en triage: {len(triage_result.vulnerabilidades)}[/dim]")
        
        # Guardar resultado
        if output:
            try:
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(complete_analysis, f, indent=2, ensure_ascii=False, default=str)
                console.print(f"[green]✅ Resultado guardado en: {output}[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️ Error guardando archivo: {str(e)}[/yellow]")
        else:
            # Mostrar resultado en consola con formato bonito
            _display_complete_analysis_report(complete_analysis)
        
        # Guardar en MongoDB si se solicita
        if mongodb:
            try:
                with LoadingSpinner("Guardando en MongoDB..."):
                    client = MongoDBClient()
                    client.connect()
                    
                    result_json = json.dumps(complete_analysis, indent=2, ensure_ascii=False, default=str)
                    document_id = client.save_report(
                            pdf, 
                            result_json,
                            {
                                'pdf_file': pdf,
                                'source_path': source,
                                'target_url': url,
                                'output_file': output,
                                'model': f"{provider}:{model_name}",
                                'temperature': temperature,
                                'analysis_type': 'complete_analysis_v2'
                            }
                        )
                    client.disconnect()
                    console.print(f"[green]✅ Guardado en MongoDB con ID: {document_id}[/green]")
                    
            except Exception as e:
                console.print(f"[yellow]⚠️ Error guardando en MongoDB: {str(e)}[/yellow]")
        
    except (PDFNotFoundError, InvalidPDFError, PDFReadError) as e:
        console.print(f"[red]❌ Error con el archivo PDF: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)
    except (ReportAnalysisError, LLMConnectionError, JSONParsingError) as e:
        console.print(f"[red]❌ Error de análisis: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error inesperado: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


if __name__ == "__main__":
    app()