# ART-4K: executed original Mesen24 sprite silhouettes versus the real 2026 GLB

**Research question:** Given the one existing 2026 five-parent, sixteen-material experimental GLB, do two *fixed historical pivot choices* plus a common, explicitly hypothetical original-ROM orientation/phase law explain actual source-alpha movement better than simple source-only 2D alternatives?

This is the first **direct paired original 1994 source-PPU / real 2026 GLB silhouette** test of the new three-control rig. The original 1994 mesh, camera, material allocation, skeletal articulation, physical angular units and source-to-2026 pose map remain **unrecovered**. The owner has not approved the 2026 blockout's likeness. The test neither promotes artwork into native Windows presentation nor grants a release/QA milestone.

## Source evidence, no emulator replay

- Reuse the already-merged **24 consecutive authentic no-frame-skip original Mesen ticks 1601–1624**, ZIP SHA-256 `28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6`. This stacked rig branch predates the ZIP merge, so the existing PR validation fetches the 233,939-byte original ZIP from **immutable commit `822d4b3fecfef66e52b2799fa686afcd8afda2fd`**, verifies the exact entire-archive SHA, ZIP CRC/97 members, OAM/VRAM/CGRAM lengths and each used decoded original index-plane SHA from #3104. It does not duplicate the more recently merged full-auditor code.
- Reuse #3104's **48 uniquely exact original-ROM primary frame IDs** (SHA-256 `6286aedcda6080acf832ecece9fcdb879354db008e870bc00ada02db3ff3aa20`) and the original 24×64 source-axis report (SHA-256 `23aa563c094471a3d7f1b5dcb12489cc1b5ca45b1240aee06fde3934a932bbd0`), both from #3104 head `820ca7b84c5ffe21996ae593043c8ef4a874bd66`. Since that PR is not yet merged, the exact read-only inputs are separately SHA-verified; **do not copy source parser code into this stacked model PR**.
- Exact current export from the **existing** #2832 OpenSCAD authoring branch and existing Windows Visual Atlas real-model-export job. It already validates exporter attempt/current pointers, GLB digest, one source SCAD SHA `e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984`, five parents and 16 material meshes. Same source may emit variable GLB bytes across builds; never assume one historical GLB SHA. **No additional model export**.
- One fixed, **provisional** side orthographic camera, SHA-256 `1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028`, with source SNES display aspect **7:6**. All scoring is on 64×64 *held OAM-local source* alpha, not reflected red final-screen pixels. Source alpha base placement is the tick-1601 lowest visible alpha span midpoint, once per racer; it is **not** independently established ground contact.

## Predeclared actual executed source comparisons

Two different original 2P source players, each with two real chronological tick edges:

| Original racer | Upper-change event | Ordinary ride event |
|---|---|---|
| Blue OAM96 | **1602→1603** | 1609→1610 |
| Red OAM97 | **1605→1606** | 1609→1610 |

Only four selected source images per racer (eight in total) are scored. The tick-1601 source sprite of each racer is a **registration anchor** and the fixed reference for two 2D nulls, not an extra secretly fitted trial. Use original #3104 ROM-exact `(phase,orientation)` integer states at the selected authentic PPU ticks; retain per-player chronological identity rather than choosing a best pose independently by IoU. **Already examined states, not a prospective blind test**.

Frozen comparison arms:

- Original tick-1601 2D alpha held unchanged.
- Original tick-1601 alpha rotated in 2D through the source orientation-index **difference** around one original-ROM even-index phase-region centre (no per-tick re-registration or deformation).
- The unchanged static 2026 upright GLB silhouette.
- The **same** GLB with whole-character source orientation index (provisionally `360×index/64` degrees), rotated around the historic wheel-axle pivot, with wheel phase fixed.
- Equivalent whole-character orientation around the **already authored** 2026 midbody stunt pivot, with wheel phase fixed.
- Both historical root pivots again with one common hypothetical crank phase law `source_phase×15°`; 2026 fork/saddle pitch remains zero.
- For both root pivots, additional **source-first relative controls**: rotate by the wrapped orientation-index change since each player's tick-1601 original frame, either with fixed crank or with the corresponding phase-index change since the **same** tick1601 source. The original absolute-index arms stay intact, making this a transparent origin-calibration sensitivity experiment rather than replacing a negative result. This physical angle law is a *predeclared convenience hypothesis*, not a recovered 1994 wheel rotation or original clock rate.

The source-to-2026 GLB 64px registration is fixed **once per player** from its actual tick-1601 alpha anchor, **not tuned per frame/pivot/camera/phase**. Each candidate is rendered under the same 7:6 camera using actual 2026 mesh triangles and root/axle parent transforms, not a silhouette surrogate. No 2026 GLB geometry, materials, pivot positions, source colours, original PPU state or source tuple is edited. The dynamic GLB is reused in memory and render cache entries are keyed by explicit integer original source phase/orientation and fixed pivot mode.

