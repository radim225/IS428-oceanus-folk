"""
Task 3 — Rising Star Radar Chart
Compares top 5 Oceanus Folk candidate artists across 5 dimensions.
Output: images/task3/task3_radar_chart.png
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from typing import cast
from matplotlib.projections.polar import PolarAxes

# ── Paths (relative to project root) ──────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT       = os.path.dirname(SCRIPT_DIR)
CSV_PATH   = os.path.join(ROOT, "Data", "mc1_csv", "processed", "task3_artist_notoriety.csv")
OUT_PATH   = os.path.join(ROOT, "images", "task3", "task3_radar_chart.png")

# ── Load & filter ──────────────────────────────────────────────────────────────
df = pd.read_csv(CSV_PATH)
df["is_oceanus_folk_artist"] = df["is_oceanus_folk_artist"].astype(str).str.strip().str.lower() == "true"
of = df[df["is_oceanus_folk_artist"]].sort_values("total_notable_works", ascending=False).head(5).copy()

# ── Genre diversity: count unique genres per artist ────────────────────────────
def count_genres(genre_str):
    if pd.isna(genre_str) or str(genre_str).strip() == "":
        return 0
    return len(set(g.strip() for g in str(genre_str).split(",")))

of["genre_diversity"] = of["genres"].apply(count_genres)

# ── Normalise helper ───────────────────────────────────────────────────────────
def minmax(series):
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series([0.5] * len(series), index=series.index)
    return (series - lo) / (hi - lo)

# ── Build 5 normalised metrics ─────────────────────────────────────────────────
of["m_works"]    = minmax(of["total_notable_works"])

span             = of["years_active_span"].astype(float)
of["m_quick"]    = minmax(span.max() - span)          # fewer years → higher score

first_yr         = of["first_notoriety_date"].astype(float)
of["m_early"]    = minmax(first_yr.max() - first_yr)  # earlier → higher

latest_yr        = of["latest_notoriety_date"].astype(float)
of["m_recent"]   = minmax(latest_yr)                  # later → higher

of["m_diversity"] = minmax(of["genre_diversity"])

# ── Verification printout ──────────────────────────────────────────────────────
METRICS     = ["m_works", "m_quick", "m_early", "m_recent", "m_diversity"]
COL_HEADERS = ["Works", "QuickBT", "EarlyBT", "RecentAct", "Diversity"]
print(f"=== Normalised scores ({'  '.join(f'{h:>9}' for h in COL_HEADERS)}) ===")
for _, row in of.iterrows():
    scores = "  ".join(f"{row[m]:9.4f}" for m in METRICS)
    print(f"  {row['performer_name']:30s}  {scores}")
print()

# ── Design constants ───────────────────────────────────────────────────────────
ARTIST_COLOURS = {
    "Orla Seabloom":        "#E6A817",
    "Copper Canyon Ghosts": "#2196A8",
    "Daniel O'Connell":     "#6B4FBB",
    "Beatrice Albright":    "#D94F3D",
    "Ping Meng":            "#3DAD6E",
}
# Fallback order if artist names differ
FALLBACK_COLOURS = ["#E6A817", "#2196A8", "#6B4FBB", "#D94F3D", "#3DAD6E"]

LABELS = [
    "Total Notable\nWorks",
    "Quick\nBreakthrough",
    "Early\nBreakthrough",
    "Recent\nActivity",
    "Genre\nDiversity",
]

N      = len(METRICS)
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]   # close polygon

GRID_COL = "#cccccc"
SPOKE_COL = "#dddddd"
TEXT_COL  = "#222222"
GREY      = "#666666"

# ── Figure: explicit axis positions ───────────────────────────────────────────
fig = plt.figure(figsize=(14, 8), dpi=150, facecolor="white")

# Radar: [left, bottom, width, height] in figure fraction
ax_radar = cast(PolarAxes, fig.add_axes([0.02, 0.05, 0.62, 0.88], polar=True))
# Table: top-right corner
ax_table = fig.add_axes([0.65, 0.45, 0.34, 0.50])

# ── Radar panel ────────────────────────────────────────────────────────────────
ax_radar.set_facecolor("white")
ax_radar.set_theta_zero_location("N")
ax_radar.set_theta_direction(-1)
ax_radar.spines["polar"].set_color(GRID_COL)

# Suppress default grid; draw manually
ax_radar.grid(False)
ax_radar.set_yticklabels([])

# Concentric circles
for r in [0.25, 0.5, 0.75, 1.0]:
    ax_radar.plot(angles, [r] * (N + 1), color=GRID_COL,
                  linewidth=0.7, linestyle="--", zorder=1)
    ax_radar.text(float(np.pi * 1.32), r, f"{r:.2f}",
                  ha="center", va="center", color=GREY, fontsize=7)

# Spoke lines
for angle in angles[:-1]:
    ax_radar.plot([angle, angle], [0, 1], color=SPOKE_COL, linewidth=0.9, zorder=1)

# Plot each artist
for i, (_, row) in enumerate(of.iterrows()):
    name   = row["performer_name"]
    colour = ARTIST_COLOURS.get(name, FALLBACK_COLOURS[i])
    values = [row[m] for m in METRICS] + [row[METRICS[0]]]
    ax_radar.plot(angles, values, color=colour, linewidth=2.5, zorder=3)
    ax_radar.fill(angles, values, color=colour, alpha=0.15, zorder=2)

# Axis tick labels (hide defaults, place manually)
ax_radar.set_xticks(angles[:-1])
ax_radar.set_xticklabels([""] * N)
ax_radar.set_ylim(0, 1)
ax_radar.set_yticks([])

# Axis labels positioned outside ring with per-axis padding
PADS = [1.45, 1.28, 1.28, 1.28, 1.28]   # top axis gets extra clearance
for i, (angle, label, pad) in enumerate(zip(angles[:-1], LABELS, PADS)):
    ax_radar.text(angle, pad, label,
                  ha="center", va="center",
                  color=TEXT_COL, fontsize=11, fontweight="bold",
                  linespacing=1.4)

# Title & subtitle sit above the radar axes
ax_radar.set_title(
    "Rising Star Profile — Oceanus Folk Candidates\n"
    "Each axis is min-max normalised within the top 5 candidates  "
    "•  Larger shape = stronger overall profile",
    pad=28, fontsize=12, color=TEXT_COL,
    linespacing=1.8,
)

# ── Data table panel (top-right) ───────────────────────────────────────────────
ax_table.axis("off")

col_labels = ["Artist", "Works", "Quick BT", "Early BT", "Recent", "Genres"]
COL_WIDTHS = [0.30, 0.10, 0.14, 0.14, 0.14, 0.12]
ROW_HEIGHT = 0.12
table_data   = []
cell_colours = []

for i, (_, row) in enumerate(of.iterrows()):
    bg = "white" if i % 2 == 0 else "#f0f4f8"
    table_data.append([
        row["performer_name"],
        int(row["total_notable_works"]),
        f"{int(row['years_active_span'])} yr",
        int(row["first_notoriety_date"]),
        int(row["latest_notoriety_date"]),
        int(row["genre_diversity"]),
    ])
    cell_colours.append([bg] * 6)

tbl = ax_table.table(
    cellText=table_data,
    colLabels=col_labels,
    cellLoc="center",
    loc="upper center",
    cellColours=cell_colours,
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(10)

for (row_idx, col_idx), cell in tbl.get_celld().items():
    cell.set_edgecolor("#dddddd")
    cell.set_linewidth(0.5)
    cell.set_height(ROW_HEIGHT)
    if col_idx < len(COL_WIDTHS):
        cell.set_width(COL_WIDTHS[col_idx])
    if row_idx == 0:
        cell.set_text_props(fontweight="bold", color="white", fontsize=10)
        cell.set_facecolor("#1a5276")

# Artist name in each row coloured to match radar
for i, (_, row) in enumerate(of.iterrows()):
    name   = row["performer_name"]
    colour = ARTIST_COLOURS.get(name, FALLBACK_COLOURS[i])
    tbl[i + 1, 0].set_text_props(color=colour, fontweight="bold")

# ── Footnote ──────────────────────────────────────────────────────────────────
fig.text(
    0.5, 0.015,
    "BT = Breakthrough  •  Values shown are raw data  "
    "•  Radar axes are normalised 0–1 within this candidate pool",
    ha="center", va="bottom",
    color=GREY, fontsize=8,
)

# ── Save ───────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
fig.savefig(OUT_PATH, dpi=150, bbox_inches="tight", facecolor="white")

size_kb = os.path.getsize(OUT_PATH) / 1024
print(f"Saved : {OUT_PATH}")
print(f"Size  : {size_kb:.1f} KB")
print("\nArtists plotted:")
for _, row in of.iterrows():
    print(f"  {row['performer_name']:30s}  works={row['total_notable_works']}  "
          f"span={row['years_active_span']}yr  "
          f"first={int(row['first_notoriety_date'])}  "
          f"latest={int(row['latest_notoriety_date'])}  "
          f"genres={row['genre_diversity']}")
