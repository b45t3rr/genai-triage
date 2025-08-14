# PDF Report Analyzer

Aplicación para analizar reportes de seguridad en PDF usando LangChain y OpenAI. Extrae texto de documentos PDF y los estructura en formato JSON siguiendo un esquema específico para reportes de vulnerabilidades.

## Características

- ✅ **Clean Architecture**: Separación clara de responsabilidades en capas
- ✅ **Principios SOLID**: Código mantenible y extensible
- ✅ **Soporte Multi-Modelo**: Compatible con OpenAI, XAI (Grok), Gemini, DeepSeek y Anthropic
- ✅ **LangChain Integration**: Orquestación de agentes de IA
- ✅ **PyPDF2**: Extracción robusta de texto de PDFs
- ✅ **CLI Moderna**: Interfaz de línea de comandos con Rich
- ✅ **Animación de Carga**: Indicadores visuales con símbolos giratorios (| / — \)
- ✅ **Manejo de Errores**: Excepciones personalizadas y mensajes claros
- ✅ **Configuración Flexible**: Variables de entorno y configuración centralizada
- ✅ **Análisis Estático**: Validación de vulnerabilidades mediante análisis de código con Semgrep
- ✅ **Análisis Dinámico**: Validación de vulnerabilidades mediante explotación en vivo
- ✅ **Herramientas de Red**: Curl, wget, nmap, telnet, netcat para pruebas de penetración
- ✅ **Metodología ReACT**: Agentes inteligentes que razonan y actúan iterativamente

## Arquitectura

```
src/
├── domain/              # Entidades y reglas de negocio
│   ├── entities.py      # Modelos de datos (Pydantic)
│   ├── interfaces.py    # Contratos/Interfaces
│   └── exceptions.py    # Excepciones personalizadas
├── application/         # Casos de uso
│   └── use_cases.py     # Lógica de aplicación
├── infrastructure/      # Implementaciones técnicas
│   ├── pdf_reader.py    # Lector de PDF (PyPDF2)
│   ├── report_analyzer.py # Analizador con LangChain
│   ├── config.py        # Configuración
│   └── factory.py       # Inyección de dependencias
└── presentation/        # Interfaz de usuario
    └── cli.py           # CLI con Typer y Rich
```

## Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone <repository-url>
   cd triage-5
   ```

2. **Crear entorno virtual**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # o
   .venv\Scripts\activate     # Windows
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**:
   ```bash
   cp .env.example .env
   # Editar .env y agregar tu OPENAI_API_KEY
   ```

## Configuración

Crea un archivo `.env` con las siguientes variables. **Configure al menos una API key** para usar la aplicación:

```env
# =============================================================================
# CONFIGURACIÓN MULTI-MODELO LLM
# Configure al menos una API key para usar la aplicación
# =============================================================================

# Proveedor por defecto (OPCIONAL)
DEFAULT_MODEL_PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.1

# XAI (Grok) Configuration
XAI_API_KEY=your_xai_api_key_here
XAI_MODEL=grok-beta
XAI_TEMPERATURE=0.1

# Google Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro
GEMINI_TEMPERATURE=0.1

# DeepSeek Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TEMPERATURE=0.1

# Anthropic Claude Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-sonnet-20240229
ANTHROPIC_TEMPERATURE=0.1

