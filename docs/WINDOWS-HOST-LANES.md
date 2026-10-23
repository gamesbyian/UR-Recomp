# Windows host lanes (Claude): ownership and interfaces

Two manually dispatched Claude lanes work on the integrated Baldosa product's
SDL3 desktop host, alongside the scheduled board in
[HOURLY-AGENT-LINES](HOURLY-AGENT-LINES.md). This page lets scheduled agents
see what those lanes write, so they can avoid concurrent edits. The board,
the [work queue](WORK-QUEUE.md) and the [release ledger](RELEASE-QUALITY-LEDGER.json)
keep their own authority; nothing here assigns work or awards a gate.

## Files the lanes write

| Lane | Files |
|---|---|
| Display and window lifecycle | `native/product/display_window_lifecycle_policy.h` (+ `tests/native/display_window_lifecycle_policy_test.cpp`), `tools/baldosa_sdl_display_lifecycle_spike.py`, `tools/baldosa_session_end_spike.py`, `tools/run_baldosa_display_lifecycle_acceptance.py`, `tools/run_baldosa_window_placement_acceptance.py`, `tools/run_baldosa_default_window_scale_acceptance.py`, `tools/run_baldosa_slow_panel_vsync_acceptance.py`, `tools/run_baldosa_render_reset_acceptance.py`, `tools/run_baldosa_launcher_gl_fallback_acceptance.py`, `tools/run_baldosa_session_end_acceptance.py` and their unit tests |
| Controller lifecycle | `native/product/controller_seat_assignment_policy.h` (+ native test), `tools/baldosa_sdl_controller_lifecycle_spike.py`, `tools/run_baldosa_controller_lifecycle_acceptance.py`, `tools/run_baldosa_keyboard_pad_join_acceptance.py` and their unit tests |
| Both | the matching steps of `.github/workflows/baldosa-windows-native-bridge.yml`; [WINDOWS-HOST-LIFECYCLE-PHYSICAL-CHECKS](WINDOWS-HOST-LIFECYCLE-PHYSICAL-CHECKS.md); the host sections of [DISPLAY-PRESENTATION-POLICY](DISPLAY-PRESENTATION-POLICY.md) and [MODERN-PRODUCT-LAYER](MODERN-PRODUCT-LAYER.md) |

**Shared with line 3 (input):** `tools/baldosa_native_modern_root.cpp`. The
lanes touch only its seat-move hooks (`join_return_moved_pad`,
`promote_lone_seat2_pad`) and test-only key-smoke modes 15–18. The join
confirmation and admission logic belong to line 3.

## Interfaces other code may rely on

- The host seats pads through `ur_controller_seat_choose`. A pad never steals
  an occupied seat. It never skips a lower free seat for its SDL player index.
  Pads found together are seated gamepads first, then by player index.
- Modern reads seats through `snesrecomp_desktop_product_seat_source` and may
  move a pad with `snesrecomp_desktop_product_seat_move`. Nothing else changes
  seats.
- The exit-time saves run once, through `UrPersistAtExit`: from the ordinary
  exit, from `WM_ENDSESSION`, or after a console close or Ctrl+C/Ctrl+Break.
  New exit-time persistence belongs inside that block, not after it.
- Log tokens used by runners and physical checks:
  - `UR_CONTROLLER_SEAT …`
  - `UR_DISPLAY …`
  - `UR_SESSION_END …`
  - `UR_BALDOSA_MODERN_ROOT join_pad_* / lone_pad_promoted`

## Open decisions

- [#2334](https://github.com/gamesbyian/UR-Recomp/issues/2334): pad input
  while the window is unfocused. Overlays such as the Xbox Game Bar currently
  leak presses into the game.

Every acceptance run above uses hosted Windows with SDL virtual devices. Real
pads, monitors, sign-out and GPU events are the physical checks.
