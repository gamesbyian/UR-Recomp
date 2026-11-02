# Original-ROM painted region versus depth-visible 2026 GLB: area and length

This post-hoc ART-4K experiment compares **2D high-chroma source raster measurements** to **depth-visible blue-material pixels in the single existing 2026 experimental rig**. It follows #3035 (original 2D wheel), #3038–3039 (registered material direction), #3047 (material depth visibility), and #3050 (source connected-component morphology). No new rig, original sprite, runtime renderer or Pages control is created.

## Why area and length must be separated

The source painted-frame direction and a candidate 2026 frame hinge can agree while their visible coloured footprints do not. Source RGB pixel count provides a raster **area**, the 7:6-corrected physical-pixel separation between the top and bottom three coloured-row centroids provides an **axial length**. Their ratio is only an *area per unit projected length proxy*, not a physical cylinder width or true original texture thickness.

For each of the 35 exact binary source masks (one vote per mask, not one vote per original ROM frame), the existing authenticated original colour-axis report supplies all separately observed P1/P2 RGBA variants, top/bottom centroid coordinates and original high-chroma count. The tool pins **the exact 2026 upright real GLB bytes, original source chroma receipt, and fixed provisional camera** by SHA-256. It rotates the existing fork+saddle parents through the original predeclared −45° to +45°/5° grid; for each candidate it depth-tests all sixteen original GLB material meshes. An original 2D painted-frame angle chooses the nearest projected blue-axis orientation **without reading silhouette overlap**. The model blue count and model visible axis length are then compared with each original RGB variant. No model-root translation, pose replacement, per-source segmentation retuning, skinning or source-authentic animation is introduced.

### First real-source and actual-GLB measurements

An independent offline actual GLB / source-colour comparison with the historical provisional +world-Y viewpoint gave these descriptive ratios:

| One vote per distinct original binary source mask | Mean source/model painted pixel area | Mean source/model painted axial length | Mean source/model area per axial length |
|---|---:|---:|---:|
| All 35 source masks | **1.49821244** | **0.91236878** | **1.64438023** |
| Historical first 16 | 1.54651596 | 0.88630568 | 1.74558196 |
| Additional 19 source SHA-distinct masks | 1.45753579 | 0.93431666 | 1.55915773 |

All **35** original source binary masks contained more painted pixels than their selected 2026 blue-material model projection; original region area averages about 50% greater, even though the measured original colour-axis **length averages about 9% shorter**. This opposes an immediate conclusion that the 2026 fork merely needs to be lengthened. Stronger alternative hypotheses include painted-area thickness, high-chroma segmentation of multiple original sprite parts, different palette/shading, and camera / materials correspondence. This numeric disparity does NOT establish which explanation is correct, and no geometry/colour defaults should be changed without visual and independent source evidence.

One limitation: these descriptive figures were first calculated from original SHA-pinned chroma and actual depth-visible GLB receipts using local analysis; the new tool is their reproducible full GLB producer, with SHA and source-variant verification and named immutable output. The original source report was itself produced through authenticated original PNG/ROM checks, **but this tool only revalidates its exact SHA**, not raw PNG bytes. The original camera is provisional and uncalibrated. The painted red/blue area may not match the same physical component as the 2026 GLB blue fork. Pose selection, camera and material hypotheses developed after inspecting these source families. No independent generalization, 1994 3D reconstruction, authentic animation timing, likeness or shipping art approval follows.

## Run and audit

Requires the exact historical 2026 upright GLB SHA `efdc8425...`, the frozen camera SHA `1261016b...`, and original-ROM 2D chroma report SHA `78f42042...`. Optionally supply the SHA-disjoint first16/additional19 report SHA `aa86e133...`. NumPy/Trimesh are required for the optional real geometry run. The unit tests' pure reducer is dependency-free and only the actual binary-mask test skips without NumPy.

    python3 -m unittest tests.unit.test_evaluate_original_racer_painted_extent
    python3 tools/art/evaluate_original_racer_painted_extent.py \
      --glb /private/historical-upright.glb \
      --camera analysis/data/racer-inverse-side-provisional-1205.json \
      --source-chroma /private/source-chroma-axes.json \
      --source-family /private/wheel-holdout.json \
      --view-y 1 \
      --out /private/new/original-painted-extent-comparison.json

The resulting numeric JSON is write-once through the existing no-replace publisher, reports all 35 binary mask identities and every original RGBA variant's area/length ratios, and identifies uncertainty and unsupported physics explicitly. It does not create a new workflow, source-pixel upload or shipping-art acceptance result.
