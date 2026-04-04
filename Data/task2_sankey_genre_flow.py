"""
Task 2 — Bidirectional Genre Influence Sankey Diagram
Shows how Oceanus Folk influences and is influenced by other genres.
Output: images/task2/task2_sankey_genre_flow_python.png
        images/task2/task2_sankey_genre_flow_python.html
"""

import os
import pandas as pd
import plotly.graph_objects as go

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT       = os.path.dirname(SCRIPT_DIR)
CSV_PATH   = os.path.join(ROOT, "Data", "mc1_csv", "processed",
                          "task2_genre_summary.csv")
OUT_DIR    = os.path.join(ROOT, "images", "task2")
OUT_PNG    = os.path.join(OUT_DIR, "task2_sankey_genre_flow_python.png")
OUT_HTML   = os.path.join(OUT_DIR, "task2_sankey_genre_flow_python.html")

os.makedirs(OUT_DIR, exist_ok=True)

# ── Load and filter data ───────────────────────────────────────────────────────
df = pd.read_csv(CSV_PATH)

# Remove internal OF-to-OF flows (should already be excluded, but safety check)
df = df[~((df["source_genre"] == "Oceanus Folk") &
          (df["target_genre"] == "Oceanus Folk"))]

# Aggregate connection counts by (genre, direction), summing across edge types
outbound = (
    df[df["direction"] == "outbound"]
    .groupby("target_genre")["connection_count"]
    .sum()
    .reset_index()
    .rename(columns={"target_genre": "genre", "connection_count": "count"})
)
inbound = (
    df[df["direction"] == "inbound"]
    .groupby("source_genre")["connection_count"]
    .sum()
    .reset_index()
    .rename(columns={"source_genre": "genre", "connection_count": "count"})
)

# Filter: keep only connections with >= 3 occurrences
MIN_COUNT = 3
outbound = outbound[outbound["count"] >= MIN_COUNT].copy()
inbound  = inbound[inbound["count"] >= MIN_COUNT].copy()

outbound = outbound.sort_values("count", ascending=False)
inbound  = inbound.sort_values("count", ascending=False)

# ── Identify bidirectional genres ──────────────────────────────────────────────
out_genres = set(outbound["genre"])
in_genres  = set(inbound["genre"])
bi_genres  = out_genres & in_genres

# ── Build node list ────────────────────────────────────────────────────────────
# Two anchor nodes + genre nodes (deduplicated across directions)
all_genres = sorted(out_genres | in_genres)

nodes = ["Oceanus Folk \u2192 Outward"]   # index 0: left anchor
nodes += [f"{g} (out)" for g in outbound["genre"]]
nodes += [f"{g} (in)" for g in inbound["genre"]]
nodes += ["Inward \u2192 Oceanus Folk"]   # last index: right anchor

node_idx = {name: i for i, name in enumerate(nodes)}
right_anchor = len(nodes) - 1

# ── Node colours ───────────────────────────────────────────────────────────────
ANCHOR_LEFT  = "rgba(31, 119, 180, 0.85)"   # blue
ANCHOR_RIGHT = "rgba(148, 103, 189, 0.85)"  # purple
COLOUR_BI    = "rgba(255, 165, 0, 0.85)"    # orange — bidirectional
COLOUR_OUT   = "rgba(135, 206, 250, 0.85)"  # light blue — outbound only
COLOUR_IN    = "rgba(220, 80, 80, 0.85)"    # red/pink — inbound only

node_colours = []
for name in nodes:
    if name == nodes[0]:
        node_colours.append(ANCHOR_LEFT)
    elif name == nodes[-1]:
        node_colours.append(ANCHOR_RIGHT)
    else:
        # Extract genre from "Genre (out)" or "Genre (in)"
        genre = name.rsplit(" (", 1)[0]
        if genre in bi_genres:
            node_colours.append(COLOUR_BI)
        elif "(out)" in name:
            node_colours.append(COLOUR_OUT)
        else:
            node_colours.append(COLOUR_IN)

