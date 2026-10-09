#!/usr/bin/env python3
"""Select a native PPM by *exact eight-word guest composition*, not frame number.

Original/HD/Ppu-masked host captures can drift +/- frames even on the
same ROM/input. The only acceptable source raster comparison is an exact
single guest state with a real captured host present; ambiguous repeats
or unequal same-state presents are rejected.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.check_racer_hd_wide_visual_parity import STATE_FIELDS
from tools.check_ppm import inspect_ppm
from tools.summarize_racer_semantic_trace import parse_trace


def select(reference_log: str, candidate_log: str, screenshot_dir: Path,
           *, reference_frame: int, max_offset: int = 10,
           expected_width: int = 256, expected_height: int = 224) -> tuple[bytes, dict]:
    if reference_frame < 0 or max_offset < 0:
        raise ValueError("invalid frame alignment constraints")
    reference = {
        row["frame"]: tuple(row[k] for k in STATE_FIELDS)
        for row in parse_trace(reference_log)
    }
    candidates = {
        row["frame"]: tuple(row[k] for k in STATE_FIELDS)
        for row in parse_trace(candidate_log)
    }
    wanted = reference.get(reference_frame)
    if wanted is None:
        raise ValueError("reference guest frame missing from authoritative trace")
    matching_frames = sorted(
        frame for frame, state in candidates.items()
        if abs(frame - reference_frame) <= max_offset and state == wanted
    )
    if len(matching_frames) != 1:
        raise ValueError(
            f"expected exactly one semantic-aligned candidate near {reference_frame}, "
            f"got {matching_frames}"
        )
    selected_frame = matching_frames[0]
    rows = []
    with (screenshot_dir / "presents.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["frame"]) == selected_frame:
                rows.append(int(row["present"]))
    if not rows:
        raise ValueError(f"missing captured host present for guest frame {selected_frame}")

    snapshots = []
    for index in rows:
        filepath = screenshot_dir / f"present_{index:06d}.ppm"
        summary = inspect_ppm(filepath)
        if (summary.width, summary.height) != (expected_width, expected_height):
            raise ValueError(
                f"wrong screenshot density at {selected_frame}: "
                f"{summary.width}x{summary.height}, expected "
                f"{expected_width}x{expected_height}"
            )
        snapshots.append((index, summary.sha256, filepath.read_bytes()))
    if len({digest for _, digest, _ in snapshots}) != 1:
        raise ValueError(f"different output pixels across one guest frame {selected_frame}")

    data = snapshots[0][2]
    return data, {
        "schema_version": 1,
        "classification": "exact eight-word guest-state match plus captured native present",
        "reference_guest_frame": reference_frame,
        "selected_guest_frame": selected_frame,
        "guest_frame_offset": selected_frame - reference_frame,
        "matching_state_fields": dict(zip(STATE_FIELDS, wanted)),
        "selected_present_indices": rows,
        "image_width": expected_width,
        "image_height": expected_height,
        "ppm_sha256": hashlib.sha256(data).hexdigest(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference-log", type=Path, required=True)
    ap.add_argument("--reference-frame", type=int, required=True)
    ap.add_argument("--candidate-log", type=Path, required=True)
    ap.add_argument("--candidate-dir", type=Path, required=True)
    ap.add_argument("--max-offset", type=int, default=10)
    ap.add_argument("--width", type=int, default=256)
    ap.add_argument("--height", type=int, default=224)
    ap.add_argument("--out-ppm", type=Path, required=True)
    ap.add_argument("--json-out", type=Path, required=True)
    a = ap.parse_args()
    data, report = select(
        a.reference_log.read_text(encoding="utf-8", errors="replace"),
        a.candidate_log.read_text(encoding="utf-8", errors="replace"),
        a.candidate_dir, reference_frame=a.reference_frame,
        max_offset=a.max_offset,
        expected_width=a.width, expected_height=a.height,
    )
    a.out_ppm.parent.mkdir(parents=True, exist_ok=True)
    a.out_ppm.write_bytes(data)
    a.json_out.parent.mkdir(parents=True, exist_ok=True)
    a.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        f"UR_RACER_HD_SAME_STATE PASS reference={a.reference_frame} "
        f"matched={report['selected_guest_frame']} "
        f"offset={report['guest_frame_offset']} "
        f"density={a.width}x{a.height}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
