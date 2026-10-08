# Ghost Presentation Trace Seam

Status: authoritative world-state sampling, live Modern 1P capture, strict checksummed trace persistence, exact ordinary-1P live-camera projection, and the first visible presentation-only renderer attachment are implemented.

## Purpose

A completed-run artifact already preserves deterministic race-relative input, exact 60 Hz timing and replay provenance. That is sufficient to reproduce the authoritative simulation, but it is not by itself sufficient to draw a ghost inside a different live run without either:

1. running a second authoritative replay instance; or
2. retaining presentation observations from the original authoritative run.

Do not infer a trajectory from controller input in a host-side physics model.

## Minimal captured state

`native/product/completed_run_ghost_world_sample.*` defines a read-only P1 sample sourced directly from promoted USA-retail WRAM semantics:

- `7E:0411`: world X;
- `7E:0415`: world Y;
- `7E:04C7`: pitch/orientation;
- `7E:0BA1`: facing;
- `7E:0FE9`: semantic racer presentation ID;
- `7E:150C`: authoritative P1 sprite attribute byte, including H/V flip;
- the synchronized Racer-HD composition tuple already consumed by `RacerGuestSnapshot`: primary IDs `0FE9/0FEB`, companion IDs `0D3F/0D41`, selectors `0C83/0C85`, and companion gates `0D1B/0D1D`.

The sample also carries the race-relative frame ordinal supplied by the completed-run lifecycle owner.

These are observations of the original simulation. The extractor exposes no guest write path, controller path or simulator callback.

## Why world coordinates, not OAM

The existing Racer-HD/OAM presentation work can recover semantic pose and on-screen sprite placement. Historical OAM coordinates, however, are relative to the historical run's camera.

A ghost must be projected through the **current live camera**. Therefore a durable ghost trace must retain camera-independent world state and let the established presentation path perform projection later. Copying prior-run screen coordinates would make the ghost drift incorrectly whenever the current run and target run use different camera positions.

## Persistence decision

The first durable representation is now a separate `.urghost` presentation trace. It is versioned, strictly parsed, checksummed independently, and bound to one exact `.urrun` artifact through the run artifact's canonical checksum.

This keeps the deterministic replay grammar unchanged. A stale trace from a different run reports `Incompatible`; checksum damage reports `Corrupt`; malformed/unknown fields fail closed; missing files are an ordinary presentation I/O failure. The completed-run artifact remains usable even when no trace exists.

The trace representation preserves these rules:

- deterministic replay remains defined by the existing input/provenance record, not by the ghost trace;
- trace samples are presentation evidence only;
- missing trace data must disable the visual ghost cleanly rather than affect gameplay;
- Circuit and Stunt remain inert until their distinct semantics are explicitly modeled;
- Authentic mode remains unchanged.

Filesystem round-trip persistence is covered by focused native acceptance. `CompletedRunGhostTraceCapture` supplies the host-independent lifecycle seam: it begins with a race attempt, accepts strictly increasing race-relative samples, aborts cleanly, and finalizes only against a validated completed-run record whose frame window contains every sample. The Modern host now calls that lifecycle from the authoritative 1P capture boundary and writes the sibling trace only after the corresponding completed-run artifact finalizes successfully. A `.urghost` is written and closed in an atomically reserved hidden staging directory on the same filesystem, then published to its checksum-bound sibling name with a rename. Readers can therefore observe only a complete old/new trace, not the bytes of an in-progress write. Existing sidecars may still be atomically replaced for repair; a special-file destination is refused. A crash before publish can strand an ignored `.pending-urghost-*` directory without exposing a truncated public trace. This guarantees publication visibility, not power-loss `fsync` durability. Trace-save failure remains presentation-only and never invalidates the run artifact.

`completed_run_ghost_projection.*` now implements the ordinary-1P coordinate/culling portion of `Race_BuildRacerOAMState` exactly from the retained historical world sample plus the current live camera/viewport context (`0419/041D`, `03ED`, `0421/0423`, `0D49`). It emulates the original 65816 sign-flag comparisons rather than substituting approximate signed arithmetic, and fails closed for the alternate `$0DDB` projection path. Focused acceptance now also holds one retained world sample constant while moving the live camera and verifies that screen projection follows the live camera rather than any historical screen coordinate.


## Selected-artifact provenance

`CompletedRunGhostState` retains the selected `StoredRunRecord`, including its immutable artifact path, while preserving the existing record-only accessor. `load_selected_completed_run_ghost_trace()` therefore resolves the sibling `.urghost` from the exact selected Previous/PB artifact and revalidates its checksum binding against that record before exposing trace samples. No filename guessing from course IDs or timing metadata is required.

## Visible Modern 1P renderer attachment

The Modern host now resolves the user's strict Off/Previous/PB target at race entry, loads only the checksum-bound sibling trace for that exact selected artifact, selects the trace sample for the current race-relative frame, projects it through the current live camera, and hands the retained synchronized composition plus semantic ID and authoritative H/V transform bits to the existing Racer-HD selector. Unregistered or composition-mismatched poses fail closed instead of inventing a second pose system.

`completed_run_ghost_raster.*` is a host-owned RGBA compositor. It receives only a renderer-ready ghost frame, an already-resolved Racer-HD registration, and a typed render style; it has no guest-memory, controller, simulation, PPU or OAM write surface. The first treatment is deliberately simple semi-transparency. The style object is the extension point for later opacity/color/style polish without widening gameplay authority.

The ordinary generated Modern host draws this compositor only during Modern active 1P races. Authentic mode is inert. Missing, corrupt, stale, unsupported or projection-incompatible trace data produces no presentation frame and therefore no draw. The fresh-process completed-run replay acceptance enables the ghost renderer, requires an actual `UR_RUN_GHOST DRAWN` event, and still requires replay-authoritative provenance, timing, splits and controller input to match the no-ghost captured run.
