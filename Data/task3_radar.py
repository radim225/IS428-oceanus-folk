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
import matplotlib.patches as mpatches

# ── Paths (relative to project root) ──────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
CSV_PATH = os.path.join(ROOT, "Data", "mc1_csv", "processed", "task3_artist_notoriety.csv")
OUT_PATH = os.path.join(ROOT, "images", "task3", "task3_radar_chart.png")

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
of["m_works"]     = minmax(of["total_notable_works"])

# Quick Breakthrough: invert years_active_span — 0 yrs → score 1.0, 17 yrs → ~0
span = of["years_active_span"].astype(float)
of["m_quick"]     = minmax(span.max() - span)

# Early Breakthrough: invert first_notoriety_date within this 5-artist range
first_yr = of["first_notoriety_date"].astype(float)
of["m_early"]     = minmax(first_yr.max() - first_yr)    # earlier → higher

latest_yr = of["latest_notoriety_date"].astype(float)
of["m_recent"]     = minmax(latest_yr)                   # later → higher

of["m_diversity"]  = minmax(of["genre_diversity"])

# ── Verification printout ──────────────────────────────────────────────────────
METRICS = ["m_works", "m_quick", "m_early", "m_recent", "m_diversity"]
COL_HEADERS = ["Works", "QuickBT", "EarlyBT", "RecentAct", "Diversity"]
print("=== Ping Meng genres ===")
pm = of[of["performer_name"] == "Ping Meng"].iloc[0]
genres_list = [g.strip() for g in str(pm["genres"]).split(",")]
print(f"  Raw   : {pm['genres']}")
print(f"  Unique: {sorted(set(genres_list))}  count={len(set(genres_list))}")
print()
print(f"=== Normalised scores ({'  '.join(f'{h:>9}' for h in COL_HEADERS)}) ===")
for _, row in of.iterrows():
    scores = "  ".join(f"{row[m]:9.4f}" for m in METRICS)
    print(f"  {row['performer_name']:30s}  {scores}")
print()

LABELS  = [
    "Total Notable\nWorks",
    "Quick\nBreakthrough",
    "Early\nBreakthrough",
    "Recent\nActivity",
    "Genre\nDiversity",
]

# Artist order after sort: Orla, Copper Canyon, Daniel, Beatrice, Ping Meng
COLOURS = ["#FFD700", "#00CED1", "#7B68EE", "#FF6B6B", "#98FB98"]

# ── Radar geometry ─────────────────────────────────────────────────────────────
N      = len(METRICS)
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]   # close polygon

# ── Plot ───────────────────────────────────────────────────────────────────────
BG = "#0d1117"
GRID_COL = "#3a3a3a"
TEXT_COL = "#e0e0e0"

fig = plt.figure(figsize=(10, 8), dpi=150, facecolor=BG)
ax  = fig.add_subplot(111, polar=True, facecolor=BG)
ax.set_theta_zero_location("N")   # first axis at top (12 o'clock)
ax.set_theta_direction(-1)        # clockwise, conventional radar layout

# Grid styling
ax.set_facecolor(BG)
ax.spines["polar"].set_color(GRID_COL)
ax.grid(color=GRID_COL, linewidth=0.8, linestyle="--", alpha=0.6)

# Draw concentric circles manually for cleaner control
for r in [0.2, 0.4, 0.6, 0.8, 1.0]:
    ax.plot(angles, [r] * (N + 1), color=GRID_COL, linewidth=0.6, linestyle="--")

# Axis lines (spokes)
for angle in angles[:-1]:
    ax.plot([angle, angle], [0, 1], color=GRID_COL, linewidth=0.8)

# Plot each artist
legend_patches = []
for i, (_, row) in enumerate(of.iterrows()):
    values = [row[m] for m in METRICS] + [row[METRICS[0]]]
    colour = COLOURS[i]
    ax.plot(angles, values, color=colour, linewidth=2.5, zorder=3)
    ax.fill(angles, values, color=colour, alpha=0.2)
    legend_patches.append(
        mpatches.Patch(facecolor=colour, edgecolor=colour, label=row["performer_name"])
    )

# Axis labels — placed manually so the top label clears the chart lines
ax.set_xticks(angles[:-1])
ax.set_xticklabels([""] * N)           # hide default tick text
for angle, label in zip(angles[:-1], LABELS):
    ax.text(angle, 1.22, label,
            ha="center", va="center",
            color=TEXT_COL, fontsize=10, fontfamily="sans-serif")

# Radial ticks
ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"],
                   color="#888888", fontsize=7, fontfamily="sans-serif")
ax.set_ylim(0, 1)

# Title
fig.text(
    0.42, 0.97,
    "Rising Star Profile — Oceanus Folk Candidates",
    ha="center", va="top",
    color=TEXT_COL, fontsize=13, fontweight="bold", fontfamily="sans-serif",
)

# Legend
leg = fig.legend(
    handles=legend_patches,
    loc="center right",
    bbox_to_anchor=(1.02, 0.5),
    fontsize=9,
    frameon=True,
    framealpha=0.15,
    edgecolor=GRID_COL,
    labelcolor=TEXT_COL,
    facecolor=BG,
    title="Artists",
    title_fontsize=9,
)
leg.get_title().set_color(TEXT_COL)

plt.tight_layout(rect=[0, 0, 0.82, 0.95])

# ── Save ───────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
fig.savefig(OUT_PATH, dpi=150, bbox_inches="tight", facecolor=BG)

size_kb = os.path.getsize(OUT_PATH) / 1024
print(f"Saved: {OUT_PATH}")
print(f"Size:  {size_kb:.1f} KB")
print("\nArtists plotted:")
for _, row in of.iterrows():
    print(f"  {row['performer_name']:30s}  works={row['total_notable_works']}  "
          f"longevity={row['years_active_span']}yr  "
          f"first={int(row['first_notoriety_date'])}  "
          f"latest={int(row['latest_notoriety_date'])}  "
          f"genres={row['genre_diversity']}")
