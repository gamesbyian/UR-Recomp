# Original-source frame-mass sensitivity of the existing ART-4K unicycle rig

**Status:** 2026-11-01 bounded offline experiment using the **single existing draft #2832 OpenSCAD model**, never a new 3D character model, source-camera recovery, or owner art approval. Read the hash-registered [five-trial result](../../analysis/data/racer-frame-mass-original-source-ablation-20261101.json).

## Motivation and measured result

The source-art comparison has already demonstrated an optimizer trap: widening the saddle 1.4× improves one manually selected original P1 sprite but makes the **ten-source-image** fit worse. The unchanged OpenSCAD rig also exposes `rig_frame_mass` [1.0, 2.0] as a bounded, source-authored frame/fork thickness parameter. The new experiment assesses that axis across the same **10 distinct authentic original 64×64 binary silhouettes**, using one equal weight per source shape, original 7:6 physical pixel aspect, one unmodified provisional camera and exact registered 2D lowest-alpha contact offsets (without per-sample score-based alignment).

| Existing rig frame mass | Original-shape mean IoU | Mean physical boundary Chamfer, lower is better |
|---|---:|---:|
| 1.0, current unmodified blockout | 0.57255469 | 0.97432622 |
| 1.2 | 0.57505352 | 0.96930239 |
| 1.4 | 0.58271615 | 0.96785973 |
| 1.6 | 0.58220835 | 0.96194186 |
| 2.0, upper authorized study bound | 0.58539651 | 0.96121329 |

**Nuance:** P1's six source shapes improve steadily to 2.0, while P2's four shapes have their best mean IoU near 1.4 and lose some ground at 2.0. The aggregate 2.0 improvement is **not** proof of authentic geometry or source camera. The source-family holdout remains unavailable, original 3D source pose pairing is unverified, and model proportions should remain unchanged until an independent 3D/source art review. The current study compares one 2026 procedural `upright` pose against a **family** of original 2D silhouettes without claiming those silhouettes correspond to its real original pose.

## Reproduce from one exact canonical 2026 procedural model

Use the existing model source **from #2832's branch** (`tools/art/candidates/unicycle_shared_rig.scad`, SHA-256 `e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984`) and a repo checkout containing source-authenticated original first-family PNGs. No original ROM is required for this narrow retained source study.

```sh
# The source SCAD comes from the existing draft rig branch, not main:
# provide the exact file path from your model workspace.
python3 tools/art/ablate_racer_frame_mass.py \
  --source-scad /private/art4k/unicycle_shared_rig.scad \
  --source-scad-sha256 e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984 \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  --mass 1.0 --mass 1.2 --mass 1.4 --mass 1.6 --mass 2.0 \
  --out /private/ur-art4k-evidence/frame-mass-study.json

python3 -m unittest tests.unit.test_ablate_racer_frame_mass
```

This opt-in tool invokes the **already installed** OpenSCAD executable; requires optional NumPy and Trimesh for STL/world-mesh work. It starts from a fully SHA-verified SCAD source, rejects unknown source entrypoint or parameter, exports the existing tire/rim/pedals(18)/saddle(0) once, rebuilds only the existing `fork_and_frame()` source module at each mass, and assembles the identical five-part source geometry for fixed 4× silhouette projection. It refuses out-of-range or duplicate parameter trials, missing unmodified 1.0 baseline, wrong original PNG/registry source, impossible source contact/camera registration, clipped candidate, and nonfinite metrics. Only numerical source/model SHA and scores are published via a **no-overwrite, outside-repository** output; intermediate STLs are deleted from a private temporary directory. The original canonical rig remains untouched. The baseline mass1.0 is independently required to match **0.57255469** for this exact source model and registered original corpus.

## Exact 3D clearance counterweight: source fork/tire CSG

A new **opt-in** guard uses the exact same authenticated model source and original OpenSCAD modules to compute `intersection(){ translate([0,0,1]) fork_and_frame(); translate([0,0,1]) tire(); }`. Unlike silhouette overlap, this is the actual **3D solid-intersection volume** of the source-authored fork and tire. See the [hash-bound three-mass CSG study](../../analysis/data/racer-original-rig-frame-tire-csg-20261101.json). All three source-derived intersections were independently processed as consistently wound **watertight** solids by Trimesh; raw STL SHA-256, connected-component counts and triangle counts are recorded. The run uses OpenSCAD **2021.01**, Trimesh **4.11.1**, and the exact #2832 SCAD digest `e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984`.

| Frame-mass value | Source 3D fork ∩ tire volume (model units³) | Relative to 1.0× | Original 2D mean IoU |
| --- | ---: | ---: | ---: |
| 1.0×, unchanged | 0.00121168 | 1.00× | 0.57255469 |
| 1.4× | 0.00560623 | **4.63×** | 0.58271615 |
| 2.0× | 0.01882075 | **15.53×** | 0.58539651 |

This is a *mechanical/visual interference warning*, not an inference that 1994 Uniracers had a physically collision-free virtual CAD model. Even the existing 1.0× blockout intersects slightly around the axle/sidewall, potentially an intentional local join. But the much larger 2.0× intersection is real **within the current procedural 3D asset**, so it must be reviewed in the interactive viewer before selecting a heavier frame based on mean 2D silhouette scores. The 2.0× candidate is therefore **not promoted** despite its modest IoU/Chamfer gains. This finding underscores why geometric source fitting should constrain actual 3D assembly viability, not blindly optimize the projected 2D mask.

To reproduce using the *existing* ablation producer (no new model exporter or web viewer):

```sh
python3 tools/art/ablate_racer_frame_mass.py \
  --source-scad /private/art4k/unicycle_shared_rig.scad \
  --source-scad-sha256 e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984 \
  --mass 1.0 --mass 1.4 --mass 2.0 \
  --measure-frame-tire-csg \
  --out /private/ur-art4k-evidence/frame-mass-plus-clearance-new.json
```

Omit `--measure-frame-tire-csg` to preserve the lightweight legacy silhouette study. The additional operation is explicitly **bounded and optional**. It fails closed if OpenSCAD cannot create a complete intersection solid, if Trimesh finds non-watertight or inconsistent winding, if volume or SHA is invalid, or if the selected mass is outside the existing source-authored [1.0,2.0] interval. All intermediate STLs stay private; only SHA-bound numeric evidence is published through the existing no-replace helper. The original rig, simulator, viewer and Pages deployment remain unchanged.

## Next responsible step

The source-mapped research demonstrates a bounded potential improvement in fork/frame visual mass, unlike the saddle-width single-frame overfit. The **model owner** should evaluate 1.4 and 2.0 in the *existing* [3D Pages reviewer](model-review/README.md), compare period 1990s CGI character art and actual 1P/2P gameplay scale, and test a **different original sprite-pose family** as a real untouched holdout before changing the canonical SCAD default. The original frames 1205–1220 are a closely related same-camera family, so a higher mean IoU is not an independent scientific reconstruction victory. Do not merge candidate settings automatically, and never modify native gameplay/HD fallback/release ledger based on this ablation alone.

**Coordination:** The current model owner is [draft #2832](https://github.com/gamesbyian/UR-Recomp/pull/2832); the sole interactive visual reviewer is [#2938](https://github.com/gamesbyian/UR-Recomp/pull/2938), and its optional research sidecar producer is merged [#2950](https://github.com/gamesbyian/UR-Recomp/pull/2950). This adds no second model/viewer or per-push GHA compute.
