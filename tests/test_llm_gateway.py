"""
LLM Gateway v2 — verification tests (multi-provider routing, crypto vault).
"""

import pytest

from app.core.crypto_vault import decrypt, encrypt, mask
from app.core.llm_gateway_v2 import LLMGatewayError, chat
from app.core.llm_gateway_v2 import test_connection as gw_test_connection


class FakeProvider:
    def __init__(self, provider_type="openai", base_url="http://localhost:9/v1",
                 model="test-model", api_key="sk-test", temperature=0.3):
        self.provider_type = provider_type
        self.base_url = base_url
        self.model = model
        self.api_key_encrypted = encrypt(api_key)
        self.temperature = temperature
        self.enabled = True
        self.embedding_model = ""


def test_crypto_vault_roundtrip():
    secret = "sk-live-abc123"
    encrypted = encrypt(secret)
    assert encrypted != secret
    assert decrypt(encrypted) == secret


def test_crypto_vault_empty_and_garbage():
    assert encrypt("") == ""
    assert decrypt("") == ""
    assert decrypt("garbage-not-encrypted") == ""


def test_mask_hides_secret():
    masked = mask("sk-live-abc123")
    assert masked.startswith("sk-l")
    assert "abc123" not in masked


def test_unsupported_provider_type_rejected():
    provider = FakeProvider(provider_type="mystery")
    with pytest.raises(LLMGatewayError):
        chat(provider, [{"role": "user", "content": "hi"}])


def test_chat_openai_compatible_payload_shape(monkeypatch):
    """Verify the OpenAI-compatible adapter builds the right request."""
    captured = {}

    def fake_http(method, url, headers, payload=None, timeout=120):
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = headers
        return 200, {
            "choices": [{"message": {"content": "hello"}}],
            "model": "test-model",
            "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
        }

    import app.core.llm_gateway_v2 as gw
    monkeypatch.setattr(gw, "_http_json", fake_http)

    provider = FakeProvider(provider_type="ollama", base_url="http://localhost:11434/v1")
    result = chat(provider, [
        {"role": "system", "content": "be brief"},
        {"role": "user", "content": "hello"},
    ], temperature=0.2)

    assert result["content"] == "hello"
    assert result["usage"]["total_tokens"] == 5
    assert captured["url"] == "http://localhost:11434/v1/chat/completions"
    assert captured["payload"]["temperature"] == 0.2
    assert captured["headers"]["Authorization"] == "Bearer sk-test"


def test_chat_anthropic_payload_shape(monkeypatch):
    captured = {}

    def fake_http(method, url, headers, payload=None, timeout=120):
        captured["url"] = url
        captured["payload"] = payload
        return 200, {
            "content": [{"text": "bonjour"}],
            "model": "claude-test",
            "usage": {"input_tokens": 4, "output_tokens": 3},
        }

    import app.core.llm_gateway_v2 as gw
    monkeypatch.setattr(gw, "_http_json", fake_http)

    provider = FakeProvider(provider_type="anthropic", base_url="https://api.anthropic.com")
    result = chat(provider, [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hi"},
    ])

    assert result["content"] == "bonjour"
    assert captured["url"].endswith("/v1/messages")
    assert captured["payload"]["system"] == "sys"
    assert captured["payload"]["messages"] == [{"role": "user", "content": "hi"}]


def test_chat_gemini_maps_roles(monkeypatch):
    captured = {}

    def fake_http(method, url, headers, payload=None, timeout=120):
        captured["payload"] = payload
        return 200, {
            "candidates": [{"content": {"parts": [{"text": "salam"}]}}],
            "usageMetadata": {"totalTokenCount": 7},
        }

    import app.core.llm_gateway_v2 as gw
    monkeypatch.setattr(gw, "_http_json", fake_http)

    provider = FakeProvider(provider_type="google", base_url="https://generativelanguage.googleapis.com")
    result = chat(provider, [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hi"},
    ])

    assert result["content"] == "salam"
    assert captured["payload"]["contents"][0]["role"] == "user"
    assert captured["payload"]["systemInstruction"]["parts"][0]["text"] == "sys"


def test_chat_error_propagates(monkeypatch):
    def fake_http(method, url, headers, payload=None, timeout=120):
        return 500, {"error": "provider exploded"}

    import app.core.llm_gateway_v2 as gw
    monkeypatch.setattr(gw, "_http_json", fake_http)

    provider = FakeProvider(provider_type="openai")
    with pytest.raises(LLMGatewayError):
        chat(provider, [{"role": "user", "content": "hi"}])


def test_test_connection_handles_down_provider():
    provider = FakeProvider(provider_type="ollama", base_url="http://localhost:9/v1")
    result = gw_test_connection(provider)
    assert result["ok"] is False
    assert "error" in result