"""
Orquestador principal del sistema
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import asyncio
from datetime import datetime

from .pdf_processor import BatchPDFProcessor
from .vectorstore import vector_store
from .llm_manager import llm_manager
from .config import settings

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Estados de la conversación"""

    IDLE = "idle"
    PROCESSING_DOCUMENTS = "processing_documents"
    READY_FOR_QUESTIONS = "ready_for_questions"
    GENERATING_RESPONSE = "generating_response"
    ERROR = "error"


class IntentType(Enum):
    """Tipos de intención del usuario"""

    GENERAL_QUESTION = "general_question"
    DOCUMENT_SUMMARY = "document_summary"
    DOCUMENT_COMPARISON = "document_comparison"
    TOPIC_CLASSIFICATION = "topic_classification"
    SPECIFIC_SEARCH = "specific_search"
    METADATA_QUERY = "metadata_query"


class ConversationOrchestrator:
    """Orquestador principal de conversaciones"""

    def __init__(self):
        self.state = ConversationState.IDLE
        self.session_id: Optional[str] = None
        self.processed_files: List[Dict[str, Any]] = []
        self.conversation_history: List[Dict[str, Any]] = []
        self.pdf_processor = BatchPDFProcessor()

        # Contexto de la sesión
        self.session_context = {
            "files_loaded": False,
            "total_documents": 0,
            "total_chunks": 0,
            "available_files": [],
        }

    def initialize_session(self, session_id: str) -> Dict[str, Any]:
        """Inicializar nueva sesión"""
        self.session_id = session_id
        self.state = ConversationState.IDLE
        self.processed_files = []
        self.conversation_history = []

        logger.info(f"Sesión inicializada: {session_id}")

        return {
            "session_id": session_id,
            "state": self.state.value,
            "message": "Sesión inicializada. Puedes subir hasta 5 archivos PDF para comenzar.",
            "llm_status": llm_manager.get_provider_status(),
            "vectorstore_status": vector_store.get_collection_stats(),
        }

    async def process_documents(
        self, files_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Procesar documentos PDF subidos"""
        try:
            self.state = ConversationState.PROCESSING_DOCUMENTS

            # Validar archivos
            if len(files_data) > settings.MAX_PDF_FILES:
                raise ValueError(f"Máximo {settings.MAX_PDF_FILES} archivos permitidos")

            # Procesar PDFs
            processing_result = self.pdf_processor.process_multiple_pdfs(files_data)

            # Añadir al vector store
            if processing_result["all_chunks"]:
                success = vector_store.add_documents(processing_result["all_chunks"])
                if not success:
                    raise Exception("Error añadiendo documentos al vector store")

            # Actualizar contexto de sesión
            self.processed_files = processing_result["processing_results"]
            self.session_context.update(
                {
                    "files_loaded": True,
                    "total_documents": processing_result["total_files"],
                    "total_chunks": processing_result["total_chunks"],
                    "available_files": processing_result["files_processed"],
                }
            )

            self.state = ConversationState.READY_FOR_QUESTIONS

            # Generar resumen automático de los documentos
            summary = await self._generate_documents_summary()

            result = {
                "success": True,
                "state": self.state.value,
                "processing_summary": processing_result,
                "files_summary": self.pdf_processor.get_files_summary(),
                "documents_summary": summary,
                "message": f"✅ {processing_result['total_files']} documentos procesados exitosamente. Puedes hacer preguntas sobre el contenido.",
            }

            # Añadir a historial
            self.conversation_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": "document_processing",
                    "content": result,
                }
            )

            return result

        except Exception as e:
            self.state = ConversationState.ERROR
            error_msg = f"Error procesando documentos: {str(e)}"
            logger.error(error_msg)

            return {
                "success": False,
                "state": self.state.value,
                "error": error_msg,
                "message": "❌ Error procesando documentos. Verifica los archivos e intenta nuevamente.",
            }

    async def process_user_query(self, query: str) -> Dict[str, Any]:
        """Procesar consulta del usuario"""
        try:
            if self.state != ConversationState.READY_FOR_QUESTIONS:
                return {
                    "success": False,
                    "message": "Primero debes subir documentos PDF para poder hacer preguntas.",
                }

            self.state = ConversationState.GENERATING_RESPONSE

            # Detectar intención
            intent = self._detect_intent(query)

            # Obtener contexto relevante
            context_docs = await self._get_relevant_context(query, intent)

            # Generar respuesta según la intención
            response = await self._generate_response_by_intent(
                query, intent, context_docs
            )

            # Formatear respuesta final
            result = {
                "success": True,
                "query": query,
                "intent": intent.value,
                "response": response["content"],
                "sources": response["sources"],
                "context_used": len(context_docs),
                "timestamp": datetime.now().isoformat(),
            }

            # Añadir a historial
            self.conversation_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "type": "user_query",
                    "query": query,
                    "response": result,
                }
            )

            self.state = ConversationState.READY_FOR_QUESTIONS
            return result

        except Exception as e:
            self.state = ConversationState.ERROR
            error_msg = f"Error procesando consulta: {str(e)}"
            logger.error(error_msg)

            return {
                "success": False,
                "error": error_msg,
                "message": "❌ Error procesando tu consulta. Intenta reformular la pregunta.",
            }

    def _detect_intent(self, query: str) -> IntentType:
        """Detectar intención del usuario"""
        query_lower = query.lower()

        # Palabras clave para cada intención
        summary_keywords = ["resumen", "resume", "resúmenes", "summarize", "summary"]
        comparison_keywords = [
            "compara",
            "diferencias",
            "comparación",
            "compare",
            "vs",
            "versus",
        ]
        classification_keywords = [
            "clasificar",
            "categorías",
            "temas",
            "topics",
            "classify",
        ]
        metadata_keywords = ["autor", "fecha", "páginas", "metadatos", "metadata"]

        if any(keyword in query_lower for keyword in summary_keywords):
            return IntentType.DOCUMENT_SUMMARY
        elif any(keyword in query_lower for keyword in comparison_keywords):
            return IntentType.DOCUMENT_COMPARISON
        elif any(keyword in query_lower for keyword in classification_keywords):
            return IntentType.TOPIC_CLASSIFICATION
        elif any(keyword in query_lower for keyword in metadata_keywords):
            return IntentType.METADATA_QUERY
        else:
            return IntentType.GENERAL_QUESTION

    async def _get_relevant_context(
        self, query: str, intent: IntentType
    ) -> List[Dict[str, Any]]:
        """Obtener contexto relevante según la consulta e intención"""
        if intent == IntentType.METADATA_QUERY:
            # Para consultas de metadatos, no necesitamos búsqueda semántica
            return []

        # Búsqueda semántica estándar
        results = vector_store.similarity_search(query, k=5)

        # Filtrar por relevancia (threshold más bajo para ser más inclusivo)
        relevant_results = [r for r in results if r["relevance_score"] > 0.1]

        return relevant_results[:3]  # Máximo 3 documentos de contexto

    async def _generate_response_by_intent(
        self, query: str, intent: IntentType, context_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generar respuesta según la intención detectada"""

        if intent == IntentType.DOCUMENT_SUMMARY:
            return await self._handle_summary_request(query, context_docs)
        elif intent == IntentType.DOCUMENT_COMPARISON:
            return await self._handle_comparison_request(query, context_docs)
        elif intent == IntentType.TOPIC_CLASSIFICATION:
            return await self._handle_classification_request(query, context_docs)
        elif intent == IntentType.METADATA_QUERY:
            return await self._handle_metadata_query(query)
        else:
            return await self._handle_general_question(query, context_docs)

    async def _handle_general_question(
        self, query: str, context_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Manejar pregunta general"""
        context_text = "\n\n".join([doc["content"] for doc in context_docs])

        prompt = f"""
        Basándote en el contexto proporcionado de los documentos PDF, responde la siguiente pregunta de manera precisa y completa.
        
        Contexto de los documentos:
        {context_text}
        
        Pregunta: {query}
        
        Instrucciones:
        - Proporciona una respuesta clara y directa
        - Cita información específica de los documentos cuando sea relevante
        - Si la información no está en el contexto, indícalo claramente
        - Mantén un tono profesional y útil
        """

        response = llm_manager.generate_response(prompt)

        return {
            "content": response,
            "sources": [doc["metadata"]["source_file"] for doc in context_docs],
            "type": "general_answer",
        }

    async def _handle_summary_request(
        self, query: str, context_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Manejar solicitud de resumen"""
        # Usar agente de resumen especializado
        from agents.summarizer import DocumentSummarizer

        summarizer = DocumentSummarizer()

        if "todos" in query.lower() or "all" in query.lower():
            # Resumen de todos los documentos
            all_docs = []
            for file_info in self.processed_files:
                # Manejar objetos Document correctamente
                for chunk in file_info["chunks"]:
                    if hasattr(chunk, "page_content"):
                        all_docs.append(chunk.page_content)
                    elif isinstance(chunk, dict) and "content" in chunk:
                        all_docs.append(chunk["content"])
                    elif isinstance(chunk, dict) and "page_content" in chunk:
                        all_docs.append(chunk["page_content"])
                    else:
                        all_docs.append(str(chunk))
            summary = await summarizer.generate_comprehensive_summary(all_docs)
        else:
            # Resumen del contexto relevante
            context_text = [doc["content"] for doc in context_docs]
            summary = await summarizer.generate_targeted_summary(context_text, query)

        return {
            "content": summary,
            "sources": list(
                set([doc["metadata"]["source_file"] for doc in context_docs])
            ),
            "type": "summary",
        }

    async def _handle_comparison_request(
        self, query: str, context_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Manejar solicitud de comparación"""
        try:
            from agents.comparator import DocumentComparator

            comparator = DocumentComparator()

            # usar SIEMPRE todos los archivos procesados
            all_sources = {}

            # Obtener contenido de todos los archivos procesados
            if self.processed_files and len(self.processed_files) >= 2:
                for file_info in self.processed_files:
                    filename = file_info["filename"]
                    # Tomar una muestra representativa de chunks de cada archivo
                    chunks_sample = file_info["chunks"][:3]  # Primeros 3 chunks

                    # Manejar tanto objetos Document como diccionarios
                    content_list = []
                    for chunk in chunks_sample:
                        if hasattr(chunk, "page_content"):
                            # Es un objeto Document de LangChain
                            content_list.append(chunk.page_content)
                        elif isinstance(chunk, dict) and "content" in chunk:
                            # Es un diccionario con clave 'content'
                            content_list.append(chunk["content"])
                        elif isinstance(chunk, dict) and "page_content" in chunk:
                            # Es un diccionario con clave 'page_content'
                            content_list.append(chunk["page_content"])
                        else:
                            # Último recurso: convertir a string
                            content_list.append(str(chunk))

                    all_sources[filename] = content_list
            else:
                # Fallback: si no hay suficientes archivos procesados, informar al usuario
                return {
                    "content": "Para realizar una comparación, necesitas tener al menos 2 documentos cargados. Actualmente tienes {} documento(s) cargado(s).".format(
                        len(self.processed_files)
                    ),
                    "sources": (
                        [f["filename"] for f in self.processed_files]
                        if self.processed_files
                        else []
                    ),
                    "type": "comparison",
                }

            # Realizar comparación
            comparison = await comparator.compare_documents(all_sources, query)

            return {
                "content": comparison,
                "sources": list(all_sources.keys()),
                "type": "comparison",
            }

        except Exception as e:
            logger.error(f"Error en comparación: {e}")
            return {
                "content": f"Error al procesar la comparación: {str(e)}",
                "sources": [],
                "type": "comparison",
            }

    async def _handle_classification_request(
        self, query: str, context_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Manejar solicitud de clasificación"""
        from agents.classifier import TopicClassifier

        classifier = TopicClassifier()

        # Clasificar todos los documentos por temas
        all_chunks = []
        for file_info in self.processed_files:
            all_chunks.extend(file_info["chunks"])

        classification = await classifier.classify_documents_by_topics(all_chunks)

        return {
            "content": classification,
            "sources": self.session_context["available_files"],
            "type": "classification",
        }

    async def _handle_metadata_query(self, query: str) -> Dict[str, Any]:
        """Manejar consulta de metadatos"""
        metadata_summary = []

        for file_info in self.processed_files:
            metadata = file_info["metadata"]
            metadata_summary.append(
                f"""
            📄 **{metadata['filename']}**
            - Título: {metadata['title']}
            - Autor: {metadata['author']}
            - Páginas: {metadata['num_pages']}
            - Chunks generados: {file_info['num_chunks']}
            - Longitud de texto: {file_info['text_length']} caracteres
            """
            )

        response = "\n".join(metadata_summary)

        return {
            "content": response,
            "sources": self.session_context["available_files"],
            "type": "metadata",
        }

    async def _generate_documents_summary(self) -> str:
        """Generar resumen automático de los documentos cargados"""
        if not self.processed_files:
            return "No hay documentos procesados"

        files_info = []
        for file_info in self.processed_files:
            preview = (
                file_info["full_text"][:300] + "..."
                if len(file_info["full_text"]) > 300
                else file_info["full_text"]
            )
            files_info.append(f"**{file_info['filename']}**: {preview}")

        prompt = f"""
        Genera un resumen ejecutivo breve de los siguientes documentos PDF que han sido cargados al sistema:
        
        {chr(10).join(files_info)}
        
        El resumen debe:
        - Ser conciso (máximo 200 palabras)
        - Identificar los temas principales
        - Mencionar los tipos de documentos cargados
        - Ser útil para orientar al usuario sobre qué puede preguntar
        """

        return llm_manager.generate_response(prompt)

    def get_session_status(self) -> Dict[str, Any]:
        """Obtener estado actual de la sesión"""
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "context": self.session_context,
            "conversation_length": len(self.conversation_history),
            "llm_status": llm_manager.get_provider_status(),
            "vectorstore_status": vector_store.get_collection_stats(),
        }

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Obtener historial de conversación"""
        return self.conversation_history

    def clear_session(self) -> Dict[str, Any]:
        """Limpiar sesión actual"""
        self.state = ConversationState.IDLE
        self.session_id = None
        self.processed_files = []
        self.conversation_history = []
        self.session_context = {
            "files_loaded": False,
            "total_documents": 0,
            "total_chunks": 0,
            "available_files": [],
        }

        # Limpiar vector store
        vector_store.clear_collection()

        return {"success": True, "message": "Sesión limpiada exitosamente"}


# Instancia global del orquestador
orchestrator = ConversationOrchestrator()
