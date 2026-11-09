#!/usr/bin/env python3
"""Read-only edge-coordinate comparison of UR-Recomp and redcomp-dream.

Upstream fselich/redcomp-dream@dc3d1ed, game/src/ws_source.c::WsSrcCell,
wraps horizontal *course-cell* coordinates. UR-Recomp's production
ur_ws_course_tile rejects out-of-range coordinates. This diagnostic resolves
each wrapped candidate through UR-Recomp's existing, bounded course decoder.
It does not claim which result matches the original game's rendered pixels.

Never mutate a WRAM snapshot, infer world/viewport origin from the grid
alone, or grant WIDE-07 or original-event acceptance from this output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import probe_live_course_world_cells as course

UPSTREAM_SHA = "dc3d1edfd7a8e86921fd5ac35b1525e8069302ed"
MAX_EDGE_CELLS = 32


def compare_edge_policy(
    wram: bytes, row_cell: int, edge_cells: int = 4, *,
    identity: dict | None = None,
) -> dict:
    """Return the *different coordinate policies*, with no correctness vote."""
    coarse_w, coarse_h = course.read_world_shape(wram)
    width = coarse_w * 4
    height = coarse_h * 4
    if not 0 <= row_cell < height:
        raise ValueError("row_cell outside course grid")
    if not 1 <= edge_cells <= MAX_EDGE_CELLS:
        raise ValueError("edge_cells must be 1..32")
    if identity is not None and (
        not identity.get("full_payload_verified")
        or not isinstance(identity.get("fine_record_count"), int)
        or identity["fine_record_count"] <= 0
    ):
        raise ValueError("invalid full-payload identity")
    limit = identity["fine_record_count"] if identity else None
    coordinates = list(range(-edge_cells, 0))
    coordinates += list(range(width, width + edge_cells))
    rows = []
    for x in coordinates:
        mapped_x = x % width
        cell = course.world_cell(
            wram, mapped_x * course.CELL_WORLD_SIZE,
            row_cell * course.CELL_WORLD_SIZE,
            coarse_w, coarse_h, limit,
        )
        rows.append({
            "query_cell": [x, row_cell],
            "ur_direct_lookup": "reject_outside_grid",
            "redcomp_wrapped_cell": [mapped_x, row_cell],
            "wrapped_word": cell["packed_word"],
            "wrapped_fine_record": cell["fine_record_id"],
            "original_ppu_match": "not_measured",
        })
    return {
        "schema_version": 1,
        "status": "hypothesis_only_no_original_raster_witness",
        "upstream_repo": "fselich/redcomp-dream",
        "upstream_sha": UPSTREAM_SHA,
        "ur_source": "native/title/uniracers_ws_margins.c",
        "upstream_source": "game/src/ws_source.c",
        "wram_sha256": hashlib.sha256(wram).hexdigest(),
        "decoded_stream_identity": identity or {
            "full_payload_verified": False,
            "warning": "No --rom/--stream-index: live WRAM only, track identity not verified",
        },
        "grid_cells": [width, height],
        "row_cell": row_cell,
        "edge_cells_per_side": edge_cells,
        "rows": rows,
        "next_evidence": (
            "Compare each hypothesis with the original-USA BG1 map word at an "
            "identified matching world cell, using exact original ROM, "
            "emulator, route, guest frame, HDMA viewport, scroll, origin "
            "and independently captured PPU/VRAM hashes; no production "
            "policy change from this file alone."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wram", type=Path, help="exactly 128 KiB WRAM snapshot")
    parser.add_argument("--row-cell", type=int, required=True)
    parser.add_argument("--edge-cells", type=int, default=4)
    parser.add_argument("--rom", type=Path, help="original ROM for full stream verification")
    parser.add_argument("--stream-index", type=int, help="1..45, tied to --rom")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    if (args.rom is None) != (args.stream_index is None):
        parser.error("--rom and --stream-index must be supplied together")
    wram = args.wram.read_bytes()
    identity = (
        course.decoded_course_identity(wram, args.rom.read_bytes(), args.stream_index)
        if args.rom is not None else None
    )
    report = compare_edge_policy(
        wram, args.row_cell, args.edge_cells, identity=identity,
    )
    result = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
