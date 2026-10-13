

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from typing import Protocol, runtime_checkable

import httpx

from zaisaku.config import Settings

logger = logging.getLogger(__name__)


@runtime_checkable
class LLMBackend(Protocol):
    def generate(self, prompt: str, system_prompt: str) -> dict:
        ...

    def generate_stream(self, prompt: str, system_prompt: str) -> Iterator[str]:
        ...


class _OllamaBackend:

    def __init__(self, config: Settings) -> None:
        self.base_url = config.ollama_base_url
        self.model = config.ollama_model
        self.timeout = config.llm_timeout
        self.env = "dev"

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
            r = httpx.post(url, json=payload, timeout=self.timeout)
            r.raise_for_status()
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

    def generate_stream(self, prompt: str, system_prompt: str) -> Iterator[str]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": True,
        }

        try:
            with httpx.stream("POST", url, json=payload, timeout=self.timeout) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            raise RuntimeError(f"Ollama error: {e}") from e


class _OpenRouterBackend:

    def __init__(self, config: Settings) -> None:
        self.api_key = config.openrouter_api_key
        self.model = config.openrouter_model
        self.base_url = config.openrouter_base_url
        self.timeout = config.llm_timeout
        self.env = "prod"
        
        # We lazy import openai to avoid hard dependency if running strictly locally
        import openai
        self.client = openai.OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
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

    def generate_stream(self, prompt: str, system_prompt: str) -> Iterator[str]:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                stream=True,
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenRouter streaming failed: {e}")
            raise RuntimeError(f"OpenRouter error: {e}") from e


class LLMRouter:

    def __init__(self, config: Settings) -> None:
        if config.env == "dev":
            self.backend: LLMBackend = _OllamaBackend(config)
        elif config.env == "prod":
            self.backend: LLMBackend = _OpenRouterBackend(config)
        else:
            raise ValueError(f"Unknown ENV: {config.env}")

    @property
    def env(self) -> str:
        return getattr(self.backend, "env", "unknown")

    @property
    def model(self) -> str:
        return getattr(self.backend, "model", "unknown")

    def generate(self, prompt: str, system_prompt: str) -> dict:
        return self.backend.generate(prompt, system_prompt)

    def generate_stream(self, prompt: str, system_prompt: str) -> Iterator[str]:
        if hasattr(self.backend, "generate_stream"):
            yield from self.backend.generate_stream(prompt, system_prompt)
        else:
            res = self.backend.generate(prompt, system_prompt)
            text = res.get("text", "")
            if text:
                yield text
