# Modern Product Layer

This document owns intentional modern product policy and the host/runtime boundary that implements it. It does not redefine stock fidelity. Historical behavior remains documented by the existing UI, progression, SRAM and semantic evidence surfaces.

## Cross-platform host contract

The modern product layer is shared across Windows x64, macOS, Web and future console-homebrew hosts. Platform code may choose storage locations, create presentation/audio devices, translate physical controller APIs and report lifecycle events, but it must not redefine product semantics.

In particular:
- persisted host state must go through a platform-neutral storage boundary rather than hard-coded desktop paths;
- semantic product inputs must not expose SDL scancodes, Win32 virtual keys, macOS keycodes, browser Gamepad indices or libnx HID enums above the host adapter;
- pause/focus/suspend policy must enter through typed lifecycle/session interfaces;
- vibration remains a host-owned setting whose physical implementation is platform-specific;
- Authentic mode remains inert with respect to all modern host policy on every platform.

The canonical target matrix is `PLATFORM-TARGETS.md`; Switch-specific feasibility work is `SWITCH-HOMEBREW-PORT.md`.

## Video and presentation settings policy

Video configuration is host-owned modern product state. It must control presentation only and must not change authoritative guest simulation timing.

The eventual user-facing video settings should support, where the platform permits:

- automatic/native-display resolution;
- explicit common output resolutions;
- arbitrary window sizing on desktop;
- windowed, borderless-fullscreen and fullscreen presentation;
- VSync;
- presentation refresh/FPS targets such as 60, 90, 120 and 144 Hz, plus platform-appropriate uncapped/native-refresh options where useful;
- internal render scale independent of output resolution when the HD compositor or post-processing path benefits from it;
- independent display-geometry/pixel-aspect selection and logical-view selection, following `DISPLAY-PRESENTATION-POLICY.md`;
- initial display roles of Authentic 4:3, Raw Pixels, and modern square-pixel presentation where appropriate;
- logical view choices including Original and true 16:9 Widescreen, with Adaptive/ultrawide admitted only when scene and renderer evidence supports them;
  The first two choices are now implemented as the persisted Modern-mode `VIEW` setting; Original is the default and 16:9 consumes the title-owned scene/materializer contract rather than stretching the source.
- graphics-pack selection and optional post-processing where available.

The **guest simulation cadence is not a user setting**. Physics, collision, timers, AI, RNG, stunt timing, animation-state selection, records and deterministic replay remain driven by the original authoritative simulation cadence on every platform.

A higher presentation refresh rate may therefore display the same guest state more than once, interpolate presentation-only transforms where technically safe, or otherwise pace host frames independently. Such interpolation must never feed values back into guest state or alter event timing.

Authentic mode should retain a literal/reference presentation path suitable for fidelity comparison even on high-refresh displays. Modern mode may provide smoother presentation, but simulation equality remains the acceptance criterion.

Output resolution and internal render scale are separate concepts. For example, a 3840x2160 output may use a lower internal HD render scale for performance and upscale to the display, while sufficiently capable hardware may render at or above output resolution for higher-quality downsampling.

Platform adapters own the concrete list of modes exposed by Windows, macOS, Web or console hosts. Shared product code owns the semantic settings and must not encode platform-specific display APIs.

## First seam: host administrative state

The first project-owned modern seam is deliberately small: independent host-side profile selection and settings.

The implementation lives in `native/product/host_product_state.{hpp,cpp}`. Its persisted envelope contains only:

- an optional opaque host profile ID;
- vibration enabled/disabled;
- pause-on-focus-loss enabled/disabled;
- desktop display mode (`windowed` / `borderless` / `fullscreen`);
- presentation VSync mode (`off` / `on` / `adaptive`);
- presentation FPS mode (`game` / `60` / `90` / `120` / `144` / `native`);
- semantic output resolution (`native` or explicit `WIDTHxHEIGHT`), with refresh selection kept separate.

This state is administrative host state. It has no WRAM addresses, SRAM layout, racer slots, medal values, league state, course state, timers, physics state or other cartridge-era semantics.

The current codec is intentionally dependency-free and deterministic. Versions 1 through 5 retain their historical strict exact-field contracts. Version 6 is the stable additive envelope: `profile`, `pause_on_focus_loss`, and `vibration_enabled` are the required administrative core; recognized additive settings may be absent and receive typed defaults, while unknown, duplicate and malformed fields still fail closed. Canonical encoding writes the complete current Version 6 state, including Widescreen and Internal Render Scale when present in the product model, so sparse accepted state normalizes on the next save without another schema bump.

The first real runtime consumer of a typed setting is `pause_on_focus_loss`. `native/product/focus_pause_policy.hpp` reduces the decision to four explicit inputs: execution mode, typed host settings, current focus state and current host-pause state. In Modern mode, the ordinary Uniracers desktop binding samples SDL keyboard focus from its existing completed-frame callback and routes a qualifying focus loss through the same `ur_modern_session_pause()` command path used by player pause input. The policy is title-gated to the established active-race/results surfaces, never writes guest state, and is inert in Authentic mode. Desktop display mode remains the next accepted consumer: Options now exposes Windowed, Borderless and Fullscreen, while a narrow SNESRecomp desktop-host interface owns the concrete window operation. SDL2 preserves its distinct borderless-desktop and exclusive-fullscreen paths; SDL3 deliberately collapses both fullscreen semantics to its single fullscreen operation without leaking that platform detail into product code. VSync is the third real setting: Options exposes Off, On and Adaptive through the same keyboard/controller cursor model, while a narrow project patch exposes SNESRecomp's existing live renderer VSync policy through `snesrecomp_desktop_set_vsync()`; renderer-specific swap-interval/reconfiguration remains framework-owned. Presentation FPS is the fourth: Options exposes Game, 60, 90, 120, 144 and Native by binding the generated title host to SNESRecomp's existing `presentation_hz` hook. Game preserves lockstep presentation at authoritative guest cadence. Positive targets use the host's separate presentation clock to re-present captured frames between simulation ticks; changing the target resets only that host clock and recomputes the live VSync interval. These are presentation controls only. They do not change guest cadence, timers, physics, AI, RNG, animation-state selection, input semantics, progression, records or SRAM. Internal Render Scale is now a production consumer too: Options cycles 1x through 4x, persists the choice in schema v6, and drives one authoritative presentation-density contract without changing guest geometry. Authored Racer HD frames render at their declared density; unsupported or unregistered replacement states retain stable density through the exact nearest-neighbour fallback compositor instead of flickering back to 1x. Evidence-backed 342x224 widened race fields preserve the same configured density while logical view width, +48 backing coverage, +43 visible world extent, PAR, viewport, camera/simulation and activation authority remain unchanged. Regional-title replacement and every current host-owned Modern modal/non-modal overlay likewise own explicit density transforms through 1x-4x, so no current Modern presentation surface requires a global 1x clamp. The framework's frozen-frame and frame-blend staging buffers remain sized for the full 4x contract. Modern binds final-window filtering to explicit nearest for the current mixed-source compositor; Authentic leaves framework/config filtering untouched. Native acceptance retains real high-density presentation evidence rather than accepting settings diagnostics alone. Authentic mode never applies the setting. `F` remains an optional Focus Pause shortcut.

