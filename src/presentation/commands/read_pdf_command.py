"""Read PDF command implementation."""

from typing import Optional, Dict, Any
from rich.panel import Panel
from rich.syntax import Syntax
from .base_command import BaseCommand
from ..utils.loading_spinner import LoadingSpinner
from ...domain.exceptions import (
    PDFAnalyzerException, PDFNotFoundError, InvalidPDFError, 
    PDFReadError, ReportAnalysisError, LLMConnectionError, JSONParsingError
)


class ReadPDFCommand(BaseCommand):
    """Command for reading and analyzing PDF reports."""
    
    def execute(
        self,
        pdf: str,
        output: Optional[str] = None,
        model: str = "openai",
        temperature: float = 0.1,
        verbose: bool = False,
        mongodb: bool = False
    ) -> Dict[str, Any]:
        """Execute PDF reading and analysis."""
        
        provider, model_name = self._parse_model_parameter(model)
        
        # Display report and model info at the beginning
        self.console.print(f"📄 Reporte: {pdf}", style="blue")
        model_display = f"{provider}:{model_name}" if model_name else provider
        self.console.print(f"🤖 Modelo: {model_display}", style="cyan")
        
        if verbose:
            self._display_verbose_info({
                "Archivo PDF": pdf,
                "Proveedor LLM": provider,
                "Modelo": model_name or "Por defecto",
                "Temperatura": temperature,
                "Archivo de salida": output or "No especificado",
                "MongoDB": "Sí" if mongodb else "No"
            })
        
        try:
            # Create use case with dependencies
            read_pdf_use_case = self.factory.create_read_pdf_use_case(
                provider=provider,
                model_name=model_name,
                temperature=temperature
            )
            
            # Execute analysis with loading spinner
            with LoadingSpinner("Analizando PDF...") as spinner:
                spinner.update_message("Leyendo archivo PDF...")
                result = read_pdf_use_case.execute(pdf)
                
                spinner.update_message("Procesando con IA...")
                # Additional processing if needed
            
            # Display results
            self._display_results(result)
            
            # Save results
            if output:
                self._save_to_file(result, output)
            
            if mongodb:
                self._save_to_mongodb(result, "pdf_analysis")
            
            return result
            
        except (PDFNotFoundError, InvalidPDFError, PDFReadError) as e:
            self._handle_error(e, "de PDF")
            raise
        except (LLMConnectionError, JSONParsingError) as e:
            self._handle_error(e, "de LLM")
            raise
        except PDFAnalyzerException as e:
            self._handle_error(e, "del analizador")
            raise
        except Exception as e:
            self._handle_error(e, "inesperado")
            raise
    
    def _display_results(self, result: Dict[str, Any]) -> None:
        """Display analysis results in a formatted way."""
        from rich.table import Table
        
        # Display document info
        if "document_info" in result:
            doc_info = result["document_info"]
            self.console.print(Panel(
                f"📄 **Archivo:** {doc_info.get('filename', 'N/A')}\n"
                f"📊 **Páginas:** {doc_info.get('pages', 'N/A')}\n"
                f"📝 **Caracteres:** {doc_info.get('characters', 'N/A')}",
                title="Información del Documento",
                border_style="blue"
            ))
        
        # Display security report summary
        if "security_report" in result:
            security = result["security_report"]
            findings_count = len(security.get("findings", []))
            
            self.console.print(Panel(
                f"🔍 **Hallazgos encontrados:** {findings_count}\n"
                f"⚠️ **Nivel de riesgo:** {security.get('risk_level', 'N/A')}\n"
                f"📋 **Recomendaciones:** {len(security.get('recommendations', []))}",
                title="Resumen del Análisis de Seguridad",
                border_style="red"
            ))
            
            # Display findings table
            if findings_count > 0:
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Vulnerabilidad", style="cyan")
                table.add_column("Severidad", style="red")
                table.add_column("Descripción", style="white")
                
                for finding in security.get("findings", [])[:5]:  # Show first 5
                    table.add_row(
                        finding.get("title", "N/A"),
                        finding.get("severity", "N/A"),
                        finding.get("description", "N/A")[:100] + "..." if len(finding.get("description", "")) > 100 else finding.get("description", "N/A")
                    )
                
                self.console.print(table)
                
                if findings_count > 5:
                    self.console.print(f"... y {findings_count - 5} hallazgos más", style="dim")
        
        self.console.print("\n✅ Análisis completado exitosamente", style="green bold")