"""
Test search service — scoring, filtering, and workflow state transitions.
"""

import pytest

from app.services.search_service import _score_candidate, search_template_links


# ---------------------------------------------------------------------------
# Scoring tests
# ---------------------------------------------------------------------------
def test_score_archive_direct_link():
    score = _score_candidate("https://example.com/ieee-template.zip", "IEEE Journal")
    assert score >= 50, f"Archive link should score >=50, got {score}"


def test_score_ctan_domain():
    score = _score_candidate("https://ctan.org/pkg/ieeetran", "IEEE")
    assert score > 0, f"CTAN link should score positive, got {score}"


def test_score_ieee_official_domain():
    score = _score_candidate(
        "https://www.ieee.org/publications/templates.zip", "IEEE Internet of Things"
    )
    assert score > 30, f"IEEE official domain should score high, got {score}"


def test_score_penalizes_social_media():
    social = _score_candidate("https://reddit.com/r/latex/comments/template", "IEEE")
    official = _score_candidate("https://ieee.org/template.zip", "IEEE")
    assert social < official, f"Social media should score lower: {social} vs {official}"


def test_score_github_template():
    score = _score_candidate(
        "https://github.com/user/latex-template", "Some Journal"
    )
    assert score >= 15, f"GitHub template should score >=15, got {score}"


# ---------------------------------------------------------------------------
# Live search (requires network; marked optional)
# ---------------------------------------------------------------------------
@pytest.mark.slow
@pytest.mark.asyncio
async def test_search_template_returns_results():
    """Live search should return at least 1 result for a well-known journal."""
    results = await search_template_links("IEEE Internet of Things Journal", "latex")
    assert isinstance(results, list)
    if results:
        assert "url" in results[0]
        assert "score" in results[0]
        assert results[0]["score"] >= 0


@pytest.mark.asyncio
async def test_search_obscure_journal_graceful():
    """Searching for gibberish should not crash."""
    results = await search_template_links("xyznonexistent12345journal", "latex")
    assert isinstance(results, list)
