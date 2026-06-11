"""
Test search service — built-in mapping + fallback.
"""

import pytest

from app.services.search_service import match_journal, search_template_links


# ---------------------------------------------------------------------------
# Built-in mapping
# ---------------------------------------------------------------------------
def test_match_ieee():
    assert match_journal("IEEE Internet of Things Journal") is not None


def test_match_acm():
    assert match_journal("ACM Transactions on Graphics") is not None


def test_match_elsevier():
    assert match_journal("Elsevier Information Sciences") is not None


def test_match_springer():
    assert match_journal("Springer Nature") is not None


def test_match_nature():
    assert match_journal("Nature Communications") is not None


def test_match_neurips():
    assert match_journal("NeurIPS 2025") is not None


def test_match_cvpr():
    assert match_journal("CVPR 2024") is not None


def test_match_ieee_substring():
    """Fuzzy matching: 'ieee' is a substring of the query."""
    assert match_journal("IEEE Journal of Something") is not None


def test_match_unknown_journal():
    """An obscure journal not in our mapping."""
    assert match_journal("Obscure Unknown Journal 12345") is None


# ---------------------------------------------------------------------------
# URL generation
# ---------------------------------------------------------------------------
def test_search_ieee_returns_urls():
    results = search_template_links("IEEE Internet of Things Journal", "latex")
    assert len(results) > 0
    # Should use Tsinghua mirror
    assert any("tsinghua" in r["url"] or "ustc" in r["url"] for r in results)
    assert results[0]["score"] >= 90


def test_search_unknown_fallsback_gracefully():
    """Even for unknown journals, should return [] without crashing."""
    results = search_template_links("Totally Fake Journal 99999", "latex")
    assert isinstance(results, list)


def test_search_word_format():
    results = search_template_links("IEEE Conference", "docx")
    assert isinstance(results, list)
