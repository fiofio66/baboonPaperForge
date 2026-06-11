"""
Template parser factory.

Dispatches to the correct parser based on template format (latex / docx)
and returns a structured TemplateMapping.
"""

from __future__ import annotations

from pathlib import Path

from app.schemas.mapping import TemplateMapping
from app.services.docx_parser import parse_docx_template
from app.services.latex_parser import parse_latex_template


def parse_template(filepath: str | Path, fmt: str) -> TemplateMapping:
    """Parse a template file into a structured module mapping.

    Args:
        filepath: Path to the template file (.tex or .docx).
        fmt: Format string — ``"latex"`` or ``"docx"``.

    Returns:
        TemplateMapping with the full module tree.

    Raises:
        ValueError: If the format is unsupported or the file doesn't exist.
        FileNotFoundError: If the filepath doesn't exist.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Template file not found: {filepath}")

    fmt_lower = fmt.lower().strip()

    if fmt_lower in ("latex", "tex"):
        modules = parse_latex_template(path)
    elif fmt_lower in ("docx", "word", "doc"):
        modules = parse_docx_template(path)
    else:
        raise ValueError(
            f"Unsupported template format: '{fmt}'. Expected 'latex' or 'docx'."
        )

    return TemplateMapping(
        template_path=str(path.resolve()),
        format=fmt_lower,
        modules=modules,
    )
