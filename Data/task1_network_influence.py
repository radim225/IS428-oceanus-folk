"""
Task 1 — Sailor Shift Direct and Indirect Influence Network
Shows the full influence chain: collaborators + works + inspired artists.
Output: images/task1/task1_influence_network.html
"""

import json
import os
import pandas as pd
from pyvis.network import Network

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PHYSICS CONFIG — change values here, they apply everywhere automatically  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
PHYSICS = {
    "gravitationalConstant": -50,   # repulsion between nodes (more negative = further apart)
    "centralGravity":        0.01,  # pull towards center (higher = tighter ball)
    "springLength":          120,   # ideal distance between connected nodes (px)
    "springConstant":        0.06,  # spring stiffness (higher = snap to springLength faster)
    "damping":               0.9,   # friction (0-1, higher = less bouncy)
}
STABILIZATION_ITERATIONS = 600     # how long to settle before showing

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
    height="100vh", width="100%",
    bgcolor="white", font_color="#1f2937",
    directed=True,
    notebook=False,
    cdn_resources="in_line",
)

# Build options JSON from the single PHYSICS config
vis_options = {
    "physics": {
        "forceAtlas2Based": PHYSICS,
        "solver": "forceAtlas2Based",
        "stabilization": {"iterations": STABILIZATION_ITERATIONS},
        "maxVelocity": 50,
        "minVelocity": 0.1,
    },
    "edges": {
        "arrows": {"to": {"enabled": True, "scaleFactor": 0.5}},
        "smooth": {"type": "continuous"},
    },
}
net.set_options(json.dumps(vis_options))

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
        font={"color": "#1f2937", "size": 11, "strokeWidth": 3, "strokeColor": "#ffffff"},
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

# ── Save & inject title + legend + overrides ──────────────────────────────────
net.save_graph(OUT_PATH)

style_reset = (
    '<style>'
    'html, body { margin:0; padding:0; width:100%; height:100%; overflow:hidden; }'
    '#mynetwork { width:100% !important; height:calc(100vh - 60px) !important; }'
    '</style>'
)
title_html = (
    '<div style="width:100%;z-index:999;'
    'background:white;padding:10px 0;text-align:center;border-bottom:1px solid #e5e7eb;">'
    '<h2 style="color:#1f2937;font-family:sans-serif;margin:0;font-size:18px;">'
    'Sailor Shift &#8212; Direct and Indirect Influence Network</h2>'
    '<p style="color:#6b7280;font-family:sans-serif;margin:4px 0 0;font-size:12px;">'
    '<span style="color:#FFD700;">&#9733;</span> Sailor Shift &nbsp;'
    '<span style="color:#FFA500;">&#9632;</span> Sailor Works &nbsp;'
    '<span style="color:#4A90D9;">&#9632;</span> Direct Collaborator &nbsp;'
    '<span style="color:#2ECC71;">&#9632;</span> Ivy Echoes Member &nbsp;'
    '<span style="color:#9B59B6;">&#9632;</span> Inspired By Sailor'
    '</p></div>'
)

# Override vis.js options AFTER network is created (pyvis sometimes ignores set_options)
# Also uses the same PHYSICS dict so you only change values in one place
physics_js = json.dumps(PHYSICS)
override_script = f"""
<script>
window.addEventListener('load', function() {{
  setTimeout(function() {{
    if (typeof network !== 'undefined') {{
      network.setOptions({{
        physics: {{
          enabled: true,
          forceAtlas2Based: {physics_js},
          solver: "forceAtlas2Based",
          stabilization: {{ enabled: false }}
        }}
      }});
      // Spread nodes horizontally to use full width
      network.once('stabilized', function() {{
        var positions = network.getPositions();
        var nodeIds = Object.keys(positions);
        if (nodeIds.length === 0) return;
        // Find current bounding box
        var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        nodeIds.forEach(function(id) {{
          if (positions[id].x < minX) minX = positions[id].x;
          if (positions[id].x > maxX) maxX = positions[id].x;
          if (positions[id].y < minY) minY = positions[id].y;
          if (positions[id].y > maxY) maxY = positions[id].y;
        }});
        // Stretch X by 1.8x, compress Y by 0.7x to favor width
        var cx = (minX + maxX) / 2;
        var cy = (minY + maxY) / 2;
        nodeIds.forEach(function(id) {{
          network.moveNode(id,
            cx + (positions[id].x - cx) * 1.8,
            cy + (positions[id].y - cy) * 0.7
          );
        }});
        // Fit to screen
        network.fit({{ animation: {{ duration: 500, easingFunction: 'easeInOutQuad' }} }});
      }});
    }}
  }}, 100);
}});
</script>
"""

html = open(OUT_PATH, encoding="utf-8").read()
html = html.replace("<head>", "<head>" + style_reset, 1)
html = html.replace("<body>", "<body>" + title_html, 1)
html = html.replace("</body>", override_script + "</body>", 1)
open(OUT_PATH, "w", encoding="utf-8").write(html)

size_kb = os.path.getsize(OUT_PATH) / 1024
print(f"\nSaved: {OUT_PATH}")
print(f"Size:  {size_kb:.1f} KB")
