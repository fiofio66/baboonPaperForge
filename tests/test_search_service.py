"""
Test search service — fuzzy matching, multi-result, LLM resolve.
"""

import pytest

from app.services.search_service import match_all, search_template_links, list_all_journals


# ---------------------------------------------------------------------------
# match_all: return all matches
# ---------------------------------------------------------------------------
def test_match_ieee_returns_multiple():
    results = match_all("ieee")
    assert len(results) >= 2  # IEEEtran + IEEEconf
    ids = [r["id"] for r in results]
    assert "ieee-tran" in ids
    assert "ieee-conf" in ids


def test_match_iotj_returns_ieee():
    """Abbreviation 'iotj' maps via alias 'ieee iotj'."""
    results = match_all("iotj")
    assert len(results) >= 1
    assert results[0]["id"] == "ieee-tran"


def test_match_eswa_returns_elsevier():
    """ESWA is an Elsevier journal alias."""
    results = match_all("eswa")
    assert len(results) >= 1
    assert results[0]["id"] == "elsevier"


def test_match_cvpr():
    results = match_all("cvpr")
    assert len(results) >= 1
    assert results[0]["id"] == "cvpr"


def test_match_neurips():
    results = match_all("neurips")
    assert len(results) >= 1
    assert results[0]["id"] == "neurips"


def test_match_unknown():
    assert match_all("xyznonexistent999") == []


def test_match_two_words():
    """Match 'ieee conference' should return IEEEconf."""
    results = match_all("ieee conference")
    assert len(results) >= 1


def test_list_all_journals():
    all_j = list_all_journals()
    assert len(all_j) >= 25


# ---------------------------------------------------------------------------
# URL generation
# ---------------------------------------------------------------------------
def test_search_ieee_returns_urls():
    results = search_template_links("ieee", "latex")
    assert len(results) >= 2
    assert all("tsinghua" in r["url"] or "ustc" in r["url"] for r in results)


def test_search_iotj_returns_urls():
    """Abbreviation should resolve and return IEEEtran."""
    results = search_template_links("iotj", "latex")
    assert len(results) >= 1
    assert results[0]["url"]


def test_search_unknown_graceful():
    results = search_template_links("FakeJournal99999", "latex")
    assert isinstance(results, list)
