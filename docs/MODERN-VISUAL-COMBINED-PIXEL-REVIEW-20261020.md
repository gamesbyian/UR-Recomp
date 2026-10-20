# Combined native Modern visual pixel review | 2026-10-20

**Source and evidence, not visual approval.** The first real SDL3 final-drawable pass [Windows run 39481197322](https://github.com/gamesbyian/UR-Recomp/actions/runs/39481197322), working PR integration head `6cfda204000f083424a73ab29e52981907da44bf`, GitHub ephemeral PR merge checkout `28128c3492c38d7aa01512b89e1cb7e142bbf81d`. Every screenshot uses the identical actual Windows PE SHA256 `e25fd8e5dea2b6e1752c39376361336cc59824df081361fbf0a4388e90a2c9b1`. Host SDL3 readback bytes were preserved as source P7 and independently converted losslessly to PNG. This is not physical 4K or an artistic decision.

| Real Windows capture | Actual SDL output | Distinct RGBA pixels | Visible/total pixels | Source finding |
| --- | --- | --- | --- | --- |
| Modern root, explicit wide | 1280×720 | 10 | 783,492 / 921,600 | Recognizable five entries, cursor, original-derived palette; right context shows **TOUR AND CONT** (truncated), still checkered engineering background |
| Modern root, 4:3 drawable | 1024×768 | 10 | 500,076 / 786,432 | A **342-wide letterboxed root** with substantial top/bottom black borders; this does not exercise true 256-wide compact frontend |
| Records keyboard | 1024×768 | 10 | 500,076 / 786,432 | Actual 1P/2P modal, selected row and explicit read-only/no-replay/status copy; underlying root cursor/gutters still peek around dialog |
| P1 Options | observed 1024×768 | 10 | 500,076 / 786,432 | Actual adjustable settings, focus, saved status and Back text; recorded output size changed from requested 1280×720 |
| First racer/profile | 1280×720 | 10 | 783,492 / 921,600 | Actual stock preset and next-launch save guidance; underlying root selection and status footer remain visible around centered modal |
| Authentic 1280×720 | 1280×720 | **1** | **0 / 921,600** | **All pixels exactly RGBA(0,0,0,0)** at SDL draw #40. Invalid visual control, despite process exit=0 and no Modern opening marker |
| Authentic 1024×768 | 1024×768 | **1** | **0 / 786,432** | Same all-transparent frame #40. Invalid visual control, no proof of original output likeness |

'Visible' here means alpha greater than zero; the Modern snapshots use alpha values 0, 192, 224 or 255. Colour count derives from complete lossless PNG pixel bytes, not a subjective approximation.

## Repairs and live qualification

1. A new real Windows capture test at the current combined-head candidate has an explicit **nonblank varied stock-frame predicate**. It samples later SDL draw **#240** for Authentic instead of #40 and fails if transparent/uniform. The first black images remain in earlier immutable artifacts for regression diagnosis; they must not be retrospectively accepted.
2. A native callback in this rehearsal now reads the *actual SDL drawable* provided by the pinned Baldosa host's `PreparePpuFrame` and chooses **256×224** for compact (aspect at most 3:2, including 1024×768) or **342×224** widescreen. Pure native C++ geometry tests pin both paths. This affects only visible Modern UI, not Authentic guest simulation. A fresh *same-head* Windows capture is required before asserting the compact canvas visibly works.
3. #2038 shared style already fixed the two-line root-preview truncation in a later independent owner branch. Its code was not silently backported to the first captured combined executable. Refresh that source head and run combined tests before the two-line preview earns captured evidence.
4. Child destination typography and source-backed business logic are substantially implemented and native reachable; however the dominant grey checkerboard, generic dialog backing, original-font shapes and original OBJ cursor remain clearly pending original-derived art integration/human review. **No screenshots here justify calling the menu aesthetically complete.**
5. Still no live 2-controller physical device, audible pause/confirmation, genuine physical 4K, uncoached navigation, source-raster/Authentic pixel parity or human original-art approval. The title's source-PAM artifact is not an SDL-final-output image.

References: [SDL root and size comparison](https://github.com/gamesbyian/UR-Recomp/actions/runs/39481197322/artifacts/12291806851), [Records/Options/profile navigation](https://github.com/gamesbyian/UR-Recomp/actions/runs/39481197322/artifacts/12290464062), [blank Authentic controls](https://github.com/gamesbyian/UR-Recomp/actions/runs/39481197322/artifacts/12291731935), [original native PE](https://github.com/gamesbyian/UR-Recomp/actions/runs/39481197322/artifacts/12290464131).

This report is a reviewed historical exact candidate, never proof of a newer head. **Admission remains unchanged: release_gate_credit=0, human_visual_approved=false, authentic_isolation_approved=false.**