# Configuración de la aplicación (OPCIONAL)
DEBUG=false
MAX_FILE_SIZE_MB=50
```

## Uso

### Comandos Principales

1. **Analizar un PDF** (usa el proveedor por defecto):
   ```bash
   python app.py read --pdf archivo.pdf
   ```

2. **Usar diferentes proveedores de LLM**:
   ```bash
   # OpenAI (por defecto)
   python app.py read --pdf archivo.pdf --model openai
   
   # XAI (Grok)
   python app.py read --pdf archivo.pdf --model xai
   
   # Google Gemini
   python app.py read --pdf archivo.pdf --model gemini
   
   # DeepSeek
   python app.py read --pdf archivo.pdf --model deepseek
   
   # Anthropic Claude
   python app.py read --pdf archivo.pdf --model anthropic
   ```

3. **Especificar modelo específico**:
   ```bash
   # Formato: proveedor:modelo
   python app.py read --pdf archivo.pdf --model openai:gpt-4
   python app.py read --pdf archivo.pdf --model anthropic:claude-3-opus-20240229
   python app.py read --pdf archivo.pdf --model gemini:gemini-1.5-pro
   ```

4. **Guardar resultado en archivo**:
   ```bash
   python app.py read --pdf archivo.pdf --output resultado.json
   ```

5. **Configurar temperatura y modo verbose**:
   ```bash
   python app.py read --pdf archivo.pdf --model openai:gpt-4 --temperature 0.2 --verbose
   ```

6. **Análisis estático de vulnerabilidades**:
   ```bash
   # Validar vulnerabilidades mediante análisis de código
   python app.py static-scan --pdf reporte.pdf --source /path/to/source/code
   
   # Con opciones adicionales
   python app.py static-scan --pdf reporte.pdf --source /path/to/source/code --output resultado.json --model openai:gpt-4 --verbose --mongodb
   ```

7. **Análisis dinámico de vulnerabilidades**:
   ```bash
   # Validar vulnerabilidades mediante explotación en vivo
   python app.py dynamic-scan --pdf reporte.pdf --url http://localhost:8080
   
   # Con opciones adicionales
   python app.py dynamic-scan --pdf reporte.pdf --url https://target-app.com --output resultado.json --model openai:gpt-4 --verbose --mongodb
   ```

### Comandos Auxiliares

- **Probar conexión con diferentes proveedores**:
  ```bash
  # Probar proveedor por defecto
  python app.py test
  
  # Probar proveedores específicos
  python app.py test --model openai
  python app.py test --model xai
  python app.py test --model gemini
  python app.py test --model deepseek
  python app.py test --model anthropic
  
  # Probar modelos específicos
  python app.py test --model openai:gpt-4
  python app.py test --model anthropic:claude-3-opus-20240229
  ```

- **Ver versión**:
  ```bash
  python app.py version
  ```

- **Ayuda**:
  ```bash
  python app.py --help
  python app.py read --help
  python app.py static-scan --help
  python app.py dynamic-scan --help
  python app.py test --help
  ```

### Animación de Carga

La aplicación incluye una animación de carga personalizada que muestra el progreso de las operaciones:

- **Símbolos giratorios**: `|` `/` `—` `\` que rotan cada 0.2 segundos
- **Mensajes dinámicos**: El texto cambia según la etapa del proceso
- **Indicadores de progreso**: Muestra qué está haciendo la aplicación en tiempo real

**Ejemplo de flujo de animación**:
```
| Inicializando componentes...
/ Leyendo archivo PDF...
— Enviando contenido al modelo de IA...
\ Analizando estructura del reporte...
| Generando JSON estructurado...
✓ Análisis completado
```

**Demo de animación**:
```bash
python demo_loading_animation.py
```

## Esquema de Salida JSON

La aplicación genera un JSON estructurado con el siguiente esquema:

```json
{
  "documento": {
    "titulo": "string",
    "fecha": "string",
    "autor": "string",
    "tipo_documento": "string",
    "numero_paginas": "number"
  },
  "resumen_ejecutivo": "string",
  "hallazgos_principales": [
    {
      "categoria": "string",
      "descripcion": "string",
      "severidad": "string",
      "impacto": "string",
      "detailed_proof_of_concept": "string"
    }
  ],
  "recomendaciones": [
    {
      "prioridad": "string",
      "accion": "string",
      "descripcion": "string"
    }
  ],
  "datos_tecnicos": {
    "entorno": "string",
    "endpoints_pruebas": ["string"],
    "credenciales_utilizadas": {},
    "observaciones_abiertas": ["string"]
  },
  "conclusiones": "string",
  "informacion_adicional": {
    "nota": "string",
    "recomendaciones_adicionales": ["string"]
  }
}
```

## Ejemplos

### Ejemplo Básico
```bash
# Analizar el PDF de prueba
python app.py read --pdf testing-assets/report.pdf
```

### Ejemplo Avanzado
```bash
# Análisis completo con configuración personalizada
python app.py read \
  --pdf testing-assets/report.pdf \
  --output analysis_result.json \
  --model gpt-4 \
  --temperature 0.1 \
  --verbose
```

### Ejemplos con MongoDB
```bash
# Guardar resultado solo en MongoDB
python app.py read \
  --pdf testing-assets/report.pdf \
  --mongodb

# Guardar en archivo Y en MongoDB
python app.py read \
  --pdf testing-assets/report.pdf \
  --output result.json \
  --mongodb \
  --verbose

