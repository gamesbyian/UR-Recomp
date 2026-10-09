#!/usr/bin/env python3
"""Evaluate actual composed native frames; route exit 0 never implies QA pass."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

COMPOSE = re.compile(r"UR_BALDOSA_NATIVE_COMPOSE frame=(\d+) racer_present=1 logical=(\d+)x(\d+) source_art=ur hd_capture=(\d+)")


def assess(baseline: Path, candidate: Path, log: Path, captures: Path, density: int = 1) -> dict:
    if density not in (1, 4):
        raise ValueError("Only verified 1x and 4x presentation scales are supported")
    left, right = baseline.read_bytes(), candidate.read_bytes()
    base_frames = left.splitlines()
    own_frames = right.splitlines()
    records = [tuple(map(int, m.groups())) for m in COMPOSE.finditer(
        log.read_text(encoding="utf-8", errors="replace"))]
    images = sorted(captures.glob("ur-baldosa-frame-*.pam"))
    details = []
    for p in images:
        data = p.read_bytes()
        expected = f"P7\nWIDTH {256*density}\nHEIGHT {224*density}\nDEPTH 4\n".encode()
        if not data.startswith(expected):
            raise ValueError(f"Unexpected composited frame geometry: {p}")
        parts = data.split(b"ENDHDR\n", 1)
        if len(parts) != 2 or len(parts[1]) != 256 * density * 224 * density * 4:
            raise ValueError(f"Truncated or invalid frame: {p}")
        details.append({"file": p.name, "sha256": hashlib.sha256(parts[1]).hexdigest()})
    return {
        "schema_version": 1,
        "status": "passed" if (
            base_frames == own_frames and len(own_frames) == 2473
            and len(images) >= 2 and len({x["sha256"] for x in details}) >= 2
            and len(records) >= 2 and all(x[1:3] == (256, 224) and x[3] == 1 for x in records)
        ) else "unproven",
        "native_title": "Baldosa AOT with UR racer asset/PPU compositor callbacks",
        "baseline_frame_count": len(base_frames),
        "candidate_frame_count": len(own_frames),
        "all_wram_crcs_identical": base_frames == own_frames,
        "source_derived_racer_presented_records": len(records),
        "actual_presented_rgba_frames": details,
        "distinct_presented_frames": len({x["sha256"] for x in details}),
        "logical_geometry": [256, 224],
        "composed_raster_dimensions": [256 * density, 224 * density],
        "presentation_density": density,
        "widescreen_or_4k_proved": False,
        "real_4x_authored_raster_proved": density == 4 and len(images) >= 2 and len({x["sha256"] for x in details}) >= 2,
        "original_native_completed_event_qa_credit": 0,
        "limits": "Native composed 1x raster only; screenshots require visual/original oracle review; no Windows or full course result gate."
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in ("baseline", "candidate", "log", "captures", "out"):
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--density", type=int, default=1, choices=[1, 4])
    a = ap.parse_args()
    result = assess(a.baseline, a.candidate, a.log, a.captures, density=a.density)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
