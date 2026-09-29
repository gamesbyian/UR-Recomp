#!/usr/bin/env python3
"""Summarize the two recovered racer-state slots from WRAM checkpoint dumps.

This deliberately keeps the preserved bot's table structure visible instead of
pretending ambiguous duplicate keys have already been semantically resolved.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SLOTS = {
    "slot1": {
        "x_pos": ("u16", 0x0411),
        "y_pos": ("u16", 0x0415),
        "x_speed": ("s16", 0x04B7),
        "y_speed": ("s16", 0x04BB),
        "air_effective": ("u8", 0x0545),
        "rotation_candidate": ("u8", 0x04C7),
        "bot_pitch_derived": ("u8", 0x0F49),
    },
    "slot2": {
        "x_pos": ("u16", 0x0413),
        "y_pos": ("u16", 0x0417),
        "x_speed": ("s16", 0x04B9),
        "y_speed": ("s16", 0x04BD),
        "air": ("u8", 0x0547),
        "rotation_candidate": ("u8", 0x04C9),
    },
}

def read_value(data: bytes, kind: str, addr: int) -> int:
    if kind == "u8":
        return data[addr]
    raw = int.from_bytes(data[addr:addr+2], "little")
    if kind == "u16":
        return raw
    if kind == "s16":
        return raw - 0x10000 if raw & 0x8000 else raw
    raise ValueError(kind)

def state(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 0x20000:
        raise ValueError(f"{path}: expected 128 KiB WRAM")
    return {
        slot: {name: read_value(data, kind, addr) for name, (kind, addr) in fields.items()}
        for slot, fields in SLOTS.items()
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump_dir", type=Path)
    ap.add_argument("--checkpoint", action="append", required=True)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    report = {}
    for tag in args.checkpoint:
        p = args.dump_dir / f"{tag}.wram.bin"
        if not p.is_file():
            raise SystemExit(f"missing checkpoint: {p}")
        s = state(p)
        report[tag] = s
        a, b = s["slot1"], s["slot2"]
        print(
            f"{tag}: "
            f"slot1 x={a['x_pos']} y={a['y_pos']} "
            f"vx={a['x_speed']} vy={a['y_speed']} "
            f"air={a['air_effective']} rot={a['rotation_candidate']} "
            f"botPitch={a['bot_pitch_derived']} | "
            f"slot2 x={b['x_pos']} y={b['y_pos']} "
            f"vx={b['x_speed']} vy={b['y_speed']} "
            f"air={b['air']} rot={b['rotation_candidate']}"
        )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
