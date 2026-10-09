#!/usr/bin/env python3
"""Stunt-recognition input boundary, snesref reference vs native recomp.

Each case boots a fresh process from the recovered real "All Silvers - No
Hunter" SRAM, reaches the Jumpover race through the stock menus (the route
in ``probe_jumpover_fallthrough_native.py``), holds Right, jumps from the
first crest (B held for 40 frames) and holds the R shoulder for N frames in
the air: the R shoulder (rotation) or A (Z twist) for N frames. No WRAM is
written. P1 pitch, roll progress (``7E:1201``), Z rotation (``7E:0DFD``),
air time, P1 boost meter and the P1 message-queue write index are dumped
every frame on both cores and compared exactly. Each family's holds
straddle the hold length at which landing first earns a reward.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import probe_jumpover_fallthrough_native as jf  # noqa: E402

JUMP = (264, 40)            # frames after race entry, B-hold length
SHOULDER_START = 272        # frames after race entry: the stunt input starts here
# (name, mask, holds): each family's holds straddle its reward boundary.
FAMILIES = (
    ("r-shoulder-rotation", 0x0800, (22, 23, 24, 25)),
    ("a-twist", 0x0100, (4, 5)),
)
# Hypothesis-generating cases only. Durations are chosen to bracket known
# input rhythms, not claimed threshold values. Keep separate from the six
# established admissible R/A boundary examples.
EXPLORATORY_FAMILIES = (
    ("l-shoulder-flip", 0x0400, (20, 22, 23, 24, 25, 28, 32)),
    ("a-r-simultaneous", 0x0900, (4, 5, 22, 24, 25)),
)


def planned_cases(explore: bool = False) -> list[tuple[str, int, int]]:
    families = FAMILIES + (EXPLORATORY_FAMILIES if explore else ())
    return [(family, mask, hold) for family, mask, holds in families
            for hold in holds]

WINDOW = (262, 352)         # dumped frames after race entry


def stunt_events(race_frame: int, hold: int, stunt_mask: int = 0x0800) -> list[tuple[int, int, int]]:
    jump_at, jump_len = JUMP
    events, run = [(race_frame, jump_at, 0x0080)], None
    for off in range(jump_at, WINDOW[1] + 10):
        mask = 0x0080
        if jump_at <= off < jump_at + jump_len:
            mask |= 0x0001
        if SHOULDER_START <= off < SHOULDER_START + hold:
            mask |= stunt_mask
        if run and run[2] == mask:
            run[1] += 1
        else:
            if run:
                events.append(tuple(run))
            run = [race_frame + off, 1, mask]
    events.append(tuple(run))
    return events


def stunt_script(race_frame: int) -> str:
    lines = [jf.MENU_SCRIPT.rstrip("\n"), f"wait {WINDOW[0]}", f"dump w{0:03d}"]
    for i in range(1, WINDOW[1] - WINDOW[0] + 1):
        lines += ["wait 1", f"dump w{i:03d}"]
    lines.append("quit")
    return "\n".join(lines) + "\n"


def read_row(wram: bytes) -> dict:
    u = lambda a: struct.unpack_from("<H", wram, a)[0]
    return {"pitch": u(0x04C7) & 0x3F, "roll_progress": u(0x1201), "rolls": u(0x11F9),
            "z_rotation": u(0x0DFD),
            "air_time": wram[0x0545], "boost": u(0x11CF), "queue_write": u(0x0CE3)}


def load_rows(directory: Path) -> list[dict]:
    rows = []
    for i in range(WINDOW[1] - WINDOW[0] + 1):
        path = directory / f"w{i:03d}.wram.bin"
        if not path.exists():
            raise jf.EvidenceError(f"missing dump {path}")
        wram = path.read_bytes()
        if len(wram) != jf.WRAM_SIZE:
            raise jf.EvidenceError(f"{path}: {len(wram)} bytes, expected a {jf.WRAM_SIZE}-byte WRAM image")
        if wram[0x00CE] != jf.JUMPOVER_TRACK_ID or wram[0x0313] != 0x01:
            raise jf.EvidenceError(f"{path}: not an active Jumpover race")
        rows.append(read_row(wram))
    return rows


def load_trajectory_rows(directory: Path) -> list[dict]:
    """Independent motion/contact channel over the SAME input-only stunt window.

    The historic six-case acceptance serializes only pose/progress/boost and
    queue cursor. Equal rewards can conceal incorrect velocity, geometry or
    persisted collision words; keep their original hashes unchanged while
    exposing these fields in an optional diagnostic.
    """
    frames = []
    for i in range(WINDOW[1] - WINDOW[0] + 1):
        path = directory / f"w{i:03d}.wram.bin"
        if not path.is_file():
            raise jf.EvidenceError(f"missing trajectory guest frame {i}: {path}")
        image = path.read_bytes()
        if len(image) != jf.WRAM_SIZE:
            raise jf.EvidenceError(f"short trajectory guest frame {i}")
        if image[0x00CE] != jf.JUMPOVER_TRACK_ID or image[0x0313] != 1:
            raise jf.EvidenceError(f"trajectory frame {i} left Jumpover race")
        frames.append({"frame_after_race_entry": WINDOW[0] + i,
                       **jf.read_p1(image)})
    return frames


def trajectory_diagnostics(reference: list[dict], native: list[dict]) -> dict:
    """Report motion divergence and airborne-to-zero changes independently.

    AIR=0 is a sampled state transition, not instruction-time proof of a
    particular collision cell, landing reward, or stunt message consumer.
    """
    count = WINDOW[1] - WINDOW[0] + 1
    if len(reference) != count or len(native) != count:
        raise jf.EvidenceError("incomplete trajectory window")
    required = set(jf.FIELDS) | {"frame_after_race_entry"}
    for index, (ref, nat) in enumerate(zip(reference, native)):
        if set(ref) != required or set(nat) != required:
            raise jf.EvidenceError("trajectory semantic field sets differ")
        if ref["frame_after_race_entry"] != WINDOW[0] + index or (
                nat["frame_after_race_entry"] != WINDOW[0] + index):
            raise jf.EvidenceError("trajectory guest-relative frame mismatch")
    first = next((
        {"frame_after_race_entry": ref["frame_after_race_entry"],
         "fields": sorted(k for k in jf.FIELDS if ref[k] != nat[k]),
         "reference": {k: ref[k] for k in jf.FIELDS if ref[k] != nat[k]},
         "native": {k: nat[k] for k in jf.FIELDS if ref[k] != nat[k]}}
        for ref, nat in zip(reference, native) if ref != nat
    ), None)

    def air_to_zero(rows: list[dict]) -> list[dict]:
        return [
            {"frame_after_race_entry": curr["frame_after_race_entry"],
             "prior_air_time": prev["air_time"],
             "contact_word": curr["contact_word"],
             "y": curr["y"], "y_speed": curr["y_speed"]}
            for prev, curr in zip(rows, rows[1:])
            if prev["air_time"] > 0 and curr["air_time"] == 0
        ]

    ref_landing = air_to_zero(reference)
    nat_landing = air_to_zero(native)
    return {
        "scope": "same input-only Jumpover circuit B window; guest postframe motion and contact",
        "observed_guest_frames": count,
        "first_trajectory_disagreement": first,
        "reference_airborne_to_zero_transitions": ref_landing,
        "native_airborne_to_zero_transitions": nat_landing,
        "motion_reference_native_equal": first is None,
        "interpretation_limit": (
            "Equal pose and boost never prove equal course-boundary physics. "
            "An airborne-to-zero state change is a landing candidate, not "
            "instruction-time collision or stunt-message reward causality."
        ),
    }


def summarize(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("no rows")
    peak = max(r["roll_progress"] for r in rows)
    reward = next((i for i in range(1, len(rows)) if rows[i]["boost"] > rows[i - 1]["boost"]), None)
    return {
        "peak_roll_progress": peak,
        "peak_z_rotation": max(r["z_rotation"] for r in rows),
        "rolls": max(r["rolls"] for r in rows),
        "reward_frame": reward,
        "boost_after_reward": rows[reward]["boost"] if reward is not None else None,
        "rewarded": reward is not None,
        "series": " ".join(f'{r["pitch"]}/{r["roll_progress"]}/{r["z_rotation"]}/{r["air_time"]}/'
                           f'{r["boost"]}/{r["queue_write"]}' for r in rows),
        "series_sha256": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snesref", type=Path, required=True)
    ap.add_argument("--core", type=Path, required=True)
    ap.add_argument("--native", type=Path, required=True)
    ap.add_argument("--rom", type=Path, required=True)
    ap.add_argument("--sram", type=Path, default=jf.DEFAULT_SRAM)
    ap.add_argument("--work-dir", type=Path, required=True)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--explore", action="store_true",
                    help="also compare non-admitted L-flip and simultaneous-A/R input hypotheses")
    ap.add_argument("--queue-evidence", action="store_true",
                    help="record per-frame P1 ring-buffer enqueues and delayed boost events")
    ap.add_argument("--trajectory-evidence", action="store_true",
                    help="compare P1 world XY, signed speed and stored contact across stunt windows")
    args = ap.parse_args(argv)
    for name in ("snesref", "core", "native", "rom", "sram", "work_dir"):
        setattr(args, name, getattr(args, name).resolve())

    ref_race, shift, cases, ok = 1088, None, [], True
    cases_to_run = planned_cases(args.explore)
    for family, stunt_mask, hold in cases_to_run:
        work = args.work_dir / f"{family}-{hold}"
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        script = work / "stunt.script"
        script.write_text(stunt_script(ref_race))
        events = stunt_events(ref_race, hold, stunt_mask)
        log = jf.run_reference(work, args, script, events)
        rf = jf.race_entry_frame(log)
        if rf is None:
            raise SystemExit(f"reference did not reach the race:\n{log[-2000:]}")
        if rf != ref_race:
            ref_race = rf
            events = stunt_events(rf, hold, stunt_mask)
            jf.run_reference(work, args, script, events)
        nat_log = jf.run_native(work, args, script, events, shift or 0)
        nf = jf.race_entry_frame(nat_log)
        if nf is None:
            raise SystemExit(f"native did not reach the race:\n{nat_log[-2000:]}")
        if nf - ref_race != (shift or 0):
            shift = nf - ref_race
            jf.run_native(work, args, script, events, shift)
        ref_rows, nat_rows = load_rows(work / "ref"), load_rows(work / "native")
        divergence = next((i for i, (a, b) in enumerate(zip(ref_rows, nat_rows)) if a != b), None)
        ref_summary, nat_summary = summarize(ref_rows), summarize(nat_rows)
        nat_summary.pop("series")
        queue_report = None
        if args.queue_evidence:
            # Reading the actual ring contents avoids inferring a named
            # message from the numeric boost alone. We still cannot assign
            # a consumer-pop event to a particular enqueue without a PC trace.
            from extract_stunt_queue_events import read_series, analyze, compare
            first, last = 0, WINDOW[1] - WINDOW[0]
            q_ref = read_series(work / "ref", first, last, track=jf.JUMPOVER_TRACK_ID)
            q_nat = read_series(work / "native", first, last, track=jf.JUMPOVER_TRACK_ID)
            queue_check = compare(q_ref, q_nat)
            queue_report = {
                "cross_engine": queue_check,
                "reference": analyze(q_ref),
                "native": analyze(q_nat),
            }
        trajectory_report = None
        if args.trajectory_evidence:
            original_motion = load_trajectory_rows(work / "ref")
            native_motion = load_trajectory_rows(work / "native")
            trajectory_report = trajectory_diagnostics(original_motion, native_motion)
        ok &= divergence is None and (
            queue_report is None or queue_report["cross_engine"]["native_reference_equal"]
        ) and (
            trajectory_report is None or trajectory_report["motion_reference_native_equal"]
        )
        entry = {"family": family, "mask": f"0x{stunt_mask:03x}", "hold_frames": hold,
                 "reference": ref_summary, "native": nat_summary,
                 "first_divergence_frame": divergence,
                 "admission_class": "exploratory" if family in {
                     item[0] for item in EXPLORATORY_FAMILIES
                 } else "retained_boundary"}
        if queue_report is not None:
            entry["message_queue"] = queue_report
        if trajectory_report is not None:
            entry["trajectory"] = trajectory_report
        cases.append(entry)
        print(json.dumps({"family": family, "hold": hold, "peak_progress": ref_summary["peak_roll_progress"],
                          "peak_z": ref_summary["peak_z_rotation"],
                          "rewarded": ref_summary["rewarded"], "boost": ref_summary["boost_after_reward"],
                          "divergence": divergence}), flush=True)

    evidence = {
        "schema_version": 1,
        "kind": "stunt-boundary-probe",
        "qualification": "input-only: fresh boot with the recovered SRAM, no WRAM writes",
        "course": {"id": "course:20", "name": "Jumpover", "track_id": jf.JUMPOVER_TRACK_ID},
        "sram_sha256": hashlib.sha256(args.sram.read_bytes()).hexdigest(),
        "reference_race_entry_frame": ref_race,
        "native_race_entry_offset_frames": shift,
        "jump": {"frame_after_race_entry": JUMP[0], "frames": JUMP[1], "mask": "0x081"},
        "stunt_input_frame_after_race_entry": SHOULDER_START,
        "window_frames_after_race_entry": list(WINDOW),
        "series_format": "space-separated pitch/roll_progress/z_rotation/air_time/boost/queue_write per frame",
        "cases": cases,
        "exploratory_cases_included": args.explore,
        "ring_buffer_observations_included": args.queue_evidence,
        "trajectory_observations_included": args.trajectory_evidence,
    }
    if args.json_out:
        args.json_out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    for family, _, _ in FAMILIES:
        flags = [c["reference"]["rewarded"] for c in cases if c["family"] == family]
        if all(flags) or not any(flags):
            print(f"{family}: matrix needs both rewarded and unrewarded holds", file=sys.stderr)
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
