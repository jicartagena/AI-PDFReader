#!/usr/bin/env python3
"""
Script de verificación del sistema PDF Copilot
Ejecutar para validar que todas las dependencias están instaladas correctamente
"""
import sys
import os
from pathlib import Path


def verificar_python():
    """Verificar versión de Python"""
    version = sys.version_info
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    if version < (3, 11):
        print("❌ Se requiere Python 3.11 o superior")
        return False
    return True


def verificar_dependencias():
    """Verificar dependencias principales"""
    dependencias = [
        ("PyPDF2", "Procesamiento de PDFs"),
        ("pdfplumber", "Extracción avanzada de PDFs"),
        ("chromadb", "Vector store"),
        ("langchain", "Framework LLM"),
        ("sentence_transformers", "Embeddings"),
        ("streamlit", "Interfaz web"),
        ("fastapi", "API REST"),
        ("uvicorn", "Servidor ASGI"),
        ("openai", "Cliente OpenAI"),
        ("requests", "Cliente HTTP"),
    ]

    print("\n📦 Verificando dependencias:")
    fallos = 0

    for dep, descripcion in dependencias:
        try:
            __import__(dep)
            print(f"✅ {dep:<20} - {descripcion}")
        except ImportError:
            print(f"❌ {dep:<20} - {descripcion} (NO INSTALADO)")
            fallos += 1

    return fallos == 0


def verificar_modulos_sistema():
    """Verificar módulos del sistema"""
    print("\n🔧 Verificando módulos del sistema:")

    # Añadir src al path
    sys.path.insert(0, str(Path(__file__).parent / "src"))

    modulos = [
        ("core.config", "Configuración"),
        ("core.pdf_processor", "Procesador PDF"),
        ("core.vectorstore", "Vector Store"),
        ("core.llm_manager", "Gestor LLM"),
        ("core.orchestrator", "Orquestador"),
    ]

    fallos = 0
    for modulo, descripcion in modulos:
        try:
            __import__(modulo)
            print(f"✅ {modulo:<25} - {descripcion}")
        except ImportError as e:
            print(f"❌ {modulo:<25} - {descripcion} ({str(e)})")
            fallos += 1

    return fallos == 0


def verificar_estructura():
    """Verificar estructura de directorios"""
    print("\n📁 Verificando estructura:")

    directorios = [
        "src/core",
        "src/agents",
        "src/ui",
        "src/api",
        "data",
        "tests",
        "docker",
    ]

    fallos = 0
    for directorio in directorios:
        path = Path(directorio)
        if path.exists():
            print(f"✅ {directorio}")
        else:
            print(f"❌ {directorio} (NO EXISTE)")
            fallos += 1

    return fallos == 0


def verificar_archivos_config():
    """Verificar archivos de configuración"""
    print("\n⚙️  Verificando configuración:")

    archivos = [
        ("requirements.txt", "Dependencias"),
        (".env.example", "Ejemplo de configuración"),
        ("docker-compose.yml", "Configuración Docker"),
        ("README.md", "Documentación"),
        ("INSTALL.md", "Guía de instalación"),
    ]

    fallos = 0
    for archivo, descripcion in archivos:
        path = Path(archivo)
        if path.exists():
            print(f"✅ {archivo:<20} - {descripcion}")
        else:
            print(f"❌ {archivo:<20} - {descripcion} (NO EXISTE)")
            fallos += 1

    return fallos == 0


def verificar_llm_providers():
    """Verificar proveedores LLM disponibles"""
    print("\n🤖 Verificando proveedores LLM:")

    try:
        from core.llm_manager import llm_manager

        status = llm_manager.get_provider_status()

        print(f"Proveedor activo: {status['active_provider']}")
        print("Proveedores disponibles:")

        for provider, disponible in status["provider_status"].items():
            estado = "✅" if disponible else "❌"
            print(f"  {estado} {provider}")

        return len(status["available_providers"]) > 0

    except Exception as e:
        print(f"❌ Error verificando LLM: {e}")
        return False


def main():
    """Función principal de verificación"""
    print("🎯 VERIFICACIÓN DEL SISTEMA PDF COPILOT")
    print("=" * 50)

    verificaciones = [
        ("Versión de Python", verificar_python),
        ("Dependencias", verificar_dependencias),
        ("Estructura de directorios", verificar_estructura),
        ("Archivos de configuración", verificar_archivos_config),
        ("Módulos del sistema", verificar_modulos_sistema),
        ("Proveedores LLM", verificar_llm_providers),
    ]

    exitos = 0
    total = len(verificaciones)

    for nombre, verificacion in verificaciones:
        try:
            if verificacion():
                exitos += 1
        except Exception as e:
            print(f"❌ Error en {nombre}: {e}")

    print("\n" + "=" * 50)
    print(f"📊 RESUMEN: {exitos}/{total} verificaciones exitosas")

    if exitos == total:
        print("🎉 ¡Sistema completamente funcional!")
        print("\n🚀 Para ejecutar la aplicación:")
        print("   streamlit run src/ui/streamlit_app.py")
        print("   Luego navegar a: http://localhost:8501")
        return True
    else:
        print("⚠️  Hay problemas que resolver antes de usar el sistema")
        print("💡 Revisa las guías en INSTALL.md y README.md")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
