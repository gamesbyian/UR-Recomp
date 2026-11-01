# 16-material five-GLB experimental colourway identity audit

**Purpose:** verify whether the current *actual exported* procedural unicycle model shares one stable material palette across all five experimental pose GLBs. This is a read-only offline result, not a second rig, player recolouring system, source-camera solution, original 1994 material reconstruction or art approval.

The source model is the canonical, still-draft [#2832](https://github.com/gamesbyian/UR-Recomp/pull/2832) OpenSCAD/GLB exporter. The [single Pages reviewer](model-review/README.md) from merged #2938/#2957 owns the website and any optional later source-bound colourway controls. The latest *published*, exact-GLB model SHA may differ from the latest authoring branch, so compare exact material/GLB hashes rather than silently claiming a new export.

## Observed actual source-owned publication

Using the real five-GLB artifact retained by [Actions #41259476190](https://github.com/gamesbyian/UR-Recomp/actions/runs/41259476190), original model source commit `d061cddcdbac9b2b5ac137d0d721b63f92dc3ec1`, source SCAD SHA-256 `e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984`:

Every one of `upright`, `pedal`, `wheelie`, `stunt`, and `bank` exports **16 named material meshes** under the same original five parts: tire 2, rim/hub 5, fork/frame 4, pedals 3, saddle 2. Each of the sixteen mesh identities has a uniform RGBA vertex colour across its own vertices. All five pose exports have the **same authored material RGBA assignment** despite differing 3D geometry. The primary fork material `fork_and_frame__material_0` is **RGB (28,89,222)**, hex `#1c59de` (blue).

By contrast, the source raster colourway study [#2965](https://github.com/gamesbyian/UR-Recomp/pull/2965) finds that exact original P1 raster source uses **red** accents, P2 uses **blue**, with 15 opaque RGB colours each and five common neutral grayscale entries. Those 2D raster colours are historically grounded, but the identity of an original pixel's 3D material, lighting and surface remains unknown. A blue blockout beside P1 red sprite should remain visibly labelled as *unpaired experimental one-colourway model*.

## Repeat for a newly staged real five-pose site

```sh
# From repository root with optional Trimesh installed, and the existing
# real model-review site containing SHA-bound GLBs and original sprite rail.
python3 tools/art/audit_real_glb_material_identity.py \
  --model-review-dir /private/verified-atlas-site/model-review \
  --out /private/ur-art4k/model-colourway-fingerprint-001.json

python3 -m unittest tests.unit.test_audit_real_glb_material_identity
```

The tool first invokes the **existing** viewer-model source authenticator and rejects forged SHA, absent GLB, untrusted source sprite rail, symlinked site or mixed manifest update. Then it parses the five **actual GLBs** using optional Trimesh, requires the known **exact set of sixteen material mesh identities**, finite existing source geometry and homogeneous, opaque RGBA vertex colours, and fingerprints all sixteen slots. Pose-specific material drift is a hard failure. It records exact viewer manifest and sprite-rail SHA, model source commit, SCAD SHA, each actual GLB SHA and the common material fingerprint. No binary model, original ROM/sprite PNG or copied photograph appears in the output. An optional output destination is published once with the existing no-replace helper, outside the website folder.

Current one-colourway exact material parity is a descriptive baseline. A future intentional **source-registered two-player colourway implementation** must version its contract and preserve all pose/geometry/part hashes separately; the current detector is deliberately narrow. It cannot decide which old pixels were fork material or infer original shader/albedo. Owner acceptance and final art integration remain separate explicit gates.

**Engineering significance:** the five original pose meshes are sufficiently material-addressable that a single shared five-part rig can plausibly support distinct authentic P1/P2 colour references, instead of two independently modelled characters. But the *provisional* red/blue mapping and accurate shading must be independently reviewed before implementing material changes to draft #2832 or publishing new colourway variants in the existing viewer.

