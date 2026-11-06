# Why two authenticated original printed saddle outlines do not uniquely recover 1994 saddle geometry

This is a **real 3D computation on one actual, unchanged 2026 source GLB**, paired with the two exact-source-PDF-verified 1994 official manual saddle image-plane measurements merged in #3176. It is a *negative identifiability control* for the next physical reconstruction decision, not a calibrated print-to-3D fit or original-art approval.

**Source identities:** Retained 1994 USA manual PDF SHA256 `50d5d02a3f8f04b9a38a1dac7ff05fd96f5583fbdf1d0afc201bbaea454e2235`, actual p14 crop SHA `cfbbc7b3e3cd1e3786897eba580bffec2ee9ceec268bcf4cdb4b5b6e30f4642b`, p15 SHA `4c9242a0126891a2d6a6e8f574eec4179c4cdbcd30cb34a1cdff8589e9290d22`, and the **actual published 2026 source upright GLB** SHA `634aa0280ec1a8a322c34d1598680e854980f317965b3a848a2cf6b240c50c08` (639,132 bytes), from the full original-source real-model Pages Windows Visual Atlas export [#42138925131](https://github.com/gamesbyian/UR-Recomp/actions/runs/42138925131). This SHA is for the *published Pages source upright GLB*; it is distinct from the separate 2026 source research blob SHA `d83a39b...` used in the original experimental spoke-volume direct audit. Both describe 2026 exports and neither proves a 1994 production mesh.

The original manual printed page 14 near-front saddle has approximate **154×66 px** source-crop image-plane bounds (±8 px per point). The large page-15 underside/oblique saddle shows about **318×273 px** (±14 px per point). These are GPT-6 visually estimated 2D edges, not independently checked artist placements, and neither includes a complete wheel for scale normalization. Original print poses, lens, zoom and composition may also differ from the 1994 gameplay sprites.

## Controlled projection against one existing 3D saddle

The actual GLB has two original saddle material meshes with **1,393 + 1,315 = 2,708** vertices. Without sculpting the model or inventing original production cameras, `tools/art/audit_print_saddle_camera_identifiability.py` enumerates one fixed orthographic **2026 model-only** camera grid: yaw 0°..180° in 5° steps (37 points), elevation −70°..70° in 5° steps (29 points), **1,073 views**. Each view computes a simple image-plane bounding width/height from **all unchanged source saddle vertices**, without a z-buffer or full-source silhouette segmentation. It deliberately does not fit camera distance, location, print foreshortening, wheel geometry, source sprite 2D alpha or 1994 original production lighting.

Conservatively propagate each independently estimated visual extreme's uncertainty as width ±2u, height ±2u. This yields a source **ratio interval** rather than pretending a measured 3D proportion.

| Exact verified original print view | 2D width:height nominal | Permissible ratio interval | 2026 model-only orbits within that interval |
|---|---:|---:|---:|
| p14 near-front | 2.3333 | 1.6829–3.4000 | **508 / 1,073** |
| p15 low oblique | 1.1648 | 0.9635–1.4122 | **188 / 1,073** |

The *same unchanged 2026 saddle* can generate ratios near either original printed observation under different uncalibrated views, resulting in **508 × 188 = 95,504 possible independently chosen camera pairs** on this intentionally coarse grid. Its full model-only vertex-envelope ratio spans approximately **0.3579–3.1965**. As examples of numerical closeness, p14 has a 2026 model orbit at yaw20° / elevation−35° with projected ratio ~2.3174; p15 has yaw140° / elevation−70° with projected ratio ~1.1671. Those orientations are selected **purely as an existence diagnostic** and must never be described as the historical original 1994 artist's camera or actual pose.

These are **not 95,504 physically compatible original 3D character reconstructions**. It is a count of camera-pair degeneracy in one particular source-model and generous 2D measurement uncertainty exercise. Since each original print image was composed separately, one image's camera does not fix the other's. Aspect-ratio agreement here is weak evidence of shape correctness.

## Consequence for the next physical sculpt

Do **not** change the 2026 saddle geometry merely to match these two print-bounds aspect ratios; that would trade one unconstrained physical parameter for an unmeasured camera. Preserve the earlier negative/mixed saddle contour sweeps, exact-original-game 23-edge motion metric, owner likeness veto and absence of release ART approval. The next physical-art evidence should locate **source-identifiable multi-part joints/surface topology**: saddle mounting/clamp, two-sided fork/crown continuation, hub/counterweight and crank attachment, with genuinely visible original print points and occlusion, before evaluating one bounded mesh variation. A camera or part assignment would require additional source-grounded landmark correspondences and independently checked render geometry.

### Reproduce

Obtain the **exact 2026 upright GLB** SHA from the existing real Pages source-model artifact and the **already merged original printed 2D report** in `analysis/data/racer-original-manual-saddle-2d-pdf-verified-20261105.json`:

```sh
python3 -m tools.art.audit_print_saddle_camera_identifiability \
  --upright-glb /private/upright-634aa0280ec1a8a3.glb \
  --source-print-report analysis/data/racer-original-manual-saddle-2d-pdf-verified-20261105.json \
  --out /private/new/print-saddle-orbit-ambiguity.json
```

The full numeric source receipt is held in `analysis/data/racer-original-manual-saddle-camera-ambiguity-20261105.json`. Optional NumPy/Trimesh are needed to recompute real 2026 model geometry; normal stdlib unit tests pin source hashes, printed 2D restrictions, the existing numeric report, and false original art/camera/release approvals. Provide env `UR_ART4K_AUTHORED_UPRIGHT_GLB=/private/upright-634aa0280ec1a8a3.glb` to have the test independently compare the true source GLB geometry result. No new runner, 1994 original ROM, default model, Pages control or game asset is involved.
