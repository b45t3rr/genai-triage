"""Test command implementation."""

from typing import Dict, Any
from rich.panel import Panel
from rich.table import Table
from .base_command import BaseCommand
from ..utils.loading_spinner import LoadingSpinner
from ...infrastructure.utils.config import validate_environment, get_available_providers
from ...domain.exceptions import LLMConnectionError


class TestCommand(BaseCommand):
    """Command for testing LLM connections."""
    
    def execute(self, model: str = "openai") -> Dict[str, Any]:
        """Execute connection test."""
        
        provider, model_name = self._parse_model_parameter(model)
        
        self.console.print(Panel(
            f"🧪 Probando conexión con {provider.upper()}",
            title="Test de Conexión LLM",
            border_style="blue"
        ))
        
        # Get available providers
        available_providers = self.factory.get_available_providers()
        self._display_provider_status(available_providers)
        
        # Test specific provider
        if not self.factory.validate_provider(provider):
            self.console.print(
                f"❌ El proveedor '{provider}' no está configurado correctamente",
                style="red"
            )
            self.console.print(
                "💡 Verifique que la API key esté configurada en el archivo .env",
                style="yellow"
            )
            return {"success": False, "provider": provider, "error": "Not configured"}
        
        try:
            with LoadingSpinner(f"Probando conexión con {provider}..."):
                # Create LLM instance
                llm = self.factory.create_llm(provider, model_name, 0.1)
                
                # Test with a simple prompt
                test_prompt = "Responde solo con 'OK' si puedes procesar este mensaje."
                response = llm.generate(test_prompt)
                
                if response and len(response.strip()) > 0:
                    self.console.print(f"✅ Conexión exitosa con {provider}", style="green bold")
                    self.console.print(f"📝 Respuesta: {response[:100]}...", style="dim")
                    
                    return {
                        "success": True,
                        "provider": provider,
                        "model": model_name,
                        "response": response
                    }
                else:
                    raise LLMConnectionError("Respuesta vacía del modelo")
                    
        except LLMConnectionError as e:
            self._handle_error(e, f"de conexión con {provider}")
            return {"success": False, "provider": provider, "error": str(e)}
        except Exception as e:
            self._handle_error(e, f"inesperado con {provider}")
            return {"success": False, "provider": provider, "error": str(e)}
    
    def _display_provider_status(self, available_providers: list) -> None:
        """Display status of all available providers."""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Proveedor", style="cyan")
        table.add_column("Estado", style="white")
        table.add_column("Configuración", style="dim")
        
        all_providers = ["openai", "xai", "gemini", "deepseek", "anthropic"]
        
        for provider in all_providers:
            if provider in available_providers:
                status = "✅ Disponible"
                config = "API key configurada"
                style = "green"
            else:
                status = "❌ No disponible"
                config = "API key faltante"
                style = "red"
            
            table.add_row(provider.upper(), status, config)
        
        self.console.print(Panel(
            table,
            title="Estado de Proveedores LLM",
            border_style="blue"
        ))
        
        if available_providers:
            self.console.print(
                f"💡 Proveedores disponibles: {', '.join(available_providers)}",
                style="green"
            )
        else:
            self.console.print(
                "⚠️ No hay proveedores configurados. Configure al menos una API key en .env",
                style="yellow"
            )