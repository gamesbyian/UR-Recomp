#!/usr/bin/env python3
"""Read placed course surface words from a native 128 KiB WRAM snapshot.

This reads guest course data at 7F:000F/800F, and behavior code at 7E:C000.
The low-ten-bit C000 selector is ROM-recovered; the other packed-word bits,
contact footprint, and checkpoint activation conditions remain unclassified.

Use --rom and --stream-index to demand full exact stream identity before
interpreting the live surface. Without those options, records are structurally
bounded but the loaded stream's identity is intentionally unverified.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyze_rnc_streams import find_streams
from probe_runtime_course_payload import is_fully_loaded_course
from rnc_method1 import unpack_method1

WRAM_SIZE = 0x20000
COURSE_BASE = 0x10000
COARSE_BASE = COURSE_BASE + 0x000F
FINE_BASE = COURSE_BASE + 0x800F
C000_BASE = 0xC000
COARSE_COUNT = 16384
FINE_BYTES = 32
CELL_WORLD_SIZE = 16
COARSE_WORLD_SIZE = 64


def u16(wram: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(wram):
        raise ValueError("u16 read exceeds WRAM")
    return wram[offset] | (wram[offset + 1] << 8)


def read_world_shape(wram: bytes) -> tuple[int, int]:
    if len(wram) != WRAM_SIZE:
        raise ValueError(f"expected exactly {WRAM_SIZE} bytes of WRAM")
    a, b = wram[COURSE_BASE + 13], wram[COURSE_BASE + 14]
    width = (a or 256) * 4
    height = (b or 256) * 4
    if width * height != COARSE_COUNT:
        raise ValueError("decoded course header does not define 16384 coarse sectors")
    return width, height


def decoded_course_identity(wram: bytes, rom: bytes, index: int) -> dict:
    """Require complete stream equality except loader-mutated bytes 0B/0C."""
    streams = list(find_streams(rom))
    if len(streams) != 45 or not 1 <= index <= 45:
        raise ValueError("expected 45 validated RNC streams and index 1..45")
    decoded = unpack_method1(streams[index - 1][1])
    if not is_fully_loaded_course(decoded, wram[COURSE_BASE:]):
        raise ValueError("selected course payload is not fully resident at 7F:0000")
    cursor = u16(decoded, 11)
    if cursor < 0x800F or (cursor - 0x800F) % FINE_BYTES:
        raise ValueError("decoded course has invalid fine-record boundary")
    return {
        "stream_index": index,
        "full_payload_verified": True,
        "fine_record_count": (cursor - 0x800F) // FINE_BYTES,
        "decoded_payload_size": len(decoded),
    }


def world_cell(
    wram: bytes, x: int, y: int, coarse_width: int, coarse_height: int,
    fine_record_limit: int | None = None,
) -> dict:
    if not (0 <= x < coarse_width * COARSE_WORLD_SIZE
            and 0 <= y < coarse_height * COARSE_WORLD_SIZE):
        raise ValueError("world position outside runtime course extent")
    sx, sy = x // COARSE_WORLD_SIZE, y // COARSE_WORLD_SIZE
    if not 0 <= sy * coarse_width + sx < COARSE_COUNT:
        raise ValueError("course coarse-sector index outside fixed table")
    record = u16(wram, COARSE_BASE + 2 * (sy * coarse_width + sx))
    physical_limit = (WRAM_SIZE - FINE_BASE) // FINE_BYTES
    limit = physical_limit if fine_record_limit is None else fine_record_limit
    if record >= limit or record >= physical_limit:
        raise ValueError(f"coarse sector selects out-of-range fine record {record}")
    local_x, local_y = (x // 16) % 4, (y // 16) % 4
    word = u16(wram, FINE_BASE + record * 32 + 2 * (local_y * 4 + local_x))
    slot = None
    behavior = None
    if word & 0x03FF:
        slot = ((word & 0x000F) >> 1) + ((word & 0x03F0) >> 2)
        if not 0 <= slot < 0x2000:
            raise ValueError("C000 slot outside WRAM behavior plane")
        behavior = wram[C000_BASE + slot]
    cell_x, cell_y = x // 16 * 16, y // 16 * 16
    return {
        "world_rect": [cell_x, cell_y, cell_x + 15, cell_y + 15],
        "coarse_sector": [sx, sy],
        "fine_record_id": record,
        "fine_cell": [local_x, local_y],
        "packed_word": f"{word:04X}",
        "c000_slot": slot,
        "c000_behavior_code": behavior,
        "c000_behavior_hex": f"{behavior:02X}" if behavior is not None else None,
        "a000_range": [slot * 32, slot * 32 + 31] if slot is not None else None,
        "known_selector_only": True,
    }


def query_rect(
    wram: bytes, rect: tuple[int, int, int, int], *,
    stream_identity: dict | None = None, max_cells: int = 1024,
) -> dict:
    width, height = read_world_shape(wram)
    x0, y0, x1, y1 = rect
    if x0 > x1 or y0 > y1:
        raise ValueError("query rectangle is reversed")
    if x0 < 0 or y0 < 0 or x1 >= width * 64 or y1 >= height * 64:
        raise ValueError("query rectangle lies outside course world extent")
    cols = x1 // 16 - x0 // 16 + 1
    rows = y1 // 16 - y0 // 16 + 1
    if cols * rows > max_cells:
        raise ValueError("query exceeds bounded cell-count limit")
    limit = stream_identity["fine_record_count"] if stream_identity else None
    cells = [
        world_cell(wram, x * 16, y * 16, width, height, limit)
        for y in range(y0 // 16, y1 // 16 + 1)
        for x in range(x0 // 16, x1 // 16 + 1)
    ]
    return {
        "schema_version": 1,
        "authority": "native WRAM placed course data",
        "stream_identity": stream_identity or {
            "full_payload_verified": False,
            "warning": "No ROM identity supplied; cell values are live, but stream identity is unverified",
        },
        "world_extent": [width * 64, height * 64],
        "query_rect": list(rect),
        "cell_count": len(cells),
        "cells": cells,
        "semantic_limit": (
            "C000 behavior bytes and packed selectors are runtime observations. "
            "Selection does not establish checkpoint activation, collision "
            "contact coordinate, or race progress."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("wram", type=Path, help="128 KiB native WRAM snapshot")
    ap.add_argument("--rect", type=int, nargs=4, required=True, metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--rom", type=Path, help="ROM for full selected-stream verification")
    ap.add_argument("--stream-index", type=int)
    ap.add_argument("--max-cells", type=int, default=1024)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    if (args.rom is None) != (args.stream_index is None):
        ap.error("--rom and --stream-index must be provided together")
    wram = args.wram.read_bytes()
    read_world_shape(wram)
    identity = (
        decoded_course_identity(wram, args.rom.read_bytes(), args.stream_index)
        if args.rom else None
    )
    result = query_rect(
        wram, tuple(args.rect), stream_identity=identity,
        max_cells=args.max_cells,
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
