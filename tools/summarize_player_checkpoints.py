#!/usr/bin/env python3
"""Extract normalized Uniracers player state from WRAM checkpoint dumps.

Compatibility aliases for older reports are retained, but addresses and signed
conversion live in tools/uniracers_state.py.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from uniracers_state import (
    HISTORICAL_BOT_EFFECTIVE,
    HISTORICAL_BOT_OVERWRITTEN,
    PLAYER1_FIELDS,
    PLAYER2_FIELDS,
    Field,
    read_field,
)

FIELDS: dict[str, Field] = {
    "in_race": PLAYER1_FIELDS["in_race"],
    "track": PLAYER1_FIELDS["track"],
    "x_pos": PLAYER1_FIELDS["x_pos"],
    "y_pos": PLAYER1_FIELDS["y_pos"],
    "x_speed": PLAYER1_FIELDS["x_speed"],
    "y_speed": PLAYER1_FIELDS["y_speed"],
    "pitch": PLAYER1_FIELDS["pitch"],
    "air": PLAYER1_FIELDS["air"],
    "rotation_candidate": PLAYER1_FIELDS["pitch"],
    "player2_pitch": PLAYER2_FIELDS["pitch"],
    "player2_air": PLAYER2_FIELDS["air"],
    "pitch_effective": HISTORICAL_BOT_EFFECTIVE["pitch_scratch"],
    "pitch_early_duplicate": HISTORICAL_BOT_OVERWRITTEN["pitch"],
    "air_effective": HISTORICAL_BOT_EFFECTIVE["air"],
    "air_early_duplicate": HISTORICAL_BOT_OVERWRITTEN["air"],
    "faced_direction": PLAYER1_FIELDS["faced_direction"],
    "countdown_timer": PLAYER1_FIELDS["countdown_timer"],
    "reverse_controls": PLAYER1_FIELDS["reverse_controls"],
    "screen_x": PLAYER1_FIELDS["screen_x"],
}

DEFAULT_CHECKPOINTS = [
    "race-entered",
    "accel-030",
    "accel-060",
    "accel-090",
    "accel-120",
    "accel-180",
]


def read_dump(path: Path) -> dict[str, int]:
    data = path.read_bytes()
    if len(data) < 0x20000:
        raise ValueError(f"{path}: expected 128 KiB WRAM, got {len(data)} bytes")
    return {name: read_field(data, field) for name, field in FIELDS.items()}


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
            f"pitch={state['pitch']} pitchScratch={state['pitch_effective']} "
            f"air={state['air']} player2Air={state['player2_air']} "
            f"countdown={state['countdown_timer']}"
        )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
