"""Base command class following Command pattern."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from rich.console import Console
from ..utils.loading_spinner import LoadingSpinner
from ...infrastructure.utils.factory import get_simple_factory
from ...infrastructure.adapters.persistence.mongodb_client import MongoDBClient


class BaseCommand(ABC):
    """Base class for all CLI commands."""
    
    def __init__(self):
        self.console = Console()
        self.factory = get_simple_factory()
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the command with given parameters."""
        pass
    
    def _parse_model_parameter(self, model: str) -> tuple[str, Optional[str]]:
        """Parse model parameter to extract provider and model name."""
        if ':' in model:
            provider, model_name = model.split(':', 1)
            return provider, model_name
        return model, None
    
    def _save_to_file(self, data: Dict[str, Any], output_path: str) -> None:
        """Save data to JSON file."""
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.console.print(f"✅ Resultado guardado en: {output_path}", style="green")
    
    def _save_to_mongodb(self, data: Dict[str, Any], collection: str) -> None:
        """Save data to MongoDB."""
        try:
            client = MongoDBClient()
            result = client.insert_document(collection, data)
            if result:
                self.console.print(f"✅ Resultado guardado en MongoDB (ID: {result})", style="green")
            else:
                self.console.print("❌ Error al guardar en MongoDB", style="red")
        except Exception as e:
            self.console.print(f"❌ Error de MongoDB: {str(e)}", style="red")
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """Handle and display errors consistently."""
        error_msg = f"Error {context}: {str(error)}" if context else str(error)
        self.console.print(f"❌ {error_msg}", style="red")
        
        if hasattr(error, '__class__'):
            error_type = error.__class__.__name__
            if error_type in ['PDFNotFoundError', 'InvalidPDFError', 'PDFReadError']:
                self.console.print("💡 Verifique que el archivo PDF existe y es válido", style="yellow")
            elif error_type in ['LLMConnectionError', 'JSONParsingError']:
                self.console.print("💡 Verifique la configuración del modelo LLM", style="yellow")
    
    def _display_verbose_info(self, info: Dict[str, Any]) -> None:
        """Display verbose information in a consistent format."""
        from rich.panel import Panel
        from rich.table import Table
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Parámetro", style="cyan")
        table.add_column("Valor", style="white")
        
        for key, value in info.items():
            table.add_row(key, str(value))
        
        self.console.print(Panel(table, title="Información de Configuración", border_style="blue"))