# ART-4K single-source continuous axle/frame pose control (experimental)

**One GLB, two interpretable mechanical controls.** This is a *new in-memory pose operator* for the existing 2026 unapproved five-parent, sixteen-material rig in draft [#2832](https://github.com/gamesbyian/UR-Recomp/pull/2832). It does not author another model or change the game's presentation, release art or source-camera estimate.

Prior experiments rotate fork+saddle about the axle and separately fix stationary rim/spoke rotation relative to an already baked pose's pedals. This combined control starts from the **one immutable upright GLB** (SHA-256 \`efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5\`) and enforces two shared, continuous transforms:

- **Wheel/crank delta (±360°)** rotates tire, rim/hub *and pedals together* about the same source-authored axle. This preserves direct-drive synchronization; upright's authored crank reference is 18°.
- **Frame pitch (±45°)** rotates fork/frame and saddle together about the same axle while preserving their preexisting relative orientation.

Both commands act on the original *part-parent transforms* with the axle-conjugated rigid transform, preserving all 16 material-separated, part-local meshes and source name hierarchy. No new CSG triangulation, per-pose geometry substitution, dedicated GLB fork or player-specific fitted mesh is introduced. The two axes are currently both the axle axis; they are identifiable only if source evidence distinguishes wheel/spoke/crank motion from relative fork/saddle tilt. Source 2D painted axes alone cannot certify those 3D mechanisms. **Repeated in-memory samples are absolute:** the first invocation caches the original five parent matrices in the scene (not the exported GLB), and later calls always transform from that same rest pose. A→B→neutral must restore the original matrices; unexpected external edits to the controlled nodes fail closed rather than accumulating rotations.

## Reuse and validation

The ROM-free tests validate bounded finite parameters, sign conventions, full-turn closure and invalid-source rejection. With NumPy/Trimesh they exercise both a direct-parent synthetic 16-mesh rig and a rotated/translated intermediate-parent (`world_1`) export hierarchy, including absolute A→B→neutral recovery. The real GLB exporter actually inserts `world_1` between `world` and all five sibling part nodes; initial source code assumed direct `world` parenting and failed before generating geometry. The corrected operator preserves either supported hierarchy and converts world target matrices into the original common parent's coordinate space, while rejecting split/deeply nested, nonrigid or mutated hierarchies. Its optional real artifact path checks exact source GLB SHA, unchanged local mesh buffers, 16 material children, and actual GLB export/reimport parent matrices. No new agent, viewer, CI workflow or source emulation.

    python3 -m unittest tests.unit.test_experimental_continuous_five_parent_pose

For explicit owner review using the already-authenticated viewer GLB artifact #13063969312:

    python3 -m tools.art.experimental_continuous_five_parent_pose \
      --source-glb /private/verified/upright.glb \
      --wheel-crank-delta-deg 25 --frame-pitch-deg 10 \
      --out-glb /private/new/phase25-pitch10.glb \
      --receipt /private/new/phase25-pitch10.json

The generated GLB and receipt are exclusive/no-overwrite. On the owner's HP, the actual original artifact #13063969312 was downloaded on 2026-11-03; all five authentic GLB SHA-256 digests matched the original immutable receipts. Python 3.12 with NumPy/Trimesh, using the exact authentic upright input (`efdc8425...595f5`), successfully exported and reimported the **+25° drive / +10° frame** candidate after correcting the intermediate-parent bug: **640,192 bytes, SHA-256 `dc89cf429ec137316887debca58b59e8a3e7fab57d877a43d0aa992587ca3f49`**, with 16 local meshes and five part-parent transforms preserved. The initial implementation had failed with `ValueError: source part parents have changed` on the identical GLB. The HP run is a real **2026 model** mechanical exporter qualification; no original 1994 source-pose registration was attempted. The continuous operator can also act in memory without exporting a GLB for every candidate.

**Existing direct-drive helper repair:** the reused `experimental_direct_drive_phase` constant had an incomplete wheelie GLB SHA and its rotation assumed direct `world` parenting. The actual wheelie file from artifact #13063969312 matches SHA-256 `859b985d8fc51f994e5e42fd64bc871d493249285454ec836b415ec833f33c27`; the incorrect constant failed before reading that legitimate model. Correct the constant and retain the actual `world -> world_1 -> five parts` hierarchy through parent-local transform conversion. The revised historical direct-drive helper was executed against **all five** original SHA-verified GLBs on the HP, with five actual export/reimport checks preserving the local meshes and materials. It is still a static-2026-source mechanical test, never a 1994 source motion registration. Focused tests cover digest completeness, the exported intermediate-parent structure and source geometry integrity.

## Next falsifiable source-registration experiment

First use genuine **adjacent** source frames from the original P1/P2 1205–1220 witness (30 consecutive player edges, 21 silhouette holds and 9 changes). The 20 later live Mesen ticks 1601–2445 are sparse, with no tick-to-tick adjacency, so do not invent transitions between their missing frames. Use the source-attested red screen reflection, the fixed 7:6 provisional camera, and only source-visible bottom alpha as the registration anchor. Predeclare one bounded mechanical phase/tilt trajectory, count changed/held pixels, wheel/paint/part residuals, and reject per-frame camera/shape tuning. Then score historical frozen source families and explicitly label the 38 new observed planes as diagnostics, **not blind held-outs**.

This module does **not** establish the 1994 original mesh, source-to-2026 pose/phase correspondence, authentic crank speed, physical wheel contact or camera, source rendering correctness, owner likeness approval or ART-4K shipping acceptance. Keep the original art fallback until an actual source-backed, visually approved animated candidate qualifies.
