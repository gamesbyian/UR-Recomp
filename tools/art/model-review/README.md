# Racer 3D Review (experimental)

A responsive, read-only Three.js inspection tool intended for GitHub Pages. This is a visualization surface for **the existing #2832 part-addressable OpenSCAD/GLB authoring candidate**, not a replacement authoring rig, a gameplay renderer, or evidence of approved source likeness.

## Launch

Serve this directory over HTTP (for example `python3 -m http.server 8000 --directory tools/art/model-review`). The viewer also accepts a local .glb upload entirely within the browser. Browser import-map support and internet access to pinned Three.js 0.170.0 CDN modules are required. Pin and vendor these dependencies for offline use before a release-quality publication. No ROM input is needed.

## Publishing contract

The default checked-in manifest intentionally contains no model. **Do not publish an invented procedural surrogate** or silently label the old #2832 blockout the 1994 asset.

The actual screenshot atlas owns the Pages root. Its existing `.github/workflows/windows-visual-atlas-site.yml` now assembles this viewer automatically under `model-review/`; the top-level atlas links to it. A manual workflow dispatch with `include_experimental_model=true` checks out the *current* #2832 experimental branch and builds all five source-owned pose GLBs, verifies their immutable receipts, and replaces the empty viewer placeholder inside the **same** atlas site. To put that complete site live, choose `deploy_pages=true` on the same workflow dispatch. Other atlas dispatches default to model-free to avoid unnecessary multi-minute OpenSCAD runs. Deployments remain an explicit owner-controlled operation, as with the pre-existing atlas. GitHub Pages must already be configured for Actions deployment.

The existing #2832 exporter creates five separate source-owned pose GLBs using `--rig-pose upright|pedal|wheelie|stunt|bank`. Once independently qualified and the draft model work is integrated, a Pages publisher should:

1. Build five pose exports from one exact source commit, with isolated output directories and OpenSCAD / NumPy / Trimesh dependencies. The opt-in GitHub Actions route automates this against the existing draft branch; a local export may use the same staging script.
2. Verify each `articulated_blockout_last_attempt.json` is `succeeded`, and its attempt ID equals the `articulated_blockout_current.json` attempt ID. Verify the SHA-256 of each GLB and receipt against that pointer, and reject any missing or mismatched file.
3. Copy the five immutable GLBs under `model-review/assets/<source-commit>/` and publish a **new manifest last**, with `model_url`, `poses[*].url`, `source_commit`, `candidate_sha256`, and `likeness_approved:false`. All URLs must be relative to this page. Do not use mutable artifact links or expired CI ZIP URLs.
4. Publish the resulting directory *within the existing Windows Visual Atlas Pages site* rather than replacing its index. The existing atlas workflow is the deployment authority.
5. For every new accepted model revision, rebuild the five poses and atomically replace the manifest only after all files validate. Never show the previous successful artifact as a newly successful run.
6. Preserve exact export SHA and original source comparison/holdout evidence separately. Show an authentic sprite-pose selector only when mappings are explicitly registered to verified source frame IDs; the five current selections are **blockout studies**, not original 1994 poses.

## Original 1994 sprite reference rail

The atlas assembler independently runs `tools/art/build_racer_source_pixel_corpus.py` and verifies the retained original first-family stock PNGs and source manifest before copying **P1 and P2 frames 1205–1220** to `model-review/sprites/`. It writes a separate `sprites.json` with each frame, authenticated source representation ID and the original PNG byte SHA-256. These are pre-existing source-registered images, not ML-generated pixels, and the user may scrub through them beside the candidate mesh. The 2D sprite scrubber is **deliberately independent** of the five blockout pose GLBs. There is no invented mapping from guest frame to a 3D rig state, nor a claim that those seven distinct stock images represent independent 3D cameras.

The true GLB source is OpenSCAD Z-up; the viewer rotates the source scene into browser Y-up. Side/front/rear/top camera shortcuts are view-only and never modify the underlying authored transforms.

## Known limitations

This page and the atlas's optional GLB export/deployment workflow are implemented on PR #2938, **but no live Pages deployment or real model-export browser smoke has yet been verified**. The draft #2832 branch is intentionally still the GLB producer. The existing workflow can publish its current experimental head only on an explicit authorized dispatch after these changes merge. The viewer's five named poses require five separately exported GLBs; a local neutral GLB upload alone cannot recreate source-defined OpenSCAD per-part crank and saddle transforms. Picking mesh nodes is diagnostic only; pivots are displayed as model-node origins. The OpenSCAD GLB has Z-up coordinates, and the viewer converts them into Three.js Y-up for normal inspection; conversion can be toggled for third-party GLBs. No owner likeness sign-off, skeletal skinning, real animation channels, source-camera calibration or sprite-pose authentication is implied.

Existing authorities: [inverse-graphics spec](../../../docs/HD-RACER-INVERSE-GRAPHICS-SPEC.md), [plan](../../../docs/HD-RACER-INVERSE-GRAPHICS-PLAN.md), [character art review](../../../docs/HD-RACER-CHARACTER-RECONSTRUCTION.md), and [#2832](https://github.com/gamesbyian/UR-Recomp/pull/2832).
