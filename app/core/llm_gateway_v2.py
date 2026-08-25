"""
LLM Gateway v2 — dynamic multi-provider routing.

Supported providers:
  - openai    (GPT)            — OpenAI-compatible chat + embeddings
  - deepseek  (DeepSeek)       — OpenAI-compatible
  - ollama    (local, privacy) — OpenAI-compatible /v1 + native /api/embeddings
  - lmstudio  (local, privacy) — OpenAI-compatible /v1
  - anthropic (Claude)         — native Messages API
  - google    (Gemini)         — native generateContent API

All calls are dependency-free (urllib) so the gateway works in any environment.
"""

import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from app.core.crypto_vault import decrypt

REQUEST_TIMEOUT = 300  # موديلات التفكير المحلية (qwen3.8) قد تحتاج دقائق لأول استدعاء


class LLMGatewayError(Exception):
    pass


# ---------------------------------------------------------------- helpers ---

def _http_json(method: str, url: str, headers: Dict[str, str], payload: Optional[Dict] = None,
               timeout: int = REQUEST_TIMEOUT) -> Tuple[int, Dict[str, Any]]:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, method=method, data=data)
    for key, value in headers.items():
        req.add_header(key, value)
    if payload is not None and "Content-Type" not in headers:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"error": raw[:400]}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LLMGatewayError(f"Connection failed: {exc}") from exc


def _auth_headers(provider, json_content: bool = True) -> Dict[str, str]:
    key = decrypt(provider.api_key_encrypted or "")
    ptype = provider.provider_type
    headers: Dict[str, str] = {}
    if json_content:
        headers["Content-Type"] = "application/json"
    if ptype == "anthropic":
        if key:
            headers["x-api-key"] = key
        headers["anthropic-version"] = "2023-06-01"
    elif ptype == "google":
        if key:
            headers["x-goog-api-key"] = key
    elif key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def _base(provider) -> str:
    return (provider.base_url or "").rstrip("/")


# ------------------------------------------------------------ chat ---

def _chat_openai_compatible(provider, messages: List[Dict], temperature: float, max_tokens: int) -> Dict[str, Any]:
    url = f"{_base(provider)}/chat/completions"
    payload = {
        "model": provider.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    status, body = _http_json("POST", url, _auth_headers(provider), payload)
    if status != 200:
        raise LLMGatewayError(f"Provider HTTP {status}: {json.dumps(body)[:300]}")
    content = (body.get("choices") or [{}])[0].get("message", {}).get("content", "")
    usage = body.get("usage", {}) or {}
    return {
        "content": content,
        "model": body.get("model", provider.model),
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        },
    }


def _chat_anthropic(provider, messages: List[Dict], temperature: float, max_tokens: int) -> Dict[str, Any]:
    system_text = "\n".join(m["content"] for m in messages if m.get("role") == "system")
    chat_messages = [m for m in messages if m.get("role") != "system"]
    url = f"{_base(provider)}/v1/messages"
    payload: Dict[str, Any] = {
        "model": provider.model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": chat_messages,
    }
    if system_text:
        payload["system"] = system_text
    status, body = _http_json("POST", url, _auth_headers(provider), payload)
    if status != 200:
        raise LLMGatewayError(f"Anthropic HTTP {status}: {json.dumps(body)[:300]}")
    content_blocks = body.get("content") or []
    text = "".join(block.get("text", "") for block in content_blocks)
    usage = body.get("usage", {}) or {}
    return {
        "content": text,
        "model": body.get("model", provider.model),
        "usage": {
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        },
    }


def _chat_gemini(provider, messages: List[Dict], temperature: float, max_tokens: int) -> Dict[str, Any]:
    system_text = "\n".join(m["content"] for m in messages if m.get("role") == "system")
    contents = []
    for m in messages:
        if m.get("role") == "system":
            continue
        role = "model" if m.get("role") == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})
    url = f"{_base(provider)}/v1beta/models/{provider.model}:generateContent"
    payload: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    if system_text:
        payload["systemInstruction"] = {"parts": [{"text": system_text}]}
    status, body = _http_json("POST", url, _auth_headers(provider), payload)
    if status != 200:
        raise LLMGatewayError(f"Gemini HTTP {status}: {json.dumps(body)[:300]}")
    candidates = body.get("candidates") or [{}]
    parts = (candidates[0].get("content") or {}).get("parts") or []
    text = "".join(part.get("text", "") for part in parts)
    usage = body.get("usageMetadata", {}) or {}
    return {
        "content": text,
        "model": provider.model,
        "usage": {
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
            "total_tokens": usage.get("totalTokenCount", 0),
        },
    }


