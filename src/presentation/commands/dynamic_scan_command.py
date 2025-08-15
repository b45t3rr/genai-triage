"""Dynamic scan command implementation."""

from typing import Optional, Dict, Any
from .base_command import BaseCommand
from ..utils.loading_spinner import LoadingSpinner


class DynamicScanCommand(BaseCommand):
    """Command for dynamic security scanning."""
    
    def execute(
        self,
        pdf: str,
        url: str,
        output: Optional[str] = None,
        model: str = "openai",
        temperature: float = 0.1,
        verbose: bool = False,
        mongodb: bool = False
    ) -> Dict[str, Any]:
        """Execute dynamic security scan."""
        
        provider, model_name = self._parse_model_parameter(model)
        
        if verbose:
            self._display_verbose_info({
                "Archivo PDF": pdf,
                "URL objetivo": url,
                "Proveedor LLM": provider,
                "Modelo": model_name or "Por defecto",
                "Temperatura": temperature,
                "Archivo de salida": output or "No especificado",
                "MongoDB": "Sí" if mongodb else "No"
            })
        
        try:
            # Create dynamic analysis agent
            llm = self.factory.create_llm(provider, model_name, temperature)
            from ...infrastructure.services.agents.dynamic_agent import DynamicAgent
            dynamic_agent = DynamicAgent(llm)
            
            with LoadingSpinner("Realizando análisis dinámico...") as spinner:
                spinner.update_message("Probando aplicación web...")
                result = dynamic_agent.analyze_application(url, pdf)
            
            # Display results
            self._display_dynamic_results(result)
            
            # Save results
            if output:
                self._save_to_file(result, output)
            
            if mongodb:
                self._save_to_mongodb(result, "dynamic_analysis")
            
            return result
            
        except Exception as e:
            self._handle_error(e, "de análisis dinámico")
            raise
    
    def _display_dynamic_results(self, result: Dict[str, Any]) -> None:
        """Display dynamic analysis results."""
        from rich.panel import Panel
        
        self.console.print(Panel(
            f"🌐 **Análisis dinámico completado**\n"
            f"🎯 **URL analizada:** {result.get('target_url', 'N/A')}\n"
            f"⚠️ **Vulnerabilidades:** {result.get('vulnerabilities_count', 'N/A')}",
            title="Resultados del Análisis Dinámico",
            border_style="green"
        ))
        
        self.console.print("✅ Análisis dinámico completado", style="green bold")