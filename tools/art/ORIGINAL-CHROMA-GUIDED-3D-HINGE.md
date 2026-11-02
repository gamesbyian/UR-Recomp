# ROM painted-axis guided 3D hinge, same shared model

This stacked ART-4K research experiment depends on source 2D wheel-ring candidates #3035 and source-wheel-registered real GLB comparison #3038. All three use the same canonical-ROM original sprite corpus, historical 2026 five-parent/16-material unapproved GLB, and the same frozen provisional 7:6 camera. No second unicycle, viewer, geometry pipeline or runtime animation selector is added.

The earlier binary pose rule selected a −40° fork/saddle hinge whenever the original sprite painted-axis angle exceeded +20°. Both thresholds were retrospective. This experiment instead computes the projected painted-axis angle of the **actual blue fork material** in the source GLB under each predeclared 5° hinge angle from −45° through +45°. The original sprite's signed 2D player-colour axis (original validated source chroma report) chooses whichever GLB blue-fork *projected axis angle* is nearest. It does not use the original source silhouette IoU to choose the 3D pose. The tire/rim/crank remain fixed; only the existing fork+seat parent matrices rotate about the actual wheel axle. No meshes are modified or saved. Source wheel-centre candidates then determine translation **without a model target-silhouette overlap search**. All tied one-pixel source wheel positions are reported as min/max, never silently reduced to one model-selected pixel.

Actual same-corpus real-GLB output:

| Equal-weight 35 exact source binary masks | Historical lowest-alpha alignment | Source-only wheel-centre fit, worst tie | Source-only wheel-centre fit, best tie |
|---|---:|---:|---:|
| Unhinged source blockout | 0.46002071 | 0.41237579 | 0.42198267 |
| Earlier binary post-hoc colour-axis 0°/−40° choice | 0.54715522 | 0.49514691 | 0.50339133 |
| New 5° discretized 3D painted-axis matching | **0.57140708** | **0.50134334** | **0.51176089** |

First connected 16 masks score 0.59332420 under old alpha alignment, 0.52879948–0.54913335 under the original wheel-centre interval. Additional 19 SHA-disjoint masks score 0.55295055 / 0.47822237–0.48028935 respectively. Model blue painted-axis angle spans about −36.17° to +48.27° as the frame hinge runs +45° to −45°. The selected hinge set includes multiple positive and negative angles. Across all 35 original masks, the mean source-to-model *painted-axis* difference on the selected 5° grid is ≈1.19° in **2D image coordinates**, not a 3D joint-angle accuracy metric.

The new semantic cue makes the selection mechanism more interpretable, but its gains are **retrospective and not independent holdout evidence**. All 35 source silhouettes, the original colour axes, grey-ring heuristic, chosen blue GLB material, frozen camera and 2026 blockout are from previously inspected reference families. The 2026 blue fork's painted region need not match the exact anatomical region the 1994 source sprite painted red/blue. Source colour and rim segmentation are partially engineered heuristics. No 1994 source camera calibration, genuine original-animation chronology, owner likeness or shipping art is established. The next acceptance test requires genuine unseen emulator-produced PPU/OAM frames and consistent source/model part landmark mapping.

Reproduce offline after extracting the retained source-corpus ZIP from run #41396846120, historical original upright GLB from run #41259476190, original source painted-axis report from run #41398486394 and optional source family split:

    python3 tools/art/evaluate_original_racer_chroma_guided_3d_hinge.py \
      --corpus /private/original-source/source-corpus.json \
      --glb /private/historical-model/upright-efdc8425f252b4a0.glb \
      --camera analysis/data/racer-inverse-side-provisional-1205.json \
      --source-chroma /private/source-chroma-axes.json \
      --source-family /private/wheel-holdout.json \
      --out /private/new/chroma-conditioned-hinge.json

This retains all original source/file SHA gates, applies the existing fourfold GLB rasterizer, uses the existing write-once numeric receipt publisher, and does not commit ROM PNGs or full GLB files. Unit tests are ROM-free; actual experiment requires optional NumPy, Trimesh and the private authenticated source receipts. No new workflow or source-data upload is required.

## Painted material overlap is a separate, unresolved visibility constraint

The GLB painted-axis is computed from the blue fork material alone, BEFORE any real depth-tested compositing. I independently projected the other 15 original material meshes and found that **approximately 36–43%** of the blue material's 64px projected pixels ALSO lie within another projected material mask across the inspected −45..+45° hinge range. This measures **projected overlap, not occlusion**: the other material can be behind the blue paint or in front of it, and the current silhouette renderer has no z-buffer. The tool now emits per-angle projected blue occupancy, other-material overlap counts and overlap fractions, explicitly marking true visible-pixel depth order as unknown. The ≈1.19° blue-axis agreement is therefore an unoccluded material-projection agreement only, and source-visible painted-axis parity cannot be accepted without proper depth/composition and source colour segmentation verification. This finding is a reason to build the next depth-aware semantic projector, not to refit an unchecked 3D hinge angle.

## Fixed-raster residual decomposition of the source-guided pose fit

A separate independent analysis of the same 35 authentic source alpha masks and real-model projection indicates that choosing the 3D frame pose through the 2D painted-axis reduces the **upper source raster-band mismatch** from 4,160–4,246 pixels (unhinged upright) to 2,455–2,535 pixels (source-axis chosen pose) when summing one vote per original source binary mask and retaining all ring-centre candidate ties. That is about a 40% improvement in upper-band XOR error. Middle rows Y=16..31 decrease more modestly from 3,541–3,609 to 3,352–3,446; lower occupied Y=32..39 remains **900–934 exactly unchanged**, consistent with rotating fork+saddle around a stationary wheel. Y=40..63 is empty. These bands are fixed raster rows, not anatomical labels. The tool now calculates and reports the per-source band envelopes and their aggregate, with explicit union-pixel denominators and XOR conservation tests; per-band best/worst candidate bounds are NOT a joint statistical confidence interval, and different regions may attain their extrema at different tied source centres. The remaining source-band errors do not license proportional source-model edits before independent frame/part registration.
