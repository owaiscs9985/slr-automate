# SLR-Automate User Guide

This guide covers advanced usage beyond the quick-start in the README.

## Configuration reference

SLR-Automate reads a YAML config file. Every field is optional except for
one of query or concepts.

### Query input (choose one)

Structured concepts (recommended):

    concepts:
      concept name:
        - synonym 1
        - synonym 2
      another concept:
        - synonym

The pipeline generates a boolean query:

    ("concept name" OR "synonym 1" OR "synonym 2")
    AND ("another concept" OR "synonym")

Raw query string:

    query: "reinforcement learning MAC protocol wireless sensor networks"

### Filtering

    Field             Type    Default   Purpose
    from_year         int     none      Lower bound on publication year
    to_year           int     none      Upper bound on publication year
    max_per_source    int     100       Maximum records per source
    sources           list    all 6     Which sources to query

### Screening

    Field                  Type    Default   Purpose
    include_keywords       list    []        Papers must contain at least N
    exclude_keywords       list    []        Papers with these are dropped
    min_include_matches    int     1         Minimum include keywords to match

### Output

    Field                Type    Default   Purpose
    output_dir           str     output    Parent folder for outputs
    use_timestamp        bool    true      Timestamped subfolder per run
    abstract_max_chars   int     300       Truncate abstracts to N chars

## Query builder

The query builder transforms structured concepts into source-specific
queries:

    Source             Query form
    OpenAlex           Canonical boolean
    Crossref           Plain keyword string
    DOAJ               Simple OR of concept names
    Europe PMC         Simple OR of concept names
    Semantic Scholar   Plain keyword string
    arXiv              Canonical boolean + submittedDate filter

## Sources and rate limits

    Source             Rate limit                    Recommended spacing
    OpenAlex           Polite pool (100k/day)        No limit
    Crossref           ~50 req/s                     No limit
    DOAJ               Generous                      No limit
    Europe PMC         Generous                      No limit
    Semantic Scholar   Shared pool without key       Space 5+ min apart
    arXiv              1 req / 3 s                   Space 15+ min apart

SLR-Automate handles rate limits gracefully: when a source returns HTTP 429
or 503, it respects the Retry-After header and retries with exponential
backoff. If retries are exhausted, the source is skipped and the pipeline
continues.

## Screening rules

Given include_keywords, exclude_keywords, and min_include_matches:

1. If a paper matches any exclude keyword, it is excluded.
2. If no include keywords are defined, all papers pass.
3. Otherwise, a paper is included only if it matches at least
   min_include_matches include keywords.

Keyword matching is case-insensitive and searches title and abstract.

## Output artifacts

    File                         Contents
    results_all.csv              All deduplicated papers
    results_included.csv         Screened, truncated abstracts, keys
    results_included_full.csv    Same with full abstracts
    results_included.xlsx        Two sheets: results + bibtex
    results_included.bib         Standalone BibTeX file
    prisma_flow.png              PRISMA 2020 diagram
    query_metadata.txt           Human-readable run summary
    config_used.yaml             Exact config used

## Reproducibility

Every run is fully reproducible:

1. The exact config is saved as config_used.yaml in the run folder.
2. Outputs are timestamped and never overwrite previous runs.
3. All sources are open-access and free.
4. query_metadata.txt records the canonical query and per-source counts.

To rerun a past search, use its config_used.yaml:

    python -m src.slr_automate.cli output/2026-10-15_12-00-00/config_used.yaml

## Troubleshooting

PermissionError when writing Excel:
Close the file in Excel, or use use_timestamp: true.

Semantic Scholar returns 0 results:
The free tier is shared. Request a free API key at
https://www.semanticscholar.org/product/api and add it as
semantic_scholar_api_key in the config.

arXiv returns 0 results:
arXiv rate-limits aggressive callers. Wait 15+ minutes between runs.

DOAJ returns 0 results:
DOAJ treats space-separated terms as AND. Use simple concept names to
increase recall.

No output for a specific source:
The source may be temporarily unreachable. Check query_metadata.txt for
per-source counts and the terminal log for retry messages.
