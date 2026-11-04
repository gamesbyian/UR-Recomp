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

## Executed real-original-ROM result (2026-11-04)

The full tooling suite passed at exact implementation head `f6d7558e041b76cf9c8c79beb166208c17a653cc`, [Actions run #41785648962](https://github.com/gamesbyian/UR-Recomp/actions/runs/41785648962), unit job `126427064938`. The ordinary sharded test runner surfaced its machine-measured `OK ART4K_PHASE_SUPPORT_2D_NULL_TEST_SUMMARY` from the real authenticated ROM, **32 odd orientation indices**, with even-only centre harmonics and one unfitted phase-support reference at angle zero:

| Fixed original pixel-region explanation | Correct pixels | False positives | False negatives | Mean IoU across angles | Pooled IoU |
| --- | ---: | ---: | ---: | ---: | ---: |
| Unmodified reference support | 613 | 3,099 | 3,124 | 0.12345763 | **0.08967232** |
| Harmonic 2D orbit, translation only | 3,410 | 302 | 327 | 0.84807947 | **0.84426838** |
| Same reference support, rigid 2D rotation | **3,477** | **243** | **260** | **0.87411704** | **0.87361809** |

The 2D rigid rotation improves pooled IoU by **0.02934971** over the fixed-form orbit translation and by **0.78394577** over a stationary source support. The two moving controls use the same 64×64 true-source comparison and a shared harmonic centre fitted only on even orientation positions. The rigid rotation is a low-parameter *2D source-image explanation*. It correctly covers **3,477 of 3,737 phase-sensitive source pixel positions summed over the 32 odd test orientations**, but that count is intentionally *instances*, not independently observed 1994 world geometry.

**Inference:** the source supports rigidly rotating a local phase-dependent *image region* more strongly than simply translating an unrotated fixed region along the same near-circular path. This does **not** yet prove that full original sprites rotate rigidly, because the comparison scores phase-sensitive **union masks**, not detailed 4bpp colour samples, depth/occlusion or the static parts of the racer. The source objects were already inspected; no prospective test was performed, and the source ROM images are original pre-rendered graphics. A real 3D replacement rig must show additional predictive value over this successful 2D null.

The follow-up exact-count regression on this PR freezes all three (TP, FP, FN, IoU) outputs. Its stronger test commit requires separate final-head CI; do not attribute the previous successful run to the later head.

## Full original sprite versus the same two-dimensional rotation (2026-11-04)

The prior 87.36% result evaluates only the **union of original phase-sensitive pixels**. This follow-up examines all original 64×64 4bpp indices, including stationary body/fork/saddle pixels and their individual palette indices. The source-only `tools/art/audit_original_rom_fullsprite_rotation_null.py` reuses the exact ROM source decoder and original 24×64 report. It freezes the one 2D centre from even orientation states, selects **four original phase slices (0,6,12,18)**, and evaluates **32 odd source orientations each (128 original authored full-frame sprites)** against two source-only predictions: unchanged orientation-zero source sprite and one rigid 2D rotation of that reference by `2π×index/64`. The latter index→2D angle is an explicit orientation hypothesis, **not** measured source physical 3D degrees.

The completed full project tooling suite on implementation head `093d31998bee55e4cc2ddd60debc64dfb47583b8`, [run #41787502835](https://github.com/gamesbyian/UR-Recomp/actions/runs/41787502835), job `126433276743`, surfaced the executed ROM-derived `OK ART4K_ORIGINAL_FULLSPRITE_ROTATION_NULL` receipt:

| Retrospective 128-sprite full 4bpp measure | Unchanged sprite | One fixed 2D rigid rotation |
|---|---:|---:|
| Original alpha intersection | 14,788 | **32,793** |
| Predicted-only alpha pixels | 26,300 | **8,183** |
| Missing source-alpha pixels | 26,353 | **8,348** |
| Pooled whole-sprite alpha IoU | 0.21927314 | **0.66484876** |
| Original source-colour index matches in overlap | 2,660 | **9,806** |
| Original source-colour mismatches inside overlap | 12,128 | **22,987** |
| Exact 4bpp colour-index recall of source opaque pixels | 0.06465570 | **0.23835104** |
| Mean per-sprite alpha IoU | 0.23902855 | **0.66833709** |

This is an important discriminator: while the original **moving region's spatial support** is largely explained by 2D rotation (0.87361809 IoU from the previous experiment), rotating an entire original sprite yields only **0.66484876** alpha IoU and **0.23835104** exact 4bpp opaque-source recall. The full source table contains substantial **residual shape and painted-index structure** not captured by this restricted transform. The residual is *not automatically 3D depth*: source sprite-specific 2D painting, transforms, camera/registration, material/shading, occlusion and source palette reuse all remain possible. Observed original ROM records are pre-rendered sprites, so these 128 data points are **retrospective, not independent camera viewpoints or prospective blind frames**.

The stronger unit regression now asserts the full exact pixel counts, including the shared original-ROM source hashes and explicit no-3D claims. That new regression commit needs its own exact-head check; historical run #41787502835 tested the preceding code version, not the later frozen-score assertion.

**What to test next:** evaluate the same **128** real original sprite index planes against the **single source-authored 2026 GLB** with globally fixed camera and mechanical parameters. Reuse the exact two historical fixed pivot hypotheses on [#3115](https://github.com/gamesbyian/UR-Recomp/pull/3115), wheel/frame coupling from #3101 and consistent red player convention. Score silhouette/colour/occlusion and report any source-index↔candidate-material ambiguity explicitly. First require improvement beyond **0.66484876 alpha IoU** and additional explanatory power beyond the **0.23835104 exact-index** 2D null *using a defensible stable palette/material rule*, not post-hoc material fitting per image. Preserve original source and 2026 GLB evidence classes. Stop if candidate 3D rig underperforms this cheap 2D-only explanation.

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
