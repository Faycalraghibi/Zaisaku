"""LLM Generation module.

Provides a Protocol for swappability, with Ollama (dev) and OpenRouter (prod) backends,
and a Router to select between them based on configuration.
"""

from __future__ import annotations

import json
import logging
from typing import Protocol, runtime_checkable

import httpx

from zaisaku.config import Settings

logger = logging.getLogger(__name__)


@runtime_checkable
class LLMBackend(Protocol):
    """Interface for LLM generation backends."""

    def generate(self, prompt: str, system_prompt: str) -> dict:
        """Generate a response from the LLM.

        Args:
            prompt: The user query + context.
            system_prompt: System-level instructions for the LLM.

        Returns:
            A dict containing:
                - "text" (str): The raw text output from the LLM.
                - "model" (str): The model identifier used.
                - "env" (str): The environment identifier (e.g. "dev", "prod").
        """
        ...


class _OllamaBackend:
    """Local LLM backend using the Ollama REST API."""

    def __init__(self, config: Settings) -> None:
        self.base_url = config.ollama_base_url
        self.model = config.ollama_model

    def generate(self, prompt: str, system_prompt: str) -> dict:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            # Force JSON format output (if supported by the specific Ollama model)
            "format": "json",
        }

        try:
            r = httpx.post(url, json=payload, timeout=60.0)
            r.raise_for_status()
            data = r.json()
            # Handle standard Ollama payload return
            text = data.get("message", {}).get("content", "")
            return {
                "text": text,
                "model": self.model,
                "env": "dev",
            }
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise RuntimeError(f"Ollama error: {e}") from e


class _OpenRouterBackend:
    """Cloud LLM backend using OpenRouter via the OpenAI SDK."""

    def __init__(self, config: Settings) -> None:
        self.api_key = config.openrouter_api_key
        self.model = config.openrouter_model
        
        # We lazy import openai to avoid hard dependency if running strictly locally
        import openai
        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

    def generate(self, prompt: str, system_prompt: str) -> dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                # response_format={"type": "json_object"} is supported by many OpenRouter models
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content or ""
            return {
                "text": text,
                "model": self.model,
                "env": "prod",
            }
        except Exception as e:
            logger.error(f"OpenRouter generation failed: {e}")
            raise RuntimeError(f"OpenRouter error: {e}") from e


class LLMRouter:
    """Facade that delegates to the appropriate LLMBackend based on configuration."""

    def __init__(self, config: Settings) -> None:
        if config.env == "dev":
            self.backend: LLMBackend = _OllamaBackend(config)
        elif config.env == "prod":
            self.backend: LLMBackend = _OpenRouterBackend(config)
        else:
            raise ValueError(f"Unknown ENV: {config.env}")

    def generate(self, prompt: str, system_prompt: str) -> dict:
        return self.backend.generate(prompt, system_prompt)
