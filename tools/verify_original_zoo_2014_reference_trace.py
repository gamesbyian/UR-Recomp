#!/usr/bin/env python3
"""Reconstruct original Zoom Zoo event observations from archived Snes9x WRAM.

Requires the original GitHub Actions artifact ZIP from run 37184022134,
artifact 11296685866. Fail closed against its SHA256 and record count before
comparing any derived sample to the source-qualified retained fixture.

IMPORTANT: this is a write trace of LOW 7E WRAM only, not an emulator CPU
instruction trace and not a fully resident 7F course-buffer witness.
Original guest postframe state is reconstructed after all writes for f.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WITNESS = ROOT / "analysis/data/zoo-original-2014-live-progression.json"
TRACE_MEMBER = "_temp/dessyreqt-first-race-trace.jsonl"
LOW_WRAM = {
    0x009F, 0x0313, 0x00CE,
    *range(0x0411, 0x0419),   # P1 and P2 position words
    0x0E95, 0x0E96,         # persisted P1 contact
    0x04B7, 0x04B8,         # P1 signed horizontal velocity
    0x11CF, 0x11D0,         # P1 boost meter
    0x0EF1, 0x0EF2,         # P1 laps remaining
    0x1199, 0x119A,         # P1 checkpoint
    0x119D, 0x119E,         # P1 finish gate
    0x0E0F, 0x0E13, 0x0E17, 0x0E1B, 0x0E1F,  # original timer digits
}
PROGRESS_ADDRESSES = {0x0EF1, 0x1199, 0x119D}
EVENT_FRAMES = (3408, 3794, 4031, 4722, 4911)
TARGETS = frozenset({3190, 3394, 3395, 3396, *EVENT_FRAMES,
                     *(f - 1 for f in EVENT_FRAMES)})


class TraceWitnessError(ValueError):
    pass


def u16(state: dict[int, int], addr: int) -> int:
    return state.get(addr, 0) | (state.get(addr + 1, 0) << 8)


def snapshot(frame: int, state: dict[int, int]) -> dict:
    return {
        "movie_frame": frame,
        "menu": state.get(0x009F, 0),
        "in_race": state.get(0x0313, 0),
        "track_id": state.get(0x00CE, 0),
        "p1_world_xy": [u16(state, 0x0411), u16(state, 0x0415)],
        "p2_world_xy": [u16(state, 0x0413), u16(state, 0x0417)],
        "p1_stored_contact_word": u16(state, 0x0E95),
        "p1_speed_x": (u16(state, 0x04B7) + 0x8000) % 0x10000 - 0x8000,
        "p1_boost": u16(state, 0x11CF),
        "progress": [u16(state, 0x1199), u16(state, 0x119D),
                     u16(state, 0x0EF1)],
        "timer_raw_digits": [state.get(a, 0) for a in
                             (0x0E0F, 0x0E13, 0x0E17, 0x0E1B, 0x0E1F)],
    }


def reconstruct(lines, targets: frozenset[int] = TARGETS) -> dict:
    state: dict[int, int] = {}
    snapshots: dict[int, dict] = {}
    writes: dict[int, list[dict]] = {}
    digest = hashlib.sha256()
    frame = None
    count = 0

    def finish_frame(previous: int, next_frame: int) -> None:
        # Capture frames that have no writes as settled WRAM state too.
        for candidate in targets:
            if previous <= candidate < next_frame:
                snapshots[candidate] = snapshot(candidate, state)

    for raw in lines:
        digest.update(raw)
        rec = json.loads(raw)
        current = int(rec["f"])
        if type(current) is not int or current < 1:
            raise TraceWitnessError("invalid frame number")
        if frame is not None and current < frame:
            raise TraceWitnessError("Snes9x WRAM frames are not monotonic")
        if frame is not None and current != frame:
            finish_frame(frame, current)
        frame = current
        count += 1
        address = int(rec["adr"], 16)
        before, after = int(rec["old"], 16), int(rec["val"], 16)
        if address in LOW_WRAM:
            state[address] = after
        if (current in targets and address in PROGRESS_ADDRESSES
                and before != after):
            writes.setdefault(current, []).append({
                "wram_offset_hex": f"{address:04X}",
                "old": before, "new": after,
            })
    if frame is not None:
        finish_frame(frame, frame + 1)
    if not targets.issubset(snapshots):
        missing = sorted(targets - snapshots.keys())
        raise TraceWitnessError(f"required original frame(s) missing: {missing}")
    return {
        "trace_sha256": digest.hexdigest(),
        "raw_record_count": count,
        "last_written_frame": frame,
        "samples": snapshots,
        "direct_progress_writes": writes,
    }


def surface_slot(word: int) -> int | None:
    if word & 0x03FF == 0:
        return None
    return ((word & 0x0F) >> 1) + ((word & 0x03F0) >> 2)


def verify(extracted: dict, witness: dict) -> dict:
    provenance = witness["provenance"]
    if (extracted["trace_sha256"] != provenance["source_sha256"]
            or extracted["raw_record_count"] != provenance["raw_trace_write_records"]
            or extracted["last_written_frame"] != witness["observed_original_up_to_frame"]):
        raise TraceWitnessError("original Snes9x source hash, record count or horizon changed")
    start = extracted["samples"][3190]
    anchored = witness["initial_active_frame"]
    for key in ("movie_frame", "menu", "in_race", "track_id",
                "p1_world_xy", "p2_world_xy", "timer_raw_digits"):
        if start[key] != anchored[key]:
            raise TraceWitnessError(f"original Zoom Zoo initial {key} changed")
    if start["progress"] != [anchored[x] for x in (
            "p1_next_checkpoint", "p1_finish_gate", "p1_laps_remaining")]:
        raise TraceWitnessError("original Zoom Zoo initial progress state changed")
    onset = witness["original_race_start_phase"]
    still = extracted["samples"][onset["last_observed_zero_x_displacement_frame"]]
    first = extracted["samples"][onset["first_p1_x_displacement_frame"]]
    timer_start = extracted["samples"][onset["first_stopwatch_nonzero_frame"]]
    if (still["p1_world_xy"][0] != start["p1_world_xy"][0]
            or still["timer_raw_digits"] != [0, 0, 0, 0, 0]
            or first["p1_world_xy"][0] != onset["first_p1_moving_x"]
            or first["p1_speed_x"] != onset["first_p1_signed_vx"]
            or first["p1_boost"] != onset["first_p1_boost_nonzero"]
            or first["timer_raw_digits"] != onset["stopwatch_at_first_motion"]
            or timer_start["timer_raw_digits"] != onset["stopwatch_at_first_timer_tick"]):
        raise TraceWitnessError("original active-race-to-motion/timer phase witness changed")
    if (first["movie_frame"] - start["movie_frame"]
            != onset["race_active_to_first_motion_guest_frames"]
            or timer_start["movie_frame"] - start["movie_frame"]
            != onset["race_active_to_timer_tick_guest_frames"]):
        raise TraceWitnessError("original scene-entry frame cadence changed")
    audited = []
    if [r["transition_frame"] for r in witness["observed_progression"]] != list(EVENT_FRAMES):
        raise TraceWitnessError("expected original course event frame sequence changed")
    for row in witness["observed_progression"]:
        f = row["transition_frame"]
        before = extracted["samples"][f - 1]
        after = extracted["samples"][f]
        if (before["p1_world_xy"] != row["p1_world_xy_before"]
                or after["p1_world_xy"] != row["p1_world_xy_after"]):
            raise TraceWitnessError(f"original movement around event {f} changed")
        progress_before = [row["progress_before"][x] for x in (
            "checkpoint", "finish_gate", "laps_remaining")]
        progress_after = [row["progress_after"][x] for x in (
            "checkpoint", "finish_gate", "laps_remaining")]
        if before["progress"] != progress_before or after["progress"] != progress_after:
            raise TraceWitnessError(f"original checkpoint/gate/lap values at {f} changed")
        if (before["p1_stored_contact_word"] != int(row["p1_stored_contact_before_hex"], 16)
                or after["p1_stored_contact_word"] != int(row["p1_stored_contact_after_hex"], 16)):
            raise TraceWitnessError(f"original stored P1 contact at {f} changed")
        if (surface_slot(before["p1_stored_contact_word"])
                != row["prior_contact_c000_slot_candidate"]
                or surface_slot(after["p1_stored_contact_word"])
                != row["new_postframe_contact_slot"]):
            raise TraceWitnessError(f"decoded C000 slot at {f} changed")
        if after["timer_raw_digits"] != row["original_timer_raw_digits"]:
            raise TraceWitnessError(f"original timer at {f} changed")
        if extracted["direct_progress_writes"].get(f, []) != row["observed_original_progress_writes"]:
            raise TraceWitnessError(f"original direct WRAM progress write order at {f} changed")
        audited.append(f)
    return {
        "qualified_original_write_trace": True,
        "source_sha256": extracted["trace_sha256"],
        "source_record_count": extracted["raw_record_count"],
        "course_id": witness["course"]["id"],
        "original_event_frames_reproduced": audited,
        "original_first_motion_frame": first["movie_frame"],
        "original_first_stopwatch_tick_frame": timer_start["movie_frame"],
        "lap_counter_decrements": [
            f for f in audited
            if extracted["samples"][f]["progress"][2]
            < extracted["samples"][f - 1]["progress"][2]
        ],
        "qualification_limit": (
            "Independent original Snes9x 7E-WRAM write trace only. "
            "No instruction-PC consumed contact, active 7F course buffer, "
            "native replay, full course result or 45-course pass demonstrated."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifact-zip", required=True, type=Path,
                    help="historical workflow 37184022134 artifact ZIP")
    ap.add_argument("--witness", type=Path, default=WITNESS)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    with zipfile.ZipFile(args.artifact_zip) as archive:
        if TRACE_MEMBER not in archive.namelist():
            raise TraceWitnessError(f"missing original {TRACE_MEMBER}")
        with archive.open(TRACE_MEMBER) as source:
            reconstructed = reconstruct(source)
    witness = json.loads(args.witness.read_text(encoding="utf-8"))
    result = verify(reconstructed, witness)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
