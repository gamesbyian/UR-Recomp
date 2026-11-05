# Original-screen fixed 2D model-reflection control, 2026-11-03

**Decision:** Is the existing five-GLB / provisional-camera comparison sensitive to a **single predeclared player-handedness convention** without fitting new geometry, poses, per-image flips, camera parameters, or making another original-emulator/GLB run?

Use the three exact SHA-1 Git-blob-pinned source receipts from merged #3091 and #3096. The existing #3097 painted-axis sensitivity already established the rationale for trying a fixed red model projection reflection. The new ROM-free calculation reuses the complete original-screen orientation of blue and red, the old held-source five-GLB IoUs and the 11 original-content-connected groups. Every existing source 2D registration retains the original ZIP SHA-256, original ROM identity, GLB source hashes, fixed camera, and fit/withheld ancestry.

## Why the held-source score is an exact reflected-model 2D control

For any 64×64 binary source silhouette S and *already source-anchor-registered* experimental GLB projection M, let R reverse the 64 columns in every row. Pixelwise intersection and union are preserved by the same bijection, so **IoU(R(S), R(M)) = IoU(S,M)**, including at a source half-pixel anchor that reflects from x2 to 126−x2. The original emulator independently authenticated the red displayed source as R(S) and blue as S. Thus the existing held-red scores against M equal the **completed-screen red scores against the fixed mirrored *registered 2D model projection* R(M)**. Blue scores stay identical. The alternative arm uses the original completed-screen red scores against unmirrored M. There is no per-source reflection selection: all red uses R(M) in the proposed arm.

This is a valid **post-registration 2D projection reflection** control, not a 3D camera solution, true model handedness, original game bones or a newly rendered mirrored GLB. In particular, it does not prove that a pre-raster 3D geometry reflection has precisely identical clipping and sampling in the existing provisional renderer.

## Observed exact-receipt results

| Descriptive optimistic best-of-five score | Shared unreflected projection | Fixed red registered-model reflection |
|---|---:|---:|
| Blue original 20 frames, mean best IoU | 0.47986515 | 0.47986515 |
| Red original 20 frames, mean best IoU | 0.46554101 | 0.48769263 |
| All 40 frames, mean best IoU | 0.47270308 | 0.48377889 |
| 11 content groups across 38 **unclassified** original examples, one equal vote/group | 0.49148426 | 0.50544332 |

Among the 11 content groups, **six improve, one worsens and four are unchanged**. The historical one fit and one withheld source are kept as independent provenance roles, not silently folded into the 11 groups. The 38 novel examples and all 11 groups are already inspected diagnostics, **not new prospective blind holdouts**. Per-image best-of-five IoU is an optimistic upper bound, not a continuous-rig fit or source-authenticated original pose label. This control neither establishes a statistically independent generalization claim nor changes the canonical rig in draft #2832.

## Minimal reproduction and next discriminator

From the repository root, with standard-library Python only:

    python3 -m unittest tests.unit.test_evaluate_original_mesen_live_reflection_control
    python3 -m tools.art.evaluate_original_mesen_live_reflection_control --out /private/ur-art4k-reflection-control.json

The optional output is immutable/no-overwrite via the existing helper; without --out, the tool prints JSON. The test validates full original dataset census/roles, source/GLB/camera bindings, exact scores and source-tile families, plus a synthetic mask/half-pixel-anchor reflection identity. No new workflow or heavy CI.

**Next:** Keep the model camera and original source identities fixed, test physically coherent rig phases and repeated source-observed chronological neighbors under a shared pose trajectory. Require an actual real-GLB-pixel render/anchor test before calling the reflected 2D projection a validated 3D mirrored camera arm. Compare source landmark, colour, boundary and temporal residuals by player and source family; do not infer wheel/joint motion or release ART-4K from the improved upper-bound IoU. If a real rig cannot explain source motion coherently, record a negative result and seek discriminating input before geometry fitting.

No owner likeness approval, Windows release gate, original 1994 3D geometry/camera or shipped artwork is claimed.
