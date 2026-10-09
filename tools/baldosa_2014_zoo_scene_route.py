#!/usr/bin/env python3
"""Create scene-anchored 2014 Zoo calibration/replay scripts WITHOUT changing
any 2014 controller timing. Actual dense inputs go via a frame file.

Critical original/native finding: each upstream `press` command inserts one
RELEASE frame. Translating 340 contiguous original movie runs to 340 `press`
commands inserted 340 extra frames (the first A/B run both wandered onward
to track 2 by their final probe). The menu script remains authoritative only
before active Zoo entry; within the scene a direct per-frame input stream
is essential. No guest writes, never an accepted result merely by timing.
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
WINDOW = 5170
BEFORE_RESULT = 4700
# Original 2014 WRAM-transition neighborhoods; a diagnostic capture is frame-neutral.
# These are hypotheses for the fresh boot, not assumed proof of lap crossings.
PROGRESS_FRAMES = (218, 604, 841, 1532, 1721)
GO_GATE = "until 0E1F != 00\n"
START_GATE = "until16 0053 == 8610\n"


def source_menu_prefix(route: str) -> str:
    """Seal upstream's original menu inputs and pivot to first active Zoo."""
    if (route.count(GO_GATE) != 1
            or route.count(START_GATE) != 1
            or route.index(GO_GATE) < route.index(START_GATE)
            or "press left 6000" not in route
            or route.count("until16 0053 == F60C") != 2):
        raise ValueError("upstream Zoom Zoo menu route unexpectedly changed")
    menu = route.split(GO_GATE, 1)[0]
    if not menu.endswith(START_GATE):
        raise ValueError("unexpected drive prefix")
    return menu + "until 0313 == 01\ndump scene-entered\n"


def render_calibration(prefix: str) -> str:
    if not prefix.endswith("dump scene-entered\n"):
        raise ValueError("missing scene anchor")
    return prefix + "quit\n"


def render_replay(prefix: str) -> str:
    """Use zero in-scene `press` calls: direct frame file holds all input."""
    if not prefix.endswith("dump scene-entered\n"):
        raise ValueError("missing scene anchor")
    parts = [prefix]
    previous = 0
    for relative_frame in PROGRESS_FRAMES:
        parts.append(f"wait {relative_frame - previous}\ndump progress-{relative_frame:04d}\n")
        previous = relative_frame
    parts.append(f"wait {BEFORE_RESULT - previous}\ndump pre-result\n")
    parts.append("until 009F == BC 1200\n"
                 "dump result-onset-candidate\nwait 8\n"
                 "dump result-stable-candidate\nquit\n")
    return "".join(parts)


def verified_window(meta: Path) -> dict:
    source, _ = movie.read_movie(movie.ARCHIVE)
    metadata = json.loads(meta.read_text(encoding="utf-8"))
    prefix = movie.window(source, metadata, FIRST, 1810)
    if prefix["raw_controller_window_sha256"] != INPUT_SHA_1810:
        raise ValueError("2014 original Zoo opening input fingerprint changed")
    return movie.window(source, metadata, FIRST, WINDOW)


def generate(meta: Path, upstream: Path, out: Path, calibration: Path,
             report_path: Path) -> dict:
    full = verified_window(meta)
    prefix = source_menu_prefix(upstream.read_text(encoding="utf-8"))
    route = render_replay(prefix)
    cal = render_calibration(prefix)
    for path, content in ((out, route), (calibration, cal)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    report = {
        "schema_version": 2,
        "source": "original 2014 Snes9x Dessyreqt movie, reset and SRAM anchored",
        "first_original_frame": FIRST,
        "original_circuit_result_onset_frame": RESULT_ONSET,
        "selected_input_frame_range": [FIRST, FIRST + WINDOW - 1],
        "raw_original_input_sha256": full["raw_controller_window_sha256"],
        "raw_prefix_1810_sha256": INPUT_SHA_1810,
        "replay_script_sha256": hashlib.sha256(route.encode()).hexdigest(),
        "calibration_script_sha256": hashlib.sha256(cal.encode()).hexdigest(),
        "source_run_count": len(full["relative_input_segments"]),
        "requires_direct_frame_inputs": True,
        "native_scene_input_is_disposable_qa_only": True,
        "original_native_course_qa_credit": 0,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--meta", type=Path, default=movie.METADATA)
    ap.add_argument("--upstream", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--calibration-out", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(generate(
        args.meta, args.upstream, args.out, args.calibration_out, args.report)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