# ── Build links ────────────────────────────────────────────────────────────────
sources, targets, values, link_colours = [], [], [], []

# Outbound: left anchor → genre nodes
for _, row in outbound.iterrows():
    src = 0  # left anchor
    tgt = node_idx[f"{row['genre']} (out)"]
    sources.append(src)
    targets.append(tgt)
    values.append(int(row["count"]))
    # Semi-transparent version of source node colour
    link_colours.append("rgba(31, 119, 180, 0.25)")

# Inbound: genre nodes → right anchor
for _, row in inbound.iterrows():
    src = node_idx[f"{row['genre']} (in)"]
    tgt = right_anchor
    sources.append(src)
    targets.append(tgt)
    values.append(int(row["count"]))
    # Semi-transparent version of source node colour
    genre = row["genre"]
    if genre in bi_genres:
        link_colours.append("rgba(255, 165, 0, 0.25)")
    else:
        link_colours.append("rgba(220, 80, 80, 0.25)")

# ── Node positions ─────────────────────────────────────────────────────────────
# Left anchor far left, right anchor far right, genre nodes in between
n_out = len(outbound)
n_in  = len(inbound)
n_total = len(nodes)

node_x, node_y = [], []
for i, name in enumerate(nodes):
    if name == nodes[0]:
        node_x.append(0.01)
        node_y.append(0.5)
    elif name == nodes[-1]:
        node_x.append(0.99)
        node_y.append(0.5)
    elif "(out)" in name:
        # Outbound genre nodes at x=0.35, spread vertically
        idx = [j for j, n in enumerate(nodes) if "(out)" in n].index(i)
        node_x.append(0.35)
        node_y.append(0.05 + 0.9 * idx / max(n_out - 1, 1))
    else:
        # Inbound genre nodes at x=0.65, spread vertically
        idx = [j for j, n in enumerate(nodes) if "(in)" in n].index(i)
        node_x.append(0.65)
        node_y.append(0.05 + 0.9 * idx / max(n_in - 1, 1))

# ── Clean display labels (remove direction suffix) ─────────────────────────────
display_labels = []
for name in nodes:
    if "(out)" in name or "(in)" in name:
        display_labels.append(name.rsplit(" (", 1)[0])
    else:
        display_labels.append(name)

# ── Build figure ───────────────────────────────────────────────────────────────
fig = go.Figure(go.Sankey(
    arrangement="snap",
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="rgba(0,0,0,0.3)", width=0.5),
        label=display_labels,
        color=node_colours,
        x=node_x,
        y=node_y,
    ),
    link=dict(
        source=sources,
        target=targets,
        value=values,
        color=link_colours,
    ),
))

fig.update_layout(
    title=dict(
        text="Oceanus Folk — Bidirectional Genre Influence Flow",
        font=dict(size=18, color="#1A1D23"),
        x=0.5,
        xanchor="center",
    ),
    font=dict(size=12, family="Helvetica Neue, Helvetica, Arial, sans-serif"),
    width=1100,
    height=700,
    paper_bgcolor="#FAFBFC",
    annotations=[
        dict(
            text=(
                "<b>Reading guide:</b> Left side shows genres influenced <i>by</i> "
                "Oceanus Folk; right side shows genres that influenced Oceanus Folk.<br>"
                "Orange nodes appear on both sides (bidirectional influence). "
                "Flows with fewer than 3 connections are excluded."
            ),
            showarrow=False,
            x=0.5, y=-0.08,
            xref="paper", yref="paper",
            xanchor="center",
            font=dict(size=11, color="#6B7280"),
            align="center",
        )
    ],
    margin=dict(l=20, r=20, t=60, b=80),
)

# ── Save outputs ───────────────────────────────────────────────────────────────
fig.write_html(OUT_HTML)
print(f"Saved: {OUT_HTML}")

fig.write_image(OUT_PNG, scale=2)
print(f"Saved: {OUT_PNG}  ({os.path.getsize(OUT_PNG)/1024:.1f} KB)")