**Score:** per-frame/pivot binary silhouette intersection, FP, FN, IoU; pooled and mean IoU separately for blue/red; **alpha change support** overlap on the four authentic chronological edges. Exact 4bpp source palette index correspondence is **not yet scored** against the 2026 material-ID model, because source palette indices have no independent one-to-one 3D part/material identification. Report missing/clip conditions as experimental failure, not as silently optimized source placement.

## Executed original 3D comparison, before reference-relative controls

**Actual GHA execution:** [run #41790188939](https://github.com/gamesbyian/UR-Recomp/actions/runs/41790188939), original Mesen source versus verified real #2832 five-part GLB, job `126441785643`, exact-head `c11e50ca48057c1c0e8fa91ce89f51286c0befa6`. Repo hygiene, full tooling units, 320–1440px Chromium smoke, true five-pose model export and exact original source-versus-rendered-GLB checks passed. Model source-derived upright GLB actual SHA during this run: `90dc439ee711847b44211ce5e82845db0ebccd0b3d60d7fd983c2d6f10b02034`; it may vary across export runs and was validated against the exact source and success-pointer receipt.

| Frozen original source versus 3D arm | Blue pooled alpha IoU | Red pooled alpha IoU |
|---|---:|---:|
| Original tick-1601 2D source sprite, held | 0.77513966 | 0.74206897 |
| Same original 2D sprite, rigidly rotated by source orientation delta | **0.83754513** | **0.82731214** |
| Static authored 2026 upright GLB | 0.49047014 | 0.36390017 |
| 2026 GLB root at wheel axle, absolute original orientation index | 0.52846054 | 0.55107352 |
| 2026 GLB root at wheel axle plus absolute 15°×source phase | 0.53441558 | 0.56028834 |
| 2026 GLB root at historic mid-body pivot, absolute index | 0.51254019 | 0.28563744 |
| Same historic mid-body root plus absolute source phase | 0.51213282 | 0.27885653 |

**Negative finding:** the current unfitted 2026 3D GLB loses to both true-source-derived 2D controls across both racers, on the *same eight authentic selected frames*. The historic mid-body pivot's retrospectively close source orbit-centre projection **does not** confer superior source silhouette overlap. The source 2D baseline uses authentic initial artwork while the GLB uses a hand-authored experimental 2026 shape; this is a stringent existing-image comparison and **cannot** by itself refute a different source-authored 1994 3D rig. It says the current candidate did not recover source visual fidelity.

**Identified fairness issue:** the first 3D experiment interpreted original orientation index as an **absolute** model rotation while its 2D null used the *change since tick-1601*. Actual original first-frame source values are blue **(phase 3, orientation 61)** and red **(phase 16, orientation 57)**. Both absolute and one-reference-relative 3D laws are now retained as separate predeclared controls without per-frame fit: `(orientation - first_orientation) mod 64`, and for the optional direct-drive arm `15°×((phase-first_phase) mod 24)`. Those offsets are fixed once at tick-1601, not reoptimized per selected event or based on IoU. The old exact-head result above remains the authenticated **absolute** experiment; the extended source-relative experiment requires a new exact-head CI execution. Even an improved relative run cannot prove actual 1994 mechanical degrees or 3D geometry.

## Source-image residual diagnosis, without changing geometry

The first real source comparison ranked seven candidate controls, then a second exact run added four source-first relative controls. **Neither original experiment partitions the remaining silhouette errors by image region**, so model geometry cannot yet be refined responsibly by assuming the apparent best global pivot is the right shape. The scorer now additionally reports **fixed original source-y bands** for every one of its already-rendered original and 2026 candidate masks: upper y=0..14, middle y=15..26, lower y=27..63, following prior source-event descriptions y4..14 / y15..26 / y27..38 and covering all 64 rows.

For every existing arm, player and selected source frame, record the raw *intersection, predicted-only, source-only, IoU* of each band. Aggregate the same counts across four source images per player; also partition the **actual two source chronological alpha-change edges** (not synthetic adjacent ROM registry observations). Invariant: summed band TP/FP/FN must equal the unpartitioned source/GLB mask, and no y region is allowed to move per frame, model, camera, pivot or player. The output is a **diagnostic spatial ledger, not an original anatomical classifier**. The upper band is not proven to be the 1994 saddle, and the lower band is not proven to be physically rotating wheel geometry.

This reuses the **same exact existing GLB export, original source archive, registered per-player tick1601 anchors and candidate render cache**. No extra OpenSCAD build, new reference capture, source pose fit, camera parameter or model geometry search is authorized. When a source band has excess/missing candidate pixels, the next experiment must identify actual visible 2026 model part support there before proposing a bounded change to the single #2832 rig. The source event and absolute/relative comparisons remain intact.

## Fixed alternative model-handedness test (new stacked #3117)

The executed #3116 fixed source-y bands sharply separate candidate difficulties. Against the original source **upper y0..14** four-frame pixel instances, unchanged 2026 candidate overlap is blue **0.22269807 IoU** but red **zero**, despite red lower y27..63 measuring **0.66317627**. For blue, fixed relative midbody improves upper IoU only to **0.27947598**; for red it remains **zero**. The original rigid 2D rotation null stays **0.80733945 blue / 0.74074074 red** in the same upper band. The one frozen real source experiment is [#41828444936](https://github.com/gamesbyian/UR-Recomp/actions/runs/41828444936), real GLB job `126569112137`, source head `fb6f30551b2f4209bb273c028f75e1692b9530e6`. Upper missing/predicted counts are 1994 sprite pixel *instances*, **not** independently recovered 1994 3D saddle surfaces.

This upper-band discrepancy motivates a **single fixed alternative 2D handedness control** before touching the 2026 saddle, frame, wheel or camera. Earlier source [#3099](https://github.com/gamesbyian/UR-Recomp/pull/3099) established that *completed-screen red* differs from the held red OAM-local source by horizontal reflection, and established the identity `IoU(R(source),R(model)) = IoU(source,model)`. Here the scorer continues to use **held OAM-local** source data for both players. Therefore mirroring **only the candidate model projection** against that held source is an intentionally separate, **alternative/unvalidated** model-handedness hypothesis, *not* the already verified red screen-compositor transform. It must never silently become the default. Measure the same candidate-only mirror on **both** blue and red, not select per frame or report only its winning player.

For each of five fixed source-model controls (static GLB, absolute axle root, absolute midbody root, source-first relative axle root and relative midbody root), use the *same already-rendered 256×256 model silhouette*, reflect it around logical source 64px x2=63, then once-only bottom-alpha register the mirrored model to each player's original tick1601 anchor. The 4× reflection preserves actual logical source pixel-centre x positions `4k+2` rather than reversing the 256px buffer off by one quarter-pixel. No original ROM data, source role, source camera or model geometry changes; no additional OpenSCAD/GLB output or per-pose pose/camera fit. Include upper/middle/lower source-band centroids **for both original and candidate** as a further diagnostic: a zero intersection can reflect lateral separation rather than anatomical absence. Band sum TP+FP+FN continues to equal the whole-mask score.

**Decision:** If fixed mirrored candidate strongly improves red upper source overlap but worsens blue, investigate a *single independently attested source player-to-rig handedness convention* using #3099's actual completed-screen evidence, while retaining OAM-local/completed-screen evidence as separate classes. If both remain poor, prioritize paired upper structure/pose anatomy and original source-camera interpretation. Do not promote any mirror as recovered historical 3D or owner-approved likeness. This branch extends #3116; current scientific scores above belong to its earlier exact-head real GLB run. The new mirror/centroid experiment needs independent exact-head CI and source-art review.

## Actual 3D frame/saddle articulation discriminator, following fixed mirror negative

[#3117](https://github.com/gamesbyian/UR-Recomp/pull/3117)'s **actual full original Mesen/2026 GLB and Chromium run [#41830180568](https://github.com/gamesbyian/UR-Recomp/actions/runs/41830180568)** disproved a simplistic image-space-handedness explanation. The 2026 static model projected upper red source-y0..14 at x≈38–39 versus actual original x≈25–26, giving 0/285 source upper pixel matches, and mirroring the candidate alone still gave zero. The tested **absolute source-index wheel-axle root** instead puts the model upper region around x≈26.6–27.8 and achieves red upper source IoU **0.33251834**, with blue absolute-axle upper **0.28798186**. The model's 2026 wheel/rim and lower fork occupy much of the lower region where alpha overlap is already far better, and the source-only 2D rigid rotation is still much better overall. This is *a verified upper image-region discrepancy*, not evidence of original 1994 frame/saddle joints.

The next most constrained physically coherent test reuses **#3101's existing, independent 2026 fork/frame+saddle rigid axle hinge** without changing **any** local model mesh, materials, renderer or camera. On the one actual 2026 GLB, apply the prior best upper-registration law, absolute original orientation-index root around the 2026 wheel axle, hold crank at original authored neutral, then test three **fixed candidate frame-pitch values** across all selected authentic blue/red Mesen source frames: **0°** (existing arm), **−15°**, **+15°**. The two new arms are `wheel_axle_root_frame_pitch_minus15` and `wheel_axle_root_frame_pitch_plus15`. These are 2026 mechanical **candidate** degrees, not recovered original game source degrees. They were chosen as a symmetric bounded mechanism discriminator **before** measuring the new 3D images. No "best pitch" per source frame/player, camera re-registration, source index timing change, new 3D mesh or second GLB authoring pass is permitted.

The same source OAM-local 64px silhouette IoU, per-y-band source/candidate centroids, full TP/FP/FN and real chronological edge-change overlap are computed for both signs alongside all 16 unmodified controls. If neither pitch improves **upper source shape** without degrading the already comparatively good middle/lower regions and if both still lose to the original source 2D null, reject the idea that a single constant simple 2026 fork/saddle hinge fixes the reconstruction. If one sign improves on **both** source players, preserve it only as an experimental **globally fixed candidate** and demand additional source-family holdout/owner visible likeness before changing authored default articulation.

This runs inside the **same existing** CI real OpenSCAD-to-GLB export route as #3116/#3117, with 2026 source SCAD, original Mesen24 and exact ROM-phase/angle source data all SHA-verified, and no new workflow/emulator. The original 1994 pre-rendered sprites, PPU-index material semantics, camera, source physical degrees and owner visual approval remain unverified.

## Independent authored saddle-mount pitch, after the shared frame-hinge result

The tested common **±15° fork/frame+saddle** hinge in #3118 failed to improve original 2P silhouettes under a shared mechanical law: +15° improved blue total IoU **0.52846054→0.55511551** but worsened red **0.55107352→0.47091584**; −15° worsened both. The same untouched 2026 OpenSCAD source already exposes a **separately pivoted saddle(lean)** about its actual source-owned mount (the existing GLB saddle node, 2 of 16 material child meshes). That is a narrower 2026 candidate articulation with independently identifiable upper-region geometry: neutral source #3119 exact GLB raster assigns 56 upper image pixels to saddle, 18 to fork/frame, with 4 pixels overlapping. This is strictly **2026 candidate shape anatomy**, not proven original 1994 saddle animation.

**New bounded hypothesis:** On the existing actual, SHA-verified 2026 GLB and the same eight authentic original Mesen24 selected blue/red PPU frames, maintain the exact pre-existing **absolute index axle-root** pose (crank/frame pitch 0) and one frozen camera/source registration. Test exactly **−15°** and **+15°** additional local saddle mounting rotation (2026 mechanical degrees) against the unchanged 0° arm. Unlike #3118, the tire, rim, pedals and fork/frame world transforms remain unchanged: a reversible context manager temporarily right-multiplies the original saddle local-parent matrix by source-world Y rotation around its authentic GLB mount, then restores the exact original parent matrix before the next GLB controller state. The same source y-band TP/FP/FN, centroids, original true-event change and full alpha metrics are recorded with all existing controls. No new 2026 saddle geometry, copied rig, camera, per-frame fitted lean, original ROM changes, emulator captures or standalone workflows.

**Decision:** A fixed saddle-only tilt must improve the **upper** source region without worsening middle/lower and preferably both original racers before being considered a plausible globally shared model articulation. If only one player improves or both remain far below the rigid source-2D baseline, preserve the negative and seek better source pose/viewpoint evidence. No original 1994 joint, camera, physical lean or owner likeness approval is claimed by a numerical improvement.

## Reproduce from an already authenticated export

```sh
python3 -m unittest tests.unit.test_score_original_mesen24_fixed_pivot_glb
python3 -m tools.art.score_original_mesen24_fixed_pivot_glb \
  --source-zip /exact/sha-verified/original-mesen-consecutive-1601-1624.zip \
  --pose-report /exact/sha-verified/original-mesen24-exact-pose-IDs.json \
  --axis-report /exact/sha-verified/original-ROM-24phase-64angle-source-axis.json \
  --camera analysis/data/racer-inverse-side-provisional-1205.json \
  --verified-exports /actual/earlier/ART4K/model-exports \
  --out /new/original-Mesen24-vs-real-five-parent-root-pivots.json
```

The owning script validates every original source/camera/GLB evidence SHA, verifies actual original PPU member and 4bpp plane identity, and writes an **exclusive no-overwrite report** with a compact machine-readable Actions log summary. CI reuses the already-running Windows Visual Atlas real-model-output job, fetching only the two SHA-checked, immutable source reports at a pinned #3104 commit. It does **not** add any new workflow or recurring source emulator replay.

**Stop/ranking rule:** Compare the two 3D pivots and the explicit wheel phase law without per-frame best-case selection. If both 3D variants fail to exceed the fixed 2D null in pooled silhouette and changed-boundary coverage across both source players, publish a negative result and preserve the experimental 2026 model unchanged. If one improves, request *new prospectively reserved orientation/phase source families* and actual owner-visible high-detail likeness review before modifying default art. The existing source-only #3114 supports rigid 2D movement but does not automatically award any 3D correspondence.

Dependencies: #3104's original data receipt and #3101/#3115's real model kinematics; exact-head tests/real-authored-GLB execution and independent scientific review before merge. No owner art acceptance.
