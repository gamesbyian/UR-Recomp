# ART-4K: source-authenticated ninth-phase 2026 ride motion vocabulary

The original-ROM research pipeline authenticated 35 distinct original 64×64 **ROM-composed** source alpha masks, 27 **authored-registry** source windows, 144 registered P1/P2 observations and 109 *integer-consecutive in that registry* player-frame pairs. Only 19 registered pairs change source silhouette; 90 are identical **within the authored source sequence**, not independently measured live gameplay hold ticks. The source corpus explicitly declares `source_kind = deterministic_canonical_USA_ROM_registered_composition`, `native_live_original_PPU_or_1994_3d_camera_independently_verified = false`, and the source registry’s sequence entries identify **authored** review windows. Thus its integer `guest_frame` labels cannot be treated as an independently observed original 1994 emulator/PPU animation cadence. The nine-phase report now requires the independently revalidated corpus manifest SHA *and* these source-origin fields, and explicitly emits `source_temporal_evidence_class` flags describing this distinction. A genuine live 1994 PPU/OAM frame trace must be collected and correlated with source registry identities before drawing timing conclusions. The source's 1994 3D camera, rig and animation time correspondence have **not** been recovered. The experimental 2026 procedural model remains unapproved art.

## Why the existing quarter-phase source study needed another control

Merged [#3020](https://github.com/gamesbyian/UR-Recomp/pull/3020) compared five real SHA-verified ride GLBs from the single draft #2832 part-addressable OpenSCAD rig at normalized authored times 0,.25,.5,.75,1. Actual 2026 source continuous formula contains `3*sin(720*u)` degrees of wobble. Every quarter-phase sample has exactly **zero wobble**, and world-space vertex sets of `ride@0`, `ride@.5`, `ride@1` are equal. That five-time experiment therefore sampled just **three distinct spatial poses**. Its four counterfactual transitions overlapped 41–80 of the 1,631 original changed source pixel positions (2.51–4.90% pose-only recall), while predicting spurious source movement on all 90 authentic sprite holds. Those are *unpaired descriptive comparisons*, not fitted original timing.

Child [#3023](https://github.com/gamesbyian/UR-Recomp/pull/3023) adds **four new t=.125,.375,.625,.875 samples** to the exact same real OpenSCAD source/export path; the authored ±3° wobble extrema are included. The actual exporter and separate GLB receipt verifier passed all **ten** job variants on CI [#41385793054](https://github.com/gamesbyian/UR-Recomp/actions/runs/41385793054): nine ride times plus the earlier stunt control. Independently downloaded GLB bytes were validated against immutable qualified SHA receipts. There are **seven distinct world-space vertex sets** among nine time samples; 0,.5,1 coincide geometrically. Actual OpenSCAD triangulation changes from 28,860 faces/14,460 concatenated vertices at the quarter phases to 28,820 faces/14,440 vertices at eighth phases. **Do not vertex-morph** differently triangulated GLBs; preserve the one rig's part pivots/transforms.

## New bounded real-ROM experiment

The `study_original_racer_eighth_ride_motion.py` wrapper invokes the **existing** `study_original_racer_continuous_ride_motion.evaluate` with exactly 9 declared times and 9 **different, exact pinned source-authored GLB SHA256 digests**. The historical five-time Python API and its GHA step remain unchanged by default. Each original 64×64 source PNG is revalidated against SHA source corpus; real GLB bytes, current immutable attempt pointer, successful independent 5-parent/16-material receipt, fixed provisional 7:6 camera are checked before projecting any pixels. The existing PNG scoring and projection routines are reused; there is no new renderer, new model or Pages viewer.

Every one of the **8 fixed authored 2026 phase intervals** (0→.125→.25→.375→.5→.625→.75→.875→1) is compared counterfactually with every one of the **109 actual** original ROM consecutive source edges, without choosing *any* source frame-to-time pairing. At each original frame edge, report source silhouette XOR pixel movement, 2026 model **pose-only** XOR at the same preceding original visible-alpha anchor, separately placed-model XOR using the next original sprite's visible-alpha anchor, raw overlap/recall/precision and false-positive 3D model movement on **all 90** original source holds. An original source held frame is a negative temporal control, even if 2026 animated geometry varies. Cycle closure 0 vs1 is a separate genuine 4× raster control. Every numeric score is descriptive, not a calibrated source-registered animation.

The original source image and model identities have already been inspected in related studies; no new *untouched original family holdout* is claimed. Predeclare whole semantic/source-mask-disjoint fit and withheld groups **before** choosing timing, pose/angle grids or camera. More original positive animation source captures are needed: only 9 of 35 current original contiguous tracks contain any silhouette change.

## Run and acceptance

Use the already established original-USA-ROM research workflow. It reuses the archived actual authored GLB exports from GHA run #41385793054, with `actions/download-artifact`, passing nine sample directories to:

```sh
python tools/art/study_original_racer_eighth_ride_motion.py \
  --corpus /private/source-corpus.json \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  --ride-sample 0.0 /private/art4k-real-continuous-ride-0.0 \
  --ride-sample 0.125 /private/art4k-real-continuous-ride-0.125 \
  --ride-sample 0.25 /private/art4k-real-continuous-ride-0.25 \
  --ride-sample 0.375 /private/art4k-real-continuous-ride-0.375 \
  --ride-sample 0.5 /private/art4k-real-continuous-ride-0.5 \
  --ride-sample 0.625 /private/art4k-real-continuous-ride-0.625 \
  --ride-sample 0.75 /private/art4k-real-continuous-ride-0.75 \
  --ride-sample 0.875 /private/art4k-real-continuous-ride-0.875 \
  --ride-sample 1.0 /private/art4k-real-continuous-ride-1.0 \
  --out /private/new/original-eighth-ride-motion.json
```

ROM-free negatives: `python -m unittest tests.unit.test_study_original_racer_eighth_ride_motion tests.unit.test_study_original_racer_continuous_ride_motion`. The real source experiment must run on GHA and publish a bounded numeric artifact. Full four-shard tooling and independent source review required before integration. No original 1994 camera/rig/cadence discovery, owner likeness signoff, shipping ART, Windows or gameplay release gate may be inferred.
