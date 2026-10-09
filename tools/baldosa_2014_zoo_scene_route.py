#!/usr/bin/env python3
"""Translate the pinned completed *original* 2014 Zoom Zoo input scene to
Baldosa's existing press/wait script grammar. Investigative, non-admitting.

This is input transplantation, not an emulator comparison or a result pass.
The scene is keyed to each fresh guest's real race entry, rather than movie
absolute frame numbers. No write/poke of guest memory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import extract_historical_smv_scene_window as movie

ROOT = Path(__file__).resolve().parents[1]
INPUT_SHA_1810 = "e77f10e4d652dfb2ed9afcf4c252e3e9f14e551a30edbbaa2a69ec50996f90b6"
FIRST = 3190
RESULT_ONSET = 8353
WINDOW = 5170  # onset at +5163, second witness six frames after +5169
BUTTONS = ((0x001, "b"), (0x002, "y"), (0x004, "select"),
           (0x008, "start"), (0x010, "up"), (0x020, "down"),
           (0x040, "left"), (0x080, "right"), (0x100, "a"),
           (0x200, "x"), (0x400, "l"), (0x800, "r"))
GO_GATE = "until 0E1F != 00\n"
START_GATE = "until16 0053 == 8610\n"


def scene_commands(segments: list[dict], count: int) -> list[str]:
    """Exactly preserve translated SNES button masks, including idle gaps."""
    if not 1 <= count <= movie.LIMIT:
        raise ValueError("invalid bounded source window")
    lines = []
    at = 0
    for segment in segments:
        start, duration, mask = (
            segment["start"], segment["duration"], int(segment["mask"], 16))
        if (type(start) is not int or type(duration) is not int or start < at
                or duration < 1 or start + duration > count
                or mask <= 0 or mask > 0xFFF):
            raise ValueError("invalid overlapping or out-of-window source input")
        if start > at:
            lines.append(f"wait {start - at}")
        buttons = [name for bit, name in BUTTONS if mask & bit]
        if not buttons:
            raise ValueError("unknown SNES button mask")
        lines.append(f"press {'+'.join(buttons)} {duration}")
        at = start + duration
    if at < count:
        lines.append(f"wait {count - at}")
    return lines


def source_menu_prefix(route: str) -> str:
    """Seal original Baldosa menu navigation, replace only its GO timer gate."""
    if (route.count(GO_GATE) != 1
            or route.count(START_GATE) != 1
            or route.index(GO_GATE) < route.index(START_GATE)
            or "press left 6000" not in route
            or route.count("until16 0053 == F60C") != 2):
        raise ValueError("upstream Zoom Zoo menu route unexpectedly changed")
    menu = route.split(GO_GATE, 1)[0]
    if not menu.endswith(START_GATE):
        raise ValueError("unexpected drive prefix")
    # Source input begins at its independently verified first active race
    # frame, not after the stopwatch first ticks 206 frames later.
    return menu + "until 0313 == 01\ndump scene-entered\n"


def render(prefix: str, segments: list[dict], frames: int = WINDOW) -> str:
    if not prefix.endswith("dump scene-entered\n"):
        raise ValueError("missing scene anchor")
    return (prefix + "\n".join(scene_commands(segments, frames)) +
            "\ndump result-onset-candidate\nwait 6\n"
            "dump result-stable-candidate\nquit\n")


def generate(meta: Path, upstream: Path, out: Path, report_path: Path) -> dict:
    source, _ = movie.read_movie(movie.ARCHIVE)
    metadata = json.loads(meta.read_text(encoding="utf-8"))
    prefix = movie.window(source, metadata, FIRST, 1810)
    if prefix["raw_controller_window_sha256"] != INPUT_SHA_1810:
        raise ValueError("2014 original Zoo opening input fingerprint changed")
    full = movie.window(source, metadata, FIRST, WINDOW)
    original_menu = source_menu_prefix(upstream.read_text(encoding="utf-8"))
    route = render(original_menu, full["relative_input_segments"])
    out.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(route, encoding="utf-8")
    report = {
        "schema_version": 1,
        "source": "original 2014 Snes9x Dessyreqt movie, reset and SRAM anchored",
        "first_original_frame": FIRST,
        "original_circuit_result_onset_frame": RESULT_ONSET,
        "selected_input_frame_range": [FIRST, FIRST + WINDOW - 1],
        "raw_original_input_sha256": full["raw_controller_window_sha256"],
        "raw_prefix_1810_sha256": INPUT_SHA_1810,
        "route_sha256": hashlib.sha256(route.encode()).hexdigest(),
        "source_run_count": len(full["relative_input_segments"]),
        "screen_result_not_proven_by_this_generation": True,
        "original_native_course_qa_credit": 0,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--meta", type=Path, default=movie.METADATA)
    ap.add_argument("--upstream", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(generate(args.meta, args.upstream, args.out, args.report)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
