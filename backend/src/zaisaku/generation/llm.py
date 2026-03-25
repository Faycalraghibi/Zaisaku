

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

import httpx

from zaisaku.config import Settings

logger = logging.getLogger(__name__)


@runtime_checkable
class LLMBackend(Protocol):
class LLMBackend(Protocol):
    def generate(self, prompt: str, system_prompt: str) -> dict:
        ...


class _OllamaBackend:
class _OllamaBackend:

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
            data = r.json()
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
class _OpenRouterBackend:

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
class LLMRouter:

    def __init__(self, config: Settings) -> None:
        if config.env == "dev":
            self.backend: LLMBackend = _OllamaBackend(config)
        elif config.env == "prod":
            self.backend: LLMBackend = _OpenRouterBackend(config)
        else:
            raise ValueError(f"Unknown ENV: {config.env}")

    def generate(self, prompt: str, system_prompt: str) -> dict:
        return self.backend.generate(prompt, system_prompt)
