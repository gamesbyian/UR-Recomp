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

## Reproduce without contaminating the existing viewer

On an offline authoring host with optional \`numpy\`, \`trimesh\` and \`Pillow\` installed, unpack the real GLB viewer artifact into a **private** directory containing \`model-review/manifest.json\`, \`model-review/sprites.json\`, all five immutable GLBs and 14 retained source PNGs. Then from repository root:

```sh
python3 tools/art/build_real_viewer_pose_matrix.py \
  --model-review-dir /private/ur-artifacts/model-review \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  --out /private/ur-artifacts/p1-1205-fixed-camera-5x10.json

python3 -m unittest tests.unit.test_build_real_viewer_pose_matrix
```

The command first runs the **existing independent** \`audit_real_viewer_glbs.inspect_viewer\` authentication for all five GLBs and all 32 retained original frame references, rather than trusting a self-consistent viewer manifest. It then rechecks source RGBA and binary-alpha SHA against the original corpus. Each real GLB is projected **once** to the exact 4× source pixel-centre mask under one common camera; each distinct original binary shape is scored against all five. No source image or 3D mesh is saved, copied to a new public website, or auto-aligned to improve its result. The JSON prints to stdout unless \`--out\` points to a **new** report path: output uses the existing atomic no-replace report helper, so a foreign file/symlink cannot be overwritten.

The report contains model/ROM/camera SHA, original frame and source representation provenance, source binary mask SHA group membership, full image comparisons (IoU, XOR, 7:6 Chamfer, bottom-alpha row), equal-source-shape mean score, and explicit false source-pose, held-out source family and art-approval flags. Synthetic matrix tests run in dependency-free CI, with optional offline real-image/GLB exercises when dependencies are installed.

**Next useful step:** recover additional authentic original pose families with the private ROM composer, freeze shape-disjoint fit versus withheld candidates using \`freeze_racer_source_family_splits.py\`, then solve one physically consistent camera/pose/geometry hypothesis against *source-authenticated correspondences*. Consider temporal pedal phases and saddle articulation from original sequence evidence rather than forcing each sprite into one of five 2026 blockout names. Only once that mapping is defensible should the other viewer agent add an optional read-only measured-score sidecar to its **existing** Pages interface. Source camera and owner likeness acceptance remain separate hard gates.
