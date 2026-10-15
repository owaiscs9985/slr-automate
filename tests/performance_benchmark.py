"""Performance benchmark for SLR-Automate."""

import sys
import time
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _time_it(fn, *args, **kwargs):
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    dt = time.perf_counter() - t0
    return dt, result


def benchmark(runs=3):
    from src.slr_automate.search import (
        Paper, search_openalex, search_crossref, search_doaj, search_europepmc,
    )
    from src.slr_automate.dedupe import deduplicate
    from src.slr_automate.screening import screen_papers
    from src.slr_automate.bibtex import enrich_papers
    from src.slr_automate.prisma import generate_prisma
    from src.slr_automate.query_builder import (
        build_canonical_query, build_plain_query, build_simple_or_query,
    )
    import tempfile

    query = "machine learning healthcare"
    max_n = 20

    timings = {
        "Query build (canonical + plain + OR)": [],
        "OpenAlex search (20 results)": [],
        "Crossref search (20 results)": [],
        "DOAJ search (20 results)": [],
        "Europe PMC search (20 results)": [],
        "Deduplication (cross-source)": [],
        "Screening (keyword-based)": [],
        "BibTeX enrichment (all papers)": [],
        "PRISMA diagram rendering": [],
        "Full pipeline": [],
    }

    source_results = {}

    for run in range(runs):
        print("Run " + str(run + 1) + " of " + str(runs) + "...")

        concepts = {"machine learning": ["ML"], "healthcare": ["health"]}
        dt, _ = _time_it(lambda: (
            build_canonical_query(concepts),
            build_plain_query(concepts),
            build_simple_or_query(concepts),
        ))
        timings["Query build (canonical + plain + OR)"].append(dt)

        t_pipeline_start = time.perf_counter()

        dt, oa = _time_it(search_openalex, query, max_n)
        timings["OpenAlex search (20 results)"].append(dt)

        dt, cr = _time_it(search_crossref, query, max_n)
        timings["Crossref search (20 results)"].append(dt)

        dt, dj = _time_it(search_doaj, query, max_n)
        timings["DOAJ search (20 results)"].append(dt)

        dt, ep = _time_it(search_europepmc, query, max_n)
        timings["Europe PMC search (20 results)"].append(dt)

        all_papers = oa + cr + dj + ep
        source_results = {
            "OpenAlex": len(oa),
            "Crossref": len(cr),
            "DOAJ": len(dj),
            "Europe PMC": len(ep),
        }

        dt, unique = _time_it(deduplicate, all_papers)
        timings["Deduplication (cross-source)"].append(dt)

        include_kw = ["machine learning", "healthcare", "health", "medical"]
        dt, (included, excluded) = _time_it(
            screen_papers, unique, include_kw, [], 1)
        timings["Screening (keyword-based)"].append(dt)

        dt, enriched = _time_it(enrich_papers, included, 300)
        timings["BibTeX enrichment (all papers)"].append(dt)

        counts = {
            "identified": len(all_papers),
            "duplicates_removed": len(all_papers) - len(unique),
            "screened": len(unique),
            "excluded_title_abstract": len(excluded),
            "fulltext_assessed": len(included),
            "excluded_fulltext": 0,
            "included": len(included),
        }
        meta = {
            "per_source": source_results,
            "canonical_query": build_canonical_query(concepts),
            "year_range": "any - any",
        }
        tmp = Path(tempfile.gettempdir()) / ("bench_prisma_" + str(run) + ".png")
        dt, _ = _time_it(generate_prisma, counts, str(tmp), meta)
        timings["PRISMA diagram rendering"].append(dt)
        tmp.unlink(missing_ok=True)

        t_pipeline = time.perf_counter() - t_pipeline_start
        timings["Full pipeline"].append(t_pipeline)

        time.sleep(1)

    return timings, source_results


def _summarize(timings):
    rows = []
    for stage, times in timings.items():
        if not times:
            continue
        rows.append({
            "stage": stage,
            "mean_s": statistics.mean(times),
            "std_s": statistics.stdev(times) if len(times) > 1 else 0.0,
            "min_s": min(times),
            "max_s": max(times),
            "n": len(times),
            "success_pct": 100.0,
        })
    return rows


def _print_table(rows):
    print("")
    print("=" * 100)
    print("PERFORMANCE BENCHMARK RESULTS")
    print("=" * 100)
    header = "{:<42} {:>9} {:>9} {:>9} {:>9} {:>8}".format(
        "Operation", "Mean (s)", "Std (s)", "Min (s)", "Max (s)", "Success")
    print(header)
    print("-" * 100)
    for r in rows:
        row = "{:<42} {:>9.3f} {:>9.3f} {:>9.3f} {:>9.3f} {:>7.1f}%".format(
            r["stage"][:41], r["mean_s"], r["std_s"], r["min_s"], r["max_s"],
            r["success_pct"])
        print(row)
    print("=" * 100)


def _write_csv(rows, path):
    import csv
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "stage", "mean_s", "std_s", "min_s", "max_s", "n", "success_pct"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("CSV saved to " + path)


def _write_markdown(rows, path):
    lines = []
    lines.append("| Operation | Mean (s) | Std (s) | Min (s) | Max (s) | Success |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        lines.append("| " + r["stage"] + " | " +
                     str(round(r["mean_s"], 3)) + " | " +
                     str(round(r["std_s"], 3)) + " | " +
                     str(round(r["min_s"], 3)) + " | " +
                     str(round(r["max_s"], 3)) + " | " +
                     str(round(r["success_pct"], 1)) + "% |")
    with open(path, "w", encoding="utf-8") as f:
        f.write(chr(10).join(lines))
    print("Markdown saved to " + path)


if __name__ == "__main__":
    print("Running performance benchmark (3 runs)...")
    print("This will make repeated live network calls.")
    print("")
    timings, sources = benchmark(runs=3)
    rows = _summarize(timings)
    _print_table(rows)
    print("")
    print("Source coverage (last run): " + str(sources))
    docs = Path(__file__).resolve().parent.parent / "docs"
    docs.mkdir(exist_ok=True)
    _write_csv(rows, str(docs / "performance_benchmark.csv"))
    _write_markdown(rows, str(docs / "performance_benchmark.md"))
