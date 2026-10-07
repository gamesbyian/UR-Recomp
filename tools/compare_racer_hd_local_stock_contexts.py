#!/usr/bin/env python3
"""Compare two player-local stock Racer HD composition contexts exactly."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from probe_racer_hd_ranked_visual_context import (
    build_player_local_stock_rgba,
    sha256,
)
from prototype_racer_hd_replacement import W, H, alpha_bounds, alpha_contact_anchor_x2_y2


def _parse_hex(value: str) -> str:
    value = value.upper()
    if not value.startswith("0X"):
        value = "0X" + value
    int(value, 16)
    return "0x" + value[2:].upper()


def _context(
    *,
    player: str,
    primary: str,
    companion: str,
    selector: int,
    gate: str,
) -> dict:
    if player not in ("p1", "p2"):
        raise ValueError(f"unsupported player: {player}")
    blank_primary = "0x0000"
    blank_companion = "0x0000"
    return {
        "p1_primary": _parse_hex(primary) if player == "p1" else blank_primary,
        "p2_primary": _parse_hex(primary) if player == "p2" else blank_primary,
        "p1_companion": _parse_hex(companion) if player == "p1" else blank_companion,
        "p2_companion": _parse_hex(companion) if player == "p2" else blank_companion,
        "p1_selector": selector if player == "p1" else 0,
        "p2_selector": selector if player == "p2" else 0,
        "p1_gate": _parse_hex(gate) if player == "p1" else "0x0000",
        "p2_gate": _parse_hex(gate) if player == "p2" else "0x0000",
    }


def compare_rgba(left: bytes, right: bytes) -> dict:
    if len(left) != W * H * 4 or len(right) != W * H * 4:
        raise ValueError("unexpected Racer HD stock raster size")

    changed = []
    alpha_added = []
    alpha_removed = []
    color_only = []
    for y in range(H):
        for x in range(W):
            pos = (y * W + x) * 4
            a = tuple(left[pos:pos + 4])
            b = tuple(right[pos:pos + 4])
            if a == b:
                continue
            changed.append([x, y])
            if a[3] == 0 and b[3] != 0:
                alpha_added.append([x, y])
            elif a[3] != 0 and b[3] == 0:
                alpha_removed.append([x, y])
            elif a[3] != 0 and b[3] != 0:
                color_only.append([x, y])

    bbox = None
    if changed:
        xs = [p[0] for p in changed]
        ys = [p[1] for p in changed]
        bbox = [min(xs), min(ys), max(xs), max(ys)]

    return {
        "changed_pixel_count": len(changed),
        "changed_bbox_inclusive": bbox,
        "alpha_added_count": len(alpha_added),
        "alpha_removed_count": len(alpha_removed),
        "color_only_changed_count": len(color_only),
        "changed_pixels": changed,
        "alpha_added_pixels": alpha_added,
        "alpha_removed_pixels": alpha_removed,
        "color_only_changed_pixels": color_only,
    }


def compare_contexts(
    rom: bytes,
    *,
    player: str,
    left_primary: str,
    left_companion: str,
    left_selector: int,
    left_gate: str,
    right_primary: str,
    right_companion: str,
    right_selector: int,
    right_gate: str,
) -> dict:
    palette = "0x06" if player == "p1" else "0x07"
    left_context = _context(
        player=player,
        primary=left_primary,
        companion=left_companion,
        selector=left_selector,
        gate=left_gate,
    )
    right_context = _context(
        player=player,
        primary=right_primary,
        companion=right_companion,
        selector=right_selector,
        gate=right_gate,
    )
    left = build_player_local_stock_rgba(rom, player, palette, left_context)
    right = build_player_local_stock_rgba(rom, player, palette, right_context)
    delta = compare_rgba(left, right)
    return {
        "schema_version": 1,
        "player": player,
        "palette_asset_id": palette,
        "left": {
            "primary": _parse_hex(left_primary),
            "companion": _parse_hex(left_companion),
            "selector": left_selector,
            "gate": _parse_hex(left_gate),
            "stock_rgba_sha256": sha256(left),
            "alpha_bounds": alpha_bounds(left, W, H),
            "contact_x2_y2": alpha_contact_anchor_x2_y2(left, W, H),
        },
        "right": {
            "primary": _parse_hex(right_primary),
            "companion": _parse_hex(right_companion),
            "selector": right_selector,
            "gate": _parse_hex(right_gate),
            "stock_rgba_sha256": sha256(right),
            "alpha_bounds": alpha_bounds(right, W, H),
            "contact_x2_y2": alpha_contact_anchor_x2_y2(right, W, H),
        },
        "delta": delta,
        "interpretation": (
            "Exact logical 64x64 stock-raster delta only. This report may guide "
            "authored review but does not establish shipping-art approval or "
            "runtime reuse."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--player", choices=("p1", "p2"), required=True)
    for side in ("left", "right"):
        ap.add_argument(f"--{side}-primary", required=True)
        ap.add_argument(f"--{side}-companion", required=True)
        ap.add_argument(f"--{side}-selector", type=int, required=True)
        ap.add_argument(f"--{side}-gate", required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    report = compare_contexts(
        args.rom.read_bytes(),
        player=args.player,
        left_primary=args.left_primary,
        left_companion=args.left_companion,
        left_selector=args.left_selector,
        left_gate=args.left_gate,
        right_primary=args.right_primary,
        right_companion=args.right_companion,
        right_selector=args.right_selector,
        right_gate=args.right_gate,
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(payload, end="")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
