#!/usr/bin/env python3
"""Generic bounded reuse discriminator for one measured Racer HD exact state."""

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

from prototype_racer_hd_replacement import (
    W, H, alpha_bounds, alpha_contact_anchor_x2_y2, build_stock_rgba,
    encode_png_rgba, nearest_rgba,
)
from probe_racer_hd_fallback_family import (
    palette_normalized_rgba, palette_role_indices,
)
from extract_racer_presentation_family import rgba_palette


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def target_entry(player: str, state: dict) -> dict:
    return {
        "player": player,
        "palette_asset_id": "0x06" if player == "p1" else "0x07",
        "composition_guards": state,
    }


def approved_entries(registry: dict) -> list[dict]:
    return [
        entry for entry in registry["entries"]
        if entry.get("authored_candidate", {}).get("shipping_approval_source")
    ]


def build_report(rom: bytes, registry: dict, state: dict, frames: list[int], output_dir: Path | None) -> dict:
    roles = palette_role_indices(rom)
    palettes = {
        "p1": rgba_palette(rom, 0x06),
        "p2": rgba_palette(rom, 0x07),
    }
    catalog = []
    for entry in approved_entries(registry):
        stock = build_stock_rgba(rom, entry)
        player = entry["player"]
        catalog.append({
            "representation_id": entry["representation_id"],
            "player": player,
            "semantic_frame_id": entry["semantic_frame_id"],
            "stock_rgba_sha256": sha256(stock),
            "normalized_geometry_sha256": sha256(
                palette_normalized_rgba(stock, palettes[player], roles)
            ),
        })

    players = {}
    for player in ("p1", "p2"):
        entry = target_entry(player, state)
        stock = build_stock_rgba(rom, entry)
        normalized = palette_normalized_rgba(stock, palettes[player], roles)
        exact_hash = sha256(stock)
        normalized_hash = sha256(normalized)
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / f"{player}-stock.png").write_bytes(
                encode_png_rgba(W, H, stock)
            )
            (output_dir / f"{player}-stock-4x.png").write_bytes(
                encode_png_rgba(W * 4, H * 4, nearest_rgba(stock, W, H, 4))
            )
        exact = sorted(
            row["representation_id"] for row in catalog
            if row["player"] == player and row["stock_rgba_sha256"] == exact_hash
        )
        normalized_matches = sorted(
            row["representation_id"] for row in catalog
            if row["normalized_geometry_sha256"] == normalized_hash
        )
        players[player] = {
            "semantic_frame_id": state[f"{player}_primary"],
            "stock_rgba_sha256": exact_hash,
            "normalized_geometry_sha256": normalized_hash,
            "alpha_bounds": alpha_bounds(stock, W, H),
            "contact_x2_y2": alpha_contact_anchor_x2_y2(stock, W, H),
            "exact_same_player_matches": exact,
            "palette_normalized_matches": normalized_matches,
            "reuse_proven": bool(exact or normalized_matches),
        }

    novel = [p for p, row in players.items() if not row["reuse_proven"]]
    return {
        "schema_version": 1,
        "state": state,
        "frames": frames,
        "player_fallback_frames": len(frames) * 2,
        "palette_normalization_role_indices": roles,
        "players": players,
        "disposition": {
            "novel_players": novel,
            "requires_new_pose_count": len(novel),
            "all_players_reuse_proven": not novel,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--state-json", required=True)
    ap.add_argument("--frames", required=True, help="comma-separated observed frame numbers")
    ap.add_argument("--registry", type=Path, default=ROOT / "analysis/data/racer-hd-replacement-prototype.json")
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--output-dir", type=Path)
    args = ap.parse_args()

    state = json.loads(args.state_json)
    frames = [int(x) for x in args.frames.split(",") if x]
    report = build_report(
        args.rom.read_bytes(),
        json.loads(args.registry.read_text(encoding="utf-8")),
        state,
        frames,
        args.output_dir,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
