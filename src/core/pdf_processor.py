import logging
from typing import List, Dict, Any
import hashlib
from io import BytesIO
import PyPDF2
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from core.config import settings

logger = logging.getLogger(__name__)


class PDFProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    def extract_text_pypdf2(self, file_content: bytes) -> str:
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error con PyPDF2: {e}")
            return ""

    def extract_text_pdfplumber(self, file_content: bytes) -> str:
        try:
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

                    tables = page.extract_tables()
                    for table in tables:
                        table_text = "\n".join(
                            ["\t".join([cell or "" for cell in row]) for row in table]
                        )
                        text += f"\n[TABLA]\n{table_text}\n[/TABLA]\n"

            return text
        except Exception as e:
            logger.error(f"Error con pdfplumber: {e}")
            return ""

    def safe_extract_metadata_value(self, value):
        if value is None:
            return ""
        try:
            str_value = str(value)
            return str_value.strip()
        except:
            return ""

    def extract_metadata(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            metadata = pdf_reader.metadata or {}

            return {
                "filename": filename,
                "title": self.safe_extract_metadata_value(metadata.get("/Title"))
                or filename,
                "author": self.safe_extract_metadata_value(metadata.get("/Author"))
                or "Unknown",
                "subject": self.safe_extract_metadata_value(metadata.get("/Subject"))
                or "",
                "creator": self.safe_extract_metadata_value(metadata.get("/Creator"))
                or "",
                "producer": self.safe_extract_metadata_value(metadata.get("/Producer"))
                or "",
                "creation_date": self.safe_extract_metadata_value(
                    metadata.get("/CreationDate")
                )
                or "",
                "modification_date": self.safe_extract_metadata_value(
                    metadata.get("/ModDate")
                )
                or "",
                "num_pages": len(pdf_reader.pages),
                "file_hash": hashlib.md5(file_content).hexdigest(),
            }
        except Exception as e:
            logger.error(f"Error extrayendo metadatos: {e}")
            return {
                "filename": filename,
                "title": filename,
                "author": "Unknown",
                "subject": "",
                "creator": "",
                "producer": "",
                "creation_date": "",
                "modification_date": "",
                "num_pages": 0,
                "file_hash": hashlib.md5(file_content).hexdigest(),
            }

    def process_pdf(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        logger.info(f"Procesando PDF: {filename}")

        metadata = self.extract_metadata(file_content, filename)
        text = self.extract_text_pdfplumber(file_content)

        if not text.strip():
            logger.warning(f"pdfplumber falló para {filename}, usando PyPDF2")
            text = self.extract_text_pypdf2(file_content)

        if not text.strip():
            raise ValueError(f"No se pudo extraer texto de {filename}")

        document = Document(page_content=text, metadata=metadata)
        chunks = self.text_splitter.split_documents([document])

        for i, chunk in enumerate(chunks):
            safe_metadata = {}
            for key, value in chunk.metadata.items():
                if isinstance(value, (str, int, float, bool)) or value is None:
                    safe_metadata[key] = value
                else:
                    safe_metadata[key] = str(value)

            safe_metadata.update(
                {"chunk_id": i, "total_chunks": len(chunks), "source_file": filename}
            )

            chunk.metadata = safe_metadata

        result = {
            "filename": filename,
            "metadata": metadata,
            "full_text": text,
            "chunks": chunks,
            "num_chunks": len(chunks),
            "text_length": len(text),
        }

        logger.info(f"PDF procesado: {filename} - {len(chunks)} chunks generados")
        return result

    def validate_pdf(self, file_content: bytes, filename: str) -> bool:
        try:
            if not file_content.startswith(b"%PDF"):
                return False
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            if len(pdf_reader.pages) == 0:
                return False
            return True
        except Exception as e:
            logger.error(f"PDF inválido {filename}: {e}")
            return False

    def get_text_preview(self, file_content: bytes, max_chars: int = 500) -> str:
        try:
            text = self.extract_text_pdfplumber(file_content)
            if not text.strip():
                text = self.extract_text_pypdf2(file_content)
            text = text.strip()[:max_chars]
            if len(text) == max_chars:
                text += "..."
            return text
        except Exception as e:
            logger.error(f"Error generando preview: {e}")
            return "Error generando preview del documento"


class BatchPDFProcessor:
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.processed_files = []

    def process_multiple_pdfs(self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(files_data) > settings.MAX_PDF_FILES:
            raise ValueError(f"Máximo {settings.MAX_PDF_FILES} archivos permitidos")

        results = []
        all_chunks = []
        total_text_length = 0

        for file_info in files_data:
            try:
                filename = file_info["filename"]
                content = file_info["content"]

                if not self.pdf_processor.validate_pdf(content, filename):
                    logger.warning(f"Archivo inválido omitido: {filename}")
                    continue

                result = self.pdf_processor.process_pdf(content, filename)
                results.append(result)
                all_chunks.extend(result["chunks"])
                total_text_length += result["text_length"]

            except Exception as e:
                logger.error(f"Error procesando {filename}: {e}")
                continue

        summary = {
            "total_files": len(results),
            "total_chunks": len(all_chunks),
            "total_text_length": total_text_length,
            "files_processed": [r["filename"] for r in results],
            "processing_results": results,
            "all_chunks": all_chunks,
        }

        self.processed_files = results
        logger.info(
            f"Procesamiento completado: {len(results)} archivos, {len(all_chunks)} chunks"
        )
        return summary

    def get_files_summary(self) -> List[Dict[str, Any]]:
        return [
            {
                "filename": file_data["filename"],
                "title": file_data["metadata"]["title"],
                "author": file_data["metadata"]["author"],
                "pages": file_data["metadata"]["num_pages"],
                "chunks": file_data["num_chunks"],
                "text_length": file_data["text_length"],
            }
            for file_data in self.processed_files
        ]
