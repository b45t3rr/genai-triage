"""Simplified CLI using Command pattern."""

import typer
from typing import Optional
from rich.console import Console

from .commands import (
    ReadPDFCommand,
    TestCommand,
    StaticScanCommand,
    DynamicScanCommand,
    TriageCommand,
    CompleteAnalysisCommand
)
from ..infrastructure.utils import get_simple_factory

app = typer.Typer(
    name="pdf-analyzer",
    help="Analizador de reportes PDF usando LangChain con arquitectura limpia",
    add_completion=False
)
console = Console()


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
    """Analizar un reporte PDF de seguridad."""
    command = ReadPDFCommand()
    try:
        command.execute(
            pdf=pdf,
            output=output,
            model=model,
            temperature=temperature,
            verbose=verbose,
            mongodb=mongodb
        )
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")
        raise typer.Exit(1)


@app.command("test")
def test_connection(
    model: str = typer.Option(
        "openai",
        "--model",
        "-m",
        help="Proveedor de LLM a probar (openai, xai, gemini, deepseek, anthropic) o formato 'proveedor:modelo'"
    )
):
    """Probar la conexión con el proveedor de LLM."""
    command = TestCommand()
    try:
        result = command.execute(model=model)
        if not result.get("success"):
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")
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
        help="Proveedor de LLM a utilizar"
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
        help="Guardar el resultado en MongoDB"
    )
):
    """Realizar análisis estático de código."""
    command = StaticScanCommand()
    try:
        command.execute(
            pdf=pdf,
            source=source,
            output=output,
            model=model,
            temperature=temperature,
            verbose=verbose,
            mongodb=mongodb
        )
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")
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
        help="Proveedor de LLM a utilizar"
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
        help="Guardar el resultado en MongoDB"
    )
):
    """Realizar análisis dinámico de aplicación web."""
    command = DynamicScanCommand()
    try:
        command.execute(
            pdf=pdf,
            url=url,
            output=output,
            model=model,
            temperature=temperature,
            verbose=verbose,
            mongodb=mongodb
        )
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")
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
        help="Proveedor de LLM a utilizar"
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
        help="Guardar el resultado en MongoDB"
    )
):
    """Realizar triage de vulnerabilidades."""
    command = TriageCommand()
    try:
        command.execute(
            report=report,
            output=output,
            model=model,
            temperature=temperature,
            verbose=verbose,
            mongodb=mongodb
        )
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")
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
        help="Proveedor de LLM a utilizar"
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
        help="Guardar el resultado en MongoDB"
    )
):
    """Realizar análisis completo de seguridad."""
    command = CompleteAnalysisCommand()
    try:
        command.execute(
            pdf=pdf,
            source=source,
            url=url,
            output=output,
            model=model,
            temperature=temperature,
            verbose=verbose,
            mongodb=mongodb
        )
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")
        raise typer.Exit(1)


@app.command("version")
def version():
    """Mostrar la versión del analizador."""
    console.print("🔍 PDF Security Analyzer v2.0.0", style="bold blue")
    console.print("Arquitectura limpia con patrón Command", style="dim")


if __name__ == "__main__":
    app()