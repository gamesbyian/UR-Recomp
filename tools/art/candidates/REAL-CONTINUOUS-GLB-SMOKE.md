# ART-4K real continuous OpenSCAD-to-GLB acceptance

**Scope:** verify the *already-authored* continuous movement in the one experimental five-part #2832 rig. This is the existing source, not a replacement model, original 1994 animation reconstruction or approved artwork.

The draft OpenSCAD source implements `continuous_rig(time, spin=false)`, `rig_pose="ride"` and `rig_pose="stunt_cycle"`. The same exporter implements source-bound `--rig-pose` and `--rig-time`, with a fail-closed `continuous_pose_recipe` parser rather than a guessed 1994 cadence. This PR adds only a real-asset qualification producer and an **independent verification of exported bytes and immutable status receipts**. No source mesh, geometry, pivot, part material, viewer, or product feature is changed.

## Real sample matrix

The path-filtered workflow `.github/workflows/art4k-real-continuous-glb-smoke.yml` runs two bounded hosted Ubuntu CPU samples against the same draft OpenSCAD source: **ride at 0.25** and **stunt_cycle at 0.5**. Different normalized times are intentional non-1994 research witnesses, not a synchronized animation frame sequence. Each job exports the actual five-part material-separated GLB through the one `export_articulated_unicycle.py` authoring path, without bypassing the existing uncolored-geometry probe, watertight checks or glTF round-trip guard. Each exports to a fresh directory, then runs:

    python3 tools/art/verify_art4k_real_continuous_glb.py --source tools/art/candidates/unicycle_shared_rig.scad --output-dir /tmp/one-real-attempt --pose ride --time 0.25 --receipt /tmp/unused-qualified.json

The verifier independently reads the existing `last_attempt` and `current` receipt pointers; verifies the same successful unique attempt and source SHA, prevents path escape, hashes the real GLB and complete immutable receipt bytes, and refuses stale success or modified originals. It recalculates the pedal phase (including unwrapped turns), saddle lean, authored pitch/bank/wobble and full 4×4 world transform from the actual OpenSCAD source formula. It verifies both the receipt and the **real source GLB round-trip** again, including five parent pivots and all 16 material child meshes, and compares the independently reconstructed result with the producer receipt. The evidence explicitly marks 1994 camera, cadence, sprite pose pairing, likeness and shipping approval as false. Output is published only when complete and never overwrites an earlier qualified file.

## Reproduce and acceptance

    python3 -m unittest tests.unit.test_verify_art4k_real_continuous_glb

Synthetic stdlib regression tests cover positive source recipe samples, invalid normalized time, swapped original 1994 approval, forged controls/transform, stale or failed pointer, changed source GLB and path escape. They use a patched GLB round-trip only to exercise receipt logic cheaply. **The real hosted job runs the genuine Trimesh and OpenSCAD asset checks, not a stub.**

The workflow uses a fixed two-sample matrix, 35-minute maximum per job, no schedule, and uploads two distinct 14-day **real GLB + receipts + source-bound qualified proof** research artifacts. The published results, not mere script existence, determine whether continuous source-to-GLB integration works. A failed task must be diagnosed from the named job; do not count a draft-syntax-only test as real model acceptance.

Next model study: use the actual original 1994 ROM temporal transition ledger (1205–1220, 1230–1239, 1244–1252 and 1261–1267) and the merged original 2D chroma-axis/source-contact witness to evaluate the *new real GLB sample projections* with a stable provisional camera. The actual source original game-to-2026 rig time mapping is **unknown**. A single 2026 authored normalized time must not be assigned to an original ROM frame without new evidence. Do not vertex-morph the original five separately triangulated static GLBs; #2985 measured changing mesh topology, so parameterized authoring is the intended route.

The final result does not approve #2832 likeness or promote its geometry to game rendering. The Windows executable, native gameplay/release gates and existing one Pages viewer are untouched.
