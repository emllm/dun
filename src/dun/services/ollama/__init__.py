"""Ollama service for interacting with LLM models."""
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import requests
from pydantic import BaseModel, Field

from dun.core.protocols import ServiceProtocol
from dun.config.settings import get_settings

logger = logging.getLogger(__name__)


class OllamaResponse(BaseModel):
    """Response from Ollama API."""
    model: str
    created_at: str
    response: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


class OllamaModelInfo(BaseModel):
    """Information about an Ollama model."""
    name: str
    model: str
    size: int
    digest: str
    details: Dict[str, Any]


class OllamaService(ServiceProtocol):
    """Service for interacting with Ollama API."""
    
    def __init__(self):
        self.settings = get_settings()
        self._client = None
        self._models: Dict[str, OllamaModelInfo] = {}
    
    @property
    def name(self) -> str:
        return "ollama"
    
    @property
    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        if not self.settings.OLLAMA_ENABLED:
            return False
        
        try:
            self._check_connection()
            return True
        except Exception as e:
            logger.warning(f"Ollama service is not available: {e}")
            return False
    
    async def initialize(self) -> None:
        """Initialize the Ollama service."""
        if not self.settings.OLLAMA_ENABLED:
            logger.info("Ollama integration is disabled in settings")
            return
        
        try:
            self._check_connection()
            await self._load_models()
            logger.info(f"Ollama service initialized with {len(self._models)} models")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama service: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Clean up resources."""
        self._models.clear()
    
    def _get_client(self):
        """Get the Ollama client, initializing it if necessary."""
        if self._client is None:
            try:
                import ollama
                self._client = ollama.Client(host=self.settings.OLLAMA_BASE_URL)
            except ImportError:
                raise RuntimeError("Ollama Python package is not installed. Install with: pip install ollama")
        return self._client
    
    def _check_connection(self) -> bool:
        """Check if we can connect to the Ollama server."""
        try:
            response = requests.get(f"{self.settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to connect to Ollama server at {self.settings.OLLAMA_BASE_URL}: {e}")
    
    async def _load_models(self) -> None:
        """Load available models from Ollama."""
        try:
            client = self._get_client()
            response = client.list()
            
            self._models.clear()
            for model_data in response.get('models', []):
                model = OllamaModelInfo(
                    name=model_data.get('name', ''),
                    model=model_data.get('model', ''),
                    size=model_data.get('size', 0),
                    digest=model_data.get('digest', ''),
                    details=model_data.get('details', {})
                )
                self._models[model.name] = model
                
        except Exception as e:
            logger.error(f"Failed to load Ollama models: {e}")
            raise
    
    async def list_models(self) -> List[OllamaModelInfo]:
        """List all available models."""
        if not self._models:
            await self._load_models()
        return list(self._models.values())
    
    async def has_model(self, model_name: str) -> bool:
        """Check if a model is available."""
        if not self._models:
            await self._load_models()
        return model_name in self._models
    
    async def generate(
        self,
        prompt: str,
        model: str = "llama2",
        system: Optional[str] = None,
        format: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> Union[OllamaResponse, str]:
        """Generate text using the specified model.
        
        Args:
            prompt: The input prompt
            model: The model to use (default: "llama2")
            system: System message to set the behavior of the model
            format: Format to return the response in (e.g., "json")
            options: Additional model options (temperature, top_p, etc.)
            stream: Whether to stream the response
            
        Returns:
            OllamaResponse if stream=False, otherwise a generator of response chunks
        """
        if not self.settings.OLLAMA_ENABLED:
            raise RuntimeError("Ollama integration is disabled in settings")
        
        client = self._get_client()
        
        try:
            response = client.generate(
                model=model,
                prompt=prompt,
                system=system,
                format=format,
                options=options or {},
                stream=stream
            )
            
            if stream:
                return self._stream_response(response)
            else:
                return OllamaResponse(**response)
                
        except Exception as e:
            logger.error(f"Error generating text with Ollama: {e}")
            raise
    
    def _stream_response(self, response_stream):
        """Handle streaming response from Ollama."""
        for chunk in response_stream:
            if chunk.get('done', False):
                break
            yield chunk.get('response', '')
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama2",
        format: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> Union[Dict[str, Any], str]:
        """Chat with the model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: The model to use (default: "llama2")
            format: Format to return the response in (e.g., "json")
            options: Additional model options
            stream: Whether to stream the response
            
        Returns:
            Dict with the response or a generator if streaming
        """
        if not self.settings.OLLAMA_ENABLED:
            raise RuntimeError("Ollama integration is disabled in settings")
        
        client = self._get_client()
        
        try:
            response = client.chat(
                model=model,
                messages=messages,
                format=format,
                options=options or {},
                stream=stream
            )
            
            if stream:
                return self._stream_response(response)
            return response
            
        except Exception as e:
            logger.error(f"Error in Ollama chat: {e}")
            raise
    
    async def embeddings(
        self,
        prompt: str,
        model: str = "llama2",
        options: Optional[Dict[str, Any]] = None,
    ) -> List[float]:
        """Get embeddings for a prompt."""
        if not self.settings.OLLAMA_ENABLED:
            raise RuntimeError("Ollama integration is disabled in settings")
        
        client = self._get_client()
        
        try:
            response = client.embeddings(
                model=model,
                prompt=prompt,
                options=options or {}
            )
            return response.get('embedding', [])
            
        except Exception as e:
            logger.error(f"Error getting embeddings from Ollama: {e}")
            raise


# Global Ollama service instance
ollama_service = OllamaService()
