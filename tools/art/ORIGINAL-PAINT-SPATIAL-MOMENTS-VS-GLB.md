# Original-ROM 2D painted spatial moments against existing 2026 model

**Unapproved ART-4K research only.** This source-bound diagnostic compares the original USA ROM-composed P1 red / P2 blue high-chroma pixel distributions with the blue fork material of the ONE historical 2026 GLB, under the uncalibrated 7:6 side camera and source-painted-axis-selected bounded 5-degree frame hinge grid.

The previous #3052 area-versus-length study found approximately 1.50 times the original painted **area** relative to the modern 2026 blue projected area, but only 0.912 times the model's axial **length**. A large area ratio can reflect a fatter painted region, different anatomical colouring, detached accents, and camera/segmentation differences. This follow-up measures major versus minor spatial spread independently of target silhouette-overlap alignment.

## Measurement definition and provenance

For each source high-chroma pixel coordinate, multiply its image X by 7/6, calculate population covariance of the physical 2D positions, and take the square root of its two positive eigenvalues. The resulting major/minor **screen-space spatial standard deviations** are translation invariant, and there is no model-fitting silhouette shift. These are NOT literal part thickness, original 3D cross-section, camera depth or probability intervals.

For original source 2D evidence, the producer independently revalidates the canonical exact ROM source-corpus manifest, each of 41 PNG bytes and decoded RGBA/binary alpha digests, original player identity and 35 source binary groups, then verifies that those 41 colour variants match the already published original painted-axis census. For model evidence, it pins the exact historical unapproved five-part GLB and fixed provisional camera SHA-256; the existing actual 16-material triangle depth renderer excludes genuinely obscured blue pixels under the selected side view. The original source mean painted-axis observation selects the authored 2026 frame hinge from -45 through +45 degrees in fixed five-degree intervals, without target silhouette IoU. Original 2D RGB variants remain separate and each unique binary silhouette receives one aggregate vote.

## Initial actual original sprite and GLB observation

An independently coded prior run against the authentic 41 original source images and actual 2026 GLB yielded:

| Source painted spatial spread relative to model visible blue | Major-axis sigma ratio | Minor-axis sigma ratio | Original shapes with larger minor spread |
| --- | ---: | ---: | ---: |
| All 35 original binary silhouettes | 1.20853026 | **2.80416866** | 35/35 |
| Historical first16 masks | 1.20311547 | 2.77802070 | 16/16 |
| Additional19 distinct original alpha SHAs | 1.21309009 | 2.82618799 | 19/19 |

The source's high-chroma 2D image is distributed much more broadly across its minor spatial axis than the projected 2026 blue-fork material under this exact provisional camera. This makes the **paint-footprint/part-correspondence hypothesis** worth testing before modifying the rig's length or width. It does NOT authorize widening the actual 2026 model fork by 2.8 times. The 1994 sprite may colour multiple anatomically distinct surfaces; the rig may use another camera or material partition. The original camera, original physical joints, and independent unseen views remain unproven. Prior hypotheses were developed on the very same source corpus, including the additional19 masks, so these results are retrospective, not a held-out 3D geometry success.

## Reproduction and counterexamples

Use the original privately retained authentic source PNG corpus from run #41396846120, exact historical 2026 upright GLB SHA beginning efdc8425, pinned original 2D colour-axis receipt SHA beginning 78f42042, frozen camera SHA beginning 1261016b and optional source family split SHA beginning aa86e133. The code uses the repository's existing actual source and model validators, source-paint connectivity and depth rasterization, and the existing write-once numeric report publisher. NumPy and Trimesh are optional for the full data run; the synthetic 2D-moment tests use the standard library.

    python3 -m unittest tests.unit.test_evaluate_original_racer_paint_spatial_moments
    python3 tools/art/evaluate_original_racer_paint_spatial_moments.py \
      --glb /private/historical-upright.glb \
      --camera analysis/data/racer-inverse-side-provisional-1205.json \
      --corpus /private/source-corpus/source-corpus.json \
      --source-chroma /private/source-chroma-axes.json \
      --source-family /private/wheel-holdout.json \
      --view-y 1 \
      --out /private/new/original-2d-painted-spatial-moments.json

Any 1994 original emulator frame sequence must still be independently captured and audited. The 3D model and Pages viewer, source ROM, Windows game and shipping art remain untouched.
