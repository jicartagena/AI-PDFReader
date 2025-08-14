# PDF Copilot - Copiloto Conversacional para Documentos

Un sistema inteligente de análisis conversacional que permite cargar hasta 5 documentos PDF y realizar consultas en lenguaje natural sobre su contenido, con capacidades de resumen, comparación y clasificación automática.

## Características Principales

-  **Carga múltiple**: Hasta 5 PDFs simultáneamente
-  **Procesamiento inteligente**: Extracción y vectorización automática del contenido
-  **Consultas naturales**: Interfaz conversacional intuitiva
-  **Agentes especializados**: Resumen, comparación y clasificación de documentos
-  **LLMs múltiples**: Soporte para OpenAI y Ollama (modelos locales)
-  **Deployment flexible**: Ejecución local y containerizada con Docker
-  **Optimizado**: Configuraciones de rendimiento y timeout ajustables

## Demo Rápido

```bash
# Inicio automático
python start_app.py

# Acceso web
http://localhost:8501
```

## Arquitectura del Sistema

```text
src/
├── core/                  # Lógica central del sistema
│   ├── config.py              # Configuración global
│   ├── pdf_processor.py       # Procesamiento de PDFs
│   ├── vectorstore.py         # Manejo del vector store
│   ├── llm_manager.py         # Gestión de múltiples LLMs
│   └── orchestrator.py        # Orquestación de flujos
├── agents/                # Agentes especializados
│   ├── summarizer.py          # Agente de resumen
│   ├── comparator.py          # Agente de comparación
│   └── classifier.py          # Agente de clasificación
└── ui/                    # Interfaz de usuario
    └── streamlit_app.py       # Aplicación Streamlit
```

## Stack Tecnológico

### Tecnologías Core
- **Python 3.11+**: Lenguaje principal
- **LangChain**: Framework de orquestación de LLMs
- **ChromaDB**: Vector store para búsqueda semántica
- **Streamlit**: Interfaz web interactiva

### Opciones de LLM
- **OpenAI GPT**: Modelos en la nube (requiere API key)
- **Ollama**: Modelos locales (Llama 3.2, Mistral, etc.)

### Herramientas de Procesamiento
- **PyPDF2/pdfplumber**: Extracción de texto de PDFs
- **sentence-transformers**: Generación de embeddings locales
- **Docker**: Containerización y deployment

## Instalación

### Método 1: Inicio Automático (Recomendado)

```bash
# Clona el repositorio
git clone <repository-url>
cd pdf-copilot

# Ejecuta el script de configuración automática
python start_app.py
```

### Método 2: Instalación Manual

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd pdf-copilot
```

2. **Crear entorno virtual**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Iniciar aplicación**
```bash
streamlit run src/ui/streamlit_app.py
```

### Método 3: Docker (Producción)

```bash
# Construcción y ejecución
docker-compose up -d

# Verificar estado
docker-compose ps
```

## Uso

### Acceso a la Aplicación
- **Local/Docker**: http://localhost:8501

### Funcionalidades Principales

1. **Carga de Documentos**
   - Arrastra hasta 5 archivos PDF a la interfaz
   - Procesamiento automático y vectorización del contenido

2. **Consultas Conversacionales**
   - Escribe preguntas en lenguaje natural
   - Obtén respuestas contextualizadas basadas en los documentos

3. **Herramientas Especializadas**
   - **Resumen**: Genera resúmenes automáticos de documentos
   - **Comparación**: Analiza diferencias y similitudes entre documentos
   - **Clasificación**: Categoriza documentos por temas automáticamente

## Configuración de LLMs

### OpenAI (Recomendado para producción)

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=tu_api_key_aqui
OPENAI_MODEL=gpt-3.5-turbo
```

### Ollama (Recomendado para desarrollo local)

**Instalación:**
```bash
# Linux/Mac
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Descargar desde https://ollama.ai/
```

