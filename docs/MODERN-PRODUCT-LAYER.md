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

The first real runtime consumer of a typed setting is `pause_on_focus_loss`. `native/product/focus_pause_policy.hpp` reduces the decision to four explicit inputs: execution mode, typed host settings, current focus state and current host-pause state. In Modern mode, the ordinary Uniracers desktop binding samples SDL keyboard focus from its existing completed-frame callback and routes a qualifying focus loss through the same `ur_modern_session_pause()` command path used by player pause input. The policy is title-gated to the established active-race/results surfaces, never writes guest state, and is inert in Authentic mode. Desktop display mode remains the next accepted consumer: Options now exposes Windowed, Borderless and Fullscreen, while a narrow SNESRecomp desktop-host interface owns the concrete window operation. SDL2 preserves its distinct borderless-desktop and exclusive-fullscreen paths; SDL3 deliberately collapses both fullscreen semantics to its single fullscreen operation without leaking that platform detail into product code. VSync is the third real setting: Options exposes Off, On and Adaptive through the same keyboard/controller cursor model, while a narrow project patch exposes SNESRecomp's existing live renderer VSync policy through `snesrecomp_desktop_set_vsync()`; renderer-specific swap-interval/reconfiguration remains framework-owned. Presentation FPS is the fourth: Options exposes Game, 60, 90, 120, 144 and Native by binding the generated title host to SNESRecomp's existing `presentation_hz` hook. Game preserves lockstep presentation at authoritative guest cadence. Positive targets use the host's separate presentation clock to re-present captured frames between simulation ticks; changing the target resets only that host clock and recomputes the live VSync interval. These are presentation controls only. They do not change guest cadence, timers, physics, AI, RNG, animation-state selection, input semantics, progression, records or SRAM. Internal Render Scale is now a production consumer too: Options cycles 1x through 4x, persists the choice in schema v6, and binds it to the Racer HD compositor's host-owned output buffer. The logical guest raster remains independent, while unsupported or unregistered presentation states continue to fall back to the original 1x frame. The current Racer HD compositor owns only the stock-width logical surface, so an active Widescreen world-expansion scene deliberately resolves presentation density to 1x rather than allocating a scaled buffer and then falling through with undefined pixels; HD density resumes on supported fixed-width scenes. Modal product overlays and host hints likewise present at 1x until the overlay renderer owns an explicit density transform, preventing 1x-coordinate menus from shrinking into a corner of a 2x–4x surface. The framework's frozen-frame and frame-blend staging buffers are sized for the full 4x contract so pause overlays and optional blending remain safe at every accepted scale. Native smoke now gates the production callback chain with a persisted 2x state, a real registered Racer HD draw, and an exact 512x448 presented-frame artifact rather than accepting settings diagnostics alone. Authentic mode never applies the setting. `F` remains an optional Focus Pause shortcut.

`native/title/uniracers_run_data.{h,cpp}` is the title-specific read-only bridge for the first Run Data view. It decodes the already-promoted authoritative timer digits at `7E:0E0F/0E13/0E17/0E1B/0E1F` into typed minutes, seconds, tenths and six-step sub-tick data, validates every digit, and exposes no write interface. The generic product UI therefore never owns Uniracers WRAM offsets. Native run `37108042695` independently decodes the same race-entry WRAM dump in CI and requires the product diagnostic to report the exact matching timer/sub-tick before accepting the subview.

`native/product/host_product_store.{hpp,cpp}` provides the versioned codec's persistence backend without owning schema semantics. The shared store accepts an explicit path, bounds reads, and rejects unsupported, malformed or oversized state. The desktop host owns placement: `UR_HOST_STATE_PATH` is an explicit development/acceptance override; otherwise SDL's platform preference directory deliberately retains the legacy `host-state-v1.txt` filename so existing Version 1/2/3/4 files are discovered and migrated in place when next saved as Version 5. Modern mode loads once before session creation and commits in-session setting changes only after the canonical state saves successfully; display-mode, VSync and presentation-FPS changes roll the live host policy back if persistence fails. Authentic mode does not load the file at all. Native run `37168499605` proves the generated host opens Options, toggles Focus Pause, advances Display through Borderless to Fullscreen, selects Adaptive VSync, selects 120 Hz presentation, saves schema v5, reloads all four settings in a fresh process, and leaves the same modern state unapplied and unloaded in Authentic mode. The same run separately proves the 120 Hz host clock emits repeated presents across a bounded guest-frame run rather than increasing guest simulation cadence.

## Independent modern profile persistence

