# Racer 3D Review (experimental)

A responsive, read-only Three.js inspection tool intended for GitHub Pages. This is a visualization surface for **the existing #2832 part-addressable OpenSCAD/GLB authoring candidate**, not a replacement authoring rig, a gameplay renderer, or evidence of approved source likeness.

## Launch

Serve this directory over HTTP (for example `python3 -m http.server 8000 --directory tools/art/model-review`). The viewer also accepts a local .glb upload entirely within the browser. Browser import-map support and internet access to pinned Three.js 0.170.0 CDN modules are required. Pin and vendor these dependencies for offline use before a release-quality publication. No ROM input is needed.

## Publishing contract

The default checked-in manifest intentionally contains no model. **Do not publish an invented procedural surrogate** or silently label the old #2832 blockout the 1994 asset.

The existing #2832 exporter creates five separate source-owned pose GLBs using `--rig-pose upright|pedal|wheelie|stunt|bank`. Once independently qualified and the draft model work is integrated, a Pages publisher should:

1. Build five pose exports from a single exact source commit, with isolated output directories and the existing OpenSCAD / NumPy / Trimesh dependencies.
2. Verify each `articulated_blockout_last_attempt.json` is `succeeded`, and its attempt ID equals the `articulated_blockout_current.json` attempt ID. Verify the SHA-256 of each GLB and receipt against that pointer, and reject any missing or mismatched file.
3. Copy the five immutable GLBs under `model-review/assets/<source-commit>/` and publish a **new manifest last**, with `model_url`, `poses[*].url`, `source_commit`, `candidate_sha256`, and `likeness_approved:false`. All URLs must be relative to this page. Do not use mutable artifact links or expired CI ZIP URLs.
4. Publish the resulting directory *within the existing Pages site* rather than replacing the entire Pages root or colliding with the screenshot atlas. If the existing site is hosted from a separate repository/branch, integrate its owning deploy workflow first.
5. For every new accepted model revision, rebuild the five poses and atomically replace the manifest only after all files validate. Never show the previous successful artifact as a newly successful run.
6. Preserve exact export SHA and original source comparison/holdout evidence separately. Show an authentic sprite-pose selector only when mappings are explicitly registered to verified source frame IDs; the five current selections are **blockout studies**, not original 1994 poses.

## Known limitations

This page is implemented, but there is **not yet a published live Pages endpoint or a Pages-integrated GLB export**. The build/publish integration is intentionally not guessed: #2832 is still draft-only and the existing Pages site's ownership/deployment layout needs to be verified before writing over it. The viewer's five named poses require five separately exported GLBs; a local neutral GLB upload alone cannot recreate source-defined OpenSCAD per-part crank and saddle transforms. Picking mesh nodes is diagnostic only; pivots are displayed as model-node origins. No owner likeness sign-off, skeletal skinning, real animation channels, source-camera calibration or sprite-pose authentication is implied.

Existing authorities: [inverse-graphics spec](../../../docs/HD-RACER-INVERSE-GRAPHICS-SPEC.md), [plan](../../../docs/HD-RACER-INVERSE-GRAPHICS-PLAN.md), [character art review](../../../docs/HD-RACER-CHARACTER-RECONSTRUCTION.md), and [#2832](https://github.com/gamesbyian/UR-Recomp/pull/2832).
