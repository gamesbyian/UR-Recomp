# Quick Practice Track Picker Integration

Status: product substrate implemented; Modern host/UI wiring pending until the active host lanes settle.

## Product goal

Replace the current single-target Quick Practice shortcut with a compact Modern track picker that launches a selected course through the stock one-player frontend and authoritative race initialization.

The picker is a Modern administrative surface. It must not write race state, course state, frontend menu bytes, physics state, results, records or progression directly.

## Implemented substrate

The product layer now separates five concerns:

1. `quick_practice_route.hpp`
   - maps stock track id 0..44 to stock tour option plus five-row track slot;
   - reproduces stock TOUR_SELECT and TRACK_SELECT cursor decisions.

2. `quick_practice_catalog.hpp`
   - owns the shipping 45-course name/tour/type catalog;
   - is mechanically checked against `analysis/data/course-corpus.json`.

3. `quick_practice_picker.hpp`, `quick_practice_selection.hpp`, and
   `quick_practice_selection_view.hpp`
   - own player selection state, cancel/confirm behavior and renderer-neutral labels.

4. `quick_practice_availability.hpp`
   - keeps catalog membership separate from player availability;
   - supports sparse masks and explicitly allows Hunter to remain hidden unless product policy enables it.

5. `quick_practice_launch.hpp` and `quick_practice_input_mask.hpp`
   - drive MAIN_MENU -> PLAYER_SELECT_P1 -> TOUR_SELECT -> TRACK_SELECT ->
     PRE_RACE_CARD -> active race using ordinary normalized SNES input;
   - debounce direction pulses until the stock menu selection byte changes;
   - map emitted input to the pinned runner mask contract:
     Up=0x10, Down=0x20, Left=0x40, Right=0x80, A/Accept=0x100.

The focused `Quick Practice product contracts` workflow compiles and runs these contracts without an emulator build.

## Native evidence already landed

PR #469 proves with the generated native executable and Authentic policy that:

- Crawler TRACK_SELECT advances `7E:009B` through 0,1,2,3,4 under ordinary Down input;
- Crawler slot 5 reaches Now Playing with current track `7E:00CE = 0x04`;
- stock Shuffler option 2 plus slot 3 reaches Now Playing with
  `7E:00CE = 0x0C`.

No guest state was written by those probes.

## Host integration shape

After the active Modern host/profile/settings work is merged, keep the host patch thin.

At the settled Modern main menu:

- F5 / controller X opens the Quick Practice picker instead of immediately launching Dragster;
- the picker initializes from a permitted course, initially Dragster if no recent choice exists;
- Up/Down move among permitted courses;
- Left/Right may move by tour while preserving the slot where possible;
- Enter / controller A confirms;
- Escape / controller B cancels;
- Help text continues to advertise Quick Practice without exposing hidden content.

On confirm:

1. obtain the validated `QuickPracticeTarget`;
2. take the same exact 8 KiB SRAM snapshot used by current Quick Practice;
3. switch to the isolated practice save root;
4. create `QuickPracticeLaunchState` from the confirmed target;
5. each completed frame, pass only:
   - `g_ram[0x009F]` menu id;
   - `g_ram[0x009B]` stock menu selection;
   - `g_ram[0x0313] == 1` active-race state;
6. if the launch machine emits an input, write one two-frame relative input entry using `quick_practice_runner_mask()`;
7. arm it through the existing `snesrecomp_desktop_load_relative_input_file` /
   `snesrecomp_desktop_arm_relative_input` path;
8. when the launch machine reports Active, reuse the existing practice overlay and persistence suppression.

Do not resurrect a second host-owned copy of tour/track routing.

## Persistence and secret boundaries

Practice continues to be disposable:

- exact pre-practice SRAM is restored on Exit Frontend;
- profile autosave is suppressed;
- completed-run, input sidecar and ghost artifacts are suppressed;
- Authentic mode remains inert.

The canonical course catalog intentionally includes Hunter because it describes the game, not because every player should see it. The picker must consume an availability mask. Do not make `quick_practice_all_tracks()` the default player policy. Hunter tracks 40..44 stay hidden until a deliberate progression/product rule says otherwise.

If normal tours are progression-gated, derive a sparse mask from established progression semantics rather than bypassing stock unlock state or revealing names early.

## Acceptance required for the host patch

The player-facing integration is complete when focused native acceptance proves:

- picker opens only from the settled Modern main menu;
- cancel returns to that menu without starting practice;
- keyboard and controller can select a non-default visible course;
- at least one cross-tour target reaches the expected `7E:00CE` track id through ordinary frontend input;
- direction settling cannot double-step the stock cursor;
- active race uses the ordinary authoritative race initialization;
- Exit Frontend restores byte-identical pre-practice SRAM;
- practice emits no profile autosave, completed-run or ghost artifact;
- hidden/unavailable tracks are not rendered or launchable;
- Authentic mode ignores the Modern picker completely.
