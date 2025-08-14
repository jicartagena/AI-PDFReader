"""
Configuración y settings del sistema PDF Copilot
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Directorios base
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
TEMP_DIR = DATA_DIR / "temp"
CHROMA_DIR = DATA_DIR / "chroma_db"

# Crear directorios si no existen
for directory in [DATA_DIR, UPLOAD_DIR, TEMP_DIR, CHROMA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class Settings:
    """Configuración global del sistema"""

    # LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")

    # OpenAI
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")

    # Vector Store
    CHROMA_PERSIST_DIRECTORY: str = os.getenv(
        "CHROMA_PERSIST_DIRECTORY", str(CHROMA_DIR)
    )
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "pdf_documents")

    # Embeddings
    EMBEDDINGS_MODEL: str = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
    EMBEDDINGS_PROVIDER: str = os.getenv("EMBEDDINGS_PROVIDER", "sentence_transformers")

    # Application
    MAX_PDF_FILES: int = int(os.getenv("MAX_PDF_FILES", "5"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

    # Server Configuration
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    STREAMLIT_HOST: str = os.getenv("STREAMLIT_HOST", "0.0.0.0")
    FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "8000"))
    FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "0.0.0.0")

    # Development
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Directories
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(UPLOAD_DIR))
    TEMP_DIR: str = os.getenv("TEMP_DIR", str(TEMP_DIR))

    @classmethod
    def validate_llm_config(cls) -> bool:
        """Validar configuración del LLM seleccionado"""
        if cls.LLM_PROVIDER == "openai":
            return cls.OPENAI_API_KEY is not None
        elif cls.LLM_PROVIDER == "ollama":
            return True
        return False

    @classmethod
    def get_active_llm_config(cls) -> dict:
        """Obtener configuración del LLM activo"""
        if cls.LLM_PROVIDER == "openai":
            return {
                "provider": "openai",
                "api_key": cls.OPENAI_API_KEY,
                "model": cls.OPENAI_MODEL,
            }
        elif cls.LLM_PROVIDER == "ollama":
            return {
                "provider": "ollama",
                "base_url": cls.OLLAMA_BASE_URL,
                "model": cls.OLLAMA_MODEL,
            }
        else:
            raise ValueError(f"Proveedor LLM no soportado: {cls.LLM_PROVIDER}")


# Instancia global de configuración.
settings = Settings()
