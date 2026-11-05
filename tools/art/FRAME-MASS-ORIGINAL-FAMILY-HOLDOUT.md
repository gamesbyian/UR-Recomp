# ART-4K: Source-authored fork/frame mass across independent original 2D silhouettes

**Goal:** determine whether a previously observed thicker 2026 fork/frame improves complete 64×64 original-ROM silhouettes *outside the original source family used to choose the mass candidate*. Do not create another rig or change the draft model's default geometry.

## Previously measured candidate and true test separation

The existing merged source-authored `ablate_racer_frame_mass.py` tested the original exact first-family ten source binary silhouettes at source OpenSCAD `rig_frame_mass=1.0` and exploratory alternatives up to 2.0. Mean whole-source IoU rose from **0.57255469** at 1.0 to **0.58271615** at 1.4 and **0.58539651** at 2.0, with improved source-raster boundary Chamfer in that *training* family. Earlier saddle expansion was less promising. The same model source still carries both bounded `rig_frame_mass` and `rig_saddle_span` parameters, but its actual final likeness remains rejected.

Since that study, original-USA-ROM source extraction has authenticated **35 SHA-distinct binary silhouettes** across 27 registered temporal windows. Some windows share identical binary source shapes and must remain in one connected family: merely using a different named window is **not** independence.

The new `evaluate_original_racer_frame_mass_holdout.py` freezes the fork-mass trials at **1.0, 1.4, 2.0** based on prior source findings, without changing them after seeing any new shape. It revalidates the authentic USA ROM-derived source corpus and all 64×64 PNG SHA/alpha pixels. It discovers connected components of source windows sharing an original binary mask. The fit family contains original 1205–1220; the separately disconnected source family provides **19 genuinely SHA-disjoint 2D silhouettes**. The withheld candidate is *not* independently proven to be a novel 1994 **3D** camera/viewpoint.

The test executes the **actual historical canonical 2026 OpenSCAD source** (source SHA-256 `e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984`) rather than a JSON mock or direct vertex shell stretch. It uses the original source's own `frame_member` hull/sphere modeling, via the existing `export_part` function. Tire, rim/hub, pedals and saddle are all rendered exactly once at unchanged source settings; **only** the fork/frame part is rerendered for each trial, then composed into one complete five-part silhouette.

Each source STL is rasterized under the same **frozen, provisional** P1-1205 side camera, source 7:6 pixel aspect, 4× source-aligned raster resolution and exact SHA-authenticated original visible-alpha lower-anchor offsets. No score-driven per-frame translation, zoom, camera fitting or pose pairing. Every original binary mask gets one vote: whole-alpha IoU, XOR, source pixel-aspect boundary Chamfer and remaining visible contact deltas are retained per original source SHA and separately summarized for fit, withheld and all 35 masks. The old first ten masks' control mean IoU **must** reproduce 0.57255469 or the job fails.

## Reproduce

    python3 tools/art/evaluate_original_racer_frame_mass_holdout.py \
      --source-scad /frozen/canonical/unicycle_shared_rig.scad \
      --corpus /actual/original-ROM/source-corpus.json \
      --camera analysis/data/racer-inverse-side-provisional-1205.json \
      --out /new/no-replace/source-frame-mass-19-heldout.json

Dependencies: OpenSCAD, NumPy, Trimesh, Pillow. This runs within the existing source-ROM research workflow, which verifies the actual USA ROM SHA, recomposes all 35 original source silhouettes, restores the exact historical five-pose GLB for other tests, and checks out the exact historical experimental draft source commit `3f63d744f6381acebd86f9df2b84de01abb2e33b` into a **separate** directory, with its source SCAD SHA verified again before each trial. No new scheduled job; existing job is allowed up to 30 minutes for real OpenSCAD CSG.

Synthetic unit tests explicitly fail on leaky original family masks, missing source trial, nonfinite/forged scores, changed source SHA and a broken candidate count. **Only the real OpenSCAD/ROM job can qualify geometry.**

## Decision

If thicker fork mass improves 19 previously unseen original binary silhouettes on both overlap and boundary metrics, preserve the result as a candidate for the **same** draft #2832 rig's optional source parameters and Pages visual comparison, under independent review, rather than making it a new shipping default. If it fails, retain the negative result and refit the wheel/saddle/source camera or rethink the underlying five-part blockout. Avoid optimizing arbitrary 2D fit at the expense of original high-detail character identity.

The source camera, 1994 physical 3D rig, original source sprite→2026 experimental pose correspondence, true ground-contact physics, original 3D viewpoint novelty, owner likeness and shipping art are **not** established by any 2D overlap improvement. No ART-02..ART-10, original/native parity, USA event or release acceptance credit.

## Observed actual OpenSCAD/source-ROM test (November 1, 2026)

[Original-USA-ROM + real OpenSCAD job #41360120641](https://github.com/gamesbyian/UR-Recomp/actions/runs/41360120641) completed successfully. Its numeric artifact #13105170134 passed ZIP CRC (archive SHA-256 `e477845b3957b1adb8b7277b85065d9b2c5d252800bdcf5caa28b5985a79680a`), and full `fork-mass-disconnected-family.json` SHA-256 is `7b1b0bef1106a2b11dc6d5b4997babc9e0b974889b9c2f2479944a277ef732f7`. All 7 original source reports were retained alongside this one. The unmodified historical first-family 10-mask control reproduced exactly **0.57255469** mean IoU.

| Source fork/frame thickness | Source training-connected 16-mask mean IoU | Previously unseen SHA-disjoint 19-mask mean IoU | Wins/losses vs original on 19 |
| --- | ---: | ---: | ---: |
| 1.0 unchanged | 0.55276425 | 0.38192089 | Control |
| **1.4** | **0.56347107** | **0.38824958** | **19 wins / 0 losses** |
| 2.0 | 0.56553270 | 0.37325690 | 0 wins / 19 losses |

The more aggressive 2.0 control overfits the first original source family: all 19 withheld 2D binary source masks score *lower* overlap than unchanged. The moderate 1.4 source thickness improves complete IoU on **all 35** original masks (mean 0.46002071 → **0.46835083**, without weighting repeat frames). However, the independent 19-mask mean source physical-pixel boundary Chamfer increases slightly from 3.07819813 to **3.08501689** at 1.4. At 2.0 the edge Chamfer improves to 3.05194882 despite worse overall IoU, showing that neither scalar alone certifies likeness. The source camera remains provisional and the 19 binary masks are **not** certified independent original 3D viewpoints.

**Engineering disposition:** preserve a **1.4× source-owned optional GLB visual comparison candidate** for the same #2832 rig and existing Pages viewer. Do not elevate it to the art default without complete source-sprite inspection/owner likeness approval. Do not blindly maximize the training IoU and choose 2.0. Verified numeric digest and all three family summaries are stored in `analysis/data/racer-art4k-source-frame-mass-original-19-mask-20261101.json`.
