"""Automated first-pass screening of papers by keyword rules."""

from typing import List, Tuple
from .search import Paper


def screen_papers(
    papers: List[Paper],
    include_keywords: List[str] = None,
    exclude_keywords: List[str] = None,
    min_include_matches: int = 1,
) -> Tuple[List[Paper], List[Paper]]:
    """Split papers into (included, excluded) based on keyword rules.

    Rules:
    - If a paper matches any exclude keyword -> excluded
    - If a paper matches >= min_include_matches include keywords -> included
    - If include_keywords is empty -> include everything not excluded
    - Otherwise -> excluded
    """
    include_keywords = [k.lower() for k in (include_keywords or [])]
    exclude_keywords = [k.lower() for k in (exclude_keywords or [])]

    included = []
    excluded = []

    for p in papers:
        text = (p.title + " " + (p.abstract or "")).lower()

        if any(k in text for k in exclude_keywords):
            excluded.append(p)
            continue

        if not include_keywords:
            included.append(p)
            continue

        matches = sum(1 for k in include_keywords if k in text)
        if matches >= min_include_matches:
            included.append(p)
        else:
            excluded.append(p)

    return included, excluded
