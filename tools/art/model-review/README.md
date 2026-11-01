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

## Optional, source-hash-verified research comparison

The only viewer at `/model-review/` includes an **opt-in** *Experimental source comparison* panel. A visitor can click **Load verified comparisons** without losing the ordinary 3D pose, camera or sprite controls. The panel is intentionally absent/closed by default; a missing, stale, malformed or hash-inconsistent `model-measurements.json` merely produces a visible unavailable message and leaves the model functional.

A valid optional packet must have schema `UR-RACER-MODEL-REVIEW-MEASUREMENT-SIDECAR/1`, be generated by `tools/art/prepare_model_review_measurement_sidecar.py`, and match the exact SHA-256 of the *served* `manifest.json` and `sprites.json`, model/ROM/GLB hashes, 32 original player+frame references, 10 distinct original 2D silhouette groups and original registration anchors. Client-side checks independently recompute mean IoU, highest-overlap counts and the top-two raw IoU gap, rejecting false approval or pose-identity declarations. Both `manifest.json` and `sprites.json` must be obtained and hashed as **exact response text**. No original-art pixels, ROM or model files are embedded in the packet.

The existing workflow `.github/workflows/windows-visual-atlas-site.yml` generates this optional packet **only** when an owner manually dispatches with `include_experimental_model=true` and the five original OpenSCAD blockout GLBs pass their SHA/receipt checks. It runs the source-registered 5×10 CPU-only scorer after that model staging, then hardlinks the verified JSON into the existing Pages site, with no extra rebuild on default atlas changes. The independent `deploy_pages=true` opt-in remains necessary to deploy it publicly. A local uploaded GLB disables the published measurement panel because it no longer matches the measured source.

All measurements are **unpaired, source-registered 2D silhouette similarities under a provisional camera**. The best-scoring `upright/pedal/wheelie/stunt/bank` label is not a verified 1994 sprite pose, and the top-two IoU margin is not a confidence/probability. No genuine held-out 3D view, owner likeness approval or shipping art credit is claimed. The original source and 2026 GLB pose controls remain independently selectable, even while the optional research panel is open. See [offline evidence sidecar contract](../MODEL-REVIEW-MEASUREMENT-SIDECAR.md) and [viewer integration issue #2952](https://github.com/gamesbyian/UR-Recomp/issues/2952).

## Known limitations

The viewer and five-pose exporter landed in PR #2938. **Real five-GLB mobile/desktop browser validation passed** in [Actions run #41259476190](https://github.com/gamesbyian/UR-Recomp/actions/runs/41259476190), while **a live Pages deployment has not been independently confirmed**. The draft #2832 branch is intentionally still the GLB producer. The existing workflow can publish its current experimental head only on an explicit authorized dispatch after these changes merge. The viewer's five named poses require five separately exported GLBs; a local neutral GLB upload alone cannot recreate source-defined OpenSCAD per-part crank and saddle transforms. Picking mesh nodes is diagnostic only; pivots are displayed as model-node origins. The OpenSCAD GLB has Z-up coordinates, and the viewer converts them into Three.js Y-up for normal inspection; conversion can be toggled for third-party GLBs. No owner likeness sign-off, skeletal skinning, real animation channels, source-camera calibration or sprite-pose authentication is implied.

Existing authorities: [inverse-graphics spec](../../../docs/HD-RACER-INVERSE-GRAPHICS-SPEC.md), [plan](../../../docs/HD-RACER-INVERSE-GRAPHICS-PLAN.md), [character art review](../../../docs/HD-RACER-CHARACTER-RECONSTRUCTION.md), and [#2832](https://github.com/gamesbyian/UR-Recomp/pull/2832).


## Reversible wheel-width A/B experiment (November 1, 2026)

The SAME existing 3D Pages viewer has a small **Wheel silhouette hypothesis** section with two 44px controls: unchanged **1.00×** source blockout and measured **1.10×** wheel/rim X span. The original five pose GLBs are loaded through the same prior manifest/rig pipeline. No second rig, extra GLB export, second viewer, camera auto-fit or heavy browser source extraction is involved. The viewer is still model-free by default until an opt-in experimental GLB is published. The local-upload path may inspect any GLB, but the wheel control becomes usable only if it contains exactly the original source-owned seven tire/rim material meshes.

The helper in wheel_hypothesis.mjs changes only the two tire and five rim/hub child meshes' X positions in browser memory; it computes appropriate nonuniform-stretch normals and updates bounds. It caches exact original typed arrays on first contact and restores **positions and normals bit-for-bit** when returning to the unchanged blockout. Parent pivots, fork, pedals, saddle, colours, independent P1/P2 sprite scrubber, pose loading and original GLB files remain untouched. Unsupported geometry/aliased wheel mesh data fail closed and leave the underlying viewer working.

The +10% factor was selected on the ten original first-family masks (mean silhouette IoU **0.57255469 → 0.59883507**), then **frozen** and evaluated on 19 additional SHA-independent original 2D silhouettes composed from the exact USA ROM, with no tuning to those new masks (mean **0.38192089 → 0.41491323**, 19 of 19 improved). Source and geometry hashes, all 19 per-shape scores and the actual GHA producer are retained in the dedicated ART-4K source-holdout evidence. That comparison is under a provisional single 2026 upright pose and side-camera hypothesis, not independently established 1994 mesh geometry or original pose labels. Other GLBs or poses may not reproduce those specific metrics.

**Qualify before claiming any implementation acceptance:** tests/unit/test_model_review_wheel_hypothesis.py runs the actual module in Node without a browser or CDN, exercising seven-material-only geometry changes, repeated revert, unchanged nonwheel parts, source original Float32 byte identity, malformed and aliased GLB cases and both existing Pages stage paths. Actual Chrome/Android viewer inspection of the opt-in model still matters for user acceptance. This is a reversible research control, not automatic promotion of a physically noncircular wheel or owner character likeness.