`native/title/uniracers_run_data.{h,cpp}` is the title-specific read-only bridge for the first Run Data view. It decodes the already-promoted authoritative timer digits at `7E:0E0F/0E13/0E17/0E1B/0E1F` into typed minutes, seconds, tenths and six-step sub-tick data, validates every digit, and exposes no write interface. The generic product UI therefore never owns Uniracers WRAM offsets. Native run `37108042695` independently decodes the same race-entry WRAM dump in CI and requires the product diagnostic to report the exact matching timer/sub-tick before accepting the subview.

`native/product/host_product_store.{hpp,cpp}` provides the versioned codec's persistence backend without owning schema semantics. The shared store accepts an explicit path, bounds reads, rejects malformed/oversized state and writes through the product codec. The desktop host owns placement: `UR_HOST_STATE_PATH` remains the most specific development/acceptance override; otherwise the Windows consumer launcher supplies the shared `UR_RECOMP_USER_DATA_ROOT`, and non-package launches fall back to SDL's platform preference directory. The legacy `host-state-v1.txt` filename is retained inside that root so older supported schema versions remain discoverable. The same root resolver owns profile catalog, onboarding/practice helper files and completed-run placement, while framework config/keybind/SRAM state follows the matching framework root and mutable mod selections use the matching `SNESRECOMP_MOD_STATE_PATH`; installed mod catalog/resources stay package-relative. Modern mode loads once before session creation; live setting changes commit product state only after host-side application and durable save succeed, with the live effect rolled back on persistence failure. Authentic mode does not load or apply this state. Exact current fields/defaults belong to `analysis/modern-product-settings.json` and native acceptance rather than being duplicated as a historical snapshot here.

## Independent modern profiles and racer identity

Modern profiles are a separate host-owned namespace, not an expansion of cartridge SRAM and not a synonym for the original named unicycles. The profile catalog owns stable profile identity and player-facing racer metadata; each profile owns its isolated framework save root, host profile state, completed-run catalog and ghost preferences. Classic named/color riders remain exact content presets that can be selected by a profile without becoming save slots.

The profile payload is versioned and bounded. It can retain an exact 8 KiB stock-SRAM mirror plus host-owned racer identity/metadata, but the SRAM bytes remain opaque to the generic profile layer: medal, tour, checksum and other progression meaning stay with the guest/SRAM semantic layer. Modern profile activation selects an isolated framework save namespace before guest SRAM is loaded, so profiles and Authentic execution do not share cartridge backing files. The selected racer is handed back through the recovered stock rider-selection path rather than bypassing ordinary race initialization.

Catalog/profile activation is fail-closed. A profile is authoritative only when the persisted catalog entry, profile metadata and required snapshot state agree; malformed, partial, mismatched or unknown identities do not acquire write or rider-projection authority. Profile IDs are constrained so Windows path aliases/device names cannot collapse distinct profiles onto one save directory. Writes use replace-on-success semantics, and malformed existing files are preserved rather than silently overwritten.

The acceptance standard is process-oriented: create/select/rename and classic-preset identity survive a fresh process; independent profiles do not share SRAM, runs or ghost preferences; migration/legacy-readable states do not silently become writable when required Modern metadata is absent; malformed catalog/profile inputs fail closed; and Authentic mode remains inert. True host-owned tour/event continuation above the stock rider-select wipe remains a separate product feature, not a reason to reinterpret the profile codec.

## Authentic versus Modern policy

`ExecutionMode::Authentic` is the regression/reference policy. In this mode:

- host profiles do not participate in game behavior;
- host settings do not override stock behavior;
- modern administrative commands are disabled;
- the original guest frontend/progression/SRAM path remains the behavior under test.

`ExecutionMode::Modern` enables host-owned product facilities. Enabling it does not grant permission to mutate authoritative race simulation. Modern features must cross an explicit runtime adapter whose effects are independently testable.

The host-state store may physically exist while Authentic mode is active, but its contents must be observationally inert with respect to guest behavior.

## Modern product decisions

These are settled product policy, not open research questions:

- Modern's top-level information architecture is **Play / Practice / Multiplayer / Records / Options**. Options contains settings only. `native/product/modern_root_menu.hpp` now owns this ordering as a pure typed navigation model: it wraps deterministically, normalizes invalid selection to Play, and names destinations without performing any guest/frontend routing. The live host integration remains a separate step so each destination can reuse its already-established authority instead of creating another route model. Stable player-facing root copy is now separated from navigation semantics through `modern_text_catalog.hpp`: each destination maps to a semantic key (`root.play`, `root.practice`, `root.multiplayer`, `root.records`, `root.options`) with built-in English fallback. This is the first localization-ready text slice, not a mandate to catalog diagnostics, evidence labels, or unstable implementation copy. `tools/validate_modern_locale.py` now defines the first external locale-pack boundary for those settled IDs: schema `ur-recomp-modern-locale-v1`, a canonical `language` or `language-REGION` tag (for example `en` or `fr-CA`), and an exact entry set matching the currently cataloged keys. Unknown, missing or duplicate keys and malformed/bounded copy fail closed. `analysis/data/modern-locale-en.json` is the canonical example. No runtime locale loader or persisted language setting exists yet; English remains built in, so introducing a loader later cannot become a guest/runtime dependency.
- profile identity/persistence is separate from racer identity and from guest SRAM slots;\n- destructive stock save administration is not exposed as a controller chord in Modern mode: the active authoritative profile has an explicit confirmed **Reset Progress** action that installs the retained exact clean stock SRAM image, preserves that profile's Modern racer identity, clears its unfinished-tour continuation, and does not delete host-owned completed-run/replay history. The profile metadata and framework SRAM update are transactional with rollback on a failed SRAM write. Authentic keeps the original stock erase chord;
- local multiplayer uses simultaneous independent join/racer selection in Modern; Authentic keeps stock sequential selection. The shared setup model now also owns a presentation-safe per-seat projection for P1/P2 (`EMPTY`, controller, or keyboard, with connected/disconnected state) without exposing opaque framework device IDs as player-facing identity. Controller-brand glyphs remain deferred until they can be derived from the authoritative remapped input surface rather than guessed from hardware family;
- Modern tour play supports host-owned Resume Tour / Restart Tour persistence;
- Modern tour challenge is player-selectable Bronze/Silver/Gold using canonical stock thresholds/opponents, and higher-tier completion satisfies lower tiers;
- secret/Hunter progression remains undisclosed discovery content;
- the result ritual is preserved, then Modern adds Next Event / Retry / Track Select / Tour Select / Records actions;
- stock League administration becomes Modern Local Tournament, defaulting to round-robin/points play while retaining original standings presentation;
- one unified Records browser owns Tracks, Racers/Profiles, Runs/Replays and Multiplayer/Tournament views while retaining classic tables as views; Windows x64 now has permanent Modern pause-menu Records navigation, profile-wide Tracks and Racers/Profiles browsing, run history/detail, and a fail-closed Multiplayer/Tournament destination. The multiplayer view deliberately reports no stored history until a durable authoritative match/tournament-history producer exists; session-local controller assignment and 1P run artifacts are not promoted into invented standings;
- Modern text entry uses native keyboard input plus controller on-screen entry; guest-compatible names use a deterministic stock-width projection when needed;
- all 16 classic racer presets remain exact, but no new canonical personalities are invented; Bronsen/Silvia/Goldwyn/ANTI-UNI retain their established opponent roles;
- the original attract/demo cycle remains default; any Local Showcase is explicit and optional.

