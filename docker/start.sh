#!/bin/bash

# Script de inicio para contenedor Docker

echo "🚀 Iniciando PDF Copilot..."

# Verificar si Ollama está disponible
if [ "$LLM_PROVIDER" = "ollama" ]; then
    echo "⏳ Esperando a que Ollama esté disponible..."
    while ! curl -f http://ollama:11434/api/tags >/dev/null 2>&1; do
        sleep 5
        echo "⏳ Ollama no está listo, esperando..."
    done
    echo "✅ Ollama está disponible"
fi

# Iniciar Streamlit
echo "🎯 Iniciando Streamlit en puerto 8501..."
cd /app
export PYTHONPATH="/app/src"
streamlit run src/ui/streamlit_app.py --server.port=8501 --server.address=0.0.0.0
