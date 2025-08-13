"""
Configuración de pruebas con pytest
"""

import os
import sys
from pathlib import Path

# Añadir src al path para importaciones
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configurar logging para pruebas
import logging

logging.getLogger().setLevel(logging.WARNING)

# Configurar variables de entorno para pruebas
os.environ.setdefault("LLM_PROVIDER", "ollama")
os.environ.setdefault("CHROMA_PERSIST_DIRECTORY", "./test_data/chroma_db")
os.environ.setdefault("UPLOAD_DIR", "./test_data/uploads")
os.environ.setdefault("TEMP_DIR", "./test_data/temp")
os.environ.setdefault("DEBUG", "true")
