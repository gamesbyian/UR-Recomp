# Ghost Presentation Trace Seam

Status: authoritative world-state sampling, live Modern 1P capture, strict checksummed trace persistence and exact ordinary-1P live-camera projection are implemented; renderer attachment remains the follow-on.

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

Filesystem round-trip persistence is covered by focused native acceptance. `CompletedRunGhostTraceCapture` supplies the host-independent lifecycle seam: it begins with a race attempt, accepts strictly increasing race-relative samples, aborts cleanly, and finalizes only against a validated completed-run record whose frame window contains every sample. The Modern host now calls that lifecycle from the authoritative 1P capture boundary and writes the sibling trace only after the corresponding completed-run artifact finalizes successfully. Trace-save failure remains presentation-only and never invalidates the run artifact.

`completed_run_ghost_projection.*` now implements the ordinary-1P coordinate/culling portion of `Race_BuildRacerOAMState` exactly from the retained historical world sample plus the current live camera/viewport context (`0419/041D`, `03ED`, `0421/0423`, `0D49`). It emulates the original 65816 sign-flag comparisons rather than substituting approximate signed arithmetic, and fails closed for the alternate `$0DDB` projection path. The remaining rendering step can therefore consume an exact live-camera screen projection and select art from the existing semantic racer-presentation path.


## Selected-artifact provenance

`CompletedRunGhostState` retains the selected `StoredRunRecord`, including its immutable artifact path, while preserving the existing record-only accessor. `load_selected_completed_run_ghost_trace()` therefore resolves the sibling `.urghost` from the exact selected Previous/PB artifact and revalidates its checksum binding against that record before exposing trace samples. No filename guessing from course IDs or timing metadata is required.

The remaining renderer boundary is narrow: resolve the user's strict Off/Previous/PB target, load the corresponding bound trace, select its sample for the current race-relative presentation frame, project that sample through `completed_run_ghost_projection.*`, and hand the retained synchronized composition plus semantic ID and authoritative H/V transform bits to the established racer selector/presentation layer. `completed_run_ghost_frame.*` now packages exactly that renderer-ready presentation frame and fails closed when either the historical sample is missing or the live viewport culls it.
