"""
MC1 Data Preprocessing Script
IS428 Visual Analytics — AY2025-2026 Term 2
Transforms mc1_nodes.csv and mc1_edges.csv into task-specific Tableau-ready CSVs.

Output files (14 CSVs in Data/mc1_csv/processed/):
  Task 1 (Charles): task1_a_who_inspired_sailor, task1_b_sailor_collaborations,
                    task1_c_oceanus_impact_timeline
  Task 2 (Klara):   task2_of_influence_out, task2_of_influence_in,
                    task2_genre_summary, task2_top_artists_influenced
  Task 3 (Radim):   task3_notable_works, task3_artist_notoriety,
                    task3_of_candidates
  Shared:           lookup_nodes_clean, lookup_edges_clean
  Network viz:      nodes, edges
"""

import pandas as pd
import numpy as np
import os

RAW_DIR = 'Data/mc1_csv/raw'
OUT_DIR = 'Data/mc1_csv/processed'
NODES_PATH = 'Data/mc1_csv/raw/mc1_nodes.csv'
EDGES_PATH = 'Data/mc1_csv/raw/mc1_edges.csv'

SAILOR_ID = 17255
BANDMATE_IDS = [17256, 17257, 17258, 17259]
IVY_ECHOES_GROUP = 17260
IVY_MEMBERS = set(BANDMATE_IDS) | {SAILOR_ID}
BANDMATE_NAMES = {
    17256: 'Maya Jensen',
    17257: 'Lila "Lilly" Hartman',
    17258: 'Jade Thompson',
    17259: 'Sophie Ramirez',
}

INFLUENCE_TYPES = ['InStyleOf', 'InterpolatesFrom', 'CoverOf',
                   'DirectlySamples', 'LyricalReferenceTo']
COLLAB_TYPES = ['PerformerOf', 'ComposerOf', 'LyricistOf', 'ProducerOf']

# Human-readable name mappings for task 1
INFLUENCE_NAME_MAP = {
    'InStyleOf': 'Inspired by Style',
    'InterpolatesFrom': 'Melody Interpolation',
    'CoverOf': 'Cover',
    'DirectlySamples': 'Direct Sample',
    'LyricalReferenceTo': 'Lyrical Reference',
}
COLLAB_NAME_MAP = {
    'PerformerOf': 'Performer',
    'ComposerOf': 'Composer',
    'LyricistOf': 'Lyricist',
    'ProducerOf': 'Producer',
}

# Task 1c: Oceanus Folk work IDs (Sailor's local OF network, 81 works)
TASK1C_OF_WORK_IDS = {
    16988, 16989, 16990, 16991, 16992, 17047, 17048, 17049, 17050, 17051,
    17052, 17053, 17121, 17122, 17123, 17124, 17125, 17231, 17232, 17233,
    17234, 17247, 17251, 17252, 17253, 17254, 17261, 17262, 17263, 17264,
    17265, 17266, 17267, 17268, 17269, 17270, 17271, 17272, 17273, 17274,
    17275, 17276, 17277, 17278, 17279, 17280, 17281, 17282, 17283, 17284,
    17285, 17286, 17287, 17288, 17289, 17290, 17291, 17292, 17293, 17294,
    17300, 17301, 17302, 17303, 17315, 17316, 17317, 17350, 17351, 17352,
    17353, 17354, 17356, 17357, 17358, 17359, 17360, 17362, 17363, 17410,
    17411,
}

# Task 1c: Breakthrough year for Sailor Shift
BREAKTHROUGH_YEAR = 2028

# Task 1c: OF-related genres (used to filter artists for the impact timeline)
OF_RELATED_GENRES = {'Oceanus Folk', 'Celtic Folk', 'Sea Shanties', 'Acoustic Folk'}


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


def save_utf16_tsv(df, filename):
    """Save as UTF-16 LE tab-separated (matches Charles's Tableau export format)."""
    path = os.path.join(OUT_DIR, filename)
    df.to_csv(path, index=False, sep='\t', encoding='utf-16')
    print(f'  Saved {filename}: {len(df):,} rows (UTF-16 TSV)')


def compute_main_genre(artist_ids, edges_df, nodes_df):
    """Compute most-common genre among each artist's works."""
    collab = edges_df[
        edges_df['source'].isin(artist_ids) &
        edges_df['edge_type'].isin(COLLAB_TYPES)
    ]
    merged = collab.merge(nodes_df[['id', 'genre']], left_on='target',
                          right_on='id', how='left')
    return merged.groupby('source')['genre'].agg(
        lambda x: x.value_counts().index[0] if len(x) > 0 else ''
    )


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

