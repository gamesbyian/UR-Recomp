# ART-4K: same-rig real wheel-width × fork-mass interaction

**Research question:** two authentic 2026 source-owned geometric hypotheses independently improved complete original-ROM 2D alpha overlap. Do they reinforce each other on source shapes outside the original first family? The previously published 1.10× wheel/rim X span is a nonuniform in-memory transform of **only** the two tire and five rim/hub material children. The fork mass 1.4 is **not** a synthetic mesh scaling: it came from the canonical 2026 OpenSCAD source with its real `rig_frame_mass=1.4` source module. All other four source parts retain their orientation, geometry, surface topology and pivot transforms.

Historical separate original-USA-ROM independent-family results: 19 SHA-distinct source binary masks, default full-silhouette mean IoU **0.38192089**, wheel1.10-only **0.41491323**, fork1.4-only **0.38824958**. The former wheel study froze factors before these source masks; the former fork mass candidates were tested on ten first-family masks and then 19 disconnected source silhouettes. Both original studies are **2D source evidence**, and this combination study has seen these same masks already. It is not an independent, originally unseen 1994 3D camera or model-pose holdout.

## Exact source experiment

The tool `evaluate_original_racer_wheel_fork_synergy.py` accepts two existing, independently verified, actual source-built upright GLBs:

- **Unchanged fork source:** GLB SHA-256 `ffa14324c10c50b68400fbfab4285d893b248d081a50361c01d09937dd03bc04`.
- **1.4× fork source:** GLB SHA-256 `5531438b95c97dc0508790247aa3f5889f7c0d96d9079ba2970529cb1e05fa53`.

Both came from the *same* canonical draft OpenSCAD source SHA `e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984`. Their real A/B workflow verified five named parent parts and sixteen material children, unchanged four nonfork part triangle surfaces, changed fork/frame surface geometry, exact immutable GLB/receipt hashes, preserved source pivots and no original 1994 pose/material/art approval. The historical artifact ID is **#13105666094** from real source GLB GHA run **#41361012210**.

The four candidates are `fork1.0_wheel1.0`, `fork1.0_wheel1.1`, `fork1.4_wheel1.0` and `fork1.4_wheel1.1`. Every source part is decoded at exact world pose and projected with the same fixed, SHA-pinned, provisional 7:6 P1-1205 camera. The original ROM is verified and its 64×64 P1/P2 alpha masks re-decoded with source PNG and binary-alpha SHA; every shape gets one vote, with source-authenticated visible lower-alpha contact registration only, no score-driven per-frame camera, scaling or translation.

Reports per original SHA-distinct binary silhouette retain whole-alpha IoU, XOR area, boundary Chamfer (7:6 physical pixels) and lower visible contact difference for **all four** geometries. Totals are split into the 16-mask original fit-connected window component and **19 binary-SHA-disjoint** additional source silhouettes, with explicit 1994 3D viewpoint/pose/likeness non-claims.

## Preliminary CPU reproduction (not yet the hosted source acceptance)

An independent local CPU implementation of the **same exact 4× barycentric triangle rasterizer** reproduced default original-source all-35 mean IoU **0.46002** and fork1.4 **0.46835** before evaluating the crossed pair. Preliminary all-35 IoU values were unchanged default **0.46002**, wheel1.10 alone **0.49030**, fork1.4 alone **0.46835**, and wheel1.10 plus fork1.4 **0.49816**. On the 19 source masks disconnected from the initial fit family, preliminary values were **0.38192089**, **0.41491323**, **0.38824957**, and **0.42076398**, respectively. The combined variant improved IoU relative to wheel-only on 19/19 original 2D masks. These figures are preliminary: final data must come from the exact-head real-ROM/GLB workflow, including **boundary Chamfer and residual visible contact**, not just overlap. An earlier approximate OpenCV preview raster did **not** reproduce historical metrics, so those approximate numbers were discarded and were not used for acceptance.

## Execution

    python3 tools/art/evaluate_original_racer_wheel_fork_synergy.py \
      --corpus /actual/original-ROM/source-corpus.json \
      --camera analysis/data/racer-inverse-side-provisional-1205.json \
      --unchanged-glb /sha-verified/unchanged.glb \
      --fork-1p4-glb /sha-verified/fork-1p4.glb \
      --out /new/no-replace/wheel-fork-2x2-synergy.json

This runs as **two added steps in the existing opt-in original-ROM source-family workflow**, with a pinned artifact restore from real #3008 source-GLB job, and uploads its JSON beside previously merged ROM temporal, wheel-width, fork-mass and whole-silhouette reports. No new scheduled compute lane, native game change, second model, new Pages reviewer or duplicate source asset. ROM-free negative tests reject changed source geometry identity, false original 2D family independence, duplicate/missing shape keys and invalid/nonfinite score values.

**Decision rule:** if exact-hosted 19-mask interaction improves both source silhouette IoU and boundary Chamfer, preserve a *combined optional* source-authored visual A/B candidate on the **single** #2832 rig and existing Pages viewer. If only IoU improves, as with fork1.4 alone, require owner visible/contact/edge judgement before any shape default change. No original 1994 3D mesh/camera/contact, sprite→2026 pose correspondence, owner likeness or shipping art accepted by a numerical 2D study.

## Actual real-ROM 2×2 result (November 1, 2026)

Source-authenticated hosted [Actions #41362035377](https://github.com/gamesbyian/UR-Recomp/actions/runs/41362035377) finished green. The numeric output archive **#13105567229** has ZIP SHA-256 `614b003f586e8f6147322792d53da9be3b15be0a0adf9c893950c1a9889c94a1` and passes CRC validation; the *complete* original 2D report `wheel-fork-2x2-synergy.json` is SHA-256 `cabf78c1e54c02911f7d7c27f210c74e2e0492acf76cb3ab7beaa9bea871611c`. Its pinned summaries are committed under `analysis/data/racer-art4k-actual-original-wheel-fork-interaction-20261101.json`.

| Actual 2026 source candidate | 19 disconnected original 2D binary masks: mean IoU | Boundary Chamfer, physical px | All 35 masks: mean IoU |
| --- | ---: | ---: | ---: |
| Original fork1.0 + wheel1.0 | 0.38192089 | 3.07819813 | 0.46002071 |
| Original fork1.0 + wheel1.1 | 0.41491323 | **2.96055248** | 0.49030377 |
| Source fork1.4 + wheel1.0 | 0.38824958 | 3.08501689 | 0.46835083 |
| **Source fork1.4 + wheel1.1** | **0.42076398** | 2.97186444 | **0.49816283** |

The combination beats wheel1.1 alone on IoU on **19/19 additional binary SHA-distinct 2D masks**, plus 35/35 of the full known original raster set. Mean IoU gains over wheel-only are **+0.00585074** for the 19 additional original shapes and **+0.00785906** over all 35. But the source physical-pixel boundary Chamfer becomes *slightly worse* on the independently SHA-disconnected 19-mask family (2.96055248 → **2.97186444**) and all 35 (2.12007021 → **2.12214899**). These are measured 2D differences and cannot be inflated into original 1994 3D shape, collision, camera or likeness validation.

**Disposition:** the combined geometry is a strong candidate for the same #2832 source model's **optional reviewer A/B**, but the stricter dual-metric original edge/contact gate is not met. Preserve all 1.0× source defaults and present the source-width plus source-mass combination as an unapproved 3D experiment until a detailed source/high-resolution visual review and actual physical/animation correspondence can be established. A fresh hidden 1994 3D camera/viewpoint holdout was not available and is not claimed.
