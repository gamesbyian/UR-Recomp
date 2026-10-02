#!/usr/bin/env python3
"""Find frame-boundary activity in the race preparation/update lists.

This consumes snesref's per-frame low-WRAM change trace. It is intentionally
bounded to the presentation seam recovered around $0DCD/$0DCF and the camera
inputs that own it.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

BEFORE_RE = re.compile(r"script f=(\d+) dump prep-emission-before-scroll(?:\s|$)")

WATCH = {
    "count_a": 0x0DCD,
    "count_b": 0x0DCF,
    "camera_x_speed": 0x04F5,
    "camera_edge_x": 0x0505,
    "camera_edge_y": 0x050D,
    "camera_x": 0x0419,
    "camera_y": 0x041D,
}


def u16(state: bytearray, addr: int) -> int:
    return state[addr] | (state[addr + 1] << 8)


def load_frames(path: Path) -> dict[int, list[dict]]:
    frames: dict[int, list[dict]] = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        frames[int(row["f"])].append(row)
    return dict(sorted(frames.items()))


def summarize(trace: Path, log: Path) -> dict:
    m = BEFORE_RE.search(log.read_text(encoding="utf-8"))
    if not m:
        raise SystemExit("could not locate prep-emission-before-scroll frame in log")
    scroll_start = int(m.group(1))

    state = bytearray(0x2000)
    samples = []
    first_nonzero = None
    episodes = []
    active_start = None
    active_last = None

    for frame, changes in load_frames(trace).items():
        for row in changes:
            addr = int(row["adr"], 16)
            if addr < len(state):
                state[addr] = int(row["val"], 16)
        if frame < scroll_start:
            continue
        count_a = u16(state, WATCH["count_a"])
        count_b = u16(state, WATCH["count_b"])
        sample = {
            "frame": frame,
            "relative_frame": frame - scroll_start,
            "count_a": count_a,
            "count_b": count_b,
            "camera_x_speed": state[WATCH["camera_x_speed"]],
            "camera_edge_x": u16(state, WATCH["camera_edge_x"]),
            "camera_edge_y": u16(state, WATCH["camera_edge_y"]),
            "camera_x": u16(state, WATCH["camera_x"]),
            "camera_y": u16(state, WATCH["camera_y"]),
        }
        samples.append(sample)
        active = bool(count_a or count_b)
        if active and first_nonzero is None:
            first_nonzero = sample.copy()
        if active:
            if active_start is None:
                active_start = frame
            active_last = frame
        elif active_start is not None:
            episodes.append({"start_frame": active_start, "end_frame": active_last})
            active_start = active_last = None

    if active_start is not None:
        episodes.append({"start_frame": active_start, "end_frame": active_last})

    return {
        "schema_version": 1,
        "fixture": "preparation-emission-race",
        "observation": "snesref low-WRAM frame-boundary trace",
        "scroll_start_frame": scroll_start,
        "first_nonzero": first_nonzero,
        "episodes": episodes,
        "sample_count": len(samples),
        "samples": samples,
    }


def write_replay(report: dict, source_script: Path, out_script: Path, out_input: Path) -> None:
    hit = report["first_nonzero"]
    if hit is None:
        return
    start = report["scroll_start_frame"]
    event = hit["frame"]
    rel = event - start
    source = source_script.read_text(encoding="utf-8")
    marker = "dump prep-emission-before-scroll\n"
    prefix = source.split(marker, 1)[0] + marker

    # Input-file events are evaluated with the current zero-based g_frame before
    # retro_run. A dump logged at f=N describes N completed frames, so starting
    # the Right event at N drives the next emulated frame exactly as the original
    # uninterrupted hold did.
    out_input.write_text(f"{start}:900:080\n", encoding="utf-8")

    waits = max(0, rel - 1)
    body = prefix
    if waits:
        body += f"wait {waits}\n"
    body += "dump prep-emission-event-minus-1\n"
    body += "wait 1\n"
    body += "dump prep-emission-event\n"
    body += "wait 1\n"
    body += "dump prep-emission-event-plus-1\n"
    body += "quit\n"
    out_script.write_text(body, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("trace", type=Path)
    ap.add_argument("log", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--source-script", type=Path)
    ap.add_argument("--replay-script", type=Path)
    ap.add_argument("--replay-input", type=Path)
    args = ap.parse_args()

    report = summarize(args.trace, args.log)
    hit = report["first_nonzero"]
    print(
        "scroll_start=", report["scroll_start_frame"],
        "samples=", report["sample_count"],
        "first_nonzero=", hit,
        "episodes=", report["episodes"],
    )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.source_script and args.replay_script and args.replay_input:
        write_replay(report, args.source_script, args.replay_script, args.replay_input)
    return 0 if hit is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
