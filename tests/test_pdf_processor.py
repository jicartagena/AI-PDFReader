"""
Pruebas unitarias para PDF Processor
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Añadir src al path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from core.pdf_processor import PDFProcessor, BatchPDFProcessor


class TestPDFProcessor:
    """Pruebas para PDFProcessor"""

    def setup_method(self):
        """Configurar cada prueba"""
        self.processor = PDFProcessor()

    @pytest.fixture
    def sample_pdf_content(self):
        """Contenido PDF de ejemplo"""
        # PDF mínimo válido
        return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"

    def test_validate_pdf_valid(self, sample_pdf_content):
        """Probar validación de PDF válido"""
        result = self.processor.validate_pdf(sample_pdf_content, "test.pdf")
        assert result is True

    def test_validate_pdf_invalid(self):
        """Probar validación de PDF inválido"""
        invalid_content = b"This is not a PDF file"
        result = self.processor.validate_pdf(invalid_content, "test.txt")
        assert result is False

    @patch("core.pdf_processor.PyPDF2.PdfReader")
    def test_extract_metadata(self, mock_pdf_reader, sample_pdf_content):
        """Probar extracción de metadatos"""
        # Mock del lector PDF
        mock_reader = MagicMock()
        mock_reader.metadata = {
            "/Title": "Test Document",
            "/Author": "Test Author",
            "/Subject": "Test Subject",
        }
        mock_reader.pages = [MagicMock(), MagicMock()]  # 2 páginas
        mock_pdf_reader.return_value = mock_reader

        metadata = self.processor.extract_metadata(sample_pdf_content, "test.pdf")

        assert metadata["filename"] == "test.pdf"
        assert metadata["title"] == "Test Document"
        assert metadata["author"] == "Test Author"
        assert metadata["subject"] == "Test Subject"
        assert metadata["num_pages"] == 2

    @patch("core.pdf_processor.pdfplumber.open")
    def test_extract_text_pdfplumber(self, mock_pdfplumber, sample_pdf_content):
        """Probar extracción de texto con pdfplumber"""
        # Mock de pdfplumber
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Test content from PDF"
        mock_page.extract_tables.return_value = []

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        text = self.processor.extract_text_pdfplumber(sample_pdf_content)

        assert "Test content from PDF" in text

    def test_text_splitter_configuration(self):
        """Probar configuración del divisor de texto"""
        assert self.processor.text_splitter.chunk_size == 1000
        assert self.processor.text_splitter.chunk_overlap == 200


class TestBatchPDFProcessor:
    """Pruebas para BatchPDFProcessor"""

    def setup_method(self):
        """Configurar cada prueba"""
        self.batch_processor = BatchPDFProcessor()

    def test_max_files_validation(self):
        """Probar validación de máximo número de archivos"""
        # Crear más archivos de los permitidos
        files_data = [
            {"filename": f"test{i}.pdf", "content": b"content"}
            for i in range(6)  # Más de MAX_PDF_FILES (5)
        ]

        with pytest.raises(ValueError, match="Máximo .* archivos permitidos"):
            self.batch_processor.process_multiple_pdfs(files_data)

    @patch.object(PDFProcessor, "validate_pdf")
    @patch.object(PDFProcessor, "process_pdf")
    def test_process_multiple_pdfs_success(self, mock_process, mock_validate):
        """Probar procesamiento exitoso de múltiples PDFs"""
        # Configurar mocks
        mock_validate.return_value = True
        mock_process.return_value = {
            "filename": "test.pdf",
            "metadata": {"title": "Test", "num_pages": 1},
            "chunks": [Mock()],
            "num_chunks": 1,
            "text_length": 100,
        }

        files_data = [
            {"filename": "test1.pdf", "content": b"content1"},
            {"filename": "test2.pdf", "content": b"content2"},
        ]

        result = self.batch_processor.process_multiple_pdfs(files_data)

        assert result["total_files"] == 2
        assert len(result["files_processed"]) == 2
        assert "test1.pdf" in result["files_processed"]
        assert "test2.pdf" in result["files_processed"]

    @patch.object(PDFProcessor, "validate_pdf")
    def test_process_multiple_pdfs_invalid_file(self, mock_validate):
        """Probar manejo de archivos inválidos"""
        # Un archivo válido, uno inválido
        mock_validate.side_effect = [True, False]

        files_data = [
            {"filename": "valid.pdf", "content": b"valid_content"},
            {"filename": "invalid.pdf", "content": b"invalid_content"},
        ]

        # Patch process_pdf para el archivo válido
        with patch.object(PDFProcessor, "process_pdf") as mock_process:
            mock_process.return_value = {
                "filename": "valid.pdf",
                "metadata": {"title": "Valid", "num_pages": 1},
                "chunks": [Mock()],
                "num_chunks": 1,
                "text_length": 100,
            }

            result = self.batch_processor.process_multiple_pdfs(files_data)

            # Solo debe procesar el archivo válido
            assert result["total_files"] == 1
            assert result["files_processed"] == ["valid.pdf"]


if __name__ == "__main__":
    pytest.main([__file__])
