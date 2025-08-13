"""
Pruebas unitarias para LLM Manager
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Añadir src al path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from core.llm_manager import (
    LLMManager,
    OpenAIProvider,
    OllamaProvider,
    HuggingFaceProvider,
)


class TestOpenAIProvider:
    """Pruebas para OpenAIProvider"""

    def setup_method(self):
        """Configurar cada prueba"""
        self.provider = OpenAIProvider("test_api_key", "gpt-3.5-turbo")

    @patch("core.llm_manager.openai")
    def test_initialize_client_success(self, mock_openai):
        """Probar inicialización exitosa del cliente"""
        provider = OpenAIProvider("valid_key", "gpt-3.5-turbo")
        assert provider.api_key == "valid_key"
        assert provider.model == "gpt-3.5-turbo"

    def test_is_available_with_client(self):
        """Probar disponibilidad con cliente válido"""
        self.provider.client = Mock()
        assert self.provider.is_available() is True

    def test_is_available_without_client(self):
        """Probar disponibilidad sin cliente"""
        self.provider.client = None
        assert self.provider.is_available() is False

    @patch("core.llm_manager.openai")
    def test_generate_response_success(self, mock_openai):
        """Probar generación exitosa de respuesta"""
        # Configurar mock
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"

        mock_openai.ChatCompletion.create.return_value = mock_response
        self.provider.client = mock_openai

        result = self.provider.generate_response("Test prompt")

        assert result == "Test response"

    def test_generate_response_no_client(self):
        """Probar generación de respuesta sin cliente"""
        self.provider.client = None

        result = self.provider.generate_response("Test prompt")

        assert "Error: Cliente OpenAI no disponible" in result


class TestOllamaProvider:
    """Pruebas para OllamaProvider"""

    def setup_method(self):
        """Configurar cada prueba"""
        self.provider = OllamaProvider("http://localhost:11434", "llama2")

    @patch("core.llm_manager.requests")
    def test_initialize_client_success(self, mock_requests):
        """Probar inicialización exitosa del cliente"""
        # Mock respuesta exitosa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        provider = OllamaProvider("http://localhost:11434", "llama2")
        assert provider.base_url == "http://localhost:11434"
        assert provider.model == "llama2"

    @patch("core.llm_manager.requests")
    def test_generate_response_success(self, mock_requests):
        """Probar generación exitosa de respuesta"""
        # Configurar mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Ollama test response"}

        mock_requests.post.return_value = mock_response
        self.provider.client = mock_requests

        result = self.provider.generate_response("Test prompt")

        assert result == "Ollama test response"

    def test_generate_response_no_client(self):
        """Probar generación de respuesta sin cliente"""
        self.provider.client = None

        result = self.provider.generate_response("Test prompt")

        assert "Error: Ollama no está disponible" in result


class TestHuggingFaceProvider:
    """Pruebas para HuggingFaceProvider"""

    def setup_method(self):
        """Configurar cada prueba"""
        self.provider = HuggingFaceProvider("test_token", "test_model")

    @patch("core.llm_manager.pipeline")
    @patch("core.llm_manager.torch")
    def test_initialize_client_success(self, mock_torch, mock_pipeline):
        """Probar inicialización exitosa del cliente"""
        mock_torch.cuda.is_available.return_value = False
        mock_pipeline.return_value = Mock()

        provider = HuggingFaceProvider("valid_token", "test_model")
        assert provider.api_token == "valid_token"
        assert provider.model == "test_model"

    def test_generate_response_success(self):
        """Probar generación exitosa de respuesta"""
        # Mock del pipeline
        mock_pipeline = Mock()
        mock_pipeline.return_value = [{"generated_text": "Original prompt HF response"}]

        self.provider.client = mock_pipeline

        result = self.provider.generate_response("Original prompt")

        assert result == " HF response"  # Texto después del prompt original


class TestLLMManager:
    """Pruebas para LLMManager"""

    def setup_method(self):
        """Configurar cada prueba"""
        self.manager = LLMManager()

    @patch("core.llm_manager.settings")
    def test_initialization_with_config(self, mock_settings):
        """Probar inicialización con configuración"""
        mock_settings.OPENAI_API_KEY = "test_key"
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_settings.OLLAMA_MODEL = "llama2"
        mock_settings.HUGGINGFACE_API_TOKEN = "hf_token"
        mock_settings.LLM_PROVIDER = "ollama"

        # Reinicializar manager
        manager = LLMManager()

        # Verificar que se inicializaron los proveedores esperados
        assert len(manager.providers) >= 1  # Al menos Ollama debería estar

    def test_set_active_provider_valid(self):
        """Probar cambio a proveedor válido"""
        # Mock de proveedor disponible
        mock_provider = Mock()
        mock_provider.is_available.return_value = True

        self.manager.providers["test_provider"] = mock_provider

        result = self.manager.set_active_provider("test_provider")

        assert result is True
        assert self.manager.active_provider == "test_provider"

    def test_set_active_provider_invalid(self):
        """Probar cambio a proveedor inválido"""
        result = self.manager.set_active_provider("nonexistent_provider")

        assert result is False

    def test_get_available_providers(self):
        """Probar obtención de proveedores disponibles"""
        # Mock de proveedores
        mock_provider1 = Mock()
        mock_provider1.is_available.return_value = True

        mock_provider2 = Mock()
        mock_provider2.is_available.return_value = False

        self.manager.providers = {
            "available": mock_provider1,
            "unavailable": mock_provider2,
        }

        available = self.manager.get_available_providers()

        assert "available" in available
        assert "unavailable" not in available

    def test_generate_response_no_active_provider(self):
        """Probar generación de respuesta sin proveedor activo"""
        self.manager.active_provider = None

        result = self.manager.generate_response("Test prompt")

        assert "Error: No hay proveedor LLM activo" in result

    def test_generate_response_with_provider(self):
        """Probar generación de respuesta con proveedor activo"""
        # Mock de proveedor
        mock_provider = Mock()
        mock_provider.generate_response.return_value = "Provider response"

        self.manager.providers["test"] = mock_provider
        self.manager.active_provider = "test"

        result = self.manager.generate_response("Test prompt", "Test context")

        assert result == "Provider response"
        mock_provider.generate_response.assert_called_once_with(
            "Test prompt", "Test context"
        )

    def test_get_provider_status(self):
        """Probar obtención de estado de proveedores"""
        # Mock de proveedores
        mock_provider1 = Mock()
        mock_provider1.is_available.return_value = True

        mock_provider2 = Mock()
        mock_provider2.is_available.return_value = False

        self.manager.providers = {
            "provider1": mock_provider1,
            "provider2": mock_provider2,
        }
        self.manager.active_provider = "provider1"

        status = self.manager.get_provider_status()

        assert status["active_provider"] == "provider1"
        assert "provider1" in status["available_providers"]
        assert "provider2" not in status["available_providers"]
        assert status["provider_status"]["provider1"] is True
        assert status["provider_status"]["provider2"] is False


if __name__ == "__main__":
    pytest.main([__file__])
