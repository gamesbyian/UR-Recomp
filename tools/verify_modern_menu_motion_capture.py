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


def measured_cursor_offset(distance: int, age: int, steps: list[int]) -> int:
    """Scale measured source travel to signed distance, round symmetrically."""
    if age >= len(steps):
        return 0
    source_distance = sum(steps)
    if source_distance != 23 or len(steps) != 12:
        raise ValueError("unknown source cursor movement step contract")
    remaining = source_distance - sum(steps[:age])
    magnitude = (abs(distance) * remaining + source_distance // 2) // source_distance
    return -magnitude if distance < 0 else magnitude


def verify_source_focus_timeline(events: list[dict[str, int]],
                                 source_steps: list[int]) -> None:
    """Reconstruct controller-selected marker easing independently of C++.

    Destination/semantic focus is authoritative immediately, while visible
    paint follows measured original 6,4,3,... pixel travel within 21px rows.
    Interruptions resume from their last computed onscreen cursor position,
    wrap/multi-row changes snap, and reduced motion completes pending travel.
    """
    if not events:
        raise ValueError("empty native focus timeline")
    selected = events[0]["selection"]
    origin_y = selected * 21
    selection_tick = events[0]["tick60"]
    for index, event in enumerate(events):
        tick = event["tick60"]
        next_selected = event["selection"]
        if next_selected != selected:
            old_target = selected * 21
            elapsed = min(12, tick - selection_tick)
            if origin_y != old_target and elapsed < 12:
                elapsed += 1
            old_y = old_target + measured_cursor_offset(
                origin_y - old_target, elapsed, source_steps)
            target_y = next_selected * 21
            origin_y = (old_y if abs(next_selected - selected) == 1
                        else target_y)
            selected = next_selected
            selection_tick = tick
        if event["reduced"]:
            origin_y = selected * 21
            selection_tick = tick
            expected_offset = 0
        else:
            age = min(12, tick - selection_tick)
            if origin_y != selected * 21 and age < 12:
                age += 1  # original visible response occurs on input frame
            expected_offset = measured_cursor_offset(
                origin_y - selected * 21, age, source_steps)
        if event["offset"] != expected_offset:
            raise ValueError(
                "source cursor signed easing mismatches at native draw "
                f"{index}: expected {expected_offset}, got {event['offset']}")


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
            numeric = r"-?[0-9]+" if key == "offset" else r"[0-9]+"
            if key not in FIELDS or key in item or not re.fullmatch(numeric, value):
                raise ValueError("unexpected, duplicate or malformed motion field")
            number = int(value)
            if key == "offset":
                if not -(1 << 31) <= number < (1 << 31):
                    raise ValueError("native signed cursor offset overflow")
            elif number > (1 << 64) - 1:
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
                  min_frames: int = 40,
                  allow_multi_session: bool = False) -> list[dict]:
    """Source timing independent of C++ constants and final SDL readback."""
    if not 1 <= min_frames <= MAX_EVENTS:
        raise ValueError("invalid minimum source native draw count")
    cursor = original["cursor"]
    slide = original["transition_main_to_options"]
    if (cursor["spin_period_frames"] != 32 or
        cursor["spin_frames_per_tile"] != [2] or
        cursor["move_y_per_frame"] != [6, 4, 3, 3, 2, 1, 1, 1, 1, 0, 0, 1] or
        slide["distance_px"] != 256 or slide["enter_frames"] != 39 or
        len(slide["enter_velocity_px_per_frame"]) != 39 or
        sum(slide["enter_velocity_px_per_frame"]) != 256):
        raise ValueError("unknown measured source cursor/slide cadence")
    cumulative = [0]
    for delta in slide["enter_velocity_px_per_frame"]:
        cumulative.append(cumulative[-1] + delta)
    sessions = []
    current: list[dict[str, int]] = []
    # Reduced motion finishes an already visible source entrance. Turning
    # motion back on must not falsely replay it, per live C++ state contract.
    intro_suppressed = False
    for event in events:
        if event["ordinal"] == 0 and current:
            if not allow_multi_session:
                raise ValueError("unexpected native root session restart; "
                                 "pass --allow-multi-session only with "
                                 "independent hide/reentry evidence")
            if len(current) < min_frames:
                raise ValueError("truncated native root session before restart")
            sessions.append(current)
            current = []
            intro_suppressed = False
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
        if current and (width, height, expected_x, expected_w) != (
                current[0]["surface_w"], current[0]["surface_h"],
                current[0]["root_x"], current[0]["root_w"]):
            raise ValueError("native root capture changed physical geometry mid-session")
        if current and event["tick60"] != current[-1]["tick60"] + 1:
            raise ValueError("native root animation failed one-tick-per-draw cadence")
        expected_spin = (
            0 if event["reduced"] else (event["tick60"] // 2) % 16)
        if event["spin"] != expected_spin:
            raise ValueError("stock 32-tick cursor spin phase disagrees with source")
        age = min(expected, 39)
        intro_suppressed = intro_suppressed or bool(event["reduced"])
        measured_entrance = (
            0 if intro_suppressed else 256 - cumulative[age])
        if event["entrance"] != measured_entrance:
            raise ValueError("root entrance phase mismatches original 39-tick scroll")
        current.append(event)
    if current:
        sessions.append(current)
    if any(len(session) < min_frames for session in sessions):
        raise ValueError("no complete required native motion draw sequence")
    for session in sessions:
        verify_source_focus_timeline(session, cursor["move_y_per_frame"])
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


def verify_log(text: str, min_frames: int = 40,
               allow_multi_session: bool = False) -> dict:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    records = parse_log(text)
    sessions = verify_events(records, data, min_frames, allow_multi_session)
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
    p.add_argument("--allow-multi-session", action="store_true",
                   help="Require external hide/reentry evidence for each session")
    args = p.parse_args()
    logfile = args.host_log.read_bytes()
    decoded = logfile.decode("utf-8", errors="replace")
    report = verify_log(decoded, args.min_frames, args.allow_multi_session)
    report["original_host_log_sha256"] = hashlib.sha256(logfile).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(f"NATIVE_MOTION_DRAW_ONLY_OK "
          f"sessions={report['session_count']} draws={report['native_draw_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
