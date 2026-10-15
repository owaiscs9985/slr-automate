"""BibTeX and citation key generation for paper records."""

import re
from typing import Dict


def make_citation_key(paper_dict: Dict) -> str:
    """Generate a BibTeX-style citation key: firstauthorYEARfirstword.

    Examples:
      Khan et al 2024 'Reinforcement Learning...' -> khan2024reinforcement
      Smith 2020 'A Study of Networks'            -> smith2020study
      Unknown author, no year                     -> unknownXXXXuntitled
    """
    authors = paper_dict.get("authors") or ""
    first_author = authors.split(",")[0].strip() if authors else ""
    first_author = first_author.split(" ")[-1] if first_author else "unknown"
    first_author = re.sub(r"[^a-zA-Z]", "", first_author).lower() or "unknown"

    year = str(paper_dict.get("year") or "XXXX")

    title = paper_dict.get("title") or ""
    first_word = ""
    for word in re.findall(r"[a-zA-Z]{3,}", title.lower()):
        if word not in {"the", "and", "for", "with", "from", "using", "based", "study", "novel"}:
            first_word = word
            break
    if not first_word:
        first_word = "untitled"

    return first_author + year + first_word


def make_bibtex_entry(paper_dict: Dict) -> str:
    """Build a BibTeX @article entry from a paper record."""
    key = make_citation_key(paper_dict)

    title = (paper_dict.get("title") or "").strip()
    authors = (paper_dict.get("authors") or "").strip()
    year = paper_dict.get("year") or ""
    venue = (paper_dict.get("venue") or "").strip()
    doi = (paper_dict.get("doi") or "").strip()
    url = (paper_dict.get("url") or "").strip()
    source = (paper_dict.get("source") or "").strip()

    def esc(s):
        return str(s).replace("{", "\\{").replace("}", "\\}")

    lines = ["@article{" + key + ","]
    if title:
        lines.append("  title = {" + esc(title) + "},")
    if authors:
        lines.append("  author = {" + esc(authors) + "},")
    if year:
        lines.append("  year = {" + str(year) + "},")
    if venue:
        lines.append("  journal = {" + esc(venue) + "},")
    if doi:
        lines.append("  doi = {" + esc(doi) + "},")
    if url:
        lines.append("  url = {" + esc(url) + "},")
    if source:
        lines.append("  note = {Retrieved via " + esc(source) + "},")

    lines.append("}")
    return "\n".join(lines)


def truncate_abstract(text, max_chars=300):
    """Truncate abstract to max_chars, adding ellipsis. 0 or negative = no truncation."""
    if text is None:
        return ""
    text = str(text).strip()
    if max_chars is None or max_chars <= 0:
        return text
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


def enrich_papers(papers, abstract_max_chars=300):
    """Add citation_key, bibtex_entry, and truncated abstract to each paper dict."""
    enriched = []
    for p in papers:
        d = p.to_dict()
        d["abstract"] = truncate_abstract(d.get("abstract"), abstract_max_chars)
        d["citation_key"] = make_citation_key(d)
        d["bibtex_entry"] = make_bibtex_entry(d)
        enriched.append(d)
    return enriched
