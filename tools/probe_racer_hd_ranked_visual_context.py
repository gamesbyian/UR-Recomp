#!/usr/bin/env python3
"""Probe one ranked player-local Racer HD visual context for canonical reuse."""

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
    W,
    H,
    alpha_bounds,
    alpha_contact_anchor_x2_y2,
    build_stock_rgba,
    encode_png_rgba,
    nearest_rgba,
)
from probe_racer_hd_fallback_family import (
    palette_normalized_rgba,
    palette_role_indices,
)
from probe_racer_hd_state_reuse import approved_entries
from extract_racer_presentation_family import rgba_palette


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def composition_guards(composition: dict) -> dict:
    return {
        "p1_primary": composition["p1_primary"],
        "p2_primary": composition["p2_primary"],
        "p1_companion": composition["p1_companion"],
        "p2_companion": composition["p2_companion"],
        "p1_selector": composition["p1_selector"],
        "p2_selector": composition["p2_selector"],
        "p1_companion_gate_word": composition["p1_gate"],
        "p2_companion_gate_word": composition["p2_gate"],
    }


def local_matches(composition: dict, target: dict) -> bool:
    player = target["player"]
    return (
        composition[f"{player}_primary"] == target["semantic_frame_id"]
        and composition[f"{player}_companion"] == target["companion"]
        and composition[f"{player}_selector"] == target["selector"]
        and composition[f"{player}_gate"] == target["gate"]
    )


def build_report(
    rom: bytes,
    registry: dict,
    measurement: dict,
    rank: int,
    output_dir: Path | None,
) -> dict:
    ranked = measurement["fallback_by_player_visual_context"]
    if rank < 0 or rank >= len(ranked):
        raise ValueError(f"visual-context rank {rank} is out of range")
    target = ranked[rank]
    player = target["player"]
    palette_id = "0x06" if player == "p1" else "0x07"

    matching_states = [
        item
        for item in measurement["unsupported_exact_states_ranked"]
        if item["player_fallback_frames"].get(player, 0) > 0
        and local_matches(item["composition"], target)
    ]
    if not matching_states:
        raise ValueError("ranked visual context has no exact-state witnesses")

    samples = []
    rasters: dict[str, bytes] = {}
    for item in matching_states:
        entry = {
            "player": player,
            "palette_asset_id": palette_id,
            "composition_guards": composition_guards(item["composition"]),
        }
        stock = build_stock_rgba(rom, entry)
        digest = sha256(stock)
        rasters.setdefault(digest, stock)
        samples.append({
            "state": item["state"],
            "frames": item["frames"],
            "player_frames": item["player_fallback_frames"][player],
            "stock_rgba_sha256": digest,
            "alpha_bounds": alpha_bounds(stock, W, H),
            "contact_x2_y2": alpha_contact_anchor_x2_y2(stock, W, H),
        })

    unique_hashes = sorted(rasters)
    local_visual_identity_proven = len(unique_hashes) == 1

    canonical = rasters[unique_hashes[0]]
    roles = palette_role_indices(rom)
    palettes = {
        "p1": rgba_palette(rom, 0x06),
        "p2": rgba_palette(rom, 0x07),
    }
    normalized = palette_normalized_rgba(canonical, palettes[player], roles)
    normalized_hash = sha256(normalized)

    catalog = []
    for entry in approved_entries(registry):
        stock = build_stock_rgba(rom, entry)
        source_player = entry["player"]
        catalog.append({
            "representation_id": entry["representation_id"],
            "player": source_player,
            "semantic_frame_id": entry["semantic_frame_id"],
            "stock_rgba_sha256": sha256(stock),
            "normalized_geometry_sha256": sha256(
                palette_normalized_rgba(stock, palettes[source_player], roles)
            ),
        })

    exact_matches = sorted(
        row["representation_id"]
        for row in catalog
        if row["player"] == player
        and row["stock_rgba_sha256"] == unique_hashes[0]
    )
    normalized_matches = sorted(
        row["representation_id"]
        for row in catalog
        if row["normalized_geometry_sha256"] == normalized_hash
    )

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "stock.png").write_bytes(encode_png_rgba(W, H, canonical))
        (output_dir / "stock-4x.png").write_bytes(
            encode_png_rgba(W * 4, H * 4, nearest_rgba(canonical, W, H, 4))
        )

    return {
        "schema_version": 1,
        "rank": rank,
        "target": target,
        "witness_exact_state_count": len(matching_states),
        "witness_player_frames": sum(x["player_frames"] for x in samples),
        "witnesses": samples,
        "unique_stock_raster_count": len(unique_hashes),
        "unique_stock_rgba_sha256": unique_hashes,
        "local_visual_identity_proven": local_visual_identity_proven,
        "canonical": {
            "stock_rgba_sha256": unique_hashes[0],
            "normalized_geometry_sha256": normalized_hash,
            "alpha_bounds": alpha_bounds(canonical, W, H),
            "contact_x2_y2": alpha_contact_anchor_x2_y2(canonical, W, H),
            "exact_same_player_matches": exact_matches,
            "palette_normalized_matches": normalized_matches,
        },
        "disposition": {
            "reuse_proven": (
                local_visual_identity_proven
                and bool(exact_matches or normalized_matches)
            ),
            "requires_new_pose": not (
                local_visual_identity_proven
                and bool(exact_matches or normalized_matches)
            ),
            "reason": (
                "all synchronized witnesses collapse to one player-local stock raster"
                if local_visual_identity_proven
                else "player-local context is insufficient: synchronized witnesses differ in stock pixels"
            ),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("measurement", type=Path)
    ap.add_argument("--rank", type=int, default=0)
    ap.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "analysis/data/racer-hd-replacement-prototype.json",
    )
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--output-dir", type=Path)
    args = ap.parse_args()

    report = build_report(
        args.rom.read_bytes(),
        json.loads(args.registry.read_text(encoding="utf-8")),
        json.loads(args.measurement.read_text(encoding="utf-8")),
        args.rank,
        args.output_dir,
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
