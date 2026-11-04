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
- Both historical root pivots again with one common hypothetical crank phase law `source_phase×15°`; 2026 fork/saddle pitch remains zero. This physical angle law is a *predeclared convenience hypothesis*, not a recovered 1994 wheel rotation or original clock rate.

The source-to-2026 GLB 64px registration is fixed **once per player** from its actual tick-1601 alpha anchor, **not tuned per frame/pivot/camera/phase**. Each candidate is rendered under the same 7:6 camera using actual 2026 mesh triangles and root/axle parent transforms, not a silhouette surrogate. No 2026 GLB geometry, materials, pivot positions, source colours, original PPU state or source tuple is edited. The dynamic GLB is reused in memory and render cache entries are keyed by explicit integer original source phase/orientation and fixed pivot mode.

**Score:** per-frame/pivot binary silhouette intersection, FP, FN, IoU; pooled and mean IoU separately for blue/red; **alpha change support** overlap on the four authentic chronological edges. Exact 4bpp source palette index correspondence is **not yet scored** against the 2026 material-ID model, because source palette indices have no independent one-to-one 3D part/material identification. Report missing/clip conditions as experimental failure, not as silently optimized source placement.

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
