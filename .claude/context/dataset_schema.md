# MC1 Dataset — Full Schema Reference

## File
MC1_graph.json — directed multigraph, JSON format (NetworkX node_link_data)

## Size
- Total nodes: 17,412
- Total edges: 37,857
- Connected components: 18

## Node Types
| Type | Count | Key Fields |
|------|-------|------------|
| Person | 11,361 | name, stage_name |
| Song | 3,615 | name, genre, release_date, written_date, single, notable, notoriety_date |
| RecordLabel | 1,217 | name |
| Album | 996 | name, genre, release_date, written_date, notable, notoriety_date |
| MusicalGroup | 223 | name |

## Edge Types
| Type | Count | Meaning |
|------|-------|---------|
| PerformerOf | 13,587 | Person/Group performed Song/Album |
| RecordedBy | 3,798 | Song/Album recorded by RecordLabel |
| ComposerOf | 3,290 | Person composed Song/Album |
| ProducerOf | 3,209 | Person/Label produced Song/Album/Person/Group |
| DistributedBy | 3,013 | Song/Album distributed by RecordLabel |
| LyricistOf | 2,985 | Person wrote lyrics for Song/Album |
| InStyleOf | 2,289 | Song/Album made in style of another Song/Album/Person/Group |
| InterpolatesFrom | 1,574 | Song/Album interpolated melody from another |
| LyricalReferenceTo | 1,496 | Song/Album makes lyrical reference to another |
| CoverOf | 1,429 | Song/Album is a cover of another |
| DirectlySamples | 619 | Song/Album directly samples audio from another |
| MemberOf | 568 | Person is/was member of MusicalGroup |

## Key Facts for Analysis
- Sailor Shift: node ID 17255, 60 direct edges, 38 works (songs/albums)
- Ivy Echoes members: Maya Jensen (17256), Lila "Lilly" Hartman (17257),
  Jade Thompson (17258), Sophie Ramirez (17259)
- Oceanus Folk songs: 235 spanning 1993–2040
- Notable Oceanus Folk artists by chart appearances:
  Sailor Shift (14), Orla Seabloom (8), Beatrice Albright (8),
  Daniel O'Connell (8), Copper Canyon Ghosts (7), Drowned Harbor (5)
- Genres most influenced by Oceanus Folk:
  Indie Folk (23), Dream Pop (23), Desert Rock (20),
  Space Rock (16), Synthwave (11), Americana (10)
- Total notable songs with notoriety date: 516
- Total notable albums with notoriety date: 133
- Artists with 3+ notable works: 34

## Popularity Fields
- notable (boolean): whether song/album appeared on a top chart
- notoriety_date (string year): when it first appeared on a top chart
These two fields are the primary measure of an artist's "rise" for Task 3.

## All 26 Genres
Acoustic Folk, Alternative Rock, Americana, Avant-Garde Folk, Blues Rock,
Celtic Folk, Darkwave, Desert Rock, Doom Metal, Dream Pop, Emo/Pop Punk,
Indie Folk, Indie Pop, Indie Rock, Jazz Surf Rock, Lo-Fi Electronica,
Oceanus Folk, Post-Apocalyptic Folk, Psychedelic Rock, Sea Shanties,
Southern Gothic Rock, Space Rock, Speed Metal, Symphonic Metal,
Synthpop, Synthwave