These decisions live above the authoritative guest. None authorizes changing race physics, scoring, AI, canonical thresholds, secret conditions, timing or stock Authentic behavior.

## Ownership rules

Keep these domains separate:

| Domain | Owner | Examples |
| --- | --- | --- |
| Race simulation | original/recompiled guest | physics, collision, stunt state, RNG, race timing |
| Stock persistence | original/recompiled guest | 8 KiB SRAM, medal matrix, derived tiers, checksum |
| Modern administration | host product layer | profile identity, settings, future save catalog and UI policy |
| Presentation | host/runtime presentation layer | window state, output scale, future overlays and graphics mode |
| Session control | explicit host/runtime adapter | pause/resume/restart/exit requests |

A modern profile is not a renamed unicycle/save slot. Racer identity and progression can later be associated with a profile by higher-level product policy, but the storage primitives remain independent.

## Session-control seam

`native/product/session_control.{hpp,cpp}` defines the first runtime-facing modern control contract without implementing runtime side effects.

The contract accepts four modern administrative commands:

- pause;
- resume;
- restart race;
- exit to frontend.

A successful command emits exactly one typed `RuntimeAction` for the runtime adapter to consume. The contract itself never writes guest memory, SRAM, timers, physics, menu state or progression. Pause/resume maintain only a host-owned running/paused phase. `ModernSessionRuntime` is the smallest product coordinator above that contract: it owns policy-gated lifecycle observation and dispatch, while `modern_session_c_api.{h,cpp}` exposes the same narrow surface to the generated C host and product UI. Exit to Frontend is implemented as a host-owned session transition that returns through the accepted frontend reconstruction path rather than writing guest menu state directly.

The queue is deliberately single-action and fail-closed: while one action is awaiting consumption, later requests return `Busy` rather than being reordered or coalesced implicitly. Redundant pause/resume requests return `NoOp`. Authentic mode rejects every session command by policy and never changes host session phase.

This gives the eventual native host a narrow integration point:

1. the product/UI layer requests a command;
2. `SessionControl` validates modern policy and transition ordering;
3. the runtime adapter consumes the emitted action;
4. the adapter performs the platform/runtime operation;
5. runtime-specific actions must have deterministic acceptance before shipping; Restart Race and Exit to Frontend both satisfy that ownership rule through their accepted lifecycle paths.

In particular, `RuntimeAction::RestartRace` does **not** mean "write known starting values into WRAM." The accepted implementation restores the exact rollback snapshot captured at the owned active-race lifecycle boundary, preserving authoritative guest/runtime initialization.

### Pinned SNESRecomp pause adapter

The pinned SNESRecomp desktop host already owns a suitable pause mechanism. Its existing `g_paused` path:

- keeps pumping host events while paused;
- pauses host audio;
- resets presentation pacing debt;
- skips `RtlRunFrame`, so the guest does not advance.

`tools/patches/snesrecomp-session-pause.patch` exposes only that existing host state through `snesrecomp_desktop_set_paused()` and `snesrecomp_desktop_is_paused()`. It does not introduce a new emulation mechanism.

`native/product/session_runtime_adapter.{hpp,cpp}` maps `SuspendGuest` and `ResumeGuest` onto this narrow host hook. For `RestartRace`, the adapter now accepts the proven `RaceRestartLifecycle` directly and invokes its exact rollback-backed restore path; the older callback slot remains only as a compatibility fallback for isolated consumers. After a successful restore the adapter calls the host reconciliation hook, which the native binding maps to the existing audio fast-forward recovery path so stale pre-restart PCM is discarded without mutating guest/APU state. `ExitToFrontend` is handled as a host-owned session/frontend transition; practice uses that same boundary to restore its isolated SRAM/save-root state before reconstructing the ordinary frontend.

The pause integration therefore has a clean ownership chain:

`modern UI/policy -> SessionControl -> RuntimeAction -> pause runtime adapter -> existing host frame gate`

At no point does the pause path write guest memory or reinterpret stock pause/menu state.

### Race-restart anchor

Modern **Restart Race** is a host-product feature; the original pause flow exposes Continue/ Quit rather than a stock restart command. The implementation should therefore reproduce a valid initialized race state, not invent a guest input chord or reinterpret console reset.

`native/product/race_restart_anchor.{hpp,cpp}` owns one exact in-memory machine snapshot for the current attempt. It is intentionally ignorant of Uniracers WRAM layout. Its lifecycle owner decides when a race has reached the accepted restart boundary, then calls `capture()` once. Later `restart()` restores those exact bytes through runtime-supplied snapshot hooks.

The first native discriminator rejected ordinary user-facing savestate semantics as the restart substrate. Capturing with `RtlSaveSnapshotToMemory()`, idling for 60 frames, restoring with `RtlLoadSnapshotFromMemory()` and replaying the same idle window reproduced the saved blob immediately but did **not** reproduce the same 60-frame future state. That negative result is retained because it shows that a one-off savestate's intentional host-clock re-anchoring is insufficient for deterministic race retry.

