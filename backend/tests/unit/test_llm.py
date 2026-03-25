"""Unit tests for zaisaku.generation.llm — LLM Router and Backends."""

from __future__ import annotations

import httpx
import pytest

from zaisaku.config import Settings
from zaisaku.generation.llm import LLMRouter, _OllamaBackend, _OpenRouterBackend


class TestLLMRouterSelection:
    """The router should select the correct backend based on ENV."""

    def test_routes_to_ollama_in_dev(self):
        settings = Settings(env="dev")
        router = LLMRouter(settings)
        assert isinstance(router.backend, _OllamaBackend)

    def test_routes_to_openrouter_in_prod(self):
        settings = Settings(env="prod")
        router = LLMRouter(settings)
        assert isinstance(router.backend, _OpenRouterBackend)

    def test_invalid_env_raises(self):
        settings = Settings(env="staging")
        with pytest.raises(ValueError, match="Unknown ENV: staging"):
            LLMRouter(settings)


class TestOllamaBackend:
    """Mocked tests for the Ollama backend."""

    def test_generate_success(self, respx_mock):
        settings = Settings(ollama_base_url="http://test:11434", ollama_model="test-model")
        backend = _OllamaBackend(settings)

        # Mock the Ollama /api/chat endpoint
        respx_mock.post("http://test:11434/api/chat").mock(
            return_value=httpx.Response(200, json={"message": {"content": '{"answer": "test"}'}})
        )

        res = backend.generate("Hello", "System")
        assert res["model"] == "test-model"
        assert res["env"] == "dev"
        assert res["text"] == '{"answer": "test"}'

    def test_generate_error(self, respx_mock):
        settings = Settings(ollama_base_url="http://test:11434", ollama_model="test-model")
        backend = _OllamaBackend(settings)

        respx_mock.post("http://test:11434/api/chat").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        with pytest.raises(RuntimeError, match="Ollama error"):
            backend.generate("Hello", "System")


class TestOpenRouterBackend:
    """Mocked tests for the OpenRouter backend."""

    def test_generate_success(self, monkeypatch):
        settings = Settings(openrouter_api_key="sk-test", openrouter_model="test-model")
        backend = _OpenRouterBackend(settings)

        # We mock openai.OpenAI.chat.completions.create
        class MockChoice:
            class MockMessage:
                content = '{"answer": "prod"}'
            message = MockMessage()

        class MockCompletion:
            choices = [MockChoice()]

        def mock_create(*args, **kwargs):
            return MockCompletion()

        monkeypatch.setattr(backend.client.chat.completions, "create", mock_create)

        res = backend.generate("Hello", "System")
        assert res["model"] == "test-model"
        assert res["env"] == "prod"
        assert res["text"] == '{"answer": "prod"}'

    def test_generate_error(self, monkeypatch):
        settings = Settings(openrouter_api_key="sk-test", openrouter_model="test-model")
        backend = _OpenRouterBackend(settings)

        def mock_create(*args, **kwargs):
            import openai
            raise openai.APIError("API Error", request=None, body=None)

        monkeypatch.setattr(backend.client.chat.completions, "create", mock_create)

        with pytest.raises(RuntimeError, match="OpenRouter error"):
            backend.generate("Hello", "System")
