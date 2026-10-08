#!/usr/bin/env python3
"""ROM-authoritative world-cell candidates for the checkpoint/finish resource.

This is a static course-content probe, NOT proof that a cell fired an event.
Resource 0x24 is behavior-confirmed on Dragster and incidence-promoted across
the race/circuit family. Per-course checkpoint order and contact semantics
still require deterministic emulator observations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from analyze_course_resource_lists import parse_course_resource_list
from analyze_rnc_streams import find_streams
from build_course_presentation_contract import (
    COARSE_TABLE_BASE, FINE_TABLE_BASE, FINE_RECORD_BYTES, descriptor,
)
from rnc_method1 import unpack_method1

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
LANDMARKS = ROOT / "analysis/generated/dessyreqt-course-landmarks.json"
USA_SHA256 = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
CHECKPOINT_RESOURCE_ID = 0x24


def le16(data: bytes, offset: int) -> int:
    return data[offset] | (data[offset + 1] << 8)


def c000_resource_ranges(rom: bytes, resource_ids: list[int]) -> list[dict]:
    """Compute ordered, repeated-resource-safe ranges from USA descriptors."""
    out = []
    cursor = 0
    for resource_id in resource_ids:
        length = descriptor(rom, resource_id)["c000_span"]
        if length <= 0:
            raise ValueError(f"resource {resource_id:02X} has empty C000 span")
        out.append({
            "resource_id": resource_id,
            "start": cursor,
            "end": cursor + length - 1,
        })
        cursor += length
    return out


def place_resource_cells(decoded: bytes, ranges: list[dict], target: int = 0x24) -> list[dict]:
    """Resolve every 16x16 world cell referencing a target resource span."""
    parsed = parse_course_resource_list(decoded)
    width, height = parsed["layout_dims"][0] * 4, parsed["layout_dims"][1] * 4
    if width * height != 16384:
        raise ValueError("invalid coarse-sector dimensions")
    cursor = parsed["resource_cursor_initial"]
    if cursor < FINE_TABLE_BASE or (cursor - FINE_TABLE_BASE) % FINE_RECORD_BYTES:
        raise ValueError("invalid 32-byte fine-record boundary")
    records = (cursor - FINE_TABLE_BASE) // FINE_RECORD_BYTES
    if not records:
        raise ValueError("course has zero fine records")
    spans = [(x["start"], x["end"]) for x in ranges if x["resource_id"] == target]
    if not spans:
        return []
    if any(lo < 0 or hi < lo for lo, hi in spans):
        raise ValueError("invalid C000 resource span")
    fine: dict[int, list[tuple[int, int]]] = {}
    result = []
    for sector_index in range(16384):
        record_id = le16(decoded, COARSE_TABLE_BASE + sector_index * 2)
        if record_id >= records:
            raise ValueError(f"sector {sector_index} has invalid fine record {record_id}")
        if record_id not in fine:
            cells = []
            base = FINE_TABLE_BASE + record_id * 32
            for index in range(16):
                word = le16(decoded, base + 2 * index)
                if not (word & 0x03FF):
                    continue
                slot = ((word & 0x000F) >> 1) + ((word & 0x03F0) >> 2)
                if any(lo <= slot <= hi for lo, hi in spans):
                    cells.append((index, slot))
            fine[record_id] = cells
        sx, sy = sector_index % width, sector_index // width
        for local, slot in fine[record_id]:
            x = sx * 64 + (local % 4) * 16
            y = sy * 64 + (local // 4) * 16
            result.append({
                "world_cell": [x, y, x + 15, y + 15],
                "coarse_sector": [sx, sy],
                "fine_record_id": record_id,
                "local_cell": [local % 4, local // 4],
                "c000_slot": slot,
            })
    return result


def summarize_placements(
    cells: list[dict],
    probe_x: int | None = None,
    query_rect: tuple[int, int, int, int] | None = None,
) -> dict:
    """Separate historical X-only finish leads from confirmed cell positions."""
    sectors = sorted({tuple(p["coarse_sector"]) for p in cells})
    records = sorted({p["fine_record_id"] for p in cells})
    summary = {
        "candidate_world_cells": len(cells),
        "candidate_coarse_sectors": len(sectors),
        "fine_record_ids": records,
        "coordinate_authority": "decoded USA course / descriptor-derived resource spans",
        "event_authority": "unconfirmed for individual placements",
    }
    if probe_x is not None:
        matches = [p for p in cells if p["world_cell"][0] <= probe_x <= p["world_cell"][2]]
        distances = [
            max(p["world_cell"][0] - probe_x, probe_x - p["world_cell"][2], 0)
            for p in cells
        ]
        summary["historical_finish_x_probe"] = {
            "x": probe_x,
            "matching_candidate_cells": len(matches),
            "closest_candidate_x_distance": min(distances) if distances else None,
            "first_24_matching_candidates": matches[:24],
            "warning": "X-only optimizer coordinate, not a runtime finish-line proof",
        }
    if query_rect is not None:
        x0, y0, x1, y1 = query_rect
        if x0 > x1 or y0 > y1:
            raise ValueError("query rectangle bounds are reversed")
        hits = [p for p in cells if (
            p["world_cell"][0] <= x1 and p["world_cell"][2] >= x0
            and p["world_cell"][1] <= y1 and p["world_cell"][3] >= y0
        )]
        summary["query"] = {
            "world_rect": list(query_rect),
            "candidate_count": len(hits),
            "candidate_cells": hits,
        }
    return summary


def inspect_course(
    rom: bytes, stream_index: int, probe_x: int | None = None,
    query_rect: tuple[int, int, int, int] | None = None,
) -> dict:
    if hashlib.sha256(rom).hexdigest() != USA_SHA256:
        raise ValueError("this descriptor-address probe requires the exact USA retail ROM")
    streams = list(find_streams(rom))
    if len(streams) != 45 or not 1 <= stream_index <= 45:
        raise ValueError("expected 45 course streams and a stream index in 1..45")
    decoded = unpack_method1(streams[stream_index - 1][1])
    parsed = parse_course_resource_list(decoded)
    if probe_x is None:
        landmarks = json.loads(LANDMARKS.read_text(encoding="utf-8"))["tracks"]
        probe_x = next(x["finish_x"] for x in landmarks if x["track_id"] == stream_index - 1)
    ranges = c000_resource_ranges(rom, parsed["resource_ids"])
    cells = place_resource_cells(decoded, ranges, CHECKPOINT_RESOURCE_ID)
    return {
        "schema_version": 1,
        "stream_index": stream_index,
        "track_id": stream_index - 1,
        "is_stunt": stream_index % 5 == 3,
        "resource_0x24_present": CHECKPOINT_RESOURCE_ID in parsed["resource_ids"],
        "resource_0x24_c000_ranges": [
            [x["start"], x["end"]] for x in ranges
            if x["resource_id"] == CHECKPOINT_RESOURCE_ID
        ],
        "world_extent": [parsed["layout_dims"][0] * 256, parsed["layout_dims"][1] * 256],
        "summary": summarize_placements(cells, probe_x, query_rect),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, default=ROM)
    parser.add_argument("--stream-index", type=int, default=1)
    parser.add_argument("--probe-x", type=int, default=None)
    parser.add_argument("--query-rect", type=int, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    result = inspect_course(
        args.rom.read_bytes(), args.stream_index, args.probe_x,
        tuple(args.query_rect) if args.query_rect else None,
    )
    rendered = json.dumps(result, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
