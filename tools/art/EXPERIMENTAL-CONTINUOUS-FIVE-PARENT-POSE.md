# ART-4K single-source continuous axle/frame pose control (experimental)

**One GLB, two interpretable mechanical controls.** This is a *new in-memory pose operator* for the existing 2026 unapproved five-parent, sixteen-material rig in draft [#2832](https://github.com/gamesbyian/UR-Recomp/pull/2832). It does not author another model or change the game's presentation, release art or source-camera estimate.

Prior experiments rotate fork+saddle about the axle and separately fix stationary rim/spoke rotation relative to an already baked pose's pedals. This combined control starts from the **one immutable upright GLB** (SHA-256 \`efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5\`) and enforces two shared, continuous transforms:

- **Wheel/crank delta (±360°)** rotates tire, rim/hub *and pedals together* about the same source-authored axle. This preserves direct-drive synchronization; upright's authored crank reference is 18°.
- **Frame pitch (±45°)** rotates fork/frame and saddle together about the same axle while preserving their preexisting relative orientation.

Both commands act on the original *part-parent transforms* with the axle-conjugated rigid transform, preserving all 16 material-separated, part-local meshes and source name hierarchy. No new CSG triangulation, per-pose geometry substitution, dedicated GLB fork or player-specific fitted mesh is introduced. The two axes are currently both the axle axis; they are identifiable only if source evidence distinguishes wheel/spoke/crank motion from relative fork/saddle tilt. Source 2D painted axes alone cannot certify those 3D mechanisms.

## Reuse and validation

The pure ROM-free regression tests validate bounded finite parameters, sign conventions, full-turn closure, invalid source rejection and, where NumPy/Trimesh are available, a synthetic translated-axle scene with exactly five parents and sixteen meshes. The optional real artifact path checks source GLB SHA, genuine scene hierarchy, all unchanged local mesh buffers, 16 colour/material children, and actual GLB export/reimport parent matrices. No new scheduled agent, web viewer, CI workflow or source emulation.

    python3 -m unittest tests.unit.test_experimental_continuous_five_parent_pose

For explicit owner review using the already-authenticated viewer GLB artifact #13063969312:

    python3 -m tools.art.experimental_continuous_five_parent_pose \
      --source-glb /private/verified/upright.glb \
      --wheel-crank-delta-deg 25 --frame-pitch-deg 10 \
      --out-glb /private/new/phase25-pitch10.glb \
      --receipt /private/new/phase25-pitch10.json

The generated GLB and receipt are exclusive/no-overwrite. A real artifact-derived output has **not** been claimed merely because this source is written; it requires executing this CLI against the actual SHA-pinned upright GLB. The continuous operator can also act **in memory** without exporting a GLB for every candidate, keeping future source registration cheap.

## Next falsifiable source-registration experiment

First use genuine **adjacent** source frames from the original P1/P2 1205–1220 witness (30 consecutive player edges, 21 silhouette holds and 9 changes). The 20 later live Mesen ticks 1601–2445 are sparse, with no tick-to-tick adjacency, so do not invent transitions between their missing frames. Use the source-attested red screen reflection, the fixed 7:6 provisional camera, and only source-visible bottom alpha as the registration anchor. Predeclare one bounded mechanical phase/tilt trajectory, count changed/held pixels, wheel/paint/part residuals, and reject per-frame camera/shape tuning. Then score historical frozen source families and explicitly label the 38 new observed planes as diagnostics, **not blind held-outs**.

This module does **not** establish the 1994 original mesh, source-to-2026 pose/phase correspondence, authentic crank speed, physical wheel contact or camera, source rendering correctness, owner likeness approval or ART-4K shipping acceptance. Keep the original art fallback until an actual source-backed, visually approved animated candidate qualifies.