The restart binding therefore uses SNESRecomp's in-process rollback-state API instead:

- `RtlRollbackSnapshotBound()` to size the allocation;
- `RtlRollbackSaveToMemory()` for capture;
- `RtlRollbackLoadFromMemory()` for restart.

Rollback snapshots carry the simulation-residue state that deterministic resimulation requires, while deliberately excluding live presentation-consumer behavior such as the audio output ring from the comparison domain. They also include `cart_saveload`, and for Uniracers that means the 8 KiB battery SRAM is inside the rollback blob. A modern Retry therefore preserves the **current** SRAM across the rollback restore instead of reverting progression or records to the race-entry image. `ur_modern_session_load_preserving_persistent_bytes()` snapshots the persistent byte domain immediately before load, invokes the validated rollback loader, and restores those exact bytes before returning, including when load fails. The restart anchor still restores authoritative volatile machine state; persistence stays on the current guest timeline.

A rewindable attempt also needs the same APU timing-ownership rule SNESRecomp already applies to netplay, run-ahead and its rollback probe. `RtlSetRewindAudioTimingLock(true)` suppresses the offline wall-clock fallback once the race anchor is established, leaving guest-frame timing authoritative until that rewindable attempt is retired. Authentic mode never enables this host policy. This is required because host elapsed time cannot be restored as part of a deterministic guest timeline.

For Uniracers, the candidate lifecycle edge remains the established transition into active gameplay, `7E:0313 = 0 -> 1`, observed at a completed host frame through the title-specific `after_run_frame` hook. The focused acceptance fixture captures there, advances a fixed 60-frame idle window, restores, and requires the simulation digest after replay to match the first pass exactly. The anchor itself does not hard-code `$0313`, because state detection belongs to the title adapter rather than the storage primitive.

A restart anchor is immutable for one attempt. Repeated capture requests do not silently move the restart point.

`RaceRestartLifecycle` owns the attempt-to-attempt policy above that storage primitive. A false→true active-race edge clears any previous anchor and captures the newly initialized race. A true→false edge does **not** clear the anchor: the just-finished attempt remains restartable through results. A confirmed course-selection/frontend transition calls `retire_attempt()`, which clears the anchor explicitly; the next actual race entry also supersedes it. If a new-race capture fails, the previous race is not retained as a misleading fallback. Repeated Restart Race requests restore the same immutable anchor. Restart while host-paused leaves the host pause gate paused, so the restored guest remains frozen until an explicit Resume command.

The reusable lifecycle receives only an `active` boolean; it does not know Uniracers WRAM addresses. `native/title/uniracers_restart_policy.{h,cpp}` owns title-specific Retry eligibility. `$0313 == 1` is an active-race Restart surface. Non-race `$009F == 0x99`, `0xBC`, or `0x18` are the established race/circuit/stunt results surfaces and retain Retry. Stable main-menu/rider/tour/track/Now Playing states `0xD7`, `0x3C`, `0x6D`, `0xF6`, and `0x16` are retirement candidates only **after a results surface has been observed**. This stateful rule matters because a normal finish can pass through frontend-coded states before the stock results screen appears. Before results, those states hide Retry but retain the anchor; after results, the next stable frontend/pre-race candidate retires it. Unknown/transient states expose no Retry and do not clear an anchor merely because their semantics are not established.

`ModernSessionRuntime` exposes restart availability only in Modern mode and forwards `RestartRace` through `SessionControl -> RuntimeAction -> SessionRuntimeAdapter -> RaceRestartLifecycle -> RaceRestartAnchor`. The C bridge now also exposes three semantic host keys, deliberately platform-independent: Escape toggles host pause, Accept resumes only from pause, and Restart dispatches only while a validated restart anchor is available. The pinned desktop host has one additive consumed-key callback before ordinary `HandleInput`, so title-owned product keys remain in the existing SDL event loop rather than creating a parallel input system. Before an anchor exists, or after `retire_attempt()`, the command reaches the real runtime path and fails predictably as `RejectedByRuntime`; Authentic mode rejects the command before lifecycle or snapshot state can change. The runtime also owns the rewind-audio timing lock for exactly the lifetime of a restartable attempt: it is enabled after successful anchor capture, retained through results while Retry remains valid, and released when the attempt is retired or replacement capture fails.

### Native Restart Race acceptance

PR #235 closes the title-specific restart-state question. Workflow run `37080761750` captures the active-race rollback snapshot, restores it exactly, and reproduces the same state after a 60-frame forward replay. The earlier APU-only replay failure was diagnostic: immediate snapshot equality had hidden one host-owned timing carrier. The desktop host enables extended APU frame timing, but rollback residue v6 did not preserve the corresponding `RtlApuFrameClock` (`start_master`, `start_guest`, `next_guest`, `last_duration`). Rollback residue v7 now saves/restores that clock along with the existing pacing state, and the unchanged replay acceptance passes.

This strengthens the validation rule for future rewindable host features: exact load equality is necessary but insufficient. Any operation that restores authoritative machine state must also prove bounded forward replay across CPU/WRAM/APU/PPU/DMA/cart partitions before it is treated as deterministic.

The product-level acceptance exercises that same native substrate through the actual typed command chain rather than calling rollback APIs directly. The active-race fixture requires immediate full simulation-digest equality and repeated 60-frame replay. A second results-screen fixture reaches the stock `0x99` results state through gameplay, requests Retry through the title policy, requires CPU/WRAM/APU/PPU/DMA to return to the race-start anchor while the **current cart/SRAM partition remains unchanged**, and then repeats the restart from the same immutable anchor. Workflow run `37086197360` passes this path end-to-end: both results-screen requests report `persistent_cart_preserved=1`, and the final marker is `UR_RESTART_RESULTS PASS results_surface=1 persistent_sram_preserved=1 repeated_restart_equal=1 window=60`. A successful restore marks the lifecycle active immediately so the next observed restored race frame cannot be mistaken for a new attempt and silently replace the anchor. The host binding also toggles the existing audio recovery path after restore and keeps `RtlSetRewindAudioTimingLock` owned by the restartable-attempt lifecycle.

## Production host integration

The accepted pause/retry stack is no longer acceptance-harness-only. `native/product/uniracers_modern_host.{h,cpp}` is the durable Uniracers desktop binding. It owns only title/product coordination: completed-frame title observation, keyboard/controller translation, the host pause/retry overlay, rollback snapshot hooks, SRAM-preserving restore and presentation reconciliation.

