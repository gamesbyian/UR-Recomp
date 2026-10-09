# QA-05 / QA-09 Modern shell implementation: evidence and remaining gates

Status: **implementation candidate, not release acceptance** (2026-10-08).
Scope: frontend input routing, visible root, existing host/guest authorities.
Source branch: `qa05-modern-root-and-restart-ownership-20261008`.
Issue references: [#890](https://github.com/gamesbyian/UR-Recomp/issues/890), [#1053](https://github.com/gamesbyian/UR-Recomp/issues/1053).
Authoritative readiness remains `RELEASE-QUALITY-LEDGER.json`, `QA-PLAYER-JOURNEYS.md`, and `MODERN-UI-VISUAL-FIDELITY.md`. Do **not** infer shipping readiness from these changes.

## Implemented candidate

- Render five real, focusable root rows (Play, Practice, Multiplayer, Records, Options) using the existing `ModernRootMenu` typed focus model. The established host controllers remain exclusive: Tour action, Practice picker, completed-run Records, frontend Options, global Racer/Profiles, guest 1P/2P stock selection. The root carries **no profile/guest/save/replay authority**.
- Human Modern sessions own the shell on settled stock `MAIN_MENU` (`009F=D7`); existing `--script` reference/acceptance routes and Authentic bypass this root. The established `frontend_modal_hold_wanted()` owns frozen guest frames; stock-entry routes explicitly release the hold and use existing relative input transport. 1P and 2P cursor handoffs are bounded with the established 60-observation settle policy and authoritative `009B` selection. No guest SRAM writes from root presentation.
- P1 physical pad A confirms, B backs out, X enters Profiles; mapped P1 directions select rows, consistent with existing fixed physical host Confirm/Back. Keyboard Up/Down, Return, Escape and F2 access work. Existing F1/F3/F5/F6/F7/F8/F9/F10 convenience shortcuts remain; F-keys are never necessary to discover a root destination.
- Back opens a separate, cancellable desktop Quit confirmation. While confirming, all other root actions are consumed; selecting an entry preserves the selected row across Back from nested host modals. Unrecognized physical input is withheld from the guest.
- Original-derived BG2 palette roles, dimensional yellow regional title/shadow, blue selected row, contextual details, profile name and clear pad/keyboard footer are used for the root. This is a **first-pass host ASCII treatment**, not a substitute for stock font/animation/SFX and actual TV-distance/4:3/16:9 image acceptance.
- Keyboard Return confirming paused host Restart arms `ModernRestartKeyRelease` before guest restore/unpause. The filter holds the default mapped guest Start bit (0x1000) while Return remains physically pressed *and* until a zero-Start human-word sample after physical release. Unrelated guest bits remain untouched. Paused host input ownership is explicit to cover release suppression on other modal confirmation edges. `UR_RESTART_INPUT` exposes raw P1 word, filtered guest word, physical Return status, release wait and host ownership for the first 12 observed samples.

## Available compact local oracles

```bash
# After building the native SDL desktop game with the canonical USA ROM:
bash tests/native/run_modern_root_acceptance.sh \
    /path/to/UniracersSNESRecomp \
    reference/roms/retail/Uniracers_USA.sfc /tmp/ur-qa09-root

# Cheap release barrier unit (independent of gameplay/audio):
g++ -std=c++17 -Wall -Wextra -Werror -pedantic \
    -I native/product tests/native/modern_restart_key_release_test.cpp \
    -o /tmp/modern_restart_key_release_test
/tmp/modern_restart_key_release_test
```

The root smoke uses **non-scripted SDL keyboard events** in real desktop processes and attempts Practice/Profiles/Records/Options/Back/Quit, plus separately Play and Multiplayer guest cursor handoffs. It asserts the application's own route and hold diagnostics. No same-mode `--script` input is allowed to masquerade as a human Modern root test. These checks are supplementary and **have not yet been executed on this source branch**. Existing native UI/Practice/Records/Options/Profile/Restart tests must remain green on the integrated revision.

## Required candidate acceptance still outstanding

| Journey / gate | Required independent evidence | Current classification |
| --- | --- | --- |
| #890, J-12/J-17 | Package built from **this commit**. With *default* keybindings, press Return to confirm Restart, hold/release/repress, inspect first resumed human word. No guest Start from confirmation; ≥5 of 5 audible Restart tails and separate uninterrupted controls. Capture actual audio samples and Windows physical key state. | **Not independently executed; defect not closed** |
| #1053, J-01/J-19 | Exact Windows portable ZIP/hash; fresh save root; one controller only, uncoached first-run onboarding/profile → Play/Practice → real result → repeat/Records → Quit/relaunch. Confirm correct saving, focus restoration, pad prompts, meaningful failure text. | **Not independently executed; candidate routes only** |
| J-06/J-11/J-12 | Two distinct pads and real Windows process. Hold P1/P2 buttons while entering/exiting nested options/tournament/Records and while confirming Quit/Restart. Check guest frame hold, guest word release, seat ownership and fresh press. | **Not independently executed** |
| QA-09 visual | Real captured root/Profile/Options/Practice screens at 4:3 and 16:9, density 1x/4x, on Windows; compare stock reference for palette, typography, cursor, SFX, legibility and controller labels. | **Partial art implementation; no visual gate** |
| Authentic isolation | Run stock `--script` comparisons and human Authentic navigation; no Modern root, no guest logic/credit/graphics timing changes. | **Source design guard, no fresh integrated result** |

Windows audio probe `.github/workflows/windows-modern-restart-audio-probe.yml` currently downloads the latest successful **main** package, not the PR candidate. Its result **cannot** certify this branch's fix. For #890, use a package whose build manifest matches this exact head commit and repeat the physical Return/default binding probe, rather than borrowing an older artifact.

**Stop condition:** merge only after a successful native/Windows candidate build and review, with explicit unfinished audio, physical pad and aesthetic gates recorded. Do not mark `RELEASE-QUALITY-LEDGER.json` QA-05 or QA-09 passed on component-only evidence.
