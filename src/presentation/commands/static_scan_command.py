"""Static scan command implementation."""

from typing import Optional, Dict, Any
from .base_command import BaseCommand
from ..utils.loading_spinner import LoadingSpinner


class StaticScanCommand(BaseCommand):
    """Command for static code analysis."""
    
    def execute(
        self,
        pdf: str,
        source: str,
        output: Optional[str] = None,
        model: str = "openai",
        temperature: float = 0.1,
        verbose: bool = False,
        mongodb: bool = False
    ) -> Dict[str, Any]:
        """Execute static code analysis."""
        
        provider, model_name = self._parse_model_parameter(model)
        
        if verbose:
            self._display_verbose_info({
                "Archivo PDF": pdf,
                "Código fuente": source,
                "Proveedor LLM": provider,
                "Modelo": model_name or "Por defecto",
                "Temperatura": temperature,
                "Archivo de salida": output or "No especificado",
                "MongoDB": "Sí" if mongodb else "No"
            })
        
        try:
            # Create static analysis agent
            static_agent = self.factory.create_static_analyzer(provider, model_name, temperature)
            
            with LoadingSpinner("Realizando análisis estático...") as spinner:
                spinner.update_message("Analizando código fuente...")
                result = static_agent.analyze_code(source, pdf)
            
            # Display results
            self._display_static_results(result)
            
            # Save results
            if output:
                self._save_to_file(result, output)
            
            if mongodb:
                self._save_to_mongodb(result, "static_analysis")
            
            return result
            
        except Exception as e:
            self._handle_error(e, "de análisis estático")
            raise
    
    def _display_static_results(self, result: Dict[str, Any]) -> None:
        """Display static analysis results."""
        from rich.panel import Panel
        
        self.console.print(Panel(
            f"🔍 **Análisis estático completado**\n"
            f"📁 **Archivos analizados:** {result.get('files_analyzed', 'N/A')}\n"
            f"⚠️ **Issues encontrados:** {result.get('issues_count', 'N/A')}",
            title="Resultados del Análisis Estático",
            border_style="blue"
        ))
        
        self.console.print("✅ Análisis estático completado", style="green bold")