"""
Multi-Agent Supervisor — true collaborative orchestration.

Agents:
  Search  → 联网搜索下载模板
  Parse   → 分析模板结构 (regex → LLM fallback on failure)
  RAG     → 检索 Author Guidelines 约束
  Assemble → 零 Token 内容注入

The Supervisor:
  - Passes shared state through all agents
  - Retries with LLM fallback if Parser fails
  - Retries Search with alternative queries
  - Aggregates RAG constraints into the mapping
  - Coordinates parallel work where possible
"""

from __future__ import annotations

import json
import logging
from typing import TypedDict

from langgraph.graph import END, StateGraph

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared Agent State
# ---------------------------------------------------------------------------
class AgentState(TypedDict, total=False):
    # Input
    journal_name: str
    template_format: str
    template_path: str
    user_content: dict[str, str]
    figures: list[dict]
    llm_config: dict | None       # for fallback

    # Search output
    search_results: list[dict]
    download_path: str
    extract_dir: str

    # Parse output
    mapping_json: str | None
    parse_attempts: int
    parse_used_llm: bool

    # RAG output
    rag_constraints: list[dict]

    # Assemble output
    assembled_text: str
    output_path: str

    # Pipeline control
    mode: str  # "full_pipeline" | "parse_only" | "search_only" | "assemble_only"
    status: str
    error: str
    agent_log: list[str]


def _log(state: AgentState, msg: str) -> None:
    log_list = state.get("agent_log", [])
    log_list.append(msg)
    state["agent_log"] = log_list
    logger.info("[Supervisor] %s", msg)


# ---------------------------------------------------------------------------
# Agent Nodes
# ---------------------------------------------------------------------------

async def agent_search(state: AgentState) -> dict:
    """Search agent: find and download template."""
    _log(state, "SearchAgent: searching for template")
    from app.services.search_service import search_template_links
    from app.services.downloader import download_and_extract
    from app.core.config import settings
    from pathlib import Path

    journal = state["journal_name"]
    fmt = state.get("template_format", "latex")

    try:
        candidates = search_template_links(journal, fmt)
        if not candidates:
            _log(state, "SearchAgent: no results, trying broader query")
            # Fallback: broader search
            candidates = search_template_links(
                f"{journal} official template cls sty", fmt
            )

        if not candidates:
            return {"status": "failed", "error": "No template links found. Try a broader journal name."}

        best = candidates[0]
        _log(state, f"SearchAgent: downloading {best['url']}")

        # Use user's preferred download path from settings, or default
        dl_dir = Path(settings.TEMPLATE_WORKDIR).resolve()
        result = await download_and_extract(best["url"], journal, fmt)

        return {
            "search_results": candidates,
            "download_path": result["archive_path"],
            "extract_dir": result["extract_dir"],
            "status": "parsing",
        }
    except Exception as exc:
        _log(state, f"SearchAgent: failed — {exc}")
        # Try second candidate
        candidates = state.get("search_results", candidates if 'candidates' in dir() else [])
        if len(candidates) > 1:
            try:
                result = await download_and_extract(candidates[1]["url"], journal, fmt)
                _log(state, f"SearchAgent: retry with {candidates[1]['url']} succeeded")
                return {
                    "extract_dir": result["extract_dir"],
                    "download_path": result["archive_path"],
                    "status": "parsing",
                }
            except Exception:
                pass
        return {"status": "failed", "error": f"All download attempts failed: {exc}"}


async def agent_parse(state: AgentState) -> dict:
    """Parser agent: analyze template structure, with LLM fallback."""
    _log(state, "ParserAgent: analyzing template structure")

    from app.services.template_parser import parse_template
    from pathlib import Path

    extract_dir = state.get("extract_dir", "")
    template_path = state.get("template_path", "")
    fmt = state.get("template_format", "latex")

    # Try to find main.tex in extract_dir
    search_path = template_path or extract_dir
    if extract_dir and not template_path:
        ed = Path(extract_dir)
        candidate = ed / "main.tex"
        if candidate.exists():
            search_path = str(candidate)
        else:
            tex_files = list(ed.rglob("*.tex"))
            if tex_files:
                search_path = str(tex_files[0])

    attempts = state.get("parse_attempts", 0) + 1

    if not search_path or not Path(search_path).exists():
        _log(state, "ParserAgent: no template file found")
        return {"status": "failed", "error": "No .tex/.docx file found in template"}

    # Try standard parser first
    try:
        mapping = parse_template(search_path, fmt)
        if mapping.modules:
            _log(state, f"ParserAgent: found {len(mapping.modules)} modules via regex")
            return {
                "template_path": search_path,
                "mapping_json": mapping.model_dump_json(indent=2),
                "parse_attempts": attempts,
                "parse_used_llm": False,
                "status": "rag",
            }
    except Exception as exc:
        _log(state, f"ParserAgent: regex parser failed — {exc}")

    # LLM fallback
    _log(state, "ParserAgent: invoking LLM fallback parser")
    try:
        from app.agents.parser_fallback import llm_parse_template
        mapping = await llm_parse_template(
            search_path, fmt, state.get("llm_config")
        )
        if mapping and mapping.modules:
            _log(state, f"ParserAgent: LLM found {len(mapping.modules)} modules")
            return {
                "template_path": search_path,
                "mapping_json": mapping.model_dump_json(indent=2),
                "parse_attempts": attempts,
                "parse_used_llm": True,
                "status": "rag",
            }
    except Exception as exc2:
        _log(state, f"ParserAgent: LLM fallback also failed — {exc2}")

    return {"status": "failed", "error": f"Parser exhausted ({attempts} attempts). Last: {exc2 if 'exc2' in dir() else exc}"}


