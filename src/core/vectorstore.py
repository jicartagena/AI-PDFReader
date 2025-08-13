"""
Gestor de vector store usando ChromaDB para almacenamiento y búsqueda semántica
"""

import logging
from typing import List, Dict, Any, Optional
import uuid
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
except ImportError:
    chromadb = None
    logging.warning("ChromaDB no disponible")

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
    logging.warning("SentenceTransformers no disponible")

from langchain_core.documents import Document
from .config import settings

logger = logging.getLogger(__name__)


class EmbeddingsManager:
    """Gestor de embeddings usando Sentence Transformers"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Inicializar modelo de embeddings"""
        if SentenceTransformer is None:
            logger.error("SentenceTransformers no disponible")
            return

        try:
            # Configurar para usar solo archivos locales (sin acceso a HuggingFace Hub)
            import os

            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            os.environ["HF_HUB_OFFLINE"] = "1"

            # Intentar cargar el modelo con configuración local
            self.model = SentenceTransformer(self.model_name, device="cpu")
            logger.info(f"Modelo de embeddings cargado: {self.model_name}")
        except Exception as e:
            logger.warning(f"Error cargando modelo de embeddings: {e}")
            logger.info("Intentando con modelo más simple...")

            # Fallback a un modelo básico si no funciona
            try:
                # Forzar descarga si es la primera vez
                os.environ.pop("TRANSFORMERS_OFFLINE", None)
                os.environ.pop("HF_HUB_OFFLINE", None)

                self.model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
                logger.info("Modelo de embeddings cargado exitosamente")

                # Reestablecer modo offline para siguientes usos
                os.environ["TRANSFORMERS_OFFLINE"] = "1"
                os.environ["HF_HUB_OFFLINE"] = "1"
            except Exception as e2:
                logger.error(f"Error crítico cargando embeddings: {e2}")
                self.model = None

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generar embeddings para lista de textos"""
        if not self.model:
            logger.error("Modelo de embeddings no disponible")
            return []

        try:
            embeddings = self.model.encode(texts, show_progress_bar=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generando embeddings: {e}")
            return []

    def is_available(self) -> bool:
        """Verificar si el modelo está disponible"""
        return self.model is not None


class VectorStore:
    """Gestor de vector store usando ChromaDB"""

    def __init__(self, collection_name: str = "pdf_documents"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.embeddings_manager = EmbeddingsManager(settings.EMBEDDINGS_MODEL)
        self._initialize_chroma()

    def _initialize_chroma(self):
        """Inicializar ChromaDB"""
        if chromadb is None:
            logger.error("ChromaDB no disponible")
            return

        try:
            # Configurar cliente persistente
            persist_directory = Path(settings.CHROMA_PERSIST_DIRECTORY)
            persist_directory.mkdir(parents=True, exist_ok=True)

            self.client = chromadb.PersistentClient(path=str(persist_directory))

            # Obtener o crear colección
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "PDF documents collection"},
            )

            logger.info(f"ChromaDB inicializado: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error inicializando ChromaDB: {e}")

    def add_documents(self, documents: List[Document]) -> bool:
        """Añadir documentos al vector store"""
        if not self.collection or not self.embeddings_manager.is_available():
            logger.error("Vector store no disponible")
            return False

        try:
            # Preparar datos
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            ids = [str(uuid.uuid4()) for _ in documents]

            # Generar embeddings
            embeddings = self.embeddings_manager.generate_embeddings(texts)

            if not embeddings:
                logger.error("No se pudieron generar embeddings")
                return False

            # Añadir a ChromaDB
            self.collection.add(
                embeddings=embeddings, documents=texts, metadatas=metadatas, ids=ids
            )

            logger.info(f"Añadidos {len(documents)} documentos al vector store")
            return True

        except Exception as e:
            logger.error(f"Error añadiendo documentos: {e}")
            return False

    def similarity_search(
        self, query: str, k: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Búsqueda por similitud"""
        if not self.collection or not self.embeddings_manager.is_available():
            logger.error("Vector store no disponible")
            return []

        try:
            # Generar embedding de la query
            query_embedding = self.embeddings_manager.generate_embeddings([query])[0]

            # Preparar filtros
            where_clause = None
            if filters:
                where_clause = filters

            # Realizar búsqueda
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )

            # Formatear resultados
            formatted_results = []
            for i in range(len(results["documents"][0])):
                distance = results["distances"][0][i]
                # Convertir distancia a score de similitud (0-1, donde 1 es más similar)
                # Usar función que maneja distancias mayores a 1
                relevance_score = max(0.0, 1.0 / (1.0 + distance))

                formatted_results.append(
                    {
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": distance,
                        "relevance_score": relevance_score,
                    }
                )

            logger.info(f"Búsqueda completada: {len(formatted_results)} resultados")
            return formatted_results

        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la colección"""
        if not self.collection:
            return {"error": "Collection not available"}

        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "embeddings_model": self.embeddings_manager.model_name,
                "is_available": True,
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {"error": str(e)}

    def clear_collection(self) -> bool:
        """Limpiar toda la colección"""
        if not self.collection:
            return False

        try:
            # Eliminar colección actual
            self.client.delete_collection(self.collection_name)

            # Recrear colección vacía
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "PDF documents collection"},
            )

            logger.info("Colección limpiada")
            return True
        except Exception as e:
            logger.error(f"Error limpiando colección: {e}")
            return False

    def search_by_metadata(
        self, metadata_filters: Dict[str, Any], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Buscar documentos por metadatos"""
        if not self.collection:
            return []

        try:
            results = self.collection.get(
                where=metadata_filters, limit=limit, include=["documents", "metadatas"]
            )

            formatted_results = []
            for i in range(len(results["documents"])):
                formatted_results.append(
                    {
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i],
                    }
                )

            return formatted_results
        except Exception as e:
            logger.error(f"Error buscando por metadatos: {e}")
            return []

    def get_documents_by_file(self, filename: str) -> List[Dict[str, Any]]:
        """Obtener todos los chunks de un archivo específico"""
        return self.search_by_metadata({"source_file": filename})

    def is_available(self) -> bool:
        """Verificar si el vector store está disponible"""
        return self.collection is not None and self.embeddings_manager.is_available()


# Instancia global del vector store
vector_store = VectorStore(settings.CHROMA_COLLECTION_NAME)
