#!/usr/bin/env python3
"""Stunt-recognition input boundary, snesref reference vs native recomp.

Each case boots a fresh process from the recovered real "All Silvers - No
Hunter" SRAM, reaches the Jumpover race through the stock menus (the route
in ``probe_jumpover_fallthrough_native.py``), holds Right, jumps from the
first crest (B held for 40 frames) and holds the R shoulder for N frames in
the air. No WRAM is written. P1 pitch, roll progress (``7E:1201``), air
time, P1 boost meter and the P1 message-queue write index are dumped every
frame on both cores and compared exactly.

The R shoulder rotates P1 by 2 pitch units per frame and the roll-progress
counter steps every eighth frame of rotation. The probe records the hold
length at which landing first earns a reward.
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
SHOULDER_START = 272        # frames after race entry
SHOULDER_MASK = 0x0800      # R
HOLDS = (22, 23, 24, 25)
WINDOW = (262, 352)         # dumped frames after race entry


def stunt_events(race_frame: int, hold: int) -> list[tuple[int, int, int]]:
    jump_at, jump_len = JUMP
    events, run = [(race_frame, jump_at, 0x0080)], None
    for off in range(jump_at, WINDOW[1] + 10):
        mask = 0x0080
        if jump_at <= off < jump_at + jump_len:
            mask |= 0x0001
        if SHOULDER_START <= off < SHOULDER_START + hold:
            mask |= SHOULDER_MASK
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


def summarize(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("no rows")
    peak = max(r["roll_progress"] for r in rows)
    reward = next((i for i in range(1, len(rows)) if rows[i]["boost"] > rows[i - 1]["boost"]), None)
    return {
        "peak_roll_progress": peak,
        "rolls": max(r["rolls"] for r in rows),
        "reward_frame": reward,
        "boost_after_reward": rows[reward]["boost"] if reward is not None else None,
        "rewarded": reward is not None,
        "series": " ".join(f'{r["pitch"]}/{r["roll_progress"]}/{r["air_time"]}/{r["boost"]}/{r["queue_write"]}'
                           for r in rows),
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
    args = ap.parse_args(argv)
    for name in ("snesref", "core", "native", "rom", "sram", "work_dir"):
        setattr(args, name, getattr(args, name).resolve())

    ref_race, shift, cases, ok = 1088, None, [], True
    for hold in HOLDS:
        work = args.work_dir / f"hold-{hold}"
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        script = work / "stunt.script"
        script.write_text(stunt_script(ref_race))
        events = stunt_events(ref_race, hold)
        log = jf.run_reference(work, args, script, events)
        rf = jf.race_entry_frame(log)
        if rf is None:
            raise SystemExit(f"reference did not reach the race:\n{log[-2000:]}")
        if rf != ref_race:
            ref_race = rf
            events = stunt_events(rf, hold)
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
        ok &= divergence is None
        cases.append({"shoulder_hold_frames": hold, "reference": ref_summary, "native": nat_summary,
                      "first_divergence_frame": divergence})
        print(json.dumps({"hold": hold, "peak_progress": ref_summary["peak_roll_progress"],
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
        "shoulder": {"frame_after_race_entry": SHOULDER_START, "mask": f"0x{SHOULDER_MASK:03x}"},
        "window_frames_after_race_entry": list(WINDOW),
        "series_format": "space-separated pitch/roll_progress/air_time/boost/queue_write per frame",
        "cases": cases,
    }
    if args.json_out:
        args.json_out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    rewarded = [c["shoulder_hold_frames"] for c in cases if c["reference"]["rewarded"]]
    if not rewarded or len(rewarded) == len(cases):
        print("matrix needs both rewarded and unrewarded holds", file=sys.stderr)
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
