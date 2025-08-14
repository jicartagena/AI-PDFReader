#!/usr/bin/env python3
"""
Script de inicio simplificado para PDF Copilot
"""

import os
import sys
import subprocess
import requests
import time
from pathlib import Path


def check_ollama():
    """Verificar si Ollama está corriendo"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


def start_ollama():
    """Intentar iniciar Ollama"""
    ollama_paths = [
        os.path.expanduser("~/.local/bin/ollama"),
        "/usr/local/bin/ollama",
        "/usr/bin/ollama",
        os.path.expanduser("~/AppData/Local/Programs/Ollama/ollama.exe"),
    ]

    for path in ollama_paths:
        if os.path.exists(path):
            try:
                subprocess.Popen([path, "serve"])
                print("Iniciando Ollama...")
                time.sleep(5)
                return True
            except:
                continue
    return False


def main():
    print("PDF Copilot - Inicio del Sistema")
    print("=" * 40)

    # Verificar Ollama
    if not check_ollama():
        print("Ollama no está corriendo. Intentando iniciar...")
        if not start_ollama():
            print("❌ No se pudo iniciar Ollama automáticamente.")
            print("   Inicia Ollama manualmente y ejecuta este script de nuevo.")
            return

        # Esperar a que Ollama esté listo
        for i in range(10):
            if check_ollama():
                break
            print(f"Esperando Ollama... ({i+1}/10)")
            time.sleep(2)

    if check_ollama():
        print("✅ Ollama está funcionando")
    else:
        print("❌ Ollama no está disponible")
        return

    # Iniciar Streamlit
    print("Iniciando aplicación Streamlit...")
    os.environ["PYTHONPATH"] = str(Path(__file__).parent / "src")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "src/ui/streamlit_app.py",
            "--server.port",
            "8501",
        ]
    )


if __name__ == "__main__":
    main()
