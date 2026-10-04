#!/usr/bin/env python3
"""Build the margin-independent structured result for a VS Widescreen capacity run."""

from __future__ import annotations
import argparse
import json
import struct
from pathlib import Path
from typing import Any

PROTECTED = ("slot1", "slot2", "race_progress", "camera_and_viewport")

def bmp_dims(path: Path) -> list[int]:
    data = path.read_bytes()
    if len(data) < 26 or data[:2] != b"BM":
        raise ValueError(f"not a BMP: {path}")
    return [struct.unpack_from("<i", data, 18)[0], abs(struct.unpack_from("<i", data, 22)[0])]

def build_result(control: dict[str, Any], candidate: dict[str, Any], control_dims: list[int], candidate_dims: list[int], margin: int) -> dict[str, Any]:
    rows = []
    accepted = True
    for checkpoint, control_row in control.items():
        if checkpoint not in candidate:
            rows.append({"checkpoint": checkpoint, "protected_differences": {"missing_candidate_checkpoint": True}})
            accepted = False
            continue
        diffs = {}
        for section in PROTECTED:
            if control_row.get(section) != candidate[checkpoint].get(section):
                diffs[section] = {"control": control_row.get(section), "candidate": candidate[checkpoint].get(section)}
        rows.append({"checkpoint": checkpoint, "protected_differences": diffs})
        accepted = accepted and not diffs
    expected_candidate_dims = [256 + 2 * margin, 224]
    geometry_ok = control_dims == [256, 224] and candidate_dims == expected_candidate_dims
    classification = (
        f"vs-plus{margin}-live-course-capacity-proven"
        if accepted and geometry_ok
        else f"vs-plus{margin}-capacity-rejected"
    )
    return {
        "schema_version": 2,
        "fixture": "vs-first-race",
        "candidate_margin_pixels_per_side": margin,
        "control_frame_geometry": control_dims,
        f"plus{margin}_frame_geometry": candidate_dims,
        "protected_sections": list(PROTECTED),
        "rows": rows,
        "protected_state_equal_at_all_checkpoints": accepted,
        "geometry_accepted": geometry_ok,
        "capacity_classification": classification,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-state", required=True, type=Path)
    parser.add_argument("--candidate-state", required=True, type=Path)
    parser.add_argument("--control-frame", required=True, type=Path)
    parser.add_argument("--candidate-frame", required=True, type=Path)
    parser.add_argument("--margin", required=True, type=int)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = build_result(
        json.loads(args.control_state.read_text()),
        json.loads(args.candidate_state.read_text()),
        bmp_dims(args.control_frame),
        bmp_dims(args.candidate_frame),
        args.margin,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["protected_state_equal_at_all_checkpoints"] and result["geometry_accepted"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