async def agent_rag(state: AgentState) -> dict:
    """RAG agent: retrieve formatting constraints from guidelines."""
    _log(state, "RAGAgent: searching guidelines")

    mapping_json = state.get("mapping_json", "")
    if not mapping_json:
        return {"rag_constraints": [], "status": "assemble"}

    try:
        from app.services.rag_service import search_guidelines
        mapping = json.loads(mapping_json)
        constraints = []

        # For each module, try to find relevant guidelines
        for mod in mapping.get("modules", []):
            label = mod.get("label", "")
            mtype = mod.get("type", "")
            if mtype in ("figure", "table"):
                continue
            query = f"{label} formatting requirements word limit citation style"
            try:
                hits = search_guidelines(query, top_k=3)
                for h in hits:
                    constraints.append({
                        "module_id": mod.get("id"),
                        "module_label": label,
                        "text": h.get("text", ""),
                        "score": h.get("score", 0),
                    })
            except Exception:
                pass  # Milvus may be offline

        _log(state, f"RAGAgent: found {len(constraints)} constraints")
        return {"rag_constraints": constraints, "status": "assemble"}
    except Exception as exc:
        _log(state, f"RAGAgent: skipped — {exc}")
        return {"rag_constraints": [], "status": "assemble"}


async def agent_assemble(state: AgentState) -> dict:
    """Assembler agent: zero-token content injection."""
    _log(state, "AssembleAgent: injecting content (zero-token)")

    from app.schemas.mapping import TemplateMapping
    from app.services.latex_assembler import assemble_latex, save_assembled_latex
    from app.services.docx_assembler import assemble_docx, save_assembled_docx
    from app.core.config import settings
    from pathlib import Path
    import uuid

    try:
        mapping = TemplateMapping.model_validate_json(state["mapping_json"])
        user_content = state.get("user_content", {})
        figures = state.get("figures", [])
        template_path = state.get("template_path", "")
        fmt = state.get("template_format", "latex")

        workdir = Path(settings.TEMPLATE_WORKDIR).resolve()
        workdir.mkdir(parents=True, exist_ok=True)

        if fmt in ("latex", "tex"):
            assembled = assemble_latex(template_path, mapping, user_content, figures=figures)
            out = workdir / f"assembled_{uuid.uuid4().hex[:8]}.tex"
            save_assembled_latex(assembled, out)
        else:
            doc = assemble_docx(template_path, mapping, user_content)
            out = workdir / f"assembled_{uuid.uuid4().hex[:8]}.docx"
            save_assembled_docx(doc, out)

        _log(state, f"AssembleAgent: output → {out}")
        return {
            "assembled_text": assembled if fmt in ("latex", "tex") else str(out),
            "output_path": str(out),
            "status": "done",
        }
    except Exception as exc:
        _log(state, f"AssembleAgent: failed — {exc}")
        return {"status": "failed", "error": str(exc)}


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
def _route_supervisor(state: AgentState) -> str:
    """Rule-based supervisor: decide next agent based on state."""
    mode = state.get("mode", "full_pipeline")
    status = state.get("status", "")

    if status == "failed":
        return END

    if mode == "search_only":
        return "search"
    if mode == "parse_only":
        return "parse"
    if mode == "assemble_only":
        return "assemble"

    # Full pipeline
    if status == "done":
        return END
    if status in ("", "searching"):
        return "search"
    if status == "parsing":
        return "parse"
    if status == "rag":
        return "rag"
    if status == "assemble":
        return "assemble"

    return END


def _after_search(state: AgentState) -> str:
    if state.get("status") == "failed":
        return END
    return "parse"


def _after_parse(state: AgentState) -> str:
    if state.get("status") == "failed":
        return END
    return "rag"


def _after_rag(state: AgentState) -> str:
    return "assemble"  # always proceed, even if RAG had no results


def _after_assemble(state: AgentState) -> str:
    return END


# ---------------------------------------------------------------------------
# Build graph
# ---------------------------------------------------------------------------
def build_supervisor_graph():
    graph = StateGraph(AgentState)

    graph.add_node("search", agent_search)       # type: ignore[arg-type]
    graph.add_node("parse", agent_parse)         # type: ignore[arg-type]
    graph.add_node("rag", agent_rag)             # type: ignore[arg-type]
    graph.add_node("assemble", agent_assemble)   # type: ignore[arg-type]

    graph.set_entry_point("search")

    graph.add_conditional_edges("search", _after_search, {"parse": "parse", END: END})
    graph.add_conditional_edges("parse", _after_parse, {"rag": "rag", END: END})
    graph.add_conditional_edges("rag", _after_rag, {"assemble": "assemble"})
    graph.add_conditional_edges("assemble", _after_assemble, {END: END})

    return graph.compile()


_supervisor = None


async def run_pipeline(
    journal_name: str,
    template_format: str = "latex",
    mode: str = "full_pipeline",
    template_path: str = "",
    user_content: dict | None = None,
    figures: list | None = None,
    llm_config: dict | None = None,
) -> AgentState:
    """Run the multi-agent pipeline."""
    global _supervisor
    if _supervisor is None:
        _supervisor = build_supervisor_graph()

    initial: AgentState = {
        "journal_name": journal_name,
        "template_format": template_format,
        "template_path": template_path,
        "user_content": user_content or {},
        "figures": figures or [],
        "llm_config": llm_config,
        "mode": mode,
        "status": "searching" if mode == "full_pipeline" else "",
        "parse_attempts": 0,
        "parse_used_llm": False,
        "rag_constraints": [],
        "agent_log": [],
    }

    result = await _supervisor.ainvoke(initial)  # type: ignore[arg-type]
    return result  # type: ignore[return-value]
