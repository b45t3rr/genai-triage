# 🛡️ Triage-5: Sistema Inteligente de Análisis de Seguridad

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![LangChain](https://img.shields.io/badge/LangChain-Enabled-green.svg)
![Clean Architecture](https://img.shields.io/badge/Architecture-Clean-orange.svg)
![License](https://img.shields.io/badge/License-Educational-red.svg)

*Un sistema avanzado de análisis de vulnerabilidades que combina IA, análisis estático y dinámico para el triage inteligente de reportes de seguridad*

</div>

## 🚀 Características Principales

### 🤖 **Arquitectura Multi-Agente Inteligente**
- **Agentes Especializados**: Sistema de agentes autónomos con capacidades cognitivas avanzadas
- **Orquestación Inteligente**: Coordinación automática entre agentes especializados
- **Análisis Colaborativo**: Síntesis de resultados mediante consenso inter-agente
- **Adaptabilidad Continua**: Agentes que aprenden y se adaptan dinámicamente

### 🔍 **Agentes Especializados**
- **📄 Agente Extractor de PDFs**: Procesamiento inteligente de reportes de seguridad
- **🔧 Agente de Análisis Estático**: Detección autónoma de patrones y vulnerabilidades
- **🌐 Agente de Análisis Dinámico**: Validación automática mediante pruebas adaptativas
- **⚖️ Agente de Triage**: Priorización cognitiva basada en correlación multi-dimensional
- **📊 Orquestador Multi-Agente**: Coordinación y síntesis colaborativa de resultados

### 🏗️ **Arquitectura Limpia**
- **Clean Architecture**: Separación clara de responsabilidades
- **SOLID Principles**: Código mantenible y extensible
- **Dependency Injection**: Factory pattern para gestión de dependencias
- **Domain-Driven Design**: Modelado rico del dominio de seguridad

*Un reporte explicativo con mas información como ejemplos, resultados y analisis se encuentra [AQUI](https://github.com/b45t3rr/genai-triage/blob/main/docs/report.md)*

## 📋 Tabla de Contenidos

- [🛠️ Instalación](#️-instalación)
- [⚙️ Configuración](#️-configuración)
- [🚀 Inicio Rápido](#-inicio-rápido)
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

## 🚀 Inicio Rápido

### 🐳 Con Docker (Recomendado)

```bash
# 1. Clonar el repositorio
git clone <repository-url>
cd triage-5

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu API key de OpenAI u otro proveedor

# 3. Levantar servicios con Docker
docker-compose up -d

# 4. Verificar que los servicios estén corriendo
docker-compose ps

# 5. Instalar dependencias Python (si no usas el contenedor principal)
pip install -r requirements.txt
```

### 🎯 Ejemplo de Análisis Completo

```bash
# Levantar la aplicación vulnerable de prueba
cd testing-assets/vuln-app-main/
docker-compose up -d
cd ../..

# Ejecutar análisis completo con orquestación multi-agente
python app.py orchestrate-agents \
  --pdf testing-assets/report.pdf \
  --source testing-assets/vuln-app-main/ \
  --url http://localhost:5000 \
  --output analisis-completo.json \
  --model openai \
  --mongodb \
  --verbose

# Ver resultados
cat analisis-completo.json | jq .

# Acceder a Mongo Express para ver datos persistidos
# http://localhost:8081 (admin/pass)
```

### 🔧 Comandos Útiles de Docker

```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f mongodb

# Reiniciar servicios
docker-compose restart

# Detener servicios
docker-compose down

# Limpiar volúmenes (⚠️ elimina datos)
docker-compose down -v
```

## 🎯 Uso Rápido

### Análisis Básico de PDF

```bash
# Activar agente extractor de PDFs
python app.py activate-pdf-agent --pdf reporte.pdf --output resultado.json

# Con configuración específica del agente
python app.py activate-pdf-agent --pdf reporte.pdf --model anthropic --temperature 0.2
```

### Triage de Vulnerabilidades

```bash
# Coordinar agente de triage
python app.py coordinate-triage-agent --report resultado.json --output triage.json
```

### Análisis Completo

```bash
# Orquestación multi-agente integral
python app.py orchestrate-agents \
  --pdf reporte.pdf \
  --source ./codigo-fuente \
  --url http://localhost:8080 \
  --output analisis-completo.json
```

## 📖 Comandos Disponibles

### 📄 `activate-pdf-agent` - Agente Extractor de PDFs
Activa el agente especializado para procesamiento cognitivo de reportes PDF.

```bash
python app.py activate-pdf-agent --pdf archivo.pdf [opciones]
```

**Opciones:**
- `--output, -o`: Archivo de salida JSON
- `--model, -m`: Proveedor LLM (openai, anthropic, gemini, xai, deepseek)
- `--temperature, -t`: Temperatura del modelo (0.0-1.0)
- `--verbose, -v`: Información detallada
- `--mongodb`: Guardar en MongoDB

### 🔧 `activate-static-agent` - Agente de Análisis Estático
Despliega el agente especializado para detección inteligente de patrones y vulnerabilidades.

```bash
python app.py activate-static-agent --pdf reporte.pdf --source ./codigo [opciones]
```

### 🌐 `deploy-dynamic-agent` - Agente de Análisis Dinámico
Despliega el agente especializado para validación autónoma mediante pruebas adaptativas.

```bash
python app.py deploy-dynamic-agent --pdf reporte.pdf --url http://target.com [opciones]
```

### ⚖️ `coordinate-triage-agent` - Agente de Triage
Coordina el agente especializado para priorización cognitiva multi-dimensional.

```bash
python app.py coordinate-triage-agent --report reporte.json [opciones]
```

### 📊 `orchestrate-agents` - Orquestación Multi-Agente
Orquesta la colaboración entre todos los agentes especializados para análisis integral.

```bash
python app.py orchestrate-agents --pdf reporte.pdf --source ./codigo --url http://target.com [opciones]
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

### 🎯 Casos de Uso Multi-Agente Principales

1. **📄 ActivatePDFAgentUseCase**: Activación del agente extractor de PDFs
2. **⚖️ CoordinateTriageAgentUseCase**: Coordinación del agente de triage
3. **📊 OrchestrateAgentsUseCase**: Orquestación integral de agentes especializados

### 🤖 Ecosistema de Agentes Especializados

- **📄 Agente Extractor de PDFs**: Procesamiento cognitivo de reportes con comprensión contextual
- **🔧 Agente de Análisis Estático**: Detección inteligente de patrones con adaptación automática
- **🌐 Agente de Análisis Dinámico**: Validación autónoma con generación dinámica de payloads
- **⚖️ Agente de Triage**: Priorización multi-dimensional con consenso inteligente
- **🗄️ Agente de Persistencia**: Gestión inteligente de datos con optimización automática

## 🧪 Ejemplos

### 📄 Activación del Agente Extractor de PDFs con Diferentes Modelos

```bash
# Con OpenAI GPT-4
python app.py activate-pdf-agent --pdf security-report.pdf --model openai:gpt-4

# Con Anthropic Claude
python app.py activate-pdf-agent --pdf security-report.pdf --model anthropic:claude-3-sonnet-20240229

# Con Google Gemini
python app.py activate-pdf-agent --pdf security-report.pdf --model gemini:gemini-pro
```

### 🔍 Despliegue del Agente de Análisis Estático

```bash
# Activar agente para código Python
python app.py activate-static-agent --pdf report.pdf --source ./python-app/

# Desplegar agente para aplicación web
python app.py activate-static-agent --pdf report.pdf --source ./web-app/ --verbose
```

### 🌐 Despliegue del Agente de Análisis Dinámico

```bash
# Desplegar agente para aplicación local
python app.py deploy-dynamic-agent --pdf report.pdf --url http://localhost:8080

# Coordinar agente con configuración específica
python app.py deploy-dynamic-agent \
  --pdf report.pdf \
  --url https://target.example.com \
  --model anthropic \
  --temperature 0.1 \
  --verbose
```

### 📊 Orquestación Multi-Agente Integral

```bash
# Orquestación completa de agentes especializados
python app.py orchestrate-agents \
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

### 🏭 Factory Pattern para Agentes Especializados

```python
from infrastructure.utils import get_agent_factory

# Obtener factory de agentes
agent_factory = get_agent_factory()

# Crear agentes especializados
pdf_agent = agent_factory.create_pdf_agent(
    provider="openai",
    model_name="gpt-4",
    temperature=0.1
)

# Activar agente
result = pdf_agent.activate("report.pdf")
```

### 🔄 Orquestación Multi-Agente

```python
# Desplegar diferentes agentes con modelos especializados
pdf_agent = agent_factory.create_pdf_agent(provider="openai")
triage_agent = agent_factory.create_triage_agent(provider="anthropic")

# Coordinar agentes colaborativamente
pdf_result = pdf_agent.activate("report.pdf")
triage_result = triage_agent.coordinate(pdf_result.cognitive_data)
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

# Ejecutar ejemplos de agentes
python examples/multi_agent_orchestration.py
```

### 📝 Guías de Contribución

1. **🔀 Fork** el repositorio
2. **🌿 Crear** una rama para tu feature
3. **✅ Commit** tus cambios
4. **📤 Push** a la rama
5. **🔄 Crear** un Pull Request

### 🏗️ Arquitectura Multi-Agente de Contribución

- **Agent Layer**: Agentes especializados con capacidades cognitivas
- **Orchestration Layer**: Coordinación y síntesis inter-agente
- **Cognitive Layer**: Procesamiento inteligente y adaptativo
- **Communication Layer**: Protocolos de comunicación entre agentes

## 📄 Licencia

**⚠️ IMPORTANTE**: Este sistema multi-agente es para fines educativos y de investigación en seguridad. Los agentes especializados requieren configuración adecuada y no deben ser desplegados en entornos de producción sin las debidas precauciones de seguridad.

---

<div align="center">

**🛡️ Desarrollado como parte de un desafio**

*Recuerda: Con gran poder viene gran responsabilidad* 🕷️

</div>