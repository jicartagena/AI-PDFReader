# PDF Copilot - Copiloto Conversacional sobre Documentos

Un copiloto conversacional inteligente que permite subir hasta 5 archivos PDF y hacer preguntas en lenguaje natural sobre su contenido.

## 🟢 Estado del Proyecto

**✅ COMPLETAMENTE FUNCIONAL** - El sistema ha sido probado y está listo para uso en producción.

### ✅ Funcionalidades Verificadas:
- ✅ Carga y procesamiento de documentos PDF
- ✅ Extracción de metadatos segura (compatible con ChromaDB)
- ✅ Búsqueda semántica con puntuaciones de relevancia corregidas
- ✅ Generación de respuestas basadas en contexto
- ✅ Integración completa Ollama + Llama 3.2
- ✅ Interfaz Streamlit totalmente funcional
- ✅ Vector store ChromaDB operativo

### 🔧 Correcciones Recientes:
- ✅ Solucionado: Error de metadatos IndirectObject en ChromaDB
- ✅ Solucionado: Puntuaciones de relevancia negativas en búsqueda semántica
- ✅ Optimizado: Filtros de relevancia más inclusivos
- ✅ Mejorado: Manejo robusto de errores en procesamiento de PDFs

## 🎯 Características Principales

- ✅ Subida de hasta 5 PDFs simultáneamente
- ✅ Extracción, división y vectorización inteligente del contenido
- ✅ Interfaz conversacional intuitiva
- ✅ Orquestación estructurada y extensible
- ✅ Múltiples opciones de LLM (OpenAI, Ollama, HuggingFace)
- ✅ Resumen automático de contenido
- ✅ Comparaciones entre documentos
- ✅ Clasificación por temas
- ✅ Despliegue local y con Docker

## 🏗️ Arquitectura del Sistema

```
├── src/
│   ├── core/              # Lógica central del sistema
│   │   ├── pdf_processor.py    # Procesamiento de PDFs
│   │   ├── vectorstore.py      # Manejo del vector store
│   │   ├── llm_manager.py      # Gestión de múltiples LLMs
│   │   └── orchestrator.py     # Orquestación de flujos
│   ├── agents/            # Agentes especializados
│   │   ├── summarizer.py       # Agente de resumen
│   │   ├── comparator.py       # Agente de comparación
│   │   └── classifier.py       # Agente de clasificación
│   ├── ui/               # Interfaz de usuario
│   │   └── streamlit_app.py    # Aplicación Streamlit
│   └── api/              # API REST
│       └── fastapi_app.py      # Aplicación FastAPI
├── data/                 # Datos y archivos temporales
├── tests/               # Pruebas unitarias
└── docker/             # Configuración Docker
```

## 🛠️ Tecnologías Utilizadas

### Core Technologies
- **Python 3.11+**: Lenguaje principal
- **LangChain**: Framework de orquestación
- **Chroma**: Vector store para embeddings
- **Streamlit**: Interfaz web interactiva
- **FastAPI**: API REST backend

### LLM Options
- **OpenAI GPT**: Para usuarios con API key
- **Ollama**: Modelos locales (Llama, Mistral)
- **HuggingFace**: Modelos open source

### Additional Tools
- **PyPDF2 / pdfplumber**: Extracción de texto PDF
- **sentence-transformers**: Embeddings locales
- **Docker**: Containerización
- **pytest**: Testing framework

## 🚀 Instalación y Configuración

### Opción 1: Instalación Local

1. **Clonar el repositorio:**
```bash
git clone <repository-url>
cd pdf-copilot
```

2. **Crear entorno virtual:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### Opción 2: Docker

```bash
docker-compose up -d
```

## 🎮 Uso

### Interfaz Streamlit
```bash
streamlit run src/ui/streamlit_app.py
```
Navegar a: `http://localhost:8501`

### API FastAPI
```bash
uvicorn src.api.fastapi_app:app --reload
```
Documentación: `http://localhost:8000/docs`

## ⚙️ Configuración de LLMs

### OpenAI
```env
OPENAI_API_KEY=tu_api_key_aqui
LLM_PROVIDER=openai
```

### Ollama (Local)
```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Descargar modelo
ollama pull llama2
```

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama2
```

### HuggingFace
```env
HUGGINGFACE_API_TOKEN=tu_token_aqui
LLM_PROVIDER=huggingface
HF_MODEL=microsoft/DialoGPT-medium
```

## 🔧 Justificación de Elecciones Técnicas

### LangChain
- **Ventajas**: Abstracción de LLMs, herramientas de orquestación robustas
- **Uso**: Gestión de flujos conversacionales y cadenas de procesamiento

### Chroma Vector Store
- **Ventajas**: Ligero, fácil setup local, buen rendimiento
- **Uso**: Almacenamiento y búsqueda semántica de embeddings

### Streamlit
- **Ventajas**: Desarrollo rápido, interfaz reactiva, ideal para prototipos
- **Uso**: Interfaz principal del usuario

### FastAPI
- **Ventajas**: Alto rendimiento, documentación automática, type hints
- **Uso**: API REST para integraciones externas

## 🔄 Flujo Conversacional

1. **Carga de Documentos**
   - Validación de archivos PDF
   - Extracción de texto y metadatos
   - División en chunks optimizados

2. **Procesamiento**
   - Generación de embeddings
   - Almacenamiento en vector store
   - Creación de índices de búsqueda

3. **Orquestación Conversacional**
   - Análisis de intención del usuario
   - Búsqueda semántica de contexto relevante
   - Selección de agente especializado

4. **Generación de Respuesta**
   - Construcción de prompt contextual
   - Invocación del LLM seleccionado
   - Post-procesamiento y formateo

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📈 Limitaciones Actuales

- Máximo 5 PDFs por sesión
- Soporte limitado a texto (no imágenes/tablas complejas)
- Modelos locales requieren hardware adecuado
- Rate limits en APIs externas

## 🗺️ Roadmap de Mejoras

### Corto Plazo
- [ ] Soporte para más formatos (DOCX, TXT)
- [ ] Mejora en extracción de tablas
- [ ] Cache inteligente de resultados
- [ ] Métricas de rendimiento

### Medio Plazo
- [ ] Análisis de imágenes y diagramas
- [ ] Integración con bases de datos externas
- [ ] Multiidioma avanzado
- [ ] Dashboard de analytics

### Largo Plazo
- [ ] Fine-tuning de modelos específicos
- [ ] Integración con sistemas empresariales
- [ ] Versioning de documentos
- [ ] Colaboración multi-usuario

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, revisa las guías de contribución y abre un issue antes de enviar un PR.

## 📄 Licencia

MIT License - ver archivo LICENSE para detalles.
