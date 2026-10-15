"""Dashboard visualizations for SLR results."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
from pathlib import Path


def load_results(csv_path):
    """Load a results CSV, returning an empty DataFrame if missing."""
    p = Path(csv_path)
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p, encoding="utf-8")


def chart_papers_per_year(df):
    """Publication trend over time."""
    if df.empty or "year" not in df.columns:
        return None
    d = df[df["year"] > 0].copy()
    if d.empty:
        return None
    counts = d["year"].value_counts().sort_index().reset_index()
    counts.columns = ["Year", "Papers"]
    fig = px.bar(counts, x="Year", y="Papers", title="Papers per Year")
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def chart_papers_per_source(df):
    """Distribution across sources."""
    if df.empty or "source" not in df.columns:
        return None
    counts = df["source"].value_counts().reset_index()
    counts.columns = ["Source", "Papers"]
    fig = px.pie(counts, names="Source", values="Papers",
                 title="Papers per Source", hole=0.4)
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def chart_top_venues(df, top_n=10):
    """Top publication venues."""
    if df.empty or "venue" not in df.columns:
        return None
    d = df[df["venue"].notna() & (df["venue"].astype(str).str.strip() != "")]
    if d.empty:
        return None
    counts = d["venue"].value_counts().head(top_n).reset_index()
    counts.columns = ["Venue", "Papers"]
    counts = counts.iloc[::-1]
    fig = px.bar(counts, x="Papers", y="Venue", orientation="h",
                 title="Top " + str(top_n) + " Venues")
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def chart_top_authors(df, top_n=10):
    """Most frequent authors."""
    if df.empty or "authors" not in df.columns:
        return None
    counter = Counter()
    for row in df["authors"].dropna():
        for author in str(row).split(","):
            a = author.strip()
            if a:
                counter[a] += 1
    if not counter:
        return None
    top = counter.most_common(top_n)
    counts = pd.DataFrame(top, columns=["Author", "Papers"])
    counts = counts.iloc[::-1]
    fig = px.bar(counts, x="Papers", y="Author", orientation="h",
                 title="Top " + str(top_n) + " Authors")
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def chart_keyword_frequency(df, top_n=20):
    """Keyword frequency across titles and abstracts."""
    if df.empty:
        return None
    import re
    stopwords = {
        "the", "of", "and", "a", "to", "in", "for", "is", "on", "that",
        "by", "this", "with", "are", "as", "an", "be", "or", "from",
        "at", "it", "we", "can", "using", "based", "these", "which",
        "has", "have", "also", "such", "their", "than", "may", "more",
        "not", "but", "they", "was", "were", "will", "been", "into",
    }
    counter = Counter()
    for col in ["title", "abstract"]:
        if col not in df.columns:
            continue
        for text in df[col].dropna().astype(str):
            words = re.findall(r"[a-zA-Z]{3,}", text.lower())
            for w in words:
                if w not in stopwords:
                    counter[w] += 1
    if not counter:
        return None
    top = counter.most_common(top_n)
    counts = pd.DataFrame(top, columns=["Keyword", "Frequency"])
    counts = counts.iloc[::-1]
    fig = px.bar(counts, x="Frequency", y="Keyword", orientation="h",
                 title="Top " + str(top_n) + " Keywords")
    fig.update_layout(height=500, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def chart_year_source_heatmap(df):
    """Stacked bar: papers per year, colored by source."""
    if df.empty or "year" not in df.columns or "source" not in df.columns:
        return None
    d = df[df["year"] > 0].copy()
    if d.empty:
        return None
    grouped = d.groupby(["year", "source"]).size().reset_index(name="Papers")
    fig = px.bar(grouped, x="year", y="Papers", color="source",
                 title="Papers per Year by Source", barmode="stack")
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def summary_metrics(df):
    """Compute headline numbers for KPI cards."""
    if df.empty:
        return {"total": 0, "years": "n/a", "sources": 0, "venues": 0}
    total = len(df)
    years_with_data = df[df["year"] > 0]["year"]
    year_range = "n/a"
    if not years_with_data.empty:
        year_range = str(int(years_with_data.min())) + "-" + str(int(years_with_data.max()))
    sources = df["source"].nunique() if "source" in df.columns else 0
    venues = df["venue"].dropna().nunique() if "venue" in df.columns else 0
    return {"total": total, "years": year_range, "sources": sources, "venues": venues}
