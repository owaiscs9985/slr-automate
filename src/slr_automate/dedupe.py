"""Deduplicate papers across sources by DOI and normalized title."""

import re
from typing import List
from .search import Paper


def normalize_title(title: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    title = title.lower()
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def _merge_missing(target: Paper, source: Paper) -> None:
    """Fill in missing fields on target from source."""
    for field in ["doi", "abstract", "venue", "url", "year"]:
        if not getattr(target, field) and getattr(source, field):
            setattr(target, field, getattr(source, field))


def deduplicate(papers: List[Paper]) -> List[Paper]:
    """Remove duplicates by DOI first, then by normalized title."""
    seen_dois = {}
    seen_titles = {}
    unique = []

    for p in papers:
        doi_key = p.doi.strip().lower() if p.doi else None
        title_key = normalize_title(p.title) if p.title else None

        if doi_key and doi_key in seen_dois:
            _merge_missing(seen_dois[doi_key], p)
            continue

        if title_key and title_key in seen_titles:
            _merge_missing(seen_titles[title_key], p)
            continue

        unique.append(p)
        if doi_key:
            seen_dois[doi_key] = p
        if title_key:
            seen_titles[title_key] = p

    return unique
