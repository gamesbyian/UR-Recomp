# Completed Run Records and Ghost Foundation

Status: foundation implemented; production race-completion capture and ghost rendering remain follow-ons.

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

## Next production seam

The next step is deliberately narrow: observe the already-resolved guest controller words at the desktop host input boundary, start/retire the recorder at the same title-owned race lifecycle edge used by Restart Race, and finalize/persist only after an authoritative completed-run surface supplies valid time/course metadata. That wiring should not add a second input parser or write guest state.

After live capture/replay is proven, PB and previous-run selection can simply choose compatible records. A ghost renderer should consume a deterministic replay/state stream derived from those records and remain presentation-only.


## Resolved-input observation seam

The pinned desktop framework now exposes the exact final controller word in `SnesDesktopHostFrameStats::controller_word`. That value is computed once from scripted input, live mapped controllers and debug input immediately before the existing run-ahead/`RtlRunFrame` dispatch, then reported after the completed guest frame. P1 occupies the low 12 bits and P2 the next 12 bits.

This matters because completed-run capture must record what the guest actually received after host-owned menu/input interception, not reconstruct intent from SDL events later.

`CompletedRunCapture` is the host-independent lifecycle owner above that observation. The caller starts it after the authoritative race-entry frame, feeds each subsequent resolved guest word, supplies authoritative split/timer observations, and finalizes a typed `CompletedRunRecord`. Abort/reset clears the attempt completely. A small `select_fastest_compatible_run()` query is the first PB/ghost-selection seam and remains read-only/presentation-side.

Fresh-process acceptance now writes a record in one process, reloads and verifies it in another, reconstructs the canonical deterministic input stream, and rejects a checksum-damaged artifact. Native race re-drive from a production-captured artifact remains the next integration proof once the currently active profile/autosave host changes are reconciled.
