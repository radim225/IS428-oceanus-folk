"""
MC1 Data Preprocessing Script
IS428 Visual Analytics — AY2025-2026 Term 2
Transforms mc1_nodes.csv and mc1_edges.csv into 12 Tableau-ready CSVs.

Output files:
  Task 1 (Charles): task1_sailor_works, task1_influence_edges,
                    task1_all_collaborators, task1_bandmates
  Task 2 (Klara):   task2_of_influence_out, task2_of_influence_in,
                    task2_genre_summary
  Task 3 (Radim):   task3_notable_works, task3_artist_notoriety,
                    task3_of_candidates
  Shared:           lookup_nodes_clean, lookup_edges_clean
"""

import pandas as pd
import os

RAW_DIR = 'Data/mc1_csv/raw'
OUT_DIR = 'Data/mc1_csv/processed'
NODES_PATH = 'Data/mc1_csv/raw/mc1_nodes.csv'
EDGES_PATH = 'Data/mc1_csv/raw/mc1_edges.csv'

SAILOR_ID = 17255
BANDMATE_IDS = [17256, 17257, 17258, 17259]
BANDMATE_NAMES = {
    17256: 'Maya Jensen',
    17257: 'Lila "Lilly" Hartman',
    17258: 'Jade Thompson',
    17259: 'Sophie Ramirez',
}

INFLUENCE_TYPES = ['InStyleOf', 'InterpolatesFrom', 'CoverOf',
                   'DirectlySamples', 'LyricalReferenceTo']
COLLAB_TYPES = ['PerformerOf', 'ComposerOf', 'LyricistOf', 'ProducerOf']


# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────

def clean_date_col(series):
    """Convert a year column (may be float or string 'NA') to clean int-year string."""
    numeric = pd.to_numeric(series, errors='coerce')
    as_int = numeric.astype('Int64')
    as_str = as_int.astype(str)
    as_str = as_str.replace({'<NA>': '', 'nan': '', 'None': ''})
    return as_str


def save(df, filename):
    path = os.path.join(OUT_DIR, filename)
    df.to_csv(path, index=False)
    print(f'  Saved {filename}: {len(df):,} rows')


# ─────────────────────────────────────────────────────────
# SECTION A — LOAD AND CLEAN
# ─────────────────────────────────────────────────────────

print('\n=== SECTION A: Loading and cleaning data ===')

nodes = pd.read_csv(NODES_PATH, na_values=['NA', ''])
edges = pd.read_csv(EDGES_PATH, na_values=['NA', ''])

# Rename columns to snake_case for easier access
nodes.rename(columns={'Node Type': 'node_type'}, inplace=True)
edges.rename(columns={'Edge Type': 'edge_type'}, inplace=True)

# Boolean columns
nodes['notable'] = nodes['notable'].fillna(False).astype(bool)
nodes['single'] = nodes['single'].fillna(False).astype(bool)

# Date columns
nodes['release_date'] = clean_date_col(nodes['release_date'])
nodes['notoriety_date'] = clean_date_col(nodes['notoriety_date'])
nodes['written_date'] = clean_date_col(nodes['written_date'])

# String columns
nodes['genre'] = nodes['genre'].fillna('Unknown')
nodes['stage_name'] = nodes['stage_name'].fillna('')
nodes['name'] = nodes['name'].str.strip()

# Ensure id is int for merging
nodes['id'] = nodes['id'].astype(int)
edges['source'] = edges['source'].astype(int)
edges['target'] = edges['target'].astype(int)

# Build lookup dict: id → row Series
node_lookup = nodes.set_index('id')

# Summary
print(f'\nTotal nodes: {len(nodes):,}')
print(nodes['node_type'].value_counts().to_string())
print(f'\nTotal edges: {len(edges):,}')
print(edges['edge_type'].value_counts().to_string())
of_count = nodes[nodes['genre'] == 'Oceanus Folk']
print(f'\nOceanus Folk songs/albums: {len(of_count):,}')
sailor_present = SAILOR_ID in nodes['id'].values
print(f'Sailor Shift (ID {SAILOR_ID}) present: {sailor_present}')


# ─────────────────────────────────────────────────────────
# SECTION B — TASK 1 (Charles — Sailor Shift Career)
# ─────────────────────────────────────────────────────────

print('\n=== SECTION B: Task 1 — Sailor Shift Career ===')

# FILE 1: task1_sailor_works.csv
sailor_work_edges = edges[
    (edges['source'] == SAILOR_ID) &
    (edges['edge_type'].isin(COLLAB_TYPES))
].copy()

