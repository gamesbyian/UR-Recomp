# ART-4K original source chromatic body-axis study

The canonical USA ROM now has a successfully executed, SHA-verified, 27-window original raster corpus from hosted [run #41280281930](https://github.com/gamesbyian/UR-Recomp/actions/runs/41280281930) / [original-source artifact #13072358512](https://github.com/gamesbyian/UR-Recomp/actions/runs/41280281930/artifacts/13072358512). This study consumes those **real source bytes** using the same source RGB chroma indicator already admitted by original colourway census #2965. It is a *2D projected body-direction observation*, not an original 1994 rig/bone rotation or camera inference.

## Why it matters

The source-first-family 1205–1220 masks were a poor basis for choosing the actual expressive 1994 unicycle posture. New original source poses have distinct visible diagonals, while a five-pose **2026 blockout** has no authenticated sprite→rig pose map. Frozen shape-disjoint comparisons #2971/#2972 measure fixed-camera IoU, but treating that as direct original 3D geometry would over-credit wheel width and under-credit missing posture.

A small robust measurement is possible without inventing segmentation: use exactly the authenticated source **red (P1)** / **blue (P2)** pixels, then take the first principal component of their original 64×64 (x, screen-down y) coordinates. Thresholds are source-descriptive RGB rules, not a recovered 3D fork part or real-world PBR material. The axis is computed relative to **screen-down vertical**; the sign and value depend on camera/projection and visible source colour pixels.

### Real SHA-bound finding

The source corpus has 59 original representation records, 41 independently checked original PNG images and 35 unique binary alpha silhouettes. The existing shape-only freezer assigns 16 unique original full binary masks to **fit** and 19 other masks to **withheld_candidate**.

| Real source player / assigned role | Independent full binary masks | Mean visible colour-region axis | Range |
| --- | ---: | ---: | ---: |
| P1 fit | 12 | +0.948° | −22.398° .. +22.228° |
| P1 withheld | 16 | **+39.809°** | **+38.474° .. +41.006°** |
| P2 fit | 10 | −1.316° | −21.873° .. +43.218° |
| P2 withheld | 3 | +16.990° | −31.156° .. +43.218° |

The nearly invariant **~40° original P1 withheld projected axis** is a strong source-derived **pose or camera/acting** difference, not evidence that the experimental upright mesh's wheel necessarily needs stretching. In particular, this verifies that the original heldout family contains a coherent diagonal presentation absent from the first family. None of these screen-angle values is a validated original-model root pivot/rotation.

### A stricter holdout contamination warning

The existing full binary-mask freezer remains valid *for its stated criterion*: no identical 64×64 binary alpha mask appears in both fit and withheld. But the original P2 source has an **identical chromatic 64px mask crossing that boundary** (SHA-256 `10ec956ef676bdfb5adc91af7df2a9896b75f499746d81e885def3ed9234a479`) while its full alpha masks differ. This means one visually identical colored body-region silhouette is represented across train/test despite different neutral wheel/rim pixels.

Therefore neither 19 disjoint **full image** masks nor their four distinct outer row envelopes justify counting **19 independent acting poses**, 19 novel cameras or 19 character-likeness confirmations. For future articulated-pose fitting, also group by original chromatic-mask identity or compare source color-axis families before assigning train/holdout. A source family held out for *wheel mask* evaluation can still leak *body acting*, and the evaluation must name its precise independence class.

## Reproduce and review

Download the actual complete 7-day hosted source artifact above (ZIP SHA-256 `219c611bf644eefd4803de5bf5001e78abec315d13388dbf9d7d4e13b69c6a0a`). Run from repository root:

    python3 tools/art/audit_original_racer_chromatic_axes.py /path/to/source-families.zip
    python3 tools/art/audit_original_racer_chromatic_axes.py /path/to/source-families.zip --out /new/path/original-source-chromatic-axis.json
    python3 -m unittest tests.unit.test_audit_original_racer_chromatic_axes

The auditor validates original declared ROM hash, source corpus manifest SHA and frozen roles, all 59 original represented PNG-byte/decoded RGBA/binary source identities and each original source alpha mask; it outputs only SHA-bound metadata and cross-role chromatic mask overlaps, not original sprite pixels. The optional immutable report uses the existing no-replace publisher and does not alter the source corpus. Source data and model/viewer assets remain separate.

Machine-readable prior real result: [original hosted colour-axis evidence](../../analysis/data/racer-art4k-hosted-chromatic-axes-20261101.json). This report is reproducible but does **not** independently identify the original physical 3D camera, actual source rig pivot, continuous source animation, or acceptable HD character art. It leaves #2832 as the **one unapproved canonical 3D rig** and #2938/#2957 as the **one source-review Pages viewer**.
