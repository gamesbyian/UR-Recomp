# Where the actual 2026 GLB silhouette comes from, in original source 64px bands

**Purpose:** independent model-only geometric part attribution following [#3116](https://github.com/gamesbyian/UR-Recomp/pull/3116)'s and [#3117](https://github.com/gamesbyian/UR-Recomp/pull/3117)'s authentic Mesen-source-versus-real-GLB evidence. The original blue/red upper source-band mismatch was measured on genuine source OAM/VRAM/CGRAM with fixed y0–14, y15–26, y27–63. Before changing an authored wheel, fork or saddle, identify **which of the *actual 2026 GLB* named parents** produce visible silhouette pixels in the same raw 64px image regions. A source y-band is not a verified original 1994 anatomical part.

**Method:** reuse the existing [#2832](https://github.com/gamesbyian/UR-Recomp/pull/2832) 2026 OpenSCAD five-parent/sixteen-material source model, original SCAD SHA-256 `e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984`. Its GHA OpenSCAD/Trimesh GLB export bytes vary between builds, so authenticate the exact current GLB against the canonical `stage_pages.py::validate` current-success pointer, original source SHA and 16 material-hierarchy record. One camera, the frozen provisional 7:6 side view, SHA-256 `1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028`, with source logical-pixel centre sampling at **4x+2,4y+2**, no auto-fit, and **no modification of GLB geometry, source camera, parts, shaders or original ROM**.

`tools/art/count_real_glb_parent_source_y_bands.py` renders **each** true 2026 GLB parent individually using the existing CPU actual-triangle renderer, OR-unions its binary silhouette with the other four, and records per-band total model pixels, each parent occupancy and pixels **exclusive to one parent** (where four other parents have no projection). It is explicit that overlapping parents are **not additive**. The current authentic source 2026 upright model has 267 visible 64px pixels under this camera; independent old source diagnostics attest its whole-part pre-union occupancy to tire 124, rim 70, fork/frame 46, pedals 14, saddle 56. The new analyzer **fails closed** if those signature counts change for this frozen source model/camera. It may detect build geometry changes despite a constant source SCAD hash. It does not use the original game 2D pixels to choose a different camera or geometry.

A **local exact-GLB exploratory raster** using the source-verified current [#3117](https://github.com/gamesbyian/UR-Recomp/pull/3117) real artifact #13322867450 (upright GLB SHA-256 `bdb2f5bb92735fe023adda73be53b982e1d9added5150eb092c08ae08cc0e5da`) reproduced the independent whole 267px and all five part occupancies. It found candidate neutral **upper y0–14 union=70 source pixels**: authored saddle occupies **56** (of which **52 are exclusive**) and fork/frame occupies **18** (of which **14 are exclusive**); no candidate tire, rim or pedal pixels occupy the upper band at this *neutral 2026 pose*. The overlapping four upper pixels explain why saddle+frame counts exceed 70. The middle y15–26 has union **83**: tire 54, rim 25, fork22. The lower y27–63 has union **114**: tire 70, rim45, pedals14, fork6. These **2026 part-geometry** numbers do not certify original 1994 saddle/wheel parts or why source red upper alpha is displaced. The exact-GHA reproducibility test of these counts is the acceptance gate for this PR, and must be completed before calling the local exploratory numbers independently validated.

**Reproduction:** on the **existing** Windows Visual Atlas real export job, after the same five current source-verified GLB assets have already been produced, run the utility once:

```sh
python3 -m unittest tests.unit.test_count_real_glb_parent_source_y_bands
python3 -m tools.art.count_real_glb_parent_source_y_bands \
  --verified-exports /current/authenticated/model-exports \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  --out /new/2026-real-model-source-y-band-parent-census.json
```

The output is an immutable no-replace JSON report, retained with the real GLB viewer/source evidence artifact. No new Mesen replay, OpenSCAD invocation, standalone workflow or new model source branch. **Decision:** the current static 2026 model's upper image region is overwhelmingly its *existing saddle silhouette*; independently tested source orientation/root articulation still matters greatly, so do **not** automatically increase saddle width or edit geometry. First distinguish current rig pose registration from genuine upper contour/perspective deficits across both original source players, then predeclare one shared geometry shape parameter and require a real source family holdout, or retain the negative. Original 1994 camera/3D mesh/materials and owner likeness remain unverified.


## Follow-up: which actual model part is wrong during authentic original upper motion?

The **neutral** 2026 model census alone cannot answer what moves where: its source-y0..14 upper region consists of 56 saddle and 18 fork/frame projected pixels, but the original Mesen source blue/red upper events occur in already-rotated states. The follow-up `tools/art/attribute_original_mesen_upper_to_real_glb_parts.py` uses the **same exact current source-verified 16-material GLB**, original ZIP/OAM/VRAM/CGRAM/source pose receipts, fixed 7:6 camera, and one tick-1601 registration per racer as the preceding real-GLB comparison.

Scope was fixed before examining new results: **blue Mesen ticks 1602 and 1603, red ticks 1605 and 1606**, only the two existing source-to-rig interpretation arms **absolute wheel-axle root** and **reference-relative mid-body root**, wheel phase and fork/saddle pitch held at zero. Both arms use the same scene, same five GLB named parents and same original 64px source alpha; neither arm receives per-image registration or camera fitting. The source-only 2D rigid-rotation control remains in the report as a baseline.

At each of the eight predetermined arm × original image comparisons, render all five actual GLB parent meshes separately at **256px** using the established source-camera rasterizer. Verify that their 256px logical OR is **bit-exact** to a separate, full real GLB triangle raster. Apply the same whole-model tick1601 anchor shift to *every* part at 256px before sampling source index centres 4x+2,4y+2. Again require the OR of those five registered 64px parts to be **bit-exact** to the registered full 256px silhouette. These are strong fail-closed assurances against part-only pose/registration drift or accidentally counting different model geometry.

In the original image-space bands y0–14, y15–26 and y27–63, report for the whole projected 2026 GLB: source/model alpha centroids, intersection, excess, missing pixels and IoU. For *each* existing 2026 part, report projected support, position, and **exclusive** true/false positive source pixels. If two existing 2026 parts overlap at a source pixel, call the ownership **ambiguous**, never award a double-counted true positive or assert a known original 1994 anatomy/material. Pixels present in original 1994 sprite alpha and absent from **all** 2026 candidate parts are explicitly *unattributed*, rather than being assigned to whichever 2026 model component happened to be nearby.

**Exact calibration correction during qualification:** the original #3104 source region's full-64-angle box-centre mean is `(31.515625,19.5859375)`, but the previously established source-only 2D null fits *even* orientation states 0,2,...62 and obtains `(31.515625,19.578125)`. The first dynamic source comparator mistakenly required the full-census vertical mean while correctly using the even-state calibration algorithm, and failed **before any dynamic GLB render** at [Actions run #41888579139](https://github.com/gamesbyian/UR-Recomp/actions/runs/41888579139). The source ROM/camera/2026 GLB authenticated successfully and the static census remained valid. The dynamic analyzer now requires the **exact source-even mean**, explicitly attested by a separate synthetic even-only fixture; it still fails closed if the SHA-pinned source's calibration ever changes. The earlier failed run cannot be cited as a dynamic part-attribution measurement. The new head needs full exact-head unit and original-real-GLB CI.

A global lower/upper geometry change remains **unjustified** until this dynamic image-space ledger shows whether the failed source upper silhouette comes from incorrect *pose registration*, the 2026 saddle contour, the fork/frame silhouette, overlapping projection, or genuinely unknown original source structure. The 1994 authored mesh, camera, light rig and skeletal joints remain unidentified. No new Mesen replay, OpenSCAD build, CI workflow, temporary model fork or shipping-art claim occurs. The existing Windows Visual Atlas real-GLB validation simply retains the new JSON evidence alongside the already produced viewer and original-source comparison.

Run after the existing authenticated current exporter, using the same SHA-verified input artifacts:

```sh
python3 -m unittest tests.unit.test_attribute_original_mesen_upper_to_real_glb_parts
python3 -m tools.art.attribute_original_mesen_upper_to_real_glb_parts \
  --source-zip /original/sha-verified/mesen24.zip \
  --pose-report /original/sha-verified/pose-report.json \
  --axis-report /original/sha-verified/axis-report.json \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  --verified-exports /current/source-validated/model-exports \
  --out /new/real-original-upper-parent-attribution.json
```

This is a new, predeclared, source-matched comparison. **Do not report numerical results until the exact new PR head has run the genuine model export, source checks, and real-image scorer.**
