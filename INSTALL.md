# 📄 PDF Copilot - Instalación y Ejecución

## 🚀 Instalación Local

### Prerrequisitos

- Python 3.11 o superior
- Git

### Paso 1: Clonar el repositorio

```bash
git clone <repository-url>
cd pdf-copilot
```

### Paso 2: Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Paso 3: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 4: Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones
# Por defecto usa Ollama (local)
```

### Paso 5: Configurar LLM (elige una opción)

#### Opción A: Ollama (Recomendado para uso local)

```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Descargar modelo
ollama pull llama3.2

# En .env configurar:
# LLM_PROVIDER=ollama
# OLLAMA_MODEL=llama3.2
```

#### Opción B: OpenAI

```bash
# En .env configurar:
# LLM_PROVIDER=openai
# OPENAI_API_KEY=tu_api_key_aqui
```

### Paso 6: Ejecutar aplicación

#### Interfaz Streamlit

```bash
streamlit run src/ui/streamlit_app.py
```

Navegar a: <http://localhost:8501>

#### API FastAPI (opcional)

```bash
uvicorn src.api.fastapi_app:app --reload
```

Documentación: <http://localhost:8000/docs>

## 🐳 Instalación con Docker

### Opción 1: Docker Compose (Recomendado)

```bash
# Construir y ejecutar
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### Opción 2: Docker manual

```bash
# Construir imagen
docker build -f docker/Dockerfile -t pdf-copilot .

# Ejecutar contenedor
docker run -p 8501:8501 -p 8000:8000 pdf-copilot
```

## 🎮 Uso Básico

1. **Subir documentos**: Arrastra hasta 5 archivos PDF
2. **Procesar**: Haz clic en "Procesar Documentos"
3. **Conversar**: Haz preguntas sobre el contenido

### Ejemplos de preguntas

- "Resume los documentos principales"
- "¿Cuáles son las diferencias entre los documentos?"
- "Clasifica los documentos por temas"
- "¿Qué dice sobre metodología el documento X?"

## 🔧 Solución de Problemas

### Error: ChromaDB no disponible

```bash
pip install chromadb
```

### Error: Modelo Ollama no encontrado

```bash
ollama pull llama3.2
# o el modelo que este configurado
```

### Error: Streamlit no inicia

```bash
# Verificar puerto
netstat -an | grep 8501

# Cambiar puerto si está ocupado
streamlit run src/ui/streamlit_app.py --server.port 8502
```

## 📊 Verificar Estado

### Verificar componentes

```bash
# Probar importaciones
python -c "from src.core.config import settings; print('Config OK')"

# Verificar LLM
python -c "from src.core.llm_manager import llm_manager; print(llm_manager.get_provider_status())"

# Verificar Vector Store
python -c "from src.core.vectorstore import vector_store; print(vector_store.get_collection_stats())"
```

## 🚨 Problemas Comunes

### 1. Dependencias faltantes

**Síntoma**: ImportError al iniciar
**Solución**:

```bash
pip install -r requirements.txt --upgrade
```

### 2. Ollama no responde

**Síntoma**: Error de conexión con Ollama
**Solución**:

```bash
# Verificar que Ollama esté corriendo
curl http://localhost:11434/api/tags

# Reiniciar Ollama si es necesario
ollama serve
```

### 3. Memoria insuficiente

**Síntoma**: Error al procesar PDFs grandes
**Solución**:

- Reducir CHUNK_SIZE en .env
- Procesar menos archivos simultáneamente
- Usar modelos LLM más pequeños

### 4. Puerto ocupado

**Síntoma**: Error "Address already in use"
**Solución**:

```bash
# Cambiar puertos en .env
STREAMLIT_PORT=8502
FASTAPI_PORT=8001
```

## 🔄 Actualizaciones

```bash
# Actualizar dependencias
pip install -r requirements.txt --upgrade

# Limpiar cache de Streamlit
streamlit cache clear

# Reiniciar servicios Docker
docker-compose down && docker-compose up -d
```

## 📝 Notas Importantes

- **Archivos PDF**: Máximo 5 archivos, 50MB cada uno
- **Modelos locales**: Requieren al menos 8GB RAM
- **OpenAI**: Requiere API key válida
- **Vector Store**: Los datos se persisten en `./data/chroma_db`
