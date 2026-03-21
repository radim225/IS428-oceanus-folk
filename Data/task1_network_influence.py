"""
Task 1 — Sailor Shift Direct and Indirect Influence Network
Shows the full influence chain: collaborators + works + inspired artists.
Output: images/task1/task1_influence_network.html
"""

import os
import pandas as pd
from pyvis.network import Network

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT       = os.path.dirname(SCRIPT_DIR)
NODES_CSV  = os.path.join(ROOT, "Data", "mc1_csv", "processed", "nodes.csv")
EDGES_CSV  = os.path.join(ROOT, "Data", "mc1_csv", "processed", "edges.csv")
OUT_PATH   = os.path.join(ROOT, "images", "task1", "task1_influence_network.html")

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────────
nodes = pd.read_csv(NODES_CSV)
edges = pd.read_csv(EDGES_CSV)

# ── Filter: all roles that tell the influence story ───────────────────────────
INCLUDE_ROLES = {
    "Sailor Shift",
    "Direct Collaborator",
    "Ivy Echoes Member",
    "Sailor Work",
    "Inspired Sailor",
    "Inspired By Sailor Circle",
}
subset = nodes[nodes["role"].isin(INCLUDE_ROLES)].copy()

print(f"Nodes included: {len(subset)}")
print(subset.groupby("role").size().to_string())

# ── Filter edges ───────────────────────────────────────────────────────────────
subset_ids = set(subset["Id"])
edges_f = edges[
    edges["Source"].isin(subset_ids) & edges["Target"].isin(subset_ids)
].copy()

print(f"\nEdges included: {len(edges_f)}")

# ── Node style map ─────────────────────────────────────────────────────────────
ROLE_STYLE = {
    "Sailor Shift":              {"color": "#FFD700", "size": 50, "shape": "star"},
    "Sailor Work":               {"color": "#FFA500", "size": 15, "shape": "dot"},
    "Direct Collaborator":       {"color": "#4A90D9", "size": 20, "shape": "dot"},
    "Ivy Echoes Member":         {"color": "#2ECC71", "size": 20, "shape": "dot"},
    "Inspired Sailor":           {"color": "#9B59B6", "size": 15, "shape": "dot"},
    "Inspired By Sailor Circle": {"color": "#9B59B6", "size": 15, "shape": "dot"},
}

# ── Build pyvis network ────────────────────────────────────────────────────────
net = Network(
    height="700px", width="100%",
    bgcolor="#0d1117", font_color="white",
    directed=True,
    notebook=False,
    cdn_resources="in_line",
)
net.toggle_physics(True)
net.set_options("""{
  "physics": {
    "forceAtlas2Based": {
      "gravitationalConstant": -60,
      "centralGravity": 0.005,
      "springLength": 150,
      "springConstant": 0.05
    },
    "solver": "forceAtlas2Based",
    "stabilization": { "iterations": 300 }
  },
  "edges": {
    "arrows": { "to": { "enabled": true, "scaleFactor": 0.5 } },
    "smooth": { "type": "continuous" }
  }
}""")

for _, row in subset.iterrows():
    style = ROLE_STYLE.get(row["role"], {"color": "#888888", "size": 12, "shape": "dot"})
    genre_info = f"<br>Genre: {row['genre']}" if pd.notna(row.get("genre")) else ""
    year_info  = f"<br>Released: {int(row['release_date'])}" if pd.notna(row.get("release_date")) else ""
    net.add_node(
        int(row["Id"]),
        label=str(row["Label"]),
        color=style["color"],
        size=style["size"],
        shape=style["shape"],
        title=f'{row["Label"]}<br>Role: {row["role"]}{genre_info}{year_info}',
        font={"color": "#e0e0e0", "size": 12},
        borderWidth=1,
        borderWidthSelected=3,
    )

for _, row in edges_f.iterrows():
    net.add_edge(
        int(row["Source"]),
        int(row["Target"]),
        title=str(row["edge_type"]),
        color={"color": "#3a3a3a", "highlight": "#aaaaaa"},
        width=1,
    )

# ── Save & inject title + legend ───────────────────────────────────────────────
net.save_graph(OUT_PATH)

title_html = (
    '<div style="position:fixed;top:0;left:0;right:0;z-index:999;'
    'background:#0d1117;padding:10px 0;text-align:center;">'
    '<h2 style="color:#e0e0e0;font-family:sans-serif;margin:0;font-size:18px;">'
    'Sailor Shift &#8212; Direct and Indirect Influence Network</h2>'
    '<p style="color:#888;font-family:sans-serif;margin:4px 0 0;font-size:12px;">'
    '<span style="color:#FFD700;">&#9733;</span> Sailor Shift &nbsp;'
    '<span style="color:#FFA500;">&#9632;</span> Sailor Works &nbsp;'
    '<span style="color:#4A90D9;">&#9632;</span> Direct Collaborator &nbsp;'
    '<span style="color:#2ECC71;">&#9632;</span> Ivy Echoes Member &nbsp;'
    '<span style="color:#9B59B6;">&#9632;</span> Inspired By Sailor'
    '</p></div>'
    '<div style="height:65px;"></div>'
)
html = open(OUT_PATH, encoding="utf-8").read()
html = html.replace("<body>", "<body>" + title_html, 1)
open(OUT_PATH, "w", encoding="utf-8").write(html)

size_kb = os.path.getsize(OUT_PATH) / 1024
print(f"\nSaved: {OUT_PATH}")
print(f"Size:  {size_kb:.1f} KB")
