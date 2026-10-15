# SLR-Automate

An open-source Python pipeline for automated systematic literature reviews.
SLR-Automate builds validated boolean queries from structured concepts,
searches multiple open-access databases in parallel, deduplicates results,
applies keyword-based screening, and produces reproducible output artifacts
including PRISMA 2020 flow diagrams and BibTeX citation files.

## Features

- Multi-source search: OpenAlex, Crossref, DOAJ, Europe PMC (all free, no
  API key required). Optional: Semantic Scholar and arXiv.
- Structured query builder: define research concepts with synonyms and get
  an auto-generated boolean query, adapted per source.
- Year-range filter: restrict retrieval to any publication window.
- Cross-source deduplication by DOI and normalized title.
- Keyword-based screening with a configurable minimum-match threshold.
- PRISMA 2020 flow diagram: auto-generated, publication-ready.
- BibTeX export: standalone .bib file plus citation keys embedded in the
  CSV and Excel output.
- Abstract truncation: control output file size; full abstracts preserved
  in a separate file.
- Timestamped outputs: every run goes to its own folder.
- Reproducible: the exact configuration is saved as config_used.yaml.
- Interactive GUI: Streamlit interface with Pipeline, Dashboard, and
  Results tabs.
- Dashboard: six bibliometric charts.

## Installation

    git clone https://github.com/owaiscs9985/slr-automate.git
    cd slr-automate
    python -m venv venv
    source venv/bin/activate          # Windows: venv\Scripts\activate
    pip install -r requirements.txt

Python 3.10 or newer is required.

## Quick start — Command line

Create a config file (see examples/example_query.yaml):

    concepts:
      reinforcement learning:
        - RL
        - Q-learning
      MAC protocol:
        - medium access control
      wireless sensor network:
        - WSN

    from_year: 2018
    to_year: 2024
    max_per_source: 50
    sources:
      - openalex
      - crossref
      - doaj
      - europepmc
    output_dir: output
    use_timestamp: true
    abstract_max_chars: 300

    include_keywords:
      - reinforcement learning
      - MAC protocol
      - wireless sensor network
    exclude_keywords:
      - editorial
      - erratum
    min_include_matches: 2

Run the pipeline:

    python -m src.slr_automate.cli examples/example_query.yaml

Each run creates a timestamped folder under output/ containing:

    results_all.csv              All deduplicated papers
    results_included.csv         Screened papers (truncated abstracts)
    results_included_full.csv    Screened papers (full abstracts)
    results_included.xlsx        Two-sheet Excel (results + bibtex)
    results_included.bib         BibTeX file for reference managers
    prisma_flow.png              PRISMA 2020 flow diagram
    query_metadata.txt           Human-readable run summary
    config_used.yaml             Exact configuration for reproducibility

## Quick start — Streamlit GUI

    streamlit run app.py

The GUI opens at http://localhost:8501 with three tabs:

- Pipeline — configure concepts, sources, year range, and screening rules
- Dashboard — six bibliometric charts rendered with Plotly
- Results — searchable table, downloads, and PRISMA diagram

## Data sources

    Source             API key      Coverage                          Notes
    OpenAlex           Not req.     250M+ works, all disciplines      Recommended
    Crossref           Not req.     150M+ works, all disciplines      Recommended
    DOAJ               Not req.     Peer-reviewed open-access journals Recommended
    Europe PMC         Not req.     33M+ life sciences publications   Reliable
    Semantic Scholar   Optional     200M+ papers                      Free tier is rate-limited
    arXiv              Not req.     2M+ preprints                     Aggressively rate-limited

## Testing

    python tests/functional_validation.py
    python -m pytest tests/ -v
    python tests/performance_benchmark.py

## Citation

If you use SLR-Automate in your research, please cite:

    Khan, O. (2026). SLR-Automate: An open-source pipeline for
    automated systematic literature reviews (v0.1.0).
    https://github.com/owaiscs9985/slr-automate

See CITATION.cff for machine-readable citation metadata.

## License

MIT — see LICENSE for details.

## Contact

Owais Khan — owaiscs@gmail.com
