# QA08 authenticated temporal source census

This is a bounded research-only census of eight real source-qualified PPU
palette observations over guest frames 5176–5186. The input archive is
SHA-256 pinned and never committed. The only observed transitions are at
5177 and 5184 with eight changed anchors each.

Run: \`python3 research/qa08/qa08_temporal_source_census.py <private-source-archive.zip>\`

The synthetic tests exercise missing and duplicate anchors, wrong phase
boundaries and palette-class corruption. A source-local temporal palette
pattern is **not** original/native PPU pixel parity, causal localization,
physical Windows qualification, or release QA acceptance.
