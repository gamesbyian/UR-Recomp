# ART-4K actual five-GLB topology audit and animation strategy

**Status: original 2026 experimental GLB verification, not original 1994 3D reconstruction or author-approved likeness.** This is a structural constraint on how the *same* part-addressable model should be animated, preserving the one draft #2832 OpenSCAD source and the single Pages model reviewer.

## Actual 2026 source-owned five-pose evidence

The real five static GLBs from Actions run #41259476190 / artifact #13063969312 share exactly **five parent part groups** and **16 named child material meshes** (two tire, five rim/hub, four fork/frame, three pedals, two saddle). Their material/node names and source export provenance are stable, but baked local meshes are NOT all identical across exported named poses.

Local read-only verification with Trimesh 4.11.1 `process=False`, comparing upright versus pedal/wheelie/stunt/bank, found:

| Mechanical condition across all five exported GLBs | Material meshes (of 16) |
| --- | ---: |
| Same vertex counts | 15 |
| Identical local vertex coordinates | 9 |
| Identical triangle-face indices/order | 10 |
| Identical world transforms | 0 |

The six changing triangle topologies are saddle material 0/1, pedals material 0/1, painted fork/frame material 0 and rim/hub material 2. **Pedals material 0 changes vertex count.** Pedals material 2 changes local vertex positions even where its faces remain identical. The tire local meshes stay identical, but their scene/world transforms change in wheelie/stunt/bank. These are five independently baked **static pose studies**, not evidence of a stable skinned/morphable mesh with registered vertex identities or original source animation pivots.

**Practical consequence:** do not simply morph or linearly interpolate the five GLB vertex/index buffers to produce continuous original racer animation. Incorrect vertex correspondence and changing topology can cause arbitrarily crossed or disconnected triangles. Even matching vertex counts and face indices cannot independently prove physical vertex semantic correspondence. Prefer extracting explicit pivot/pose **parameters from the one canonical #2832 authoring source** and regenerating or evaluating a stable articulated model; alternatively build a separate audited topologically stable rig as a deliberate source upgrade, not a naive blend of five files.

## Reproduce

Use the exact historical five-pose GLBs at `real-model-site/model-review/assets/d061cddcdbac9b2b5ac137d0d721b63f92dc3ec1/` and run:

    python3 tools/art/audit_art4k_real_pose_topology.py --model-review-dir /verified/real-model-site/model-review
    python3 tools/art/audit_art4k_real_pose_topology.py --model-review-dir /verified/real-model-site/model-review --out /private/new/immutable-topology-audit.json
    python3 -m unittest tests.unit.test_audit_art4k_real_pose_topology

This optional original-source-SHA-pinned checker uses NumPy and Trimesh for actual GLB reads, and its synthetic regression cases use only Python stdlib. It examines imported vertices, face indices and exact named node world transforms without altering source GLB or rig files. For actual original-model art review, preserve the independent original ROM pose angle analysis and original player animation frame transition ledger.

The actual five-GLB measured summary and input SHA identities are at [analysis/data/racer-art4k-five-pose-actual-topology-audit-20261101.json](../../analysis/data/racer-art4k-five-pose-actual-topology-audit-20261101.json). Source ownership, original 3D pose/camera recovery, the artist's likeness judgment and shipping gates remain separate; all are unapproved.
