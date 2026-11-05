# ART-4K: authenticate old 4bpp tiles against 40 newly executed original sprites

**Experimental original 2D source-content lineage only.** The new 20-tick, two-racer Mesen source archive is authenticated (merged #3088). This experiment relates its 40 actual SNES OAM/VRAM-derived 64×64 4bpp index planes to the older, separate authored-registry 35-plane original-ROM corpus. It does not recover a 1994 3D model, camera, skeleton, animation label or owner likeness.

## Actual source result, November 3, 2026

The SHA-pinned historical PNG corpus, original 4bpp palette-index census, historical 8×8 tile-reuse graph and frozen source index-plane holdout were independently re-read from four original source-run ZIP artifacts, not trusted as a later hand-transcribed summary. Every one of 59 historical source PNGs maps back to its exact 4bpp source-index SHA. The 35 distinct index planes yield **250 distinct nonblank 8×8 index-content tiles**, plus the universal all-zero transparent tile (the original report's 251st). All **170** historical plane pairs sharing a nonblank tile and their exact overlap counts were independently reproduced.

Of the 40 actual live source planes, **one** exact source index plane belongs to the historically frozen fit set (blue tick1952), **one** to the historically frozen withheld set (red tick1601), and **38** are previously unclassified. Of those 38, **29** share at least one nonblank 8×8 tile with the old 16-plane fit group, **zero** share any nonblank tile with the old 19-plane withheld group (including the strict six), and **nine** share none with any of the old 35 planes. Across all 38 new planes there are 307 distinct nonblank tile payloads, including **247 that were absent** from the historical 35-plane corpus.

Content-leakage caution: the new 38 source planes are not independent from one another. They form 11 transitively content-connected groups of sizes 9, 8, 4, 4, 3, 3, 2, 2, 1, 1 and 1. Exactly **three connected groups of sizes 4, 4 and 1** are disconnected from the historical fit/withheld tile content. Their original player/tick identities are frozen in the source-only numerical report analysis/data/racer-original-live40-historical-tile-content-novelty-20261103.json.

The three content-independent candidates consist of (a) blue original ticks 1648,1671,1700,2011, (b) red ticks 1671,1700,1731 plus blue tick2283, and (c) blue tick2445. **They have not been assigned new fit or withheld roles.** Their existing 2026 five-GLB comparison scores have already been inspected, so those historic scores cannot be retrospectively advertised as blind holdout evaluation.

## Reproduce without emulation or GLB rendering

Offline producer: tools/art/audit_original_live40_historical_tile_novelty.py (Pillow required only for this offline source-archive reproduction). It validates each original ZIP SHA-256 and every source JSON, PNG, RGBA and reconstructed 4bpp-index plane SHA; reproduces the historic 170-edge exact-tile graph; verifies all original PPU/P6 screen correspondences from merged #3088; decodes the 40 live planes directly from genuine raw original OAM/VRAM; then computes exact nonblank tile content sharing and transitive novel-plane components. It publishes a fresh JSON report without overwriting earlier evidence.

    python3 -m tools.art.audit_original_live40_historical_tile_novelty --original-20-zip /private/original20.zip --historical-corpus-zip /private/historic-corpus.zip --historical-index-zip /private/historic-index.zip --historical-tile-zip /private/historic-tiles.zip --historical-holdout-zip /private/historic-holdout.zip --receipt analysis/data/racer-original-mesen-twenty-live-2d-screen-registrations-20261103.json --out /private/new/live40-tiles.json

Exact original artifact IDs in order are 13217381754 (live Mesen run 41605614082), 13194096004 (original first-family source corpus), 13183968725 (original source-index census), 13194250673 (original 8×8 tile-lineage graph), and 13193992845 (strict tile-disjoint historical holdout). Their byte-identical ZIP hashes are pinned in both source code and the permanent numerical receipt; historical original JSON SHA and canonical ROM SHA are checked independently. No new emulator run is needed for this question.

## Decision

These are source-content grouping candidates for a **future prospective model comparison**. To avoid hidden train/test leakage, any proposed new source split must freeze *entire* tile-connected components and respect the old 16 fit / 19 withheld / strict-six index-plane identities, while separately checking actual animation-time and camera/viewpoint independence. Existing 2026 GLBs, their five authored pose names, provisional source camera and all already-inspected IoU scores remain retrospective. No native gameplay renderer, Windows acceptance, model default, Pages viewer, 1994 rig identity or owner art approval is changed.
