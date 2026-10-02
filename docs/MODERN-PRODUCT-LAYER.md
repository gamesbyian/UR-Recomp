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
| Session control | future explicit runtime adapter | pause/resume/restart/exit requests |

A modern profile is not a renamed unicycle/save slot. Racer identity and progression can later be associated with a profile by higher-level product policy, but the storage primitives remain independent.

## Session-control seam

`native/product/session_control.{hpp,cpp}` defines the first runtime-facing modern control contract without implementing runtime side effects.

The contract accepts four modern administrative commands:

- pause;
- resume;
- restart race;
- exit to frontend.

A successful command emits exactly one typed `RuntimeAction` for a future runtime adapter to consume. The contract itself never writes guest memory, SRAM, timers, physics, menu state or progression. Pause/resume maintain only a host-owned running/paused phase. Restart and exit are requests, not implementations.

The queue is deliberately single-action and fail-closed: while one action is awaiting consumption, later requests return `Busy` rather than being reordered or coalesced implicitly. Redundant pause/resume requests return `NoOp`. Authentic mode rejects every session command by policy and never changes host session phase.

This gives the eventual native host a narrow integration point:

1. the product/UI layer requests a command;
2. `SessionControl` validates modern policy and transition ordering;
3. the runtime adapter consumes the emitted action;
4. the adapter performs the platform/runtime operation;
5. runtime-specific restart semantics receive their own deterministic acceptance before shipping.

In particular, `RuntimeAction::RestartRace` does **not** mean "write known starting values into WRAM." The future implementation must re-establish a valid race start through an owned runtime lifecycle boundary, with authoritative simulation initialized by the guest/runtime path.

### Pinned SNESRecomp pause adapter

The pinned SNESRecomp desktop host already owns a suitable pause mechanism. Its existing `g_paused` path:

- keeps pumping host events while paused;
- pauses host audio;
- resets presentation pacing debt;
- skips `RtlRunFrame`, so the guest does not advance.

`tools/patches/snesrecomp-session-pause.patch` exposes only that existing host state through `snesrecomp_desktop_set_paused()` and `snesrecomp_desktop_is_paused()`. It does not introduce a new emulation mechanism.

`native/product/session_runtime_adapter.{hpp,cpp}` maps `SuspendGuest` and `ResumeGuest` onto this narrow host hook. The same adapter explicitly refuses `RestartRace` and `ExitToFrontend` until those operations have owned runtime semantics. This is intentional: the framework's machine reset/save-state facilities are not evidence that a product-level "restart this race" command is correct.

The pause integration therefore has a clean ownership chain:

`modern UI/policy -> SessionControl -> RuntimeAction -> pause runtime adapter -> existing host frame gate`

At no point does the pause path write guest memory or reinterpret stock pause/menu state.

### Race-restart anchor

Modern **Restart Race** is a host-product feature; the original pause flow exposes Continue/ Quit rather than a stock restart command. The implementation should therefore reproduce a valid initialized race state, not invent a guest input chord or reinterpret console reset.

`native/product/race_restart_anchor.{hpp,cpp}` owns one exact in-memory machine snapshot for the current attempt. It is intentionally ignorant of Uniracers WRAM layout. Its lifecycle owner decides when a race has reached the accepted restart boundary, then calls `capture()` once. Later `restart()` restores those exact bytes through runtime-supplied snapshot hooks.

The intended native binding is the existing SNESRecomp whole-machine API:

- `RtlSaveSnapshotToMemory()` for capture;
- `RtlLoadSnapshotFromMemory()` for restart.

That path includes the machine/save-state domains already owned by the runtime instead of reconstructing race state field by field. The anchor uses the same conservative 2 MiB first-probe ceiling as the framework rewind/state tests and fails closed if capture does not fit or the runtime refuses it.

For Uniracers, the current candidate lifecycle edge is the already established transition into active gameplay, `7E:0313 = 0 -> 1`, observed at a completed host frame through the title-specific `after_run_frame` hook. The exact capture frame still requires a native acceptance fixture before this becomes the shipping restart boundary. The anchor itself does not hard-code `$0313`, because state detection belongs to the title adapter rather than the storage primitive.

A restart anchor is immutable for one attempt. Repeated capture requests do not silently move the restart point.

`RaceRestartLifecycle` owns the attempt-to-attempt policy above that storage primitive. A false→true active-race edge clears any previous anchor and captures the newly initialized race. A true→false edge does **not** clear the anchor: the just-finished attempt remains restartable through results or other post-race host UI. The next actual race entry supersedes it. If that new capture fails, the previous race is not retained as a misleading fallback.

The lifecycle receives only an `active` boolean; it does not know the Uniracers WRAM address that supplies it. That title-specific binding remains outside the reusable product layer.

`SessionRuntimeHooks::restart_race` is now optional. If no proven restart implementation is attached, the dispatcher returns `MissingHook`; if the runtime refuses a restore, it returns `RejectedByRuntime`. This keeps a UI button from becoming evidence that restart semantics are actually available.

## Extension points

Do not add these systems to `HostProductState` merely because they are planned. Add narrow interfaces when there is a concrete runtime consumer:

- **pause/restart:** pause is connected to the owned host frame gate; wire the restart anchor into the generated Uniracers title hook and prove deterministic race re-entry before treating restart as complete;
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
