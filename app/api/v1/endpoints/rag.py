"""
RAG API endpoints.

POST /api/v1/rag/ingest     — ingest a PDF into Milvus
GET  /api/v1/rag/search      — semantic search over guidelines
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.agents.rag_workflow import run_ingest, run_search

router = APIRouter(prefix="/rag", tags=["rag"])


class IngestResponse(BaseModel):
    status: str
    pdf_path: str
    chunk_count: int
    error: str | None = None


class SearchResult(BaseModel):
    text: str
    score: float
    source: str


class SearchResponse(BaseModel):
    status: str
    query: str
    results: list[SearchResult]


@router.post("/ingest", response_model=IngestResponse)
async def ingest_pdf(pdf_path: str = Query(..., description="Path to the Author Guidelines PDF")):
    """Ingest a PDF into the Milvus vector store.

    Extracts text, chunks it, generates embeddings (local model),
    and stores vectors for later semantic search.
    """
    try:
        result = await run_ingest(pdf_path)
        return IngestResponse(
            status=result.get("status", "unknown"),
            pdf_path=pdf_path,
            chunk_count=result.get("chunk_count", 0),
            error=result.get("error"),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/search", response_model=SearchResponse)
async def search_guidelines_api(
    q: str = Query(..., description="Natural language query about formatting rules"),
    top_k: int = Query(5, ge=1, le=20),
):
    """Search ingested author guidelines for formatting constraints.

    Example queries:
    - "What is the maximum word count for the abstract?"
    - "Reference format requirements"
    - "Figure resolution minimum"
    """
    try:
        result = await run_search(q, top_k=top_k)
        hits = result.get("results", [])
        return SearchResponse(
            status=result.get("status", "done"),
            query=q,
            results=[SearchResult(**h) for h in hits],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
