#!/usr/bin/env python3
"""Measure deterministic semantic anchors for an exact composed racer state."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from extract_racer_presentation_family import (
    compose_racer_staging,
    extract_frame,
    rasterize_composed_player_rgba,
)
from prototype_racer_hd_replacement import (
    alpha_bounds,
    alpha_contact_anchor_x2_y2,
    object_flip_pivot_x2_y2,
)


def hx(value: str) -> int:
    return int(value, 0)


def measure(
    rom: bytes,
    *,
    p1_primary: int,
    p2_primary: int,
    p1_companion: int,
    p2_companion: int,
    p1_selector: int,
    p2_selector: int,
    p1_gate: int,
    p2_gate: int,
    player: str,
    palette_asset_id: int,
) -> dict:
    frames = {
        "p1_primary": extract_frame(rom, p1_primary),
        "p2_primary": extract_frame(rom, p2_primary),
        "p1_companion": extract_frame(rom, p1_companion),
        "p2_companion": extract_frame(rom, p2_companion),
    }
    composition = compose_racer_staging(
        frames["p1_primary"],
        frames["p2_primary"],
        frames["p1_companion"],
        frames["p2_companion"],
        p1_selector=p1_selector,
        p2_selector=p2_selector,
        p1_companion_enabled=p1_gate != 0,
        p2_companion_enabled=p2_gate != 0,
    )
    rgba = rasterize_composed_player_rgba(
        rom, composition, player, palette_asset_id
    )
    return {
        "player": player,
        "palette_asset_id": f"0x{palette_asset_id:02X}",
        "composition": {
            "p1_primary": f"0x{p1_primary:04X}",
            "p2_primary": f"0x{p2_primary:04X}",
            "p1_companion": f"0x{p1_companion:04X}",
            "p2_companion": f"0x{p2_companion:04X}",
            "p1_selector": p1_selector,
            "p2_selector": p2_selector,
            "p1_gate": f"0x{p1_gate:04X}",
            "p2_gate": f"0x{p2_gate:04X}",
        },
        "alpha_bounds": alpha_bounds(rgba, 64, 64),
        "flip_pivot_x2_y2": object_flip_pivot_x2_y2(64, 64),
        "wheel_contact_x2_y2": alpha_contact_anchor_x2_y2(rgba, 64, 64),
        "rgba_sha256": hashlib.sha256(rgba).hexdigest(),
        "opaque_pixel_count": sum(1 for i in range(3, len(rgba), 4) if rgba[i] != 0),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--p1-primary", required=True, type=hx)
    ap.add_argument("--p2-primary", required=True, type=hx)
    ap.add_argument("--p1-companion", required=True, type=hx)
    ap.add_argument("--p2-companion", required=True, type=hx)
    ap.add_argument("--p1-selector", default=0, type=int)
    ap.add_argument("--p2-selector", default=0, type=int)
    ap.add_argument("--p1-gate", default="0x0000", type=hx)
    ap.add_argument("--p2-gate", default="0x0000", type=hx)
    ap.add_argument("--player", required=True, choices=("p1", "p2"))
    ap.add_argument("--palette-asset-id", required=True, type=hx)
    args = ap.parse_args()

    result = measure(
        args.rom.read_bytes(),
        p1_primary=args.p1_primary,
        p2_primary=args.p2_primary,
        p1_companion=args.p1_companion,
        p2_companion=args.p2_companion,
        p1_selector=args.p1_selector,
        p2_selector=args.p2_selector,
        p1_gate=args.p1_gate,
        p2_gate=args.p2_gate,
        player=args.player,
        palette_asset_id=args.palette_asset_id,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
