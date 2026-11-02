# ART-4K experimental axle-centred fork/saddle hinge

**Experimental 2026 blockout, not approved original Uniracers art.** Reuse one source-owned five-part, sixteen-material GLB rig (#2832). This add-on reads the historical exact 2026 upright model GLB from the existing artifact run #41259476190, checks SHA-256 efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5, and changes **only the existing parent transforms** of fork/frame and saddle around the real tire axle. Tire, rim, hub and pedals remain unchanged. It adds no geometry, forked canonical SCAD source, viewer or runtime renderer. No new 1994 source animation timing is assumed.

## Command

Install optional offline Python packages numpy and trimesh in the experiment environment. Obtain the original GLB using existing authenticated model-review artifact #13063969312 from run #41259476190. Never replace an original or prior candidate.

    python3 tools/art/experimental_frame_hinge.py \
      --source-glb /private/upright-efdc8425f252b4a0.glb \
      --frame-pitch-degrees 3 \
      --out-glb /private/new/hinge-plus3.glb \
      --receipt /private/new/hinge-plus3.json

Accept the derived GLB only with its successfully published write-once receipt. The tool checks exact source input SHA, finite bounded experimental angle ±45°, five source parent and sixteen material child identities, source wheel/rim/crank pivot consistency, preserved untransformed source vertex/face buffers after actual GLB round-trip, exact unchanged wheel/rim/pedal transforms, and no overwrites. A zero-degree transform retains original geometry; it can produce a different export hash due to reserialization.

## Independent fixed-camera original-ROM diagnostic (2026-11-02)

Derived real source-locked GLBs using trimesh 4.11.1 / numpy 2.3.5:
- +3°: SHA-256 fd08d6f277d78f55d7b7ca3823f808587543f3f3e64c3d077ffd284b39af8172, 640012 bytes.
- −3°: SHA-256 385bf80875960cfd4c105ecb8a0d3466406ab370f12e66cec237ad081e5ffb8e, 640012 bytes.

Original mask source: authenticated canonical USA ROM-corpus artifact #13118909409 from run #41396846120, source-corpus manifest SHA-256 e26193f767d22280ab65b0549e707fa05ef246a903a4cebd47411f75726dc66e. Exact original 64×64 PNG and binary-mask SHA-256 identities were checked again. Split membership comes from actual prior fixed "wheel-holdout.json" report, artifact #13120351488: first connected 16 masks and disconnected additional 19 masks (the single initial 1205–1220 window by itself has only ten distinct masks). The original fixed provisional 7:6 side camera at analysis/data/racer-inverse-side-provisional-1205.json and the existing fourfold triangle rasterization and source-alpha placement conventions were reproduced. Baseline full-model mean IoU **0.46002071** exactly reproduces the published source experiment.

| Diagnostic source family | Unchanged GLB | +3° parent hinge | −3° parent hinge |
|---|---:|---:|---:|
| First connected 16 | 0.55276425 | 0.54748542 | 0.55159519 |
| Other 19 binary-SHA-disjoint | 0.38192089 | 0.38421620 | 0.38285225 |
| All 35 unique source silhouettes | 0.46002071 | 0.45885356 | 0.45999188 |

+3° improved per-source mask IoU on **19 of 19 disconnected additional 2D masks**, but **worsened the fit on the connected first 16**. It is therefore useful as a *possible adjustable joint* hypothesis, **not** a reason to turn the model permanently or describe a character-likeness improvement. The fixed-camera logical 64px projected GLB alpha changes for +3° occupy 34 pixels, 32 in Y=0..15 and 2 in Y=16..31; none in Y≥32. For −3°: 38, distributed 31 / 7 / 0 / 0. These are model pixel differences, not source pixel changes.

Source masks, and the authored registry's timing/hold schedule, remain separate evidence classes. No live original-emulator PPU/OAM chronology, source-registered 3D joint/camera/physical contact, unseen pose holdout, likeness or release acceptance. Any fitting should jointly compare source shape and rigid translation with frozen camera, and require actual temporal capture before timing claims. In the canonical rig (#2832), wheel/spoke synchronization is a separate known mechanical issue: applying a fix only in the SCAD whole-scene composition would leave independent GLB exporter tire/rim nodes unrotated. Coordinate that work there, not in this optional parent-transform study.

## Validation

    python3 -m unittest tests.unit.test_art4k_experimental_frame_hinge

Pure-Python matrix and invalid-angle tests need only stdlib. Four scene/asset tests use optional numpy/trimesh and skip if unavailable. Local real-GLB export of both ±3° samples passed all five-source-parent and sixteen-source-material checks, and their bytes match the previously generated candidate hashes. Hosted PR checks and independent source review still required; no candidate GLB is committed to the repository or substituted for shipping artwork.


## Extended source-family orientation experiment (post-hoc, not 3D pose recovered)

Further local real GLB variants used exactly the same source GLB, parent-only rotation, source renderer and ROM SHA-verified 35-mask corpus. The larger ±40° range remains **experimental**: it models possible distinct wheel-attached frame orientations, not a recovered original joint and not an approved continuous animation. Source image-target shapes were inspected before candidate angle selection. The default authored OpenSCAD model remains unchanged.

| Fork/frame + saddle angle around axle | Connected first 16 mean IoU | Additional 19 mean IoU | All 35 mean IoU |
|---|---:|---:|---:|
| 0° historical upright | 0.55276425 | 0.38192089 | 0.46002071 |
| +3° | 0.54748542 | 0.38421620 | 0.45885356 |
| −3° | 0.55159519 | 0.38285225 | 0.45999188 |
| +6° | 0.54781536 | 0.38902168 | 0.46161307 |
| −6° | 0.54189989 | 0.38434949 | 0.45637253 |
| +20° | 0.46752865 | 0.39046905 | 0.42569629 |
| −20° | 0.45744548 | 0.43093374 | 0.44305339 |
| +40° | 0.39956527 | 0.38729922 | 0.39290656 |
| −40° | 0.41585476 | 0.53320448 | 0.47955889 |

Actual −40° derived GLB SHA-256 `64bcf0e6aa70b6b9941d78b5c7706a86e8555640ffa4eddea22de71cc72ef676`, 640000 bytes; +40° `e46fbefe1ad86fef4c33b28c9ff73beb294e0122a507b8a6cc9c8d4f1cb5c137`, 640000 bytes. Eighteen of nineteen additional masks improve against the unhinged baseline at −40°, while fourteen of sixteen first-connected masks worsen. **No one static hinge angle fits every source pose family.** Each original 64x64 source mask has only a 2D silhouette, so these remain *unpaired* candidate pose comparisons, not confirmed historical animation.

The independently ROM-authenticated, already merged original 2D painted-colour-axis witness `source-chroma-axes.json` from run #41398486394 supplies a plausible explanation without cherry-picking a 3D joint: first-connected 16 have signed image-vertical axis median **−1.053°**, while additional 19 have median **+41.504°**, one vote per binary source SHA. The two family sets are very different in *observed 2D painted orientation*. These source axis angles cannot be equated directly to any GLB axle rotation, nor do they establish original camera. Before fitting geometry, use the existing chroma-axis semantic cue and original masked part visibility to assign pose hypotheses, preserve frozen train/test clusters and validate independently with future genuine emulator PPU temporal capture.

The ±45° code range is a finite exploratory authoring envelope, **not** a physically or historically accepted permissible tilt limit. Source-matched validation must test wheel/rim/crank synchronization, fork-to-hub connectivity, real contact and saddle shape as separate kinematic constraints. No shipping geometry is promoted automatically.


## Exploratory source-painted-axis pose choice, NOT independent validation

A source-image feature can be used to choose *between* two real existing-geometry GLB poses without selecting the best silhouette score for each target. Reuse the existing ROM-authenticated `tools/art/audit_original_racer_chroma_axes.py` output, namely `source_variants.source_masks[].equal_colour_variant_mean_projected_angle_deg`, then apply:

- signed painted axis > +20° relative to source image vertical: choose −40° axle-centred frame hinge;
- otherwise: choose original 0° upright GLB.

`exploratory_pose_from_source_painted_axis()` is deliberately a separate, pure-Python **research** helper. It does not modify `process()` defaults, source rig, exported animation or live game. With the same 35 authentic ROM-composed source masks, 20 selected −40°, 15 selected upright. Under the unchanged provisional 7:6 camera, this gave **mean silhouette IoU 0.54715522** compared with original static upright 0.46002071. The 20 selected masks improve individually and none lose; connected first 16 scored **0.56328621** (two selected −40°), and other SHA-disjoint 19 scored **0.53357123** (18 selected −40°).

This number has a major **training/selection warning**: the −40° candidate, the signed +20° threshold, and the two source families were all inspected on these same 35 masks before evaluating this rule. This is *not held-out validation*, an original 1994 joint angle, calibrated source camera, animation-timing recovery, or a rule proven useful on new sprites. It does establish that 2D original painted appearance can provide a deterministic cue for choosing two constrained poses of the existing 3D GLB, without a per-mask silhouette-IoU oracle at the final selection step. Require new independent original PPU/OAM source captures and predeclared unseen pose-family test before calling the colour-conditioned mapping predictive.
