# ART-4K original raster-pixel motion versus experimental 3D pose motion

## Purpose and boundaries

A temporal label such as `bank → upright` is not itself evidence that actual pixels of the 1994 source silhouette move in the same way as projected geometry of the 2026 experimental model. Moreover, repositioning a *static* GLB to the source sprite's changing bottom alpha can produce apparent model motion without changing a joint. This small source-authoritative diagnostic separates those effects before attempting continuous pose fitting.

The tool `audit_original_racer_pose_transition_pixels.py` adds **no new model, OpenSCAD source, renderer, worker lane or Pages viewer**. It runs inside the existing path-filtered original-ROM experiment after the source-authenticated 35×5 matrix and all-window pose sequence exist.

It independently checks the exact canonical USA-ROM corpus receipt plus all original 64×64 PNGs, the matrix/sequence file digests and independently reproduced label sequence, the original 35-mask census, the original 27-window/144-player-observation/109-consecutive-edge chronology, all five SHA-locked real GLB meshes from the existing viewer artifact, and the unchanged 7:6 provisional camera. Each of the actual 175 original-mask/model-pose IoU values is independently recomputed from projected geometry and source-visible-alpha registered binary masks. Any mismatch refuses publication.

For each actually adjacent original P1/P2 guest-frame edge, compare three binary masks:

1. **Original ROM source change** between the two independently authenticated original raster silhouettes, pixelwise XOR.
2. **Placed model change** between corresponding model poses, with each pose independently placed using its corresponding original sprite's visible-bottom alpha anchor, pixelwise XOR. This can include a translation attributable to source-visible placement.
3. **Pose-only model change** at the **same previous original source anchor**, so moving the placement anchor does not masquerade as articulation.

Track source versus predicted change-pixel intersection, missed original pixels, extra model change pixels, IoU, recall and precision. Empty/held source transitions are explicit, including model false motion. Report true label flips, placement-anchor changes and pose-only raster changes separately. A source binary hold is not an independent time-varying 3D-camera observation. The source anchor is **lowest visible alpha midpoint**, not a physically verified tire-road contact.

### Reproduce with authentic, private original source assets

```sh
python3 -m unittest tests.unit.test_audit_original_racer_pose_transition_pixels
python3 tools/art/audit_original_racer_pose_transition_pixels.py \
  --corpus /private/verified/source-corpus.json \
  --pose-matrix /private/reports/original-35-by-five-real-glb-pose-matrix.json \
  --pose-sequence /private/reports/original-all-window-discrete-pose-sequence.json \
  --model-review-dir /private/verified/real-model-site/model-review \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  --out /private/new/original-temporal-model-pixel-motion.json
```

The output is write-once. The canonical original-ROM GitHub Actions job verifies the source controls and publishes only the bounded numeric JSON report among its existing short-lived research artifacts. It includes strict acceptance counts **109 observed per-player adjacent edges, 19 source silhouette-change edges and 90 source holds**. All experimental art/release approval booleans remain false.

### How to interpret results

Model transition recall is meaningful only for comparing **declared, unchanged model assumptions**, never identifying 1994 original 3D joint angles or true rig time. Training selections have already inspected all 35 masks, so these are **post-hoc explanatory diagnostics**, not a newly untouched shape-family holdout. The distinction between pose-only and source-placed motion directly identifies when a seemingly good transition score comes from source anchor shifts rather than 3D articulation.

Next actual 3D step: use the existing draft #2832 continuous source-owned `ride` and `stunt_cycle` authoring paths. Export a *predeclared bounded time grid* with immutable GLB/transform receipts, then score original-frame-wise **differences** with a fixed camera and frozen family exclusions before any optimization; report motion hallucinations on source holds as strongly as gains on original transitions. Never map a normalized 2026 rig time directly to an original 1994 guest frame without new evidence, and do not introduce a second rig or viewer.