`tools/patch_modern_product_host.py` keeps generated SNESRecomp output disposable. It adds only the durable header/callback pointers to generated `src/main.c` and links the project-owned product/title sources through generated CMake. The ordinary `native-build-smoke.yml` now applies that patch before compiling, so the normal native executable includes the modern product surface rather than reserving it for the focused Restart acceptance workflow.

Modern mode is the production default. Setting `UR_EXECUTION_MODE=authentic` creates the same host binding in Authentic policy mode; rejected product actions are not consumed, so ordinary frontend/guest input remains authoritative. Modern pause activation is intentionally title-gated to established active-race/results surfaces, which keeps frontend Start/Escape behavior out of the product overlay. The same title gate now applies to pause-on-focus-loss, so losing focus in stock frontend flow cannot freeze or reinterpret guest menu behavior.

## First-run help and quick practice

Modern Windows x64 has one deliberately compact onboarding surface rather than a parallel tutorial game mode.

On the first genuinely new Modern install, the host presents a dismissible controls/help overlay. Existing installs with a product-state file are treated as already established so an upgrade does not interrupt normal play or deterministic regression captures. `F1` reopens Help later. The overlay explains only the fundamental play loop that should not require external documentation:

- Left/Right movement;
- B to jump and Y to brake;
- A/X/L/R as stunt controls;
- land wheel-down to complete the stunt;
- clean completed stunts add speed.

Keyboard labels come from SNESRecomp's live P1 `keybinds.ini` state. Controller labels describe the normalized SNES pad controls the framework feeds to the guest, while physical controller remapping remains owned by the framework. The existing pause-menu Controls view uses the same live sources. Advanced discoveries, the stock cheat and hidden tour/progression rewards are intentionally absent.

The first-run dismissal is host-only state in `onboarding-v1.seen`; it has no guest/SRAM representation and Authentic mode neither reads nor displays it.

Modern main-menu Quick Practice is available through `F5` or controller X. It does not write a course ID, menu byte, physics state or race-start structure directly. A canonical 45-course product catalog, progression-derived availability mask and pure selection controller produce only a validated `QuickPracticeTarget`. The launch machine then observes the proven stock frontend states and feeds ordinary directional/confirm inputs through the existing deterministic host input path:

`MAIN_MENU (D7) -> RIDER_SELECT (3C) -> TOUR_SELECT (6D) -> TRACK_SELECT (F6) -> NOW_PLAYING (16) -> active race (0313=01)`.

That keeps the ordinary guest frontend and race initializer authoritative while still allowing rapid selection of any currently permitted stock course. Catalog membership is deliberately separate from availability, so hidden/locked content cannot become browsable merely because its metadata is known. Keyboard/gamepad events map to a small semantic picker vocabulary, and the renderer consumes a prepared view model rather than duplicating selection or formatting logic.

Practice is non-progressing Modern product state. At launch, the host snapshots the exact 8 KiB guest SRAM and switches framework persistence to an isolated practice save root. Modern profile autosave and completed-run capture are disabled while practice is active. Choosing the existing Pause > Exit Frontend path restores the exact pre-practice SRAM bytes and original save root before the already-accepted full session reboot publishes SRAM and reconstructs the stock frontend. A small in-race hint makes that return path discoverable. Authentic mode cannot enter this path.

The dedicated native acceptance requires first-run visibility/dismissal persistence, rendered live keyboard/controller binding diagnostics, stock-input-driven launch into authoritative active-race state, byte-identical pre/post-practice SRAM digests, clean return to main menu, absence of profile autosave during practice, and complete Authentic inertness. Intermediate menu IDs are diagnostic rather than mandatory because stock transitions can cross them between host observation boundaries.

## Fast repeat and recent-course navigation

Ordinary Windows play now reuses the existing Restart and Quick Practice authorities for the highest-value repeat paths instead of adding another race launcher.

- On a validated results surface, **R / controller X** is a one-action Rematch. If the completed attempt is Quick Practice, the same action is presented as **Repeat Practice**. Both dispatch the already-accepted rollback-backed Restart command, so the stock-initialized race anchor, current course and Practice/non-Practice persistence policy are preserved.
- **Ctrl+R** remains the direct Restart shortcut on any validated restart surface.
- While a race is active, the host may remember a **Recent Course** only after `ur_uniracers_identify_course()` validates the live course, and only for a race the player started: the idle attract demo (main menu → title `0x84` → demo race) is ignored through `recent_course_origin.hpp`, which counts only frontend states held stable for 8 frames because `$9F` is per-frame scratch during course load (native acceptance: `UR_RECENT_ATTRACT_NATIVE`). At the settled Modern main menu, **F6 / controller R** (and controller Y when no tour is resumable, since Y otherwise opens the Tour surface) relaunches that validated course as non-progressing Quick Practice. The host supplies only a `QuickPracticeTarget`; `QuickPracticeLaunchState` then drives the proven stock menu route with normalized directional/confirm input. No course/menu/progression byte is written directly.
- The settled Modern main menu shows one compact **continue strip** below the stock menu items instead of loose hints. It has at most two rows, each naming the inputs that actually trigger it: `F3/Y NEXT EVENT <course>` (or `F3/Y TOUR <tour> n/5` when the next event is ambiguous) and `F6/R RECENT <course>`. The rows come from `modern_main_menu_strip.hpp` and are sized so every shipping course and tour name fits. The strip is laid out through the shared overlay-composition policy, so it fails closed rather than overlapping stock OPTIONS, and it is hidden while the Tour surface, onboarding, pause, Practice or a tour route owns the screen. Native acceptance presses a real SDL virtual-gamepad R with a resumable 4/5 tour present and requires Recent Course to launch, not Tour.
- Recent Course is current-profile-context-scoped and fail-closed. A named profile can only reuse a course observed while that same profile was active; the no-profile Modern context is process-local and isolated from every named profile. Missing or invalid course identity exposes no launch action. A course already observed authoritatively may be repeated even if it is normally hidden from the generic picker, because this affordance does not reveal an unseen course.
- For a named profile, Recent Course is now durable navigation metadata. Profile codec v5 (`UR-HOST-PROFILE/5`) adds one field, `recent_track` (empty or a canonical course id 0–44); v1–v4 files still load, and an out-of-catalog or non-numeric value fails closed like every other malformed profile field (read-only defaulted profile, file never rewritten). When a newly observed course differs from the stored one, the host re-saves the in-memory profile with only `recent_track` changed. That is a metadata-only write: no live or Practice SRAM capture, no cartridge SRAM write, and no autosave-generation bump. Loading a profile seeds that profile's Recent Course, so F6 / pad Y works from MAIN_MENU in a fresh process. Native acceptance (`tests/native/run_modern_recent_course_persistence_acceptance.sh`) proves four cases: a v4 profile gains `recent_track` with byte-identical SRAM snapshot and generation; a fresh process restores a non-default course (Monster) and relaunches it as isolated Practice without touching the profile file; a malformed value fails closed without rewrite; and Authentic is inert.
- Product-navigation presses and releases are consumed before guest controller dispatch. Authentic mode neither exposes nor consumes these shortcuts.

