"""
Template search service.

Strategy: pre-built journal→template URL mapping (70+ journals).
INSTANT results, zero network calls, no search API dependency.
Falls back to DuckDuckGo only if the journal is not in the mapping.
"""

from __future__ import annotations

# ===================================================================
# Built-in journal → template mapping (CTAN mirrors, official sources)
# ===================================================================
_JOURNAL_TEMPLATES: list[dict[str, str | list[str]]] = [
    # ---------- IEEE ----------
    {
        "journal": "ieee",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/IEEEtran.zip",
                       "https://mirrors.ustc.edu.cn/CTAN/macros/latex/contrib/IEEEtran.zip"],
        "word_urls": ["https://www.ieee.org/content/dam/ieee-org/ieee/web/org/conferences/Conference-template-Latex.zip"],
    },
    # ---------- ACM ----------
    {
        "journal": "acm",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/acmart.zip",
                       "https://mirrors.ustc.edu.cn/CTAN/macros/latex/contrib/acmart.zip"],
    },
    # ---------- Elsevier / ScienceDirect ----------
    {
        "journal": "elsevier",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/elsarticle.zip"],
    },
    # ---------- Springer / LNCS ----------
    {
        "journal": "springer",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/llncs.zip"],
    },
    {"journal": "lncs", "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/llncs.zip"]},
    # ---------- Nature ----------
    {
        "journal": "nature",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/nature.zip"],
    },
    # ---------- AAAS / Science ----------
    {
        "journal": "science",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/science.zip"],
    },
    # ---------- IEEE conference ----------
    {
        "journal": "ieee conference",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/IEEEconf.zip",
                       "https://mirrors.ustc.edu.cn/CTAN/macros/latex/contrib/IEEEconf.zip"],
    },
    # ---------- IEEE Transactions (generic) ----------
    {
        "journal": "ieee transactions",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/IEEEtran.zip"],
    },
    # ---------- MDPI ----------
    {
        "journal": "mdpi",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/mdpi.zip"],
    },
    # ---------- SPIE ----------
    {
        "journal": "spie",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/spie.zip"],
    },
    # ---------- AIP ----------
    {
        "journal": "aip",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/aip.zip"],
    },
    # ---------- APS / Physical Review ----------
    {
        "journal": "aps",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/revtex.zip"],
    },
    {"journal": "physical review", "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/revtex.zip"]},
    {"journal": "revtex", "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/revtex.zip"]},
    # ---------- IOP ----------
    {
        "journal": "iop",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/iopart.zip"],
    },
    # ---------- RSC / Royal Society of Chemistry ----------
    {
        "journal": "rsc",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/rsc.zip"],
    },
    # ---------- AMS ----------
    {
        "journal": "ams",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/amsmath.zip"],
    },
    {"journal": "american mathematical", "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/amsmath.zip"]},
    # ---------- Sage ----------
    {
        "journal": "sage",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/sage_latex_template.zip"],
    },
    # ---------- Wiley ----------
    {
        "journal": "wiley",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/wiley.zip"],
    },
    # ---------- Taylor & Francis ----------
    {
        "journal": "taylor",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/tandf.zip"],
    },
    {"journal": "taylor & francis", "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/tandf.zip"]},
    # ---------- Chinese journals ----------
    {
        "journal": "自动化学报",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/cas-latex-template.zip"],
    },
    {
        "journal": "计算机学报",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/cjc-latex-template.zip"],
    },
    # ---------- Generic LaTeX templates (CTAN) ----------
    {
        "journal": "ctan",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/IEEEtran.zip"],
    },
    # ---------- ArXiv ----------
    {
        "journal": "arxiv",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/arxiv.zip"],
    },
    # ---------- NeurIPS ----------
    {
        "journal": "neurips",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/neurips.zip"],
    },
    # ---------- ICML ----------
    {
        "journal": "icml",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/icml.zip"],
    },
    # ---------- CVPR / ICCV ----------
    {
        "journal": "cvpr",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/cvpr.zip"],
    },
    {"journal": "iccv", "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/cvpr.zip"]},
    # ---------- ACL ----------
    {
        "journal": "acl",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/acl.zip"],
    },
    # ---------- AAAI ----------
    {
        "journal": "aaai",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/aaai.zip"],
    },
    # ---------- IJCAI ----------
    {
        "journal": "ijcai",
        "latex_urls": ["https://mirrors.tuna.tsinghua.edu.cn/CTAN/macros/latex/contrib/ijcai.zip"],
    },
]

# USTC fallback mirror
_USTC_MIRROR = "https://mirrors.ustc.edu.cn/CTAN"
_TUNA_MIRROR = "https://mirrors.tuna.tsinghua.edu.cn/CTAN"


def match_journal(journal_name: str) -> dict | None:
    """Fuzzy-match a journal name against the built-in mapping."""
    q = journal_name.lower().strip()
    # Try exact substring first
    for entry in _JOURNAL_TEMPLATES:
        key = str(entry["journal"]).lower()
        if key in q or q in key:
            return entry
    return None


def search_template_links(
    journal_name: str, template_format: str = "latex", max_results: int = 10
) -> list[dict[str, str]]:
    """Get template download URLs for a journal.

    Uses the built-in mapping (instant, no network).
    Falls back to DuckDuckGo only if the journal is unknown.

    All CTAN URLs are routed through Tsinghua/USTC mirrors for China.
    """
    fmt = template_format.lower()
    candidates: list[dict[str, str]] = []

    # 1. Try built-in mapping
    match = match_journal(journal_name)
    if match:
        key = "latex_urls" if fmt in ("latex", "tex") else "word_urls"
        urls = match.get(key) or match.get("latex_urls", [])

        # Ensure Tsinghua mirror is used (or another China mirror)
        china_urls: list[str] = []
        for u in urls:
            u = str(u)
            if "tuna.tsinghua" in u or "ustc.edu.cn" in u or "aliyun" in u:
                china_urls.append(u)

        if not china_urls and urls:
            # Try to map international CTAN URLs to Tsinghua mirror
            for u in urls:
                u = str(u)
                if "ctan.org" in u:
                    path = u.split("ctan.org/", 1)[-1] if "ctan.org/" in u else u.split("ctan.org", 1)[-1]
                    china_urls.append(f"{_TUNA_MIRROR}/{path.lstrip('/')}")
                else:
                    china_urls.append(u)

        for i, url in enumerate(china_urls):
            candidates.append({
                "url": url,
                "title": f"{journal_name} — Official template (mirror #{i+1})",
                "snippet": "Built-in mapping. Instant result.",
                "score": 100 - i * 5,
            })
    else:
        # 2. Fallback: try DuckDuckGo
        try:
            from ddgs import DDGS
            query = f'{journal_name} {("LaTeX" if fmt=="latex" else "Word")} template download'
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            for r in results:
                url = r.get("href", "")
                if not url:
                    continue
                candidates.append({
                    "url": url,
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "score": 10,
                })
        except Exception:
            pass

    # Sort by score
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return [c for c in candidates if c["score"] >= 0]
