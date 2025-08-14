import os
from typing import Optional, Literal
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    # Multi-Model Configuration
    default_model_provider: Literal["openai", "xai", "gemini", "deepseek", "anthropic"] = Field("openai", env="DEFAULT_MODEL_PROVIDER")
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-5-nano", env="OPENAI_MODEL")
    openai_temperature: float = Field(0.1, env="OPENAI_TEMPERATURE")
    
    # XAI Configuration
    xai_api_key: Optional[str] = Field(None, env="XAI_API_KEY")
    xai_model: str = Field("grok-beta", env="XAI_MODEL")
    xai_temperature: float = Field(0.1, env="XAI_TEMPERATURE")
    
    # Gemini Configuration
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    gemini_model: str = Field("gemini-pro", env="GEMINI_MODEL")
    gemini_temperature: float = Field(0.1, env="GEMINI_TEMPERATURE")
    
    # DeepSeek Configuration
    deepseek_api_key: Optional[str] = Field(None, env="DEEPSEEK_API_KEY")
    deepseek_model: str = Field("deepseek-chat", env="DEEPSEEK_MODEL")
    deepseek_temperature: float = Field(0.1, env="DEEPSEEK_TEMPERATURE")
    
    # Anthropic Configuration
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field("claude-3-sonnet-20240229", env="ANTHROPIC_MODEL")
    anthropic_temperature: float = Field(0.1, env="ANTHROPIC_TEMPERATURE")
    
    # Application Configuration
    app_name: str = Field("PDF Report Analyzer", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    debug: bool = Field(False, env="DEBUG")
    
    # File Configuration
    max_file_size_mb: int = Field(50, env="MAX_FILE_SIZE_MB")
    supported_extensions: list = Field(['.pdf'], env="SUPPORTED_EXTENSIONS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignorar campos extra del .env


# Instancia global de configuración
settings = Settings()


def get_settings() -> Settings:
    """Obtiene la configuración de la aplicación."""
    return settings


def validate_environment(provider: str = None) -> bool:
    """Valida que las variables de entorno necesarias estén configuradas."""
    try:
        settings = get_settings()
        if provider is None:
            provider = settings.default_model_provider
        
        api_key_map = {
            "openai": settings.openai_api_key,
            "xai": settings.xai_api_key,
            "gemini": settings.gemini_api_key,
            "deepseek": settings.deepseek_api_key,
            "anthropic": settings.anthropic_api_key
        }
        
        return bool(api_key_map.get(provider))
    except Exception:
        return False


def get_available_providers() -> list[str]:
    """Obtiene la lista de proveedores disponibles (con API keys configuradas)."""
    settings = get_settings()
    providers = []
    
    if settings.openai_api_key:
        providers.append("openai")
    if settings.xai_api_key:
        providers.append("xai")
    if settings.gemini_api_key:
        providers.append("gemini")
    if settings.deepseek_api_key:
        providers.append("deepseek")
    if settings.anthropic_api_key:
        providers.append("anthropic")
    
    return providers