Modern profile storage is now a separate versioned substrate rather than an expansion of the global settings envelope. `native/product/host_profile_state.{hpp,cpp}` owns one typed profile payload and `host_profile_store.{hpp,cpp}` owns bounded file I/O. Version 1 stores an opaque profile ID, a monotonic autosave generation and an optional exact 8 KiB stock-SRAM mirror. The mirror is intentionally uninterpreted here: progression meaning stays with the guest/SRAM semantic layer, while profile ownership stays with the host product layer.

This is the ownership boundary for independent modern saves. Original racers remain content/identity, never save slots. A future profile catalog may point at one profile file per modern player, and future racer identity, records and ghosts may attach beside this progression payload without changing cartridge SRAM layout.

The only guest-facing operations are narrow `capture_stock_sram_for_profile()` and `restore_stock_sram_from_profile()` calls. Both are rejected by `ExecutionMode::Authentic`; no profile file is readable or writable through this API under Authentic policy. Modern capture requires an exact 8192-byte buffer and increments the autosave generation only after a complete copy. Restore requires the same exact extent and a previously captured snapshot. Neither function understands medals, tours, racers or frontend state.

Profile writes use a temporary sibling file and replace the destination only after a complete flush/close, so a failed write does not truncate the last accepted profile state. Reads are bounded, exact-profile-ID matched and fail closed on malformed input. Missing or malformed profile files resolve to a fresh in-memory typed profile with generation zero; malformed files are preserved rather than silently overwritten. This is the real migration bridge for older global `HostProductState` files: an existing v1-v5 active profile ID can resolve into the new per-profile substrate even though no profile file existed when that host state was written. The existing global `HostProductState` v1-v6 decoder remains the authority for those older envelopes.

The native acceptance helper is deliberately process-oriented: one invocation writes a Modern profile, a fresh invocation reloads and restores the exact SRAM bytes, another decodes a real legacy global host-state profile selection and proves missing-profile defaulting, another proves malformed profile state defaults in memory while the bad file is preserved, and an Authentic invocation proves resolve/capture/save are all inert. This lands the durable seam needed for autosave/resume without yet choosing when the shipping host should capture or reapply guest SRAM. That lifecycle decision belongs to the next product slice, not to the storage codec.

The runtime ownership step is now explicit as well. `native/product/host_profile_runtime.{hpp,cpp}` maps execution mode plus the active opaque profile ID to the framework save namespace. The ordinary desktop host binds that decision through `SnesDesktopHostGame.after_config`, which executes before ROM initialization and the framework's `RtlReadSram()`. Authentic mode and Modern sessions without an active profile reset to the framework's ordinary `saves` root. A Modern active profile selects the framework-creatable flat root `saves/profile-<profile-id>` (with `UR_PROFILE_SAVE_ROOT` reserved as a deterministic development/acceptance override) and asks the framework to create that root before guest SRAM is loaded.

This reuses SNESRecomp's existing `RtlSetSaveRoot()` contract, already designed for isolated content/netplay save namespaces, rather than copying bytes into guest SRAM after startup. Consequently profile A, profile B and Authentic do not share the same cartridge SRAM backing file. The guest still owns the exact 8 KiB contents and all medal/checksum/tour semantics; the host only chooses which profile-owned backing namespace the framework opens. This is the required isolation boundary before any Modern tour-resume repair can be allowed to write the otherwise stock-owned tour-flag table.

## Authentic versus Modern policy

`ExecutionMode::Authentic` is the regression/reference policy. In this mode:

- host profiles do not participate in game behavior;
- host settings do not override stock behavior;
- modern administrative commands are disabled;
- the original guest frontend/progression/SRAM path remains the behavior under test.

`ExecutionMode::Modern` enables host-owned product facilities. Enabling it does not grant permission to mutate authoritative race simulation. Modern features must cross an explicit runtime adapter whose effects are independently testable.

The host-state store may physically exist while Authentic mode is active, but its contents must be observationally inert with respect to guest behavior.

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

A successful command emits exactly one typed `RuntimeAction` for the runtime adapter to consume. The contract itself never writes guest memory, SRAM, timers, physics, menu state or progression. Pause/resume maintain only a host-owned running/paused phase. `ModernSessionRuntime` is the smallest product coordinator above that contract: it owns policy-gated lifecycle observation and dispatch, while `modern_session_c_api.{h,cpp}` exposes the same narrow surface to the generated C host and later pause/results UI. Exit to Frontend remains request-only/unsupported at the current runtime adapter.

