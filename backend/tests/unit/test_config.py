"""Unit tests for zaisaku.config — Settings loading and validation."""

from __future__ import annotations

import pytest

from zaisaku.config import Settings, get_settings


class TestSettingsDefaults:
    """Settings should load sensible defaults when no env vars are set."""

    def test_default_env_is_dev(self):
        s = Settings(env="dev")
        assert s.env == "dev"

    def test_default_chunk_size(self):
        s = Settings()
        assert s.chunk_size == 512

    def test_default_chunk_overlap(self):
        s = Settings()
        assert s.chunk_overlap == 64

    def test_default_retrieval_top_k(self):
        s = Settings()
        assert s.retrieval_top_k == 10

    def test_default_rerank_top_k(self):
        s = Settings()
        assert s.rerank_top_k == 3

    def test_default_app_port_is_int(self):
        s = Settings()
        assert isinstance(s.app_port, int)
        assert s.app_port == 5000

    def test_default_chroma_port_is_int(self):
        s = Settings()
        assert isinstance(s.chroma_port, int)
        assert s.chroma_port == 8000


class TestSettingsOverrides:
    """Environment variables should override defaults."""

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("ENV", "prod")
        s = Settings()
        assert s.env == "prod"

    def test_chunk_size_override(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("CHUNK_SIZE", "256")
        s = Settings()
        assert s.chunk_size == 256

    def test_chroma_port_override_type_coercion(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("CHROMA_PORT", "9999")
        s = Settings()
        assert s.chroma_port == 9999
        assert isinstance(s.chroma_port, int)

    def test_ollama_base_url_override(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://custom:11434")
        s = Settings()
        assert s.ollama_base_url == "http://custom:11434"

    def test_cors_origin_override(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("CORS_ORIGIN", "http://example.com")
        s = Settings()
        assert s.cors_origin == "http://example.com"


class TestSettingsFixture:
    """The test_settings fixture should provide test-friendly overrides."""

    def test_fixture_chunk_size(self, test_settings: Settings):
        assert test_settings.chunk_size == 128

    def test_fixture_chunk_overlap(self, test_settings: Settings):
        assert test_settings.chunk_overlap == 16

    def test_fixture_retrieval_top_k(self, test_settings: Settings):
        assert test_settings.retrieval_top_k == 5


class TestGetSettings:
    """get_settings() should return a cached singleton."""

    def test_returns_settings_instance(self):
        get_settings.cache_clear()
        s = get_settings()
        assert isinstance(s, Settings)

    def test_is_cached(self):
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
