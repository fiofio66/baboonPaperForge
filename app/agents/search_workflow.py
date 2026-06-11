"""
LangGraph search workflow.

Orchestrates: build_query → search → select_best → download → extract → persist

State flows through each node; errors short-circuit to a terminal state.
"""

from __future__ import annotations

import logging
from typing import TypedDict
from uuid import UUID

from langgraph.graph import END, StateGraph

from app.services.downloader import download_and_extract
from app.services.search_service import search_template_links

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
class SearchState(TypedDict, total=False):
    journal_name: str
    template_format: str
    candidates: list[dict]       # from search_service
    selected_url: str            # best candidate URL
    archive_path: str            # downloaded archive location
    extract_dir: str             # extracted directory
    file_count: int              # files in extracted tree
    status: str                  # searching | downloading | extracting | done | failed
    error: str                   # error detail if failed


# ---------------------------------------------------------------------------
# Node implementations
# ---------------------------------------------------------------------------

async def node_search(state: SearchState) -> dict:
    """Search the web for template download candidates."""
    logger.info("SearchNode: searching for %s [%s]", state["journal_name"], state["template_format"])
    try:
        candidates = await search_template_links(
            state["journal_name"], state["template_format"]
        )
        if not candidates:
            return {"candidates": [], "status": "failed", "error": "No template links found"}
        return {"candidates": candidates, "status": "downloading"}
    except Exception as exc:
        logger.exception("SearchNode failed")
        return {"status": "failed", "error": str(exc)}


async def node_select_best(state: SearchState) -> dict:
    """Pick the highest-scoring candidate URL."""
    candidates = state.get("candidates", [])
    if not candidates:
        return {"status": "failed", "error": "No candidates to select from"}

    best = candidates[0]  # already sorted by score desc
    logger.info("SelectNode: picked %s (score=%d)", best["url"], best["score"])
    return {"selected_url": best["url"], "status": "downloading"}


async def node_download(state: SearchState) -> dict:
    """Download and extract the selected template archive."""
    url = state.get("selected_url", "")
    if not url:
        return {"status": "failed", "error": "No URL selected"}

    logger.info("DownloadNode: downloading %s", url)
    try:
        result = await download_and_extract(
            url, state["journal_name"], state["template_format"]
        )
        return {
            "archive_path": result["archive_path"],
            "extract_dir": result["extract_dir"],
            "file_count": result["file_count"],
            "status": "done",
        }
    except Exception as exc:
        logger.exception("DownloadNode failed for %s", url)
        # Try next candidate if available
        candidates = state.get("candidates", [])
        if len(candidates) > 1:
            next_url = candidates[1]["url"]
            logger.info("DownloadNode: retrying with %s", next_url)
            try:
                result = await download_and_extract(
                    next_url, state["journal_name"], state["template_format"]
                )
                return {
                    "selected_url": next_url,
                    "archive_path": result["archive_path"],
                    "extract_dir": result["extract_dir"],
                    "file_count": result["file_count"],
                    "status": "done",
                }
            except Exception as exc2:
                return {"status": "failed", "error": f"All downloads failed. Last error: {exc2}"}
        return {"status": "failed", "error": str(exc)}


# ---------------------------------------------------------------------------
# Conditional edges
# ---------------------------------------------------------------------------

def _after_search(state: SearchState) -> str:
    if state.get("status") == "failed":
        return END
    return "select_best"


def _after_select(state: SearchState) -> str:
    if state.get("status") == "failed":
        return END
    return "download"


def _after_download(state: SearchState) -> str:
    return END  # terminal — caller reads state


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_search_graph() -> StateGraph:
    """Construct and compile the search workflow graph."""
    graph = StateGraph(SearchState)

    graph.add_node("search", node_search)         # type: ignore[arg-type]
    graph.add_node("select_best", node_select_best)  # type: ignore[arg-type]
    graph.add_node("download", node_download)     # type: ignore[arg-type]

    graph.set_entry_point("search")

    graph.add_conditional_edges("search", _after_search, {
        "select_best": "select_best",
        END: END,
    })
    graph.add_conditional_edges("select_best", _after_select, {
        "download": "download",
        END: END,
    })
    graph.add_conditional_edges("download", _after_download, {END: END})

    return graph.compile()


# ---------------------------------------------------------------------------
# Top-level runner
# ---------------------------------------------------------------------------
_search_graph = None


async def run_search(
    journal_name: str,
    template_format: str = "latex",
) -> SearchState:
    """Run the full search→download→extract workflow.

    Returns the final SearchState with archive_path, extract_dir, and status.
    """
    global _search_graph
    if _search_graph is None:
        _search_graph = build_search_graph()

    initial: SearchState = {
        "journal_name": journal_name,
        "template_format": template_format,
        "status": "searching",
    }

    result = await _search_graph.ainvoke(initial)  # type: ignore[arg-type]
    return result  # type: ignore[return-value]
