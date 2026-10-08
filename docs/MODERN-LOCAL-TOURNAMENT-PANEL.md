# Modern Local Tournament: player-facing panel

Status: **Windows product-host integration with native (Linux desktop) acceptance**. A player can now create a Local Tournament, see its standings and fixtures, and arm their own fixture from the ordinary stock 2P route without any environment hook. Windows-package and multi-session (3+ entrant, relaunch-and-continue) acceptance are still pending; see *Remaining gaps*.

## Where it lives

The panel belongs to the stock `TWO_PLAYER_SELECT` visit (`7E:009F = 3D`) **after** the Modern join overlay has confirmed two distinct profiles. Only then is there a seated pair whose own fixture can be armed before the stock route continues. A bottom-centred hint strip names the working inputs (`F4/PAD <L> TOURNAMENT`, where `<L>` is the live GamepadMap button bound to SNES L — `LB` by default), plus `TOURNAMENT MATCH READY` when the seated pair has an unplayed meeting or `EVENT MATCH: RACE <COURSE>` once a fixture is armed. Authentic mode never shows it.

Input: `F4` or the mapped `L` semantic opens; arrows / D-pad move; Enter or physical pad A confirms; Escape, `F4`, physical pad B, Start or `L` back out. The panel owns the human P1 input word like every other host modal, and freezes guest frames for human sessions (never under `--script`).

## Pages

- **Setup** (no active event, or the active event is complete): the authoritative profile catalog with the seated pair preselected, a course preset (`CRAWLER` … the eighth ordinary tour, or `ALL TOURS`; Hunter is never offered), and `START`. The cursor opens on `START`, so the common case is one key. 2–8 entrants; the ninth toggle is refused.
- **Standings**: the existing 3/1/0 table (`local_tournament_standings`), ranked with shared ties.
- **Fixtures**: every round-robin meeting with `*` played / `>` armed, the selected fixture's course and authoritative result (oriented back to the scheduled entrants when race seats were swapped), and whether the seated pair can play it.

- **History**: one summary row per completed event (`<CHAMPION> WON  N RACERS`, or `TIE` for a shared lead) from `load_completed_local_tournament_history`, i.e. only immutable per-instance definitions plus exact receipt-linked saved pairs; archives that fail validation are counted as `UNAVAILABLE`, never shown. Random instance-ID order is deterministic, not chronological.

Left/Right cycles Standings → Fixtures → History; on Setup, Left/Right off the course row opens History, and Back returns to the page it came from. On a complete event, confirm opens Setup for a new event.

## Authority rules kept

- The pure model `native/product/local_tournament_panel.hpp` holds no files or identity. It returns explicit *create* and *arm* requests; the host performs them only through the existing coordinator (`create_local_tournament_coordinator`, `arm_local_tournament_fixture`).
- Tournament instance IDs and capture-attempt IDs are minted from OS entropy (`mint_local_tournament_token`). Failure refuses the action (`NO SECURE ID`). The fixed IDs remain confined to the older env-armed acceptance route.
- An unfinished event is never replaced from the panel. Replacement is allowed only when the active event is complete, or when its restore was rejected (for example, an entrant profile was deleted).
- Arming requires no pending attempt and a fixture that is unplayed **and** belongs to the seated pair (either seat order). The checkpoint is durable before the panel closes. The existing capture owner still checks the guest-observed course at race start, and a wrong course retires only that attempt while ordinary Records still save. Returning to the settled main menu cancels an armed attempt that was never raced.
- Result authority is unchanged: stock 2P result → `.urrun` + `.urmatch` → fixture receipt → standings.

## Evidence

- `tests/unit/test_local_tournament_panel_cpp.py` (GCC + Clang, `-Werror -pedantic`): presets, setup navigation/cap/roster order, seated-fixture lookup, seat-swap result orientation, 24-cell row bounds.
- `tests/unit/test_local_tournament_panel_host_contract.py`: input ownership, 0x3D + confirmed-pair context, minted IDs only, no replacement of an unfinished event, acceptance uses the production key handler.
- `tests/native/run_modern_local_tournament_panel_acceptance.sh` (manual `multiplayer-match-capture-acceptance.yml` step): two framework pads join and confirm real profiles → `F4` → `START` creates a minted event → Enter arms fixture 0 (`course:01`) → genuine stock 2P race → `CAPTURE_TAGGED` → `FIXTURE_COMMITTED` → a fresh-process checker restores the minted instance and 3/0 standings → a **relaunched** game process rejoins the same pair, opens the panel on the restored complete event's Standings and reaches History with one completed event (`completed=1 unavailable=0`). Passed locally on 2026-10-08 against a Linux desktop build of the current host (minted instance `af699f78…`).

## Remaining gaps

1. Run the panel acceptance on the Windows x64 package, not only the Linux desktop build.
2. Native multi-session continuation of a 3+ entrant event: rotate seated pairs across fixtures and finish the event over several processes. The two-entrant relaunch path (restore → Standings → History) is proven.
3. Completed-event history is a summary list only (no per-event standings drill-down) and is not yet mirrored in Records → Multiplayer/Tournament.
4. A two-entrant event is a single race. Double round-robin or "best of N" would need a schedule-format change, which this slice deliberately does not make.
5. The P2 pad is not filtered while the panel is open (only the P1 human word is host-owned, as on the join overlay).
