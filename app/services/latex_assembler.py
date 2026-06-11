"""
Zero-Token LaTeX Assembler.

Reads a .tex template and a TemplateMapping (from the parser), then injects
user-provided content into each module by matching anchor patterns.

STRICT RULE: User content NEVER passes through any LLM. This is pure string
substitution driven by regex/environment anchors.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.schemas.mapping import TemplateMapping

# LaTeX special chars that must be escaped in user text
_LATEX_ESCAPE_MAP: dict[int, str | None] = {
    ord("&"): r"\&",
    ord("%"): r"\%",
    ord("$"): r"\$",
    ord("#"): r"\#",
    ord("_"): r"\_",
    ord("{"): r"\{",
    ord("}"): r"\}",
    ord("~"): r"\textasciitilde{}",
    ord("^"): r"\^{}",
    ord("\\"): None,  # keep backslashes (may be intentional LaTeX)
}


def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters in plain user text."""
    return text.translate(_LATEX_ESCAPE_MAP)  # type: ignore[arg-type]


def _safe_sub(pattern: str, replacement: str, text: str, **kwargs) -> str:
    """re.sub that escapes backslashes in the replacement so that
    ``\\t`` stays literal backslash-t, not a tab character."""
    escaped_repl = replacement.replace("\\", "\\\\")
    return re.sub(pattern, escaped_repl, text, **kwargs)


# ---------------------------------------------------------------------------
# Figure / Table template
# ---------------------------------------------------------------------------
_FIGURE_TEMPLATE = r"""
\begin{{{env_name}}}[htbp]
    \centering
    \includegraphics[width={width}]{{{image_path}}}
    \caption{{{caption}}}
    \label{{{label}}}
\end{{{env_name}}}
""".strip()

_TABLE_TEMPLATE = r"""
\begin{{{env_name}}}[htbp]
    \centering
    \caption{{{caption}}}
    \label{{{label}}}
    {content}
\end{{{env_name}}}
""".strip()


def assemble_latex(
    template_path: str | Path,
    mapping: TemplateMapping,
    user_sections: dict[str, str],
    figures: list[dict[str, Any]] | None = None,
) -> str:
    """Inject user content into a LaTeX template.

    Args:
        template_path: Path to the original .tex template file.
        mapping: Module structure from the template parser.
        user_sections: dict of ``module_id → new_plaintext_content``.
        figures: Optional list of figure configs, each with keys:
            ``caption``, ``label``, ``image_path``, ``is_wide`` (bool).

    Returns:
        The fully assembled .tex source as a string.
    """
    path = Path(template_path)
    text = path.read_text(encoding="utf-8", errors="replace")

    figures = figures or []
    # Track which figure slots have been filled
    figure_index = 0

    # Process modules in reverse line order so line numbers stay valid
    # when we insert multi-line replacements. Actually, for regex-based
    # replacement we don't need line numbers — we substitute in-place.
    for module in mapping.modules:
        mod_id = module.id
        new_content = user_sections.get(mod_id, "")
        if not new_content and module.type not in ("figure", "table"):
            continue

        escaped = _escape_latex(new_content)

        anchor = module.anchor_pattern
        mod_type = module.type

        # --- title / author / date → replace in \cmd{...} ---
        if mod_type in ("title", "author", "date") and anchor:
            replacement = rf"\{mod_type}{{{escaped}}}"
            text = _safe_sub(anchor, replacement, text, count=1)

        # --- section / subsection → replace heading ---
        elif mod_type == "section" and anchor:
            cmd = "chapter" if module.level == 0 else \
                  "section" if module.level == 1 else \
                  "subsection" if module.level == 2 else "subsubsection"
            replacement = rf"\{cmd}{{{escaped}}}"
            text = _safe_sub(anchor, replacement, text, count=1)

        # --- abstract / acknowledgments / bibliography (environments) ---
        elif mod_type in ("abstract", "acknowledgments") and anchor:
            env = "abstract" if mod_type == "abstract" else \
                  "acknowledgments" if "acknowledgment" in module.label.lower() else "abstract"
            replacement = rf"\\begin{{{env}}}\n{escaped}\n\\end{{{env}}}"
            text = _safe_sub(
                rf"\\begin\{{{env}\}}.*?\\end\{{{env}\}}",
                replacement,
                text,
                count=1,
                flags=re.DOTALL,
            )

        # --- bibliography (replace body of thebibliography env) ---
        elif mod_type == "bibliography" and anchor:
            # Only replace if the user provided content (don't delete bib)
            if new_content.strip():
                text = _safe_sub(
                    r"(\\begin\{thebibliography\}.*?)\\end\{thebibliography\}",
                    rf"\1\n{escaped}\n\\end{{thebibliography}}",
                    text,
                    count=1,
                    flags=re.DOTALL,
                )

        # --- figure: inject complete figure environment ---
        elif mod_type == "figure":
            if figure_index < len(figures):
                fig = figures[figure_index]
                figure_index += 1
                is_wide = fig.get("is_wide", False)
                env_name = "figure*" if is_wide else "figure"
                width = fig.get("width", r"\columnwidth" if not is_wide else r"\textwidth")
                img_path = fig.get("image_path", "")
                caption = _escape_latex(fig.get("caption", ""))
                label = _escape_latex(fig.get("label", ""))

                new_figure = _FIGURE_TEMPLATE.format(
                    env_name=env_name,
                    width=width,
                    image_path=img_path,
                    caption=caption,
                    label=label,
                )
                text = _safe_sub(anchor, new_figure, text, count=1, flags=re.DOTALL)

        # --- table: inject complete table environment ---
        elif mod_type == "table":
            if figure_index < len(figures):  # reuse figures list for tables too
                fig = figures[figure_index]
                figure_index += 1
                is_wide = fig.get("is_wide", False)
                env_name = "table*" if is_wide else "table"
                caption = _escape_latex(fig.get("caption", ""))
                label = _escape_latex(fig.get("label", ""))
                table_content = fig.get("content", r"\centering\begin{tabular}{c}...\end{tabular}")

                new_table = _TABLE_TEMPLATE.format(
                    env_name=env_name,
                    caption=caption,
                    label=label,
                    content=table_content,
                )
                text = _safe_sub(anchor, new_table, text, count=1, flags=re.DOTALL)

    return text


def save_assembled_latex(
    assembled_text: str, output_path: str | Path
) -> Path:
    """Write assembled LaTeX source to disk."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(assembled_text, encoding="utf-8")
    return out
