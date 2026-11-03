# Original 8×8 source-tile lineage (ART-4K)

This is a **source-only, ROM-authenticated experimental classifier of 2D tile reuse**, separate from draft #3060's original palette-index versus experimental 2026 GLB part-ID hypotheses. It does not assert 1994 anatomical parts, live emulator chronology or source 3D geometry.

The existing bounded SNES frame compositor already knows which 8×8 planar 4bpp payload occupies each of the original 30 player staging positions. The new `audit_original_racer_tile_lineage.py` reconstructs the final 64×64 index plane with each occupied slot's original packed word, ROM content SHA-256 and opaque/nonopaque index counts. Its first independent gate is the previously merged #3057 original-ROM audit: exact USA ROM SHA, frozen historical registry SHA, source corpus manifest and 59 registered source RGBA round trips. Its second gate compares the newly assembled 64×64 index/tile-written planes byte-for-byte against the previously authenticated original compositor for every representation.

A tile's exact **32-byte ROM payload SHA**, not an arbitrary cell ID or a palette RGB colour, defines tile content identity. The scorer groups the 59 descriptions into **35 distinct original 4bpp index planes**. If two original silhouettes share a nonblank tile payload, that is evidence of **literal 2D source reuse**. Moving the same tile to another slot does not establish a rigid 3D component, pivot, source-camera view, or chronological transition. Different palette colourways of the identical index plane cannot inflate independent evidence. Blank payloads are excluded from positive cross-pose matches. A different tile source address may contain the same exact content; distinguish content identity from byte address.

The numerical summary records distinct tile hashes, reused nonblank tiles, moved assets and original-mask pair overlaps. The summary deliberately contains no 8×8 pixel arrays or inferred body-part assignments. A historical source-asset match may reflect common shading/edges and isn't by itself proof of a specific 3D part.

Run ROM-free controls:

```sh
python3 -m unittest tests.unit.test_audit_original_racer_tile_lineage
```

With the frozen original-source PNG archive and its SHA-matched historical registry:

```sh
python3 -m tools.art.audit_original_racer_tile_lineage \
 --rom reference/roms/retail/Uniracers_USA.sfc \
 --registry /path/to/historical/racer-hd-replacement-prototype.json \
 --source-zip /path/to/authenticated/source-corpus.zip \
 --out /private/new/original-tile-lineage.json
```

**Admission:** no shipping art/release gate, no GLB changes, no novel PPU timing, no asset redistribution and no claim of source anatomical segmentation. Real-ROM producer execution and an independent exact-head code/CI review are required before treating aggregate tile-reuse counts as measured evidence. Any numeric output must carry exact source and registry hashes.
