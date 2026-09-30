#!/usr/bin/env python3
"""Model the SNES live sprite-engine OAM cursor during active display.

This is a small executable specification for the active-display $2104 behavior
used by Uniracers VS mode. It follows the cursor rules implemented by pinned
jgenesis: two-dot sprite evaluation, reverse-order tile fetch, 32-sprite and
34-tile limits, and retention of the last fetched sprite index across lines
that contain no sprites.

It intentionally models only the cursor. It does not render pixels or emulate
the complete PPU.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

OAM_BYTES = 544
MAX_SPRITES_PER_LINE = 32
MAX_SPRITE_TILES_PER_LINE = 34
SPRITE_EVALUATION_END_DOT = 256
SPRITE_FETCH_START_DOT = 270
SPRITE_FETCH_END_DOT = 340

OBJ_SIZES = (
    ((8, 8), (16, 16)),
    ((8, 8), (32, 32)),
    ((8, 8), (64, 64)),
    ((16, 16), (32, 32)),
    ((16, 16), (64, 64)),
    ((32, 32), (64, 64)),
    ((16, 32), (32, 64)),
    ((16, 32), (32, 32)),
)


@dataclass(frozen=True)
class Sprite:
    index: int
    x: int
    y: int
    width: int
    height: int


def _decode_sprite(oam: bytes | bytearray, index: int, size_select: int) -> Sprite:
    if len(oam) != OAM_BYTES:
        raise ValueError(f"OAM image must be exactly {OAM_BYTES} bytes")
    if not 0 <= index < 128:
        raise ValueError("sprite index must be 0..127")
    if not 0 <= size_select < 8:
        raise ValueError("OBJ size select must be 0..7")

    base = index * 4
    high = oam[0x200 + (index >> 2)] >> (2 * (index & 3))
    x = oam[base] | ((high & 1) << 8)
    large = bool(high & 2)
    width, height = OBJ_SIZES[size_select][1 if large else 0]
    return Sprite(index=index, x=x, y=oam[base + 1], width=width, height=height)


def _line_overlaps(y: int, height: int, scanline: int) -> bool:
    delta = (scanline - y) & 0xFF
    return delta < height


def _sprite_is_scan_candidate(sprite: Sprite, scanline: int) -> bool:
    if not _line_overlaps(sprite.y, sprite.height, scanline):
        return False
    return not (sprite.x >= 256 and sprite.x + sprite.width <= 512)


def scan_sprites(
    oam: bytes | bytearray,
    *,
    scanline: int,
    size_select: int,
    start_index: int = 0,
    limit: int = 128,
) -> tuple[list[int], int]:
    """Scan up to *limit* OBJ entries and return accepted indices + next index."""
    if not 0 <= scanline <= 255:
        raise ValueError("scanline must be 0..255")
    if not 0 <= start_index < 128:
        raise ValueError("start index must be 0..127")
    if limit < 0:
        raise ValueError("limit must be non-negative")

    accepted: list[int] = []
    index = start_index
    for _ in range(min(limit, 128)):
        sprite = _decode_sprite(oam, index, size_select)
        if _sprite_is_scan_candidate(sprite, scanline):
            if len(accepted) == MAX_SPRITES_PER_LINE:
                return accepted, (index + 1) & 0x7F
            accepted.append(index)
        index = (index + 1) & 0x7F
    return accepted, index


def active_oam_sprite_index(
    oam: bytes | bytearray,
    *,
    scanline: int,
    dot: int,
    size_select: int,
    last_fetched_index: int,
    start_index: int = 0,
) -> tuple[int, int]:
    """Return (live_cursor_index, updated_last_fetched_index).

    `last_fetched_index` is persistent PPU state from previous lines. The
    returned second value is what should be carried forward after progressing
    sprite fetch to `dot`.
    """
    if not 0 <= dot <= 340:
        raise ValueError("dot must be 0..340")
    if not 0 <= last_fetched_index < 128:
        raise ValueError("last fetched index must be 0..127")

    if dot <= SPRITE_EVALUATION_END_DOT:
        accepted, next_index = scan_sprites(
            oam,
            scanline=scanline,
            size_select=size_select,
            start_index=start_index,
            limit=dot // 2,
        )
        if dot == SPRITE_EVALUATION_END_DOT or len(accepted) == MAX_SPRITES_PER_LINE:
            cursor = last_fetched_index if not accepted else 0
            return cursor, last_fetched_index
        return next_index, last_fetched_index

    accepted, _ = scan_sprites(
        oam,
        scanline=scanline,
        size_select=size_select,
        start_index=start_index,
        limit=128,
    )
    if dot < SPRITE_FETCH_START_DOT:
        return (last_fetched_index if not accepted else 0), last_fetched_index
    if not accepted:
        return last_fetched_index, last_fetched_index

    end_dot = min(dot, SPRITE_FETCH_END_DOT)
    tiles_to_fetch = end_dot // 2 - SPRITE_FETCH_START_DOT // 2
    buffer_index = len(accepted) - 1
    tile_index = 0
    fetched = 0
    last = last_fetched_index

    while fetched < tiles_to_fetch:
        obj_index = accepted[buffer_index]
        sprite = _decode_sprite(oam, obj_index, size_select)

        if not _line_overlaps(sprite.y, sprite.height, scanline):
            if buffer_index == 0:
                return last, last
            buffer_index -= 1
            tile_index = 0
            continue

        tile_count = sprite.width // 8
        while tile_index < tile_count and fetched < tiles_to_fetch:
            tile_x = sprite.x + 8 * tile_index
            if tile_x >= 256 and tile_x + 8 < 512:
                tile_index += 1
                continue

            if fetched == MAX_SPRITE_TILES_PER_LINE:
                return last, last

            last = obj_index
            tile_index += 1
            fetched += 1

        if tile_index == tile_count:
            if buffer_index == 0:
                return last, last
            buffer_index -= 1
            tile_index = 0

    if dot >= SPRITE_FETCH_END_DOT:
        return last, last
    return accepted[buffer_index], last


def high_oam_byte(index: int) -> int:
    if not 0 <= index < 128:
        raise ValueError("sprite index must be 0..127")
    return 0x200 | (index >> 2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("oam", type=Path, help="544-byte OAM snapshot")
    ap.add_argument("--scanline", type=lambda x: int(x, 0), required=True)
    ap.add_argument("--dot", type=lambda x: int(x, 0), required=True)
    ap.add_argument("--size-select", type=lambda x: int(x, 0), required=True)
    ap.add_argument("--last-fetched-index", type=lambda x: int(x, 0), required=True)
    ap.add_argument("--start-index", type=lambda x: int(x, 0), default=0)
    args = ap.parse_args()

    cursor, last = active_oam_sprite_index(
        args.oam.read_bytes(),
        scanline=args.scanline,
        dot=args.dot,
        size_select=args.size_select,
        last_fetched_index=args.last_fetched_index,
        start_index=args.start_index,
    )
    report = {
        "schema_version": 1,
        "scanline": args.scanline,
        "dot": args.dot,
        "cursor_sprite_index": cursor,
        "high_oam_byte": f"0x{high_oam_byte(cursor):03X}",
        "last_fetched_index": last,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
