"""Complete analysis command implementation."""

from typing import Optional, Dict, Any
from rich.panel import Panel
from .base_command import BaseCommand
from ..utils.loading_spinner import LoadingSpinner


class CompleteAnalysisCommand(BaseCommand):
    """Command for complete security analysis workflow."""
    
    def execute(
        self,
        pdf: str,
        source: str,
        url: str,
        output: Optional[str] = None,
        model: str = "openai",
        temperature: float = 0.1,
        verbose: bool = False,
        mongodb: bool = False
    ) -> Dict[str, Any]:
        """Execute complete security analysis."""
        
        provider, model_name = self._parse_model_parameter(model)
        
        if verbose:
            self._display_verbose_info({
                "Archivo PDF": pdf,
                "Código fuente": source,
                "URL objetivo": url,
                "Proveedor LLM": provider,
                "Modelo": model_name or "Por defecto",
                "Temperatura": temperature,
                "Archivo de salida": output or "No especificado",
                "MongoDB": "Sí" if mongodb else "No"
            })
        
        try:
            # Create complete analysis use case
            from ...application.use_cases import CompleteSecurityAnalysisUseCase
            
            complete_use_case = self.factory.create_complete_analysis_use_case(
                provider=provider,
                model_name=model_name,
                temperature=temperature
            )
            
            with LoadingSpinner("Realizando análisis completo...") as spinner:
                spinner.update_message("Fase 1: Análisis de PDF...")
                # Execute complete analysis
                result = complete_use_case.execute(pdf, source, url)
                
                spinner.update_message("Fase 2: Análisis estático...")
                # Additional phases handled by use case
                
                spinner.update_message("Fase 3: Análisis dinámico...")
                # Final processing
                
                spinner.update_message("Generando reporte consolidado...")
            
            # Display results
            self._display_complete_results(result)
            
            # Save results
            if output:
                self._save_to_file(result, output)
            
            if mongodb:
                self._save_to_mongodb(result, "complete_analysis")
            
            return result
            
        except Exception as e:
            self._handle_error(e, "de análisis completo")
            raise
    
    def _display_complete_results(self, result: Dict[str, Any]) -> None:
        """Display complete analysis results."""
        from rich.table import Table
        
        # Display summary
        self.console.print(Panel(
            f"📊 **Análisis Completo Finalizado**\n"
            f"📄 **PDF:** Analizado\n"
            f"🔍 **Código:** Escaneado\n"
            f"🌐 **Aplicación:** Probada\n"
            f"⚠️ **Total vulnerabilidades:** {result.get('total_vulnerabilities', 'N/A')}",
            title="Resumen del Análisis Completo",
            border_style="magenta"
        ))
        
        # Display analysis phases
        if "phases" in result:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Fase", style="cyan")
            table.add_column("Estado", style="green")
            table.add_column("Hallazgos", style="white")
            
            phases = result["phases"]
            for phase_name, phase_data in phases.items():
                status = "✅ Completado" if phase_data.get("completed") else "❌ Error"
                findings = str(phase_data.get("findings_count", 0))
                table.add_row(phase_name.title(), status, findings)
            
            self.console.print(table)
        
        self.console.print("\n🎉 Análisis completo finalizado exitosamente", style="green bold")