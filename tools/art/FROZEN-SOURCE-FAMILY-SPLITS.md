# Freeze source-racer fitting and withheld-family partitions

**Status: offline evidence planning; no independent 3D viewpoint or art acceptance.** This implements A1's protected source-family split using actual decoded original **binary** pixels, not merely semantic sprite IDs or 2026 blockout pose names.

The input is a private immutable output from `tools/art/export_registered_original_racer_corpus.py`, not the public viewer's curated sprite rail. Every PNG is re-decoded and checked against its registered RGBA SHA, alpha SHA, binary mask SHA, image-file SHA, occupancy/bbox and original player/frame identity.

## Reproduce and freeze

```sh
# On a private computer with exact canonical-USA ROM-produced corpus:
python3 tools/art/freeze_racer_source_family_splits.py \
  /private/ur-art-corpus/snapshot-001/source-corpus.json \
  --template > /private/ur-art-corpus/snapshot-001/roles-draft.json

# Edit `roles-draft.json` to assign every window one of:
# fit                 geometry/camera parameter optimization
# diagnostic          inspection only, without independent-view claims
# withheld_candidate  reserved source family, excluded from fitting
python3 tools/art/freeze_racer_source_family_splits.py \
  /private/ur-art-corpus/snapshot-001/source-corpus.json \
  /private/ur-art-corpus/snapshot-001/roles-frozen.json \
  > /private/ur-art-corpus/snapshot-001/split-evidence.json
python3 -m unittest tests.unit.test_freeze_racer_source_family_splits
```

The conservative draft assigns **all** windows `diagnostic`. A human/agent must deliberately choose `fit` and `withheld_candidate` groups before using them for optimization. Every original binary silhouette creates a connection between all windows in which it occurs, including repeated frames, semantic aliases and palette variants. All members of one connected component must share one role. Any cross-role leakage is a hard failure naming the offending windows.

The resulting JSON carries SHA-256 of the exact original corpus and role request, independently checked PNG count, connected groups, explicit role/window/shape counts, and all component silhouette hashes. It never labels a source-family-only diagnostic as an independent 3D viewpoint. A result with no distinct withheld component must not be called a held-out accuracy result.

## Scope and ownership

Source pixels remain in a private external directory. The command prints JSON and never publishes original artwork, ROM, model binaries or speculative scores to GitHub Pages. Tests use ROM-free synthetic sources, including deliberately aliased shapes and forged hashes. The deterministic exporter reports canonical ROM composition, but its receipt is not an external signature; only the first-family original source has additional separately retained PNG witnesses. Other original families require an independently hash-verified local ROM for authentic input.

The existing [model-review viewer](model-review/README.md), merged in [#2938](https://github.com/gamesbyian/UR-Recomp/pull/2938), alone owns the WebGL site, original 1205–1220 sprite rail, five experimental GLB poses and Pages publication. The fitting lane owns the frozen splits and [multi-pose scorer](MULTIPOSE-SOURCE-EVALUATION.md); never create a second web reviewer or silently pair a source frame to an experimental GLB pose. The [real published-GLB baseline](REAL-VIEWER-GLB-BASELINE.md) is a reproducible but provisional source-camera observation.

**Stop condition:** if shared original masks link all windows into one connected component, there is no leakage-free within-corpus holdout. Acquire additional authentic source evidence rather than fabricate a partition. A distinct 2D mask is not proof of a distinct 3D camera.
