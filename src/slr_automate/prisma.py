"""PRISMA 2020 flow diagram (simplified, automation-scope-aware)."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from datetime import datetime


# ---- Palette (matches the reference PRISMA template) ----
BLUE_BG = "#dbe8f5"
BLUE_EDGE = "#2e5c8a"
BLUE_BAND = "#7fa8d0"
GREEN_BG = "#e3f0dc"
GREEN_EDGE = "#4a7d3f"
GREEN_BAND = "#9ec98f"
PURPLE_BG = "#eadcf2"
PURPLE_EDGE = "#6c4a94"
PURPLE_BAND = "#a98fc4"
YELLOW_BG = "#fdf3d0"
YELLOW_EDGE = "#c9a227"
GREY_TEXT = "#444444"
TITLE_BG = "#1b3a5c"


def _box(ax, x, y, w, h, lines, facecolor, edgecolor,
         fontsize=9.5, title_size=10.5, title_bold=True):
    """Draw a box with an optional bold title line and normal sub-lines."""
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.5,
        edgecolor=edgecolor,
        facecolor=facecolor,
        zorder=2,
    )
    ax.add_patch(rect)

    n = len(lines)
    if n == 0:
        return
    line_gap = h / (n + 1)
    for i, line in enumerate(lines):
        y_pos = y + h - (i + 1) * line_gap
        is_title = (i == 0)
        ax.text(
            x + 0.15, y_pos, line,
            ha="left", va="center",
            fontsize=title_size if is_title else fontsize,
            color="#1a1a1a",
            fontweight="bold" if (is_title and title_bold) else "normal",
            zorder=3,
        )


def _arrow(ax, x1, y1, x2, y2, color="#333333", dashed=False, lw=1.6):
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>",
        mutation_scale=14,
        linewidth=lw,
        color=color,
        linestyle="dashed" if dashed else "solid",
        zorder=1,
    )
    ax.add_patch(arrow)


def generate_prisma(counts, output_path="prisma_flow.png", metadata=None):
    """Render a simplified PRISMA 2020 flow diagram with source breakdown."""
    metadata = metadata or {}
    per_source = metadata.get("per_source", {})
    canonical_query = metadata.get("canonical_query", "")
    year_range = metadata.get("year_range", "")

    # Landscape canvas: 14 x 9 units
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis("off")

    # ============ Header band ============
    header = FancyBboxPatch(
        (0.15, 8.15), 13.7, 0.75,
        boxstyle="round,pad=0.02,rounding_size=0.1",
        linewidth=0, facecolor=TITLE_BG, zorder=2,
    )
    ax.add_patch(header)
    ax.text(7, 8.68, "PRISMA 2020 Flow Diagram",
            ha="center", va="center", fontsize=17, fontweight="bold",
            color="white", zorder=3)
    ax.text(7, 8.32, "Identification, screening, and inclusion of studies",
            ha="center", va="center", fontsize=10, color="#cdd9e6",
            zorder=3)

    # Metadata line under header
    meta_parts = []
    if year_range:
        meta_parts.append("Period: " + year_range)
    meta_parts.append("Generated: " + datetime.now().strftime("%Y-%m-%d"))
    ax.text(7, 7.92, "  |  ".join(meta_parts),
            ha="center", va="center", fontsize=8.5, color=GREY_TEXT)

    if canonical_query:
        q = canonical_query if len(canonical_query) < 150 else canonical_query[:147] + "..."
        ax.text(7, 7.68, "Query: " + q,
                ha="center", va="center", fontsize=7.5, color="#666666")

    # ============ Left phase bands ============
    band_x = 0.25
    band_w = 0.55

    # Identification band
    id_y, id_h = 5.60, 1.85
    rect = FancyBboxPatch((band_x, id_y), band_w, id_h,
                          boxstyle="round,pad=0.02,rounding_size=0.08",
                          linewidth=0, facecolor=BLUE_BAND, zorder=2)
    ax.add_patch(rect)
    ax.text(band_x + band_w / 2, id_y + id_h / 2, "Identification",
            ha="center", va="center", rotation=90,
            fontsize=11, fontweight="bold", color="white", zorder=3)

    # Screening band
    scr_y, scr_h = 3.30, 2.10
    rect = FancyBboxPatch((band_x, scr_y), band_w, scr_h,
                          boxstyle="round,pad=0.02,rounding_size=0.08",
                          linewidth=0, facecolor=GREEN_BAND, zorder=2)
    ax.add_patch(rect)
    ax.text(band_x + band_w / 2, scr_y + scr_h / 2, "Screening",
            ha="center", va="center", rotation=90,
            fontsize=11, fontweight="bold", color="white", zorder=3)

    # Included band
    inc_band_y, inc_band_h = 1.45, 1.60
    rect = FancyBboxPatch((band_x, inc_band_y), band_w, inc_band_h,
                          boxstyle="round,pad=0.02,rounding_size=0.08",
                          linewidth=0, facecolor=PURPLE_BAND, zorder=2)
    ax.add_patch(rect)
    ax.text(band_x + band_w / 2, inc_band_y + inc_band_h / 2, "Included",
            ha="center", va="center", rotation=90,
            fontsize=11, fontweight="bold", color="white", zorder=3)

    # ============ Central column ============
    col_x = 1.10
    col_w = 6.20
    col_center = col_x + col_w / 2

    # --- Identification box ---
    ident_y, ident_h = 5.70, 1.70
    source_lines = ["Records identified from:"]
    for name, cnt in per_source.items():
        source_lines.append("    " + str(name) + "  (n = " + str(cnt) + ")")
    source_lines.append("    Total  (n = " + str(counts["identified"]) + ")")

    # Manually lay out source lines with proper spacing
    rect = FancyBboxPatch((col_x, ident_y), col_w, ident_h,
                          boxstyle="round,pad=0.02,rounding_size=0.08",
                          linewidth=1.5, edgecolor=BLUE_EDGE,
                          facecolor=BLUE_BG, zorder=2)
    ax.add_patch(rect)

    n_lines = len(source_lines)
    line_gap = ident_h / (n_lines + 1)
    for i, line in enumerate(source_lines):
        y_pos = ident_y + ident_h - (i + 1) * line_gap
        is_title = (i == 0)
        is_total = line.strip().startswith("Total")
        ax.text(col_x + 0.2, y_pos, line,
                ha="left", va="center",
                fontsize=9.5 if not is_title else 10.5,
                color="#1a1a1a",
                fontweight="bold" if (is_title or is_total) else "normal",
                zorder=3)

    # --- Records removed before screening (right side) ---
    rmv_x = 8.10
    rmv_w = 5.55
    rmv_y, rmv_h = 5.70, 1.70
    rmv_lines = [
        "Records removed before screening:",
        "    Duplicate records removed  (n = " + str(counts["duplicates_removed"]) + ")",
        "    Records removed for other reasons  (n = 0)",
    ]
    rect = FancyBboxPatch((rmv_x, rmv_y), rmv_w, rmv_h,
                          boxstyle="round,pad=0.02,rounding_size=0.08",
                          linewidth=1.5, edgecolor=YELLOW_EDGE,
                          facecolor=YELLOW_BG, zorder=2)
    ax.add_patch(rect)
    n2 = len(rmv_lines)
    gap2 = rmv_h / (n2 + 1)
    for i, line in enumerate(rmv_lines):
        y_pos = rmv_y + rmv_h - (i + 1) * gap2
        is_title = (i == 0)
        ax.text(rmv_x + 0.2, y_pos, line,
                ha="left", va="center",
                fontsize=10.5 if is_title else 9.5,
                color="#1a1a1a",
                fontweight="bold" if is_title else "normal",
                zorder=3)

    # Arrow: identification -> removed
    _arrow(ax, col_x + col_w, ident_y + ident_h / 2,
           rmv_x, rmv_y + rmv_h / 2, color="#666666")

    # --- Records screened ---
    screened_y, screened_h = 3.75, 1.35
    _box(ax, col_x, screened_y, col_w, screened_h,
         ["Records screened",
          "    n = " + str(counts["screened"])],
         facecolor=GREEN_BG, edgecolor=GREEN_EDGE)

    # Arrow: identified -> screened
    _arrow(ax, col_center, ident_y, col_center, screened_y + screened_h)

    # --- Records excluded (right) ---
    exc_x = 8.10
    exc_w = 5.55
    exc_y, exc_h = 3.75, 1.35
    _box(ax, exc_x, exc_y, exc_w, exc_h,
         ["Records excluded:",
          "    Excluded at title/abstract  (n = " + str(counts["excluded_title_abstract"]) + ")"],
         facecolor=YELLOW_BG, edgecolor=YELLOW_EDGE)

    _arrow(ax, col_x + col_w, screened_y + screened_h / 2,
           exc_x, exc_y + exc_h / 2, color="#666666")

    # --- Reports assessed for eligibility ---
    elig_y, elig_h = 2.10, 1.15
    _box(ax, col_x, elig_y, col_w, elig_h,
         ["Reports assessed for eligibility",
          "    n = " + str(counts["fulltext_assessed"])],
         facecolor=GREEN_BG, edgecolor=GREEN_EDGE)

    _arrow(ax, col_center, screened_y, col_center, elig_y + elig_h)

    # --- Studies included in review ---
    inc_y, inc_h = 0.55, 1.20
    _box(ax, col_x, inc_y, col_w, inc_h,
         ["Studies included in review",
          "    n = " + str(counts["included"])],
         facecolor=PURPLE_BG, edgecolor=PURPLE_EDGE,
         title_size=11.5, fontsize=10)

    _arrow(ax, col_center, elig_y, col_center, inc_y + inc_h)

    # ============ Footer ============
    ax.text(7, 0.15, "Generated by SLR-Automate",
            ha="center", va="center", fontsize=7.5, color="#999999", style="italic")

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close()
    print("PRISMA diagram saved to " + output_path)
