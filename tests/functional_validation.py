"""Functional validation of SLR-Automate components.

Runs each component in isolation and produces a pass/fail table
suitable for the SoftwareX paper (Section 3.2, Table 5).
"""

import sys
import time
import traceback
import importlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _record(results, test_id, objective, expected, passed, notes=""):
    results.append({
        "id": test_id,
        "objective": objective,
        "expected": expected,
        "result": "Pass" if passed else "Fail",
        "notes": notes,
    })


def run_all_tests():
    results = []

    # ---------- FT-01: query_builder canonical query ----------
    try:
        from src.slr_automate.query_builder import build_canonical_query
        concepts = {"machine learning": ["ML"], "medical imaging": ["MRI"]}
        q = build_canonical_query(concepts)
        ok = ('"machine learning"' in q and '"ML"' in q and " AND " in q)
        _record(results, "FT-01", "Query builder - canonical boolean",
                "Valid boolean with quotes and AND", ok)
    except Exception as e:
        _record(results, "FT-01", "Query builder - canonical boolean",
                "Valid boolean", False, str(e))

    # ---------- FT-02: query_builder plain query ----------
    try:
        from src.slr_automate.query_builder import build_plain_query
        q = build_plain_query({"machine learning": ["ML"]})
        ok = ("machine learning" in q and "ML" in q and "(" not in q)
        _record(results, "FT-02", "Query builder - plain keyword",
                "Space-joined keywords, no booleans", ok)
    except Exception as e:
        _record(results, "FT-02", "Query builder - plain keyword",
                "Plain string", False, str(e))

    # ---------- FT-03: query_builder simple OR (DOAJ/EPMC) ----------
    try:
        from src.slr_automate.query_builder import build_simple_or_query
        q = build_simple_or_query({"a": [], "b": []})
        ok = (q == '"a" OR "b"')
        _record(results, "FT-03", "Query builder - simple OR",
                '"a" OR "b"', ok)
    except Exception as e:
        _record(results, "FT-03", "Query builder - simple OR",
                "OR string", False, str(e))

    # ---------- FT-04: query_builder per-source adaptation ----------
    try:
        from src.slr_automate.query_builder import adapt_for_source
        q, params = adapt_for_source("CANON", "PLAIN", "doaj", 2018, 2024,
                                     concepts={"a": []})
        ok = (q == '"a"' and params.get("from_year") == 2018)
        _record(results, "FT-04", "Query builder - per-source adaptation",
                "DOAJ receives simple OR + year params", ok)
    except Exception as e:
        _record(results, "FT-04", "Query builder - per-source adaptation",
                "Source-adapted query", False, str(e))

    # ---------- FT-05: deduplication by DOI ----------
    try:
        from src.slr_automate.search import Paper
        from src.slr_automate.dedupe import deduplicate
        p1 = Paper("A", "X", 2020, "10.1/abc", "", "Test", "", "")
        p2 = Paper("A duplicate", "Y", 2020, "10.1/abc", "", "Test", "", "")
        p3 = Paper("B", "Z", 2021, "10.1/xyz", "", "Test", "", "")
        result = deduplicate([p1, p2, p3])
        ok = (len(result) == 2)
        _record(results, "FT-05", "Deduplication - by DOI",
                "Identical DOI merged", ok,
                "Input 3, output " + str(len(result)))
    except Exception as e:
        _record(results, "FT-05", "Deduplication - by DOI",
                "Merge by DOI", False, str(e))

    # ---------- FT-06: deduplication by normalized title ----------
    try:
        from src.slr_automate.search import Paper
        from src.slr_automate.dedupe import deduplicate
        p1 = Paper("Neural Networks for Imaging", "X", 2020, "", "", "Test", "", "")
        p2 = Paper("neural networks for imaging", "Y", 2020, "", "", "Test", "", "")
        result = deduplicate([p1, p2])
        ok = (len(result) == 1)
        _record(results, "FT-06", "Deduplication - by title",
                "Case-insensitive title merge", ok)
    except Exception as e:
        _record(results, "FT-06", "Deduplication - by title",
                "Merge by title", False, str(e))

    # ---------- FT-07: screening inclusion ----------
    try:
        from src.slr_automate.search import Paper
        from src.slr_automate.screening import screen_papers
        papers = [
            Paper("Deep learning MRI", "X", 2020, "", "neural imaging", "Test", "", ""),
            Paper("Editorial note", "Y", 2020, "", "editorial", "Test", "", ""),
        ]
        inc, exc = screen_papers(papers, ["deep learning"], ["editorial"], 1)
        ok = (len(inc) == 1 and len(exc) == 1)
        _record(results, "FT-07", "Screening - include/exclude",
                "1 in, 1 out", ok)
    except Exception as e:
        _record(results, "FT-07", "Screening - include/exclude",
                "Keyword rules", False, str(e))

    # ---------- FT-08: screening min-match ----------
    try:
        from src.slr_automate.search import Paper
        from src.slr_automate.screening import screen_papers
        papers = [
            Paper("Machine learning for medical imaging",
                  "X", 2020, "", "machine learning imaging research", "Test", "", ""),
            Paper("Machine learning only",
                  "Y", 2020, "", "machine learning approaches", "Test", "", ""),
        ]
        inc, exc = screen_papers(papers, ["machine learning", "imaging"], [], 2)
        ok = (len(inc) == 1)
        _record(results, "FT-08", "Screening - minimum match threshold",
                "Only 2-match paper included", ok)
    except Exception as e:
        _record(results, "FT-08", "Screening - minimum match threshold",
                "Enforce threshold", False, str(e))

    # ---------- FT-09: citation key generation ----------
    try:
        from src.slr_automate.bibtex import make_citation_key
        p = {"authors": "Owais Khan", "year": 2024, "title": "Reinforcement Learning for WSN"}
        k = make_citation_key(p)
        ok = (k.startswith("khan2024") and "reinforcement" in k)
        _record(results, "FT-09", "BibTeX - citation key format",
                "khan2024reinforcement", ok, "Generated: " + k)
    except Exception as e:
        _record(results, "FT-09", "BibTeX - citation key format",
                "citation key", False, str(e))

    # ---------- FT-10: BibTeX entry generation ----------
    try:
        from src.slr_automate.bibtex import make_bibtex_entry
        p = {"authors": "Jane Doe", "year": 2023, "title": "Test",
             "venue": "Journal X", "doi": "10.1/x", "url": "http://x", "source": "OpenAlex"}
        entry = make_bibtex_entry(p)
        ok = (entry.startswith("@article{") and "title = {" in entry
              and "Jane Doe" in entry and entry.strip().endswith("}"))
        _record(results, "FT-10", "BibTeX - @article entry",
                "Valid @article block", ok)
    except Exception as e:
        _record(results, "FT-10", "BibTeX - @article entry",
                "BibTeX entry", False, str(e))

    # ---------- FT-11: abstract truncation default ----------
    try:
        from src.slr_automate.bibtex import truncate_abstract
        text = "a" * 500
        t = truncate_abstract(text, 300)
        ok = (len(t) == 303 and t.endswith("..."))
        _record(results, "FT-11", "Abstract truncation - default 300 chars",
                "Truncated with ellipsis", ok)
    except Exception as e:
        _record(results, "FT-11", "Abstract truncation - default 300 chars",
                "Truncate correctly", False, str(e))

    # ---------- FT-12: abstract truncation disabled ----------
    try:
        from src.slr_automate.bibtex import truncate_abstract
        text = "a" * 500
        t = truncate_abstract(text, 0)
        ok = (len(t) == 500)
        _record(results, "FT-12", "Abstract truncation - disabled",
                "Full text preserved when 0", ok)
    except Exception as e:
        _record(results, "FT-12", "Abstract truncation - disabled",
                "No truncation", False, str(e))

    # ---------- FT-13: PRISMA diagram generation ----------
    try:
        from src.slr_automate.prisma import generate_prisma
        import tempfile
        tmp = Path(tempfile.gettempdir()) / "test_prisma.png"
        counts = {
            "identified": 200, "duplicates_removed": 20, "screened": 180,
            "excluded_title_abstract": 72, "fulltext_assessed": 108,
            "excluded_fulltext": 0, "included": 108,
        }
        meta = {
            "per_source": {"OpenAlex": 50, "Crossref": 50, "DOAJ": 50, "Europe PMC": 50},
            "canonical_query": "(test) AND (query)",
            "year_range": "2018 - 2024",
        }
        generate_prisma(counts, str(tmp), metadata=meta)
        ok = tmp.exists() and tmp.stat().st_size > 10000
        _record(results, "FT-13", "PRISMA diagram rendering",
                "PNG > 10 KB produced", ok,
                "Size: " + str(tmp.stat().st_size) + " bytes" if tmp.exists() else "missing")
        tmp.unlink(missing_ok=True)
    except Exception as e:
        _record(results, "FT-13", "PRISMA diagram rendering",
                "PNG produced", False, str(e))

    # ---------- FT-14: search connectors importable ----------
    try:
        from src.slr_automate.search import (
            search_openalex, search_crossref, search_doaj,
            search_europepmc, search_semantic_scholar, search_arxiv,
        )
        ok = all(callable(f) for f in [search_openalex, search_crossref,
                                       search_doaj, search_europepmc,
                                       search_semantic_scholar, search_arxiv])
        _record(results, "FT-14", "Search connectors - all 6 importable",
                "All callables present", ok)
    except Exception as e:
        _record(results, "FT-14", "Search connectors - all 6 importable",
                "All present", False, str(e))

    # ---------- FT-15: OpenAlex live query ----------
    try:
        from src.slr_automate.search import search_openalex
        t0 = time.time()
        r = search_openalex("machine learning", 5)
        dt = time.time() - t0
        ok = (len(r) > 0 and dt < 30)
        _record(results, "FT-15", "OpenAlex live search",
                "Returns >0 papers", ok,
                "n=" + str(len(r)) + ", " + str(round(dt, 2)) + "s")
    except Exception as e:
        _record(results, "FT-15", "OpenAlex live search",
                "Returns papers", False, str(e))

    # ---------- FT-16: Crossref live query ----------
    try:
        from src.slr_automate.search import search_crossref
        t0 = time.time()
        r = search_crossref("machine learning", 5)
        dt = time.time() - t0
        ok = (len(r) > 0 and dt < 30)
        _record(results, "FT-16", "Crossref live search",
                "Returns >0 papers", ok,
                "n=" + str(len(r)) + ", " + str(round(dt, 2)) + "s")
    except Exception as e:
        _record(results, "FT-16", "Crossref live search",
                "Returns papers", False, str(e))

    # ---------- FT-17: DOAJ live query ----------
    try:
        from src.slr_automate.search import search_doaj
        t0 = time.time()
        r = search_doaj("machine learning", 5)
        dt = time.time() - t0
        ok = (len(r) > 0 and dt < 30)
        _record(results, "FT-17", "DOAJ live search",
                "Returns >0 papers", ok,
                "n=" + str(len(r)) + ", " + str(round(dt, 2)) + "s")
    except Exception as e:
        _record(results, "FT-17", "DOAJ live search",
                "Returns papers", False, str(e))

    # ---------- FT-18: Europe PMC live query ----------
    try:
        from src.slr_automate.search import search_europepmc
        t0 = time.time()
        r = search_europepmc("machine learning", 5)
        dt = time.time() - t0
        ok = (len(r) > 0 and dt < 30)
        _record(results, "FT-18", "Europe PMC live search",
                "Returns >0 papers", ok,
                "n=" + str(len(r)) + ", " + str(round(dt, 2)) + "s")
    except Exception as e:
        _record(results, "FT-18", "Europe PMC live search",
                "Returns papers", False, str(e))

    return results


