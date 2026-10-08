# Pause-menu controller navigation contract

## Current implementation audit

The live desktop host already has most of this slice. `ur_uniracers_modern_system_gamepad_button` maps Start to pause toggle, D-pad Up/Down to the same pause-menu actions used by keyboard Up/Down, A to activation, and B to cancel. Options also accept D-pad Up/Down and A, while B/Start closes a host subview. Button releases are consumed while paused, which prevents a release edge from falling through to guest input.

The remaining gap is therefore deliberately small: normalize these physical bindings behind semantic host navigation actions, add Left/Right adjustment for option rows that support cycling, and prove input ownership/unlatching explicitly. Do not build a second controller subsystem.

## Paused presentation

The pause family is drawn by the title's `system_overlay` while the guest is frozen, but the pinned desktop host's paused loop presents nothing new. Until `tools/patches/snesrecomp-paused-overlay-present.patch`, every Modern paused surface (pause root, Options, Controls, Run Data, Records, Quit confirmation) was therefore invisible on screen: the window kept the last race frame while diagnostics reported the menus open. The patch keeps a copy of each presented field taken *before* the title overlay and, when a title opts in with `snesrecomp_desktop_set_paused_overlay_presentation(1)`, re-presents that backdrop (nearest-scaled to the current presentation density) plus the current overlay on every paused loop iteration without running guest code. Modern opts in at session creation; Authentic keeps the framework default. A density or Widescreen change made from paused Options rescales the frozen backdrop until the guest resumes. `SNESRECOMP_PAUSED_OVERLAY_DUMP` captures the latest paused present, and Native UI evidence requires `tools/check_paused_overlay_dump.py` to find the shared modal panel over the frame centre after its paused Options journey. The paused Records/Local Runs shortcut hint belongs to the pause root and yields to open subviews.

Pause-menu **Restart** restores the race-start anchor and then resumes the session, matching results Retry and Ctrl+R. It previously left the session paused with the menu over the stale pre-restart frame until the player also chose Resume.

### Main-menu modal hold

The stock MAIN_MENU starts its attract demo after ~503 idle frames, and host modals own human input there, so the attract timer used to expire underneath them: after ~8 s the title left MAIN_MENU and the Quick Practice picker, Tour Progress, frontend Options/Controls and the Tour action surface closed as stale while the player was reading them, and the first-run Welcome panel vanished into the demo. `tools/patches/snesrecomp-host-frame-hold.patch` adds `snesrecomp_desktop_set_frame_hold()`, which freezes guest frames and audio exactly like a pause without being one (`snesrecomp_desktop_is_paused()` and the session phase are unchanged), and presents the frozen field plus the current overlay through the paused-presentation path. `frontend_modal_hold_wanted()` engages it only in Modern, on the settled main menu, while one of those modals is open and no Practice/Tour route needs guest frames; it is re-evaluated on every present, so it releases as soon as the modal closes. The hold applies to human-driven sessions only: `--script` harnesses and the in-host acceptance drivers advance on emulated frames and drive these surfaces themselves (Next Event, picker, overview, frontend Options), so a held frame would stall them, just as scripted input bypasses the human-input filter (`snesrecomp_desktop_script_active()`).

## Authority boundary

- Guest controller state remains authoritative for Uniracers simulation.
- While the modern pause UI owns focus, navigation input is consumed by the host product layer and must not leak into the guest input mask.
- Authentic mode remains stock: modern pause/controller policy is inert.
- Existing keyboard navigation remains a control path and must retain equivalent menu semantics.

Non-pause host surfaces (Welcome/onboarding, Tour action, Quick Practice picker, results navigation, profile picker, local-multiplayer join and their routes) share the same final-human-word boundary. `native/product/modern_host_input_release_latch.hpp` owns its closing-edge rule: while a surface owns input the whole P1 word is withheld, and every bit still held when the surface closes stays withheld until that bit is released. A one-frame suppression was insufficient: on the stock MAIN_MENU, dismissing the first-run Welcome panel with a held Enter/Start reached the guest a few frames later and selected 1P (`0xD7 → 0x3C`). The latch never synthesizes input; scripted/reference input bypasses the filter and Authentic mode is unchanged.

## Minimal input vocabulary

Use semantic host actions: Up, Down, Left, Right, Confirm, and Back. The SDL3 adapter translates physical keyboard/gamepad events into those actions; title/product state must not depend on SDL button constants.

Up/Down move selection. Left/Right adjust an option where the existing option contract supports cycling. Confirm activates or toggles the selected item. Back leaves a subview or closes the pause surface according to the existing lifecycle.

## Acceptance

Native tests must prove:

1. controller and keyboard actions reach the same host menu transitions;
2. consumed pause-menu controller actions do not change the guest input mask;
3. closing pause returns control cleanly without a stuck or latched guest button;
4. Authentic mode ignores the modern controller-navigation policy;
5. Restart, Options, Quit, Controls and Run Data behavior remains unchanged except for the normalized navigation source;
6. Left/Right only affects option rows with a defined adjustment and fails inertly elsewhere.

## Non-goals

Do not add rebinding, controller glyph selection, hot-plug UX, per-controller persistence, or a frontend redesign in this slice.
