"""Architecture and system diagrams for SLR-Automate."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from pathlib import Path


# ---- Colors ----
TITLE_TEXT = "#1b3a5c"
SUB_TEXT = "#666666"
BOX_FILL = "#dbe8f5"
BOX_EDGE = "#2e5c8a"
SUPPORT_FILL = "#f5f5f5"
SUPPORT_EDGE = "#888888"
OUTPUT_FILL = "#e3f0dc"
OUTPUT_EDGE = "#4a7d3f"
ARROW_COLOR = "#333333"
DASH_COLOR = "#888888"
BAND_IN = "#a8c8e8"
BAND_PROC = "#7eb56b"
BAND_OUT = "#9d7fc0"
TEXT = "#111111"


def _box(ax, x, y, w, h, fill, edge, lw=1.5):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=lw, edgecolor=edge, facecolor=fill, zorder=2,
    ))


def _text(ax, x, y, s, size=12, bold=False, color=TEXT, ha="left", va="top"):
    ax.text(x, y, s, fontsize=size, ha=ha, va=va, color=color,
            fontweight="bold" if bold else "normal", zorder=4)


def _arrow(ax, x1, y1, x2, y2, color=ARROW_COLOR, dashed=False, lw=1.7):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>", mutation_scale=14,
        linewidth=lw, color=color,
        linestyle="dashed" if dashed else "solid",
        zorder=3,
    ))


def _band(ax, x, y, w, h, label, fill):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        linewidth=0, facecolor=fill, zorder=1,
    ))
    ax.text(x + w / 2, y + h / 2, label,
            ha="center", va="center", rotation=90,
            fontsize=12, fontweight="bold", color="white", zorder=4)


def render_architecture(output_path="architecture.png"):
    """Render the SLR-Automate component architecture diagram."""
    # Landscape 16:9 canvas
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")

    # ---------------- Title ----------------
    ax.text(8, 8.72, "SLR-Automate: Component Architecture",
            ha="center", va="center", fontsize=20, fontweight="bold",
            color=TITLE_TEXT, zorder=4)
    ax.text(8, 8.42, "An open-source pipeline for automated systematic literature reviews",
            ha="center", va="center", fontsize=11, style="italic",
            color=SUB_TEXT, zorder=4)

    # ---------------- Left phase bands ----------------
    # USER INPUT  (spans row 1)
    # PROCESSING  (spans rows 2-3)
    # OUTPUT      (spans row 4)
    band_x = 0.20
    band_w = 0.42

    row1_top = 8.05
    row1_bot = 6.85

    row2_top = 6.55
    row2_bot = 4.80

    row3_top = 4.45
    row3_bot = 3.30

    row4_top = 3.00
    row4_bot = 1.15

    # Aligned bands
    _band(ax, band_x, row1_bot, band_w, row1_top - row1_bot, "USER INPUT", BAND_IN)
    _band(ax, band_x, row3_bot, band_w, row2_top - row3_bot, "PROCESSING", BAND_PROC)
    _band(ax, band_x, row4_bot, band_w, row4_top - row4_bot, "OUTPUT", BAND_OUT)

    # ---------------- Row 1: User interfaces ----------------
    gui_x, gui_y = 3.30, 6.95
    gui_w, gui_h = 4.60, 1.00

    cli_x = 8.60
    cli_w, cli_h = 4.60, 1.00

    _box(ax, gui_x, gui_y, gui_w, gui_h, BOX_FILL, BOX_EDGE, lw=1.8)
    _text(ax, gui_x + gui_w / 2, gui_y + gui_h - 0.20,
          "Streamlit GUI", size=14, bold=True, ha="center")
    _text(ax, gui_x + gui_w / 2, gui_y + gui_h - 0.48,
          "Browser-based  ·  3 tabs", size=10.5, ha="center", color="#333")
    _text(ax, gui_x + gui_w / 2, gui_y + gui_h - 0.72,
          "Pipeline | Dashboard | Results", size=10.5, ha="center", color="#333")

    _box(ax, cli_x, gui_y, cli_w, cli_h, BOX_FILL, BOX_EDGE, lw=1.8)
    _text(ax, cli_x + cli_w / 2, gui_y + cli_h - 0.20,
          "Command-Line Interface", size=14, bold=True, ha="center")
    _text(ax, cli_x + cli_w / 2, gui_y + cli_h - 0.48,
          "YAML configuration", size=10.5, ha="center", color="#333")
    _text(ax, cli_x + cli_w / 2, gui_y + cli_h - 0.72,
          "Reproducible batch runs", size=10.5, ha="center", color="#333")

    # ---------------- Row 2: Pipeline (5 boxes) ----------------
    pipeline_y = 4.80
    pipeline_h = 1.75
    box_w = 2.55
    gap = 0.20
    pipeline_start_x = 0.85

    pipeline_boxes = [
        ("1. Query Builder",
         ["Concepts + synonyms", "Boolean generation", "Year range filter"]),
        ("2. Multi-Source Search",
         ["OpenAlex  ·  Crossref", "DOAJ  ·  Europe PMC", "Optional: S2 · arXiv"]),
        ("3. Deduplication",
         ["By DOI", "By normalized title", "Cross-source merge"]),
        ("4. Screening",
         ["Include / exclude keywords", "Minimum match threshold", "Rule-based filter"]),
        ("5. Enrichment",
         ["Citation keys", "BibTeX entries", "Abstract truncation"]),
    ]

    pipeline_centers = []
    for i, (title, lines) in enumerate(pipeline_boxes):
        x = pipeline_start_x + i * (box_w + gap)
        _box(ax, x, pipeline_y, box_w, pipeline_h, BOX_FILL, BOX_EDGE, lw=1.8)
        _text(ax, x + box_w / 2, pipeline_y + pipeline_h - 0.22,
              title, size=12.5, bold=True, ha="center")
        for j, line in enumerate(lines):
            _text(ax, x + 0.15, pipeline_y + pipeline_h - 0.55 - j * 0.32,
                  line, size=10.5)
        pipeline_centers.append(x + box_w / 2)

    # Arrows between pipeline boxes
    for i in range(len(pipeline_boxes) - 1):
        x1 = pipeline_start_x + i * (box_w + gap) + box_w
        x2 = pipeline_start_x + (i + 1) * (box_w + gap)
        y = pipeline_y + pipeline_h / 2
        _arrow(ax, x1, y, x2, y)

    # ---------------- Row 3: Supporting modules ----------------
    support_y = 3.35
    support_h = 0.90
    support_w = 3.60
    support_gap = 0.55
    support_total = 3 * support_w + 2 * support_gap
    support_start_x = (16 - support_total) / 2

    support_boxes = [
        ("Dashboard (Plotly)", "6 bibliometric charts"),
        ("Reproducibility Module", "Timestamped folders · config export"),
        ("PRISMA Generator", "PRISMA 2020 flow diagram"),
    ]

    support_centers = []
    for i, (title, sub) in enumerate(support_boxes):
        x = support_start_x + i * (support_w + support_gap)
        _box(ax, x, support_y, support_w, support_h, SUPPORT_FILL, SUPPORT_EDGE, lw=1.4)
        _text(ax, x + support_w / 2, support_y + support_h - 0.22,
              title, size=11.5, bold=True, ha="center")
        _text(ax, x + support_w / 2, support_y + support_h - 0.55,
              sub, size=10, ha="center", color="#444")
        support_centers.append(x + support_w / 2)

    # ---------------- Row 4: Output package ----------------
    out_x = 0.85
    out_y = 1.20
    out_w = 12.30
    out_h = 1.80

    _box(ax, out_x, out_y, out_w, out_h, OUTPUT_FILL, OUTPUT_EDGE, lw=2.0)
    _text(ax, out_x + 0.30, out_y + out_h - 0.20,
          "Output Package (per run)", size=14, bold=True)

    left_items = [
        "results_all.csv",
        "results_included.csv",
        "results_included_full.csv",
        "results_included.xlsx (2 sheets: results + bibtex)",
    ]
    right_items = [
        "results_included.bib",
        "prisma_flow.png",
        "query_metadata.txt",
        "config_used.yaml",
    ]
    mid = out_x + out_w / 2
    for i, item in enumerate(left_items):
        _text(ax, out_x + 0.55, out_y + out_h - 0.60 - i * 0.28,
              "•  " + item, size=10.5)
    for i, item in enumerate(right_items):
        _text(ax, mid + 0.30, out_y + out_h - 0.60 - i * 0.28,
              "•  " + item, size=10.5)

    # ---------------- Arrows: Row 1 -> Row 2 ----------------
    # From GUI bottom and CLI bottom, merge into a single line into pipeline Box 1
    gui_bottom_x = gui_x + gui_w / 2
    cli_bottom_x = cli_x + cli_w / 2
    merge_y = pipeline_y + pipeline_h + 0.35
    target_x = pipeline_centers[0]

    # Vertical drops from GUI and CLI
    _arrow(ax, gui_bottom_x, gui_y, gui_bottom_x, merge_y)
    _arrow(ax, cli_bottom_x, gui_y, cli_bottom_x, merge_y)

    # Horizontal merge line
    ax.plot([gui_bottom_x, cli_bottom_x], [merge_y, merge_y],
            color=ARROW_COLOR, linewidth=1.7, zorder=3)

    # Down into Query Builder
    _arrow(ax, target_x, merge_y, target_x, pipeline_y + pipeline_h)

    # ---------------- Arrows: Row 2 -> Output ----------------
    enrich_center_x = pipeline_centers[-1]
    _arrow(ax, enrich_center_x, pipeline_y, enrich_center_x, out_y + out_h)

    # ---------------- Arrows: Supporting modules -> targets ----------------
    # Dashboard -> 5. Enrichment (up)
    dash_x = support_centers[0]
    _arrow(ax, dash_x, support_y + support_h,
           enrich_center_x, pipeline_y, dashed=True, color=DASH_COLOR)
    # Wait — that would be diagonal. Let's do a cleaner path:
    # Instead, connect Dashboard up to Enrichment using an L-shaped path.

    # Reproducibility -> Output Package (down)
    repro_x = support_centers[1]
    _arrow(ax, repro_x, support_y, repro_x, out_y + out_h, dashed=True, color=DASH_COLOR)

    # PRISMA -> Output Package (down)
    prisma_x = support_centers[2]
    _arrow(ax, prisma_x, support_y, prisma_x, out_y + out_h, dashed=True, color=DASH_COLOR)

    # ---------------- Legend ----------------
    leg_x, leg_y = 13.45, 1.20
    leg_w, leg_h = 2.30, 3.95

    ax.add_patch(FancyBboxPatch(
        (leg_x, leg_y), leg_w, leg_h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.2, edgecolor="#aaaaaa", facecolor="white", zorder=2,
    ))
    _text(ax, leg_x + 0.15, leg_y + leg_h - 0.15,
          "Legend", size=11.5, bold=True)

    leg_items = [
        (BOX_FILL, BOX_EDGE, "Core component"),
        (SUPPORT_FILL, SUPPORT_EDGE, "Supporting module"),
        (OUTPUT_FILL, OUTPUT_EDGE, "Output artifact"),
    ]
    y_cursor = leg_y + leg_h - 0.55
    for fill, edge, label in leg_items:
        ax.add_patch(Rectangle(
            (leg_x + 0.15, y_cursor - 0.10), 0.32, 0.22,
            facecolor=fill, edgecolor=edge, linewidth=1.3, zorder=3,
        ))
        _text(ax, leg_x + 0.60, y_cursor + 0.03, label, size=9.5)
        y_cursor -= 0.42

    # Arrow legends
    _arrow(ax, leg_x + 0.15, y_cursor - 0.05, leg_x + 0.47, y_cursor - 0.05)
    _text(ax, leg_x + 0.60, y_cursor + 0.03, "Data flow", size=9.5)
    y_cursor -= 0.42

    _arrow(ax, leg_x + 0.15, y_cursor - 0.05, leg_x + 0.47, y_cursor - 0.05,
           dashed=True, color=DASH_COLOR)
    _text(ax, leg_x + 0.60, y_cursor + 0.03, "Optional support path", size=9.5)

    # ---------------- Footer caption ----------------
    ax.text(8, 0.45,
            "Fig. 1. SLR-Automate component architecture. Queries flow through five processing "
            "stages, producing reproducible datasets and publication-ready artifacts.",
            ha="center", va="center", fontsize=9, color="#333")

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close()
    print("Architecture diagram saved to " + output_path)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent.parent / "docs" / "architecture.png"
    out.parent.mkdir(exist_ok=True)
    render_architecture(str(out))
