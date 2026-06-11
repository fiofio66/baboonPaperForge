"""
Test Zero-Token LaTeX Assembler — content injection via regex/environment matching.
"""

import tempfile
from pathlib import Path

import pytest

from app.schemas.mapping import ModuleMapping, TemplateMapping
from app.services.latex_assembler import assemble_latex


@pytest.fixture
def sample_tex_path(tmp_path: Path) -> Path:
    template = r"""
\documentclass{article}
\title{Sample Title Placeholder}
\author{John Doe}

\begin{document}
\maketitle

\begin{abstract}
This is the abstract placeholder text.
\end{abstract}

\section{Introduction}
Intro content here.

\section{Methodology}
Methodology content here.

\section{Conclusion}
Conclusion content here.

\begin{thebibliography}{00}
\bibitem{ref1} Placeholder bib.
\end{thebibliography}

\begin{figure}[htbp]
    \centering
    \includegraphics[width=\columnwidth]{figures/placeholder.png}
    \caption{Placeholder figure}
    \label{fig:placeholder}
\end{figure}

\end{document}
"""
    p = tmp_path / "main.tex"
    p.write_text(template)
    return p


@pytest.fixture
def sample_mapping() -> TemplateMapping:
    return TemplateMapping(
        template_path="/fake/main.tex",
        format="latex",
        modules=[
            ModuleMapping(id="mod-001", type="title", label="Title", anchor_line=3,
                          anchor_type="regex", anchor_pattern=r"\\title\{[^}]*\}",
                          content=r"\title{Sample Title Placeholder}"),
            ModuleMapping(id="mod-002", type="author", label="Author", anchor_line=4,
                          anchor_type="regex", anchor_pattern=r"\\author\{[^}]*\}",
                          content=r"\author{John Doe}"),
            ModuleMapping(id="mod-003", type="abstract", label="Abstract", anchor_line=9,
                          anchor_type="environment",
                          anchor_pattern=r"\\begin\{abstract\}.*?\\end\{abstract\}",
                          content=r"\begin{abstract}...\end{abstract}"),
            ModuleMapping(id="mod-004", type="section", label="Introduction", anchor_line=12,
                          anchor_type="regex", anchor_pattern=r"\\section\{[^}]*\}", level=1,
                          content=r"\section{Introduction}"),
            ModuleMapping(id="mod-005", type="section", label="Methodology", anchor_line=15,
                          anchor_type="regex", anchor_pattern=r"\\section\{[^}]*\}", level=1,
                          content=r"\section{Methodology}"),
            ModuleMapping(id="mod-006", type="section", label="Conclusion", anchor_line=18,
                          anchor_type="regex", anchor_pattern=r"\\section\{[^}]*\}", level=1,
                          content=r"\section{Conclusion}"),
            ModuleMapping(id="mod-007", type="bibliography", label="References", anchor_line=21,
                          anchor_type="environment",
                          anchor_pattern=r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}",
                          content=""),
            ModuleMapping(id="mod-008", type="figure", label="Figure", anchor_line=26,
                          anchor_type="environment",
                          anchor_pattern=r"\\begin\{figure\}.*?\\end\{figure\}",
                          content=""),
        ],
    )


def test_assemble_title_injection(sample_tex_path: Path, sample_mapping: TemplateMapping):
    user = {"mod-001": "My Actual Paper Title"}
    result = assemble_latex(sample_tex_path, sample_mapping, user)
    assert r"\title{My Actual Paper Title}" in result
    assert "Sample Title Placeholder" not in result


def test_assemble_abstract_injection(sample_tex_path: Path, sample_mapping: TemplateMapping):
    user = {"mod-003": "This is the real abstract."}
    result = assemble_latex(sample_tex_path, sample_mapping, user)
    assert r"\begin{abstract}" in result
    assert "This is the real abstract." in result
    assert "placeholder abstract text" not in result


def test_assemble_section_injection(sample_tex_path: Path, sample_mapping: TemplateMapping):
    user = {"mod-004": "Intro Replaced"}
    result = assemble_latex(sample_tex_path, sample_mapping, user)
    assert r"\section{Intro Replaced}" in result
    assert r"\section{Introduction}" not in result


def test_assemble_bibliography_injection(sample_tex_path: Path, sample_mapping: TemplateMapping):
    user = {"mod-007": r"\bibitem{real1} Real Author, Real Title, 2025."}
    result = assemble_latex(sample_tex_path, sample_mapping, user)
    assert "Real Author" in result


def test_assemble_figure_injection(sample_tex_path: Path, sample_mapping: TemplateMapping):
    user = {"mod-008": ""}  # figure uses figures list, not user_content
    figures = [
        {"caption": "My custom figure", "label": "fig:custom",
         "image_path": "plots/result.png", "is_wide": False}
    ]
    result = assemble_latex(sample_tex_path, sample_mapping, user, figures=figures)
    assert r"\caption{My custom figure}" in result
    assert r"\label{fig:custom}" in result
    assert "plots/result.png" in result
    assert r"\begin{figure}" in result
    assert r"\begin{figure*}" not in result


def test_assemble_figure_wide(sample_tex_path: Path, sample_mapping: TemplateMapping):
    figures = [{"caption": "Wide fig", "label": "fig:wide",
                "image_path": "wide.png", "is_wide": True}]
    result = assemble_latex(sample_tex_path, sample_mapping, {"mod-008": ""}, figures=figures)
    assert r"\begin{figure*}" in result


def test_latex_escape_special_chars(sample_tex_path: Path, sample_mapping: TemplateMapping):
    """User text with &, %, $, #, _, {, } must be escaped."""
    user = {"mod-001": "Paper on A & B % with $100 #1 _test_ {key}"}
    result = assemble_latex(sample_tex_path, sample_mapping, user)
    assert r"A \& B \% with \$100 \#1 \_test\_ \{key\}" in result


def test_no_llm_token_usage():
    """Sanity: the assembler is pure Python, no API calls."""
    import inspect
    src = inspect.getsource(assemble_latex)
    forbidden = ["openai", "anthropic", "langchain", "llm", "chat", "completion"]
    src_lower = src.lower()
    for word in forbidden:
        assert word not in src_lower, f"Assembler must not call {word}"
