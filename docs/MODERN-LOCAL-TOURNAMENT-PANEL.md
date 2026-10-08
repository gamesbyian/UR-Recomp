# Modern Local Tournament: player-facing panel

Status: **player-facing panel and one-fixture Windows packaged acceptance proven** (#946/#964). A player can create a Local Tournament, see standings/fixtures and arm a seated fixture through ordinary stock 2P. Three-plus-entrant multi-session completion and fully raced multi-leg continuation remain release-level QA gaps; see *Remaining gaps* and the QA-03 gate.

## Cross-session release-quality boundary (2026-10-08)

One complete packaged 2P race and relaunch is **demonstrated**, as recorded below, but neither the 3+ entrant multi-session event nor actually completing a 2–3-leg meeting from the second results screen is accepted end to end. These are P0 QA-03 gates J-04 and J-05 in [QA-PLAYER-JOURNEYS.md](QA-PLAYER-JOURNEYS.md). The currently unfiltered P2 word while the panel owns P1 and freezes guest frames creates a *suspected* post-close held-button leak, **not a confirmed bug**; J-06 must measure first resumed guest frame, P2 release/re-press, rejoin/disconnect and any visible unintended stock action. Do not claim resolved until host+native acceptance demonstrates actual P2 ownership on both sides of the panel lifecycle.

## Where it lives

The panel belongs to the stock `TWO_PLAYER_SELECT` visit (`7E:009F = 3D`) **after** the Modern join overlay has confirmed two distinct profiles. Only then is there a seated pair whose own fixture can be armed before the stock route continues. Because `0x3D` is the stock *PICK A PLAYER* rider grid, the hint is a single top-centred row over the decorative title, never over a rider name: `F4/PAD <L> TOURNAMENT` (`<L>` is the live GamepadMap button bound to SNES L, `LB` by default), `MATCH READY  F4/PAD <L>` when the seated pair has an unplayed meeting, or `EVENT: RACE <COURSE> F4/<L>` once a fixture is armed. Authentic mode never shows it.

Input: `F4` or the mapped `L` semantic opens; arrows / D-pad move; Enter or physical pad A confirms; Escape, `F4`, physical pad B, Start or `L` back out. The panel owns the human P1 input word like every other host modal, and freezes guest frames for human sessions (never under `--script`).

The panel is also available on the same pair's **ordinary 2P results screen** (`0xF9`) once its capture has settled, so a multi-leg event continues without leaving the session: there the results notice alternates with `F4/PAD <L> NEXT MATCH` while the seated pair still has an unplayed meeting.

## Pages

- **Setup** (no active event, or the active event is complete): the authoritative profile catalog (`(X)` selected) with the seated pair preselected, a course preset (`CRAWLER` … the eighth ordinary tour, or `ALL TOURS`; Hunter is never offered), `MEET EACH < 1X..3X >` legs (two racers on 3X is a best-of-three), and `START  N RACES`. The cursor opens on `START`, so the common case is one key. 2–8 entrants; the ninth toggle is refused.
- **Standings**: the existing 3/1/0 table (`local_tournament_standings`), ranked with shared ties.
- **Fixtures**: every round-robin meeting with `*` played / `>` armed, the selected fixture's course and authoritative result (oriented back to the scheduled entrants when race seats were swapped), and whether the seated pair can play it.

- **History**: one summary row per completed event (`<CHAMPION> WON  N RACERS`, or `TIE` for a shared lead) from `load_completed_local_tournament_history`, i.e. only immutable per-instance definitions plus exact receipt-linked saved pairs; archives that fail validation are counted as `UNAVAILABLE`, never shown. Random instance-ID order is deterministic, not chronological.

**Result notice:** when a fixture is credited, the stock 2P results screen shows one bottom-band row (rows there end near y=200; title and course own the top): `CHAMPION: <NAME>` / `EVENT TIED ON N PTS` for a completed event, else `LEADS: <NAME> N PTS played/total` or `LEAD SHARED …`. It is derived from receipt-backed standings only and retires as soon as that stock screen ends. Native acceptance asserts `RESULT_NOTICE … text=CHAMPION: MIKE`; framebuffer dumps confirm placement.

Left/Right cycles Standings → Fixtures → History; on Setup, Left/Right off the course row opens History, and Back returns to the page it came from. On a complete event, confirm opens Setup for a new event.

## Authority rules kept

- The pure model `native/product/local_tournament_panel.hpp` holds no files or identity. It returns explicit *create* and *arm* requests; the host performs them only through the existing coordinator (`create_local_tournament_coordinator`, `arm_local_tournament_fixture`).
- Tournament instance IDs and capture-attempt IDs are minted from OS entropy (`mint_local_tournament_token`). Failure refuses the action (`NO SECURE ID`). The fixed IDs remain confined to the older env-armed acceptance route.
- An unfinished event is never *silently* replaced. Replacement is allowed when the active event is complete, when its restore was rejected (for example, an entrant profile was deleted), or after an explicit **End Event**: A on its Standings page asks (`A AGAIN: END THIS EVENT`), a second A opens Setup (`START REPLACES THE EVENT`). Back from that Setup withdraws the request. At START, any armed-but-unraced attempt is cancelled first. The ended event's archive stays an incomplete instance and never enters History. Native: the legs route ends a two-leg event with leg 2 armed and replaces it (`ENDED_AND_REPLACED pending=0`).
- Arming requires no pending attempt and a fixture that is unplayed **and** belongs to the seated pair (either seat order). The checkpoint is durable before the panel closes. The existing capture owner still checks the guest-observed course at race start, and a wrong course retires only that attempt while ordinary Records still save. Returning to the settled main menu cancels an armed attempt that was never raced.
- Result authority is unchanged: stock 2P result → `.urrun` + `.urmatch` → fixture receipt → standings.

## Evidence

- `tests/unit/test_local_tournament_panel_cpp.py` (GCC + Clang, `-Werror -pedantic`): presets, setup navigation/cap/roster order, seated-fixture lookup, seat-swap result orientation, 24-cell row bounds.
- `tests/unit/test_local_tournament_panel_host_contract.py`: input ownership, 0x3D + confirmed-pair context, minted IDs only, no replacement of an unfinished event, acceptance uses the production key handler.
- `tests/native/run_modern_local_tournament_panel_acceptance.sh` (manual `multiplayer-match-capture-acceptance.yml` step): two framework pads join and confirm real profiles → `F4` → `START` creates a minted event → Enter arms fixture 0 (`course:01`) → genuine stock 2P race → `CAPTURE_TAGGED` → `FIXTURE_COMMITTED` → a fresh-process checker restores the minted instance and 3/0 standings → a **relaunched** game process rejoins the same pair, opens the panel on the restored complete event's Standings and reaches History with one completed event (`completed=1 unavailable=0`). Passed locally on 2026-10-08 against a Linux desktop build of the current host (minted instance `af699f78…`).

- **Windows package:** manual `windows-local-tournament-package-acceptance.yml` (input: a successful `windows-native-smoke` run ID) downloads that run's exact portable ZIP, verifies its SHA-256, extracts it with Windows' own archive reader and runs `tests/native/run_windows_local_tournament_package_acceptance.sh` through `run-uniracers.cmd` with an isolated per-user data root: join → panel → minted event → genuine stock 2P race → receipt → `CHAMPION` notice → a relaunched packaged process restores Standings and History. No rebuild, so it tests the artifact players download.

## Remaining gaps

1. **[done] Windows package:** green in run 37852389769 (windows-2022, ZIP from main's smoke run 37851158377, head `1056fe8`): the extracted portable ZIP, run through `run-uniracers.cmd` with an isolated user-data root, completed join → panel → minted event → stock 2P race → receipt → champion notice, then a relaunched packaged process restored Standings and History. Re-run it per release candidate against that candidate's smoke run.
2. Native multi-session continuation of a 3+ entrant event: rotate seated pairs across fixtures and finish the event over several processes. The two-entrant relaunch path (restore → Standings → History) is proven.
3. Completed-event history is a summary list only (no per-event standings drill-down) and is not yet mirrored in Records → Multiplayer/Tournament.
4. Multi-leg continuation is native-proven up to arming leg 2 from the results screen (`run_modern_local_tournament_legs_acceptance.sh`); racing leg 2 to a complete best-of-three is not yet automated.
5. **Partial P2 boundary mitigation under adversarial QA:** new P2 *press edges* while the tournament panel is visible are consumed by the dedicated P2 modal policy, with suppression of their matching post-close releases. A release from a press that predates the panel passes to the framework to avoid trapping old held state; native pure-policy and host-link tests cover these edges. The P2 pad *already held before opening* and real post-close guest-word behavior remain **unverified** until J-06 exercises the actual product guest and both controller seats. Do not mark the P2 isolation gate passed from edge-only proof.
