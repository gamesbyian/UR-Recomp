#!/usr/bin/env python3
"""Evaluate actual composed native frames; route exit 0 never implies QA pass."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

COMPOSE = re.compile(r"UR_BALDOSA_NATIVE_COMPOSE frame=(\d+) racer_present=1 logical=(\d+)x(\d+) source_art=ur hd_capture=(\d+)")
SOURCE_PIXELS = re.compile(r"UR_RACER_HD_SOURCE_OBJ frame=(\d+) top_opaque=(\d+) bottom_opaque=(\d+) top_painted=(\d+) bottom_painted=(\d+)")


def assess(baseline: Path, candidate: Path, log: Path, captures: Path, density: int = 1) -> dict:
    if density not in (1, 4):
        raise ValueError("Only verified 1x and 4x presentation scales are supported")
    left, right = baseline.read_bytes(), candidate.read_bytes()
    base_frames = left.splitlines()
    own_frames = right.splitlines()
    native_log = log.read_text(encoding="utf-8", errors="replace")
    records = [tuple(map(int, m.groups())) for m in COMPOSE.finditer(native_log)]
    pixel_records = [
        tuple(map(int, m.groups())) for m in SOURCE_PIXELS.finditer(native_log)
    ]
    visible_frames = {
        x[0] for x in pixel_records
        if x[1] > 0 and x[2] > 0 and x[3] > 0 and x[4] > 0
    }
    witnessed_frames = {x[0] for x in records if x[3] == 1}
    images = sorted(captures.glob("ur-baldosa-frame-*.pam"))
    details = []
    captured_frames = set()
    spatially_nonuniform_frames = set()
    for p in images:
        data = p.read_bytes()
        expected = f"P7\nWIDTH {256*density}\nHEIGHT {224*density}\nDEPTH 4\n".encode()
        if not data.startswith(expected):
            raise ValueError(f"Unexpected composited frame geometry: {p}")
        parts = data.split(b"ENDHDR\n", 1)
        if len(parts) != 2 or len(parts[1]) != 256 * density * 224 * density * 4:
            raise ValueError(f"Truncated or invalid frame: {p}")
        match = re.fullmatch(r"ur-baldosa-frame-(\\d{6}).pam", p.name)
        if match is None:
            raise ValueError(f"Unexpected capture filename: {p}")
        frame = int(match.group(1))
        captured_frames.add(frame)
        pixels = parts[1]
        # Distinct solid-color frames do not establish moving rider imagery.
        # Every accepted capture must have actual spatial detail.
        if len(set(pixels[0::4])) > 1 or len(set(pixels[1::4])) > 1 or len(set(pixels[2::4])) > 1:
            spatially_nonuniform_frames.add(frame)
        details.append({"file": p.name, "frame": frame, "sha256": hashlib.sha256(pixels).hexdigest()})
    verified_captures = captured_frames & visible_frames & witnessed_frames & spatially_nonuniform_frames
    passed = (
        base_frames == own_frames and len(own_frames) == 2473
        and len(images) >= 2 and len({x["sha256"] for x in details}) >= 2
        and len(records) >= 2
        and all(x[1:3] == (256, 224) and x[3] == 1 for x in records)
        and len(verified_captures) >= 2
    )
    return {
        "schema_version": 1,
        "status": "passed" if passed else "unproven",
        "native_title": "Baldosa AOT with UR racer asset/PPU compositor callbacks",
        "baseline_frame_count": len(base_frames),
        "candidate_frame_count": len(own_frames),
        "all_wram_crcs_identical": base_frames == own_frames,
        "source_derived_racer_presented_records": len(records),
        "source_obj_capture_records": len(pixel_records),
        "visible_source_obj_frame_count": len(visible_frames & witnessed_frames),
        "requires_actual_source_obj_pixels_both_viewports": True,
        "captured_source_obj_spatial_frames": len(verified_captures),
        "actual_presented_rgba_frames": details,
        "distinct_presented_frames": len({x["sha256"] for x in details}),
        "logical_geometry": [256, 224],
        "composed_raster_dimensions": [256 * density, 224 * density],
        "presentation_density": density,
        "widescreen_or_4k_proved": False,
        "real_4x_authored_raster_proved": density == 4 and passed,
        "original_native_completed_event_qa_credit": 0,
        "limits": "Native 1x/4x raster only; spatial variation alone cannot prove correct racer placement or animation. No widescreen, 4K, Windows, or completed-event gate."
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
