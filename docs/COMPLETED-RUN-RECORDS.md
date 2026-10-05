# Completed Run Records and Ghost Foundation

Status: completed-run capture/replay, Previous/PB selection, checksum-bound presentation traces, live-camera projection, and the first visible Modern 1P ghost renderer are implemented.

## Ownership

Completed-run records are host-owned artifacts. The authoritative Uniracers simulation remains the only gameplay model. A record contains enough information to re-drive that simulation, not a serialized replacement simulation.

The v1 primary representation contains strong game/ROM/build/course/mode provenance, exact elapsed time in authoritative 60 Hz guest timer ticks, named split/checkpoint times in the same unit, an optional terminal authoritative simulation digest, and run-length encoded P1/P2 12-bit controller words.

native/product/completed_run_record.{hpp,cpp} owns the typed record, strict validation, persistence checksum, compatibility checks and replay lookup.

## Replay interoperability

The controller payload intentionally uses the same start:duration:p1-mask[:p2-mask] semantics as tools/controller_input.py and the pinned native INPUT_FILE replay path. encode_completed_run_input_file() emits that grammar directly. Playback should initialize the requested course through the normal guest/runtime path and feed these controller words back through the existing deterministic input route. The record must never write arbitrary WRAM to force course or racer state.

The optional terminal digest is a validation oracle only. It does not grant host data authority over gameplay.

## Timing

ur_uniracers_run_data_ticks60() converts the established title timer digits to exact 60 Hz ticks: ticks60 = whole_seconds * 60 + tenths * 6 + sub_tick. This avoids host-wall-clock timing and keeps PB/split arithmetic aligned with authoritative guest timing.

## Format evolution and failure policy

Schema v1 is strict and self-identifying. Unknown fields, malformed values, duplicate required fields, overlapping inputs and checksum damage fail closed. A valid but unsupported future schema reports UnsupportedVersion. A valid record whose game/ROM/build/course/mode provenance does not match the playback target reports Incompatible.

The explicit schema version and separate build compatibility id allow future codecs to migrate old records deliberately without pretending an incompatible replay is valid.

## Acceptance now covered

tests/native/completed_run_record_test.cpp and tests/unit/test_completed_run_record_cpp.py prove a representative 1P Dragster-style input stream can be captured as authoritative per-frame controller words, compressed into canonical runs, serialized to a typed/versioned artifact, reloaded across a filesystem boundary, reproduced frame-for-frame, exported verbatim to the existing deterministic INPUT_FILE grammar, and rejected on corruption, future schema mismatch and course incompatibility. The run-data contract also tests exact timer conversion.

## Visible presentation seam

The first visual ghost is now attached downstream of authoritative simulation. A selected Previous/PB record resolves its exact checksum-bound `.urghost` trace, looks up the current race-relative sample, projects retained world state through the current live camera, selects the existing Racer-HD semantic representation, and blends that host-owned asset into the Modern presentation surface. No second simulation, guest-memory write or ghost controller-submission path exists.


## Resolved-input observation seam

The pinned desktop framework now exposes the exact final controller word in `SnesDesktopHostFrameStats::controller_word`. That value is computed once from scripted input, live mapped controllers and debug input immediately before the existing run-ahead/`RtlRunFrame` dispatch, then reported after the completed guest frame. P1 occupies the low 12 bits and P2 the next 12 bits.

This matters because completed-run capture must record what the guest actually received after host-owned menu/input interception, not reconstruct intent from SDL events later.

`CompletedRunCapture` is the host-independent lifecycle owner above that observation. The caller starts it after the authoritative race-entry frame, feeds each subsequent resolved guest word, supplies authoritative split/timer observations, and finalizes a typed `CompletedRunRecord`. Abort/reset clears the attempt completely. A small `select_fastest_compatible_run()` query is the first PB/ghost-selection seam and remains read-only/presentation-side.

Fresh-process acceptance now writes a record in one process, reloads and verifies it in another, reconstructs the canonical deterministic input stream, and rejects a checksum-damaged artifact. Native race re-drive from a production-captured artifact remains the next integration proof once the currently active profile/autosave host changes are reconciled.


## Production local persistence

