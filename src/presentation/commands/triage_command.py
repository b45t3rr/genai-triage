"""Triage command implementation."""

import json
from typing import Optional, Dict, Any
from rich.panel import Panel
from rich.table import Table
from .base_command import BaseCommand
from ..utils.loading_spinner import LoadingSpinner
from ...domain.exceptions import (
    PDFAnalyzerException, ReportAnalysisError, LLMConnectionError, JSONParsingError
)


class TriageCommand(BaseCommand):
    """Command for vulnerability triage analysis."""
    
    def execute(
        self,
        report: str,
        output: Optional[str] = None,
        model: str = "openai",
        temperature: float = 0.1,
        verbose: bool = False,
        mongodb: bool = False
    ) -> Dict[str, Any]:
        """Execute vulnerability triage."""
        
        provider, model_name = self._parse_model_parameter(model)
        
        if verbose:
            self._display_verbose_info({
                "Reporte de entrada": report,
                "Proveedor LLM": provider,
                "Modelo": model_name or "Por defecto",
                "Temperatura": temperature,
                "Archivo de salida": output or "No especificado",
                "MongoDB": "Sí" if mongodb else "No"
            })
        
        try:
            # Load security report
            with open(report, 'r', encoding='utf-8') as f:
                security_report = json.load(f)
            
            self.console.print(f"📄 Reporte cargado: {report}", style="blue")
            
            # Create triage use case
            triage_use_case = self.factory.create_triage_use_case(
                provider=provider,
                model_name=model_name,
                temperature=temperature
            )
            
            # Execute triage with loading spinner
            with LoadingSpinner("Realizando triage de vulnerabilidades...") as spinner:
                spinner.update_message("Analizando vulnerabilidades...")
                result = triage_use_case.execute(security_report)
                
                spinner.update_message("Generando recomendaciones...")
                # Additional processing if needed
            
            # Display results
            self._display_triage_results(result)
            
            # Save results
            if output:
                self._save_to_file(result, output)
            
            if mongodb:
                self._save_to_mongodb(result, "vulnerability_triage")
            
            return result
            
        except FileNotFoundError:
            error_msg = f"No se encontró el archivo de reporte: {report}"
            self.console.print(f"❌ {error_msg}", style="red")
            raise
        except json.JSONDecodeError as e:
            error_msg = f"Error al parsear JSON: {str(e)}"
            self.console.print(f"❌ {error_msg}", style="red")
            raise
        except (LLMConnectionError, JSONParsingError) as e:
            self._handle_error(e, "de LLM")
            raise
        except ReportAnalysisError as e:
            self._handle_error(e, "de análisis")
            raise
        except Exception as e:
            self._handle_error(e, "inesperado")
            raise
    
    def _display_triage_results(self, result: Dict[str, Any]) -> None:
        """Display triage results in a formatted way."""
        
        # Display summary
        if "summary" in result:
            summary = result["summary"]
            self.console.print(Panel(
                f"🔍 **Vulnerabilidades analizadas:** {summary.get('total_vulnerabilities', 'N/A')}\n"
                f"🔥 **Críticas:** {summary.get('critical_count', 0)}\n"
                f"⚠️ **Altas:** {summary.get('high_count', 0)}\n"
                f"📊 **Medias:** {summary.get('medium_count', 0)}\n"
                f"ℹ️ **Bajas:** {summary.get('low_count', 0)}",
                title="Resumen del Triage",
                border_style="red"
            ))
        
        # Display triaged vulnerabilities
        if "triaged_vulnerabilities" in result:
            vulnerabilities = result["triaged_vulnerabilities"]
            
            if vulnerabilities:
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Vulnerabilidad", style="cyan")
                table.add_column("Severidad Original", style="yellow")
                table.add_column("Severidad Triage", style="red")
                table.add_column("Prioridad", style="white")
                table.add_column("Confianza", style="green")
                
                for vuln in vulnerabilities[:10]:  # Show first 10
                    table.add_row(
                        vuln.get("title", "N/A")[:30] + "..." if len(vuln.get("title", "")) > 30 else vuln.get("title", "N/A"),
                        vuln.get("original_severity", "N/A"),
                        vuln.get("triage_severity", "N/A"),
                        vuln.get("priority", "N/A"),
                        f"{vuln.get('confidence_score', 0):.1f}%"
                    )
                
                self.console.print(table)
                
                if len(vulnerabilities) > 10:
                    self.console.print(f"... y {len(vulnerabilities) - 10} vulnerabilidades más", style="dim")
        
        # Display key recommendations
        if "recommendations" in result:
            recommendations = result["recommendations"]
            if recommendations:
                self.console.print("\n🎯 **Recomendaciones Principales:**", style="bold blue")
                for i, rec in enumerate(recommendations[:3], 1):
                    self.console.print(f"{i}. {rec.get('description', 'N/A')}", style="white")
        
        self.console.print("\n✅ Triage completado exitosamente", style="green bold")