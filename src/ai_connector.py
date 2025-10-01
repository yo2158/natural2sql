"""
AI connector module for Text-to-SQL generation.

This module provides connectors for different AI providers (Gemini, Ollama)
using the Strategy Pattern.
"""

from abc import ABC, abstractmethod
from typing import Dict
import google.generativeai as genai
import requests


class AIConnector(ABC):
    """
    Abstract base class for AI connectors.

    Defines the interface for AI model connectors using Strategy Pattern.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Generate AI response from prompt.

        Args:
            prompt: Input prompt for AI model

        Returns:
            Generated text response from AI model

        Raises:
            Exception: If AI generation fails
        """
        pass


class GeminiConnector(AIConnector):
    """Gemini API connector for Text-to-SQL generation."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash") -> None:
        """
        Initialize Gemini connector.

        Args:
            api_key: Gemini API key
            model_name: Model name (default: gemini-2.5-flash)
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str) -> str:
        """
        Generate SQL from prompt using Gemini API.

        Args:
            prompt: Input prompt for SQL generation

        Returns:
            Generated SQL or ERROR response

        Raises:
            Exception: If API call fails or times out
        """
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.0,
                    "max_output_tokens": 2048,
                },
                request_options={"timeout": 120},
            )
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")


class OllamaConnector(AIConnector):
    """Ollama API connector for Text-to-SQL generation."""

    def __init__(self, host: str, model: str) -> None:
        """
        Initialize Ollama connector.

        Args:
            host: Ollama server URL (e.g., http://localhost:11434)
            model: Model name (e.g., gemma3:12b)
        """
        self.endpoint = f"{host}/api/generate"
        self.model = model

    def generate(self, prompt: str) -> str:
        """
        Generate SQL from prompt using Ollama API.

        Args:
            prompt: Input prompt for SQL generation

        Returns:
            Generated SQL or ERROR response

        Raises:
            Exception: If API call fails or times out
        """
        try:
            response = requests.post(
                self.endpoint,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0, "num_predict": 2048},
                },
                timeout=120,
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")


def create_ai_connector(provider: str, **kwargs) -> AIConnector:
    """
    Factory function to create AI connector.

    Args:
        provider: Provider name ('gemini' or 'ollama')
        **kwargs: Provider-specific parameters
            - For Gemini: api_key (required), model (optional)
            - For Ollama: host (required), model (required)

    Returns:
        AIConnector instance

    Raises:
        ValueError: If provider is not supported

    Example:
        >>> connector = create_ai_connector('gemini', api_key='YOUR_KEY')
        >>> connector = create_ai_connector('ollama', host='http://localhost:11434', model='gemma3:12b')
    """
    if provider == "gemini":
        return GeminiConnector(
            kwargs["api_key"], kwargs.get("model", "gemini-2.5-flash")
        )
    elif provider == "ollama":
        return OllamaConnector(kwargs["host"], kwargs["model"])
    else:
        raise ValueError(f"未対応のプロバイダ: {provider}")
