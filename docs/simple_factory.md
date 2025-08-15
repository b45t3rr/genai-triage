# Simplified Dependency Factory

El `SimpleDependencyFactory` es una implementación simplificada del patrón Factory que facilita la creación e inyección de dependencias en la aplicación de análisis de seguridad.

## Características Principales

### 🎯 **Simplicidad**
- API clara y fácil de usar
- Métodos descriptivos y bien documentados
- Configuración automática con valores por defecto

### 🚀 **Eficiencia**
- Cache automático de instancias LLM
- Validación automática de proveedores
- Gestión inteligente de recursos

### 🔧 **Flexibilidad**
- Soporte para múltiples proveedores LLM
- Configuración personalizable por caso de uso
- Fácil extensión y mantenimiento

## Uso Básico

### Obtener la Instancia del Factory

```python
from infrastructure.utils import get_simple_factory

# Obtener instancia singleton
factory = get_simple_factory()
```

### Crear Casos de Uso Completos

```python
# Análisis de PDF
pdf_use_case = factory.create_read_pdf_use_case(
    provider="openai",
    model_name="gpt-4",
    temperature=0.1
)

# Triage de vulnerabilidades
triage_use_case = factory.create_triage_use_case(
    provider="anthropic",
    model_name="claude-3-sonnet-20240229"
)

# Análisis completo
complete_use_case = factory.create_complete_analysis_use_case(
    provider="openai",
    temperature=0.2
)
```

### Crear Componentes Individuales

```python
# Adaptadores
pdf_reader = factory.create_pdf_reader()
llm = factory.create_llm(provider="openai")

# Analizadores
security_analyzer = factory.create_security_analyzer(llm)
triage_analyzer = factory.create_triage_analyzer(llm)
static_analyzer = factory.create_static_analyzer(llm)
```

## Métodos Disponibles

### Adaptadores Core

#### `create_pdf_reader() -> PDFReaderInterface`
Crea una instancia del lector de PDF.

#### `create_llm(provider, model_name, temperature) -> LLMInterface`
Crea una instancia LLM con cache automático.

**Parámetros:**
- `provider`: Proveedor LLM (openai, anthropic, google, ollama)
- `model_name`: Nombre del modelo específico
- `temperature`: Temperatura para la generación (0.0-1.0)

### Servicios de Dominio

#### `create_security_analyzer(llm) -> SecurityAnalyzerInterface`
Crea analizador de seguridad para reportes.

#### `create_triage_analyzer(llm) -> TriageAnalyzerInterface`
Crea analizador para triage de vulnerabilidades.

#### `create_static_analyzer(provider, model_name, temperature, llm) -> StaticAnalysisAgent`
Crea agente de análisis estático.

### Casos de Uso

#### `create_read_pdf_use_case(provider, model_name, temperature) -> ReadPDFUseCase`
Crea caso de uso completo para análisis de PDF.

#### `create_triage_use_case(provider, model_name, temperature) -> TriageVulnerabilitiesUseCase`
Crea caso de uso para triage de vulnerabilidades.

#### `create_complete_analysis_use_case(provider, model_name, temperature) -> CompleteSecurityAnalysisUseCase`
Crea caso de uso para análisis completo de seguridad.

### Utilidades

#### `get_available_providers() -> list[str]`
Retorna lista de proveedores LLM disponibles.

#### `validate_provider(provider: str) -> bool`
Valida si un proveedor está correctamente configurado.

#### `clear_cache() -> None`
Limpia el cache de instancias LLM.

## Configuración de Proveedores

### Variables de Entorno Requeridas

```bash
# OpenAI
OPENAI_API_KEY=your_openai_key

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_key

# Google
GOOGLE_API_KEY=your_google_key

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
```

### Validación Automática

El factory valida automáticamente la configuración:

```python
# Verificar proveedores disponibles
available = factory.get_available_providers()
print(f"Proveedores configurados: {available}")

# Validar proveedor específico
if factory.validate_provider("openai"):
    print("OpenAI está configurado correctamente")
```

## Cache y Optimización

### Cache Automático
Las instancias LLM se cachean automáticamente basándose en:
- Proveedor
- Nombre del modelo
- Temperatura

### Gestión de Memoria
```python
# Limpiar cache cuando sea necesario
factory.clear_cache()

# Útil para testing o gestión de memoria
from infrastructure.utils import reset_factory
reset_factory()  # Reinicia la instancia singleton
```

## Ejemplos Prácticos

### Análisis de PDF Completo

```python
from infrastructure.utils import get_simple_factory

factory = get_simple_factory()

# Crear caso de uso
use_case = factory.create_read_pdf_use_case(
    provider="openai",
    model_name="gpt-4",
    temperature=0.1
)

# Ejecutar análisis
result = use_case.execute("security_report.pdf")
print(f"Resumen: {result.summary}")
print(f"Vulnerabilidades: {len(result.vulnerabilities)}")
```

### Triage Personalizado

```python
# Crear componentes individuales para mayor control
llm = factory.create_llm(
    provider="anthropic",
    model_name="claude-3-sonnet-20240229",
    temperature=0.2
)

triage_analyzer = factory.create_triage_analyzer(llm)

# Usar directamente
result = triage_analyzer.analyze(security_data)
```

### Análisis Multi-Proveedor

```python
# Usar diferentes proveedores para diferentes tareas
pdf_use_case = factory.create_read_pdf_use_case(provider="openai")
triage_use_case = factory.create_triage_use_case(provider="anthropic")

# Combinar resultados
pdf_result = pdf_use_case.execute("report.pdf")
triage_result = triage_use_case.execute(pdf_result.raw_data)
```

## Ventajas sobre el Factory Original

### ✅ **Más Simple**
- Menos código boilerplate
- API más intuitiva
- Configuración automática

### ✅ **Mejor Performance**
- Cache inteligente
- Reutilización de instancias
- Validación eficiente

### ✅ **Más Mantenible**
- Código más limpio
- Mejor separación de responsabilidades
- Fácil testing

### ✅ **Más Flexible**
- Configuración por método
- Soporte para múltiples proveedores
- Extensible sin modificar código existente

## Testing

```python
import pytest
from infrastructure.utils import get_simple_factory, reset_factory

def test_factory_creation():
    factory = get_simple_factory()
    assert factory is not None
    
def test_pdf_reader_creation():
    factory = get_simple_factory()
    reader = factory.create_pdf_reader()
    assert reader is not None
    
def teardown_function():
    # Limpiar entre tests
    reset_factory()
```

## Migración desde Factory Original

### Cambios Necesarios

```python
# Antes
from infrastructure.utils import get_factory
factory = get_factory()
use_case = factory.create_read_pdf_use_case(provider, model, temp)

# Después
from infrastructure.utils import get_simple_factory
factory = get_simple_factory()
use_case = factory.create_read_pdf_use_case(provider, model, temp)
```

### Compatibilidad
El factory simplificado mantiene compatibilidad con la API existente mientras añade nuevas funcionalidades.

## Conclusión

El `SimpleDependencyFactory` proporciona una solución elegante y eficiente para la gestión de dependencias, siguiendo los principios de Clean Architecture mientras simplifica el uso diario de la aplicación.