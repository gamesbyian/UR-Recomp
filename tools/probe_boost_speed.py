#!/usr/bin/env python3
"""Game-facing boost -> speed semantics, snesref reference vs native recomp.

Each case boots a fresh process from the recovered real "All Silvers - No
Hunter" SRAM, reaches the Jumpover race through the stock menus (the same
route as ``probe_jumpover_fallthrough_native.py``), holds Right, and once P1
is at full ground speed on the flat start straight seeds P1's persistent boost
meter (``7E:11CF``) with one frame-boundary write. P1 X speed, boost, Y and
air time are dumped every frame afterwards on both cores and compared
exactly. The seed only sets the stored value the game's own stunt rewards
write; how the game turns it into speed and how it depletes are observed.
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

SEED_OFFSET = 222       # race entry + 222: grounded, full speed, flat straight
FRAMES = 40             # dumped frames after the seed
SEEDS = (0, 16, 32, 64, 96, 128, 256, 0x180, 0x200, 0x400)
# Airborne scenario: seed just before the halfpipe jump (B held at race
# entry + 372 for 20 frames clears the halfpipe), then compare in-air
# depletion and speed with the ground law.
AIR_SEED_OFFSET = 364
AIR_JUMP = (372, 20)
AIR_SEEDS = (64, 128, 256)
# Offscreen scenario: a full meter seeded on the straight and a 40-frame
# jump from the first crest carries P1 above its viewport (7E:121B set)
# while still moving right.
OFFSCREEN_SEED = (242, 0x400)          # (frames after race entry, value)
OFFSCREEN_JUMP = (264, 40)
OFFSCREEN_FRAMES = 90
BASE_SPEED = 448        # hold-Right ground speed with an empty meter
SPEED_CAP = 640


def boost_script(race_frame: int, value: int, seed_offset: int = SEED_OFFSET,
                 frames: int = FRAMES) -> str:
    seed = race_frame + seed_offset
    lines = [jf.MENU_SCRIPT.rstrip("\n"), f"wait {seed - race_frame}",
             f"poke 11CF {value & 0xFF:02x}{value >> 8:02x}", "dump s000"]
    for i in range(1, frames + 1):
        lines += ["wait 1", f"dump s{i:03d}"]
    lines.append("quit")
    return "\n".join(lines) + "\n"


def read_row(wram: bytes) -> dict:
    return {
        "x_speed": struct.unpack_from("<h", wram, 0x04B7)[0],
        "boost": struct.unpack_from("<H", wram, 0x11CF)[0],
        "y": struct.unpack_from("<H", wram, 0x0415)[0],
        "air_time": wram[0x0545],
        "offscreen": wram[0x121B],
    }


def load_rows(directory: Path, frames: int = FRAMES) -> list[dict]:
    """Every frame must be a full WRAM image of an active Jumpover race."""
    rows = []
    for i in range(frames + 1):
        path = directory / f"s{i:03d}.wram.bin"
        if not path.exists():
            raise jf.EvidenceError(f"missing dump {path}")
        wram = path.read_bytes()
        if len(wram) != jf.WRAM_SIZE:
            raise jf.EvidenceError(f"{path}: {len(wram)} bytes, expected a {jf.WRAM_SIZE}-byte WRAM image")
        if wram[0x00CE] != jf.JUMPOVER_TRACK_ID or wram[0x0313] != 0x01:
            raise jf.EvidenceError(f"{path}: not an active Jumpover race")
        rows.append(read_row(wram))
    return rows


FLAT_FRAMES = 22        # frames after the seed still on the flat straight


def law_speed(boost: int) -> int:
    return min(BASE_SPEED + boost // 2, SPEED_CAP)


def summarize(rows: list[dict]) -> dict:
    """Observables on the flat window: the boost/2 law, ramp, cap and depletion."""
    if len(rows) <= FLAT_FRAMES:
        raise ValueError("series shorter than the flat window")
    flat = rows[:FLAT_FRAMES + 1]
    # Speed follows the previous frame's meter once it has ramped to it.
    deviations = [flat[i]["x_speed"] - law_speed(flat[i - 1]["boost"]) for i in range(1, len(flat))]
    start = next((i for i, d in enumerate(deviations) if d >= -2), len(deviations))
    converged = deviations[start:]
    ramp = [flat[i]["x_speed"] - flat[i - 1]["x_speed"] for i in range(1, len(flat))
            if flat[i]["x_speed"] > flat[i - 1]["x_speed"]]
    return {
        "series": " ".join(f'{r["x_speed"]}/{r["boost"]}/{r["air_time"]}' for r in rows),
        "max_flat_x_speed": max(r["x_speed"] for r in flat),
        "ramp_frames": start,
        "max_law_deviation_after_ramp": max((abs(d) for d in converged), default=None),
        "max_ramp_step": max(ramp, default=0),
        "boost_spent_on_flat": flat[0]["boost"] - flat[-1]["boost"],
        "airborne_frames": sum(1 for r in rows if r["air_time"]),
        "series_sha256": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
    }


def summarize_offscreen(rows: list[dict]) -> dict:
    """Per-frame X-speed change on offscreen airborne frames that are neither
    fresh off a bounce nor already limited by the boost law; plus the per-frame
    meter drain values seen in the run."""
    off_deltas = sorted({rows[i]["x_speed"] - rows[i - 1]["x_speed"] for i in range(1, len(rows))
                         if rows[i]["offscreen"] and rows[i - 1]["offscreen"]
                         and rows[i]["air_time"] >= 3 and rows[i - 1]["air_time"] >= 3
                         and rows[i - 1]["x_speed"] < law_speed(rows[i - 1]["boost"]) - 4})
    drains = sorted({rows[i - 1]["boost"] - rows[i]["boost"] for i in range(1, len(rows))})
    return {
        "series": " ".join(f'{r["x_speed"]}/{r["boost"]}/{r["air_time"]}/{r["offscreen"]}' for r in rows),
        "offscreen_frames": sum(1 for r in rows if r["offscreen"]),
        "offscreen_airborne_x_speed_deltas": off_deltas,
        "meter_drain_values_per_frame": drains,
        "series_sha256": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
    }


def summarize_air(rows: list[dict]) -> dict:
    """Depletion and the speed law over the longest airborne run."""
    runs, start = [], None
    for i, r in enumerate(rows + [{"air_time": 0}]):
        if r["air_time"] and start is None:
            start = i
        elif not r["air_time"] and start is not None:
            runs.append((start, i - 1))
            start = None
    if not runs:
        raise ValueError("no airborne frames")
    a, b = max(runs, key=lambda r: r[1] - r[0])
    deviations = [abs(rows[i]["x_speed"] - law_speed(rows[i - 1]["boost"])) for i in range(max(a, 1), b + 1)]
    return {
        "series": " ".join(f'{r["x_speed"]}/{r["boost"]}/{r["air_time"]}' for r in rows),
        "airborne_run": [a, b],
        "boost_spent_airborne": rows[a]["boost"] - rows[b]["boost"],
        "max_law_deviation_airborne": max(deviations, default=None),
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
    for value in SEEDS:
        work = args.work_dir / f"seed-{value}"
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        script = work / "boost.script"
        script.write_text(boost_script(ref_race, value))
        events = [(ref_race, SEED_OFFSET + FRAMES + 8, 0x0080)]
        log = jf.run_reference(work, args, script, events)
        rf = jf.race_entry_frame(log)
        if rf is None:
            raise SystemExit(f"reference did not reach the race:\n{log[-2000:]}")
        if rf != ref_race:
            ref_race = rf
            script.write_text(boost_script(rf, value))
            events = [(rf, SEED_OFFSET + FRAMES + 8, 0x0080)]
            jf.run_reference(work, args, script, events)
        nat_log = jf.run_native(work, args, script, events, shift or 0)
        nf = jf.race_entry_frame(nat_log)
        if nf is None:
            raise SystemExit(f"native did not reach the race:\n{nat_log[-2000:]}")
        if nf - ref_race != (shift or 0):
            shift = nf - ref_race
            nat_log = jf.run_native(work, args, script, events, shift)
        ref_rows, nat_rows = load_rows(work / "ref"), load_rows(work / "native")
        divergence = next((i for i, (a, b) in enumerate(zip(ref_rows, nat_rows)) if a != b), None)
        ref_summary, nat_summary = summarize(ref_rows), summarize(nat_rows)
        nat_summary.pop("series")  # identical when first_divergence_frame is null
        case = {"seed": value, "reference": ref_summary, "native": nat_summary,
                "first_divergence_frame": divergence}
        ok &= divergence is None
        cases.append(case)
        r = case["reference"]
        print(json.dumps({"seed": value, "max_flat_speed": r["max_flat_x_speed"],
                          "law_dev": r["max_law_deviation_after_ramp"], "ramp": r["max_ramp_step"],
                          "spent": r["boost_spent_on_flat"], "divergence": divergence}), flush=True)

    air_cases = []
    for value in AIR_SEEDS:
        work = args.work_dir / f"air-seed-{value}"
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        script = work / "boost.script"
        script.write_text(boost_script(ref_race, value, AIR_SEED_OFFSET))
        jump_at, jump_len = AIR_JUMP
        events = [(ref_race, jump_at, 0x0080), (ref_race + jump_at, jump_len, 0x0081),
                  (ref_race + jump_at + jump_len, FRAMES + 40, 0x0080)]
        jf.run_reference(work, args, script, events)
        jf.run_native(work, args, script, events, shift or 0)
        ref_rows, nat_rows = load_rows(work / "ref"), load_rows(work / "native")
        divergence = next((i for i, (a, b) in enumerate(zip(ref_rows, nat_rows)) if a != b), None)
        ref_summary, nat_summary = summarize_air(ref_rows), summarize_air(nat_rows)
        nat_summary.pop("series")
        ok &= divergence is None
        air_cases.append({"seed": value, "reference": ref_summary, "native": nat_summary,
                          "first_divergence_frame": divergence})
        print(json.dumps({"air_seed": value, "run": ref_summary["airborne_run"],
                          "spent_airborne": ref_summary["boost_spent_airborne"],
                          "law_dev": ref_summary["max_law_deviation_airborne"],
                          "divergence": divergence}), flush=True)

    work = args.work_dir / "offscreen"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    script = work / "boost.script"
    seed_at, seed_value = OFFSCREEN_SEED
    script.write_text(boost_script(ref_race, seed_value, seed_at, OFFSCREEN_FRAMES))
    jump_at, jump_len = OFFSCREEN_JUMP
    events = [(ref_race, jump_at, 0x0080), (ref_race + jump_at, jump_len, 0x0081),
              (ref_race + jump_at + jump_len, OFFSCREEN_FRAMES + 40, 0x0080)]
    jf.run_reference(work, args, script, events)
    jf.run_native(work, args, script, events, shift or 0)
    ref_rows = load_rows(work / "ref", OFFSCREEN_FRAMES)
    nat_rows = load_rows(work / "native", OFFSCREEN_FRAMES)
    off_div = next((i for i, (a, b) in enumerate(zip(ref_rows, nat_rows)) if a != b), None)
    off_ref, off_nat = summarize_offscreen(ref_rows), summarize_offscreen(nat_rows)
    off_nat.pop("series")
    ok &= off_div is None
    offscreen_case = {"seed_frame_after_race_entry": seed_at, "seed": seed_value,
                      "jump": {"frame_after_race_entry": jump_at, "frames": jump_len, "mask": "0x081"},
                      "frames": OFFSCREEN_FRAMES, "reference": off_ref, "native": off_nat,
                      "first_divergence_frame": off_div}
    print(json.dumps({"offscreen_frames": off_ref["offscreen_frames"],
                      "offscreen_deltas": off_ref["offscreen_airborne_x_speed_deltas"],
                      "drains": off_ref["meter_drain_values_per_frame"],
                      "divergence": off_div}), flush=True)

    evidence = {
        "schema_version": 3,
        "kind": "boost-speed-probe",
        "qualification": ("controlled-state measurement: each case writes P1's boost meter "
                          "(7E:11CF) once at a frame boundary and observes what the game does with it"),
        "course": {"id": "course:20", "name": "Jumpover", "track_id": jf.JUMPOVER_TRACK_ID},
        "sram_sha256": hashlib.sha256(args.sram.read_bytes()).hexdigest(),
        "reference_race_entry_frame": ref_race,
        "native_race_entry_offset_frames": shift,
        "seed_frame_after_race_entry": SEED_OFFSET,
        "frames": FRAMES,
        "flat_frames": FLAT_FRAMES,
        "series_format": "space-separated x_speed/boost/air_time per frame, frame 0 = seed frame",
        "base_speed": BASE_SPEED,
        "speed_cap": SPEED_CAP,
        "cases": cases,
        "air_seed_frame_after_race_entry": AIR_SEED_OFFSET,
        "air_jump": {"frame_after_race_entry": AIR_JUMP[0], "frames": AIR_JUMP[1], "mask": "0x081"},
        "air_cases": air_cases,
        "offscreen_case": offscreen_case,
    }
    if args.json_out:
        args.json_out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
