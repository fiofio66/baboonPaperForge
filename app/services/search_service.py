"""
Template search service.

Searches the web for official LaTeX/Word template download links
using duckduckgo_search (free, no API key required).
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from ddgs import DDGS

# Known official template domains — boosted in ranking
_OFFICIAL_DOMAINS: dict[str, list[str]] = {
    "ieee": ["ieee.org", "ieeexplore.ieee.org", "ctan.org"],
    "acm": ["acm.org", "ctan.org"],
    "elsevier": ["elsevier.com", "ctan.org"],
    "springer": ["springer.com", "ctan.org"],
    "nature": ["nature.com"],
    "science": ["science.org", "aaas.org"],
    "arxiv": ["arxiv.org"],
    "acs": ["acs.org", "pubs.acs.org"],
    "wiley": ["wiley.com"],
    "iop": ["iop.org", "ioppublishing.org"],
    "osa": ["osa.org", "optica.org", "opg.optica.org"],
    "spie": ["spie.org"],
    "sage": ["sagepub.com", "sagepublications.com"],
}

# Archive-like file extensions
_ARCHIVE_EXT = re.compile(r"\.(zip|tar\.gz|tgz|tar\.bz2|tar\.xz)$", re.IGNORECASE)

# URL patterns that indicate a template/resource page
_TEMPLATE_KEYWORDS = re.compile(
    r"template|latex|cls|sty|manuscript|submission|author.guide|"
    r"word.template|format|style.file|article.class|paper.kit",
    re.IGNORECASE,
)


def _score_candidate(url: str, journal_name: str) -> int:
    """Score a candidate URL. Higher = more likely the right template."""
    score = 0
    url_lower = url.lower()
    parsed = urlparse(url)

    # Archive file direct link → gold
    if _ARCHIVE_EXT.search(url_lower):
        score += 50

    # Domain boost
    jn_lower = journal_name.lower()
    for keyword, domains in _OFFICIAL_DOMAINS.items():
        if keyword in jn_lower:
            for d in domains:
                if d in parsed.netloc:
                    score += 30
                    break

    # Template-related keywords in URL
    if _TEMPLATE_KEYWORDS.search(url_lower):
        score += 20

    # CTAN is a trusted LaTeX repository
    if "ctan.org" in parsed.netloc:
        score += 25

    # GitHub repos with "template" in name
    if "github.com" in parsed.netloc and "template" in url_lower:
        score += 15

    # Penalize social media / general sites
    low_quality = {"reddit.com", "twitter.com", "facebook.com", "youtube.com",
                   "stackexchange.com", "stackoverflow.com", "quora.com"}
    if any(lq in parsed.netloc for lq in low_quality):
        score -= 30

    return score


async def search_template_links(
    journal_name: str, template_format: str = "latex", max_results: int = 10
) -> list[dict[str, str]]:
    """Search the web for template download links.

    Args:
        journal_name: e.g. "IEEE Internet of Things Journal"
        template_format: "latex" or "docx"
        max_results: number of raw results to fetch from the search engine

    Returns:
        List of dicts with ``url``, ``title``, ``score``, sorted by score desc.
    """
    fmt_label = "LaTeX" if template_format.lower() in ("latex", "tex") else "Word"
    query = f'{journal_name} {fmt_label} template download'

    candidates: list[dict[str, str]] = []

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception:
        # duckduckgo may rate-limit; return empty gracefully
        return []

    for r in results:
        url = r.get("href", "")
        if not url:
            continue
        score = _score_candidate(url, journal_name)
        candidates.append({
            "url": url,
            "title": r.get("title", ""),
            "snippet": r.get("body", ""),
            "score": score,
        })

    # Sort by score descending, then filter negatives
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return [c for c in candidates if c["score"] >= 0]
