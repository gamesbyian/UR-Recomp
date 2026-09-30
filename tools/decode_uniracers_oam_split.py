#!/usr/bin/env python3
"""Decode and assert Uniracers' split-screen high-OAM control byte.

SNES OAM is 544 bytes:
- 0x000..0x1FF: 128 four-byte sprite records
- 0x200..0x21F: 32 high-table bytes, two bits per sprite

Independent emulator research places Uniracers' active-display write at OAM
byte 0x218. High-table byte index 0x18 therefore controls sprites 96..99.
Within each 2-bit field, bit 0 is X position bit 8 and bit 1 is the sprite-size
selection bit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

OAM_SIZE = 544
HIGH_OAM_BASE = 0x200
TARGET_OAM_OFFSET = 0x218
TARGET_HIGH_INDEX = TARGET_OAM_OFFSET - HIGH_OAM_BASE
FIRST_SPRITE = TARGET_HIGH_INDEX * 4


def decode_high_oam_byte(value: int, first_sprite: int = FIRST_SPRITE) -> list[dict]:
    if not 0 <= value <= 0xFF:
        raise ValueError("high-OAM byte must fit 8 bits")
    return [
        {
            "sprite": first_sprite + i,
            "field": (value >> (i * 2)) & 0x03,
            "x_msb": (value >> (i * 2)) & 0x01,
            "size_select": (value >> (i * 2 + 1)) & 0x01,
        }
        for i in range(4)
    ]


def inspect_oam(path: Path, expected: int | None = None) -> dict:
    data = path.read_bytes()
    if len(data) != OAM_SIZE:
        raise ValueError(f"{path}: expected {OAM_SIZE} OAM bytes, got {len(data)}")
    value = data[TARGET_OAM_OFFSET]
    if expected is not None and value != expected:
        raise AssertionError(
            f"{path}: OAM[0x{TARGET_OAM_OFFSET:03X}]=0x{value:02X}, "
            f"expected 0x{expected:02X}"
        )
    return {
        "path": str(path),
        "oam_offset": f"0x{TARGET_OAM_OFFSET:03X}",
        "high_table_index": f"0x{TARGET_HIGH_INDEX:02X}",
        "first_sprite": FIRST_SPRITE,
        "last_sprite": FIRST_SPRITE + 3,
        "value": value,
        "value_hex": f"0x{value:02X}",
        "sprites": decode_high_oam_byte(value),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("oam", nargs="+", type=Path)
    ap.add_argument("--expect", type=lambda x: int(x, 0))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    rows = [inspect_oam(path, args.expect) for path in args.oam]
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        for row in rows:
            print(
                f"{row['path']}: {row['oam_offset']}={row['value_hex']} "
                f"sprites={row['first_sprite']}..{row['last_sprite']}"
            )
            for sprite in row["sprites"]:
                print(
                    f"  sprite {sprite['sprite']}: "
                    f"x_msb={sprite['x_msb']} size={sprite['size_select']}"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
