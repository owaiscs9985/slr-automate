"""Command-line interface for SLR-Automate."""

import argparse
import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime

from .search import (
    search_openalex,
    search_semantic_scholar,
    search_arxiv,
    search_crossref,
    search_doaj,
    search_europepmc,
)
from .dedupe import deduplicate
from .screening import screen_papers
from .prisma import generate_prisma
from .query_builder import build_canonical_query, build_plain_query, adapt_for_source
from .bibtex import enrich_papers, make_bibtex_entry


def _resolve_query(cfg):
    if "concepts" in cfg and cfg["concepts"]:
        concepts = cfg["concepts"]
        return build_canonical_query(concepts), build_plain_query(concepts)
    raw = cfg.get("query", "")
    return raw, raw


def _resolve_output_dir(cfg):
    """Return the actual output folder for this run (timestamped or not)."""
    base = Path(cfg.get("output_dir", "output"))
    use_ts = cfg.get("use_timestamp", True)
    if use_ts:
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return base / stamp
    return base


def run(config_path):
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    canonical_query, plain_query = _resolve_query(cfg)
    concepts = cfg.get("concepts")
    print("Canonical query: " + canonical_query)
    print("")

    max_per_source = cfg.get("max_per_source", 100)
    sources = cfg.get("sources", ["openalex", "crossref", "semantic_scholar", "arxiv"])
    out_dir = _resolve_output_dir(cfg)
    s2_key = cfg.get("semantic_scholar_api_key")
    include_kw = cfg.get("include_keywords", [])
    exclude_kw = cfg.get("exclude_keywords", [])
    min_matches = cfg.get("min_include_matches", 1)
    from_year = cfg.get("from_year")
    to_year = cfg.get("to_year")
    abstract_max_chars = cfg.get("abstract_max_chars", 300)
    out_dir.mkdir(parents=True, exist_ok=True)
    print("Output directory: " + str(out_dir))
    print("")

    if from_year or to_year:
        print("Year range: " + str(from_year or "any") + " - " + str(to_year or "any"))
        print("")

    all_papers = []
    per_source_counts = {}

    if "openalex" in sources:
        print("Searching OpenAlex...")
        q, params = adapt_for_source(canonical_query, plain_query, "openalex", from_year, to_year)
        oa = search_openalex(q, max_per_source, extra_params=params)
        per_source_counts["OpenAlex"] = len(oa)
        all_papers.extend(oa)

    if "crossref" in sources:
        print("Searching Crossref...")
        q, params = adapt_for_source(canonical_query, plain_query, "crossref", from_year, to_year)
        cr = search_crossref(q, max_per_source, extra_params=params)
        per_source_counts["Crossref"] = len(cr)
        all_papers.extend(cr)

    if "doaj" in sources:
        print("Searching DOAJ...")
        q, params = adapt_for_source(canonical_query, plain_query, "doaj", from_year, to_year, concepts=concepts)
        if from_year:
            params["from_year"] = from_year
        if to_year:
            params["to_year"] = to_year
        dj = search_doaj(q, max_per_source, extra_params=params)
        per_source_counts["DOAJ"] = len(dj)
        all_papers.extend(dj)

    if "europepmc" in sources:
        print("Searching Europe PMC...")
        q, params = adapt_for_source(canonical_query, plain_query, "europepmc", from_year, to_year, concepts=concepts)
        ep = search_europepmc(q, max_per_source, extra_params=params)
        per_source_counts["Europe PMC"] = len(ep)
        all_papers.extend(ep)

    if "semantic_scholar" in sources:
        print("Searching Semantic Scholar...")
        q, params = adapt_for_source(canonical_query, plain_query, "semantic_scholar", from_year, to_year)
        s2 = search_semantic_scholar(q, max_per_source, api_key=s2_key, extra_params=params)
        per_source_counts["Semantic Scholar"] = len(s2)
        all_papers.extend(s2)

    if "arxiv" in sources:
        print("Searching arXiv...")
        q, params = adapt_for_source(canonical_query, plain_query, "arxiv", from_year, to_year)
        ax = search_arxiv(q, max_per_source, extra_params=params)
        per_source_counts["arXiv"] = len(ax)
        all_papers.extend(ax)

    print("")
    print("Total records retrieved: " + str(len(all_papers)))
    print("Per source: " + str(per_source_counts))

    unique = deduplicate(all_papers)
    duplicates_removed = len(all_papers) - len(unique)
    print("After deduplication: " + str(len(unique)) + " (removed " + str(duplicates_removed) + ")")

    if include_kw or exclude_kw:
        print("Screening with " + str(len(include_kw)) + " include keywords (min " + str(min_matches) + ")...")
        included, excluded = screen_papers(unique, include_kw, exclude_kw, min_matches)
        print("Screening result: " + str(len(included)) + " included, " + str(len(excluded)) + " excluded")
    else:
        included = unique
        excluded = []

    for old in ["results.csv", "results.xlsx"]:
        old_path = out_dir / old
        if old_path.exists():
            old_path.unlink()

    # Enrich included papers with citation keys and bibtex entries
    enriched_included = enrich_papers(included, abstract_max_chars)
    enriched_all = enrich_papers(unique, abstract_max_chars)
    full_included = enrich_papers(included, 0)

    cols = ["title", "authors", "year", "source", "venue", "doi", "url",
            "abstract", "citation_key", "bibtex_entry"]

    df_all = pd.DataFrame(enriched_all)
    df_all = df_all[[c for c in cols if c in df_all.columns]]
    df_all.to_csv(out_dir / "results_all.csv", index=False, encoding="utf-8")

    df_inc = pd.DataFrame(enriched_included)
    df_inc = df_inc[[c for c in cols if c in df_inc.columns]]
    df_inc.to_csv(out_dir / "results_included.csv", index=False, encoding="utf-8")

    df_full = pd.DataFrame(full_included)
    df_full = df_full[[c for c in cols if c in df_full.columns]]
    df_full.to_csv(out_dir / "results_included_full.csv", index=False, encoding="utf-8")

    # Multi-sheet Excel: main + bibtex-only sheet
    with pd.ExcelWriter(out_dir / "results_included.xlsx", engine="openpyxl") as writer:
        df_inc.to_excel(writer, sheet_name="results", index=False)
        df_inc[["citation_key", "bibtex_entry"]].to_excel(writer, sheet_name="bibtex", index=False)

    # Standalone .bib file
    bib_lines = []
    for p in included:
        d = p.to_dict()
        bib_lines.append(make_bibtex_entry(d))
        bib_lines.append("")
    with open(out_dir / "results_included.bib", "w", encoding="utf-8") as bf:
        bf.write("\n".join(bib_lines))

    print("Saved: results_all.csv, results_included.csv, results_included_full.csv")
    print("Saved: results_included.xlsx (sheets: results, bibtex)")
    print("Saved: results_included.bib (" + str(len(included)) + " entries)")

    meta_path = out_dir / "query_metadata.txt"
    with open(meta_path, "w", encoding="utf-8") as mf:
        mf.write("Canonical query:\n" + canonical_query + "\n\n")
        mf.write("Sources:\n" + str(sources) + "\n\n")
        mf.write("Year range: " + str(from_year) + " - " + str(to_year) + "\n\n")
        mf.write("Per-source counts:\n" + str(per_source_counts) + "\n\n")
        mf.write("Duplicates removed: " + str(duplicates_removed) + "\n")
        mf.write("Included after screening: " + str(len(included)) + "\n")
        mf.write("Abstract max chars: " + str(abstract_max_chars) + "\n")
    print("Saved: query_metadata.txt")

    # Export the exact config used (reproducibility)
    config_copy_path = out_dir / "config_used.yaml"
    with open(config_copy_path, "w", encoding="utf-8") as cf:
        yaml.safe_dump(cfg, cf, allow_unicode=True, sort_keys=False)
    print("Saved: config_used.yaml")

    counts = {
        "identified": len(all_papers),
        "duplicates_removed": duplicates_removed,
        "screened": len(unique),
        "excluded_title_abstract": len(excluded),
        "fulltext_assessed": len(included),
        "excluded_fulltext": 0,
        "included": len(included),
    }
    year_label = "any - any"
    if from_year or to_year:
        year_label = str(from_year or "any") + " - " + str(to_year or "any")
    active_sources = {k: v for k, v in per_source_counts.items() if v > 0}
    prisma_metadata = {
        "per_source": active_sources,
        "canonical_query": canonical_query,
        "year_range": year_label,
    }
    generate_prisma(counts, str(out_dir / "prisma_flow.png"), metadata=prisma_metadata)


def main():
    parser = argparse.ArgumentParser(description="SLR-Automate")
    parser.add_argument("config", help="Path to YAML config file")
    args = parser.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