sailor_works = sailor_work_edges.merge(
    nodes[['id', 'node_type', 'name', 'genre', 'release_date',
           'written_date', 'single', 'notable', 'notoriety_date']],
    left_on='target', right_on='id', how='inner'
)
sailor_works = sailor_works[
    sailor_works['node_type'].isin(['Song', 'Album'])
].copy()
sailor_works = sailor_works.rename(columns={
    'target': 'work_id',
    'name': 'work_name',
    'edge_type': 'role',
})
sailor_works = sailor_works[
    ['work_id', 'work_name', 'node_type', 'genre', 'release_date',
     'written_date', 'single', 'notable', 'notoriety_date', 'role']
].drop_duplicates(subset=['work_id', 'role'])
sailor_works = sailor_works.sort_values('release_date')
save(sailor_works, 'task1_sailor_works.csv')

# FILE 2: task1_influence_edges.csv
infl_edges = edges[
    ((edges['source'] == SAILOR_ID) | (edges['target'] == SAILOR_ID)) &
    (edges['edge_type'].isin(INFLUENCE_TYPES))
].copy()

infl_edges = infl_edges.merge(
    nodes[['id', 'name', 'node_type', 'genre']].rename(columns={
        'id': 'source', 'name': 'source_name',
        'node_type': 'source_type', 'genre': 'source_genre'
    }),
    on='source', how='left'
).merge(
    nodes[['id', 'name', 'node_type', 'genre']].rename(columns={
        'id': 'target', 'name': 'target_name',
        'node_type': 'target_type', 'genre': 'target_genre'
    }),
    on='target', how='left'
)
infl_edges['direction'] = infl_edges['source'].apply(
    lambda x: 'Sailor_influenced_others' if x == SAILOR_ID else 'others_influenced_Sailor'
)
infl_edges = infl_edges.rename(columns={'edge_type': 'edge_type', 'source': 'source_id', 'target': 'target_id'})
infl_edges = infl_edges[
    ['edge_type', 'source_id', 'source_name', 'source_type', 'source_genre',
     'target_id', 'target_name', 'target_type', 'target_genre', 'direction']
]
save(infl_edges, 'task1_influence_edges.csv')

# FILE 3: task1_all_collaborators.csv
all_collab = edges[
    (edges['source'] == SAILOR_ID) | (edges['target'] == SAILOR_ID)
].copy()
all_collab = all_collab[all_collab['source'] != all_collab['target']]  # no self-loops

all_collab = all_collab.merge(
    nodes[['id', 'name', 'node_type']].rename(columns={
        'id': 'source', 'name': 'source_name', 'node_type': 'source_type'
    }),
    on='source', how='left'
).merge(
    nodes[['id', 'name', 'node_type']].rename(columns={
        'id': 'target', 'name': 'target_name', 'node_type': 'target_type'
    }),
    on='target', how='left'
)
all_collab = all_collab.rename(columns={
    'edge_type': 'edge_type', 'source': 'source_id', 'target': 'target_id'
})
all_collab = all_collab[
    ['edge_type', 'source_id', 'source_name', 'source_type',
     'target_id', 'target_name', 'target_type']
]
save(all_collab, 'task1_all_collaborators.csv')

# FILE 4: task1_bandmates.csv
bm_edges = edges[
    edges['source'].isin(BANDMATE_IDS) | edges['target'].isin(BANDMATE_IDS)
].copy()

bm_edges = bm_edges.merge(
    nodes[['id', 'name', 'node_type']].rename(columns={
        'id': 'source', 'name': 'source_name', 'node_type': 'source_type'
    }),
    on='source', how='left'
).merge(
    nodes[['id', 'name', 'node_type', 'genre', 'release_date', 'notable']].rename(columns={
        'id': 'target', 'name': 'target_name', 'node_type': 'target_type',
        'genre': 'target_genre', 'release_date': 'target_release_date',
        'notable': 'target_notable'
    }),
    on='target', how='left'
)

def get_bandmate_name(row):
    for bid in BANDMATE_IDS:
        if row['source'] == bid:
            return BANDMATE_NAMES[bid]
        if row['target'] == bid:
            return BANDMATE_NAMES[bid]
    return ''

