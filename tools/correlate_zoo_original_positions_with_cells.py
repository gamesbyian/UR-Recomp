#!/usr/bin/env python3
"""Original Snes9x Zoom Zoo samples versus exact USA checkpoint-family cells.

The candidate surface rectangles are *static*, in world coordinates. A
sampled rider inside a rectangle does NOT establish same-frame handler
dispatch: rider footprint, selected C000 slot, previous-frame contact,
and progression gate are independent evidence still to be obtained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from analyze_rnc_streams import find_streams
from analyze_course_resource_lists import parse_course_resource_list
from rnc_method1 import unpack_method1
from probe_course_checkpoint_placements import (
    USA_SHA256, CHECKPOINT_RESOURCE_ID,
    c000_resource_ranges, place_resource_cells,
)

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
REFERENCE = ROOT / "analysis/generated/historical-2014-first-race-replay.json"
FRAMES = (3400, 3800, 4200, 4600, 5000)


class SpatialWitnessError(ValueError):
    pass


def point_gap(x: int, y: int, rect: list[int]) -> tuple[int, int]:
    """Unsigned world-unit gap to inclusive 16x16 resource bounding box."""
    if not isinstance(x, int) or not isinstance(y, int):
        raise SpatialWitnessError("world coordinates must be integers")
    if len(rect) != 4:
        raise SpatialWitnessError("invalid candidate cell rectangle")
    x0, y0, x1, y1 = rect
    if x1 < x0 or y1 < y0:
        raise SpatialWitnessError("reversed candidate bounds")
    return max(x0 - x, x - x1, 0), max(y0 - y, y - y1, 0)


def closest_cells(x: int, y: int, cells: list[dict]) -> dict:
    if not cells:
        raise SpatialWitnessError("no ROM-backed candidate cells")
    ranking = sorted(
        ((dx * dx + dy * dy, dx + dy, dx, dy, item)
         for item in cells
         for dx, dy in (point_gap(x, y, item["world_cell"]),)),
        key=lambda item: (item[0], item[1], item[4]["world_cell"],
                          item[4]["c000_slot"]),
    )
    distance_squared, distance_manhattan, dx, dy, nearest = ranking[0]
    hits = [item for item in ranking if item[0] == 0]
    return {
        "nearest_distance_squared": distance_squared,
        "nearest_distance_manhattan": distance_manhattan,
        "nearest_separate_axis_gaps": [dx, dy],
        "inside_static_cell_count": len(hits),
        "nearest_world_cell": nearest["world_cell"],
        "nearest_c000_slot": nearest["c000_slot"],
        "nearest_fine_record_id": nearest["fine_record_id"],
    }


def original_zoom_zoo_positions(reference: dict) -> list[dict]:
    if reference.get("source_movie") != (
        "reference/imported/tas-bots/dessyreqt-4250-submission.smv"
    ):
        raise SpatialWitnessError("source is not the pinned original 2014 movie")
    by_frame = {row["frame"]: row for row in
                reference.get("sampled_mismatches", [])}
    positions = []
    for frame in FRAMES:
        if frame not in by_frame:
            raise SpatialWitnessError(f"missing original frame {frame}")
        row = by_frame[frame].get("reference")
        # Fields: menu, race_active, track, x, y, vx, vy, air, pitch.
        if not isinstance(row, list) or len(row) != 9 or row[:3] != [0, 1, 1]:
            raise SpatialWitnessError(
                f"original frame {frame} is not an active Zoom Zoo scene"
            )
        if not 0 <= row[3] < 16384 or not 0 <= row[4] < 4096:
            raise SpatialWitnessError(f"original frame {frame} exceeds Zoo world bounds")
        positions.append({"movie_frame": frame, "x": row[3], "y": row[4],
                          "velocity": row[5:7]})
    return positions


def build(rom: bytes, original: dict) -> dict:
    if hashlib.sha256(rom).hexdigest() != USA_SHA256:
        raise SpatialWitnessError("requires exact canonical USA retail ROM")
    streams = list(find_streams(rom))
    if len(streams) != 45:
        raise SpatialWitnessError("requires exactly 45 ROM course streams")
    decoded = unpack_method1(streams[1][1])
    parsed = parse_course_resource_list(decoded)
    if CHECKPOINT_RESOURCE_ID not in parsed["resource_ids"]:
        raise SpatialWitnessError("Zoom Zoo has no checkpoint family")
    if [n * 256 for n in parsed["layout_dims"]] != [16384, 4096]:
        raise SpatialWitnessError("Zoom Zoo original world extent changed")
    cells = place_resource_cells(
        decoded, c000_resource_ranges(rom, parsed["resource_ids"])
    )
    positions = original_zoom_zoo_positions(original)
    samples = [
        {**p, **closest_cells(p["x"], p["y"], cells)} for p in positions
    ]
    return {
        "schema_version": 1,
        "source_kind": "original-Snes9x postframe rider XY, exact-USA-ROM static resource cells",
        "course": "course:02",
        "decoded_course_resource_0x24_candidate_cells": len(cells),
        "sample_count": len(samples),
        "samples": samples,
        "limits": (
            "No original frame records executed handler PC, chosen per-player "
            "object code, stored previous-frame contact or lap-gate transition. "
            "Inside a 16x16 world cell is geometric proximity ONLY, and "
            "a separated rider center may still collide due to footprint."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, default=ROM)
    parser.add_argument("--reference", type=Path, default=REFERENCE)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    report = build(args.rom.read_bytes(),
                   json.loads(args.reference.read_text(encoding="utf-8")))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n",
                                 encoding="utf-8")
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