# Sailor's works (via collaboration edges from Sailor)
sailor_work_edges = edges[
    (edges['source'] == SAILOR_ID) & (edges['edge_type'].isin(COLLAB_TYPES))
]
sailor_work_ids = set(sailor_work_edges['target'].values)

# Main genre per artist (for task1b and task1c)
all_person_ids = set(
    nodes[nodes['node_type'].isin(['Person', 'MusicalGroup'])]['id']
)
_main_genre_map = compute_main_genre(all_person_ids, edges, nodes)

# ── FILE 1: task1_a_who_inspired_sailor.csv ──
# Influence edges FROM Sailor's works + FROM Sailor (person) to inspirations
infl_from_works = edges[
    edges['source'].isin(sailor_work_ids) &
    edges['edge_type'].isin(INFLUENCE_TYPES)
].copy()
infl_from_works['_is_person'] = 0

infl_from_person = edges[
    (edges['source'] == SAILOR_ID) &
    edges['edge_type'].isin(INFLUENCE_TYPES)
].copy()
infl_from_person['_is_person'] = 1

all_infl = pd.concat([infl_from_works, infl_from_person], ignore_index=True)

rows_a = []
for _, e in all_infl.iterrows():
    insp = node_lookup.loc[int(e['target'])]
    if e['_is_person'] == 0:
        sw = node_lookup.loc[int(e['source'])]
        rows_a.append({
            'Influence Type': INFLUENCE_NAME_MAP[e['edge_type']],
            'Inspiration Genre': insp['genre'] if pd.notna(insp.get('genre')) else '',
            'Inspiration Id': int(e['target']),
            'Inspiration Is Notable': True if insp.get('notable') == True else np.nan,
            'Inspiration Name': insp['name'],
            'Inspiration Node Type': insp['node_type'],
            'Inspiration Release Year': float(insp.get('release_date', '')) if insp.get('release_date', '') != '' else np.nan,
            'Sailor Work Genre': sw['genre'] if pd.notna(sw.get('genre')) else '',
            'Sailor Work Id': int(e['source']),
            'Sailor Work Name': sw['name'],
            'Sailor Work Notable': True if sw.get('notable') == True else np.nan,
            'Sailor Work Notoriety Year': np.nan,
            'Sailor Work Release Year': float(sw.get('release_date', '')) if sw.get('release_date', '') != '' else np.nan,
            'Source Is Person': 0,
        })
    else:
        rows_a.append({
            'Influence Type': INFLUENCE_NAME_MAP[e['edge_type']],
            'Inspiration Genre': insp['genre'] if pd.notna(insp.get('genre')) else '',
            'Inspiration Id': int(e['target']),
            'Inspiration Is Notable': True if insp.get('notable') == True else np.nan,
            'Inspiration Name': insp['name'],
            'Inspiration Node Type': insp['node_type'],
            'Inspiration Release Year': np.nan,
            'Sailor Work Genre': '',
            'Sailor Work Id': SAILOR_ID,
            'Sailor Work Name': 'Sailor Shift',
            'Sailor Work Notable': np.nan,
            'Sailor Work Notoriety Year': np.nan,
            'Sailor Work Release Year': np.nan,
            'Source Is Person': 1,
        })

task1_a = pd.DataFrame(rows_a)
save_utf16_tsv(task1_a, 'task1_a_who_inspired_sailor.csv')

# ── FILE 2: task1_b_sailor_collaborations.csv ──
# All collaboration edges on Sailor's 38 works, with person metadata
all_collabs = edges[
    edges['target'].isin(sailor_work_ids) & edges['edge_type'].isin(COLLAB_TYPES)
].copy()

