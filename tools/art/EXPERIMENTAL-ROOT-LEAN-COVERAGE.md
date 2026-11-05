# ART-4K original-source painted-axis lean-grid research

**Experimental source-bound 2D directional-coverage study. No original 1994 3D camera, original source pose identity, joint, wheel-contact physics, default geometry or art acceptance is inferred.**

The verified original USA-ROM corpus supplies 35 SHA-independent original binary sprite silhouettes, with known red/blue painted-axis image slopes (7:6 pixel aspect). The actual 2026 five-pose material-separated GLBs were source-hash verified in earlier research. Their fixed-camera painted axes (upright/pedal +6.944°, wheelie +33.869°, stunt -43.167°, bank +9.273°) leave 8 of the original 35 binary masks over 10° from any available experimental static pose, mean nearest angle difference 8.599°.

The newly exported **real continuous source** GLBs (ride t=.25 and stunt_cycle t=.5, PR #2996) add projected axes about +7.386° and +6.383°, respectively, barely improving source direction coverage (mean gap 8.599° to 8.439°; still eight >10°). Repeating the existing ride/spin source formulas is therefore a weak way to fill the remaining source directions.

This source-only test samples **one unchanged, source-SHA-verified upright GLB** under a fixed set of **20 in-memory root world-Y rotations**, −45° to +50° at 5° increments, around provisional world (0,0,0), without changing a GLB vertex, OpenSCAD source, one shared rig, viewer or rendered game. The actual painted fork/frame mesh is world-transform baked from the real GLB, rotated in memory, projected at 4× under the same SHA-pinned provisional side camera and 7:6 pixel aspect, and evaluated by the exact same original red/blue three-row image-axis descriptor. Original source measurements are **completely rederived from verified ROM PNGs before comparison**, not trusted from an attacker-editable reported SHA count.

On an initial local CPU reproduction, two candidate directions emerged: a source-world **−35° Y-root** sample projects to roughly **+40.50°** image slope, while **+15° Y-root** projects to about **−8.84°**. Adding these two descriptors to the original five reduces the *training source set* mean nearest-axis gap from about **8.599° to 3.634°**, with the count of original masks over 10° from any study direction declining from 8 to 3. Under a mean-gap objective alone, the nearby (−35°, +10°) pair yields about 3.570°, but leaves five >10° gaps. The complete fixed 20-sample grid and alternative objective rankings are recorded, rather than hiding unfavourable directions.

**Critical limits:** this is descriptive angular coverage, not full sprite silhouette IoU, realistic tire contact, bank physics, a 1994 camera reconstruction, 3D mesh fit or original animation matching. All 35 source masks were inspected during candidate selection and many are visually correlated; this is explicitly post-hoc optimisation, not independently withheld performance. The apparent positive/negative tilt signs differ because source-world Y rotation and image-space source-axis angle use different conventions. No root-lean pose is promoted as a canonical rig or art default.

## Reproduce

    python3 tools/art/study_original_racer_root_lean_grid.py --corpus /verified/original/source-corpus.json --source-axes /verified/reports/source-chroma-axes.json --model-review-dir /verified/model-review --camera analysis/data/racer-inverse-side-provisional-1205.json --out /new/immutable/root-lean-grid.json
    python3 -m unittest tests.unit.test_study_original_racer_root_lean_grid

Uses optional NumPy and Trimesh through the existing original raster and GLB projection modules. The existing bounded original-ROM GHA research job reruns the grid against **actual** original PNG/source GLBs and publishes numeric provenance in the same artifact set, without launching any new recurring job.

**Next gating study:** add opt-in in-memory lean samples to the *existing* Pages model viewer for owner visual feedback, preserve the default #2832 draft GLB and avoid treating a numerically matching painted-axis direction as reconstructed 1994 physical pose. Validate silhouettes, bottom visible contact and at least one genuinely separate semantic source pose family before proposing any source-model/animation geometry promotion.
