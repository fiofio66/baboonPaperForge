"""
Word (.docx) template structure parser.

Parses a .docx file and extracts the module structure tree by:
1. Iterating paragraphs and detecting Word heading styles
2. Detecting placeholder patterns: {{TITLE}}, [[ABSTRACT]], etc.
3. Falling back to heuristics for plain-text markers

Returns the same ModuleMapping dict format as the LaTeX parser.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from docx import Document

ModuleDict = dict[str, Any]

# ---------------------------------------------------------------------------
# Placeholder patterns → module type
# ---------------------------------------------------------------------------
PLACEHOLDER_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\{\{\s*TITLE\s*\}\}", re.IGNORECASE), "title"),
    (re.compile(r"\{\{\s*AUTHOR\s*\}\}", re.IGNORECASE), "author"),
    (re.compile(r"\{\{\s*ABSTRACT\s*\}\}", re.IGNORECASE), "abstract"),
    (re.compile(r"\{\{\s*KEYWORDS\s*\}\}", re.IGNORECASE), "keywords"),
    (re.compile(r"\{\{\s*ACKNOWLEDGMENTS?\s*\}\}", re.IGNORECASE), "acknowledgments"),
    (re.compile(r"\[\[\s*INTRODUCTION\s*\]\]", re.IGNORECASE), "section"),
    (re.compile(r"\[\[\s*CONCLUSION\s*\]\]", re.IGNORECASE), "section"),
    (re.compile(r"\[\[\s*METHODS?\s*\]\]", re.IGNORECASE), "section"),
    (re.compile(r"\[\[\s*RESULTS?\s*\]\]", re.IGNORECASE), "section"),
    (re.compile(r"\[\[\s*DISCUSSION\s*\]\]", re.IGNORECASE), "section"),
    (re.compile(r"\[\[\s*REFERENCES?\s*\]\]", re.IGNORECASE), "bibliography"),
]

# Word built-in heading style IDs → section level
HEADING_STYLES: dict[str, int] = {
    "Heading 1": 1,
    "Heading 2": 2,
    "Heading 3": 3,
    "heading 1": 1,
    "heading 2": 2,
    "heading 3": 3,
}


def parse_docx_template(filepath: str | Path) -> list[ModuleDict]:
    """Parse a .docx template and return its module structure.

    Args:
        filepath: Path to a .docx file.

    Returns:
        List of module dicts (same schema as latex_parser).
    """
    path = Path(filepath)
    doc = Document(str(path))

    modules: list[ModuleDict] = []
    counter = 0

    def _next_id() -> str:
        nonlocal counter
        counter += 1
        return f"mod-{counter:03d}"

    # ------------------------------------------------------------------
    # Pass 1: Word heading styles → section modules
    # ------------------------------------------------------------------
    for pidx, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if not text:
            continue

        style_name = para.style.name if para.style else ""

        # 1a. Built-in heading style
        if style_name in HEADING_STYLES:
            level = HEADING_STYLES[style_name]
            modules.append({
                "id": _next_id(),
                "type": "section",
                "label": text,
                "anchor_para_index": pidx,
                "anchor_type": "heading_style",
                "anchor_pattern": style_name,
                "content": text,
                "level": level,
                "constraints": [],
            })
            continue

        # 1b. Placeholder pattern match
        matched = False
        for pattern, mod_type in PLACEHOLDER_PATTERNS:
            if pattern.search(text):
                modules.append({
                    "id": _next_id(),
                    "type": mod_type,
                    "label": text,
                    "anchor_para_index": pidx,
                    "anchor_type": "placeholder",
                    "anchor_pattern": pattern.pattern,
                    "content": text,
                    "constraints": [],
                })
                matched = True
                break
        if matched:
            continue

        # 1c. Heuristic: "1. Introduction", "2. Methods" etc.
        m = re.match(r"^(\d+[\.\)]\s*)?(Abstract|Introduction|Background|Related Work|"
                     r"Methodology|Methods?|Experiments?|Results?|Discussion|"
                     r"Conclusion|Future Work|References?|Bibliography|"
                     r"Acknowledgments?|Appendix)",
                     text, re.IGNORECASE)
        if m:
            label = m.group(2).strip()
            mod_type = "abstract" if label.lower() == "abstract" else \
                       "bibliography" if label.lower() in ("references", "bibliography") else \
                       "acknowledgments" if label.lower().startswith("acknowledgment") else \
                       "section"
            modules.append({
                "id": _next_id(),
                "type": mod_type,
                "label": label,
                "anchor_para_index": pidx,
                "anchor_type": "heuristic",
                "anchor_pattern": re.escape(text),
                "content": text,
                "constraints": [],
            })

    if not modules:
        # Fallback: return at least a minimal structure
        modules.append({
            "id": _next_id(),
            "type": "title",
            "label": "Title",
            "anchor_para_index": 0,
            "anchor_type": "placeholder",
            "anchor_pattern": "",
            "content": "",
            "constraints": [],
        })

    return modules
