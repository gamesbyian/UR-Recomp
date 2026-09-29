#!/usr/bin/env python3
"""Extract recovered player-1 state anchors from WRAM checkpoint dumps."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

FIELDS = {
    "in_race": ("u8", 0x0313),
    "track": ("u8", 0x00CE),
    "x_pos": ("u16", 0x0411),
    "y_pos": ("u16", 0x0415),
    "x_speed": ("s16", 0x04B7),
    "y_speed": ("s16", 0x04BB),
    # Dessyreqt's player-1 Lua table declares airValue and pitch twice.
    # Lua keeps the later key, so these are the effective addresses used by
    # the bot. The earlier candidates are retained separately for archaeology.
    "pitch_effective": ("u8", 0x0F49),
    "pitch_early_duplicate": ("u8", 0x04C9),
    "air_effective": ("u8", 0x0545),
    "air_early_duplicate": ("u8", 0x0547),
    "faced_direction": ("u8", 0x0BA1),
    "countdown_timer": ("u16", 0x11BA),
    "reverse_controls": ("u8", 0x132B),
    "screen_x": ("u8", 0x1509),
}

DEFAULT_CHECKPOINTS = [
    "race-entered",
    "accel-030",
    "accel-060",
    "accel-090",
    "accel-120",
    "accel-180",
]


def read_field(data: bytes, kind: str, addr: int) -> int:
    if kind == "u8":
        return data[addr]
    raw = int.from_bytes(data[addr : addr + 2], "little", signed=False)
    if kind == "u16":
        return raw
    if kind == "s16":
        return raw - 0x10000 if raw & 0x8000 else raw
    raise ValueError(kind)


def read_dump(path: Path) -> dict[str, int]:
    data = path.read_bytes()
    if len(data) < 0x20000:
        raise ValueError(f"{path}: expected 128 KiB WRAM, got {len(data)} bytes")
    return {name: read_field(data, kind, addr) for name, (kind, addr) in FIELDS.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump_dir", type=Path)
    ap.add_argument("--checkpoint", action="append", dest="checkpoints")
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    checkpoints = args.checkpoints or DEFAULT_CHECKPOINTS
    report: dict[str, dict[str, int]] = {}
    for tag in checkpoints:
        p = args.dump_dir / f"{tag}.wram.bin"
        if not p.is_file():
            raise SystemExit(f"missing checkpoint: {p}")
        state = read_dump(p)
        report[tag] = state
        print(
            f"{tag}: "
            f"xPos={state['x_pos']} yPos={state['y_pos']} "
            f"xSpeed={state['x_speed']} ySpeed={state['y_speed']} "
            f"pitch={state['pitch_effective']} pitchEarly={state['pitch_early_duplicate']} "
            f"air={state['air_effective']} airEarly={state['air_early_duplicate']} "
            f"countdown={state['countdown_timer']}"
        )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