rows_b = []
for _, e in all_collabs.iterrows():
    person = node_lookup.loc[int(e['source'])]
    work = node_lookup.loc[int(e['target'])]
    pid = int(e['source'])
    rd = work.get('release_date', '')
    wd = work.get('written_date', '')
    nd = work.get('notoriety_date', '')

    rows_b.append({
        'Collaboration Type': COLLAB_NAME_MAP.get(e['edge_type'], e['edge_type']),
        'Person Genre': person['genre'] if pd.notna(person.get('genre')) else np.nan,
        'Person Id': pid,
        'Person Main Genre': _main_genre_map.get(pid, ''),
        'Person Name': person['name'],
        'Person Type': 'Musical Group' if person['node_type'] == 'MusicalGroup' else person['node_type'],
        'Work Genre': work['genre'] if pd.notna(work.get('genre')) else '',
        'Work Id': int(e['target']),
        'Work Is Notable': bool(work.get('notable')) if pd.notna(work.get('notable')) else False,
        'Work Name': work['name'],
        'Work Node Type': work['node_type'],
        'Work Notoriety Year': nd if nd != '' else np.nan,
        'Work Release Year': int(float(rd)) if rd != '' and pd.notna(rd) else np.nan,
        'Work Written Year': float(wd) if wd != '' and pd.notna(wd) else np.nan,
        'Is Ivy Member': 1 if pid in IVY_MEMBERS else 0,
        'Is Sailor': 1 if pid == SAILOR_ID else 0,
    })

task1_b = pd.DataFrame(rows_b)
save_utf16_tsv(task1_b, 'task1_b_sailor_collaborations.csv')

# ── FILE 3: task1_c_oceanus_impact_timeline.csv ──
# OF-related artists collaborating on the 81 Oceanus Folk works, with Era
of_collabs = edges[
    edges['target'].isin(TASK1C_OF_WORK_IDS) &
    edges['edge_type'].isin(COLLAB_TYPES)
].copy()

# Filter to artists whose main genre is OF-related
of_collab_artists = set(of_collabs['source'].unique())
of_artists = {
    aid for aid in of_collab_artists
    if aid in _main_genre_map and _main_genre_map[aid] in OF_RELATED_GENRES
}

of_collabs = of_collabs[of_collabs['source'].isin(of_artists)]

rows_c = []
for _, e in of_collabs.iterrows():
    artist = node_lookup.loc[int(e['source'])]
    work = node_lookup.loc[int(e['target'])]
    aid = int(e['source'])
    rd = work.get('release_date', '')
    wd = work.get('written_date', '')
    nd = work.get('notoriety_date', '')

    # Determine Era based on work release year vs breakthrough year
    try:
        release_yr = int(float(rd))
        if release_yr < BREAKTHROUGH_YEAR:
            era = 'Before Breakthrough'
        elif release_yr == BREAKTHROUGH_YEAR:
            era = 'Breakthrough Year'
        else:
            era = 'After Breakthrough'
    except (ValueError, TypeError):
        era = ''

    rows_c.append({
        'Artist Id': aid,
        'Artist Main Genre': _main_genre_map.get(aid, ''),
        'Artist Name': artist['name'],
        'Artist Type': artist['node_type'],
        'Era': era,
        'Is Ivy Member': 'Yes' if aid in IVY_MEMBERS else 'No',
        'Relation Type': COLLAB_NAME_MAP.get(e['edge_type'], e['edge_type']),
        'Work Genre': work['genre'] if pd.notna(work.get('genre')) else '',
        'Work Id': int(e['target']),
        'Work Is Notable': bool(work.get('notable')) if pd.notna(work.get('notable')) else False,
        'Work Name': work['name'],
        'Work Notoriety Year': nd if nd != '' and pd.notna(nd) else np.nan,
        'Work Release Year': int(float(rd)) if rd != '' and pd.notna(rd) else np.nan,
        'Work Written Year': float(wd) if wd != '' and pd.notna(wd) else np.nan,
        'Is Sailor': 1 if aid == SAILOR_ID else 0,
    })

task1_c = pd.DataFrame(rows_c)
save_utf16_tsv(task1_c, 'task1_c_oceanus_impact_timeline.csv')


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

# FILE 8: task2_top_artists_influenced.csv
# Top 30 artists influenced by Oceanus Folk, traced via PerformerOf edges.
# 1. Start from of_out (OF works → non-OF targets via influence edges)
# 2. Filter to targets outside OF genre
# 3. Trace PerformerOf edges from artists to those influenced works
# 4. Aggregate per artist: count of influenced works, count of notable works,
#    and primary genre (most frequent genre among their influenced works)
influenced_targets = of_out[of_out['target_genre'] != 'Oceanus Folk'].copy()
influenced_work_ids = set(influenced_targets['target_id'].values)

