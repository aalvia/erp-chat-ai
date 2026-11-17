import httpx

from app.config import get_settings


class OllamaError(Exception):
    pass


class OllamaService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = httpx.Client(timeout=httpx.Timeout(180.0, connect=5.0))

    def health(self) -> dict:
        model = self.settings.ollama_model
        try:
            response = self._client.get(f"{self.settings.ollama_base_url}/api/tags", timeout=5)
            response.raise_for_status()
            names = [item.get("name", "") for item in response.json().get("models", [])]
        except httpx.HTTPError:
            return {"ok": False, "model": model, "models": []}
        ready = any(name == model or name.startswith(f"{model}:") for name in names)
        return {"ok": ready, "model": model, "models": names}

    def chat(self, messages: list[dict], tools: list[dict] | None = None, response_format: dict | None = None) -> dict:
        payload: dict = {
            "model": self.settings.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0, "num_ctx": self.settings.ollama_num_ctx},
            "keep_alive": self.settings.ollama_keep_alive,
        }
        if tools:
            payload["tools"] = tools
        if response_format is not None:
            payload["format"] = response_format
        try:
            response = self._client.post(f"{self.settings.ollama_base_url}/api/chat", json=payload)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OllamaError("Ollama no respondió.") from exc
        return response.json().get("message", {})

    def embed(self, text: str) -> list[float]:
        try:
            response = self._client.post(
                f"{self.settings.ollama_base_url}/api/embed",
                json={"model": self.settings.ollama_embedding_model, "input": text, "keep_alive": 0},
                timeout=90,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OllamaError("No se pudo generar el embedding.") from exc
        embeddings = response.json().get("embeddings") or []
        if not embeddings:
            raise OllamaError("El modelo de embeddings no devolvió un vector.")
        return embeddings[0]


ollama_service = OllamaService()
