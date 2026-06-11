"""
RAG (Retrieval-Augmented Generation) service.

Handles PDF ingestion, chunking, embedding, and Milvus vector search
for Author Guidelines / formatting rules retrieval.

Supports two embedding backends:
- sentence-transformers (local, zero API key)
- OpenAI embeddings (BYOK, via stored LLMConfig)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
_CHUNK_SIZE = 800
_CHUNK_OVERLAP = 100

_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=_CHUNK_SIZE,
    chunk_overlap=_CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def chunk_text(text: str, metadata: dict | None = None) -> list[dict[str, Any]]:
    """Split text into overlapping chunks with metadata.

    Returns list of dicts with ``content`` and ``metadata`` keys.
    """
    meta = metadata or {}
    docs = _text_splitter.create_documents([text], [meta])
    return [{"content": d.page_content, "metadata": d.metadata} for d in docs]


# ---------------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------------
def extract_pdf_text(filepath: str | Path) -> str:
    """Extract full text from a PDF using pymupdf (fitz).

    Returns concatenated text of all pages, separated by form feeds.
    """
    import fitz  # pymupdf
    path = Path(filepath)
    doc = fitz.open(str(path))
    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text("text"))
    doc.close()
    return "\n\n".join(pages)


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------
_embedding_model = None
_embedding_model_name: str | None = None


def _get_local_embedder():
    """Lazy-load sentence-transformers model (cached)."""
    global _embedding_model, _embedding_model_name
    model_name = "all-MiniLM-L6-v2"  # light, 384-dim, good for guidelines
    if _embedding_model is None or _embedding_model_name != model_name:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model: %s", model_name)
        _embedding_model = SentenceTransformer(model_name)
        _embedding_model_name = model_name
    return _embedding_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of text strings.

    Uses local sentence-transformers by default (no API key required).
    """
    model = _get_local_embedder()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def embed_query(text: str) -> list[float]:
    """Generate a single query embedding."""
    return embed_texts([text])[0]


# ---------------------------------------------------------------------------
# Milvus operations
# ---------------------------------------------------------------------------
_COLLECTION_NAME = "author_guidelines"
_DIM = 384  # all-MiniLM-L6-v2 output dim


def _get_milvus_client():
    """Lazy-connect to Milvus."""
    from pymilvus import MilvusClient
    from app.core.config import settings
    return MilvusClient(uri=f"http://{settings.MILVUS_HOST}:{settings.MILVUS_PORT}")


def ensure_collection():
    """Create the guidelines collection if it doesn't exist."""
    from pymilvus import MilvusClient
    client = _get_milvus_client()
    if _COLLECTION_NAME not in client.list_collections():
        client.create_collection(
            collection_name=_COLLECTION_NAME,
            dimension=_DIM,
            metric_type="COSINE",
        )
        logger.info("Created Milvus collection: %s", _COLLECTION_NAME)


def insert_chunks(chunks: list[dict[str, Any]]) -> int:
    """Embed and insert chunk dicts into Milvus.

    Returns the number of inserted vectors.
    """
    if not chunks:
        return 0

    ensure_collection()
    client = _get_milvus_client()

    texts = [c["content"] for c in chunks]
    embeddings = embed_texts(texts)

    data = []
    for i, chunk in enumerate(chunks):
        data.append({
            "id": i,
            "vector": embeddings[i],
            "text": chunk["content"],
            "source": chunk.get("metadata", {}).get("source", ""),
        })

    # Delete old data for same source
    source = chunks[0].get("metadata", {}).get("source", "")
    if source:
        client.delete(_COLLECTION_NAME, filter=f'source == "{source}"')

    result = client.insert(collection_name=_COLLECTION_NAME, data=data)
    logger.info("Inserted %d chunks into Milvus", result["insert_count"])
    return result["insert_count"]


def search_guidelines(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Semantic search over ingested author guidelines.

    Returns list of {text, score, source}.
    """
    ensure_collection()
    client = _get_milvus_client()

    query_vec = embed_query(query)

    results = client.search(
        collection_name=_COLLECTION_NAME,
        data=[query_vec],
        limit=top_k,
        output_fields=["text", "source"],
    )

    hits = []
    for batch in results:
        for hit in batch:
            entity = hit.get("entity", {})
            hits.append({
                "text": entity.get("text", ""),
                "score": hit.get("distance", 0),
                "source": entity.get("source", ""),
            })
    return hits
