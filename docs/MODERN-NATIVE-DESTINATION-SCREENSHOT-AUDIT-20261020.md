# Real Windows Modern destination screenshot review | 2026-10-20

**Status: automation-level source/display evidence acquired; final visual approval withheld.** This is an independent in-game rendering review, not trailer or promotional artwork.

## Exact witnessed native candidate

- CI: [Modern integrated visual native SDL rehearsal, run 39528321957](https://github.com/gamesbyian/UR-Recomp/actions/runs/39528321957) (pass)
- [Unmodified SDL drawable PNG/P7/log/JSON artifacts](https://github.com/gamesbyian/UR-Recomp/actions/runs/39528321957/artifacts/12314776230), retained for 7 days
- GitHub Actions checkout source SHA: `24b71133e0e4db777505d125fbf31e029eecfc66` (merge-test revision; retain PR parent/source refs separately)
- Exactly one Win32 native AOT executable across all five route processes, SHA256: `ba747b9eaa0e79bb21bd85835e4291828b6bc1227c4d2d6da12ef67ea87ca32a`
- Real SDL3 `SDL_RenderReadPixels` output **1280×720** for all five, converted P7→PNG losslessly with file-level SHA256, zero crop/relabel/AI repaint. Native Modern destination logs independently show `raster=342x224 root=11,10,320,204`. Keyboard/P1 semantic host routes were real but simulated at the input boundary, not physical-controller approval.
- The same integration also captured genuine compact 1024×768 Windows scenes using `raster=256x224 root=8,10,240,204` ([earlier full modal family, run 39518329126](https://github.com/gamesbyian/UR-Recomp/actions/runs/39518329126)). This matters: these are **actual distinct 4:3/16:9 frontend geometries**, not a relabelled wide screenshot inside a narrow letterbox.

| Captured native destination | Exact semantic route and stage | Original 1280×720 PNG SHA256 prefix | Source-bound observation |
| --- | --- | --- | --- |
| Practice course picker | `practice-picker-p1`, `practice-picker` | `105f751c1de8` | Source menu offers Dragster, Crawler/Race and 20 unlocked courses; Up/Down course, L/R tour, A/Back visibly differentiated |
| Multiplayer unrecorded warning | `multiplayer-unbound`, `multiplayer-unrecorded-warning` | `b6f94325c4f5` | Explains two named racers required for recorded 2P; stock 2P still allowed; A consent and B Back |
| Records read-only archive | `records-keyboard`, `records-1p` | `f1b704bb084d` | 1P/2P headings, no named profile status, no replay claim and page/back legend; no fabricated earned record |
| Options before changing display | `options-open-p1`, `options` | `81479c73b50b` | Explicit 16:9 opened state before the existing mode-12 host action changes Windowed→Borderless; real Display/VSYNC/Volume/Controls/Defaults rows |
| First racer selection | `profile-first-p1`, `profile-first` | `740e8d2ec8b1` | Preset Mike, saved for next launch; avoids claiming a live guest profile switch and preserves explicit restart notice |

These stage labels were observed in the **same respective native process log** as each SDL capture. The QA driver additionally verifies the original source/capture bytes and refuses a requested 1280×720 output if SDL produces a different size.

## Pixel review

The five captured screens are consistently composed and text is visible within the same safe rectangle at 16:9. The source-derived yellow headings, grey metadata, light-blue selected rows and blue Back/action hints remain consistent. The old engineering-modal stack defects visible on prior Windows captures (selection bar protruding outside an opened child, underlying root buttons duplicated beneath a child) are **absent in the inspected new screenshots**. Practice/Multiplayer/Records/Options/first-racer show a single dominant content plane with no obvious overlapping commands. The distinct 4:3 screenshots also show the same general hierarchy without cut-off side columns.

A separate **native C++ composition regression** in destination PR #2040 draws the actual shared root shell and actual destination view sequentially into a simple RGBA raster at 256 and 342 source widths, asserting the old root blue focus bar/command footer is occluded in all five child families. It is a geometry/layering test and has no license to approve font fidelity, animation or final appearance.

### Still open, explicitly uncredited

**Design**: Current graphics remain predominantly neutral panels/checkerboard; the original menu's source-derived bitmap font sheets, true spinning OBJ cursor, background layers and appropriate racer/track illustration still await licensed integration and owner visual review. Green CI is not proof of a polished final 4K art direction. Styling of the shared root and title remains with their separate visual agents.

**Source gameplay**: Screenshot states for paired named 2P join/READY, earned 1P and 2P Records, fresh process profile re-selection and live paused Options must be captured from real reachable sessions on one integrated source epoch. Empty/no-profile and unrecorded-warning screenshots do not prove those different states.

**Human/device**: Physical P1/P2 pads, widescreen television overscan/true 4K, audible cues, tab order/keyboard access where applicable, uncoached usability and visual approval remain holds. Authentic SDL controls were separately photographed but source guest pixel-exact parity still requires independent gate evidence.

No screenshot was fabricated, redrawn or added to the repository, no ROM/private profile was archived, and **no release gate credit** is awarded by this review.
