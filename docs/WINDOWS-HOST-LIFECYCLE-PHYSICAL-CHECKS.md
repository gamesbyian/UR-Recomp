# Windows host lifecycle: physical check script

**Purpose.** This is a short operator script for exercising the integrated Baldosa product's window/display and controller lifecycle on **real Windows hardware**: real pads, real monitors and a real alt-tab. Hosted CI already drives the same code paths with SDL virtual devices and a scripted minimize. It cannot observe XInput slot behaviour, driver reconnects, multi-monitor hot-plug, DPI changes, monitor mode switches, a real 50 Hz panel, a real GPU device reset, or a remote-desktop/driver-less OpenGL context.

**What this document is not.** It produces *observations*. Attach them as operator notes and logs in a [QA-04 witness packet](QA04-PRIVATE-PHYSICAL-WINDOWS-WITNESS-PACKETS-20261019.md). Independent QA alone judges them; nothing here awards or waives a release gate (see [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json)).

The behaviour contracts live in [MODERN-PRODUCT-LAYER.md](MODERN-PRODUCT-LAYER.md) (controller seats, disconnect/focus pause, display persistence) and [DISPLAY-PRESENTATION-POLICY.md](DISPLAY-PRESENTATION-POLICY.md) (display modes and monitor changes).

## Setup

- Use one exact candidate ZIP and record its source SHA and ZIP SHA256.
- Capture the host log by starting from a command prompt in the extracted folder:
  `run-uniracers.cmd > host-lifecycle.log 2>&1`
  The tokens quoted below appear in that file. `diagnostics/startup.log` is the bounded startup log and does not contain them.
- Record OS build, GPU and driver, every monitor (resolution, refresh rate, scaling %) and every controller (model and connection: USB, Bluetooth, wireless dongle).
- Unless a step says otherwise, play in Modern (the default launcher).

For each check, note **pass / fail / not possible on this hardware** and what you saw. Do not edit logs. Remove personal paths before sharing.

## Controllers

