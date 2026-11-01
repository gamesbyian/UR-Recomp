# First complete unpaired source-to-model pose similarity matrix

**2026-11-01, inverse-graphics research only.** This work is downstream of the [single viewer already merged in #2938](https://github.com/gamesbyian/UR-Recomp/pull/2938), the real-asset baseline [#2944](https://github.com/gamesbyian/UR-Recomp/pull/2944), and the provisional camera/candidate scorer. It introduces no second rig, new image classifier or model viewer.

The immutable reference run is [original 5-pose GLB artifact #13063969312](https://github.com/gamesbyian/UR-Recomp/actions/runs/41259476190/artifacts/13063969312), sourced from draft #2832 at commit \`d061cddcdbac9b2b5ac137d0d721b63f92dc3ec1\`. Its five model hashes and all original sprite hashes were independently checked against the retained first-family corpus. The [complete baseline matrix](../../analysis/data/racer-unpaired-real-glb-pose-matrix-20261101.json) records each authentic binary-source shape SHA, all 50 silhouette IoU scores and provenance, without committing 1994 artwork or GLBs.

## Measurement and why the result is a warning

Under the **same** *provisional* P1 frame1205 camera (9.5 source logical px per 2026 model unit, SNES horizontal PAR 7:6, no per-frame recenter/zoom), all 32 original frame observations collapse into **10** distinct authentic 64×64 binary silhouettes. The five experimental 3D poses are scored independently against each source shape, giving **50** image comparisons.

| Actual GLB study | Mean IoU, weighting each authentic silhouette once | Highest IoU for N original shapes |
| --- | ---: | ---: |
| upright | 0.48114718 | 0 / 10 |
| pedal | 0.47762999 | 0 / 10 |
| wheelie | 0.33199071 | 0 / 10 |
| stunt | 0.20627268 | 0 / 10 |
| bank | 0.50781314 | 10 / 10 |

**Bank tops every original shape, even though none of the ten has an authenticated bank pose mapping.** This most likely reflects a projection/geometry/IoU preference for that model silhouette rather than ten genuine bank poses. Likewise, P1 frame1205 \`upright\` scoring 0.58288770 and \`bank\` scoring 0.60540541 does not mean \`bank\` is the authentic pose. The provisional camera was selected for a different 3D study and is **not** independently registered to the other nine binary masks. Both source-player framing and 3D animation introduce confounds.

This finding is useful as a **negative control for automatic pose mapping**: selecting the highest IoU to assign a frame to a model pose would produce systematically misleading labels. It also reveals that a five-pose render library does not yet span the original animation's actual shape dynamics.

## Correcting 2D placement from original-source semantic registration

The original game representation registry already specifies an object-local `wheel_contact_x2_y2` anchor (source `64x64` pixels, fixed-point factor 2) derived from each genuine original silhouette's **lowest visible alpha row**. Across the first-family sprite groups, its horizontal coordinate ranges **57 to 69**, versus the P1 frame1205 value **67**. This is a **known source placement contract**, not a physically proven 1994 collision-contact coordinate and not an automatic image-alignment parameter.

Run the same **five real GLBs × ten original source shapes** with `--registration-mode source-registered`. The tool verifies the exact original registry SHA against the independently authenticated source corpus, requires each original sprite identity to have the correct source-player anchor, and translates the projected model image by **exact integer logical-pixel** differences `(source_anchor_x2 - 67)/2`, rejecting any half-pixel parity mismatch or clipping rather than rounding or trimming. Camera orientation, fixed 9.5 px/unit scale, world-origin assumption, original 7:6 physical pixel aspect and 3D geometry remain identical. Distinct original masks with contradictory registered contacts are rejected instead of silently choosing a representative.

At 9.5, **the registered-anchor IoU winner split becomes upright 5/10 and bank 5/10**, instead of bank 10/10 at the P1:1205 witness anchor. Mean one-vote-per-original-shape IoU rises to **0.57255469 (upright)** and **0.57434425 (bank)** from 0.48114718/0.50781314 under the fixed P1 witness anchor. See the [source-registered 50-score table](../../analysis/data/racer-real-glb-registered-anchor-pose-matrix-20261101.json). This is improved alignment to known original sprite coordinates, **not** improved 3D mesh fidelity. Even after alignment, `wheelie` and `stunt` remain very poor unpaired matches, which cannot yet be attributed to an incorrect shape versus missing source pose/angle correspondence.

## A nine-point real-GLB saddle-width ablation falsifies the single-frame fit

The earlier 1.4× saddle-X width trial maximized **one manually selected** original P1 frame1205 IoU at an additionally tuned camera scale9.4. An independent [nine-point multi-source ablation](../../analysis/data/racer-real-upright-saddle-multisource-ablation-20261101.json) reused the real 16-material published `upright` GLB, varied **only** its saddle child mesh X span around its source pivot x=0.04 (all other wheel/fork/rim/pedals geometry unchanged), and evaluated one common scale9.5 camera using the original-source-registered placement for **all ten different first-family binary silhouettes**. Each source shape counts once.

| Saddle X span | Mean IoU | Mean 7:6 boundary Chamfer, physical px |
| --- | ---: | ---: |
| 1.0× (original unapproved blockout) | **0.57255469** | **0.97432622** |
| 1.2× | 0.57153372 | 0.98837239 |
| 1.4× | 0.56061627 | 1.03987456 |
| 1.6× | 0.54766519 | 1.11893645 |
| 2.0× | 0.51815796 | 1.34817320 |

Both metrics favour the **unchanged saddle** over this particular wider-saddle family under the shared fixed provisional camera. It is now unsafe to promote 1.4× to the canonical rig on the strength of the earlier single-source improvement. It remains **equally unsafe to declare the 1.0× saddle the authentic 1994 design**: all these scores compare the same experimental `upright` pose with the same short first-family source window, and authentic sprite-to-GLB pose assignment, physically verified 3D camera and withheld animation families are absent. This is an effective *negative control* on overfitting, not a final design verdict.

## Shared-camera scale sensitivity (still **unpaired**)

A second [eight-point controlled shared-camera scale sweep](../../analysis/data/racer-unpaired-pose-shared-camera-sensitivity-20261101.json) projected the **same exact five real GLBs** against the **same exact ten source alpha masks**, varying *only* the common vertical model-to-logical-pixel scale, holding world axes, camera origin, 7:6 source PAR, source P1:1205 bottom-alpha anchor and all 3D pose parameters fixed. At `9.5`, `bank` wins **10/10** silhouette IoU comparisons; at `9.3`, **upright wins 6/10** and bank 4/10. This ~2.1% camera-scale variation reverses six unpaired pose winner labels. Despite that, bank remains the highest **equal-source-shape mean** IoU at both scales: 0.50781314 at 9.5 versus upright 0.48114718; 0.49231925 at 9.3 versus upright 0.48747993. Maximum-pairwise pose identity is *not identifiable* from these sprites and camera hypothesis alone.

This is why geometry fitting must lock shared source-camera hypotheses and require real pose/cadence evidence; **no per-frame camera fitting to maximize IoU**. The eight scale samples were obtained on a local offline Trimesh/NumPy renderer of the hash-verified viewer GLBs; the new matrix tool's `--camera` flag can independently reproduce each specified hypothesis with a SHA-bound camera manifest. These are research sensitivity checks, not source-calibrated camera receipts or original 1994 pose measurements.

## Reproduce without contaminating the existing viewer

On an offline authoring host with optional \`numpy\`, \`trimesh\` and \`Pillow\` installed, unpack the real GLB viewer artifact into a **private** directory containing \`model-review/manifest.json\`, \`model-review/sprites.json\`, all five immutable GLBs and 14 retained source PNGs. Then from repository root:

```sh
python3 tools/art/build_real_viewer_pose_matrix.py \
  --model-review-dir /private/ur-artifacts/model-review \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  --registration-mode fixed-witness \
  --out /private/ur-artifacts/p1-1205-fixed-camera-5x10.json

# A separate source-exact anchor registration, no score-fitting or arbitrary
# recentering. Does not overwrite the previous report.
python3 tools/art/build_real_viewer_pose_matrix.py \
  --model-review-dir /private/ur-artifacts/model-review \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  --registration-mode source-registered \
  --out /private/ur-artifacts/source-registered-5x10.json

python3 -m unittest tests.unit.test_build_real_viewer_pose_matrix
```

The command first runs the **existing independent** \`audit_real_viewer_glbs.inspect_viewer\` authentication for all five GLBs and all 32 retained original frame references, rather than trusting a self-consistent viewer manifest. It then rechecks source RGBA and binary-alpha SHA against the original corpus. Each real GLB is projected **once** to the exact 4× source pixel-centre mask under one common camera; each distinct original binary shape is scored against all five. No source image or 3D mesh is saved, copied to a new public website, or auto-aligned to improve its result. The JSON prints to stdout unless \`--out\` points to a **new** report path: output uses the existing atomic no-replace report helper, so a foreign file/symlink cannot be overwritten.

The report contains model/ROM/camera SHA, original frame and source representation provenance, source binary mask SHA group membership, full image comparisons (IoU, XOR, 7:6 Chamfer, bottom-alpha row), equal-source-shape mean score, and explicit false source-pose, held-out source family and art-approval flags. Synthetic matrix tests run in dependency-free CI, with optional offline real-image/GLB exercises when dependencies are installed.

**Next useful step:** recover additional authentic original pose families with the private ROM composer, freeze shape-disjoint fit versus withheld candidates using \`freeze_racer_source_family_splits.py\`, then solve one physically consistent camera/pose/geometry hypothesis against *source-authenticated correspondences*. Consider temporal pedal phases and saddle articulation from original sequence evidence rather than forcing each sprite into one of five 2026 blockout names. Only once that mapping is defensible should the other viewer agent add an optional read-only measured-score sidecar to its **existing** Pages interface. Source camera and owner likeness acceptance remain separate hard gates.
