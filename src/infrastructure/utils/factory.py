"""Factory para crear instancias de las dependencias."""

from ...domain.interfaces import PDFReaderInterface, SecurityAnalyzerInterface, LLMInterface
from ...domain.services import SecurityAnalysisService, ReportValidationService
from ...application.use_cases import ReadPDFUseCase
from ..adapters.external.tools.pdf_reader import PyPDF2Reader
from ..services.agents import LangChainReportAnalyzer, StaticAnalysisAgent
# LLMFactory se importa dinámicamente para evitar importación circular
from .config import get_settings, validate_environment, get_available_providers


class DependencyFactory:
    """Factory para crear e inyectar dependencias."""
    
    def __init__(self):
        self._settings = get_settings()
    
    def create_pdf_reader(self) -> PDFReaderInterface:
        """Crea una instancia del lector de PDF."""
        return PyPDF2Reader()
    
    def create_llm(self, provider: str = None, model_name: str = None, temperature: float = None) -> LLMInterface:
        """Crea una instancia del LLM."""
        # Importación dinámica para evitar importación circular
        from ..adapters.llm.llm_adapters import LLMFactory
        
        if provider is None:
            provider = self._settings.default_model_provider
        
        # Validar que el proveedor tenga API key configurada
        if not validate_environment(provider):
            available = get_available_providers()
            if available:
                provider = available[0]  # Usar el primer proveedor disponible
            else:
                raise ValueError("No hay proveedores de LLM configurados. Configure al menos una API key.")
        
        return LLMFactory.create_llm(provider, model_name, temperature)
    
    def create_report_analyzer(self, llm: LLMInterface = None) -> SecurityAnalyzerInterface:
        """Crea una instancia del analizador de reportes."""
        if llm is None:
            llm = self.create_llm()
        return LangChainReportAnalyzer(llm)
    
    def create_static_analysis_agent(self, llm: LLMInterface = None) -> StaticAnalysisAgent:
        """Crea una instancia del agente de análisis estático."""
        if llm is None:
            llm = self.create_llm()
        return StaticAnalysisAgent(llm)
    
    def create_read_pdf_use_case(
        self, 
        provider: str = None,
        model_name: str = None,
        temperature: float = None,
        pdf_reader: PDFReaderInterface = None,
        report_analyzer: SecurityAnalyzerInterface = None
    ) -> ReadPDFUseCase:
        """Crea una instancia del caso de uso principal."""
        if pdf_reader is None:
            pdf_reader = self.create_pdf_reader()
        
        if report_analyzer is None:
            llm = self.create_llm(provider, model_name, temperature)
            report_analyzer = self.create_report_analyzer(llm)
        
        analysis_service = SecurityAnalysisService()
        validation_service = ReportValidationService()
        
        return ReadPDFUseCase(
            pdf_reader=pdf_reader,
            security_analyzer=report_analyzer,
            analysis_service=analysis_service,
            validation_service=validation_service
        )


# Instancia global del factory
factory = DependencyFactory()


def get_factory() -> DependencyFactory:
    """Obtiene la instancia del factory."""
    return factory