import re
from pathlib import Path

import chromadb

from app.ai.embedding_service import embed_text
from app.config import get_settings

COLLECTION = "erp_knowledge"


def _client() -> chromadb.PersistentClient:
    settings = get_settings()
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(settings.chroma_dir))


def _chunks(path: Path) -> list[tuple[str, str, str]]:
    raw = path.read_text(encoding="utf-8")
    sections = re.split(r"\n(?=#{1,3} )", raw)
    chunks: list[tuple[str, str, str]] = []
    for section in sections:
        text = section.strip()
        if len(text) < 40:
            continue
        title = text.splitlines()[0].lstrip("#").strip()
        blocks = [text] if len(text) <= 900 else _split(text)
        for index, block in enumerate(blocks):
            chunks.append((f"{path.name}:{title}:{index}", block, title))
    return chunks


def _split(text: str) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    blocks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) < 800:
            current = f"{current}\n\n{paragraph}".strip()
        else:
            if current:
                blocks.append(current)
            current = paragraph[:900]
    if current:
        blocks.append(current)
    return blocks or [text[:900]]


def index_knowledge() -> dict:
    settings = get_settings()
    folder = settings.knowledge_dir
    files = sorted(folder.glob("*.md"))
    client = _client()
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []
    embeddings: list[list[float]] = []
    for path in files:
        for chunk_id, text, title in _chunks(path):
            ids.append(chunk_id)
            documents.append(text)
            metadatas.append({"source": path.name, "title": title})
            embeddings.append(embed_text(text))
    if ids:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
    return {"documents": len(files), "chunks": len(ids), "collection": COLLECTION}


def stats() -> dict:
    client = _client()
    try:
        collection = client.get_collection(COLLECTION)
        count = collection.count()
    except Exception:
        count = 0
    files = list(get_settings().knowledge_dir.glob("*.md"))
    return {"documents": len(files), "chunks": count, "collection": COLLECTION}


def retrieve(query: str, limit: int = 4) -> list[dict]:
    client = _client()
    try:
        collection = client.get_collection(COLLECTION)
    except Exception:
        return []
    if collection.count() == 0:
        return []
    vector = embed_text(query)
    found = collection.query(query_embeddings=[vector], n_results=min(limit, collection.count()))
    results = []
    documents = found.get("documents") or [[]]
    metadatas = found.get("metadatas") or [[]]
    distances = found.get("distances") or [[]]
    for document, metadata, distance in zip(documents[0], metadatas[0], distances[0]):
        if distance is not None and distance > 0.55:
            continue
        results.append(
            {
                "title": metadata.get("title") or metadata.get("source") or "Manual",
                "source": metadata.get("source") or "",
                "excerpt": document[:700],
                "distance": distance,
            }
        )
    return results
