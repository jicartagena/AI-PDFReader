"""
Aplicación Streamlit para PDF Copilot
"""

import streamlit as st
import asyncio
import uuid
import logging
from typing import List, Dict, Any
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Añadir el directorio src al path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from core.orchestrator import orchestrator
    from core.config import settings
    from core.llm_manager import llm_manager
    from core.vectorstore import vector_store
except ImportError as e:
    st.error(f"Error importando módulos: {e}")
    st.stop()

# Configuración de página
st.set_page_config(
    page_title="PDF Copilot",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS personalizado que se adapta a temas claro y oscuro
st.markdown(
    """
<style>
.main-header {
    font-size: 3rem;
    color: #1e3a8a;
    text-align: center;
    margin-bottom: 2rem;
}

.status-box {
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
}

.status-success {
    background-color: rgba(16, 185, 129, 0.1);
    border-left: 4px solid #10b981;
}

.status-error {
    background-color: rgba(239, 68, 68, 0.1);
    border-left: 4px solid #ef4444;
}

.status-warning {
    background-color: rgba(245, 158, 11, 0.1);
    border-left: 4px solid #f59e0b;
}

.chat-message {
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
    color: inherit; /* Hereda el color del tema actual */
}

.chat-user {
    background-color: rgba(59, 130, 246, 0.1);
    border-left: 4px solid #3b82f6;
}

.chat-assistant {
    background-color: rgba(34, 197, 94, 0.1);
    border-left: 4px solid #22c55e;
}

.metric-card {
    background-color: var(--background-color);
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid var(--border-color);
}

/* Adaptación automática para tema oscuro */
@media (prefers-color-scheme: dark) {
    .status-success {
        background-color: rgba(16, 185, 129, 0.2);
    }
    
    .status-error {
        background-color: rgba(239, 68, 68, 0.2);
    }
    
    .status-warning {
        background-color: rgba(245, 158, 11, 0.2);
    }
    
    .chat-user {
        background-color: rgba(59, 130, 246, 0.2);
    }
    
    .chat-assistant {
        background-color: rgba(34, 197, 94, 0.2);
    }
}

/* Forzar colores específicos para Streamlit en modo oscuro */
[data-testid="stApp"][data-baseweb-theme="dark"] .chat-message {
    color: #ffffff !important;
}

[data-testid="stApp"][data-baseweb-theme="light"] .chat-message {
    color: #000000 !important;
}

/* Asegurar que el texto sea legible en ambos temas */
[data-testid="stApp"] .chat-message strong {
    color: inherit;
}

[data-testid="stApp"] .chat-message small {
    color: inherit;
    opacity: 0.8;
}
</style>""",
    unsafe_allow_html=True,
)


def initialize_session_state():
    """Inicializar estado de la sesión"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        orchestrator.initialize_session(st.session_state.session_id)

    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    if "documents_processed" not in st.session_state:
        st.session_state.documents_processed = False

    if "processing_results" not in st.session_state:
        st.session_state.processing_results = None


async def process_uploaded_files(uploaded_files):
    """Procesar archivos PDF subidos"""

    if not uploaded_files:
        return None

    if len(uploaded_files) > settings.MAX_PDF_FILES:
        st.error(f"❌ Máximo {settings.MAX_PDF_FILES} archivos permitidos")
        return None

    # Preparar datos de archivos
    files_data = []

    with st.spinner("📄 Procesando archivos PDF..."):
        for uploaded_file in uploaded_files:
            # Validar tamaño
            if uploaded_file.size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                st.error(
                    f"❌ Archivo {uploaded_file.name} demasiado grande (máximo {settings.MAX_FILE_SIZE_MB}MB)"
                )
                continue

            # Leer contenido
            content = uploaded_file.read()

            files_data.append({"filename": uploaded_file.name, "content": content})

    if not files_data:
        return None

    # Procesar documentos
    try:
        result = await orchestrator.process_documents(files_data)
        return result
    except Exception as e:
        st.error(f"❌ Error procesando documentos: {str(e)}")
        return None


async def process_user_query(query: str):
    """Procesar consulta del usuario"""
    try:
        result = await orchestrator.process_user_query(query)

        # Validar que la respuesta tenga la estructura esperada
        if not isinstance(result, dict):
            return {
                "success": False,
                "error": f"Respuesta inválida del orchestrator: {type(result)}",
                "message": "Error interno de la aplicación",
            }

        return result
    except Exception as e:
        logger.error(f"Error en process_user_query: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error procesando la consulta",
        }


def display_system_status():
    """Mostrar estado del sistema"""

    st.sidebar.header("🔧 Estado del Sistema")

    # Estado del LLM
    llm_status = llm_manager.get_provider_status()

    with st.sidebar.expander("🤖 Estado LLM", expanded=True):
        st.write(f"**Proveedor activo:** {llm_status['active_provider']}")
        st.write(
            f"**Proveedores disponibles:** {len(llm_status['available_providers'])}"
        )

        for provider, available in llm_status["provider_status"].items():
            status = "✅" if available else "❌"
            st.write(f"- {provider}: {status}")

    # Estado del Vector Store
    vector_status = vector_store.get_collection_stats()

    with st.sidebar.expander("📊 Vector Store", expanded=True):
        if "error" not in vector_status:
            st.write(f"**Documentos:** {vector_status['document_count']}")
            st.write(f"**Colección:** {vector_status['collection_name']}")
            st.write(f"**Estado:** ✅ Disponible")
        else:
            st.write("**Estado:** ❌ Error")
            st.write(f"Error: {vector_status['error']}")


def display_processing_results(results: Dict[str, Any]):
    """Mostrar resultados del procesamiento"""

    if not results or not results.get("success"):
        return

    st.success(results.get("message", "Documentos procesados exitosamente"))

    # Resumen de procesamiento
    summary = results.get("processing_summary", {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📄 Archivos", summary.get("total_files", 0))

    with col2:
        st.metric("📝 Chunks", summary.get("total_chunks", 0))

    with col3:
        st.metric("📊 Caracteres", summary.get("total_text_length", 0))

    with col4:
        st.metric("💾 Vector Store", "✅ Activo")

    # Detalles de archivos
    files_summary = results.get("files_summary", [])

    if files_summary:
        st.subheader("📋 Detalles de Archivos Procesados")

        for file_info in files_summary:
            with st.expander(f"📄 {file_info['filename']}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Título:** {file_info['title']}")
                    st.write(f"**Autor:** {file_info['author']}")

                with col2:
                    st.write(f"**Páginas:** {file_info['pages']}")
                    st.write(f"**Chunks:** {file_info['chunks']}")

    # Resumen de documentos
    doc_summary = results.get("documents_summary", "")
    if doc_summary:
        st.subheader("📖 Resumen de Documentos")
        st.info(doc_summary)


def display_conversation_history():
    """Mostrar historial de conversación"""

    history = st.session_state.conversation_history

    if not history:
        st.info("💬 Haz una pregunta para comenzar la conversación")
        return

    for i, (query, response) in enumerate(history):
        # Mensaje del usuario
        st.markdown(
            f"""
        <div class="chat-message chat-user">
            <strong>👤 Tú:</strong><br>
            {query}
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Respuesta del asistente
        if response and isinstance(response, dict) and response.get("success"):
            content = response.get("response", "Sin respuesta")
            sources = response.get("sources", [])
            intent = response.get("intent", "general")

            # Validar que sources sea una lista
            if not isinstance(sources, list):
                sources = []

            sources_text = (
                f"<br><small>📚 Fuentes: {', '.join(sources)}</small>"
                if sources
                else ""
            )
            intent_text = f"<br><small>🎯 Tipo: {intent}</small>"

            st.markdown(
                f"""
            <div class="chat-message chat-assistant">
                <strong>🤖 PDF Copilot:</strong><br>
                {content}
                {sources_text}
                {intent_text}
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            error_msg = (
                response.get("error", "Error desconocido")
                if response
                else "Sin respuesta"
            )
            st.markdown(
                f"""
            <div class="chat-message status-error">
                <strong>❌ Error:</strong><br>
                {error_msg}
            </div>
            """,
                unsafe_allow_html=True,
            )


def main():
    """Función principal de la aplicación"""

    # Inicializar estado
    initialize_session_state()

    # Header principal
    st.markdown('<h1 class="main-header">📄 PDF Copilot</h1>', unsafe_allow_html=True)
    st.markdown(
        "**Copiloto conversacional inteligente para análisis de documentos PDF**"
    )

    # Sidebar con estado del sistema
    display_system_status()

    # Sidebar con configuración
    st.sidebar.header("⚙️ Configuración")

    # Cambio de proveedor LLM
    available_providers = llm_manager.get_available_providers()
    if available_providers:
        current_provider = llm_manager.active_provider
        selected_provider = st.sidebar.selectbox(
            "Proveedor LLM",
            available_providers,
            index=(
                available_providers.index(current_provider)
                if current_provider in available_providers
                else 0
            ),
        )

        if selected_provider != current_provider:
            if llm_manager.set_active_provider(selected_provider):
                st.sidebar.success(f"✅ Cambiado a {selected_provider}")
                st.rerun()

    # Botón para limpiar sesión
    if st.sidebar.button("🗑️ Limpiar Sesión"):
        orchestrator.clear_session()
        st.session_state.clear()
        st.success("✅ Sesión limpiada")
        st.rerun()

    # Área principal
    tab1, tab2, tab3 = st.tabs(
        ["📄 Subir Documentos", "💬 Conversación", "📊 Estadísticas"]
    )

    with tab1:
        st.header("📤 Subir Documentos PDF")

        # Upload de archivos
        uploaded_files = st.file_uploader(
            f"Selecciona hasta {settings.MAX_PDF_FILES} archivos PDF",
            type=["pdf"],
            accept_multiple_files=True,
            help=f"Tamaño máximo por archivo: {settings.MAX_FILE_SIZE_MB}MB",
        )

        if uploaded_files:
            st.write(f"**Archivos seleccionados:** {len(uploaded_files)}")

            for file in uploaded_files:
                size_mb = file.size / (1024 * 1024)
                st.write(f"- {file.name} ({size_mb:.1f}MB)")

            if st.button("🚀 Procesar Documentos", type="primary"):
                # Ejecutar procesamiento
                result = asyncio.run(process_uploaded_files(uploaded_files))

                if result:
                    st.session_state.documents_processed = True
                    st.session_state.processing_results = result
                    st.rerun()

        # Mostrar resultados si existen
        if st.session_state.processing_results:
            display_processing_results(st.session_state.processing_results)

    with tab2:
        st.header("💬 Conversación")

        if not st.session_state.documents_processed:
            st.warning("⚠️ Primero debes subir y procesar documentos PDF")
        else:
            # Input para consultas
            query = st.text_input(
                "Haz una pregunta sobre tus documentos:",
                placeholder="Ej: ¿Cuáles son los puntos principales del documento?",
                help="Puedes preguntar sobre resúmenes, comparaciones, temas específicos, etc.",
            )

            col1, col2 = st.columns([1, 4])

            with col1:
                send_query = st.button("📤 Enviar", type="primary")

            if query and send_query:
                # Procesar consulta
                with st.spinner("🤔 Procesando tu consulta..."):
                    result = asyncio.run(process_user_query(query))

                # Añadir a historial
                st.session_state.conversation_history.append((query, result))
                st.rerun()

            # Mostrar historial
            display_conversation_history()

    with tab3:
        st.header("📊 Estadísticas y Métricas")

        # Estado de la sesión
        session_status = orchestrator.get_session_status()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Estado de la Sesión")
            st.json(session_status)

        with col2:
            st.subheader("🔍 Historial de Conversación")
            history = orchestrator.get_conversation_history()

            if history:
                st.write(f"**Total de interacciones:** {len(history)}")

                # Tipos de consultas
                query_types = [h.get("type", "unknown") for h in history]
                from collections import Counter

                type_counts = Counter(query_types)

                st.write("**Tipos de consultas:**")
                for query_type, count in type_counts.items():
                    st.write(f"- {query_type}: {count}")
            else:
                st.info("Sin historial disponible")


if __name__ == "__main__":
    main()
