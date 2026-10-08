#!/usr/bin/env python3
"""Summarize historic USJO v8 reads and independently proven persistent boost slots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

FIELDS = [
    ("x_speed", 0x04B7, 16, True),
    ("y_speed", 0x04BB, 16, True),
    ("air", 0x0545, 8, False),
    ("twists", 0x0F61, 8, False),
    ("tabletops", 0x042F, 8, False),
    ("zflips", 0x042B, 8, False),
    ("rolls", 0x11F9, 8, False),
    ("flips", 0x11FD, 8, False),
    ("z_rotation", 0x0DFD, 8, False),
    ("z_pre_rotation", 0x0F57, 8, False),
    ("boost_meter_low", 0x11CD, 8, False),
    ("boost_meter_high", 0x11CE, 8, False),
    ("boost_meter_word", 0x11CD, 16, False),
    # The USJO v8 byte at 11CD is a shared racer-update workspace, not
    # the authoritative P1/P2 award destination. These game-owned persistent
    # words receive delayed queue-consumer credit at 81:C167 / 81:C2B0.
    ("p1_boost_persistent", 0x11CF, 16, False),
    ("p2_boost_persistent", 0x11D1, 16, False),
]


def read_value(blob: bytes, addr: int, width: int, signed: bool) -> int:
    if width == 8:
        return blob[addr]
    v = blob[addr] | (blob[addr + 1] << 8)
    if signed and v & 0x8000:
        v -= 0x10000
    return v


def summarize(root: Path, checkpoints: list[str]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for cp in checkpoints:
        path = root / f"{cp}.wram.bin"
        if not path.is_file():
            raise SystemExit(f"missing checkpoint dump: {path}")
        blob = path.read_bytes()
        if len(blob) != 0x20000:
            raise SystemExit(f"WRAM dump {path}: expected 131072 bytes, got {len(blob)}")
        out[cp] = {
            name: read_value(blob, addr, width, signed)
            for name, addr, width, signed in FIELDS
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump_dir", type=Path)
    ap.add_argument("--checkpoint", action="append", required=True)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    report = summarize(args.dump_dir, args.checkpoint)
    for cp, row in report.items():
        vals = " ".join(f"{k}={v}" for k, v in row.items())
        print(f"{cp}\t{vals}")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