**Configuración:**
```bash
# Descargar modelo
ollama pull llama3.2

# Variables de entorno
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

## Optimizaciones de Rendimiento

### Configuraciones Aplicadas

- **Timeout extendido**: 90 segundos para consultas complejas
- **Contexto optimizado**: Máximo 3000 caracteres para mejor velocidad
- **Parámetros LLM ajustados**: 
  - `num_ctx`: 1024 tokens (balance velocidad/calidad)
  - `num_predict`: 256 tokens máximo por respuesta
  - `temperature`: 0.7 (respuestas balanceadas)

### Mejoras de Estabilidad

-  Manejo robusto de errores y timeouts
-  Validación exhaustiva de archivos PDF
-  Recuperación automática de conexiones LLM
-  Limitación inteligente de contexto para evitar sobrecarga

## Arquitectura y Flujo de Datos

### 1. Procesamiento de Documentos
```text
PDF Upload → Text Extraction → Chunking → Embedding Generation → Vector Storage
```

### 2. Consulta Conversacional
```text
User Query → Intent Analysis → Semantic Search → Context Assembly → LLM Response
```

### 3. Agentes Especializados
- **Summarizer**: Análisis y síntesis de contenido
- **Comparator**: Análisis diferencial entre documentos
- **Classifier**: Categorización automática por temas

## Justificación Técnica

### LangChain
- **Ventajas**: Abstracción robusta para LLMs, gestión de cadenas complejas
- **Uso**: Orquestación de flujos conversacionales y procesamiento de documentos

### ChromaDB
- **Ventajas**: Vector store ligero, setup simple, buen rendimiento local
- **Uso**: Almacenamiento y búsqueda semántica de embeddings de documentos

### Streamlit
- **Ventajas**: Desarrollo rápido, interfaz reactiva, ideal para prototipos y demos
- **Uso**: Interfaz principal de usuario para interacción conversacional

## Limitaciones Conocidas

- **Capacidad**: Máximo 5 PDFs por sesión de trabajo
- **Contenido**: Soporte limitado a texto plano (sin imágenes o tablas complejas)
- **Hardware**: Modelos locales requieren recursos computacionales adecuados
- **APIs**: Rate limits aplicables para servicios externos (OpenAI)
- **Idioma**: Optimizado para contenido en español e inglés

## Estructura del Proyecto

```text
pdf-copilot/
├── src/
│   ├── core/                  # Lógica central
│   │   ├── config.py              # Configuración global
│   │   ├── pdf_processor.py       # Procesamiento de PDFs
│   │   ├── vectorstore.py         # Gestión del vector store
│   │   ├── llm_manager.py         # Gestión de LLMs múltiples
│   │   └── orchestrator.py        # Orquestación de flujos
│   ├── agents/                # Agentes especializados
│   │   ├── summarizer.py          # Resumen de documentos
│   │   ├── comparator.py          # Comparación de documentos
│   │   └── classifier.py          # Clasificación automática
│   └── ui/                    # Interfaz de usuario
│       └── streamlit_app.py       # Aplicación web
├── docker/                    # Configuración Docker
│   ├── Dockerfile
│   └── start.sh
├── data/                      # Datos y archivos temporales
├── tests/                     # Pruebas unitarias
├── requirements.txt           # Dependencias Python
├── docker-compose.yml         # Orquestación de contenedores
├── start_app.py              # Script de inicio automático
├── .env.example              # Plantilla de configuración
├── README.md                 # Documentación principal
└── INSTALL.md                # Guía de instalación detallada
```

## Roadmap

### Funcionalidades a Largo Plazo
- [ ] Soporte para formatos adicionales (DOCX, TXT, EPUB)
- [ ] Análisis de imágenes y diagramas con modelos multimodales
- [ ] Sistema de plugins para extensiones personalizadas
- [ ] API REST para integración con sistemas externos
- [ ] Interfaz colaborativa multi-usuario

### Mejoras Técnicas
- [ ] Cache inteligente de respuestas frecuentes
- [ ] Optimización de memoria para documentos grandes
- [ ] Métricas de rendimiento y analytics
- [ ] Fine-tuning de modelos específicos del dominio



## Licencia

MIT License - Consulta el archivo `LICENSE` para más detalles.
