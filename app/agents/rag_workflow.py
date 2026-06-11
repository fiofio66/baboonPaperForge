"""
LangGraph RAG workflow.

Orchestrates: extract PDF → chunk → embed → insert → (optional) retrieve

Two modes:
- ingest:  PDF → Milvus vector store
- search:  query → top-K relevant guideline chunks
"""

from __future__ import annotations

import logging
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.services.rag_service import (
    chunk_text,
    extract_pdf_text,
    insert_chunks,
    search_guidelines,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
class RAGState(TypedDict, total=False):
    mode: str               # "ingest" | "search"
    pdf_path: str           # ingest: path to PDF
    query: str              # search: natural-language question
    top_k: int              # search: number of results

    # Internal
    raw_text: str
    chunks: list[dict]
    chunk_count: int
    results: list[dict]     # search hits
    status: str             # extracting | chunking | embedding | storing | done | failed
    error: str


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

async def node_extract(state: RAGState) -> dict:
    """Extract text from PDF."""
    logger.info("RAG extract: %s", state.get("pdf_path", ""))
    try:
        raw_text = extract_pdf_text(state["pdf_path"])
        return {"raw_text": raw_text, "status": "chunking"}
    except Exception as exc:
        return {"status": "failed", "error": f"PDF extraction failed: {exc}"}


async def node_chunk(state: RAGState) -> dict:
    """Chunk the raw text."""
    text = state.get("raw_text", "")
    if not text:
        return {"status": "failed", "error": "No text to chunk"}

    source = state.get("pdf_path", "unknown")
    chunks = chunk_text(text, metadata={"source": source})
    logger.info("RAG chunk: %d chunks from %d chars", len(chunks), len(text))
    return {"chunks": chunks, "chunk_count": len(chunks), "status": "embedding"}


async def node_insert(state: RAGState) -> dict:
    """Embed chunks and insert into Milvus."""
    chunks = state.get("chunks", [])
    if not chunks:
        return {"status": "failed", "error": "No chunks to insert"}

    try:
        count = insert_chunks(chunks)
        return {"status": "done", "chunk_count": count}
    except Exception as exc:
        return {"status": "failed", "error": f"Milvus insert failed: {exc}"}


async def node_search(state: RAGState) -> dict:
    """Search Milvus for relevant guideline chunks."""
    query = state.get("query", "")
    top_k = state.get("top_k", 5)
    try:
        results = search_guidelines(query, top_k=top_k)
        logger.info("RAG search: %d hits for '%s'", len(results), query[:60])
        return {"results": results, "status": "done"}
    except Exception as exc:
        return {"status": "failed", "error": f"Search failed: {exc}"}


# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------
def _route(state: RAGState):
    """Entry router: ingest or search."""
    mode = state.get("mode", "")
    if mode == "search":
        return "search"
    return "extract"


def _after(state: RAGState):
    if state.get("status") == "failed":
        return END
    current = state.get("status", "")
    route_map = {
        "chunking": "chunk",
        "embedding": "insert",
        "done": END,
    }
    return route_map.get(current, END)


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def build_rag_graph() -> StateGraph:
    graph = StateGraph(RAGState)

    graph.add_node("extract", node_extract)   # type: ignore[arg-type]
    graph.add_node("chunk", node_chunk)       # type: ignore[arg-type]
    graph.add_node("insert", node_insert)     # type: ignore[arg-type]
    graph.add_node("search", node_search)     # type: ignore[arg-type]

    graph.set_conditional_entry_point(_route, {
        "extract": "extract",
        "search": "search",
    })

    graph.add_conditional_edges("extract", _after, {"chunk": "chunk", END: END})
    graph.add_conditional_edges("chunk", _after, {"insert": "insert", END: END})
    graph.add_conditional_edges("insert", _after, {END: END})
    graph.add_conditional_edges("search", _after, {END: END})

    return graph.compile()


# ---------------------------------------------------------------------------
# Top-level runners
# ---------------------------------------------------------------------------
_rag_graph = None


async def run_ingest(pdf_path: str) -> RAGState:
    global _rag_graph
    if _rag_graph is None:
        _rag_graph = build_rag_graph()
    result = await _rag_graph.ainvoke({"mode": "ingest", "pdf_path": pdf_path})  # type: ignore[arg-type]
    return result  # type: ignore[return-value]


async def run_search(query: str, top_k: int = 5) -> RAGState:
    global _rag_graph
    if _rag_graph is None:
        _rag_graph = build_rag_graph()
    result = await _rag_graph.ainvoke({"mode": "search", "query": query, "top_k": top_k})  # type: ignore[arg-type]
    return result  # type: ignore[return-value]