Quick Practice launch itself is fail-closed against frontend timing and course drift. The reusable router waits the proven 60 guest frames after each stock menu surface first appears before issuing its first input, rejects an active race reached before the expected stock route completed, and requires the decoded live course identity to equal the requested Practice target before reporting `RACE_READY`. A wrong/bypassed race restores the disposable Practice snapshot and returns through the existing frontend reboot path. That Practice → Frontend transition is transactional: because the reboot request publishes the current SRAM, the profile snapshot must be restored before requesting it; if the request itself fails, the host restores the live disposable Practice SRAM, Practice save root and launch bookkeeping exactly so the session remains isolated and retryable. In-flight Practice routing exclusively owns keyboard/gamepad edges, matching the continuation router's input-ownership discipline and preventing guest menu interference. That ownership is bounded: the route times out after 3,600 observations and supports Escape or B/Start cancellation, both of which restore isolated Practice state and reboot to frontend.

The focused native acceptance now covers all three fast-navigation slices plus pre-race cancellation safety. Rematch completes a stock race, invokes the real one-action results shortcut, re-enters the authoritative active-race lifecycle and requires both the live SRAM digest and validated course identity to remain equal across the repeat. Repeat Practice does the same inside isolated Practice and additionally requires no profile autosave. Recent Course observes a live authoritative course, returns through the existing Exit Frontend lifecycle in the same process, invokes the real F6 shortcut from settled MAIN_MENU, and requires the resulting isolated Practice race to identify as the same course. The cancel fixture starts Practice with the real F5 shortcut, cancels during stock rider-select routing with Escape, and requires exact SRAM restoration plus a return to Modern MAIN_MENU without ever reaching `RACE_READY`.

**Next Event is routed for the uniquely derivable case.** The proven progression state can identify an unfinished tour and which events in that row have qualified. With one to three qualified events the player still has a choice, so Next Event is not offered. When exactly four of five qualification flags are valid and set, `next_event_derivation.hpp` derives the one remaining slot. The Modern Tour surface (F3 / pad Y at settled MAIN_MENU) then leads with a preselected `NEXT EVENT <course>` row above Resume / Restart / Back. Confirming it starts the existing Resume route (`ModernTourEntryIntent::NextEvent` carries the same restore-at-TRACK_SELECT contract and never retires continuation). After `apply_tour_resume` has restored the row at settled TRACK_SELECT, the route keeps input ownership and drives the stock track cursor to the derived slot with the same `quick_practice_track_input` policy Quick Practice uses, leaving a four-observation release gap after each observed cursor move so routed two-frame presses cannot merge. It then confirms NOW_PLAYING after the usual 60-frame settle and releases ownership when the authoritative tour race begins. Entry is verified by decoding the live course identity against the derived track (`UR_NEXT_EVENT RACE_VERIFIED ... course_equal=1`). Escape / B during selection cancels through the ordinary tour-route abort and preserves the restored progress. A race reached before the routed confirm is not reported as Next Event. There is no new progression field, picker, catalog or guest-state write. Ambiguous, complete, empty and malformed rows, Authentic mode and stale context (the action is re-resolved on confirm) all fail closed. Native acceptance (`tests/native/run_modern_next_event_acceptance.sh`, run by the onboarding/fast-repeat workflow) proves that a 2/5 row hides the action, a 4/5 row reaches the remaining event's authoritative race in one confirm, and cancellation during selection leaves the durable row and profile continuation unchanged.

## Extension points

Do not add these systems to `HostProductState` merely because they are planned. Add narrow interfaces when there is a concrete runtime consumer:

