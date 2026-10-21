#!/usr/bin/env python3
"""Verify bounded ORIGINAL-paced native Modern-root compositor motion receipts.

Consumes actual UR_MODERN_MENU_MOTION_CAPTURE lines from the native host with
UR_MODERN_MENU_TEST_TICK60=N and UR_MODERN_MENU_TEST_ADVANCE_PER_PRESENT=1.

This checks host P6/root *draw* evidence only. It cannot certify an SDL P7
swap, original source art, keyboard/controller input provenance, production
wall-clock pacing, or human approval. No ROM or saved user data is required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "analysis/generated/menu-visual-language.json"
PREFIX = "UR_MODERN_MENU_MOTION_CAPTURE "
FIELDS = (
    "ordinal", "tick60", "selection", "spin", "offset", "entrance",
    "reduced", "root_x", "root_w", "surface_w", "surface_h", "painted"
)
MAX_EVENTS = 100_000


def parse_log(log_text: str) -> list[dict[str, int]]:
    """Ignore unrelated host logs, reject every malformed motion witness."""
    events = []
    for line in log_text.splitlines():
        pos = line.find(PREFIX)
        if pos < 0:
            continue
        data = line[pos + len(PREFIX):].strip().split()
        if len(data) != len(FIELDS):
            raise ValueError("malformed native motion record field count")
        item = {}
        for token in data:
            if token.count("=") != 1:
                raise ValueError("malformed native motion record token")
            key, value = token.split("=", 1)
            if key not in FIELDS or key in item or not re.fullmatch(r"[0-9]+", value):
                raise ValueError("unexpected, duplicate or nondecimal motion field")
            number = int(value)
            if number > (1 << 64) - 1:
                raise ValueError("native motion field integer overflow")
            item[key] = number
        if set(item) != set(FIELDS):
            raise ValueError("missing native motion provenance fields")
        events.append(item)
        if len(events) > MAX_EVENTS:
            raise ValueError("unbounded native motion log")
    if not events:
        raise ValueError("no actual native root motion witness lines")
    return events


def verify_events(events: list[dict[str, int]], original: dict,
                  min_frames: int = 40) -> list[dict]:
    """Source timing independent of C++ constants and final SDL readback."""
    if not 1 <= min_frames <= MAX_EVENTS:
        raise ValueError("invalid minimum source native draw count")
    cursor = original["cursor"]
    slide = original["transition_main_to_options"]
    if (cursor["spin_period_frames"] != 32 or
        cursor["spin_frames_per_tile"] != [2] or
        slide["distance_px"] != 256 or slide["enter_frames"] != 39 or
        len(slide["enter_velocity_px_per_frame"]) != 39 or
        sum(slide["enter_velocity_px_per_frame"]) != 256):
        raise ValueError("unknown measured source cursor/slide cadence")
    cumulative = [0]
    for delta in slide["enter_velocity_px_per_frame"]:
        cumulative.append(cumulative[-1] + delta)
    sessions = []
    current: list[dict[str, int]] = []
    for event in events:
        if event["ordinal"] == 0 and current:
            sessions.append(current)
            current = []
        expected = len(current)
        if event["ordinal"] != expected:
            raise ValueError("missing, duplicate or out-of-order root draw ordinal")
        if event["painted"] != 1:
            raise ValueError("capture includes invisible/failed cursor render")
        if event["selection"] > 4 or event["reduced"] > 1:
            raise ValueError("invalid semantic selection or reduced motion state")
        width, height = event["surface_w"], event["surface_h"]
        if height != 224 or width not in (256, 342):
            raise ValueError("unsupported actual logical native surface geometry")
        expected_x, expected_w = ((8, 240) if width == 256 else (11, 320))
        if (event["root_x"], event["root_w"]) != (expected_x, expected_w):
            raise ValueError("focus animation rectangle differs from native root")
        if current and event["tick60"] != current[-1]["tick60"] + 1:
            raise ValueError("native root animation failed one-tick-per-draw cadence")
        if event["spin"] != (event["tick60"] // 2) % 16:
            raise ValueError("stock 32-tick cursor spin phase disagrees with source")
        age = min(expected, 39)
        measured_entrance = 0 if event["reduced"] else 256 - cumulative[age]
        if event["entrance"] != measured_entrance:
            raise ValueError("root entrance phase mismatches original 39-tick scroll")
        # No layout/guest command inferred from menu selection. For an
        # unchanged focus index on consecutive frames, the measured marker
        # must not leap more than the source-normalized first 6px step.
        if current and event["selection"] == current[-1]["selection"] and \
                event["reduced"] == current[-1]["reduced"] == 0:
            if abs(event["offset"] - current[-1]["offset"]) > 6:
                raise ValueError("source cursor movement jumped unexpectedly")
        current.append(event)
    if current:
        sessions.append(current)
    if max(map(len, sessions)) < min_frames:
        raise ValueError("no complete required native motion draw sequence")
    return [{
        "first_tick60": series[0]["tick60"],
        "last_tick60": series[-1]["tick60"],
        "draw_count": len(series),
        "logical_width": series[0]["surface_w"],
        "logical_height": series[0]["surface_h"],
        "root_x": series[0]["root_x"],
        "root_width": series[0]["root_w"],
        "reduced_motion_frames": sum(row["reduced"] for row in series),
        "final_source_entrance_remaining_px": series[-1]["entrance"],
    } for series in sessions]


def verify_log(text: str, min_frames: int = 40) -> dict:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    records = parse_log(text)
    sessions = verify_events(records, data, min_frames)
    return {
        "schema_version": 1,
        "evidence_kind": "actual_native_root_compositor_draw_receipts",
        "not_proven": [
            "SDL P7 final drawable", "real input ownership",
            "natural-clock pacing", "original-raster art", "human visual approval",
        ],
        "source_contract": SOURCE.relative_to(ROOT).as_posix(),
        "source_contract_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "native_draw_count": len(records),
        "session_count": len(sessions),
        "sessions": sessions,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host-log", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--min-frames", type=int, default=40)
    args = p.parse_args()
    logfile = args.host_log.read_bytes()
    decoded = logfile.decode("utf-8", errors="replace")
    report = verify_log(decoded, args.min_frames)
    report["original_host_log_sha256"] = hashlib.sha256(logfile).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(f"NATIVE_MOTION_DRAW_ONLY_OK "
          f"sessions={report['session_count']} draws={report['native_draw_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