# Probar conexión con MongoDB
python app.py test-mongodb
```

### Análisis Estático con Static-Agent
```bash
# Validar vulnerabilidades usando análisis estático
python app.py static-scan \
  --pdf testing-assets/report.pdf \
  --source testing-assets/vuln-app-main/

# Análisis completo con salida detallada
python app.py static-scan \
  --pdf testing-assets/report.pdf \
  --source testing-assets/vuln-app-main/ \
  --output static_analysis_result.json \
  --model gpt-4 \
  --verbose

# Guardar resultado en MongoDB
python app.py static-scan \
  --pdf testing-assets/report.pdf \
  --source testing-assets/vuln-app-main/ \
  --mongodb \
  --verbose
```

#### Características del Static-Agent

- **Análisis de Reporte PDF**: Utiliza el agente `pdf_analyzer` existente
- **Escaneo con Semgrep**: Ejecuta análisis estático automático del código fuente
- **Metodología ReACT**: Reasoning and Action para validación iterativa
- **Correlación Inteligente**: Relaciona vulnerabilidades del reporte con hallazgos de semgrep
- **Lectura de Archivos**: Herramientas para examinar código fuente específico
- **Validación Automática**: Determina si las vulnerabilidades son realmente explotables

#### Formato de Salida del Static-Agent

```json
{
  "vulnerabilidades_reportadas": 5,
  "vulnerabilidades_vulnerables": 3,
  "timestamp": "2024-01-15T10:30:00",
  "vulnerabilidades": [
    {
      "nombre": "SQL Injection",
      "estado": "vulnerable",
      "severidad": "critica",
      "detalles": "THOUGHT: Analizando vulnerabilidad SQL Injection...",
      "evidencia": "query = 'SELECT * FROM users WHERE id = ' + user_id"
    }
  ]
}
```

### Análisis Dinámico con Dynamic-Agent

```bash
# Validar vulnerabilidades mediante explotación en vivo
python app.py dynamic-scan \
  --pdf testing-assets/report.pdf \
  --url http://localhost:8080

# Análisis completo con salida detallada
python app.py dynamic-scan \
  --pdf testing-assets/report.pdf \
  --url https://target-application.com \
  --output dynamic_analysis_result.json \
  --model gpt-4 \
  --verbose

# Guardar resultado en MongoDB
python app.py dynamic-scan \
  --pdf testing-assets/report.pdf \
  --url http://vulnerable-app.local \
  --mongodb \
  --verbose
