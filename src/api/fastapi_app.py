"""
API FastAPI para PDF Copilot
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import asyncio
import logging
from pathlib import Path
import sys

# Añadir el directorio src al path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from core.orchestrator import orchestrator
    from core.config import settings
    from core.llm_manager import llm_manager
    from core.vectorstore import vector_store
except ImportError as e:
    logging.error(f"Error importando módulos: {e}")
    raise

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="PDF Copilot API",
    description="API REST para el copiloto conversacional de documentos PDF",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Modelos Pydantic
class SessionCreateRequest(BaseModel):
    session_id: Optional[str] = None


class SessionCreateResponse(BaseModel):
    session_id: str
    state: str
    message: str
    llm_status: Dict[str, Any]
    vectorstore_status: Dict[str, Any]


class QueryRequest(BaseModel):
    session_id: str
    query: str


class QueryResponse(BaseModel):
    success: bool
    query: str
    intent: str
    response: str
    sources: List[str]
    context_used: int
    timestamp: str
    error: Optional[str] = None


class DocumentProcessingResponse(BaseModel):
    success: bool
    state: str
    processing_summary: Optional[Dict[str, Any]] = None
    files_summary: Optional[List[Dict[str, Any]]] = None
    documents_summary: Optional[str] = None
    message: str
    error: Optional[str] = None


class StatusResponse(BaseModel):
    session_id: Optional[str]
    state: str
    context: Dict[str, Any]
    conversation_length: int
    llm_status: Dict[str, Any]
    vectorstore_status: Dict[str, Any]


# Endpoints
@app.get("/", summary="Health Check")
async def root():
    """Endpoint de health check"""
    return {"message": "PDF Copilot API", "version": "1.0.0", "status": "running"}


@app.get("/health", summary="Health Status")
async def health_check():
    """Verificar estado de salud de la API"""

    # Verificar componentes
    llm_status = llm_manager.get_provider_status()
    vector_status = vector_store.get_collection_stats()

    health_status = {
        "api": "healthy",
        "llm": "healthy" if llm_status["active_provider"] else "error",
        "vectorstore": "healthy" if vector_status.get("is_available") else "error",
        "timestamp": str(asyncio.get_event_loop().time()),
    }

    # Determinar estado general
    overall_status = (
        "healthy"
        if all(
            status == "healthy"
            for status in health_status.values()
            if status != health_status["timestamp"]
        )
        else "degraded"
    )

    health_status["overall"] = overall_status

    return health_status


@app.post(
    "/sessions", response_model=SessionCreateResponse, summary="Create New Session"
)
async def create_session(request: SessionCreateRequest):
    """Crear nueva sesión de conversación"""

    try:
        session_id = request.session_id or str(uuid.uuid4())
        result = orchestrator.initialize_session(session_id)

        return SessionCreateResponse(**result)

    except Exception as e:
        logger.error(f"Error creando sesión: {e}")
        raise HTTPException(status_code=500, detail=f"Error creando sesión: {str(e)}")


@app.get(
    "/sessions/{session_id}/status",
    response_model=StatusResponse,
    summary="Get Session Status",
)
async def get_session_status(session_id: str):
    """Obtener estado de una sesión"""

    try:
        # Configurar sesión si es necesaria
        if orchestrator.session_id != session_id:
            orchestrator.initialize_session(session_id)

        status = orchestrator.get_session_status()
        return StatusResponse(**status)

    except Exception as e:
        logger.error(f"Error obteniendo estado de sesión: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo estado: {str(e)}"
        )


@app.post(
    "/sessions/{session_id}/documents",
    response_model=DocumentProcessingResponse,
    summary="Upload and Process Documents",
)
async def upload_documents(
    session_id: str,
    files: List[UploadFile] = File(..., description="Archivos PDF a procesar"),
):
    """Subir y procesar documentos PDF"""

    try:
        # Configurar sesión
        if orchestrator.session_id != session_id:
            orchestrator.initialize_session(session_id)

        # Validar archivos
        if len(files) > settings.MAX_PDF_FILES:
            raise HTTPException(
                status_code=400,
                detail=f"Máximo {settings.MAX_PDF_FILES} archivos permitidos",
            )

        # Preparar datos de archivos
        files_data = []

        for file in files:
            # Validar tipo de archivo
            if not file.filename.lower().endswith(".pdf"):
                raise HTTPException(
                    status_code=400, detail=f"Archivo {file.filename} no es PDF"
                )

            # Validar tamaño
            content = await file.read()
            if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=400, detail=f"Archivo {file.filename} demasiado grande"
                )

            files_data.append({"filename": file.filename, "content": content})

        # Procesar documentos
        result = await orchestrator.process_documents(files_data)

        return DocumentProcessingResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando documentos: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error procesando documentos: {str(e)}"
        )


@app.post(
    "/sessions/{session_id}/query",
    response_model=QueryResponse,
    summary="Process User Query",
)
async def process_query(session_id: str, request: QueryRequest):
    """Procesar consulta del usuario"""

    try:
        # Configurar sesión
        if orchestrator.session_id != session_id:
            orchestrator.initialize_session(session_id)

        # Procesar consulta
        result = await orchestrator.process_user_query(request.query)

        if result.get("success"):
            return QueryResponse(**result)
        else:
            return QueryResponse(
                success=False,
                query=request.query,
                intent="error",
                response="",
                sources=[],
                context_used=0,
                timestamp="",
                error=result.get("error", "Error desconocido"),
            )

    except Exception as e:
        logger.error(f"Error procesando consulta: {e}")
        return QueryResponse(
            success=False,
            query=request.query,
            intent="error",
            response="",
            sources=[],
            context_used=0,
            timestamp="",
            error=str(e),
        )


@app.get("/sessions/{session_id}/history", summary="Get Conversation History")
async def get_conversation_history(session_id: str):
    """Obtener historial de conversación"""

    try:
        # Configurar sesión
        if orchestrator.session_id != session_id:
            orchestrator.initialize_session(session_id)

        history = orchestrator.get_conversation_history()

        return {
            "session_id": session_id,
            "history": history,
            "total_interactions": len(history),
        }

    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo historial: {str(e)}"
        )


@app.delete("/sessions/{session_id}", summary="Clear Session")
async def clear_session(session_id: str):
    """Limpiar sesión y datos asociados"""

    try:
        # Configurar sesión
        if orchestrator.session_id != session_id:
            orchestrator.initialize_session(session_id)

        result = orchestrator.clear_session()

        return {
            "session_id": session_id,
            "cleared": True,
            "message": "Sesión limpiada exitosamente",
        }

    except Exception as e:
        logger.error(f"Error limpiando sesión: {e}")
        raise HTTPException(status_code=500, detail=f"Error limpiando sesión: {str(e)}")


@app.get("/llm/providers", summary="Get LLM Providers Status")
async def get_llm_providers():
    """Obtener estado de proveedores LLM"""

    return llm_manager.get_provider_status()


@app.post("/llm/provider", summary="Set Active LLM Provider")
async def set_llm_provider(provider: str):
    """Cambiar proveedor LLM activo"""

    try:
        success = llm_manager.set_active_provider(provider)

        if success:
            return {
                "success": True,
                "active_provider": provider,
                "message": f"Proveedor cambiado a {provider}",
            }
        else:
            raise HTTPException(
                status_code=400, detail=f"Proveedor {provider} no disponible"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cambiando proveedor: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error cambiando proveedor: {str(e)}"
        )


@app.get("/vectorstore/stats", summary="Get Vector Store Statistics")
async def get_vectorstore_stats():
    """Obtener estadísticas del vector store"""

    return vector_store.get_collection_stats()


@app.post("/vectorstore/clear", summary="Clear Vector Store")
async def clear_vectorstore():
    """Limpiar vector store"""

    try:
        success = vector_store.clear_collection()

        return {
            "success": success,
            "message": (
                "Vector store limpiado" if success else "Error limpiando vector store"
            ),
        }

    except Exception as e:
        logger.error(f"Error limpiando vector store: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error limpiando vector store: {str(e)}"
        )


# Manejo de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejo global de excepciones"""

    logger.error(f"Error no manejado: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "detail": str(exc) if settings.DEBUG else "Error interno",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "fastapi_app:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
