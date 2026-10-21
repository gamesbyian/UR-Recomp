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
