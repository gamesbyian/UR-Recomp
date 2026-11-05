# Original ROM orientation-normalized 2D contour consensus

**Purpose:** construct a source-exact, uncertainty-aware 64×64 *image-space* contour target from all 64 original pre-rendered orientations at four existing original animation phases (0,6,12,18). This is a cheap reference for future 2026 rig geometry comparisons. It is **not** a recovered historical 1994 3D model, camera, bone map, material ID, physical angular rate or likeness approval.

## Why this follows #3114

The preceding [#3114](https://github.com/gamesbyian/UR-Recomp/pull/3114) measured only **66.48%** pooled whole-original sprite silhouette overlap and **23.84%** exact original opaque 4bpp-index recall when a single source orientation-zero sprite was rigidly rotated across 32 already-inspected odd original orientations at four phases. A later fixed global one-to-one 4bpp palette-index permutation scarcely improved exact recall (**24.03%**). That residual could contain source-specific 2D sprite redraw, view-dependent shading and occlusion, or real 3D geometry/view signal. The same source 2D rotation explains the original **phase-changing region's support** considerably better (~87.36%), so the location and identity of the disagreeing *full-sprite* pixels matter more than another global rotation score.

The new source-only [`tools/art/recover_original_rom_derotated_consensus.py`](recover_original_rom_derotated_consensus.py) recovers the exact full USA original ROM **24×64** source 4bpp index table with the existing decoder and SHA-locked [#3104](https://github.com/gamesbyian/UR-Recomp/pull/3104) source 64-orientation phase-variation bbox report. On the **32 even original orientation indices**, the existing centre fit is **(31.515625,19.578125)** in raw original 64px sprite coordinates. It differs slightly from the full-state mean y **19.5859375**. The exact source-pinned even-only centre is fixed once for all 256 source sprite observations, no per-image image/geometry registration.

At each of the selected original source phases, take all 64 real pre-rendered indexed sprites, undo the previously tested **2D source-index-space rotation** `-2π×original_index/64` around that fixed centre, and count in each target 64px coordinate how many original orientations had an opaque index. A separately inverse-rotated **all-valid** source canvas records whether the inverse sampler fell *inside* the source 64×64 raster. Cropped corners are **not** counted as observed transparent backgrounds, which is necessary to avoid an artificial consensus around edge silhouettes.

For the 64 de-rotated original sprites at each phase, define one original 2D model-space pixel as:

* **Core:** valid in at least 32 original orientation samples and opaque in ≥90% of its valid source samples.
* **Consensus silhouette:** valid in at least 32 and opaque in strictly more than 50%.
* **View-dependent fringe:** valid in at least 32 and opaque in strictly more than 10% but less than 90% of those source views.
* **Unidentified/undersampled:** fewer than 32 originally valid orientation samples, so it is not silently called background or part of the canonical silhouette.

Store the exact per-pixel source valid-sample and opaque-sample counts, a 64×64 **2D source plural-index** image chosen by a deterministic plurality among original opaque 4bpp labels only where the consensus alpha is set, and SHA digests for the binary consensus/core and indexed plurality. The original 4bpp palette indices are source image colour codes, **not** recovered 3D surface materials or illumination. Also partition source core/fringe/consensus counts in the same previously frozen image y0–14, y15–26, y27–63 bands that the real 2026 GLB parent-census PR uses.

**Discriminator:** highly stable de-rotated core pixels at multiple original phases are credible *2D common-source contours*, suitable for constraining a **single shared 2026 source-model projection**. They do not prove those pixels physically belong to the source artist's 3D fork/saddle/wheel, nor that their cross-orientation differences are solely physical 3D parallax. View-dependent fringe pixels or shifting original indexed colours must remain explicit targets; a fit to the core alone cannot claim to have solved original 3D anatomy or occlusion.

## Reproduction

```sh
python3 -m unittest tests.unit.test_recover_original_rom_derotated_consensus
python3 -m tools.art.recover_original_rom_derotated_consensus \
  --rom reference/roms/retail/Uniracers_USA.sfc \
  --axis-report analysis/data/racer-original-ROM-24phase-64angle-source-axis-20261103.json \
  --out /new/original-ROM-derotated-2D-contour-consensus.json
```

No new original Mesen capture, OpenSCAD geometry, renderer or GitHub workflow. The standard source SHA checks and exclusive no-overwrite report publisher fail closed. Tests verify synthetic 4bpp opacity/fringe/missing-view contracts and the **actual complete original USA ROM source family**; all numeric results must be drawn from exact-head CI execution.

## Executed original ROM contour result

The exact original 2,097,152-byte USA ROM and SHA-pinned 24×64 phase/orientation source report were exercised in the full dependency-free tooling suite at implementation head `5a862badb692f246199a6ecd1aa8a321f1aa5b08`, [GHA run #41890911468](https://github.com/gamesbyian/UR-Recomp/actions/runs/41890911468), with [hygiene #41890911798](https://github.com/gamesbyian/UR-Recomp/actions/runs/41890911798) also green. These are source-only exact evidence pixels, *not* the 2026 GLB's model parts. The observed original 2D inverse-rotation consensus per predeclared phase is:

| Original ROM phase | 2D consensus opaque pixels | Near-invariant 2D core pixels | Orientation-dependent 2D fringe pixels |
|---|---:|---:|---:|
| 0 | **297** | **173** | 329 |
| 6 | **300** | **165** | 337 |
| 12 | **295** | **176** | 326 |
| 18 | **297** | **171** | 331 |

Core is a subset of consensus; fringe overlaps other classifications, so **do not add those three counts** as disjoint components. The 2D source view-dependence and opacity uncertainty remain large even after a single fixed original orientation-index-space rotation, and the source evidence supports retaining multiple independently authored 2D views. Original view-dependent pixels could reflect 3D occlusion, shading or hand-authored sprite changes. **Do not infer a recovered 1994 surface or a physical camera.**

The subsequent test commit freezes these **12 exact source counts**, not just the existence of a report; it requires its own final-head unit/hygiene checks after the implementation run above.

## Scientific stop and handoff

This experiment is source-only, stacked on #3104/#3113/#3114; compare any later changed 2026 mesh against the **same** 2D source-normalized core and a truly held-out source perspective/orientation family, retaining prior 2D rigid rotation, source-phase orbit and full 4bpp references as controls. Do not select a mesh parameter or camera per original image after inspecting residuals. Current 2026 #2832 model authoring and owner art veto remain fully intact.
