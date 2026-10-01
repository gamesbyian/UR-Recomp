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

CAMERA_AND_VIEWPORT = {
    "mode": {
        "split_screen_active_raw": ("u8", 0x0DDB),
        "player1_offscreen_raw": ("u8", 0x121B),
        "player2_offscreen_raw": ("u8", 0x121D),
    },
    "camera": {
        "player1_x": ("u16", 0x0419),
        "player2_x": ("u16", 0x041B),
        "player1_y": ("u16", 0x041D),
        "player2_y": ("u16", 0x041F),
        "player1_x_velocity": ("s16", 0x04F5),
        "player2_x_velocity": ("s16", 0x04F7),
        "player1_y_velocity": ("s16", 0x04F9),
        "player2_y_velocity": ("s16", 0x04FB),
    },
    "world_window": {
        "camera1_edge_raw": ("s16", 0x0505),
        "camera2_edge_raw": ("s16", 0x0507),
        "camera1_span_raw": ("u16", 0x052B),
        "camera2_span_raw": ("u16", 0x052D),
        "camera1_fine_raw": ("s16", 0x0509),
        "camera2_fine_raw": ("s16", 0x050B),
    },
    "screen_relative": {
        "screen2_player2_x": ("u8", 0x1501),
        "screen2_player2_y": ("u8", 0x1502),
        "screen2_player1_x": ("u8", 0x1505),
        "screen2_player1_y": ("u8", 0x1506),
        "screen1_player1_x": ("u8", 0x1509),
        "screen1_player1_y": ("u8", 0x150A),
        "screen1_player2_x": ("u8", 0x150D),
        "screen1_player2_y": ("u8", 0x150E),
        "screen1_player1_visibility_raw": ("u8", 0x1599),
    },
}

RACE_PROGRESS = {
    "player1": {
        "next_checkpoint": ("u16", 0x1199),
        "finish_gate": ("u16", 0x119D),
        "laps_remaining": ("u16", 0x0EF1),
    },
    "player2": {
        "next_checkpoint": ("u16", 0x119B),
        "finish_gate": ("u16", 0x119F),
        "laps_remaining": ("u16", 0x0EF3),
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
    out = {
        slot: {name: read_value(data, kind, addr) for name, (kind, addr) in fields.items()}
        for slot, fields in SLOTS.items()
    }
    out["camera_and_viewport"] = {
        group: {name: read_value(data, kind, addr) for name, (kind, addr) in fields.items()}
        for group, fields in CAMERA_AND_VIEWPORT.items()
    }
    out["race_progress"] = {
        player: {name: read_value(data, kind, addr) for name, (kind, addr) in fields.items()}
        for player, fields in RACE_PROGRESS.items()
    }
    return out

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
        rp1, rp2 = s["race_progress"]["player1"], s["race_progress"]["player2"]
        mode = s["camera_and_viewport"]["mode"]
        cam = s["camera_and_viewport"]["camera"]
        world = s["camera_and_viewport"]["world_window"]
        screen = s["camera_and_viewport"]["screen_relative"]
        print(
            f"{tag}: "
            f"slot1 x={a['x_pos']} y={a['y_pos']} "
            f"vx={a['x_speed']} vy={a['y_speed']} "
            f"air={a['air_effective']} rot={a['rotation_candidate']} "
            f"botPitch={a['bot_pitch_derived']} | "
            f"slot2 x={b['x_pos']} y={b['y_pos']} "
            f"vx={b['x_speed']} vy={b['y_speed']} "
            f"air={b['air']} rot={b['rotation_candidate']} | "
            f"split={mode['split_screen_active_raw']} "
            f"offscreen=({mode['player1_offscreen_raw']},{mode['player2_offscreen_raw']}) | "
            f"camera p1=({cam['player1_x']},{cam['player1_y']}) "
            f"p2=({cam['player2_x']},{cam['player2_y']}) "
            f"p1v=({cam['player1_x_velocity']},{cam['player1_y_velocity']}) "
            f"p2v=({cam['player2_x_velocity']},{cam['player2_y_velocity']}) | "
            f"worldwin p1edge={world['camera1_edge_raw']} span={world['camera1_span_raw']} "
            f"p2edge={world['camera2_edge_raw']} span={world['camera2_span_raw']} | "
            f"screen1 p1=({screen['screen1_player1_x']},{screen['screen1_player1_y']}) "
            f"p2=({screen['screen1_player2_x']},{screen['screen1_player2_y']}) "
            f"screen2 p1=({screen['screen2_player1_x']},{screen['screen2_player1_y']}) "
            f"p2=({screen['screen2_player2_x']},{screen['screen2_player2_y']}) "
            f"vis1raw={screen['screen1_player1_visibility_raw']} | "
            f"finish p1 checkpoint={rp1['next_checkpoint']} gate={rp1['finish_gate']} "
            f"laps={rp1['laps_remaining']} p2 checkpoint={rp2['next_checkpoint']} "
            f"gate={rp2['finish_gate']} laps={rp2['laps_remaining']}"
        )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
