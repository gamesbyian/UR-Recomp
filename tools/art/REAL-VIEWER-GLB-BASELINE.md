# Measured REAL model-review GLBs against original sprite: first independent cross-lane baseline

**2026-11-01. Status: source-hash verified, unapproved, one provisional camera; explicitly no authenticated sprite→3D pose correspondence.** Machine-readable data: [racer-inverse-real-viewer-glb-baseline-20261101.json](../../analysis/data/racer-inverse-real-viewer-glb-baseline-20261101.json).

## Why this matters

The previous [P1 source-fitting pilot](../../analysis/data/racer-inverse-first-source-pilot-20261031.json) exported the five part modules of the same source OpenSCAD file through a *simplified* temporary GLB assembly. Meanwhile the other agent delivered the real Pages [model viewer #2938](https://github.com/gamesbyian/UR-Recomp/pull/2938), with a SHA-verified bundle from the **existing unapproved #2832 material-separated exporter**. To close that provenance gap, this audit downloaded and opened the **actual real-five-pose viewer artifact**:

- [Actions run #41259476190](https://github.com/gamesbyian/UR-Recomp/actions/runs/41259476190), artifact **13063969312**, \`ur-experimental-model-review-actual-glbs\`, original ZIP SHA-256 \`1088445987fd11fb5c6f0c66d8ca3db6712a6e239df6273bfa892c899dcf6fd1\` (GitHub listed expiry **2026-11-15 01:06 UTC**; don't depend on perpetual artifact availability).
- Model source commit \`d061cddcdbac9b2b5ac137d0d721b63f92dc3ec1\`, source SCAD SHA-256 \`e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984\`.
- **All five** distinct GLB file bytes match their exact model-review manifest digests. Each imports in Trimesh, with **5 parent parts**, **16 material-separated geometric meshes**, 22 scene-graph nodes and ~28,820–28,860 triangles. No missing geometry or non-finite world bounds was observed in this bundle.
- **All 32 original P1/P2 source-rail frame records** match their actual staged PNG hashes. The rail contains 14 PNG filenames, 10 decoded RGBA images and **10 distinct exact 64x64 binary silhouettes** (6 P1, 4 P2), consistent with the first source-corpus work. This is not 10 independently observed 3D camera views.

## First real comparison, with an honest caveat

The real GLBs were projected from original OpenSCAD **Z-up** through the *same deliberately unfitted* side orthographic camera as the preceding P1 frame1205 single-source pilot: world right [+X], up [+Z], vertical scale **9.5 source logical pixels per model unit**, 7:6 original pixel aspect, registered P1 1205 lowest-alpha midpoint [67,76] in half-pixel units; no mesh auto-center or crop. Output was binary 256x256 RGBA, sampled at \`4*x+2, 4*y+2\` to compare exact original source logical alpha.

| Actual published #2832 model pose | Test vs original P1 frame1205 mask IoU | Mean 7:6 boundary Chamfer (physical px) |
| --- | ---: | ---: |
| Upright | **0.58288770** | 0.92199627 |
| Pedal | 0.58400000 | 0.92959100 |
| Wheelie | 0.23760331 | 2.35132607 |
| Stunt | 0.16500994 | 3.62963076 |
| Bank | 0.60540541 | 0.88338010 |

**Only upright serves as the deliberately manually selected P1 source baseline.** Every other comparison puts a *different experimental source-2026 model pose against the **same** original P1 frame1205*, without proving it represents that original sprite pose. The bank score therefore does **not** show bank is "more authentic" or that a real source-to-rig mapping was recovered. It is a projection/coverage diagnostic for multiple model files under one fixed camera.

The real upright GLB gives **exactly 0.58288770** IoU, source 325 opaque vs candidate 267 opaque logical pixels, and 156 XOR mask pixels: the **same pixel-level score as the earlier locally reassembled five-part SCAD module pilot**. That is a valuable cross-check that the simplified earlier mesh was measuring the intended source geometry. It is not a visual-likeness verdict or proof of correct camera or mechanics.

## Re-run on future viewer output without rebuilding the game

The added \`tools/art/audit_real_viewer_glbs.py\` consumes an already-staged model-review site folder with original \`manifest.json\`, \`sprites.json\`, original sprite PNGs and five real source-model GLBs. It verifies the existing viewer's hashes and experimental/unapproved source-pose flags; loads the GLB parent hierarchy and real mesh geometry with optional Trimesh, NumPy and Pillow; generates a temporary 256×256 alpha silhouette for each pose, then **recomputes the existing source-registered P1 frame1205 score**. It prints a research-only JSON audit. It never edits or publishes the site.

```sh
# Obtain the exact ZIP from the verified Actions artifact (no direct HTTP
# media URL is assumed stable), safely extract it to a private directory.
# The download's extracted site has:
# real-model-site/model-review/{manifest.json,sprites.json,sprites/,assets/}
python3 tools/art/audit_real_viewer_glbs.py \
  --model-review-dir /private/ur-viewer-artifact/real-model-site/model-review \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  > /private/ur-viewer-artifact/audit.json

python3 -m unittest tests.unit.test_audit_real_viewer_glbs
```

The auditor imports existing \`render_racer_glb_projection.py\`, \`score_racer_candidate.py\`, and the bounded source PNG decoder. It does **not** create another rig, another viewer, another Pages pipeline, or a local authoritative model export. Each model file is authenticated against the viewer manifest, and the original source frame is independently rechecked against the repo's original-stock PNG corpus. If a new viewer artifact changes model shape, pose, source or camera, run the same audit and compare the new digest-bound results.

## Next actual art tasks, not relabelling this pilot

1. Extend *source* evidence to different actual registered original pose families through the **private** [ROM corpus exporter](ORIGINAL-RACER-CORPUS-EXPORT.md) where a canonical ROM is legally held; declare disjoint temporal/shape held-out partitions before fitting.
2. Fit **one shared 3D geometry/camera hypothesis** across multiple originals and consistent verified source-pose controls. The experimental named OpenSCAD poses alone do not establish those controls.
3. Use the **existing Pages viewer** from #2938 for owner inspection, eventually feeding it a read-only measured comparison sidecar with SHA identity, uncertainty and exact source-frame provenance. Coordinate that UI change with the other viewer agent. No new website or automatic source-pose claim.
4. Keep original 1994 source-character likeness approval and game-ready asset integration separate. No ART-4K acceptance or shipping credit from this study.

**No original copyrighted PNG, ROM, source-derived GLB binary or customer-provided secret was committed here.** The data report contains hashes, source identity, camera assumptions and scores only.
