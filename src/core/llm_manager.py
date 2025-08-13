"""
Gestor de LLMs múltiples con soporte para OpenAI, Ollama y HuggingFace
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

try:
    from langchain_openai import ChatOpenAI
    from langchain_community.llms import Ollama
    from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
except ImportError:
    # Fallback si LangChain no está disponible
    logging.warning("LangChain no disponible, usando implementación básica")

from .config import settings

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Clase base para proveedores de LLM"""

    @abstractmethod
    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generar respuesta del LLM"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Verificar si el proveedor está disponible"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """Proveedor OpenAI"""

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Inicializar cliente OpenAI"""
        try:
            import openai

            openai.api_key = self.api_key
            self.client = openai
            logger.info("Cliente OpenAI inicializado")
        except ImportError:
            logger.error("OpenAI no está instalado")
        except Exception as e:
            logger.error(f"Error inicializando OpenAI: {e}")

    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generar respuesta usando OpenAI"""
        if not self.client:
            return "Error: Cliente OpenAI no disponible"

        try:
            full_prompt = (
                f"Contexto: {context}\n\nPregunta: {prompt}" if context else prompt
            )

            response = self.client.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente experto en análisis de documentos PDF. Proporciona respuestas precisas y contextuales.",
                    },
                    {"role": "user", "content": full_prompt},
                ],
                max_tokens=1000,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generando respuesta OpenAI: {e}")
            return f"Error generando respuesta: {str(e)}"

    def is_available(self) -> bool:
        """Verificar disponibilidad OpenAI"""
        return self.client is not None and self.api_key is not None


class OllamaProvider(BaseLLMProvider):
    """Proveedor Ollama para modelos locales"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Inicializar cliente Ollama"""
        try:
            import requests

            # Verificar que Ollama esté corriendo
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.client = requests
                logger.info("Cliente Ollama inicializado")
            else:
                logger.error("Ollama no está corriendo")
        except ImportError:
            logger.error("Requests no está disponible")
        except Exception as e:
            logger.error(f"Error conectando con Ollama: {e}")

    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generar respuesta usando Ollama"""
        if not self.client:
            return "Error: Ollama no está disponible"

        try:
            full_prompt = (
                f"Contexto: {context}\n\nPregunta: {prompt}" if context else prompt
            )

            payload = {"model": self.model, "prompt": full_prompt, "stream": False}

            response = self.client.post(
                f"{self.base_url}/api/generate", json=payload, timeout=30
            )

            if response.status_code == 200:
                return response.json()["response"]
            else:
                return f"Error: {response.status_code}"

        except Exception as e:
            logger.error(f"Error generando respuesta Ollama: {e}")
            return f"Error generando respuesta: {str(e)}"

    def is_available(self) -> bool:
        """Verificar disponibilidad Ollama"""
        return self.client is not None


class HuggingFaceProvider(BaseLLMProvider):
    """Proveedor HuggingFace"""

    def __init__(self, api_token: str, model: str = "microsoft/DialoGPT-medium"):
        self.api_token = api_token
        self.model = model
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Inicializar cliente HuggingFace"""
        try:
            from transformers import pipeline
            import torch

            # Verificar token
            if not self.api_token or not self.api_token.strip():
                logger.warning("Token de HuggingFace no configurado")
                return

            # Usar GPU si está disponible
            device = 0 if torch.cuda.is_available() else -1

            self.client = pipeline(
                "text-generation", model=self.model, device=device, token=self.api_token
            )
            logger.info("Cliente HuggingFace inicializado")
        except ImportError:
            logger.error("Transformers no está disponible")
        except Exception as e:
            logger.error(f"Error inicializando HuggingFace: {e}")
            self.client = None

    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generar respuesta usando HuggingFace"""
        if not self.client:
            return "Error: HuggingFace no está disponible"

        try:
            full_prompt = (
                f"Contexto: {context}\n\nPregunta: {prompt}" if context else prompt
            )

            response = self.client(
                full_prompt,
                max_length=500,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
            )

            return response[0]["generated_text"][len(full_prompt) :].strip()
        except Exception as e:
            logger.error(f"Error generando respuesta HuggingFace: {e}")
            return f"Error generando respuesta: {str(e)}"

    def is_available(self) -> bool:
        """Verificar disponibilidad HuggingFace"""
        return self.client is not None


class LLMManager:
    """Gestor de múltiples proveedores LLM"""

    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.active_provider: Optional[str] = None
        self._initialize_providers()

    def _initialize_providers(self):
        """Inicializar proveedores disponibles"""
        # OpenAI
        if settings.OPENAI_API_KEY:
            self.providers["openai"] = OpenAIProvider(
                settings.OPENAI_API_KEY, settings.OPENAI_MODEL
            )

        # Ollama
        self.providers["ollama"] = OllamaProvider(
            settings.OLLAMA_BASE_URL, settings.OLLAMA_MODEL
        )

        # HuggingFace - solo si hay token válido
        hf_token = settings.HUGGINGFACE_API_TOKEN
        if hf_token and hf_token.strip() and hf_token != "None":
            try:
                self.providers["huggingface"] = HuggingFaceProvider(
                    hf_token, settings.HF_MODEL
                )
                logger.info("HuggingFace provider inicializado correctamente")
            except Exception as e:
                logger.warning(f"No se pudo inicializar HuggingFace: {e}")
        else:
            logger.info("HuggingFace deshabilitado - no hay token configurado")

        # Configurar proveedor activo
        self.set_active_provider(settings.LLM_PROVIDER)

    def set_active_provider(self, provider_name: str) -> bool:
        """Cambiar proveedor activo"""
        if (
            provider_name in self.providers
            and self.providers[provider_name].is_available()
        ):
            self.active_provider = provider_name
            logger.info(f"Proveedor activo: {provider_name}")
            return True
        else:
            logger.error(f"Proveedor no disponible: {provider_name}")
            return False

    def get_available_providers(self) -> List[str]:
        """Obtener lista de proveedores disponibles"""
        return [
            name for name, provider in self.providers.items() if provider.is_available()
        ]

    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generar respuesta usando el proveedor activo"""
        if not self.active_provider or self.active_provider not in self.providers:
            return "Error: No hay proveedor LLM activo"

        provider = self.providers[self.active_provider]
        return provider.generate_response(prompt, context)

    def get_provider_status(self) -> Dict[str, Any]:
        """Obtener estado de todos los proveedores"""
        return {
            "active_provider": self.active_provider,
            "available_providers": self.get_available_providers(),
            "provider_status": {
                name: provider.is_available()
                for name, provider in self.providers.items()
            },
        }


# Instancia global del gestor
llm_manager = LLMManager()
