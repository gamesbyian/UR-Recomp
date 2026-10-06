#!/usr/bin/env python3
"""Probe one measured unsupported Racer HD state against shipping same-player poses.

This is intentionally narrower than the registered-family dossier. It answers the
pre-registration question: can an unsupported exact state reuse already-approved
same-player stock geometry, or would admission require a genuinely new pose?
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

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
from extract_racer_presentation_family import rgba_palette

TARGET_STATE = {
    "p1_primary": "0x0544",
    "p2_primary": "0x0578",
    "p1_companion": "0x0000",
    "p2_companion": "0x0D63",
    "p1_selector": 0,
    "p2_selector": 0,
    "p1_companion_gate_word": "0x0000",
    "p2_companion_gate_word": "0x0001",
}
TARGET_FRAMES = [1280, 1281, 1282, 1283, 1285, 1286]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def alpha_mask_sha256(rgba: bytes) -> str:
    if len(rgba) != W * H * 4:
        raise ValueError("unexpected RGBA byte length")
    return sha256(bytes(1 if rgba[i + 3] else 0 for i in range(0, len(rgba), 4)))


def palette_role_indices(rom: bytes) -> list[int]:
    """Return palette slots whose values differ between the proven P1/P2 palettes."""
    p1 = rgba_palette(rom, 0x06)
    p2 = rgba_palette(rom, 0x07)
    if len(p1) != len(p2):
        raise ValueError("racer palettes have different lengths")
    roles = [i for i, pair in enumerate(zip(p1, p2)) if pair[0] != pair[1]]
    if 0 in roles:
        raise ValueError("transparent palette role may not be normalized")
    return roles


def palette_normalized_rgba(
    rgba: bytes,
    palette: list[tuple[int, int, int, int]],
    role_indices: list[int],
) -> bytes:
    """Replace only proven player-color palette values with stable role tokens."""
    role_map: dict[bytes, bytes] = {}
    for index in role_indices:
        source = bytes(palette[index])
        if source in role_map and role_map[source] != bytes((index, 0, 0, 255)):
            raise ValueError("ambiguous racer-color palette value")
        role_map[source] = bytes((index, 0, 0, 255))

    out = bytearray(rgba)
    for i in range(0, len(out), 4):
        pixel = bytes(out[i:i + 4])
        token = role_map.get(pixel)
        if token is not None:
            out[i:i + 4] = token
    return bytes(out)


def temporary_entry(player: str) -> dict[str, Any]:
    if player not in ("p1", "p2"):
        raise ValueError(player)
    return {
        "player": player,
        "palette_asset_id": "0x06" if player == "p1" else "0x07",
        "composition_guards": dict(TARGET_STATE),
    }


def approved_same_player_entries(registry: dict[str, Any], player: str) -> list[dict[str, Any]]:
    rows = []
    for entry in registry["entries"]:
        if entry.get("player") != player:
            continue
        authored = entry.get("authored_candidate")
        if not authored:
            continue
        if not authored.get("shipping_approval_source"):
            continue
        rows.append(entry)
    return rows


def build_report(rom: bytes, registry: dict[str, Any], output_dir: Path | None = None) -> dict[str, Any]:
    roles = palette_role_indices(rom)
    palettes = {
        "p1": rgba_palette(rom, 0x06),
        "p2": rgba_palette(rom, 0x07),
    }

    approved = []
    seen_representation_ids = set()
    for player in ("p1", "p2"):
        for entry in approved_same_player_entries(registry, player):
            rid = entry["representation_id"]
            if rid in seen_representation_ids:
                continue
            seen_representation_ids.add(rid)
            stock = build_stock_rgba(rom, entry)
            normalized = palette_normalized_rgba(stock, palettes[player], roles)
            approved.append({
                "player": player,
                "semantic_frame_id": entry["semantic_frame_id"],
                "representation_id": rid,
                "palette_asset_id": entry["palette_asset_id"],
                "shipping_approval_source": entry["authored_candidate"]["shipping_approval_source"],
                "stock_rgba_sha256": sha256(stock),
                "normalized_geometry_sha256": sha256(normalized),
                "alpha_mask_sha256": alpha_mask_sha256(stock),
                "alpha_bounds": alpha_bounds(stock, W, H),
                "contact_x2_y2": alpha_contact_anchor_x2_y2(stock, W, H),
            })

    players = {}
    for player in ("p1", "p2"):
        target_entry = temporary_entry(player)
        target = build_stock_rgba(rom, target_entry)
        normalized = palette_normalized_rgba(target, palettes[player], roles)
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / f"{player}-stock.png").write_bytes(
                encode_png_rgba(W, H, target)
            )
            stock4 = nearest_rgba(target, W, H, 4)
            (output_dir / f"{player}-stock-4x.png").write_bytes(
                encode_png_rgba(W * 4, H * 4, stock4)
            )
        target_hash = sha256(target)
        normalized_hash = sha256(normalized)

        same_player_exact = sorted(
            row["representation_id"] for row in approved
            if row["player"] == player and row["stock_rgba_sha256"] == target_hash
        )
        palette_normalized = sorted(
            row["representation_id"] for row in approved
            if row["normalized_geometry_sha256"] == normalized_hash
        )

        players[player] = {
            "palette_asset_id": target_entry["palette_asset_id"],
            "semantic_frame_id": TARGET_STATE[f"{player}_primary"],
            "stock_rgba_sha256": target_hash,
            "normalized_geometry_sha256": normalized_hash,
            "alpha_mask_sha256": alpha_mask_sha256(target),
            "alpha_bounds": alpha_bounds(target, W, H),
            "contact_x2_y2": alpha_contact_anchor_x2_y2(target, W, H),
            "exact_same_player_reuse_matches": same_player_exact,
            "exact_same_player_reuse_proven": bool(same_player_exact),
            "palette_normalized_reuse_matches": palette_normalized,
            "palette_normalized_reuse_proven": bool(palette_normalized),
        }

    all_reusable = all(
        players[p]["exact_same_player_reuse_proven"]
        or players[p]["palette_normalized_reuse_proven"]
        for p in ("p1", "p2")
    )
    novel = [
        p for p in ("p1", "p2")
        if not (
            players[p]["exact_same_player_reuse_proven"]
            or players[p]["palette_normalized_reuse_proven"]
        )
    ]
    return {
        "schema_version": 2,
        "purpose": "Bounded pre-registration reuse discriminator for measured Racer HD fallback burden.",
        "target": {
            "state": TARGET_STATE,
            "frames": TARGET_FRAMES,
            "episode_count": 2,
            "player_fallback_frames": 12,
        },
        "palette_normalization": {
            "palette_assets": ["0x06", "0x07"],
            "normalized_role_indices": roles,
            "rule": (
                "Only palette indices whose canonical P1/P2 values differ are replaced "
                "by stable role tokens; transparent and byte-identical neutral/material "
                "entries remain untouched."
            ),
        },
        "players": players,
        "approved_pose_catalog": approved,
        "disposition": {
            "all_players_reuse_proven": all_reusable,
            "novel_players": novel,
            "requires_new_pose_count": len(novel),
            "admission_rule": (
                "Exact same-player RGBA reuse is preferred. Cross-player reuse is allowed "
                "only when the palette-normalized stock raster is byte-identical after "
                "normalizing exactly the proven player-color palette roles. Unmatched poses "
                "remain Original until distinct authored art passes ordinary review gates."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=Path)
    parser.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "analysis/data/racer-hd-replacement-prototype.json",
    )
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--trace-out", type=Path)
    args = parser.parse_args()

    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    report = build_report(
        args.rom.read_bytes(),
        registry,
        args.output_dir,
    )
    if args.trace_out:
        ids = {
            "p1": "ordinary-racer-0x0544-p1-frequency-0578-reference",
            "p2": "ordinary-racer-0x0578-p2-frequency-0544-reference",
        }
        known = {entry["representation_id"] for entry in registry["entries"]}
        if not all(rid in known for rid in ids.values()):
            raise SystemExit("target family is not fully registered")
        trace = {
            "schema_version": 1,
            "source": {
                "kind": "retained-measured-fallback-family",
                "fallback_report": "analysis/generated/racer-hd-fallback-frequency-2026-10-05.json",
                "state": TARGET_STATE,
                "frames": TARGET_FRAMES,
            },
            "registered_composition_coverage": {
                "frames": [
                    {
                        "frame": frame,
                        "fully_registered": True,
                        "p1_representation_id": ids["p1"],
                        "p2_representation_id": ids["p2"],
                    }
                    for frame in TARGET_FRAMES
                ]
            },
        }
        args.trace_out.parent.mkdir(parents=True, exist_ok=True)
        args.trace_out.write_text(
            json.dumps(trace, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