| # | Do | Expect (screen) | Expect (`host-lifecycle.log`) |
|---|---|---|---|
| C1 | Start with no pads. Plug pad A, then pad B. | A drives P1 menus; B can join P2 in the 2P join. | `UR_CONTROLLER_SEAT assign … seat=0`, then `… seat=1` |
| C2 | In a 2P race, unplug **A** and plug it back in. | The race pauses with **P1 CONTROLLER DISCONNECTED**; after replug, **P1 CONTROLLER RECONNECTED**. Resume: A is still P1 and B is still P2. | `UR_BALDOSA_LIFECYCLE_PAUSE reason=controller_disconnect seat=1`; `UR_CONTROLLER_SEAT assign … seat=0 reason=reclaimed` |
| C3 | Repeat C2 with **B** (P2). | The same, naming P2. A is never moved or affected. | `… reason=controller_disconnect seat=2`; `… seat=1 reason=reclaimed` |
| C4 | Hold accelerate/direction on A, unplug A mid-race, resume. | The racer does not keep moving on its own (no stuck input). | `UR_CONTROLLER_SEAT vacate … seat=0` |
| C5 | With A and B seated, plug a third pad C and press A on it. | Nothing happens. C does not steal a seat. | `UR_CONTROLLER_SEAT assign … seat=-1` |
| C6 | Unplug B, then press A on C. | C becomes P2. That claiming press does nothing else. | `UR_CONTROLLER_SEAT claim … seat=1` |
| C7 | Same-model pads only: unplug both, then replug them in the opposite order. | Each pad returns to its own player, or the two swap. Identical pads are indistinguishable; note which happened. | two `reason=reclaimed` lines |
| C8 | Run the Authentic launcher and unplug a pad mid-race. | **No** pause; the guest just loses that input. | no `UR_BALDOSA_LIFECYCLE_PAUSE` |
| C9 | Unplug a pad in a menu (not racing), then start a race. | No pause appears later because of the earlier unplug. | no `UR_BALDOSA_LIFECYCLE_PAUSE` |
| C10 | Generic (unmapped) pad only: with A and B seated, plug a generic USB pad G that the log reports as `unmapped raw joystick`. Unplug B, then press a button on G. | G becomes P2; that press does nothing else. | `UR_CONTROLLER_SEAT spare_kept … raw=1`, then `claim … seat=1` |
| C11 | With A as P1, open the in-game launcher, unplug A, close the launcher; then open it again, plug A back in, close it. | After the first close, P1 has no pad (no ghost seat). After the second, A is P1 again. | `UR_CONTROLLER_SEAT reconcile reason=launcher_returned gone …`; then `… new …` and `assign … seat=0 reason=reclaimed` |
| C12 | No pads plugged in, keyboard only: press Ctrl+L, close the launcher, then quit and relaunch. Race with the arrow keys. Then plug a pad in and race with it. | The keyboard still drives P1 after the launcher and after the relaunch. Once the pad is plugged in, the pad drives P1. | `config.ini` shows `SourceP1 = 2`, yet the keyboard works |
| C13 | Two pads with player lights (DualSense, DualShock 4 or Switch Pro), A as P1 and B as P2: unplug A, plug it back in; then, with A and B both seated, plug in a third pad C. | The lights always match the seats: A shows player 1 after it returns, B player 2; C, left without a seat, does not show player 1 or 2, and A and B keep theirs. | `UR_CONTROLLER_SEAT assign … seat=…` for each pad |
| C14 | Two racer profiles, one pad and the keyboard. Open the 2P join, confirm P1 with Enter, then press A on the pad; pick a racer and press A again. Race. Then open the join again with two pads, confirm P2 on pad B, unplug B, and confirm P1. | The pad joins as P2 and drives P2 in the race while the keyboard drives P1. With B unplugged, P2 shows as not confirmed and no 2P race starts. | `UR_BALDOSA_MODERN_ROOT join_pad_moved from=1 to=2`; `… join_seat_left seat=2 confirmation_cleared=1` |
| C15 | One Xbox pad whose ring light shows player 2 (or 3, 4): with no other pad connected, start the game. Then connect a second Xbox pad and restart with both connected. | The lone pad drives P1 menus. With both connected at start-up, the pad whose ring light shows the lower number is P1. | `UR_CONTROLLER_SEAT assign … seat=0 reason=first_free player_index=1` |

## Focus

| # | Do | Expect | Log |
|---|---|---|---|
| F1 | Alt-tab away mid-race (Pause on Focus Loss is on by default). | The race pauses once. | `UR_BALDOSA_LIFECYCLE_PAUSE reason=focus_loss` |
| F2 | While another window still has focus, resume with the pad. | It resumes and does **not** immediately pause again. | no second `focus_loss` until focus returns and is lost again |
| F3 | Do F1 in exclusive FULLSCREEN. | The game minimizes and pauses. Clicking it restores the same mode. | `focus_loss` |

## Display

