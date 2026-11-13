import os
import httpx

OLLAMA = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
CHAT_MODEL = "gemma3:latest"
EMBED_MODEL = "nomic-embed-text"


class ModelUnavailable(Exception):
    """Ollama is not running or a model is missing."""


def _post(path, payload, timeout):
    try:
        r = httpx.post(f"{OLLAMA}{path}", json=payload, timeout=timeout, trust_env=False)
        r.raise_for_status()
        return r.json()
    except (httpx.ConnectError, httpx.TimeoutException):
        raise ModelUnavailable("The local model is not reachable. Start Ollama.")
    except httpx.HTTPStatusError:
        raise ModelUnavailable("Ollama refused the request. Check that both models are installed (ollama list).")


def installed_models():
    try:
        r = httpx.get(f"{OLLAMA}/api/tags", timeout=5, trust_env=False)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except httpx.HTTPError:
        raise ModelUnavailable("The local model is not reachable. Start Ollama.")


def embed(texts):
    return _post("/api/embed", {"model": EMBED_MODEL, "input": texts}, 120)["embeddings"]


def chat(system, user, schema=None):
    payload = {
        "model": CHAT_MODEL, "stream": False,
        "options": {"temperature": 0, "num_ctx": 4096},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    if schema:
        payload["format"] = schema
    return _post("/api/chat", payload, 300)["message"]["content"]