The queue is deliberately single-action and fail-closed: while one action is awaiting consumption, later requests return `Busy` rather than being reordered or coalesced implicitly. Redundant pause/resume requests return `NoOp`. Authentic mode rejects every session command by policy and never changes host session phase.

This gives the eventual native host a narrow integration point:

1. the product/UI layer requests a command;
2. `SessionControl` validates modern policy and transition ordering;
3. the runtime adapter consumes the emitted action;
4. the adapter performs the platform/runtime operation;
5. runtime-specific actions must have deterministic acceptance before shipping; Restart Race now satisfies that requirement through PR #235, while Exit to Frontend does not yet have an implementation.

In particular, `RuntimeAction::RestartRace` does **not** mean "write known starting values into WRAM." The accepted implementation restores the exact rollback snapshot captured at the owned active-race lifecycle boundary, preserving authoritative guest/runtime initialization.

### Pinned SNESRecomp pause adapter

The pinned SNESRecomp desktop host already owns a suitable pause mechanism. Its existing `g_paused` path:

- keeps pumping host events while paused;
- pauses host audio;
- resets presentation pacing debt;
- skips `RtlRunFrame`, so the guest does not advance.

`tools/patches/snesrecomp-session-pause.patch` exposes only that existing host state through `snesrecomp_desktop_set_paused()` and `snesrecomp_desktop_is_paused()`. It does not introduce a new emulation mechanism.

`native/product/session_runtime_adapter.{hpp,cpp}` maps `SuspendGuest` and `ResumeGuest` onto this narrow host hook. For `RestartRace`, the adapter now accepts the proven `RaceRestartLifecycle` directly and invokes its exact rollback-backed restore path; the older callback slot remains only as a compatibility fallback for isolated consumers. After a successful restore the adapter calls the host reconciliation hook, which the native binding maps to the existing audio fast-forward recovery path so stale pre-restart PCM is discarded without mutating guest/APU state. `ExitToFrontend` remains unsupported.

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

Modern main-menu Quick Practice is available through `F5` or controller X. It does not write a course ID, menu byte, physics state or race-start structure directly. Instead it observes the already-proven stock frontend states and feeds ordinary A-button pulses through SNESRecomp's existing deterministic input parser when those stable menu states are visible at a host observation boundary:

`MAIN_MENU (D7) -> RIDER_SELECT (3C) -> TOUR_SELECT (6D) -> TRACK_SELECT (F6) -> NOW_PLAYING (16) -> active race (0313=01)`.

That keeps the ordinary guest frontend and race initializer authoritative for the practice attempt. The current path deliberately accepts the default first rider/tour/track, yielding a representative first race without duplicating tournament-selection semantics. Broader direct track selection can remain a later practice-product refinement.

Practice is non-progressing Modern product state. At launch, the host snapshots the exact 8 KiB guest SRAM and switches framework persistence to an isolated practice save root. Modern profile autosave and completed-run capture are disabled while practice is active. Choosing the existing Pause > Exit Frontend path restores the exact pre-practice SRAM bytes and original save root before the already-accepted full session reboot publishes SRAM and reconstructs the stock frontend. A small in-race hint makes that return path discoverable. Authentic mode cannot enter this path.

The dedicated native acceptance requires first-run visibility/dismissal persistence, rendered live keyboard/controller binding diagnostics, stock-input-driven launch into authoritative active-race state, byte-identical pre/post-practice SRAM digests, clean return to main menu, absence of profile autosave during practice, and complete Authentic inertness. Intermediate menu IDs are diagnostic rather than mandatory because stock transitions can cross them between host observation boundaries.

## Extension points

Do not add these systems to `HostProductState` merely because they are planned. Add narrow interfaces when there is a concrete runtime consumer:

