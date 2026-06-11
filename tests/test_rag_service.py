"""
Test RAG service — chunking, PDF extraction, embedding.

Embedding tests require huggingface.co (model download).
Run all:  pytest -m "slow or network or not (slow or network)"
"""

from pathlib import Path

import pytest

from app.services.rag_service import chunk_text, extract_pdf_text


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
def test_chunk_text_basic():
    text = "Section 1. Abstract. " * 200
    chunks = chunk_text(text, metadata={"source": "test.pdf"})
    assert len(chunks) >= 3, f"Expected at least 3 chunks, got {len(chunks)}"
    for c in chunks:
        assert "content" in c
        assert "metadata" in c
        assert c["metadata"].get("source") == "test.pdf"


def test_chunk_text_short():
    chunks = chunk_text("Short abstract text.")
    assert len(chunks) == 1
    assert chunks[0]["content"] == "Short abstract text."


def test_chunk_text_empty():
    assert chunk_text("") == []


# ---------------------------------------------------------------------------
# Embedding (requires network — huggingface.co)
# ---------------------------------------------------------------------------
@pytest.mark.network
def test_embed_texts_returns_correct_dim():
    from app.services.rag_service import embed_query, embed_texts
    embs = embed_query("Abstract word limit")
    assert len(embs) == 384
    batch = embed_texts(["Abstract word limit", "Reference format IEEE"])
    assert len(batch) == 2
    assert all(len(v) == 384 for v in batch)


@pytest.mark.network
def test_embed_query_normalized():
    from app.services.rag_service import embed_query
    emb = embed_query("Test query about citation format")
    norm = sum(v * v for v in emb) ** 0.5
    assert 0.99 <= norm <= 1.01, f"Expected unit vector, got norm={norm:.4f}"


# ---------------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------------
def test_extract_pdf_text(tmp_path: Path):
    import fitz
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(50, 100), "Abstract\n\nThis paper presents a novel method.")
    doc.save(str(pdf_path))
    doc.close()
    text = extract_pdf_text(pdf_path)
    assert "Abstract" in text
    assert "novel method" in text


def test_extract_pdf_multi_page(tmp_path: Path):
    import fitz
    pdf_path = tmp_path / "multi.pdf"
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page()
        page.insert_text(fitz.Point(50, 100), f"Page {i+1} content")
    doc.save(str(pdf_path))
    doc.close()
    text = extract_pdf_text(pdf_path)
    assert "Page 1" in text
    assert "Page 3" in text


# ---------------------------------------------------------------------------
# Full pipeline (chunk only, no embedding when offline)
# ---------------------------------------------------------------------------
def test_full_pipeline_chunk_only():
    text = (
        "Abstract Word Limit: 200 words. "
        "Citation Style: IEEE numeric. "
        "Figure Resolution: 300 DPI minimum. "
    ) * 50
    chunks = chunk_text(text, metadata={"source": "guidelines.pdf"})
    assert len(chunks) >= 1
    assert all("content" in c and "metadata" in c for c in chunks)


@pytest.mark.network
def test_full_pipeline_with_embedding():
    from app.services.rag_service import embed_query, embed_texts
    text = ("Abstract Word Limit: 200 words. ") * 50
    chunks = chunk_text(text, metadata={"source": "guidelines.pdf"})
    embeddings = embed_texts([c["content"] for c in chunks])
    assert len(embeddings) == len(chunks)
    assert all(len(e) == 384 for e in embeddings)
    q = embed_query("What is the abstract word limit?")
    assert len(q) == 384