- **pause/restart:** pause and Restart Race are connected end-to-end through the typed product/runtime command surface, and the first desktop key binding is now wired through the host event loop. Escape toggles host pause; Enter resumes from pause; Ctrl+R reaches Restart Race only when the validated anchor is available. Visual pause/results presentation is present, and keyboard/controller navigation now share one platform-independent pause-input policy above the host-owned pause/menu model. Keyboard uses Escape to toggle, Up/Down to navigate, Enter to activate and Ctrl+R as the direct Restart hotkey. Controller uses Start to toggle, D-pad Up/Down to navigate, A to activate and B to cancel/resume. Restart appears only while the validated anchor is available. The host consumes these normalized product buttons before configured guest/GamepadMap dispatch, so modern menu navigation cannot leak into the SNES controller word. Focused native acceptance now drives the first deterministic restart through that actual gamepad menu path and the second through the real Ctrl+R key path, proving both player-facing inputs converge on the same accepted lifecycle restore. Remaining pause-menu work is polish and broader controller/platform UX, not another runtime or snapshot seam;
- **controls presentation/rebinding:** the Modern Controls panel and first-run Help read SNESRecomp's live P1 `keybinds.ini` state. The Controls panel now layers only cursor/capture UI state above that authority: Up/Down selects one of the framework's 12 P1 SNES controls, Enter/A begins keyboard capture, Escape/B cancels capture or closes the panel, Delete/Backspace or controller X clears, and R or controller Y resets P1 defaults. Apply/clear/reset call the pinned framework's `keybinds_set_button(1, ...)`, `keybinds_reset_player(1)` and `keybinds_save()` directly; the panel rereads `keybinds_get_button()` for presentation, so edits are immediately live and no second input map or config schema exists. Duplicate physical keys remain legal by policy. Focused native acceptance opens the real pause Controls surface, captures a replacement key, cancels a second capture, persists through the framework authority, launches a fresh executable process, reopens Controls to prove framework reload, assigns the same physical key to a second logical SNES control to prove duplicate-key semantics through the live authority, then clears and resets through the same player-facing UI. Deterministic model coverage separately preserves duplicate-key and failure semantics, while the host keeps every Controls mutation behind Modern-mode ownership. Controls gamepad navigation now defers raw physical buttons to SNESRecomp's configured GamepadMap and consumes only the resulting P1 semantic SNES controls; non-SNES framework commands and guest dispatch are suppressed while the panel owns input, and deferred releases remain paired even when B/Start closes the panel on press. Physical controller mapping therefore remains framework-owned. Controller hot-plug now has a first player-facing layer above the framework's existing seat events (`controller_hotplug_policy.hpp`): the title remembers only which opaque SDL source occupies each of SNESRecomp's two seats, shows the P1 pad's sanitized device name (or NONE) in the Controls panel, and, when the device occupying a seat is removed during a validated active-race/results surface, latches one Modern pause applied at the next completed-frame boundary through the ordinary `ur_modern_session_pause()` command with a `P1/P2 CONTROLLER DISCONNECTED` notice. Reconnection stays framework-owned (SDL/SNESRecomp choose the seat; GamepadMap bindings are unchanged) and turns the notice into `RECONNECTED`; notices retire when play resumes. Stale removals for a source that no longer owns the seat are ignored, the latch is consumed once and never carried from a menu into a later race, and Authentic mode never pauses. Native acceptance attaches a real SDL3 virtual gamepad during an authoritative race, holds a GamepadMap-mapped direction until it reaches the human P1 word, unplugs it while held, and requires the held bit to be absent from the next observed word plus a Modern pause and in-pause reconnect; the same run in Authentic must release the input without pausing. A negative control that disabled an explicit framework release-on-removal showed the word still clears, because SDL3 recenters/releases a removed device's buttons before delivering the removal event, so no framework patch was added for that case;
- **autosave/resume:** profile-local result autosave and unfinished-tour continuation are integrated. The host persists only the proven rider/tour/medal-generation/five-flag continuation, and the title adapter restores only those five flags after stock rider confirmation has performed its historical wipe. Windows x64 exposes an explicit Resume Tour / confirmed Restart Tour surface only for an authoritative active profile whose persisted and live SRAM agree across the proven continuation fields. Both actions route MAIN_MENU -> RIDER_SELECT -> saved TOUR_SELECT using ordinary stock inputs and stop at TRACK_SELECT. Resume alone restores the saved row. Restart carries typed suppression through settlement and retires metadata only after the title adapter proves stock left the row empty; cancellation, route/input failure and retirement-save failure preserve continuation; post-rider-wipe aborts roll live SRAM back from the existing exact profile snapshot before releasing control, while pre-wipe failures leave unrelated live SRAM untouched. Keyboard and mapped semantic controller navigation share the existing host-navigation vocabulary, while the displayed Bronze/Silver/Gold challenge tier is derived from the existing stock-medal challenge model rather than persisted again. Malformed/stale/mismatched state fails closed and Authentic mode never loads, routes, presents or applies continuation metadata. Broader Modern root/task navigation remains product-layer work, not a reason to widen guest-memory authority;
- **records/ghosts:** append-only run artifacts keyed by profile and course identity, sourced from observed authoritative race state;
- **racer identity:** product data associated with a profile, explicitly separate from the original save-slot/unicycle coupling;
- **settings/product UI:** `pause_on_focus_loss`, desktop display mode, presentation VSync, presentation FPS, Output Resolution, Widescreen view and Internal Render Scale have production consumers, durable desktop persistence and one shared host-owned Options home. Output Resolution is derived from the active monitor's normalized mode catalog, stores `native` or explicit dimensions, applies a concrete mode only in true Fullscreen, remains inert in Windowed/Borderless, and uses apply → persist → rollback semantics. Entering Fullscreen reconciles the current semantic resolution; stale saved dimensions recover effectively to Native without rewriting persistence. Controls, Run Data, Exit to Frontend and confirmed Quit remain at their root positions. Internal Render Scale independently selects 1x–4x presentation density without altering guest geometry. Vibration is now a real host setting. Options ends with a `VIBRATION ON/OFF` row, appended last so earlier row positions are unchanged. It persists the existing v6 `vibration_enabled` field with the same persist-then-commit rule as Focus Pause. The stock title emits no rumble, so every pulse is a host presentation choice tied to an event the host already observes authoritatively (`haptic_feedback_policy.hpp`): a short light pulse at each new checkpoint split and one firmer pulse when the race reaches results. Pulses fire only for a supported Modern 1P timed race (the same run-capture gate as the timing HUD, so 2P/VS, Practice and replays stay silent), only to the controller in the P1 framework seat, never while paused, and never in Authentic. Native acceptance (`tests/native/run_modern_vibration_acceptance.sh`) covers three things. First, it turns Vibration off through the real pause → Options keys and checks that `vibration_enabled=0` persists. Second, with Vibration on, a real SDL virtual gamepad's Rumble callback receives exactly the pulses the host sent during a Dragster race (three checkpoints plus the finish). Third, a fresh process using the persisted off value stays silent and produces the same authoritative race outcome (course, elapsed time, every split and the race-relative controller stream; only the jitter-prone post-finish frame count and its checksum are excluded), so vibration never touches simulation; Authentic is also silent. Volume follows Vibration as the last Options row. It is deliberately not duplicated into `HostSettings`: SNESRecomp already owns `[Sound] Volume` (0..100 in config.ini, keypad +/- in 5% steps, an OSD bar), and `tools/patches/snesrecomp-live-volume.patch` only exposes get/step accessors that reuse that sole framework authority. Left/Right (or the d-pad) on `VOLUME < n% >` step it down or up; A/Enter steps up. The framework saves it to config.ini on exit and Modern keeps no copy in host state. Native acceptance (`tests/native/run_modern_volume_acceptance.sh`) lowers it with the real keys from an authoritative race, checks config.ini and the unchanged host state, and proves a fresh process loads the new value. Overlay text follows one rule: every line fits inside its panel at 1x. Text is drawn in 8-pixel cells inside an 8-pixel margin, so the shared 212-pixel pause-family panel holds 24 cells and a 240-pixel panel holds 28 (`modern_overlay_text_fit.hpp`). Fixed hints are written to that budget; dynamic rows built from live key bindings, device names or profile names are fitted rather than allowed to spill over the game. Reduced flashing has no clean seam in the shipped build: SNESRecomp's presentation frame blend is compiled only with the recomp-ui launcher, which the product build disables. Readable text remains a product/UI layout task, not another presentation-density authority. `native/product/modern_text_layout.hpp` now supplies the pure fitting policy: Standard uses the existing logical glyph metrics; Large doubles logical glyph/line metrics only when the caller's content envelope still fits its existing logical panel; an oversized Large request falls back to Standard, while content that cannot fit Standard fails closed for explicit reflow/shortening. Final raster scale is derived only after fitting as logical text scale multiplied by the existing 1x-4x presentation density. No persisted readable-text setting or host integration exists yet, deliberately: surfaces must adopt the layout contract before a user-facing toggle can be truthful.

