# Modern Product Layer

This document owns intentional modern product policy and the host/runtime boundary that implements it. It does not redefine stock fidelity. Historical behavior remains documented by the existing UI, progression, SRAM and semantic evidence surfaces.

## First seam: host administrative state

The first project-owned modern seam is deliberately small: independent host-side profile selection and settings.

The implementation lives in `native/product/host_product_state.{hpp,cpp}`. Its persisted envelope contains only:

- an optional opaque host profile ID;
- vibration enabled/disabled;
- pause-on-focus-loss enabled/disabled.

This state is administrative host state. It has no WRAM addresses, SRAM layout, racer slots, medal values, league state, course state, timers, physics state or other cartridge-era semantics.

The current codec is intentionally dependency-free and deterministic. Version 1 writes one canonical byte representation and rejects duplicate, unknown or malformed fields. The platform-specific file location and write strategy are left to the eventual shipping host shell.

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

## Extension points

Do not add these systems to `HostProductState` merely because they are planned. Add narrow interfaces when there is a concrete runtime consumer:

- **pause/restart:** pause and Restart Race are connected end-to-end through the typed product/runtime command surface, and the first desktop key binding is now wired through the host event loop. Escape toggles host pause; Enter resumes from pause; Ctrl+R reaches Restart Race only when the validated anchor is available. Remaining work is visual pause/results presentation and controller navigation, not another runtime, snapshot or keyboard-event seam;
- **autosave/resume:** a coordinator that owns host save metadata while preserving guest SRAM as guest data;
- **records/ghosts:** append-only run artifacts keyed by profile and course identity, sourced from observed authoritative race state;
- **racer identity:** product data associated with a profile, explicitly separate from the original save-slot/unicycle coupling;
- **settings:** typed host options whose ownership and Authentic-mode fallback are explicit.

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
9. failed capture/restore attempts fail closed without replacing a valid anchor or synthesizing guest state.

The host-state and session-control C++ contracts are compiled and executed from `tests/unit/test_host_product_state_cpp.py` and `tests/unit/test_session_control_cpp.py`, so both participate in the lightweight project tooling test surface without requiring the external SNESRecomp build.

## Fidelity versus product policy

The distinction is explicit:

- reproducing the original frontend, racer/save-slot coupling and SRAM progression is a **fidelity** concern;
- choosing independent profiles, host settings, autosave UX, pause/restart UX, records and ghosts is **modern product policy**;
- a product-policy feature is acceptable only while the Authentic path stays reproducible and authoritative race behavior remains unchanged.

PR #213 closed the stock gameplay-authored progression/save-load acceptance gap. That evidence is the reason this layer can now treat SRAM as a proven guest-owned substrate rather than commandeering it as a modern profile store.
