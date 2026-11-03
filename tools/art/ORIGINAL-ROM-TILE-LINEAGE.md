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


## Authenticated original-ROM result (November 3, 2026)

One-off [original source workflow #41554638043](https://github.com/gamesbyian/UR-Recomp/actions/runs/41554638043) **passed**, using the exact frozen 41-PNG original archive, historical registry and USA-ROM hash already required by the merged #3057 audit. The [full numeric report (artifact #13194250673)](https://github.com/gamesbyian/UR-Recomp/actions/runs/41554638043/artifacts/13194250673), SHA-256 `cccb78328307003b3f8148aa20ef7cca27c905e77610be2b3ffd1aa7e7d5f33f`, is retained only until November 10, 2026. Compact durable evidence is in `analysis/data/racer-original-source-tile-lineage-summary-20261103.json`.

Across **59 original registered source descriptions**, the authentic original content comprises **41 RGBA images** and **35 distinct 4bpp source index planes**. Those 35 planes contain **250 distinct nonzero 8×8 planar tile payloads** (251 if counting the zero tile). Exactly **62** nonzero payloads recur in more than one distinct index plane; **170 of the 595 possible unordered distinct-plane pairs** share at least one nonzero tile. Among those 170 positive pairs the median is eight shared distinct nonzero tiles (maximum ten).

**Important negative result:** only **one nonzero tile payload** occurs at more than one source tile-cell position. Its exact byte digest is `36a2afe3cc14227c4f656a57bd9dcfa5c2c0b1028afe3ecd581613ecde6221d0`, at original 5×6 staging slots `[row 4, column 3]` and `[row 4, column 4]` in two different source index planes. The total `tile_payloads_observed_at_multiple_source_slots` is two **only because it includes the all-zero tile**; the additional named nonblank counter is one. No 3D translation, rigid wheel fragment or animated bone is proven by the source reuse.

As a genuinely different reconstruction route, the 41 source PNGs were independently decoded and SHA-verified, their exact palette indices regenerated from the previously authenticated RGB-to-index lookup, and each opaque 8×8 index region re-encoded into 32-byte SNES planar 4bpp. This independent archived-PNG route reproduced **250 unique nonzero tile payload hashes, 62 reused across unique index planes, one moved nonzero payload, and 170 positive index-plane pairs**. It does not independently prove that the original 1994 game displayed these authored-registry frames in any particular temporal order.

The next discriminator should prioritize **live original PPU/OAM frame capture and source pose pairing**. This source-only tile census shows that treating a shared packed tile as a movable 3D mesh component would manufacture unsupported anatomy. At minimum, independent held-out pose evaluations should quantify asset-content overlap as well as avoiding identical binary silhouettes: a silhouette-disjoint pair can still reuse exact 8×8 original source content.