```

#### Características del Dynamic-Agent

- **Análisis de Reporte PDF**: Utiliza el agente `pdf_analyzer` existente
- **Herramientas de Red**: Curl, wget, nmap, telnet, netcat para pruebas de penetración
- **Metodología ReACT**: Reasoning and Action para explotación iterativa
- **Explotación en Vivo**: Replica ataques descritos en el reporte contra aplicaciones reales
- **Validación Automática**: Determina si las vulnerabilidades son realmente explotables
- **Técnicas de Explotación**: SQL injection, XSS, directory traversal, command injection
- **Verificación de Conectividad**: Ping y verificación de puertos antes de las pruebas

#### Herramientas de Red Disponibles

- **HTTP Requests**: `curl` para solicitudes HTTP/HTTPS personalizadas
- **File Download**: `wget` para descargar archivos y probar endpoints
- **Port Scanning**: `nmap` para descubrimiento de servicios
- **Network Testing**: `ping` para verificar conectividad
- **Service Testing**: `telnet` y `netcat` para pruebas de servicios específicos
- **Exploitation Tests**: Pruebas automatizadas para vulnerabilidades comunes

#### Formato de Salida del Dynamic-Agent

```json
{
  "vulnerabilidades_reportadas": 4,
  "vulnerabilidades_explotables": 2,
  "timestamp": "2024-01-15T14:30:00",
  "target_url": "http://localhost:8080",
  "conectividad": "exitosa",
  "vulnerabilidades": [
    {
      "nombre": "SQL Injection",
      "estado": "explotable",
      "severidad": "critica",
      "detalles": "THOUGHT: Probando inyección SQL en endpoint /login...",
      "evidencia": "curl -X POST http://localhost:8080/login -d \"username=admin' OR '1'='1&password=test\"",
      "respuesta": "Login successful - Admin panel access granted"
    },
    {
      "nombre": "XSS Reflected",
      "estado": "no_explotable",
      "severidad": "media",
      "detalles": "THOUGHT: Probando XSS reflejado en parámetro search...",
      "evidencia": "curl 'http://localhost:8080/search?q=<script>alert(1)</script>'",
      "respuesta": "Input sanitizado correctamente"
    }
  ]
}
```

## Desarrollo

### Estructura del Proyecto

- **Domain Layer**: Contiene las entidades de negocio y reglas
- **Application Layer**: Casos de uso y lógica de aplicación
- **Infrastructure Layer**: Implementaciones técnicas (PDF, LLM, Config, Agents)
  - **Agents**: Agentes especializados para diferentes tipos de análisis
- **Presentation Layer**: Interfaz de usuario (CLI)

### Principios Aplicados

1. **Single Responsibility**: Cada clase tiene una responsabilidad específica
2. **Open/Closed**: Extensible sin modificar código existente
3. **Liskov Substitution**: Las implementaciones son intercambiables
4. **Interface Segregation**: Interfaces específicas y cohesivas
5. **Dependency Inversion**: Dependencias hacia abstracciones

### Agregar Nuevas Funcionalidades

1. **Nuevo lector de PDF**: Implementar `PDFReaderInterface`
2. **Nuevo analizador**: Implementar `ReportAnalyzerInterface`
3. **Nuevo LLM**: Implementar `LLMInterface`
4. **Nuevo agente**: Crear en `src/infrastructure/agents/`
5. **Nuevos comandos**: Agregar en `cli.py`

## Funcionalidad Multi-Modelo

### Proveedores Soportados

La aplicación soporta múltiples proveedores de LLM:

| Proveedor | Modelos Disponibles | API Key Requerida |
|-----------|--------------------|-----------------|
| **OpenAI** | gpt-3.5-turbo, gpt-4, gpt-4-turbo | `OPENAI_API_KEY` |
| **XAI (Grok)** | grok-beta | `XAI_API_KEY` |
| **Google Gemini** | gemini-pro, gemini-1.5-pro | `GEMINI_API_KEY` |
| **DeepSeek** | deepseek-chat | `DEEPSEEK_API_KEY` |
| **Anthropic** | claude-3-sonnet, claude-3-opus | `ANTHROPIC_API_KEY` |

### Ventajas del Sistema Multi-Modelo

- **Flexibilidad**: Cambia entre proveedores según tus necesidades
- **Redundancia**: Si un proveedor falla, usa otro automáticamente
- **Optimización de costos**: Elige el proveedor más económico para tu caso de uso
- **Comparación de resultados**: Prueba diferentes modelos para el mismo documento
- **Disponibilidad**: No dependes de un solo proveedor

### Configuración Automática

La aplicación detecta automáticamente qué proveedores están configurados:

```bash
# Si solo tienes OpenAI configurado
python app.py test
# ✓ Conectado a OpenAI gpt-3.5-turbo

# Si intentas usar un proveedor no configurado
python app.py test --model gemini
# ❌ API key para gemini no está configurada
# Proveedores disponibles: openai, xai, deepseek
```

## Integración con MongoDB

### Características de MongoDB

- ✅ **Almacenamiento Persistente**: Guarda resultados de análisis en base de datos
- ✅ **Búsqueda Avanzada**: Consulta documentos por criterios específicos
- ✅ **Historial Completo**: Mantiene registro de todos los análisis realizados
- ✅ **Metadatos Enriquecidos**: Información adicional sobre el procesamiento
- ✅ **Configuración Flexible**: Soporte para MongoDB local y en la nube

### Configuración de MongoDB

Agrega las siguientes variables a tu archivo `.env`:

```env
# MongoDB Configuration (OPCIONAL)
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=pdf_analyzer
MONGODB_COLLECTION=analysis_results
```

### Uso con MongoDB

1. **Guardar resultado solo en MongoDB**:
   ```bash
   python app.py read --pdf archivo.pdf --mongodb
   ```

2. **Guardar en archivo Y en MongoDB**:
   ```bash
   python app.py read --pdf archivo.pdf --output resultado.json --mongodb
   ```

3. **Probar conexión con MongoDB**:
   ```bash
   python app.py test-mongodb
   ```

### Estructura de Datos en MongoDB

Cada documento guardado incluye:

```json
{
  "_id": "ObjectId",
  "timestamp": "2024-01-15T10:30:00Z",
  "file_info": {
    "filename": "report.pdf",
    "file_size": 1024000,
    "file_hash": "sha256_hash"
  },
  "processing_info": {
    "model_provider": "openai",
    "model_name": "gpt-3.5-turbo",
    "temperature": 0.1,
    "processing_time_seconds": 45.2
  },
  "analysis_result": {
    "documento": { /* ... */ },
    "resumen_ejecutivo": "...",
    "hallazgos_principales": [ /* ... */ ],
    "recomendaciones": [ /* ... */ ],
    "datos_tecnicos": { /* ... */ },
    "conclusiones": "...",
    "informacion_adicional": { /* ... */ }
  }
}
```

### Docker Compose para MongoDB

Puedes usar Docker para ejecutar MongoDB localmente:

```yaml
# docker-compose.yml
version: '3.8'
services:
  mongodb:
    image: mongo:7
    container_name: pdf_analyzer_mongo
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

