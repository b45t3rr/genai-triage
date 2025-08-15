"""Adaptadores para diferentes proveedores de LLM."""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import SystemMessage, HumanMessage
from ....domain.interfaces import LLMInterface
from ....domain.exceptions import LLMConnectionError
from ...utils.config import get_settings


class BaseLLMAdapter(LLMInterface, ABC):
    """Clase base para adaptadores de LLM."""
    
    def __init__(self, model_name: str, temperature: float = 0.1):
        self.model_name = model_name
        self.temperature = temperature
        self.llm = self._create_llm()
    
    @abstractmethod
    def _create_llm(self):
        """Crea la instancia del LLM específico."""
        pass
    
    def generate_response(self, prompt: str, content: str) -> str:
        """Genera una respuesta usando el LLM."""
        try:
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=content)
            ]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            raise LLMConnectionError(f"Error al generar respuesta con {self.__class__.__name__}: {str(e)}")
    
    def is_available(self) -> bool:
        """Verifica si el LLM está disponible para uso."""
        try:
            # Intenta crear el LLM para verificar disponibilidad
            if self.llm is None:
                return False
            return True
        except Exception:
            return False


class OpenAIAdapter(BaseLLMAdapter):
    """Adaptador para OpenAI."""
    
    def _create_llm(self):
        settings = get_settings()
        if not settings.openai_api_key:
            raise LLMConnectionError("OpenAI API key no configurada")
        
        return ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            openai_api_key=settings.openai_api_key
        )


class XAIAdapter(BaseLLMAdapter):
    """Adaptador para XAI (usando OpenAI compatible API)."""
    
    def _create_llm(self):
        settings = get_settings()
        if not settings.xai_api_key:
            raise LLMConnectionError("XAI API key no configurada")
        
        return ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            openai_api_key=settings.xai_api_key,
            openai_api_base="https://api.x.ai/v1"
        )


class GeminiAdapter(BaseLLMAdapter):
    """Adaptador para Google Gemini."""
    
    def _create_llm(self):
        settings = get_settings()
        if not settings.gemini_api_key:
            raise LLMConnectionError("Gemini API key no configurada")
        
        return ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=self.temperature,
            google_api_key=settings.gemini_api_key
        )


class DeepSeekAdapter(BaseLLMAdapter):
    """Adaptador para DeepSeek (usando OpenAI compatible API)."""
    
    def _create_llm(self):
        settings = get_settings()
        if not settings.deepseek_api_key:
            raise LLMConnectionError("DeepSeek API key no configurada")
        
        return ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            openai_api_key=settings.deepseek_api_key,
            openai_api_base="https://api.deepseek.com/v1"
        )


class AnthropicAdapter(BaseLLMAdapter):
    """Adaptador para Anthropic Claude."""
    
    def _create_llm(self):
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise LLMConnectionError("Anthropic API key no configurada")
        
        return ChatAnthropic(
            model=self.model_name,
            temperature=self.temperature,
            anthropic_api_key=settings.anthropic_api_key
        )


class LLMFactory:
    """Factory para crear adaptadores de LLM."""
    
    _adapters = {
        "openai": OpenAIAdapter,
        "xai": XAIAdapter,
        "gemini": GeminiAdapter,
        "deepseek": DeepSeekAdapter,
        "anthropic": AnthropicAdapter
    }
    
    _default_models = {
        "openai": "gpt-5-nano",
        "xai": "grok-beta",
        "gemini": "gemini-pro",
        "deepseek": "deepseek-chat",
        "anthropic": "claude-3-sonnet-20240229"
    }
    
    @classmethod
    def create_llm(cls, provider: str, model_name: str = None, temperature: float = None) -> LLMInterface:
        """Crea un adaptador de LLM para el proveedor especificado."""
        if provider not in cls._adapters:
            raise ValueError(f"Proveedor no soportado: {provider}. Proveedores disponibles: {list(cls._adapters.keys())}")
        
        settings = get_settings()
        
        # Usar modelo por defecto si no se especifica
        if model_name is None:
            model_name = getattr(settings, f"{provider}_model", cls._default_models[provider])
        
        # Usar temperatura por defecto si no se especifica
        if temperature is None:
            temperature = getattr(settings, f"{provider}_temperature", 0.1)
        
        adapter_class = cls._adapters[provider]
        return adapter_class(model_name, temperature)
    
    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Obtiene la lista de proveedores soportados."""
        return list(cls._adapters.keys())
    
    @classmethod
    def parse_model_string(cls, model_string: str) -> tuple[str, str]:
        """Parsea un string de modelo en formato 'provider:model' o solo 'provider'."""
        if ":" in model_string:
            provider, model = model_string.split(":", 1)
            return provider.lower(), model
        else:
            provider = model_string.lower()
            return provider, cls._default_models.get(provider)