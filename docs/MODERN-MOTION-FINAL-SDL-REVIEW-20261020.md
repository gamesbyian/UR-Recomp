# Modern menu motion: final Windows SDL pixel review (2026-10-20)

Status: **bounded native evidence pending**. No visual or release approval.

## Decision

PR #2042 merged the real native 60Hz presentation-only selected-row motion, but the 840-paint historical native evidence verified source compositor P6, not final SDL P7. This new bounded witness runs the same genuinely compiled Windows game executable four times with its source-verified retail USA ROM and disposable isolated save roots.

| Real Modern root route | Injected presentation tick | Reduced motion | Expected original SDL P7 RGB |
| --- | --- | --- | --- |
| root-motion-normal-zero | 0 | Off | Visible original-state cursor accent |
| root-motion-normal-eight | 8 | Off | At least one actual changed RGB pixel |
| root-motion-reduced-zero | 0 | On | Static reduced state |
| root-motion-reduced-eight | 8 | On | Pixel-identical reduced state |

Each run uses the existing root-quit native semantic route, real SDL drawable draw ordinal 40 and the previously implemented UI-only fixed-tick override with per-present stepping disabled. Nothing writes guest gameplay memory or changes real game logic. The four captures at one window size must have one source SHA, original executable SHA256, matching actual Windows drawable geometry, native rooted/painted log events, authentic source readback marker and correct lossless P7 bytes.

The standalone qa_modern_motion_final_sdl_pair.py comparator checks those original logged/native-P7 constraints and compares **RGB** pixels, not alpha (Windows native SDL readback can contain legitimate RGB with alpha zero). It refuses missing true animation, reduced-mode pixel movement, mixed binary/source epochs, altered logs, substituted frames, symlinked evidence or incorrect dimensions. The branch-scoped existing Windows QA workflow runs this evidence in 1280x720 and 1024x768 from one compiled executable. It retains original P7, PNG, precise SHA receipts and successful native process logs, never ROMs or save files.

Unit tests intentionally synthesize P7 records only to exercise rejection logic; they cannot validate real Windows art. Actual 1280x720 drawable evidence does not automatically qualify logical 342-wide source viewport before #2043 and #2053 integrate. These static sampled clock poses do not prove natural wall-clock pace, original OBJ/racer likeness, copyright permission, final 4K/PAR or hardware gamepad and audio, and cannot close release- or human-acceptance gates. The independent Windows job and exact-head QA status decide whether even this restricted claim is earned.

Three-project reuse: existing UR/Baldosa native execution and SDL screenshot observer reused. Malmazuke is advisory, not a second original game clock or drawing engine. No new CI job persists beyond this dedicated branch experiment.

## First real native run and corrected capture boundary

The initial genuine Windows run [39541709491](https://github.com/gamesbyian/UR-Recomp/actions/runs/39541709491) built and launched one real PE (SHA256 `b3fe9287a021474acbf20de58a2898499e00cfa5a2f340114402c0addf5adbea`) and captured 1280x720 P7 at all four proposed presentation clock settings. **All four P7 hashes were exactly identical** (`c2013f0bac14f6e9a56228b06fe280b4e54ffc68c09781d3f15f8af09db8f5fe`), so the independent comparator rejected the result instead of declaring animation. There was no guest crash or forged pixel comparison; this failed the positive motion witness before running 1024x768.

The capture harness had reused the normal root-quit smoke 14, which sends a real native gamepad B at guest frame60 and A at frame62. SDL present ordinal 40 is **not** necessarily guest frame40; the screenshot could therefore be sampled after the root left the screen. In the corrected four motion-only routes, the existing native `UR_BALDOSA_MODERN_ROOT_KEY_SMOKE_LAST_FRAME=59` gate suppresses those two scripted exit inputs but retains the same real root, UI, native game clock, script-end quit and saved-state isolation. Other routes are unchanged. A native process reporting any scripted `quit_gamepad` edge is explicitly rejected. Tests now verify the exact four route/pinned-clock/cutoff env combinations.

This is a **causal hypothesis** pending a second actual Windows P7 run. Do not reclassify the first failure as proven post-quit, or claim final SDL visible motion until the corrected real source/PE-bound run passes. Its SHA evidence and failed verdict remain useful negative data.

## Root cause isolated from shared visual grammar

The stock-family shared root painter already fills the selected focus band at `root.x+5` with a **3-logical-pixel full-height blue stripe** of `0xFFA0D0F8`. The merged motion painter wrote a **2-logical-pixel blue stripe in the identical colour and location** on top. Its 10px-versus-12px geometric breathing exposed only the *already blue* unchanged underlying focus stripe, so it had no visible pixels to move. This source-level finding explains why the first P7 comparator correctly rejected four identical screens. The earlier post-quit theory remains unproven and the independent input-cutoff precaution is retained.

The correction in `native/product/modern_menu_motion.hpp` restores the existing focus-band background `0xE0283058` beneath the 2px motion track **before** painting its original constant blue ink. The third static source-blue focus pixel remains untouched. An inset now produces a two-pixel dark notch at the upper/lower edges instead of blue-on-blue; reduced motion or phase zero repaints the entire 12px blue strip. It changes no underlying product focus, 60Hz source model, measured cursor-step table, host clock, palette colour, ROM art, animation frame sequence, guest timing or Authentic mode.

The C++ motion tests now prepaint the exact stock-blue focus stripe and demand distinct final composited pixels between source phase zero/eight, with pixel-identical reduced-motion control across 1x/4x and compact/wide hosts. The 48-frame compiled source-motion oracle independently checks the two-colour fill/notch area and strict no-offscreen behaviour, not only the return value of the paint call. **These synthetic C++ tests still do not replace the second genuine final Windows SDL witness.** No human visual approval or 4K claim.
