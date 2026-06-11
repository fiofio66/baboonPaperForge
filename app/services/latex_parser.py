"""
LaTeX template structure parser — robust for IEEE/ACM/Elsevier/etc.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

ModuleDict = dict[str, Any]

SECTION_CMDS: dict[str, int] = {
    "chapter": 0, "section": 1, "subsection": 2, "subsubsection": 3,
    "section*": 1, "subsection*": 2, "subsubsection*": 3,
}


def parse_latex_template(filepath: str | Path) -> list[ModuleDict]:
    path = Path(filepath)
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines()
    modules: list[ModuleDict] = []
    cnt = [0]

    def nid(): cnt[0] += 1; return f"mod-{cnt[0]:03d}"

    def add(typ, label, lineno, anch_type, pattern, content="", level=None):
        modules.append({
            "id": nid(), "type": typ, "label": label,
            "anchor_line": lineno, "anchor_type": anch_type,
            "anchor_pattern": pattern, "content": content[:500],
            "level": level, "constraints": [],
        })

    # Track what we've already found on each line to avoid duplicates
    seen_on_line: dict[int, set[str]] = {}

    for lineno, line in enumerate(lines, start=1):
        s = line.strip()
        if not s or s.startswith("%"):
            continue
        seen = seen_on_line.setdefault(lineno, set())

        # \title{...} — also catches \title[short]{long}
        m = re.search(r'\\title\s*(?:\[[^\]]*\])?\s*\{', s)
        if m and 'title' not in seen:
            seen.add('title')
            add("title", "Title", lineno, "regex", r'\\title\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}', s)

        # \author{...}
        m = re.search(r'\\author\s*\{', s)
        if m and 'author' not in seen:
            seen.add('author')
            add("author", "Author", lineno, "regex", r'\\author\s*\{([^}]*)\}', s)

        # \section / \subsection / \subsubsection (with or without *)
        for cmd, lvl in SECTION_CMDS.items():
            m = re.search(rf'\\{cmd}\s*\{{\s*([^}}]*)', s)
            if m and f'section_{cmd}' not in seen:
                seen.add(f'section_{cmd}')
                label = m.group(1).strip()
                add("section", label, lineno, "regex",
                    rf'\\{cmd}\s*\{{([^}}]*)\}}', s, level=lvl)
                break

        # \bibliography{...}
        m = re.search(r'\\bibliography\s*\{', s)
        if m and 'bibliography' not in seen:
            seen.add('bibliography')
            add("bibliography", "References", lineno, "regex",
                r'\\bibliography\{([^}]*)\}', s)

    # Pass 2: environments (abstract, thebibliography, figure, table)
    for env_name, mod_type in [
        ("abstract", "abstract"), ("figure", "figure"), ("figure*", "figure"),
        ("table", "table"), ("table*", "table"),
        ("thebibliography", "bibliography"),
        ("acknowledgments", "acknowledgments"),
        ("acknowledgement", "acknowledgments"),
        ("keywords", "keywords"),
    ]:
        for i, m in enumerate(re.finditer(
            rf'\\begin\{{{re.escape(env_name)}\}}(.*?)\\end\{{{re.escape(env_name)}\}}',
            raw, re.DOTALL
        )):
            body = m.group(1)
            est_lineno = raw[:m.start()].count("\n") + 1
            env_id = f"{env_name}_{i}"
            if any(env_id in seen_on_line.get(l, set()) for l in range(est_lineno-2, est_lineno+2)):
                continue
            add(mod_type, env_name.replace("*", "").title(), est_lineno,
                "environment", rf'\\begin\{{{re.escape(env_name)}\}}.*?\\end\{{{re.escape(env_name)}\}}',
                body[:300])

    # Fallback: if nothing found, look for ANY section-like pattern
    if not modules:
        for lineno, line in enumerate(lines, start=1):
            s = line.strip()
            if re.search(r'\\(section|subsection|chapter)\*?\s*\{', s):
                for cmd, lvl in SECTION_CMDS.items():
                    m = re.search(rf'\\{cmd}\s*\{{([^}}]*)', s)
                    if m:
                        add("section", m.group(1).strip(), lineno, "regex",
                            rf'\\{cmd}\s*\{{([^}}]*)\}}', s, level=lvl)
                        break

    # Always sort by line number
    modules.sort(key=lambda m: m["anchor_line"])
    return modules
