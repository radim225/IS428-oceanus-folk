"""
Task 1 — Sailor Shift Direct Collaborators Network
Shows WHO Sailor collaborated with (persons only).
Edges are derived: collaborator → shared work ← Sailor → collapsed to collaborator—Sailor edge.
Output: images/task1/task1_collaboration_network.html
"""

import os
import pandas as pd
from pyvis.network import Network

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT       = os.path.dirname(SCRIPT_DIR)
NODES_CSV  = os.path.join(ROOT, "Data", "mc1_csv", "processed", "nodes.csv")
EDGES_CSV  = os.path.join(ROOT, "Data", "mc1_csv", "processed", "edges.csv")
OUT_PATH   = os.path.join(ROOT, "images", "task1", "task1_collaboration_network.html")

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────────
nodes = pd.read_csv(NODES_CSV)
edges = pd.read_csv(EDGES_CSV)

sailor_node = nodes[nodes["role"] == "Sailor Shift"].iloc[0]
sailor_id   = int(sailor_node["Id"])

# ── Sailor's connected work-node IDs ──────────────────────────────────────────
sailor_edges = edges[(edges["Source"] == sailor_id) | (edges["Target"] == sailor_id)]
sailor_work_ids = set()
for _, r in sailor_edges.iterrows():
    other = int(r["Target"]) if r["Source"] == sailor_id else int(r["Source"])
    sailor_work_ids.add(other)

# ── Filter person nodes ────────────────────────────────────────────────────────
PERSON_ROLES = {"Sailor Shift", "Direct Collaborator", "Ivy Echoes Member"}
persons = nodes[
    nodes["role"].isin(PERSON_ROLES) &
    nodes["node_type"].isin(["Person", "MusicalGroup"])
].copy()
person_ids = set(persons["Id"].astype(int))

print(f"Persons included: {len(persons)}")
print(persons.groupby("role").size().to_string())

# ── Build derived edges: collaborator —[shared work]— Sailor ──────────────────
# For each edge where one end is a collaborator person and other end is a Sailor work
collab_connections: dict[int, list[str]] = {}
for _, r in edges.iterrows():
    src, tgt = int(r["Source"]), int(r["Target"])
    et = str(r["edge_type"])
    if src in person_ids and src != sailor_id and tgt in sailor_work_ids:
        collab_connections.setdefault(src, []).append(et)
    elif tgt in person_ids and tgt != sailor_id and src in sailor_work_ids:
        collab_connections.setdefault(tgt, []).append(et)

print(f"\nCollaborators with shared Sailor works: {len(collab_connections)}")

# ── Node style map ─────────────────────────────────────────────────────────────
ROLE_STYLE = {
    "Sailor Shift":       {"color": "#FFD700", "size": 40},
    "Direct Collaborator":{"color": "#4A90D9", "size": 20},
    "Ivy Echoes Member":  {"color": "#2ECC71", "size": 25},
}

# ── Build pyvis network ────────────────────────────────────────────────────────
net = Network(
    height="700px", width="100%",
    bgcolor="white", font_color="#1f2937",
    directed=False,
    notebook=False,
    cdn_resources="in_line",
)
net.toggle_physics(True)
net.set_options("""{
  "physics": {
    "forceAtlas2Based": {
      "gravitationalConstant": -80,
      "centralGravity": 0.02,
      "springLength": 120,
      "springConstant": 0.08
    },
    "solver": "forceAtlas2Based",
    "stabilization": { "iterations": 250 }
  }
}""")

for _, row in persons.iterrows():
    style = ROLE_STYLE.get(row["role"], {"color": "#888888", "size": 15})
    net.add_node(
        int(row["Id"]),
        label=str(row["Label"]),
        color=style["color"],
        size=style["size"],
        title=f'{row["Label"]}<br>Role: {row["role"]}',
        font={"color": "#e0e0e0", "size": 14},
        borderWidth=2,
        borderWidthSelected=4,
    )

# Add derived edges to Sailor
for collab_id, edge_types in collab_connections.items():
    unique_types = list(dict.fromkeys(edge_types))  # preserve order, deduplicate
    tooltip = "Collaborations:<br>" + "<br>".join(f"• {et}" for et in unique_types)
    edge_label = unique_types[0] if len(unique_types) == 1 else f"{len(unique_types)} roles"
    net.add_edge(
        sailor_id, collab_id,
        title=tooltip,
        label=edge_label,
        color={"color": "#444444", "highlight": "#888888"},
        width=1.5,
        font={"color": "#888888", "size": 9},
    )

# ── Save & inject title ────────────────────────────────────────────────────────
net.save_graph(OUT_PATH)

title_html = (
    '<div style="position:fixed;top:0;left:0;right:0;z-index:999;'
    'background:white;padding:10px 0;text-align:center;border-bottom:1px solid #e5e7eb;">'
    '<h2 style="color:#1f2937;font-family:sans-serif;margin:0;font-size:18px;">'
    'Sailor Shift &#8212; Direct Collaborators Network</h2>'
    '<p style="color:#6b7280;font-family:sans-serif;margin:4px 0 0;font-size:12px;">'
    '<span style="color:#FFD700;">&#9632;</span> Sailor Shift &nbsp;'
    '<span style="color:#4A90D9;">&#9632;</span> Direct Collaborator &nbsp;'
    '<span style="color:#2ECC71;">&#9632;</span> Ivy Echoes Member'
    '</p></div>'
    '<div style="height:60px;"></div>'
)
html = open(OUT_PATH, encoding="utf-8").read()
html = html.replace("<body>", "<body>" + title_html, 1)
open(OUT_PATH, "w", encoding="utf-8").write(html)

size_kb = os.path.getsize(OUT_PATH) / 1024
print(f"\nSaved: {OUT_PATH}")
print(f"Size:  {size_kb:.1f} KB")