```bash
# Ejecutar MongoDB con Docker
docker-compose up -d mongodb

# Verificar que esté funcionando
  python app.py test-mongodb
  ```

## Pruebas de Conexión

```bash
# Probar conexión con LLM
python app.py test
# ✓ Conectado a OpenAI gpt-3.5-turbo

# Si intentas usar un proveedor no configurado
python app.py test --model gemini
# ❌ API key para gemini no está configurada
# Proveedores disponibles: openai, xai, deepseek
```

## Troubleshooting

### Errores Comunes

1. **API Key no configurada**:
   ```
   API key para [proveedor] no está configurada
   Proveedores disponibles: openai, xai, deepseek
   ```
   **Solución**: Configurar la variable correspondiente en `.env` (ej: `OPENAI_API_KEY`, `GEMINI_API_KEY`)

2. **Proveedor no válido**:
   ```
   Proveedor 'xyz' no es válido. Proveedores soportados: openai, xai, gemini, deepseek, anthropic
   ```
   **Solución**: Usar uno de los proveedores soportados

3. **Formato de modelo incorrecto**:
   ```
   Formato de modelo inválido. Use 'proveedor' o 'proveedor:modelo'
   ```
   **Solución**: Usar formato correcto como `openai:gpt-4` o solo `openai`

4. **Archivo PDF no encontrado**:
   ```
   Archivo no encontrado: El archivo X no existe
   ```
   **Solución**: Verificar la ruta del archivo

5. **PDF corrupto**:
   ```
   Archivo PDF inválido: Error leyendo PDF
   ```
   **Solución**: Verificar que el archivo PDF no esté corrupto

6. **Error de conexión MongoDB**:
   ```
   Error conectando a MongoDB: [ServerSelectionTimeoutError]
   ```
   **Solución**: 
   - Verificar que MongoDB esté ejecutándose
   - Configurar `MONGODB_URI` en `.env`
   - Para Docker: `docker-compose up mongodb`
   - Para local: instalar y ejecutar MongoDB localmente

7. **MongoDB no configurado**:
   ```
   Error guardando en MongoDB: No hay conexión activa
   ```
   **Solución**: Configurar las variables de MongoDB en `.env` y probar con `python app.py test-mongodb`
   **Solución**: Verificar que el archivo sea un PDF válido

6. **Error de conexión**:
   ```
   Error de conexión con [proveedor]
   ```
   **Solución**: Verificar API key, conexión a internet y estado del servicio

### Logs y Debug

Usar el flag `--verbose` para obtener información detallada:

```bash
python app.py read --pdf archivo.pdf --verbose
```

## Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Tecnologías Utilizadas

### Core
- **Python 3.8+**
- **LangChain**: Orquestación de agentes de IA
- **PyPDF2**: Extracción de texto de PDFs
- **Typer**: Framework para CLI
- **Rich**: Interfaz rica para terminal
- **Pydantic**: Validación de datos
- **python-dotenv**: Manejo de variables de entorno

### Proveedores de LLM
- **OpenAI**: GPT-3.5, GPT-4 y variantes
- **XAI (Grok)**: Modelos Grok de xAI
- **Google Gemini**: Gemini Pro y variantes
- **DeepSeek**: Modelos DeepSeek Chat
- **Anthropic**: Claude 3 (Sonnet, Opus)

### Integraciones LangChain
- **langchain-openai**: Integración con OpenAI
- **langchain-google-genai**: Integración con Google Gemini
- **langchain-anthropic**: Integración con Anthropic Claude

---

**Versión**: 1.0.0  
**Autor**: AI Assistant  
**Fecha**: 2024