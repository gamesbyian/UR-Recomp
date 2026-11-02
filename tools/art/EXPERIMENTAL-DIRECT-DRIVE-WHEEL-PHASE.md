# ART-4K: source-locked direct-drive wheel/crank phase experiment

**Technical 2026 blockout study only, not approved Uniracers shipping art.** The existing original #2832 OpenSCAD five-part shared unicycle rig uses authored pedal phases 18, 88, 44, 120 and 150 degrees for upright, pedal, wheelie, stunt and bank respectively. Its unchanged eight-spoke rim remains in one local orientation across the five separately exported GLBs. A direct-drive unicycle should rotate the spokes with the cranks, without rotating the fork or saddle.

The optional offline script experimental_direct_drive_phase.py accepts only exact SHA-pinned five GLBs from the prior real-model-review workflow #41259476190. It applies a local source-wheel rotation of minus (pedal phase minus 18 degrees) around the *actual posed* wheel axle, using a rigid matrix conjugation. A tilted wheelie or bank therefore spins about its own wheel axle, not world Y. The source pedal meshes already contain the correct baked pedal phase and remain unchanged. Only tire and rim-and-hub parent transforms change; the existing five parent part identities, sixteen material child meshes, and all vertex/face buffers are verified after actual GLB round-trip. No new canonical OpenSCAD source, renderer, viewer, runtime asset or original sprites are created.

    python3 tools/art/experimental_direct_drive_phase.py --pose pedal \
      --source-glb /private/pedal-f692277bb9bf215c.glb \
      --out-glb /private/new/pedal-synced.glb \
      --receipt /private/new/pedal-synced.json

The output and receipt are write-once. Receipt last is the sole success signal. On a collision, leave an unreceipted orphan rather than risk deleting a concurrent writer's data. Use numpy==2.3.5 and trimesh==4.11.1 for optional 3D tests and generation. Run:

    python3 -m unittest tests.unit.test_art4k_experimental_direct_drive_phase

Five actual source-locked GLBs were generated and verified locally. Derived binary SHA-256 hashes using that original pinned source and those package versions:

| Pose | Relative wheel phase | Derived real GLB SHA-256 |
|---|---:|---|
| upright | 0° | 2109f47fe0d21d15af15fd3fa8f483b4e037b296df0eb6d67a70b7a9f6662f8d |
| pedal | +70° | 7aede90f6d4f0be9aec6466444f910c7549b2dd9bed867f41a03e80131970549 |
| wheelie | +26° | 1b57f9668a83d450619f6fbc8b78c3c1564f4d8fef2083a50eb86bbda4a339ec |
| stunt | +102° | d9c698b5e41a915c046b82e0208a40b76aa4c106aea6cd25ccf1ba3e99e3b2d1 |
| bank | +132° | 4d682d4a74e93e56bfa6ad22190909643872296f077e13f15ad8fc225c1333b0 |

For any future canonical change in the one #2832 source rig, both the SCAD whole-assembly wheel transform AND the independent GLB exporter wheel parent transform must match. Changing only one produces a new source-vs-GLB discrepancy and invalidates old source receipt hashes. Separate historical fork-mass/continuous-motion source hashes must remain explicitly versioned.

This does **not** measure or recover the 1994 original wheel rotation, joint constraints, camera, physics, silhouette pose registration, emulator PPU frame cadence, or character likeness. The merged #3026 validator remains only a consistency/provenance gate until an independent live emulator trace is produced. No art-acceptance, Windows release or shipping status follows.
