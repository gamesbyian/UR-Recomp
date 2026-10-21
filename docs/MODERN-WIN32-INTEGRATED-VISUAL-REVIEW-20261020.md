# Real Win32 visual review: Modern root and destination controls

**Status: independent inspection of retained Windows SDL3 output, historical candidate, NOT final visual acceptance.**

## Immutable evidence

Observed integrated Windows pipeline: [real SDL output run 39481197322](https://github.com/gamesbyian/UR-Recomp/actions/runs/39481197322), PR #2053 then-head `6cfda204000f083424a73ab29e52981907da44bf` with GitHub PR merge checkout `28128c3492c38d7aa01512b89e1cb7e142bbf81d`. The Windows executable's SHA-256 was `e25fd8e5dea2b6e1752c39376361336cc59824df081361fbf0a4388e90a2c9b1` in every capture receipt. Evidence is actual native SDL drawable readback/CRC-checked PNG, not a newly generated illustration.

- [Root 1280×720 and 1024×768 Windows PNG/P7](https://github.com/gamesbyian/UR-Recomp/actions/runs/39481197322/artifacts/12291806851)
- [Opened Records, Options, first-racer dialogs](https://github.com/gamesbyian/UR-Recomp/actions/runs/39481197322/artifacts/12290464062)
- [Authentic-mode 1280×720 and 1024×768 captures](https://github.com/gamesbyian/UR-Recomp/actions/runs/39481197322/artifacts/12291731935)
- [Baseline Modern root native frame](https://github.com/gamesbyian/UR-Recomp/actions/runs/39481197322/artifacts/12291702039)
- [Exact tested Win64 executable](https://github.com/gamesbyian/UR-Recomp/actions/runs/39481197322/artifacts/12290464131)

The older images must remain tagged with the **older source**. They are not photographic evidence of newer integration head `23d15cebb6ffbf6051eb86051e6b943920449c65` or newer upstream PR heads.

## Inspection and code actions

| Observed screenshot | Supported finding | Disposition / next check |
| --- | --- | --- |
| Modern root 1280×720 | Five readable selectable options; selected Play and wide preview separated; panel retains pronounced temporary monochrome checkerboard and plain block layout. | Shared-style #2038/title #2043 own artist-approved skin. Modern destination lane must not counterfeit source art or alter Authentic. |
| Records at 1024×768 | New modal heading, rows and read-only messages appear. **The old root's `A/ENTER SELECT B/ESC QUIT` and racer shortcut remain visibly printed beneath the active child**, conflicting with destination Back instructions. Root focus blue edge also escapes into the left gutter. | Fixed as an **opaque Modern-only body scrim** in #2040 and current #2053; masks root interactive body from y+40 to root bottom while retaining outer frame, profile identity and modal controls. Native 4:3/342-width geometry test added. Await an exact-head SDL re-capture. |
| Options at 1024×768 | Modal operates real host settings (selected Volume 90%, displayed saved state) but also shows `B/ESC QUIT` below `B BACK`, which is not accurate inside the child. | Same body scrim fix and regression test. |
| First-racer at 1280×720 | Stock preset and next-restart saved state shown; parent footer's `A/ENTER SELECT` and X setup shortcut still show beneath modal, misleading about focus. | Same body scrim fix; preserve next-boot persistence rather than suggesting immediate active racer switch. |
| Authentic at 1280×720 and 1024×768 | Captured **completely black drawable** at the selected early frame. Process logs independently confirmed Authentic mode startup and no Modern root paint. | This is useful as a mode-guard witness **only**. Black frames cannot establish visual/guest-frame parity or stock aesthetic. Later source-aligned guest frames and CRC comparison remain mandatory. |
| Root at 1024×768 | A widescreen logical frontend is visibly letterboxed inside 4:3 output on this **older executable**. | Later title agent now implements `modern_title_logical_width(drawable_width, drawable_height, true)` to select 256 or 342. Require **new exact combined-head native captures** proving true 4:3 source selection before treating fallback as accepted; keep authentic guest mode unchanged. |

All screenshots are static hosted Windows tests with no physical controllers, sound output, real monitor, human visual sign-off or genuine historical source font/rotating cursor atlas embedded. Green SDL readback validates that a PE presented pixels and exercised semantic input routes, **not** finished visual quality.

## Current acceptance sequence

1. On the latest merged rehearsal head, execute full ROM-free C++ contract; all Python files must parse and pass. A pair of Play route syntax errors introduced in a newer QA driver were repaired in the integration branch without loosening any route assertion.
2. Produce new exact-head 1280×720, 1024×768, Records/Options/profile, Play source handoff and Authentic screenshots. Verify modal **root-only text and selection** are absent and both logical 256×224 and 342×224 source geometry occur in their intended host output modes.
3. Exercise Practice, Multiplayer P1-first/P2-first/readiness/unrecorded branch, and live paused Options on the real native binary. Assert focus/controller ownership via logs and the actual captured pixels, not only ROM-free synthetic fixtures.
4. Obtain source-verified original font/OBJ/cursor and surrounding asset approval. Inspect composition at multiple physical display densities, especially high-density 4×, before signing off any artistic or hardware acceptance.

This document does not change release ledger credits. No trailer/promotional footage was touched.
