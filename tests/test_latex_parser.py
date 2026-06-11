"""
Test LaTeX template parser with inline .tex templates.
"""

import tempfile
from pathlib import Path

import pytest

from app.services.latex_parser import parse_latex_template

# ---------------------------------------------------------------------------
# Minimal ACM/IEEE-style LaTeX template for testing
# ---------------------------------------------------------------------------
SAMPLE_TEX = r"""
\documentclass[conference]{IEEEtran}
\title{Your Paper Title Here}
\author{
    \IEEEauthorblockN{First Author\IEEEauthorrefmark{1}}
    \IEEEauthorblockA{University of Example}
}

\begin{document}
\maketitle

\begin{abstract}
This paper presents a novel approach to...
\end{abstract}

\begin{keywords}
component, formatting, style
\end{keywords}

\section{Introduction}
\IEEEPARstart{T}{his} is the introduction section...

\section{Related Work}
Prior work in this area includes...

\section{Methodology}
We propose the following method...

\subsection{Dataset}
The dataset consists of...

\subsection{Model Architecture}
Our model uses a transformer-based...

\section{Experiments}
\subsection{Setup}
We train on 8 GPUs...

\subsection{Results}
Table~\ref{tab:results} shows...

\section{Conclusion}
In this paper we have shown...

\begin{thebibliography}{00}
\bibitem{ref1} Author, ``Title,'' Journal, 2024.
\end{thebibliography}

\end{document}
"""


@pytest.fixture
def sample_tex_path(tmp_path: Path) -> Path:
    p = tmp_path / "main.tex"
    p.write_text(SAMPLE_TEX)
    return p


def test_parse_latex_finds_title(sample_tex_path: Path):
    modules = parse_latex_template(sample_tex_path)

    titles = [m for m in modules if m["type"] == "title"]
    assert len(titles) == 1
    assert titles[0]["label"] == "Title"
    assert "title" in titles[0]["anchor_pattern"]


def test_parse_latex_finds_abstract(sample_tex_path: Path):
    modules = parse_latex_template(sample_tex_path)

    abstracts = [m for m in modules if m["type"] == "abstract"]
    assert len(abstracts) >= 1


def test_parse_latex_finds_sections(sample_tex_path: Path):
    modules = parse_latex_template(sample_tex_path)

    sections = [m for m in modules if m["type"] == "section"]
    # Introduction, Related Work, Methodology, Experiments, Conclusion
    assert len(sections) >= 5

    labels = {m["label"] for m in sections}
    assert "Introduction" in labels
    assert "Methodology" in labels
    assert "Conclusion" in labels


def test_parse_latex_finds_subsections(sample_tex_path: Path):
    modules = parse_latex_template(sample_tex_path)

    subsections = [m for m in modules if m["type"] == "section" and m.get("level") == 2]
    # Dataset, Model Architecture, Setup, Results
    assert len(subsections) >= 4, f"Expected >=4 subsections, got {len(subsections)}: {[m['label'] for m in subsections]}"


def test_parse_latex_finds_bibliography(sample_tex_path: Path):
    modules = parse_latex_template(sample_tex_path)

    bibs = [m for m in modules if m["type"] == "bibliography"]
    assert len(bibs) >= 1


def test_parse_latex_modules_sorted_by_line(sample_tex_path: Path):
    modules = parse_latex_template(sample_tex_path)
    lines = [m["anchor_line"] for m in modules]
    assert lines == sorted(lines), f"Modules not sorted by line: {lines}"


def test_parse_latex_empty_file(tmp_path: Path):
    p = tmp_path / "empty.tex"
    p.write_text("% nothing here")
    modules = parse_latex_template(p)
    assert modules == []


def test_parse_latex_all_modules_have_required_keys(sample_tex_path: Path):
    modules = parse_latex_template(sample_tex_path)
    required = {"id", "type", "label", "anchor_line", "anchor_type", "anchor_pattern", "content"}
    for m in modules:
        missing = required - m.keys()
        assert not missing, f"Module {m.get('id', '?')} missing keys: {missing}"


def test_parse_latex_with_maketitle(tmp_path: Path):
    p = tmp_path / "mktitle.tex"
    p.write_text(r"\documentclass{article}\title{Test}\author{Me}\begin{document}\maketitle\section{Intro}Hi\end{document}")
    modules = parse_latex_template(p)
    types = {m["type"] for m in modules}
    assert "title" in types
    assert "section" in types
