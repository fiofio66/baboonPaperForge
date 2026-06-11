"""
LaTeX template structure parser.

Parses a .tex file and extracts the module structure tree:
- \\title{}, \\author{}  → title, author
- \\begin{abstract}      → abstract
- \\section{}, \\subsection{}, \\subsubsection{} → section (level 1/2/3)
- \\begin{thebibliography} / \\bibliography{} → bibliography
- \\begin{figure}, \\begin{table} → figure, table

Returns a list of ModuleMapping dicts with insertion anchors.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from TexSoup import TexSoup

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
ModuleDict = dict[str, Any]

# ---------------------------------------------------------------------------
# Structural command → module type mapping
# ---------------------------------------------------------------------------
SECTION_COMMANDS: dict[str, int] = {
    "chapter": 0,
    "section": 1,
    "subsection": 2,
    "subsubsection": 3,
}

SINGLETON_COMMANDS: dict[str, str] = {
    "title": "title",
    "author": "author",
    "date": "date",
    "maketitle": "maketitle",
}

# Environment names that indicate structural modules
ENV_TYPE_MAP: dict[str, str] = {
    "abstract": "abstract",
    "figure": "figure",
    "figure*": "figure",
    "table": "table",
    "table*": "table",
    "thebibliography": "bibliography",
    "acknowledgments": "acknowledgments",
    "acknowledgement": "acknowledgments",
}


def _build_regex(command: str, n_args: int = 1) -> str:
    """Build a capture regex for a LaTeX command with n arguments."""
    parts = [r"\\" + command]
    for _ in range(n_args):
        parts.append(r"\{([^}]*)\}")
    return "".join(parts)


def parse_latex_template(filepath: str | Path) -> list[ModuleDict]:
    """Parse a LaTeX template file and return its module structure.

    Args:
        filepath: Path to a .tex file.

    Returns:
        List of module dicts, each containing:
        - id, type, label, anchor_line, anchor_type, anchor_pattern, content, constraints
    """
    path = Path(filepath)
    raw_text = path.read_text(encoding="utf-8", errors="replace")
    lines = raw_text.splitlines()

    modules: list[ModuleDict] = []
    counter = 0

    def _next_id() -> str:
        nonlocal counter
        counter += 1
        return f"mod-{counter:03d}"

    # ------------------------------------------------------------------
    # Pass 1: line-by-line scan for commands that TexSoup may flatten
    # ------------------------------------------------------------------
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()

        # --- \title{...} ---
        if re.search(r"\\title\s*\{", stripped):
            modules.append({
                "id": _next_id(),
                "type": "title",
                "label": "Title",
                "anchor_line": lineno,
                "anchor_type": "regex",
                "anchor_pattern": _build_regex("title"),
                "content": stripped,
                "constraints": [],
            })

        # --- \author{...} ---
        if re.search(r"\\author\s*\{", stripped):
            modules.append({
                "id": _next_id(),
                "type": "author",
                "label": "Author",
                "anchor_line": lineno,
                "anchor_type": "regex",
                "anchor_pattern": _build_regex("author"),
                "content": stripped,
                "constraints": [],
            })

        # --- \bibliography{...} ---
        if re.search(r"\\bibliography\s*\{", stripped):
            modules.append({
                "id": _next_id(),
                "type": "bibliography",
                "label": "References",
                "anchor_line": lineno,
                "anchor_type": "regex",
                "anchor_pattern": _build_regex("bibliography"),
                "content": stripped,
                "constraints": [],
            })

        # --- \section / \subsection / \subsubsection ---
        for cmd, level in SECTION_COMMANDS.items():
            m = re.search(rf"\\{cmd}\s*\{{", stripped)
            if m:
                label_match = re.search(rf"\\{cmd}\s*\{{([^}}]*)\}}", stripped)
                raw_label = label_match.group(1) if label_match else cmd.title()
                modules.append({
                    "id": _next_id(),
                    "type": "section",
                    "label": raw_label.strip(),
                    "anchor_line": lineno,
                    "anchor_type": "regex",
                    "anchor_pattern": _build_regex(cmd),
                    "content": stripped,
                    "level": level,
                    "constraints": [],
                })
                break

    # ------------------------------------------------------------------
    # Pass 2: TexSoup parse for environments (abstract, bibliography, etc.)
    # ------------------------------------------------------------------
    try:
        soup = TexSoup(raw_text)
    except Exception:
        # TexSoup choked — return whatever the line-by-line pass found
        return modules

    for env_name, mod_type in ENV_TYPE_MAP.items():
        for env in soup.find_all(env_name):
            # Estimate line number from raw position
            env_text = str(env)
            est_lineno = 1
            idx = raw_text.find(env_text.splitlines()[0][:60])
            if idx >= 0:
                est_lineno = raw_text[:idx].count("\n") + 1

            modules.append({
                "id": _next_id(),
                "type": mod_type,
                "label": env_name.replace("*", "").title(),
                "anchor_line": est_lineno,
                "anchor_type": "environment",
                "anchor_pattern": rf"\\begin\{{{env_name}\}}(.*?)\\end\{{{env_name}\}}",
                "content": env_text[:300],
                "constraints": [],
            })

    # Sort by line number
    modules.sort(key=lambda m: m["anchor_line"])
    return modules
