"""Unit tests for zaisaku.generation.llm — LLM Router and Backends."""

from __future__ import annotations

import httpx
import pytest

from zaisaku.config import Settings
from zaisaku.generation.llm import LLMRouter, _OllamaBackend, _OmniRouteBackend, _OpenRouterBackend


class TestLLMRouterSelection:
    """The router should select the correct backend based on ENV and LLM_PROVIDER."""

    def test_routes_to_ollama_in_dev(self):
        settings = Settings(env="dev", llm_provider="")
        router = LLMRouter(settings)
        assert isinstance(router.backend, _OllamaBackend)

    def test_routes_to_openrouter_in_prod(self):
        settings = Settings(env="prod", llm_provider="")
        router = LLMRouter(settings)
        assert isinstance(router.backend, _OpenRouterBackend)

    def test_routes_to_omniroute_via_provider(self):
        settings = Settings(llm_provider="omniroute")
        router = LLMRouter(settings)
        assert isinstance(router.backend, _OmniRouteBackend)

    def test_routes_to_omniroute_via_env(self):
        settings = Settings(env="omniroute", llm_provider="")
        router = LLMRouter(settings)
        assert isinstance(router.backend, _OmniRouteBackend)

    def test_invalid_env_raises(self):
        settings = Settings(env="staging", llm_provider="")
        with pytest.raises(ValueError, match="Unknown LLM provider.*staging"):
            LLMRouter(settings)


class TestOllamaBackend:
    """Mocked tests for the Ollama backend."""

    def test_generate_success(self, monkeypatch):
        settings = Settings(ollama_base_url="http://test:11434", ollama_model="test-model")
        backend = _OllamaBackend(settings)

        class MockResponse:
            def __init__(self, json_data, status_code=200):
                self._json = json_data
                self.status_code = status_code
            def json(self):
                return self._json
            def raise_for_status(self):
                pass

        def mock_post(*args, **kwargs):
            return MockResponse({"message": {"content": '{"answer": "test"}'}})

        monkeypatch.setattr("httpx.post", mock_post)

        res = backend.generate("Hello", "System")
        assert res["model"] == "test-model"
        assert res["env"] == "dev"
        assert res["text"] == '{"answer": "test"}'

    def test_generate_error(self, monkeypatch):
        settings = Settings(ollama_base_url="http://test:11434", ollama_model="test-model")
        backend = _OllamaBackend(settings)

        def mock_post(*args, **kwargs):
            raise httpx.RequestError("Mocked error")

        monkeypatch.setattr("httpx.post", mock_post)

        with pytest.raises(RuntimeError, match="Ollama error"):
            backend.generate("Hello", "System")

    def test_generate_stream_success(self, monkeypatch):
        settings = Settings(ollama_base_url="http://test:11434", ollama_model="test-model")
        backend = _OllamaBackend(settings)

        class MockStreamResponse:
            def raise_for_status(self):
                pass
            def iter_lines(self):
                yield '{"message": {"content": "chunk 1 "}}'
                yield '{"message": {"content": "chunk 2"}}'
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass

        def mock_stream(*args, **kwargs):
            return MockStreamResponse()

        monkeypatch.setattr("httpx.stream", mock_stream)
        tokens = list(backend.generate_stream("Hello", "System"))
        assert tokens == ["chunk 1 ", "chunk 2"]


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

    def test_generate_stream_success(self, monkeypatch):
        settings = Settings(openrouter_api_key="sk-test", openrouter_model="test-model")
        backend = _OpenRouterBackend(settings)

        class MockChunk:
            def __init__(self, text):
                class MockChoice:
                    class MockDelta:
                        def __init__(self, c): self.content = c
                    def __init__(self, c): self.delta = MockChoice.MockDelta(c)
                self.choices = [MockChoice(text)]

        def mock_create(*args, **kwargs):
            return [MockChunk("OpenRouter "), MockChunk("stream!")]

        monkeypatch.setattr(backend.client.chat.completions, "create", mock_create)
        tokens = list(backend.generate_stream("Hello", "System"))
        assert tokens == ["OpenRouter ", "stream!"]


class TestOmniRouteBackend:
    """Mocked tests for the OmniRoute backend."""

    def test_generate_success(self, monkeypatch):
        settings = Settings(omniroute_base_url="http://localhost:20128/v1", omniroute_model="auto")
        backend = _OmniRouteBackend(settings)

        class MockChoice:
            class MockMessage:
                content = '{"answer": "omniroute"}'
            message = MockMessage()

        class MockCompletion:
            choices = [MockChoice()]

        def mock_create(*args, **kwargs):
            return MockCompletion()

        monkeypatch.setattr(backend.client.chat.completions, "create", mock_create)

        res = backend.generate("Hello", "System")
        assert res["model"] == "auto"
        assert res["env"] == "omniroute"
        assert res["text"] == '{"answer": "omniroute"}'

    def test_generate_stream_success(self, monkeypatch):
        settings = Settings(omniroute_base_url="http://localhost:20128/v1", omniroute_model="auto")
        backend = _OmniRouteBackend(settings)

        class MockChunk:
            def __init__(self, text):
                class MockChoice:
                    class MockDelta:
                        def __init__(self, c): self.content = c
                    def __init__(self, c): self.delta = MockChoice.MockDelta(c)
                self.choices = [MockChoice(text)]

        def mock_create(*args, **kwargs):
            return [MockChunk("OmniRoute "), MockChunk("response")]

        monkeypatch.setattr(backend.client.chat.completions, "create", mock_create)
        tokens = list(backend.generate_stream("Hello", "System"))
        assert tokens == ["OmniRoute ", "response"]

    def test_generate_error(self, monkeypatch):
        settings = Settings(omniroute_base_url="http://localhost:20128/v1", omniroute_model="auto")
        backend = _OmniRouteBackend(settings)

        def mock_create(*args, **kwargs):
            import openai
            raise openai.APIError("Connection refused", request=None, body=None)

        monkeypatch.setattr(backend.client.chat.completions, "create", mock_create)

        with pytest.raises(RuntimeError, match="OmniRoute error"):
            backend.generate("Hello", "System")