# Trace PerformerOf to find the artist behind each influenced work
performer_edges = edges[
    (edges['edge_type'] == 'PerformerOf') &
    edges['target'].isin(influenced_work_ids)
]
# Merge with node info for the artist
perf_with_work = performer_edges.merge(
    nodes[['id', 'name']].rename(columns={'id': 'artist_id', 'name': 'artist_name'}),
    left_on='source', right_on='artist_id', how='left'
)
# Merge with work info for genre and notable status
perf_with_work = perf_with_work.merge(
    nodes[['id', 'genre', 'notable']].rename(
        columns={'id': 'work_id', 'genre': 'work_genre', 'notable': 'work_notable'}),
    left_on='target', right_on='work_id', how='left'
)

# Aggregate per artist
artist_agg = perf_with_work.groupby('artist_name').agg(
    influenced_works_count=('work_id', 'nunique'),
    notable_works_count=('work_notable', lambda x: x.sum()),
    primary_genre=('work_genre', lambda x: x.value_counts().index[0] if len(x) > 0 else ''),
).reset_index()
artist_agg['notable_works_count'] = artist_agg['notable_works_count'].astype(int)
artist_agg = artist_agg.sort_values('influenced_works_count', ascending=False).head(30)
artist_agg = artist_agg[['artist_name', 'influenced_works_count',
                          'notable_works_count', 'primary_genre']]
save(artist_agg, 'task2_top_artists_influenced.csv')


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

# ─────────────────────────────────────────────────────────
# SECTION F — TASK 1 NETWORK VISUALISATION INPUTS
# ─────────────────────────────────────────────────────────
# Charles's curated 204-node subgraph used by the Pyvis
# scripts (task1_network_collaboration.py and
# task1_network_influence.py).

print('\n=== SECTION F: Task 1 Network Files ===')

# --- Classify nodes into roles ---
sailor_circle = IVY_MEMBERS | {IVY_ECHOES_GROUP}

# Works that Sailor + bandmates + Ivy Echoes produced
sc_collab_edges = edges[
    edges['source'].isin(sailor_circle) &
    edges['edge_type'].isin(COLLAB_TYPES)
]
sc_work_ids = set(sc_collab_edges['target'].values)

# Direct collaborators: persons/groups (not in sailor_circle) who share works with the circle
dc_edges = edges[
    edges['target'].isin(sc_work_ids) &
    edges['edge_type'].isin(COLLAB_TYPES) &
    ~edges['source'].isin(sailor_circle)
]
direct_collab_ids = set(dc_edges['source'].values)

# Collaborator works: works of direct collaborators that aren't in sc_work_ids
dc_work_edges = edges[
    edges['source'].isin(direct_collab_ids) &
    edges['edge_type'].isin(COLLAB_TYPES) &
    ~edges['target'].isin(sc_work_ids)
]
collab_work_ids = set(dc_work_edges['target'].values)

# Influence: works/entities inspired by Sailor's works (or by Sailor person)
infl_from_sailor = edges[
    (edges['source'].isin(sailor_work_ids) | (edges['source'] == SAILOR_ID)) &
    edges['edge_type'].isin(INFLUENCE_TYPES)
]
inspired_sailor_ids = set(infl_from_sailor['target'].values)

# Influence from the wider Sailor circle's works
sc_infl_edges = edges[
    edges['source'].isin(sc_work_ids) & edges['edge_type'].isin(INFLUENCE_TYPES)
]
inspired_by_circle_ids = set(sc_infl_edges['target'].values) - inspired_sailor_ids

# Collect all relevant IDs
all_net_ids = (
    sailor_circle | sc_work_ids | direct_collab_ids |
    collab_work_ids | inspired_sailor_ids | inspired_by_circle_ids
)

# Build role assignment (priority order)
role_map = {}
for nid in all_net_ids:
    if nid == SAILOR_ID:
        role_map[nid] = 'Sailor Shift'
    elif nid in BANDMATE_IDS:
        role_map[nid] = 'Ivy Echoes Member'
    elif nid == IVY_ECHOES_GROUP:
        role_map[nid] = 'Ivy Echoes (Group)'
    elif nid in sc_work_ids and node_lookup.loc[nid]['node_type'] in ('Song', 'Album'):
        role_map[nid] = 'Sailor Work'
    elif nid in direct_collab_ids:
        role_map[nid] = 'Direct Collaborator'
    elif nid in collab_work_ids and node_lookup.loc[nid]['node_type'] in ('Song', 'Album'):
        role_map[nid] = 'Collaborator Work'
    elif nid in inspired_sailor_ids:
        role_map[nid] = 'Inspired Sailor'
    elif nid in inspired_by_circle_ids:
        role_map[nid] = 'Inspired By Sailor Circle'
    else:
        role_map[nid] = 'Other'

