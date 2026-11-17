from app.ai.ollama_service import ollama_service


def embed_text(text: str) -> list[float]:
    return ollama_service.embed(text[:2000])
