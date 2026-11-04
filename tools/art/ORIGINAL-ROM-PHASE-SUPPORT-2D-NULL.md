# ART-4K: test whether original phase-sensitive pixels move as a rigid 2D shape

**Source boundary:** the authentic original USA ROM's complete 24-phase × 64-orientation primary 4bpp sprite table, as recovered in #3104. This is a source-only retrospective 2D experiment. The frame states may be compatible with a 3D authoring rig, but no surviving 1994 mesh, camera, bone, source physical joint degrees or owner-approved likeness is inferred.

The preceding [#3113](https://github.com/gamesbyian/UR-Recomp/pull/3113) found that the **bounding-box centre** of the phase-sensitive pixel region traces a near-first-harmonic path across 64 orientation values. A bounding box is insufficient to establish a rotating shape. A fixed-sized graphic translated along that circle and a genuinely rotating graphic share nearly the same centres. **This experiment discriminates those 2D hypotheses using every individual source pixel in the changing region.**

## Reuse and exact definitions

- Input: the **original** 2,097,152-byte USA ROM, SHA-256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`; #3104's original 24×64 source axis receipt SHA-256 `23aa563c094471a3d7f1b5dcb12489cc1b5ca45b1240aee06fde3934a932bbd0`.
- Reuse `source_frame_tiles` and `render_original_primary_sprite64` from the existing authenticated original-ROM decoder. At each fixed original orientation `a`, the binary **source support** at pixel `(x,y)` is set if *any* of the other 23 original phase images has a different 4bpp palette index from original phase zero. Alpha changes and opaque-to-opaque changes both count. No source RGB threshold or 2026 GLB materials enter this support map.
- Independently recompute 64 support bounding boxes and **require exact agreement** with #3104's source axis receipt. A mismatch rejects the analysis. No generated counterfactual can silently replace original ROM-authored pixels.
- Freeze the support template at original orientation **0**. Determine the first-harmonic centre path using **even** orientation indices 0,2,..62 only. Test only the **32 odd** orientation indices 1,3,..63 for the reported summary. All 64 states are already known/inspected, so this is an internal diagnostic split, **not a prospective blind holdout**.

Three fixed 2D nulls predict each odd-angle support: (1) the unmodified orientation-zero support; (2) a pixel-preserving translation by the *predicted harmonic displacement* without per-angle registration; and (3) one rigid 2D rotation about the single harmonic mean pivot, by an **uncalibrated** index-space angle `2πa/64`. All sample the same 64×64 original source grid without wrapping, using nearest source-pixel centres. No per-angle free translation, mask deformation, camera or feature selection is allowed.

Report per-angle and pooled intersection, predicted-only, source-only, IoU, precision and recall, with one vote per odd index in the mean IoU. Source support masks are source-derived geometric *regions* only, not physical part labels. The original SNES **7:6** pixel aspect remains explicit: the match operates in original 64×64 integer source coordinates, not incorrectly pre-stretched display pixels.

## Decision rule and next actual 3D discriminator

If rigid 2D rotation fails to outperform a translated/static phase-support template on the changed-pixel support, reject the claim that the observed bounding-box orbit by itself supports rigid rotated source anatomy. If rotation works better, it still supplies a credible **2D rotation null** that any more elaborate 3D rig must beat on independent full alpha, opaque 4bpp painted-index and temporal evidence. Neither result can uniquely identify a 3D object. Do not make the existing #2832 GLB a default or edit geometry from an unpaired retrospective gain.

The next legitimate experiment uses the unchanged 16-material 2026 GLB, one locked provisional 7:6 camera, and the existing #3101 isolated continuous wheel/rim/pedals and fork/saddle controls. Score actual changing source pixels under one shared 3D parameterization and **against whichever stronger 2D null this source-only test identifies**. Predeclare physical angle and temporal correspondence *as hypotheses*; original ROM 24/64 indices are not independently measured physical degrees. A 2D-only generator may remain the most parsimonious explanation.

## Reproduce

```sh
python3 -m unittest tests.unit.test_analyze_original_rom_phase_support_2d_null
python3 -m tools.art.analyze_original_rom_phase_support_2d_null \
  --rom reference/roms/retail/Uniracers_USA.sfc \
  --original-axis-report analysis/data/racer-original-ROM-24phase-64angle-source-axis-20261103.json \
  --out /new/source-phase-support-2d-null.json
```

The script verifies all source identities, uses the existing atomic exclusive no-overwrite report publisher, and prints aggregate numerical scores. No new original Mesen run, model export or recurring research workflow is required. Record actual executed scores only after exact-head CI passes. This branch depends on #3104 and #3113 and requires its own independent code/source interpretation review.
