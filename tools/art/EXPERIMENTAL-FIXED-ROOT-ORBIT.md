# ART-4K: one existing five-parent GLB with a third, fixed whole-character orientation control

**Engineering experiment only.** This extends the existing 2026 unapproved 16-material, five-parent GLB and [PR #3101](https://github.com/gamesbyian/UR-Recomp/pull/3101)'s two independent, axle-based controls. There is **no new mesh**, alternate rig, procedural sprite upscaler, PPU producer or replacement gameplay artwork.

## Why this control is now worth testing

The original ROM's authenticated **24-phase × 64-orientation** 2D presentation table was recovered on #3104. Source-only #3113 measures a near-circular orbit of the region whose 4bpp pixels change with phase as original orientation varies; #3114's exact original-ROM test on 32 internally separated orientations finds a fixed **2D rigid-rotation explanation** with **0.87361809 pooled support IoU**, outperforming an unrotated source region simply translated along the orbital path (**0.84426838**). This is strong 2D evidence for a coherent source-image orientation transform, but not a recovered historical 3D camera, joint axis or mesh.

The previous #3101 wheel/crank and fork/saddle pitch controls *only rotate separate parent groups about the wheel axle*. They cannot express an **entire unicycle spinning around a mid-body centre**. The historical 2026 original OpenSCAD author already supplied a whole-character spin pivot at world **Z=1.80**, while its wheel axle is world **Z=1.00**, in source SHA-256 `e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984`. The #3113 provisional-camera backprojection estimates the original source orbit centre near world Z=1.938 and, under only that provisional view, the historical midbody pivot is 2.66 display-corrected source pixels away versus 9.21 for the historical axle. This is a **conditional retrospective comparison of 2026 art hypotheses**, not historical source geometry.

## Implementation

`tools/art/experimental_fixed_root_orbit.py` operates on the **one existing SHA-verified 2026 upright GLB**, no additional OpenSCAD creation. It composes three interpretable controls:

1. Existing shared direct-drive **wheel/rim/pedals** rotation about their authentic 2026 GLB axle.
2. Existing **fork/frame+saddle** pitch about that same axle.
3. A whole-character **source-world Y orientation hypothesis**, applied to **all five parent matrices together**, around exactly one of two **pre-existing** pivot choices: `wheel_axle`, or `historical_midbody` 0.8 model units above that axle in world Z.

The input is an integer original-ROM orientation index 0..63. For this *test only*, its corresponding whole-model root rotation is assumed `2π×index/64`. This is explicitly an **uncalibrated 2026 rendering hypothesis**, not a measured 1994 physical angular step or newly identified camera. No per-frame change to the pivot, scale, camera, source pixel registration, geometry or material colours is allowed. If the source-generated 2D pixels cannot be predicted at the full index/alpha/occlusion level, the hypothesis fails.

This code reuses #3101's **exact original rest-matrix and source-graph integrity controls**, applying global rotation after its independent axle controls. The previous model scene's identical five parent names and sixteen material meshes are preserved, including the actual intermediate `world_1` parent used by the source GLB exporter. Repeated A→B→neutral selections restore exact original parent matrices without drift, and external mutation triggers the existing fail-closed state check. A derived optional GLB can be serialized/reimported without modifying the original part-local vertices/faces, and output/receipt publication remains exclusive/no-overwrite.

```sh
python3 -m unittest tests.unit.test_experimental_fixed_root_orbit
python3 -m tools.art.experimental_fixed_root_orbit \
  --source-glb /verified/actual/2026-upright.glb \
  --source-orientation-index 16 \
  --pivot-mode historical_midbody \
  --wheel-crank-delta-deg 25 --frame-pitch-deg 10 \
  --out-glb /new/experimental-orientation-16.glb \
  --receipt /new/experimental-orientation-16.json
```

The generated candidate is **unapproved 2026 art**. Neither the ROM's index values nor the source 7:6 camera have yet been calibrated to physical 3D degrees. A potential model index grid is a useful way to test common poses, not a proof that the entire historic sprite family was made by this control.

## Next source-to-3D falsifiable test

Reuse the #3104 complete exact original ROM frame index planes, #3113/#3114 frozen 2D source-orbit/rigidity controls, the one #3101 real GLB and the provisional 7:6 source camera. For several predeclared orientations spanning the complete range, apply each of the two fixed source root pivots plus a **single shared phase law**. Score full source 64×64 alpha, source 4bpp interior changes, material visibility and wheel/fork/saddle landmark residuals. Compare against the **2D rigid-rotation baseline** and the unchanged GLB. No per-image best-of-root/pivot/phase/geometry/camera selection. Use the original source OAM-local orientation first; source red completed-screen reflection remains a separate established screen transform.

If the 2026 whole-model rotation loses to the cheap 2D explanation, preserve this negative result and revisit shared camera/identity and internal authored detail, rather than forcing the model to fit each source frame. The original game’s authoring mesh, camera, skeletal joints and owner likeness approval remain unverified. This is not a Windows release gate. Independent source review and exact-head unit/real-GLB export/browser acceptance are needed before integrating this control.
