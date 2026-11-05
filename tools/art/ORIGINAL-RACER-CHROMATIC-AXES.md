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


## Compare against the *real* five experimental 2026 GLB frame poses

There is also one source-aware **unpaired** 3D comparator, with the same provisional side camera already used for the silhouette audit. The optional tool `audit_real_glb_coloured_frame_axes.py` validates the existing **single** model-review site (five complete GLB SHA plus original sprite rail), then reads the actual named blue `fork_and_frame__material_0` child of each pose, checks its unchanged original 2026 material RGB (28,89,222), bakes its parent world transform and rasterizes the triangles with the **existing 4× fixed-camera renderer**. The PCA is measured in *exactly the same* 64×64 source-pixel axes as the authentic original chromatic region, but **original rendered colour pixels are not a verified semantic 3D fork segment**.

| Real 2026 experimental GLB pose | Screen-space colour-frame axis |
| --- | ---: |
| Upright | **+5.952°** |
| Pedal | **+5.952°** |
| Wheelie | **+30.637°** |
| Stunt | **−39.497°** |
| Bank | **+7.124°** |
| Original 1994 withheld P1, unpaired reference | **+39.809°** |

The original P1 heldout screen axis is about **9.17° away from the 2026 wheelie blue frame projected axis** *under this provisional camera*. This is a falsifiable source-to-render diagnostic; it is **not** evidence that the original scene was the wheelie state, that the physical original wheelie root pitch was 40° or that increasing a 2026 GLB node rotation by 9.17° would recover authentic movement. The model's remaining tire/saddle silhouettes, camera/depth foreshortening, original figure bending, material masks and source cadence must be compared simultaneously. Do not fit against the withheld family and then count it as a holdout.

Run against an already-built, SHA-verified existing Pages model-review directory containing five real GLBs and original PNGs:

    python3 tools/art/audit_real_glb_coloured_frame_axes.py --model-review-dir /path/to/existing/model-review
    python3 tools/art/audit_real_glb_coloured_frame_axes.py --model-review-dir /path/to/existing/model-review --out /new/immutable/experimental-five-glb-axes.json
    python3 -m unittest tests.unit.test_audit_real_glb_coloured_frame_axes

Requires optional offline NumPy, Trimesh and Pillow already used by the existing deterministic GLB renderer; never requires OpenSCAD/Blender/ROM rerender or model editing. Source-authenticated original chromatic axis output is a **separate evidence class** from the 2026 material-part axis. See [actual five-GLB material-source SHA/axis pilot](../../analysis/data/racer-art4k-real-five-glb-frame-axis-20261101.json). Preserve the existing canonical #2832 rig and one Pages reviewer while iterating.


## Original frame-time chromatic acting, not just isolated silhouettes

The source-audit output also includes every original registered **guest-frame observation** in chronological order for all source windows and all players, with exact representation/binary/chroma SHAs. Adjacent frames holding the same original source chromatic image are preserved as one contiguous *observed* hold segment. An apparent source hold is **not** permission to invent continuous 3D root rotation/pedal phase interpolation through unseen frames.

One actual first-family example, using the original authenticated USA ROM source sequence:

| Original guest-frame period | P1 red body projected axis | P2 blue body projected axis |
| --- | ---: | ---: |
| 1205–1206 | +11.62° | −16.57° |
| 1207–1212 | +16.56° (six-frame hold) | −16.57° |
| 1213–1214 | +11.62° | −16.57° |
| 1215–1216 | +6.09° | −11.00° |
| 1217 | +0.97° | −11.00° |
| 1218 | +0.97° | −5.54° |
| 1219–1220 | −4.68° | −0.41° |

This provides a bounded visible 2D **posture-and-hold sequence** from the original, rather than pretending the five unrelated 2026 authored blockout poses define original pedal cadence. The 1994 3D wheel, saddle stretch, camera and code-driven original pose state still require separate authenticated evidence before controlling the native Remastered model.
