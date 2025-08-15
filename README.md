# 🛡️ Triage-5: Sistema Inteligente de Análisis de Seguridad

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![LangChain](https://img.shields.io/badge/LangChain-Enabled-green.svg)
![Clean Architecture](https://img.shields.io/badge/Architecture-Clean-orange.svg)
![License](https://img.shields.io/badge/License-Educational-red.svg)

*Un sistema avanzado de análisis de vulnerabilidades que combina IA, análisis estático y dinámico para el triage inteligente de reportes de seguridad*

</div>

## 🚀 Características Principales

### 🤖 **Análisis Inteligente Multi-Modelo**
- **Soporte Multi-LLM**: OpenAI GPT, Anthropic Claude, Google Gemini, XAI Grok, DeepSeek
- **Análisis de PDFs**: Extracción y procesamiento inteligente de reportes de seguridad
- **Triage Automatizado**: Priorización y clasificación automática de vulnerabilidades
- **Validación Cruzada**: Correlación entre reportes y código fuente real

### 🔍 **Capacidades de Análisis**
- **📄 Análisis de Reportes PDF**: Extracción estructurada de vulnerabilidades
- **🔧 Análisis Estático**: Integración con Semgrep para análisis de código
- **🌐 Análisis Dinámico**: Pruebas automatizadas contra aplicaciones web
- **⚖️ Triage Inteligente**: Priorización basada en impacto y explotabilidad
- **📊 Análisis Completo**: Combinación de todas las metodologías

### 🏗️ **Arquitectura Limpia**
- **Clean Architecture**: Separación clara de responsabilidades
- **SOLID Principles**: Código mantenible y extensible
- **Dependency Injection**: Factory pattern para gestión de dependencias
- **Domain-Driven Design**: Modelado rico del dominio de seguridad

## 📋 Tabla de Contenidos

- [🛠️ Instalación](#️-instalación)
- [⚙️ Configuración](#️-configuración)
- [🎯 Uso Rápido](#-uso-rápido)
- [📖 Comandos Disponibles](#-comandos-disponibles)
- [🏛️ Arquitectura](#️-arquitectura)
- [🧪 Ejemplos](#-ejemplos)
- [🐳 Docker](#-docker)
- [🤝 Contribuir](#-contribuir)

## 🛠️ Instalación

### Requisitos Previos
- Python 3.8+
- pip o poetry
- Docker (opcional)
- MongoDB (opcional)

### Instalación Rápida

```bash
# Clonar el repositorio
git clone <repository-url>
cd triage-5

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys
```

### Dependencias Principales

```txt
🤖 LangChain - Framework de IA
📄 PyPDF2 - Procesamiento de PDFs
🎨 Typer + Rich - CLI moderna
🔍 Semgrep - Análisis estático
🗄️ PyMongo - Base de datos (opcional)
🐍 Pydantic - Validación de datos
```

## ⚙️ Configuración

### 🔑 API Keys

Configura al menos una API key en tu archivo `.env`:

```bash
# OpenAI (Recomendado)
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4

# Anthropic Claude
ANTHROPIC_API_KEY=your-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Google Gemini
GEMINI_API_KEY=your-key-here

# XAI Grok
XAI_API_KEY=your-key-here

# DeepSeek
DEEPSEEK_API_KEY=your-key-here
```

### 🗄️ MongoDB (Opcional)

```bash
# Para persistencia de resultados
MONGO_USERNAME=admin
MONGO_PASSWORD=password123
MONGO_DATABASE=vulnerability_validation
MONGODB_URI=mongodb://admin:password123@localhost:27017/vulnerability_validation
```

## 🎯 Uso Rápido

### Análisis Básico de PDF

```bash
# Analizar un reporte PDF
python app.py read --pdf reporte.pdf --output resultado.json

# Con modelo específico
python app.py read --pdf reporte.pdf --model anthropic --temperature 0.2
```

### Triage de Vulnerabilidades

```bash
# Procesar reporte existente
python app.py triage --report resultado.json --output triage.json
```

### Análisis Completo

```bash
# Análisis integral: PDF + Código + Pruebas dinámicas
python app.py complete-analysis \
  --pdf reporte.pdf \
  --source ./codigo-fuente \
  --url http://localhost:8080 \
  --output analisis-completo.json
```

## 📖 Comandos Disponibles

### 📄 `read` - Análisis de PDF
Extrae y analiza vulnerabilidades de reportes PDF.

```bash
python app.py read --pdf archivo.pdf [opciones]
```

**Opciones:**
- `--output, -o`: Archivo de salida JSON
- `--model, -m`: Proveedor LLM (openai, anthropic, gemini, xai, deepseek)
- `--temperature, -t`: Temperatura del modelo (0.0-1.0)
- `--verbose, -v`: Información detallada
- `--mongodb`: Guardar en MongoDB

### 🔧 `static-scan` - Análisis Estático
Analiza código fuente usando Semgrep y correlaciona con reporte PDF.

```bash
python app.py static-scan --pdf reporte.pdf --source ./codigo [opciones]
```

### 🌐 `dynamic-scan` - Análisis Dinámico
Realiza pruebas automatizadas contra aplicaciones web.

```bash
python app.py dynamic-scan --pdf reporte.pdf --url http://target.com [opciones]
```

### ⚖️ `triage` - Triage Inteligente
Prioriza y clasifica vulnerabilidades basado en impacto y explotabilidad.

```bash
python app.py triage --report reporte.json [opciones]
```

### 📊 `complete-analysis` - Análisis Integral
Combina todas las metodologías en un análisis completo.

```bash
python app.py complete-analysis --pdf reporte.pdf --source ./codigo --url http://target.com [opciones]
```

### 🧪 Comandos de Utilidad

```bash
# Probar conexión con LLM
python app.py test --model openai

# Verificar versión
python app.py version

# Probar MongoDB
python app.py test-mongodb
```

## 🏛️ Arquitectura

### 📁 Estructura del Proyecto

```
triage-5/
├── 📱 app.py                    # Punto de entrada principal
├── 🐳 docker-compose.yml       # Configuración Docker
├── 📋 requirements.txt         # Dependencias Python
├── 🔧 .env.example             # Plantilla de configuración
├── 📚 docs/                    # Documentación
├── 🧪 examples/                # Ejemplos de uso
├── 🗃️ testing-assets/          # Aplicación vulnerable de prueba
└── 📦 src/
    ├── 🎯 application/         # Casos de uso
    │   └── use_cases/
    ├── 🏛️ domain/              # Lógica de negocio
    │   ├── entities.py
    │   ├── interfaces.py
    │   ├── models/
    │   ├── services/
    │   └── value_objects/
    ├── 🔌 infrastructure/      # Adaptadores externos
    │   ├── adapters/
    │   ├── services/
    │   └── utils/
    └── 🖥️ presentation/        # Interfaz de usuario
        ├── cli.py
        ├── cli_new.py
        └── commands/
```

### 🎯 Casos de Uso Principales

1. **📄 ReadPDFUseCase**: Extracción de vulnerabilidades de PDFs
2. **⚖️ TriageVulnerabilitiesUseCase**: Priorización inteligente
3. **📊 CompleteSecurityAnalysisUseCase**: Análisis integral

### 🤖 Agentes Especializados

- **📄 PDFAnalyzerAgent**: Procesamiento de reportes PDF
- **🔧 StaticAnalysisAgent**: Análisis de código estático
- **🌐 DynamicAgent**: Pruebas dinámicas automatizadas
- **⚖️ TriageAgent**: Clasificación y priorización

## 🧪 Ejemplos

### 📄 Análisis de PDF con Diferentes Modelos

```bash
# Con OpenAI GPT-4
python app.py read --pdf security-report.pdf --model openai:gpt-4

# Con Anthropic Claude
python app.py read --pdf security-report.pdf --model anthropic:claude-3-sonnet-20240229

# Con Google Gemini
python app.py read --pdf security-report.pdf --model gemini:gemini-pro
```

### 🔍 Análisis Estático con Semgrep

```bash
# Analizar código Python
python app.py static-scan --pdf report.pdf --source ./python-app/

# Analizar aplicación web
python app.py static-scan --pdf report.pdf --source ./web-app/ --verbose
```

### 🌐 Pruebas Dinámicas

```bash
# Probar aplicación local
python app.py dynamic-scan --pdf report.pdf --url http://localhost:8080

# Probar con configuración específica
python app.py dynamic-scan \
  --pdf report.pdf \
  --url https://target.example.com \
  --model anthropic \
  --temperature 0.1 \
  --verbose
```

### 📊 Análisis Completo

```bash
# Análisis integral de una aplicación
python app.py complete-analysis \
  --pdf security-assessment.pdf \
  --source ./vulnerable-app/ \
  --url http://localhost:5000 \
  --model openai \
  --output complete-analysis.json \
  --mongodb \
  --verbose
```

## 🐳 Docker

### 🚀 Inicio Rápido con Docker

```bash
# Iniciar MongoDB
docker-compose up -d

# Verificar servicios
docker-compose ps

# Ver logs
docker-compose logs -f
```

### 🗄️ Servicios Incluidos

- **MongoDB**: Base de datos para persistencia
- **Mongo Express**: Interfaz web de administración (puerto 8081)

### 🧪 Aplicación de Prueba

El proyecto incluye una aplicación web vulnerable para testing:

```bash
cd testing-assets/vuln-app-main/
docker-compose up --build
```

**Credenciales por defecto:**
- Admin: `admin` / `admin123`
- Usuario: `user1` / `user123`

**Vulnerabilidades incluidas:**
- 💉 SQL Injection
- 🚨 XSS (Cross-Site Scripting)
- 🔗 SSRF (Server-Side Request Forgery)
- 🔓 IDOR (Insecure Direct Object Reference)
- 📁 Path Traversal

## 🎨 Características Avanzadas

### 🏭 Factory Pattern Simplificado

```python
from infrastructure.utils import get_simple_factory

# Obtener factory
factory = get_simple_factory()

# Crear casos de uso
pdf_use_case = factory.create_read_pdf_use_case(
    provider="openai",
    model_name="gpt-4",
    temperature=0.1
)

# Ejecutar análisis
result = pdf_use_case.execute("report.pdf")
```

### 🔄 Análisis Multi-Proveedor

```python
# Usar diferentes modelos para diferentes tareas
pdf_analyzer = factory.create_read_pdf_use_case(provider="openai")
triage_analyzer = factory.create_triage_use_case(provider="anthropic")

# Combinar resultados
pdf_result = pdf_analyzer.execute("report.pdf")
triage_result = triage_analyzer.execute(pdf_result.raw_data)
```

### 📊 Reportes Estructurados

Todos los análisis generan reportes JSON estructurados con:

- 📋 **Metadatos**: Información del análisis
- 🔍 **Vulnerabilidades**: Lista detallada con severidad
- 💡 **Recomendaciones**: Sugerencias de remediación
- 📈 **Métricas**: Estadísticas del análisis
- 🏷️ **Triage**: Priorización y clasificación

## 🤝 Contribuir

### 🛠️ Desarrollo

```bash
# Configurar entorno de desarrollo
git clone <repository-url>
cd triage-5
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Ejecutar ejemplos
python examples/simple_factory_usage.py
```

### 📝 Guías de Contribución

1. **🔀 Fork** el repositorio
2. **🌿 Crear** una rama para tu feature
3. **✅ Commit** tus cambios
4. **📤 Push** a la rama
5. **🔄 Crear** un Pull Request

### 🏗️ Arquitectura de Contribución

- **Domain Layer**: Lógica de negocio pura
- **Application Layer**: Casos de uso y orquestación
- **Infrastructure Layer**: Adaptadores y servicios externos
- **Presentation Layer**: Interfaces de usuario

## 📄 Licencia

**⚠️ IMPORTANTE**: Este proyecto es solo para fines educativos y de investigación en seguridad. No debe ser utilizado en entornos de producción sin las debidas precauciones de seguridad.

## 🙏 Agradecimientos

- 🤖 **LangChain**: Framework de IA
- 🔍 **Semgrep**: Análisis estático
- 🎨 **Rich**: Interfaz de terminal moderna
- 🐳 **Docker**: Containerización
- 🗄️ **MongoDB**: Base de datos

---

<div align="center">

**🛡️ Desarrollado con ❤️ para la comunidad de seguridad**

*Recuerda: Con gran poder viene gran responsabilidad* 🕷️

</div>