def _print_table(results):
    print("")
    print("=" * 110)
    print("FUNCTIONAL VALIDATION RESULTS")
    print("=" * 110)
    header = "{:<7} {:<45} {:<32} {:<6}".format("Test ID", "Objective", "Expected Result", "Result")
    print(header)
    print("-" * 110)
    for r in results:
        row = "{:<7} {:<45} {:<32} {:<6}".format(
            r["id"], r["objective"][:44], r["expected"][:31], r["result"])
        print(row)
    print("=" * 110)
    total = len(results)
    passed = sum(1 for r in results if r["result"] == "Pass")
    print("Total: " + str(passed) + "/" + str(total) + " passed")
    print("=" * 110)


def _write_csv(results, path):
    import csv
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "objective", "expected", "result", "notes"])
        w.writeheader()
        for r in results:
            w.writerow(r)
    print("CSV saved to " + path)


def _write_markdown(results, path):
    lines = []
    lines.append("| Test ID | Objective | Expected Result | Result |")
    lines.append("|---|---|---|---|")
    for r in results:
        lines.append("| " + r["id"] + " | " + r["objective"] + " | " + r["expected"] + " | " + r["result"] + " |")
    with open(path, "w", encoding="utf-8") as f:
        f.write(chr(10).join(lines))
    print("Markdown saved to " + path)


if __name__ == "__main__":
    print("Running functional validation...")
    print("(This will make live network calls to OpenAlex, Crossref, DOAJ, Europe PMC)")
    print("")
    results = run_all_tests()
    _print_table(results)

    docs = Path(__file__).resolve().parent.parent / "docs"
    docs.mkdir(exist_ok=True)
    _write_csv(results, str(docs / "functional_validation.csv"))
    _write_markdown(results, str(docs / "functional_validation.md"))