- **pause/restart:** pause and Restart Race are connected end-to-end through the typed product/runtime command surface, and the first desktop key binding is now wired through the host event loop. Escape toggles host pause; Enter resumes from pause; Ctrl+R reaches Restart Race only when the validated anchor is available. Visual pause/results presentation is present, and keyboard/controller navigation now share one platform-independent pause-input policy above the deterministic two-row menu. Keyboard uses Escape to toggle, Up/Down to navigate, Enter to activate and Ctrl+R as the direct Restart hotkey. Controller uses Start to toggle, D-pad Up/Down to navigate, A to activate and B to cancel/resume. Restart appears only while the validated anchor is available. The host consumes these normalized product buttons before configured guest/GamepadMap dispatch, so modern menu navigation cannot leak into the SNES controller word. Focused native acceptance now drives the first deterministic restart through that actual gamepad menu path and the second through the real Ctrl+R key path, proving both player-facing inputs converge on the same accepted lifecycle restore. Remaining pause-menu work is polish and broader controller/platform UX, not another runtime or snapshot seam;
- **controls presentation:** the Modern Controls panel and first-run Help read SNESRecomp's live P1 `keybinds.ini` view for keyboard controls and describe the framework-normalized SNES pad controls for controller play. Help also explains jump, brake, wheel-down landing and the stunt-to-speed loop while deliberately preserving secrets. This is read-only presentation: SNESRecomp remains the sole keyboard/gamepad mapping authority and still produces the exact controller word submitted to the guest. The framework already has a live binding editor/reload path; exposing that editor directly from the title is a later host-integration slice, not a reason to duplicate mapping state in UR-Recomp;
- **autosave/resume:** a coordinator that owns host save metadata while preserving guest SRAM as guest data;
- **records/ghosts:** append-only run artifacts keyed by profile and course identity, sourced from observed authoritative race state;
- **racer identity:** product data associated with a profile, explicitly separate from the original save-slot/unicycle coupling;
- **settings/product UI:** `pause_on_focus_loss`, desktop display mode, presentation VSync, presentation FPS, Output Resolution, Widescreen view and Internal Render Scale have production consumers, durable desktop persistence and one shared host-owned Options home. Output Resolution is derived from the active monitor's normalized mode catalog, stores `native` or explicit dimensions, applies a concrete mode only in true Fullscreen, remains inert in Windowed/Borderless, and uses apply → persist → rollback semantics. Entering Fullscreen reconciles the current semantic resolution; stale saved dimensions recover effectively to Native without rewriting persistence. Controls, Run Data, Exit to Frontend and confirmed Quit remain at their root positions. Internal Render Scale independently selects 1x–4x Racer HD compositor density without altering guest geometry. Vibration and additional proven settings remain future work.

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

Modern Options now owns a persisted `VIEW` setting with `Original` and `16:9` choices. It stays inside host product state, defaults to Original, and is inert in Authentic execution mode. The existing `URRECOMP_WS_VIEW` environment selector remains only as a deterministic diagnostic override.

The setting changes presentation only. Active evidence-backed 1P and ordinary-2P race scenes may request the accepted 342×224 logical view over +48 backing; frontend, transitions, results, unknown races and VS remain fixed-center. A title-owned dynamic native-wide callback keeps those fixed scenes on the stock PPU raster path. Output Resolution, Display Mode, VSync and Presentation FPS remain independent settings.

Host-state codec v6 now follows the catalog's additive-key rule: its seven historical core keys remain required, `widescreen` is a known optional v6 key whose absence defaults to `original`, and unknown keys still fail closed. This keeps already-written v6 files readable without inventing a schema bump for one optional setting.

### Completed-run records / replay foundation

native/product/completed_run_record.*, completed_run_capture.*, completed_run_store.* and completed_run_comparison.* now own the host-only records substrate. The pinned desktop framework exposes the exact controller word actually submitted to RtlRunFrame through the existing post-frame stats callback; the title adapter derives the canonical USA course ordinal from immutable decoded-header fields while ignoring the known mutable resource cursor. Modern 1P attempts start at the same authoritative race-entry boundary used by Retry, successful Retry explicitly aborts/re-arms the recorder, results finalization attaches exact guest-timer/split metadata, and records append beneath runs/<active-profile>/ in the app preference root. The codec is strict/versioned/checksummed, compatible records can supply previous-run/PB candidates and exact signed deltas, and record input exports directly to the existing INPUT_FILE replay path. `completed_run_presentation.*` now provides the first reusable run-data view model above that substrate: exact 60 Hz values are formatted without collapsing to host wall-clock precision, PB/previous targets receive explicit presentation labels, and live split/finish observations reuse the canonical signed-delta arithmetic instead of inventing a second comparison rule. This layer reads immutable completed-run evidence only and has no guest-memory or controller-submission authority. Authentic mode and non-1P modes gain no record authority. The first visible Previous/PB ghost renderer is now attached downstream of this substrate for Modern 1P races: it loads only the exact checksum-bound selected trace, performs race-relative lookup and current-camera projection, reuses the Racer-HD semantic/composition selector, and blends through a host-only render-style contract. Missing/incompatible trace or pose data fails closed, and Authentic mode remains inert. Local ghost management and richer records/replay browsing remain follow-on product work; see COMPLETED-RUN-RECORDS.md.
