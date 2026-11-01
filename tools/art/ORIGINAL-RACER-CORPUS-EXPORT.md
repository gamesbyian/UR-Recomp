# Reproducible registered original-racer source corpus

**An offline, private input supplier for inverse-graphics fitting.** This tool deliberately consumes the project's **existing** deterministic ROM compositor (not a second extractor) and the existing \`analysis/data/racer-hd-replacement-prototype.json\` registry. It can regenerate registered original sprite sources when historical Actions artifacts have expired. No ROM or newly extracted source sprite pixels are added to the repository. The exporter **rejects destinations anywhere inside the public checkout** (even ignored directories); choose an external private output path. It does **not** claim final native PPU/foreground visibility or original source 3D camera recovery.

## Private workflow

```sh
# Source ROM must be a local, legally obtained *exact* original USA ROM.
python3 tools/verify_rom.py reference/roms/retail/Uniracers_USA.sfc

# Default: all currently registered source windows, including the existing
# first-family 1205..1220 and the separately registered hold/recovery families.
# Choose a NEW output path; any existing output is an error.
python3 tools/art/export_registered_original_racer_corpus.py \
  --rom reference/roms/retail/Uniracers_USA.sfc \
  --out /private/ur-art4k-source-corpus-<run-id>

# Narrow a diagnostic extraction without changing the source registry.
python3 tools/art/export_registered_original_racer_corpus.py \
  --rom reference/roms/retail/Uniracers_USA.sfc \
  --window ordinary-race-1244-1252-hold-recovery \
  --out /private/ur-art4k-hold-corpus-<run-id>

python3 -m unittest tests.unit.test_export_registered_original_racer_corpus
```

**Source proof:** verify ROM size 2,097,152 bytes and USA SHA-256 \`859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478\` *before* reading/encoding original sprites. Reuse \`prototype_racer_hd_replacement.build_stock_rgba\`, which decodes exact frame composition guards, native source graphics and registered palette IDs from the original ROM. Independently cross-check the 1205–1220 first-family fresh composition against all **32** retained source-frame original RGBA hash declarations, when that window is among the selected inputs; missing or mismatching source metadata is a hard error. This is additional corroboration, not proof of original 1994 source mesh identity.

**Output:** one immutable private \`source-corpus.json\` plus \`stock/source-<decoded RGBA SHA>.png\` files, copied only after a successful validated complete run. The JSON carries canonical ROM and registry hashes, selected exact source window names, frame/player/representation identities, deduplicated pixel SHA-256, binary-alpha SHA, occupied bounds, palette/alpha variant groups and clear \`false\` approval/novel-camera flags. Exact repeated decoded RGBA values share one saved PNG; distinct palette variants can share a **binary silhouette** and are recorded under one silhouette group. A failed composer or corrupted source fails before publication. Existing output directories cannot be overwritten.

## Relationship with the separate 3D viewer agent

The owner has another agent implementing the **existing** [Racer Model Review](model-review/README.md) UI, part of the Windows Visual Atlas Pages site at \`/model-review/\` (landed in [PR #2938](https://github.com/gamesbyian/UR-Recomp/pull/2938)). Its responsibilities are **WebGL model inspection, five experimental named rig poses, verified original-sprite scrubber and optional Pages publication**. Its \`tools/art/model-review/stage_pages.py\` already reads the existing #2832 five-pose GLBs and checks SHA-bound success receipts; do not create another model/pose viewer, duplicate its publisher or replace its atlas root. It currently imports the **retained 1205–1220 P1/P2 original sprite rail** via \`windows_visual_atlas.py\`. That rail remains authoritative and unchanged.

This corpus exporter creates additional **private fit/evidence inputs**. It does **not** write to the viewer's \`sprites.json\`, manipulate \`model-review/manifest.json\`, publish new source art to Pages or imply a source-frame-to-3D-pose pairing. New family evidence may be offered to the viewer only when separately inspected for rights and provenance and when the viewer owner explicitly extends its existing reference rail contract. Any future rendered comparison attached to the viewer should reference **read-only** immutable \`racer_inverse_current.json\` and \`packet.json\` source hashes, model GLB/source-commit hashes, pixel-aspect and provisional-camera status, with **no** implied matching of the experimental \`upright/pedal/wheelie/stunt/bank\` GLBs to original guest frames. Do not add heavy fitting/ROM extraction to the Pages default build.

## Next integration tasks

1. Re-extract authenticated different-family source rasters using the exact original ROM and compare their source-alpha and semantic pose grouping. Keep the first-family training fitting window separate from a predeclared held-out **different** family. A semantic-ID novelty alone cannot certify an independent camera.
2. Consume the existing #2832 immutable GLB result through \`tools/art/run_racer_inverse_packet.py\`. Use fixed-camera PNG scoring and \`tools/art/aggregate_racer_pose_scores.py\` with one weight per source binary silhouette. Do not optimize against a diagnostic/held-out family.
3. Supply resulting **source-bound artifacts** to the *same* model-review Pages UI, when its owner is ready, with an explicit experimental/provisional label and no second rig or website.
4. Preserve the explicit original-character likeness veto until the owner reviews actual gameplay-scale 1P/2P animation. Source pixel, model export, rendered-alpha scoring and visual art acceptance are different gates.

**Dependencies:** source-corpus extraction requires the original ROM and existing stdlib compositor code. The unit tests use ROM-free synthetic registered frames and must not require the ROM. Heavy OpenSCAD, Trimesh, Blender, neural reconstruction and WebGL are optional separate lanes, not imported by this exporter.
