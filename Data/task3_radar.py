"""
Task 3 — Rising Star Radar Chart (Optimised Layout)
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.projections.polar import PolarAxes
from typing import cast

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT       = os.path.dirname(SCRIPT_DIR)
CSV_PATH   = os.path.join(ROOT, "Data", "mc1_csv", "processed",
             "task3_artist_notoriety.csv")
OUT_PATH   = os.path.join(ROOT, "images", "task3", "task3_radar_chart.png")

# ── Load from CSV ──────────────────────────────────────────────────────────────
df = pd.read_csv(CSV_PATH)
df["is_oceanus_folk_artist"] = (
    df["is_oceanus_folk_artist"].astype(str).str.strip().str.lower() == "true"
)
of = df[df["is_oceanus_folk_artist"]].sort_values(
    "total_notable_works", ascending=False
).head(5).copy()
of = of.reset_index(drop=True)

# ── Genre diversity ────────────────────────────────────────────────────────────
def count_genres(genre_str):
    if pd.isna(genre_str) or str(genre_str).strip() == "":
        return 0
    return len(set(g.strip() for g in str(genre_str).split(",")))

of["genre_diversity"] = of["genres"].apply(count_genres)

# ── Normalisation ──────────────────────────────────────────────────────────────
def minmax(series):
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series([0.5] * len(series), index=series.index)
    return (series - lo) / (hi - lo)

of["m_works"]     = minmax(of["total_notable_works"])
span              = of["years_active_span"].astype(float)
of["m_quick"]     = minmax(span.max() - span)
first_yr          = of["first_notoriety_date"].astype(float)
of["m_early"]     = minmax(first_yr.max() - first_yr)
latest_yr         = of["latest_notoriety_date"].astype(float)
of["m_recent"]    = minmax(latest_yr)
of["m_diversity"] = minmax(of["genre_diversity"])

METRICS = ["m_works", "m_quick", "m_early", "m_recent", "m_diversity"]

# ── Style constants ────────────────────────────────────────────────────────────
ARTIST_COLOURS = {
    "Orla Seabloom":        "#D4A017",
    "Copper Canyon Ghosts": "#1B8A9A",
    "Daniel O'Connell":     "#6B4FBB",
    "Beatrice Albright":    "#C94432",
    "Ping Meng":            "#2E9B5E",
}
ARTIST_ORDER = list(ARTIST_COLOURS.keys())

LABELS = [
    "Total Notable\nWorks",
    "Quick\nBreakthrough",
    "Early\nBreakthrough",
    "Recent\nActivity",
    "Genre\nDiversity",
]

N      = len(METRICS)
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]

BG         = "#FAFBFC"
CARD_BG    = "#FFFFFF"
GRID       = "#D5DAE0"
SPOKE      = "#E0E4E8"
BLACK      = "#1A1D23"
DARK_GREY  = "#3B3F46"
MID_GREY   = "#6B7280"
LIGHT_GREY = "#9CA3AF"
HEADER_BG  = "#1E3A52"
ROW_ALT    = "#F4F7FA"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "text.color": DARK_GREY,
})

# ── Figure ─────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(16, 9.5), dpi=150, facecolor=BG)

# ── Title block ────────────────────────────────────────────────────────────────
fig.text(0.04, 0.96,
         "Rising Star Profile",
         ha="left", va="top",
         fontsize=22, fontweight="bold", color=BLACK,
         fontfamily="sans-serif")
fig.text(0.04, 0.925,
         "Oceanus Folk Candidates",
         ha="left", va="top",
         fontsize=14, fontweight="normal", color=MID_GREY)
fig.text(0.04, 0.895,
         "Each axis is min–max normalised within the top 5 candidates.  Larger shape = stronger overall profile.",
         ha="left", va="top",
         fontsize=11, fontweight="normal", color=LIGHT_GREY)

from matplotlib.lines import Line2D
sep = Line2D([0.04, 0.96], [0.878, 0.878], transform=fig.transFigure,
             color="#E5E7EB", linewidth=0.8, zorder=0)
fig.add_artist(sep)

# ── Radar axes ─────────────────────────────────────────────────────────────────
ax = cast(PolarAxes, fig.add_axes([0.04, 0.10, 0.52, 0.72], polar=True))
ax.set_facecolor(BG)
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.spines["polar"].set_visible(False)
ax.grid(False)
ax.set_yticklabels([])
ax.set_yticks([])
ax.set_ylim(0, 1.08)

for r in [0.25, 0.50, 0.75, 1.0]:
    ax.plot(angles, [r] * (N + 1), color=GRID, linewidth=0.6,
            linestyle="-", alpha=0.55, zorder=1)

for r, lbl in zip([0.25, 0.50, 0.75], [".25", ".50", ".75"]):
    ax.text(float(np.radians(198)), r + 0.04, lbl,
            ha="center", va="center", color=LIGHT_GREY, fontsize=11,
            zorder=5,
            path_effects=[pe.withStroke(linewidth=2.5, foreground=BG)])

for angle in angles[:-1]:
    ax.plot([angle, angle], [0, 1.0], color=SPOKE, linewidth=0.7, zorder=1)

for i in range(len(of) - 1, -1, -1):
    row    = of.iloc[i]
    name   = row["performer_name"]
    colour = ARTIST_COLOURS.get(name, "#888888")
    vals   = [row[m] for m in METRICS] + [row[METRICS[0]]]
    lw     = 2.8 if i == 0 else 2.0
    ax.fill(angles, vals, color=colour, alpha=0.10, zorder=2 + i)
    ax.plot(angles, vals, color=colour, linewidth=lw, zorder=7 + i,
            solid_capstyle="round")
    for a, v in zip(angles[:-1], vals[:-1]):
        ax.plot(a, v, "o", color=colour, markersize=4, zorder=12 + i,
                markeredgecolor="white", markeredgewidth=0.6)

ax.set_xticks(angles[:-1])
ax.set_xticklabels([""] * N)

PADS = [1.16, 1.18, 1.20, 1.20, 1.18]
for angle, label, pad in zip(angles[:-1], LABELS, PADS):
    ax.text(angle, pad, label,
            ha="center", va="center",
            color=DARK_GREY, fontsize=11, fontweight="semibold",
            linespacing=1.35)

# ── Legend ─────────────────────────────────────────────────────────────────────
legend_y     = 0.07
legend_x     = 0.06
spacing      = 0.175
for idx, name in enumerate(ARTIST_ORDER):
    x      = legend_x + idx * spacing
    colour = ARTIST_COLOURS[name]
    fig.patches.append(plt.Circle((x, legend_y), 0.006,
                                  transform=fig.transFigure,
                                  facecolor=colour, edgecolor="none",
                                  zorder=10))
    fig.text(x + 0.012, legend_y, name,
             ha="left", va="center",
             fontsize=11, color=DARK_GREY,
             transform=fig.transFigure)

# ── Table panel ────────────────────────────────────────────────────────────────
ax_t = fig.add_axes([0.58, 0.22, 0.40, 0.62])
ax_t.axis("off")

col_labels = ["Artist", "Works", "Span", "First\nNotable", "Latest\nNotable", "Genres"]
COL_W      = [0.30, 0.10, 0.12, 0.16, 0.16, 0.12]
ROW_H      = 0.125

rows, cell_bg = [], []
for i, (_, row) in enumerate(of.iterrows()):
    bg = CARD_BG if i % 2 == 0 else ROW_ALT
    rows.append([
        row["performer_name"],
        int(row["total_notable_works"]),
        f"{int(row['years_active_span'])} yr",
        int(row["first_notoriety_date"]),
        int(row["latest_notoriety_date"]),
        int(row["genre_diversity"]),
    ])
    cell_bg.append([bg] * 6)

tbl = ax_t.table(
    cellText=rows,
    colLabels=col_labels,
    cellLoc="center",
    loc="upper center",
    cellColours=cell_bg,
    bbox=[0.0, 0.0, 0.97, 1.0],
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(10)

for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor("#E5E7EB")
    cell.set_linewidth(0.4)
    cell.set_height(ROW_H)
    if c < len(COL_W):
        cell.set_width(COL_W[c])
    if r == 0:
        cell.set_text_props(fontweight="bold", color="white", fontsize=11)
        cell.set_facecolor(HEADER_BG)
        cell.set_edgecolor(HEADER_BG)
        cell.set_height(ROW_H * 1.15)
    else:
        cell.set_text_props(fontsize=11, color=DARK_GREY)

for i in range(len(of)):
    name   = of.iloc[i]["performer_name"]
    colour = ARTIST_COLOURS.get(name, "#888888")
    tbl[i + 1, 0].set_text_props(color=colour, fontweight="bold", fontsize=11)

fig.text(0.58, 0.87,
         "Raw Data — Top 5 Candidates",
         ha="left", va="bottom",
         fontsize=11, fontweight="bold", color=DARK_GREY)
fig.text(0.58, 0.852,
         "Sorted by total notable works (descending)",
         ha="left", va="top",
         fontsize=11, color=LIGHT_GREY)

# ── Footnote ───────────────────────────────────────────────────────────────────
fig.text(0.96, 0.018,
         "Span = years between first and latest notable work  •  "
         "Radar axes are normalised 0–1 within this candidate pool",
         ha="right", va="bottom", color=LIGHT_GREY, fontsize=11,
         fontstyle="italic")

# ── Save ───────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
fig.savefig(OUT_PATH, dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(fig)
print(f"Saved: {OUT_PATH}  ({os.path.getsize(OUT_PATH)/1024:.1f} KB)")