bm_edges['bandmate_name'] = bm_edges.apply(get_bandmate_name, axis=1)
bm_edges = bm_edges.rename(columns={
    'edge_type': 'edge_type', 'source': 'source_id', 'target': 'target_id'
})
bm_edges = bm_edges[
    ['bandmate_name', 'edge_type', 'source_id', 'source_name', 'source_type',
     'target_id', 'target_name', 'target_type', 'target_genre',
     'target_release_date', 'target_notable']
]
save(bm_edges, 'task1_bandmates.csv')


# ─────────────────────────────────────────────────────────
# SECTION C — TASK 2 (Klara — Oceanus Folk Genre Spread)
# ─────────────────────────────────────────────────────────

print('\n=== SECTION C: Task 2 — Oceanus Folk Genre Spread ===')

of_ids = set(nodes[nodes['genre'] == 'Oceanus Folk']['id'].values)

src_cols = nodes[['id', 'name', 'genre', 'release_date', 'notable', 'notoriety_date']].rename(columns={
    'id': 'source_id', 'name': 'source_name', 'genre': 'source_genre',
    'release_date': 'source_release_date', 'notable': 'source_notable',
    'notoriety_date': 'source_notoriety_date'
})
tgt_cols = nodes[['id', 'name', 'genre', 'release_date', 'notable']].rename(columns={
    'id': 'target_id', 'name': 'target_name', 'genre': 'target_genre',
    'release_date': 'target_release_date', 'notable': 'target_notable'
})

# FILE 5: task2_of_influence_out.csv
of_out_e = edges[
    edges['source'].isin(of_ids) & edges['edge_type'].isin(INFLUENCE_TYPES)
].rename(columns={'edge_type': 'edge_type', 'source': 'source_id', 'target': 'target_id'})
of_out = of_out_e[['edge_type', 'source_id', 'target_id']].merge(src_cols, on='source_id', how='left').merge(tgt_cols, on='target_id', how='left')
of_out = of_out[['edge_type', 'source_id', 'source_name', 'source_genre',
                  'source_release_date', 'source_notable', 'source_notoriety_date',
                  'target_id', 'target_name', 'target_genre',
                  'target_release_date', 'target_notable']]
of_out = of_out.sort_values('source_release_date')
save(of_out, 'task2_of_influence_out.csv')

# FILE 6: task2_of_influence_in.csv
of_in_e = edges[
    edges['target'].isin(of_ids) & edges['edge_type'].isin(INFLUENCE_TYPES)
].rename(columns={'edge_type': 'edge_type', 'source': 'source_id', 'target': 'target_id'})
of_in = of_in_e[['edge_type', 'source_id', 'target_id']].merge(src_cols, on='source_id', how='left').merge(tgt_cols, on='target_id', how='left')
of_in = of_in[['edge_type', 'source_id', 'source_name', 'source_genre',
                'source_release_date', 'source_notable', 'source_notoriety_date',
                'target_id', 'target_name', 'target_genre',
                'target_release_date', 'target_notable']]
of_in = of_in.sort_values('target_release_date')
save(of_in, 'task2_of_influence_in.csv')

# FILE 7: task2_genre_summary.csv
out_summary = (
    of_out.groupby(['source_genre', 'target_genre', 'edge_type'])
    .size().reset_index(name='connection_count')
)
out_summary['direction'] = 'outbound'
out_summary.rename(columns={'source_genre': 'source_genre', 'target_genre': 'target_genre'}, inplace=True)

in_summary = (
    of_in.groupby(['source_genre', 'target_genre', 'edge_type'])
    .size().reset_index(name='connection_count')
)
in_summary['direction'] = 'inbound'

genre_summary = pd.concat([out_summary, in_summary], ignore_index=True)
# Remove rows where both source and target are Oceanus Folk
genre_summary = genre_summary[
    ~((genre_summary['source_genre'] == 'Oceanus Folk') &
      (genre_summary['target_genre'] == 'Oceanus Folk'))
]
save(genre_summary, 'task2_genre_summary.csv')


# ─────────────────────────────────────────────────────────
# SECTION D — TASK 3 (Radim — Rising Star Prediction)
# ─────────────────────────────────────────────────────────

print('\n=== SECTION D: Task 3 — Rising Star Prediction ===')

# FILE 8: task3_notable_works.csv
notable_nodes = nodes[
    (nodes['notable'] == True) & (nodes['notoriety_date'] != '')
].copy()
notable_ids = set(notable_nodes['id'].values)

performer_edges = edges[
    (edges['edge_type'] == 'PerformerOf') & (edges['target'].isin(notable_ids))
].copy()
performer_edges = performer_edges.rename(columns={'source': 'performer_id', 'target': 'work_id'})