# Build nodes DataFrame
net_nodes_rows = []
for nid, role in role_map.items():
    n = node_lookup.loc[nid]
    is_sailor = 1 if nid == SAILOR_ID else 0
    is_ivy = 1 if nid in IVY_MEMBERS else 0
    genre_raw = n['genre'] if pd.notna(n.get('genre')) else np.nan
    genre_display = genre_raw if pd.notna(genre_raw) else (
        _main_genre_map.get(nid, np.nan) if nid in _main_genre_map else np.nan
    )
    net_nodes_rows.append({
        'Id': nid,
        'Label': n['name'],
        'node_type': n['node_type'],
        'role': role,
        'genre': genre_raw,
        'release_date': n.get('release_date') if n.get('release_date', '') != '' else np.nan,
        'written_date': n.get('written_date') if n.get('written_date', '') != '' else np.nan,
        'notoriety_date': n.get('notoriety_date') if n.get('notoriety_date', '') != '' else np.nan,
        'notable': n.get('notable') if pd.notna(n.get('notable')) else np.nan,
        'single': n.get('single') if pd.notna(n.get('single')) else np.nan,
        'stage_name': n.get('stage_name') if pd.notna(n.get('stage_name')) else np.nan,
        'is_sailor': is_sailor,
        'is_ivy_member': is_ivy,
        'genre_inferred': _main_genre_map.get(nid, np.nan) if n['node_type'] in ('Person', 'MusicalGroup') else np.nan,
        'genre_display': genre_display,
    })

net_nodes = pd.DataFrame(net_nodes_rows)
save(net_nodes, 'nodes.csv')

# Build edges DataFrame
edge_cat_map = {}
for et in COLLAB_TYPES:
    edge_cat_map[et] = 'Collaboration'
for et in INFLUENCE_TYPES:
    edge_cat_map[et] = 'Influence'
edge_cat_map['MemberOf'] = 'Membership'

net_edge_rows = []
net_node_ids = set(net_nodes['Id'].values)
for _, e in edges.iterrows():
    src, tgt = int(e['source']), int(e['target'])
    if src in net_node_ids and tgt in net_node_ids:
        src_n = node_lookup.loc[src]
        tgt_n = node_lookup.loc[tgt]
        src_genre = src_n['genre'] if pd.notna(src_n.get('genre')) else np.nan
        tgt_genre = tgt_n['genre'] if pd.notna(tgt_n.get('genre')) else np.nan
        src_rd = src_n.get('release_date') if src_n.get('release_date', '') != '' else np.nan
        tgt_rd = tgt_n.get('release_date') if tgt_n.get('release_date', '') != '' else np.nan
        net_edge_rows.append({
            'Source': src,
            'Target': tgt,
            'edge_type': e['edge_type'],
            'edge_category': edge_cat_map.get(e['edge_type'], 'Other'),
            'source_name': src_n['name'],
            'source_node_type': src_n['node_type'],
            'source_genre': src_genre,
            'source_release_year': float(src_rd) if pd.notna(src_rd) and src_rd != '' else np.nan,
            'target_name': tgt_n['name'],
            'target_node_type': tgt_n['node_type'],
            'target_genre': tgt_genre,
            'target_release_year': float(tgt_rd) if pd.notna(tgt_rd) and tgt_rd != '' else np.nan,
            'involves_sailor': 1 if (src == SAILOR_ID or tgt == SAILOR_ID) else 0,
            'involves_ivy': 1 if (src in IVY_MEMBERS or tgt in IVY_MEMBERS) else 0,
            'source_genre_display': src_genre if pd.notna(src_genre) else (
                _main_genre_map.get(src, np.nan) if src in _main_genre_map else np.nan
            ),
            'target_genre_display': tgt_genre if pd.notna(tgt_genre) else (
                _main_genre_map.get(tgt, np.nan) if tgt in _main_genre_map else np.nan
            ),
        })

net_edges = pd.DataFrame(net_edge_rows)
save(net_edges, 'edges.csv')


print('\n=== All files saved successfully ===')
