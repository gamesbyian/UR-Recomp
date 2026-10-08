# Quick Practice Track Picker Integration

Status: full player-facing Windows Modern picker integrated on PR #734, subject to the fresh-process native acceptance gate. The shipping host now consumes the existing availability-backed selection model and target-aware launch machine; the stock route remains the sole gameplay authority.

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

The host patch is now thin at the launch boundary: `uniracers_modern_host.cpp` creates a validated target and advances `QuickPracticeLaunchState` from observed stock menu/race state. It emits only normalized menu input through the established relative-input runner. The remaining picker UI should stay above this same path rather than creating another router.

The launch contract is now identity-safe rather than merely race-active-safe. Stock menu IDs are known to become visible before their first input-ready frame, so the reusable launch machine encodes the same 60-guest-frame settle window proven by the deterministic frontend fixtures before emitting its first input on each menu surface. It will not accept an active race unless the router has actually completed the expected MAIN_MENU → RIDER_SELECT → TOUR_SELECT → TRACK_SELECT → NOW_PLAYING sequence and the authoritative decoded-course identity matches the requested zero-based Quick Practice target. An attract/demo race, bypassed route, unknown course identity, or different valid course therefore cannot be silently promoted to a successful Practice launch; mismatches restore the isolated Practice state and return through the existing frontend reboot lifecycle. While that stock-menu route is in flight, the host exclusively consumes keyboard/gamepad edges so incidental player input cannot perturb the menu cursor; guest control resumes only after the requested race has been validated. Routing is bounded to 3,600 host observations and can be cancelled explicitly with Escape or B/Start; timeout/cancel restores the Practice snapshot/root and returns to frontend instead of trapping input ownership indefinitely. Returning from Practice is transactional across SRAM/save-root restoration and the framework reboot request: if the reboot request fails, the live disposable Practice SRAM/root and router state are restored rather than leaving the host half-transitioned.


For the eventual full picker presentation:

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
   - the zero-based course id from `ur_uniracers_identify_course()`, or unavailable until the decoded live course is authoritative;
6. if the launch machine emits an input, write one two-frame relative input entry using `quick_practice_runner_mask()`;
7. arm it through the existing `snesrecomp_desktop_load_relative_input_file` /
   `snesrecomp_desktop_arm_relative_input` path;
8. when the launch machine reports Active, reuse the existing practice overlay and persistence suppression.

Do not resurrect a second host-owned copy of tour/track routing.

Fast repeat/navigation builds on the same rule. A course observed during an authoritative live race may be cached process-locally for the current Modern profile context as Recent Course. Named profiles never share the cache with one another, and the no-profile context is isolated from every named profile. F6 / controller Y at the settled Modern main menu converts that validated identity back to a `QuickPracticeTarget` and enters the same isolated Practice lifecycle. Completed Practice results use the existing rollback Restart anchor for one-action Repeat Practice; no relaunch routing is needed for that case.

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

## Windows Modern player-facing integration (PR #734)

At settled Modern MAIN_MENU, F5 or physical gamepad X opens the host-owned Quick Practice picker. A validated Recent Course supplies the initial selection, otherwise the picker starts on Crawler/Dragster. Up/Down move among available courses, Left/Right move between available tours preserving the slot, Enter or mapped P1 A confirms, and Escape or mapped P1 B/Start cancels. Physical gamepad X is a shortcut only to open the surface; its navigation uses the live GamepadMap's semantic controls.

The picker uses `open_available_quick_practice_selection` and `quick_practice_available_selection_apply` without another catalog, input map, course identity or router. A narrow title-owned, read-only adapter decodes the existing per-rider stock unlock-tier byte (SRAM `0x10D3 + rider`, matched to selected rider `0x0748`). Tier 0 exposes the four beginning tours (Crawler/Shuffler/Walker/Hopper; 20 tracks), tier 1 adds Jumper/Bounder (30 tracks), tier 2 adds Runner/Sprinter (40 tracks), and stock tier 3 remains limited to those 40 ordinary tracks by the deliberate Modern Practice hidden-Hunter policy. Missing/malformed stock SRAM or rider identity fails closed. The established `quick_practice_availability_from_tour_options` model expands only stock TOUR_SELECT option identities; the host does not invent or alter unlock progression. Background provenance: [TASVideos Uniracers technical SRAM observation](https://tasvideos.org/Forum/Topics/979?CurrentPage=4&Highlight=39298&PageSize=25&Sort=CreateTimestamp), complemented by the canonical stock tier/menu behavior already recovered in the repo. The host modal consumes human guest inputs and rejects changed profile, menu, mode or race context; confirmation hands the validated target to `begin_practice(track_id)`, preserving Practice's isolated SRAM/save root, course-identity proof, result Repeat Practice, exit restoration and persistence suppression. Rendering uses the existing logical overlay layout/density contract at configured 1x–4x.

`tests/native/run_modern_practice_picker_acceptance.sh` exercises actual fresh-process keyboard input in the product build: open/present, locked-tour/Hunter-skipping wrap, cancel without launch, cross-tour Shuffler/Looper selection, exact observed course identity 10 during stock race, profile-independent SRAM restoration, no Practice run files, and Authentic inertness. It is part of the existing Modern onboarding/practice acceptance shard. The full picker is shipping-ready only after green native evidence and merge; the stock unlock-tier decoder also has strict C++17 unit coverage.