Ordinary Modern one-player timed Race slots now use the already-proven rider-selection mode latch (0x3C = 1P, 0x3D = ordinary 2P, 0x3E = VS) to decide eligibility. A completed 1P run is appended beneath the app preference root as `runs/<active-profile>/run-<time>-<suffix>.urrun`. The active profile ID is host namespace only; record compatibility still depends on game/ROM/build/course/mode provenance inside the artifact.

The local store loads only compatible, valid records in filename order. That directly supplies a previous-run selector, while the fastest-compatible selector supplies the PB candidate. Corrupt and incompatible files are skipped rather than poisoning the catalog. No record or ghost data can write guest state.

For deterministic native acceptance, `UR_RUN_RECORD_CAPTURE_PATH` overrides the ordinary append-only destination with one exact path and writes a sibling `.input` file that remains race-relative. `SNESRECOMP_INPUT_RELATIVE=1` makes the framework hold that stream inert until the Modern host observes the authoritative race-entry edge and arms the replay origin; relative frame 0 is then consumed by the immediately following simulation frame. Absolute `INPUT_FILE` behavior remains unchanged for existing tooling. This sidecar is acceptance plumbing only; the portable record is race-relative by design.


Current production eligibility is deliberately narrower than the file format: Crawler-style timed Race slots (tour slots 1 and 4) are recorded now; Circuit and Stunt completion remain inert until their distinct best-lap and score semantics are attached to the record/comparison model. This prevents a generic lowest-elapsed-time PB rule from being applied to incompatible event types.


## Replay-equivalence note

`frame_count` remains persisted because it is useful lifecycle metadata for the captured attempt, but it is not an input to replay and is not required to match across fresh-process replay. The retained Dragster acceptance evidence showed identical provenance, `elapsed_ticks60`, all four split IDs/ticks, and all 65 RLE input runs while the host-observed active-race lifecycle window differed by one frame (2290 vs 2289). That one-frame lifecycle observation difference does not alter the guest input stream or authoritative timing, so deterministic replay acceptance treats it as diagnostic metadata rather than simulation equivalence.


## Presentation-only ghost selection

`native/product/completed_run_ghost.{hpp,cpp}` is the first consumer of the persisted catalog. At an eligible Modern 1P race-entry edge, the host loads compatible records from the active profile namespace and binds two immutable selections: the most recent compatible run and the fastest compatible personal best. The state owns copies of those records and exposes race-relative controller lookup only.

The ghost state has no guest-memory pointer, no simulator callback, no WRAM writer, and no authority over controller input submitted to the real racer. The renderer consumes only the immutable selected record/trace projection and host-owned presentation assets; gameplay continues to come exclusively from the authoritative guest simulation. Retry clears and rebinds this presentation state at the next race-entry edge. Deterministic acceptance capture overrides remain isolated from the ordinary profile ghost catalog.

## Authoritative ghost presentation traces

A renderable ghost now has a durable presentation-evidence path that remains separate from replay authority. `native/product/completed_run_ghost_world_sample.*` observes P1 world X/Y, pitch, facing and semantic racer-presentation ID directly from promoted guest state after each captured race-relative frame. Historical OAM coordinates are deliberately not retained as the primary location source because they belong to the historical run's camera; a later renderer must project retained world state through the current live camera.

`native/product/completed_run_ghost_trace.*` owns a strict versioned/checksummed `.urghost` sidecar. Each trace is bound to the exact completed-run artifact checksum, rejects stale/corrupt/malformed evidence independently, and can disappear or fail without invalidating the replay record. The Modern 1P capture lifecycle starts trace collection with the run recorder, aborts it on Retry/attempt retirement, and after successful run finalization writes a sibling `.urrun.urghost` file when the trace validates. Trace persistence never changes deterministic replay equivalence and does not make `frame_count` authoritative.

That bounded rendering step is now implemented for Modern 1P races. Missing or incompatible trace data simply makes the visual ghost unavailable. The first renderer uses the existing Racer-HD registration selector and a typed host-only render style with semi-transparent blending; unsupported semantic/composition states fail closed. Fresh-process replay acceptance requires a real ghost draw while preserving the same replay-authoritative provenance, elapsed time, splits and controller stream as the no-ghost capture, so the presentation path remains downstream of gameplay authority.
