"""
Script de inicio para desarrollo local
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_python_version():
    """Verificar versión de Python"""
    if sys.version_info < (3, 11):
        logger.error("Python 3.11+ requerido. Versión actual: %s", sys.version)
        return False
    logger.info("✅ Python version: %s", sys.version.split()[0])
    return True


def check_dependencies():
    """Verificar que las dependencias estén instaladas"""
    try:
        import streamlit
        import fastapi
        import langchain

        logger.info("✅ Dependencias principales instaladas")
        return True
    except ImportError as e:
        logger.error("❌ Dependencias faltantes: %s", e)
        logger.info("Ejecuta: pip install -r requirements.txt")
        return False


def check_environment():
    """Verificar configuración del entorno"""
    env_file = Path(".env")
    if not env_file.exists():
        logger.warning("⚠️ Archivo .env no encontrado, copiando .env.example")
        if Path(".env.example").exists():
            import shutil

            shutil.copy(".env.example", ".env")
            logger.info("✅ Archivo .env creado")
        else:
            logger.error("❌ Archivo .env.example no encontrado")
            return False

    logger.info("✅ Configuración de entorno OK")
    return True


def check_llm_provider():
    """Verificar proveedor LLM configurado"""
    try:
        from dotenv import load_dotenv

        load_dotenv()

        provider = os.getenv("LLM_PROVIDER", "ollama")
        logger.info("🤖 Proveedor LLM configurado: %s", provider)

        if provider == "ollama":
            # Verificar si Ollama está corriendo
            try:
                import requests

                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    logger.info("✅ Ollama está corriendo")
                else:
                    logger.warning("⚠️ Ollama no responde correctamente")
            except:
                logger.warning("⚠️ Ollama no está corriendo. Ejecuta: ollama serve")

        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                logger.info("✅ OpenAI API key configurada")
            else:
                logger.warning("⚠️ OpenAI API key no configurada")

        return True
    except Exception as e:
        logger.error("❌ Error verificando LLM provider: %s", e)
        return False


def create_directories():
    """Crear directorios necesarios"""
    directories = ["data", "data/uploads", "data/temp", "data/chroma_db"]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    logger.info("✅ Directorios creados")


def start_streamlit():
    """Iniciar aplicación Streamlit"""
    logger.info("🚀 Iniciando Streamlit...")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "src/ui/streamlit_app.py",
        "--server.port",
        "8501",
        "--server.address",
        "0.0.0.0",
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        logger.info("👋 Aplicación detenida por el usuario")
    except subprocess.CalledProcessError as e:
        logger.error("❌ Error ejecutando Streamlit: %s", e)


def start_fastapi():
    """Iniciar API FastAPI"""
    logger.info("🚀 Iniciando FastAPI...")

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.api.fastapi_app:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        logger.info("👋 API detenida por el usuario")
    except subprocess.CalledProcessError as e:
        logger.error("❌ Error ejecutando FastAPI: %s", e)


def main():
    """Función principal"""
    logger.info("🎯 Iniciando PDF Copilot...")

    # Verificaciones
    checks = [
        check_python_version(),
        check_dependencies(),
        check_environment(),
        check_llm_provider(),
    ]

    if not all(checks):
        logger.error("❌ Falló alguna verificación. Revisa los errores arriba.")
        return

    # Crear directorios
    create_directories()

    # Preguntar qué iniciar
    print("\n🎮 ¿Qué deseas iniciar?")
    print("1. Interfaz Streamlit (recomendado)")
    print("2. API FastAPI")
    print("3. Ambos (en terminales separadas)")

    choice = input("\nSelecciona una opción (1-3): ").strip()

    if choice == "1":
        start_streamlit()
    elif choice == "2":
        start_fastapi()
    elif choice == "3":
        logger.info("📝 Para iniciar ambos servicios:")
        logger.info("Terminal 1: python start.py -> opción 1")
        logger.info("Terminal 2: python start.py -> opción 2")
        logger.info("O usa: docker-compose up")
    else:
        logger.error("Opción inválida")


if __name__ == "__main__":
    main()