PROVIDER_ADAPTERS = {
    "openai": _chat_openai_compatible,
    "deepseek": _chat_openai_compatible,
    "ollama": _chat_openai_compatible,
    "lmstudio": _chat_openai_compatible,
    "openai_compatible": _chat_openai_compatible,  # أي مزود يتبع بروتوكول OpenAI (Groq, OpenRouter, Together, Mistral, vLLM...)
    "anthropic": _chat_anthropic,
    "google": _chat_gemini,
}


def chat(provider, messages: List[Dict[str, str]], temperature: Optional[float] = None,
         max_tokens: int = 4096, model_override: str = "") -> Dict[str, Any]:
    """Route a chat completion to the provider's native protocol."""
    adapter = PROVIDER_ADAPTERS.get(provider.provider_type)
    if adapter is None:
        raise LLMGatewayError(f"Unsupported provider type: {provider.provider_type}")
    if model_override:
        provider.model = model_override
    provider_temp = getattr(provider, "temperature", None)
    temp = temperature if temperature is not None else (provider_temp if provider_temp else 0.7)
    return adapter(provider, messages, temp, max_tokens)


# -------------------------------------------------------- embeddings ---

def embed(provider, text: str) -> Optional[List[float]]:
    """Embedding via Ollama native API or OpenAI-compatible /embeddings."""
    if provider is None or not provider.enabled:
        return None
    model = provider.embedding_model or provider.model
    try:
        if provider.provider_type == "ollama":
            url = f"{_base(provider).replace('/v1', '')}/api/embeddings"
            status, body = _http_json("POST", url, _auth_headers(provider), {"model": model, "prompt": text})
            if status == 200 and body.get("embedding"):
                return body["embedding"]
            return None
        if provider.provider_type in ("openai", "deepseek", "lmstudio", "openai_compatible"):
            url = f"{_base(provider)}/embeddings"
            status, body = _http_json("POST", url, _auth_headers(provider), {"model": model, "input": text})
            if status == 200:
                data = body.get("data") or [{}]
                return data[0].get("embedding")
        return None
    except LLMGatewayError:
        return None


# ---------------------------------------------------- test connection ---

def test_connection(provider) -> Dict[str, Any]:
    """Probe a provider: models endpoint where available, else a minimal chat."""
    started = time.time()
    ptype = provider.provider_type
    base = _base(provider)
    try:
        if ptype == "ollama":
            status, body = _http_json("GET", f"{base.replace('/v1', '')}/api/tags", _auth_headers(provider, json_content=False), timeout=15)
            models = [m.get("name", "") for m in body.get("models", [])]
            latency = int((time.time() - started) * 1000)
            return {"ok": status == 200, "latency_ms": latency, "models": models}
        if ptype in ("openai", "deepseek", "lmstudio", "openai_compatible"):
            status, body = _http_json("GET", f"{base}/models", _auth_headers(provider, json_content=False), timeout=15)
            models = [m.get("id", "") for m in body.get("data", [])][:40]
            latency = int((time.time() - started) * 1000)
            return {"ok": status == 200, "latency_ms": latency, "models": models}
        if ptype == "anthropic":
            status, body = _http_json("GET", f"{base}/v1/models", _auth_headers(provider, json_content=False), timeout=15)
            models = [m.get("id", "") for m in body.get("data", [])][:40]
            latency = int((time.time() - started) * 1000)
            return {"ok": status == 200, "latency_ms": latency, "models": models}
        if ptype == "google":
            status, body = _http_json("GET", f"{base}/v1beta/models", _auth_headers(provider, json_content=False), timeout=15)
            models = [m.get("name", "") for m in body.get("models", [])][:40]
            latency = int((time.time() - started) * 1000)
            return {"ok": status == 200, "latency_ms": latency, "models": models}
        return {"ok": False, "latency_ms": 0, "models": [], "error": f"Unknown provider type {ptype}"}
    except LLMGatewayError as exc:
        return {"ok": False, "latency_ms": int((time.time() - started) * 1000), "models": [], "error": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "latency_ms": int((time.time() - started) * 1000), "models": [], "error": str(exc)}