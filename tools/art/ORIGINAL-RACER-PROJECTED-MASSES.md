# ART-4K source-bound original first-family projected masses

This is a measured, **source-registered 2D shape constraint**, not a reconstructed 1994 model, true camera or approved likeness. It extends [first-family source corpus](build_racer_source_pixel_corpus.py), [source colours](ORIGINAL-RACER-COLOURWAY-SOURCE.md), [real five-pose comparison](REAL-GLB-POSE-SIMILARITY-MATRIX.md) and the **single draft #2832 rig**. Do not create a second viewer: #2938/#2957 own the Pages review tool.

## Inputs and meaning

The retained original USA ROM-composed 64x64 P1/P2 guest frames 1205–1220 are first reauthenticated by the existing corpus loader (source representation, ROM SHA, PNG file SHA, decoded RGBA and binary silhouette SHA). They represent 32 player/frame observations but only **10 independent binary silhouette shapes** (six P1, four P2); repeated animation holds receive no extra weight. No ROM re-extraction, 3D original camera or independent source-family holdout is claimed.

The new stdlib tool uses **two explicitly frozen source logical-pixel row windows**: upper rows **0–9** (saddle-like occupancy) and lower rows **22–38** (wheel-like occupancy). It records inclusive alpha bounding rectangles and dimensionless centre/width/clearance ratios, correcting horizontal distances by the original **7:6** source pixel aspect. These are deliberately **window regions, not segmented 3D mesh parts**. The tool fails on a sprite outside the verified ordinary-racer family morphology instead of assuming this window is valid for wheelies or stunts.

Actual archived original sprite bytes in [successful real-GLB viewer run #13063969312](https://github.com/gamesbyian/UR-Recomp/actions/runs/41259476190/artifacts/13063969312), independently file-hashed against the authenticated viewer sprite rail, yield:

| Dimensionless projected source ratio, one vote per original binary mask | P1 | P2 |
| --- | ---: | ---: |
| Upper width / lower height | 1.086601 | 1.080882 |
| Lower width / lower height | 1.235294 | 1.235294 |
| Vertical upper/lower centre separation / lower height | 1.431372 | 1.397059 |
| Clear rows between masses / lower height | 0.705882 | 0.705882 |
| Upper X minus lower X centre / lower height | -0.154412 | +0.128676 |

The **actual 2026 material-separated upright GLB**, read from the same retained artifact, has ideal unposed side-view X/Z tire width-to-height **1.0**, saddle width / tire diameter **0.989245**, and saddle-to-tire centre separation / tire diameter **1.18**. Comparing mathematically ideal GLB part bounds to painterly, quantized, 7:6-corrected original pixel silhouettes is a **diagnostic only**. Source camera/lighting, pose and original 3D saddle/tire geometry remain unknown. These differences are hypotheses requiring controlled projection tests, not authorizations to distort the canonical model.

See [hash-bound real sprite and GLB evidence](../../analysis/data/racer-first-family-viewer-projected-masses-20261101.json). All original camera, held-out-family, original sprite-to-GLB pose and likeness/shipping status remain explicitly false.

## Reproduce (no GPU, model rebuild or ROM required)

    python3 tools/art/audit_original_racer_projected_masses.py
    python3 tools/art/audit_original_racer_projected_masses.py --out /path/to/new/source-proportions.json
    python3 -m unittest tests.unit.test_audit_original_racer_projected_masses

The original corpus loader reauthenticates inputs first; the output is once-only published with the existing no-clobber helper. Stdlib tests cover duplicate animation holds, original source tampering, wrong frame/player/ROM, invalid alpha, changed morphology and real retained PNGs on an actual checkout.

**Next:** obtain an independent different pose-family source window with the existing #2968 ROM exporter and freeze holdout partitions. Test one locked side/three-quarter camera interpretation and exact source contact placement across that family before altering saddle, fork and tire shape. Previous single-frame widening of the saddle proved counterproductive in the ten-mask study. Keep the unapproved blockout reversible, and retain independent owner likeness review before native integration.


## Controlled real-GLB camera-versus-wheel-width ablation

A follow-up test uses the **actual same upright 16-mesh GLB**, authenticated 32 source observations/10 SHA-independent source masks and existing source-registered 64px lowest-alpha positions. The camera remains the one existing **provisional** P1:1205 side camera: vertical 9.5 logical pixels per model unit, horizontal scale 6/7 to account for the stated SNES 7:6 PAR, anchor [67,76] half-pixels, no per-frame fitted shift/zoom or guessed 1994 pose identity.

Two deliberately different hypotheses were tested, using the same ten original shapes and one vote per source mask.

| Hypothesis | Mean source-mask IoU | Worst mask IoU |
| --- | ---: | ---: |
| Unchanged experimental wheel/rim and fixed camera | 0.57255469 | 0.47607053 |
| Whole-model horizontal camera factor 1.0 instead of 6/7 | 0.55147386 | 0.47517730 |
| Wheel + rim world-X scale 1.05, all other parts unchanged | 0.59453184 | 0.49748744 |
| Wheel + rim world-X scale **1.10**, all other parts unchanged | **0.59883507** | **0.50123457** |
| Wheel + rim world-X scale 1.15, all other parts unchanged | 0.55958054 | 0.47215496 |
| Wheel + rim world-X scale 1.20, all other parts unchanged | 0.53307955 | 0.44941176 |

Widening the wheel *alone* has a repeatable positive signal within this short family, whereas globally stretching the camera/candidate would degrade it. These are original-raster **training-family** IoUs against the current *2026 upright* hypothesis, not identified 1994 3D proportions or source-authentic pose labels; a mathematically circular 3D wheel may still be the true original design. The observed gain at 1.10 could reflect a wrong camera, image quantization, OAM composite or unsupported pose correspondence. **No permanent tire geometry or material was changed.**

The optional offline reproducibility command (requires NumPy, Trimesh and Pillow, uses existing source and GLB authenticator):

    python3 tools/art/ablate_original_racer_wheel_width.py --model-review-dir /path/to/verified/model-review
    python3 tools/art/ablate_original_racer_wheel_width.py --model-review-dir /path/to/verified/model-review --out /path/to/unused/immutable-wheel-ablation.json
    python3 -m unittest tests.unit.test_ablate_original_racer_wheel_width

That script does not create GLBs, change source PNGs, edit the existing viewer or run by default in CI. Wheel/rim X coordinates are varied **in memory only**, one immutable source geometry per factor, with every other part's world vertices unchanged. Source original PNGs and contact anchors are authenticated again. The [machine-readable real-data diagnosis](../../analysis/data/racer-first-family-viewer-projected-masses-20261101.json) records the tested factors and the whole-model camera-stretch negative control.

**Required before a model refit:** verify improvement in a different authentic original pose family *not used to choose the 1.10 factor*, and test a source-respecting camera model and physical wheel circularity. A training-family improvement alone cannot remove the owner character-likeness veto.
