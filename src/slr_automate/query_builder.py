"""Query builder: converts structured concepts into boolean search strings."""

from typing import Dict, List, Optional


def build_canonical_query(concepts: Dict[str, List[str]]) -> str:
    """Build a canonical boolean query string for display and documentation.

    concepts = {
        "concept 1": ["synonym a", "synonym b"],
        "concept 2": ["synonym c"],
    }
    Returns: ("concept 1" OR "synonym a" OR "synonym b") AND ("concept 2" OR "synonym c")
    """
    groups = []
    for concept, synonyms in concepts.items():
        terms = [concept] + [s for s in synonyms if s]
        quoted = ['"' + t.strip() + '"' for t in terms if t.strip()]
        if quoted:
            groups.append("(" + " OR ".join(quoted) + ")")
    return " AND ".join(groups)


def build_plain_query(concepts: Dict[str, List[str]]) -> str:
    """Build a plain keyword query for APIs that don't support boolean.

    Just concatenates all terms with spaces.
    """
    terms = []
    for concept, synonyms in concepts.items():
        terms.append(concept)
        terms.extend(synonyms)
    return " ".join(t.strip() for t in terms if t.strip())


def build_simple_or_query(concepts):
    """Build a simple OR query from just the concept names (no synonyms).

    Useful for APIs like DOAJ that treat space-separated terms as AND.
    Example: ("reinforcement learning" OR "MAC protocol" OR "wireless sensor network")
    """
    names = [c.strip() for c in concepts.keys() if c.strip()]
    if not names:
        return ""
    quoted = ['"' + n + '"' for n in names]
    return " OR ".join(quoted)


def build_openalex_filter(from_year: Optional[int], to_year: Optional[int]) -> str:
    """OpenAlex uses filter syntax: publication_year:2020-2024"""
    if from_year and to_year:
        return "publication_year:" + str(from_year) + "-" + str(to_year)
    if from_year:
        return "publication_year:>" + str(from_year - 1)
    if to_year:
        return "publication_year:<" + str(to_year + 1)
    return ""


def build_crossref_filter(from_year: Optional[int], to_year: Optional[int]) -> Dict[str, str]:
    """Crossref uses from-pub-date and until-pub-date params."""
    filters = {}
    if from_year:
        filters["from-pub-date"] = str(from_year) + "-01-01"
    if to_year:
        filters["until-pub-date"] = str(to_year) + "-12-31"
    return filters


def build_arxiv_year_filter(from_year: Optional[int], to_year: Optional[int]) -> str:
    """arXiv supports submittedDate:[YYYYMMDD TO YYYYMMDD] in search_query."""
    if not from_year and not to_year:
        return ""
    f = str(from_year or 1991) + "0101"
    t = str(to_year or 2100) + "1231"
    return "submittedDate:[" + f + " TO " + t + "]"


def adapt_for_source(
    canonical_query: str,
    plain_query: str,
    source: str,
    from_year: Optional[int] = None,
    to_year: Optional[int] = None,
    concepts: dict = None,
):
    """Return (query_string, extra_params) suited for the target source.

    extra_params is a dict of additional params to pass to the API.
    """
    if source == "openalex":
        filt = build_openalex_filter(from_year, to_year)
        params = {"filter": filt} if filt else {}
        return canonical_query, params

    if source == "crossref":
        params = build_crossref_filter(from_year, to_year)
        return plain_query, params

    if source == "arxiv":
        year_filter = build_arxiv_year_filter(from_year, to_year)
        if year_filter:
            combined = "(" + canonical_query + ") AND " + year_filter
        else:
            combined = "(" + canonical_query + ")"
        return combined, {}

    if source == "semantic_scholar":
        return plain_query, {"year": _s2_year_str(from_year, to_year)}

    if source == "doaj":
        if concepts:
            q = build_simple_or_query(concepts)
        else:
            q = plain_query
        return q, {"from_year": from_year, "to_year": to_year}

    if source == "europepmc":
        if concepts:
            q = build_simple_or_query(concepts)
        else:
            q = plain_query
        return q, {"from_year": from_year, "to_year": to_year}

    return plain_query, {}


def _s2_year_str(from_year: Optional[int], to_year: Optional[int]) -> str:
    """Semantic Scholar year filter format: '2020-2024' or '2020-' or '-2024'."""
    if from_year and to_year:
        return str(from_year) + "-" + str(to_year)
    if from_year:
        return str(from_year) + "-"
    if to_year:
        return "-" + str(to_year)
    return ""