notable_works = performer_edges[['performer_id', 'work_id']].merge(
    notable_nodes[['id', 'name', 'node_type', 'genre', 'release_date',
                   'written_date', 'notoriety_date', 'notable']].rename(columns={'id': 'work_id', 'name': 'work_name'}),
    on='work_id', how='inner'
).merge(
    nodes[['id', 'name', 'node_type']].rename(columns={
        'id': 'performer_id', 'name': 'performer_name', 'node_type': 'performer_type'
    }),
    on='performer_id', how='left'
)
notable_works = notable_works[
    ['work_id', 'work_name', 'node_type', 'genre', 'release_date',
     'written_date', 'notoriety_date', 'notable', 'performer_id',
     'performer_name', 'performer_type']
]
notable_works = notable_works.sort_values('notoriety_date')
save(notable_works, 'task3_notable_works.csv')

# FILE 9: task3_artist_notoriety.csv
def safe_year_diff(s):
    try:
        years = pd.to_numeric(s, errors='coerce').dropna()
        if len(years) < 2:
            return 0
        return int(years.max() - years.min())
    except Exception:
        return 0

artist_groups = notable_works.groupby('performer_name')
notoriety_rows = []
for performer_name, grp in artist_groups:
    total = len(grp)
    first_nd = grp['notoriety_date'].replace('', pd.NA).dropna().min() if not grp['notoriety_date'].replace('', pd.NA).dropna().empty else ''
    latest_nd = grp['notoriety_date'].replace('', pd.NA).dropna().max() if not grp['notoriety_date'].replace('', pd.NA).dropna().empty else ''
    genres = ', '.join(sorted(grp['genre'].dropna().unique()))
    span = safe_year_diff(grp['release_date'])
    notoriety_rows.append({
        'performer_name': performer_name,
        'total_notable_works': total,
        'first_notoriety_date': first_nd,
        'latest_notoriety_date': latest_nd,
        'genres': genres,
        'years_active_span': span,
        'is_oceanus_folk_artist': 'Oceanus Folk' in genres,
    })

artist_notoriety = pd.DataFrame(notoriety_rows)
artist_notoriety = artist_notoriety.sort_values('total_notable_works', ascending=False)
save(artist_notoriety, 'task3_artist_notoriety.csv')

# FILE 10: task3_of_candidates.csv
of_artists = artist_notoriety[artist_notoriety['is_oceanus_folk_artist'] == True]['performer_name'].tolist()
of_works = notable_works[notable_works['performer_name'].isin(of_artists)].copy()

of_candidates = of_works.merge(
    artist_notoriety[['performer_name', 'total_notable_works', 'first_notoriety_date', 'years_active_span']],
    left_on='performer_name', right_on='performer_name', how='left'
)
of_candidates = of_candidates.rename(columns={'performer_name': 'artist_name', 'work_name': 'work_name'})
of_candidates = of_candidates[
    ['artist_name', 'work_name', 'genre', 'release_date', 'notoriety_date',
     'total_notable_works', 'first_notoriety_date', 'years_active_span']
]
of_candidates = of_candidates.sort_values(['artist_name', 'notoriety_date'])
save(of_candidates, 'task3_of_candidates.csv')


# ─────────────────────────────────────────────────────────
# SECTION E — SHARED LOOKUP FILES
# ─────────────────────────────────────────────────────────

print('\n=== SECTION E: Shared Lookup Files ===')

# FILE 11: lookup_nodes_clean.csv
save(nodes, 'lookup_nodes_clean.csv')

# FILE 12: lookup_edges_clean.csv
edges_clean = edges.copy()
edges_clean = edges_clean.merge(
    nodes[['id', 'name', 'node_type']].rename(columns={
        'id': 'source', 'name': 'source_name', 'node_type': 'source_type'
    }),
    on='source', how='left'
).merge(
    nodes[['id', 'name', 'node_type']].rename(columns={
        'id': 'target', 'name': 'target_name', 'node_type': 'target_type'
    }),
    on='target', how='left'
)
edges_clean = edges_clean.rename(columns={'edge_type': 'edge_type', 'source': 'source_id', 'target': 'target_id'})
edges_clean = edges_clean[
    ['edge_type', 'source_id', 'source_name', 'source_type',
     'target_id', 'target_name', 'target_type', 'key']
]
save(edges_clean, 'lookup_edges_clean.csv')

print('\n=== All files saved successfully ===')