| # | Do | Expect | Log |
|---|---|---|---|
| D1 | Options → DISPLAY → **FULLSCREEN**. | A real exclusive mode switch; the monitor may blank briefly. | `UR_DISPLAY fullscreen_mode=exclusive display=… mode=WxH@Hz` (the desktop's own resolution and refresh) |
| D2 | Options → DISPLAY → **BORDERLESS**. | Fullscreen without a mode switch; alt-tab is instant. | no new `fullscreen_mode=exclusive` |
| D3 | From FULLSCREEN press Alt+Enter, then Alt+Enter again. | First press: windowed. Second press: **borderless**, not exclusive. | |
| D4 | On the main Modern menu press Alt+Enter. | Only the window changes; no game or race starts. | no `UR_BALDOSA_MODERN_ROOT stock_requested` |
| D5 | Pick a display mode with Alt+Enter, quit normally, relaunch. | It opens in the mode you picked. | `UR_BALDOSA_OPTIONS adopt_live_display … result=2`; next launch `options_boot display=…` |
| D6 | Windowed: change the size with Ctrl+mouse-wheel (or Ctrl+Up/Down if bound), quit normally, relaunch. | It opens at the size you picked. | |
| D7 | Two monitors, windowed: put the window on monitor 2, then unplug monitor 2. | The window reappears on the primary monitor, reachable by its title bar. | `UR_DISPLAY reconcile reason=… action=rescue` |
| D8 | Two monitors, FULLSCREEN: move the game to the other monitor (Win+Shift+Arrow). | It is fullscreen at **that** monitor's resolution and refresh. | `UR_DISPLAY reconcile … action=remode` |
| D9 | Monitors at different refresh rates (e.g. 60 and 144 Hz): move the window between them with the FPS readout on (`f`). | Pacing follows the new display; game speed is unchanged. | |
| D10 | Monitors at different scaling (e.g. 100% and 150%): with no `WindowScale` in `config.ini`, move a windowed game from the small-scale monitor to the large-scale one and back. Repeat with `WindowScale = 2`. | Unset: the window grows on the large-scale monitor and shrinks back on the other, staying about where it was dropped, and `config.ini` still says `WindowScale = 0`. Set: the size is kept. Both: the window still fits on screen. | `UR_DISPLAY reconcile reason=display_scale_changed action=follow_dpi scale=…->…`; `… action=rescale` if a set size overflowed |
| D11 | Two monitors, windowed: move the window to monitor 2, quit normally, relaunch. Repeat in FULLSCREEN. | It reopens on monitor 2 (windowed: at the same spot; fullscreen: at monitor 2's mode). | `UR_DISPLAY placement saved=1 display=…`; next launch `UR_DISPLAY placement restored display=…` |
| D12 | After D11, unplug monitor 2, then launch. | It opens on the primary monitor, fully reachable. | `UR_DISPLAY placement saved_display_missing name=…` |
| D13 | Windowed: maximize the window (title-bar button or Win+Up), quit normally, relaunch. Then un-maximize. | It reopens maximized on the same monitor; un-maximizing returns it to its earlier windowed spot. | `UR_DISPLAY placement restored … maximized=1` |
| D16 | On a 50 Hz display (a PAL TV, or a monitor set to 50 Hz), with VSync On, time 60 seconds of a race against a stopwatch, using the in-race clock. | The in-race clock keeps pace with the stopwatch, not about 17% slow. | `UR_DISPLAY vsync panel_hz=50.000 … wait=no` |
| D17 | During a race, reset the graphics driver with Win+Ctrl+Shift+B (or, on a hybrid-GPU laptop, dock or undock it). | The picture comes back within a second and the race continues; no lasting black window. | `UR_DISPLAY render_device_reset` then `… texture_recreated=…` |
| D18 | On a 4K or 150%/200% scaled display, with no `WindowScale` in `config.ini` and no `window-placement.txt`, launch the game; then open and close the in-game launcher without changing anything, quit and relaunch. | The window opens at a comfortable size for that display, not a small 640×480 box, and fits on screen. It reopens at the same size, and `config.ini` still says `WindowScale = 0`. | `UR_DISPLAY default_window_scale content_scale=… scale=…` |
| D14 | Two monitors, windowed on monitor 2: open the in-game launcher, unplug monitor 2, close the launcher. | The game window is on the primary monitor, reachable. | `UR_DISPLAY reconcile reason=launcher_returned action=rescue` |
| D15 | Over Remote Desktop (or on a PC without a GPU driver), start a race and open the in-game launcher. | Either the launcher opens normally, or it does not appear and the game simply carries on. The game never closes or crashes. | `[launcher] UR_LAUNCHER_GL unusable version=…` and `in-game launcher: action=2` when refused |

## Reporting

Per tester, attach:
- `host-lifecycle.log`;
- the hardware inventory above;
- the per-check results.

Include every failure as observed, and mark any check the hardware cannot perform as `not possible on this hardware`.

A failing check is a product defect report for the Windows host lane. Open an issue citing the check number, the candidate SHA and the log lines.
