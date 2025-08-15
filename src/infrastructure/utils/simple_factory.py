"""Simplified dependency factory following Clean Architecture principles."""

from typing import Optional
from ...domain.interfaces import (
    PDFReaderInterface,
    LLMInterface,
    SecurityAnalyzerInterface,
    TriageAnalyzerInterface
)
from ...application.use_cases import (
    ReadPDFUseCase,
    TriageVulnerabilitiesUseCase,
    CompleteSecurityAnalysisUseCase
)
from ..adapters.external.tools.pdf_reader import PyPDF2Reader
# LLMFactory se importa dinámicamente para evitar importación circular
from ..services.agents import LangChainReportAnalyzer, StaticAnalysisAgent, TriageAgent
from .config import get_settings, validate_environment, get_available_providers


class SimpleDependencyFactory:
    """Simplified factory for creating and injecting dependencies."""
    
    def __init__(self):
        self._settings = get_settings()
        self._llm_cache = {}
    
    # Core adapters
    def create_pdf_reader(self) -> PDFReaderInterface:
        """Create PDF reader instance."""
        return PyPDF2Reader()
    
    def create_llm(
        self, 
        provider: Optional[str] = None, 
        model_name: Optional[str] = None, 
        temperature: Optional[float] = None
    ) -> LLMInterface:
        """Create LLM instance with caching."""
        # Use defaults if not provided
        provider = provider or self._settings.default_model_provider
        temperature = temperature or 0.1
        
        # Create cache key
        cache_key = f"{provider}:{model_name}:{temperature}"
        
        # Return cached instance if available
        if cache_key in self._llm_cache:
            return self._llm_cache[cache_key]
        
        # Validate provider configuration
        if not validate_environment(provider):
            available = get_available_providers()
            if available:
                provider = available[0]
            else:
                raise ValueError("No LLM providers configured. Set up at least one API key.")
        
        # Create and cache LLM instance
        # Importación dinámica para evitar importación circular
        from ..adapters.llm.llm_adapters import LLMFactory
        llm = LLMFactory.create_llm(provider, model_name, temperature)
        self._llm_cache[cache_key] = llm
        return llm
    
    # Domain services (analyzers)
    def create_security_analyzer(self, llm: Optional[LLMInterface] = None) -> SecurityAnalyzerInterface:
        """Create security analyzer."""
        if llm is None:
            llm = self.create_llm()
        return LangChainReportAnalyzer(llm)
    
    def create_triage_analyzer(self, llm: Optional[LLMInterface] = None) -> TriageAnalyzerInterface:
        """Create triage analyzer."""
        if llm is None:
            llm = self.create_llm()
        return TriageAgent(llm)
    
    def create_static_analyzer(
        self, 
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        llm: Optional[LLMInterface] = None
    ) -> StaticAnalysisAgent:
        """Create static analysis agent."""
        if llm is None:
            llm = self.create_llm(provider, model_name, temperature)
        return StaticAnalysisAgent(llm)
    
    # Use cases
    def create_read_pdf_use_case(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> ReadPDFUseCase:
        """Create PDF reading use case with all dependencies."""
        pdf_reader = self.create_pdf_reader()
        llm = self.create_llm(provider, model_name, temperature)
        security_analyzer = self.create_security_analyzer(llm)
        
        return ReadPDFUseCase(
            pdf_reader=pdf_reader,
            security_analyzer=security_analyzer,
            llm=llm
        )
    
    def create_triage_use_case(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> TriageVulnerabilitiesUseCase:
        """Create vulnerability triage use case."""
        llm = self.create_llm(provider, model_name, temperature)
        triage_analyzer = self.create_triage_analyzer(llm)
        
        return TriageVulnerabilitiesUseCase(
            triage_analyzer=triage_analyzer,
            llm=llm
        )
    
    def create_complete_analysis_use_case(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> CompleteSecurityAnalysisUseCase:
        """Create complete analysis use case."""
        # Create individual use cases
        read_pdf_use_case = self.create_read_pdf_use_case(provider, model_name, temperature)
        triage_use_case = self.create_triage_use_case(provider, model_name, temperature)
        
        # Create additional analyzers
        llm = self.create_llm(provider, model_name, temperature)
        static_analyzer = self.create_static_analyzer(llm)
        
        return CompleteSecurityAnalysisUseCase(
            read_pdf_use_case=read_pdf_use_case,
            triage_use_case=triage_use_case,
            static_analyzer=static_analyzer,
            llm=llm
        )
    
    # Utility methods
    def get_available_providers(self) -> list[str]:
        """Get list of available LLM providers."""
        return get_available_providers()
    
    def validate_provider(self, provider: str) -> bool:
        """Validate if provider is properly configured."""
        return validate_environment(provider)
    
    def clear_cache(self) -> None:
        """Clear LLM cache."""
        self._llm_cache.clear()


# Global factory instance
_factory_instance = None


def get_simple_factory() -> SimpleDependencyFactory:
    """Get global factory instance (singleton pattern)."""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = SimpleDependencyFactory()
    return _factory_instance


def reset_factory() -> None:
    """Reset factory instance (useful for testing)."""
    global _factory_instance
    _factory_instance = None