Network transport, accounts, cloud persistence and hosted leaderboards remain outside this architecture.

## Validation contract

Every host-state schema or transition must have deterministic tests. At minimum:

1. default state has one exact serialized representation;
2. encode → decode → encode is byte-stable;
3. malformed, duplicate and unknown fields fail closed;
4. Authentic policy exposes no host profile/settings/modern-command capability;
5. no new host schema field may silently acquire guest simulation or cartridge-save authority;
6. Authentic session control rejects every modern command without changing phase;
7. session actions are emitted deterministically, one at a time, and redundant pause/resume requests are explicit no-ops;
8. a race-restart anchor is captured at most once until explicitly cleared;
9. failed capture/restore attempts fail closed without replacing a valid anchor or synthesizing guest state;
10. focus-loss pause policy is enabled only by Modern host-settings authority, respects the typed setting and current pause state, and is inert in Authentic mode;
11. persisted host state must decode through the exact versioned schema, reject malformed/oversized content, and remain entirely unread by Authentic product policy.
12. per-profile persistence must round-trip exact stock-SRAM mirrors across process restart, default missing/malformed profiles deterministically without overwriting malformed files, and reject all load/save/capture/restore authority in Authentic mode.

The host-state and session-control C++ contracts are compiled and executed from `tests/unit/test_host_product_state_cpp.py` and `tests/unit/test_session_control_cpp.py`, so both participate in the lightweight project tooling test surface without requiring the external SNESRecomp build.

## Fidelity versus product policy

The distinction is explicit:

- reproducing the original frontend, racer/save-slot coupling and SRAM progression is a **fidelity** concern;
- choosing independent profiles, host settings, autosave UX, pause/restart UX, records and ghosts is **modern product policy**;
- a product-policy feature is acceptable only while the Authentic path stays reproducible and authoritative race behavior remains unchanged.

PR #213 closed the stock gameplay-authored progression/save-load acceptance gap. That evidence is the reason this layer can now treat SRAM as a proven guest-owned substrate rather than commandeering it as a modern profile store.


## Widescreen product binding

Modern Options owns a persisted `VIEW` setting with `Original` and `16:9` choices. It stays inside host product state, defaults to Original, and is inert in Authentic execution mode. The existing `URRECOMP_WS_VIEW` environment selector remains only as a deterministic diagnostic override.

The setting changes presentation only. Evidence-backed active 1P, ordinary-2P and VS race scenes use the accepted host-owned widened composition while frontend, transitions, results and unknown scenes remain fixed/centred and fail closed to the stock PPU path. Per-viewport course-model margins remain presentation data rather than widened guest simulation or activation state. Output Resolution, Display Mode, VSync, Presentation FPS and internal render density are independent axes.

Host-state codec v6 now follows the catalog's additive-key rule: its seven historical core keys remain required, `widescreen` is a known optional v6 key whose absence defaults to `original`, and unknown keys still fail closed. This keeps already-written v6 files readable without inventing a schema bump for one optional setting.

### Completed-run records / replay foundation

native/product/completed_run_record.*, completed_run_capture.*, completed_run_store.* and completed_run_comparison.* own the host-only records substrate. The framework exposes the exact controller word submitted to `RtlRunFrame`; the title adapter derives canonical course identity from immutable decoded-header fields; timing and splits remain in authoritative guest units. Modern 1P attempts begin at the same race-entry boundary used by Retry, Retry aborts/re-arms capture, and finalized records append beneath the active profile using a strict versioned/checksummed codec. Compatible records supply Previous/PB candidates, exact signed deltas and canonical deterministic replay input without acquiring guest-memory authority.

The product layer consumes that substrate in three presentation surfaces without changing authority. Local Runs presents the active profile's catalog, keeps malformed/incompatible artifacts visible but disabled, launches a selected compatible record through the established deterministic input/restart path, and shows the selected run's exact signed delta versus the canonical PB. Previous/PB ghosts load only checksum-bound trace sidecars, perform race-relative lookup and current-camera projection, reuse the Racer-HD semantic/composition selector, and blend as host-only presentation. Supported Modern 1P timed Race play now also shows a compact exact timing panel: current/finish time, compatible PB, checkpoint delta only at an authoritative named split, and finish delta on results. Missing/stale/incompatible data fails closed, Authentic/non-1P modes gain no record, ghost or timing-overlay authority, and the stock results/score presentation remains intact. Remaining work is richer lap/split history, unified records/statistics browsing and local-management polish rather than a second records, replay or ghost data model; see `COMPLETED-RUN-RECORDS.md`, `COMPLETED-RUN-BROWSER.md` and `GHOST-PRESENTATION-TRACE.md`.

## Regional presentation profile

Modern owns one hidden global regional-presentation value: `NorthAmerica` or `Europe`. It exists to reproduce evidence-backed Uniracers-versus-Unirally presentation differences while keeping one authoritative gameplay runtime.

The feature is intentionally absent from ordinary Options. At the accepted idle title surface, keyboard text `PAL` / `NTSC` and semantic controller input Left Left Left L A / Right Right Right R A select Europe or North America. Recognition is host-semantic, timeout-bounded, text-entry-aware and inert outside Modern's accepted title context.

The state has presentation authority only. It cannot alter guest cadence, physics, collision, AI, RNG, timers, stunt scoring, progression, SRAM, completed-run identity, replay semantics or PB comparability. It is global host administrative state rather than profile progression. On durable-storage-capable platforms it survives a fresh process; profile changes do not alter it. Malformed/unknown persisted values fail safely to North America, while Authentic execution remains observationally inert to the stored value.

The implementation substrate is `regional_presentation.hpp`, `regional_presentation_secret.*` and `regional_presentation_runtime.*`. Host-state schema v6 treats `regional_presentation` as a known additive field. The runtime adapter changes only that field and reports `SaveRequired` only for a real transition, leaving existing host-store/platform adapters responsible for durable I/O.

Exact presentation consumers remain evidence-driven. The first intended consumer is title/logo branding. A successful secret should also use an evidence-backed original frontend transition primitive rather than a bespoke modern effect: prefer stock horizontal movement, with PAL/Left revealing Unirally leftward and NTSC/Right revealing Uniracers rightward; if the captured original title transition is a better isolated primitive, use that instead, with a stock palette fade only as fallback. The transition remains presentation-only and cannot reboot or retime the authoritative guest merely for visual effect. Other frontend or course-local regional differences require retained evidence from `docs/REGIONAL-PRESENTATION.md`; no executable/timing difference becomes presentation policy by inference alone.
