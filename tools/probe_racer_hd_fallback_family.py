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
)

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


def build_report(rom: bytes, registry: dict[str, Any]) -> dict[str, Any]:
    players = {}
    any_exact_reuse = False
    requires_new_pose = False

    for player in ("p1", "p2"):
        target_entry = temporary_entry(player)
        target = build_stock_rgba(rom, target_entry)
        target_hash = sha256(target)
        target_alpha_hash = alpha_mask_sha256(target)

        matches = []
        canonical = {}
        for entry in approved_same_player_entries(registry, player):
            stock = build_stock_rgba(rom, entry)
            stock_hash = sha256(stock)
            row = canonical.setdefault(stock_hash, {
                "stock_rgba_sha256": stock_hash,
                "alpha_mask_sha256": alpha_mask_sha256(stock),
                "semantic_frame_ids": set(),
                "representation_ids": [],
                "shipping_approval_sources": set(),
                "alpha_bounds": alpha_bounds(stock, W, H),
                "contact_x2_y2": alpha_contact_anchor_x2_y2(stock, W, H),
            })
            row["semantic_frame_ids"].add(entry["semantic_frame_id"])
            row["representation_ids"].append(entry["representation_id"])
            row["shipping_approval_sources"].add(
                entry["authored_candidate"]["shipping_approval_source"]
            )
            if stock_hash == target_hash:
                matches.append(entry["representation_id"])

        canonical_rows = []
        for row in canonical.values():
            canonical_rows.append({
                **row,
                "semantic_frame_ids": sorted(row["semantic_frame_ids"]),
                "representation_ids": sorted(row["representation_ids"]),
                "shipping_approval_sources": sorted(row["shipping_approval_sources"]),
            })
        canonical_rows.sort(key=lambda row: row["stock_rgba_sha256"])

        exact = bool(matches)
        any_exact_reuse = any_exact_reuse or exact
        requires_new_pose = requires_new_pose or not exact
        players[player] = {
            "palette_asset_id": target_entry["palette_asset_id"],
            "semantic_frame_id": TARGET_STATE[f"{player}_primary"],
            "stock_rgba_sha256": target_hash,
            "alpha_mask_sha256": target_alpha_hash,
            "alpha_bounds": alpha_bounds(target, W, H),
            "contact_x2_y2": alpha_contact_anchor_x2_y2(target, W, H),
            "approved_same_player_unique_stock_pose_count": len(canonical_rows),
            "exact_rgba_reuse_matches": sorted(matches),
            "exact_rgba_reuse_proven": exact,
            "palette_normalization_disposition": (
                "not needed: all approved same-player comparison poses use the same "
                "stock palette asset, so exact RGBA is already the stricter proof"
            ),
            "approved_same_player_pose_catalog": canonical_rows,
        }

    return {
        "schema_version": 1,
        "purpose": "Bounded pre-registration reuse discriminator for measured Racer HD fallback burden.",
        "target": {
            "state": TARGET_STATE,
            "frames": TARGET_FRAMES,
            "episode_count": 2,
            "player_fallback_frames": 12,
        },
        "players": players,
        "disposition": {
            "all_players_exact_reuse_proven": all(
                players[p]["exact_rgba_reuse_proven"] for p in ("p1", "p2")
            ),
            "any_player_exact_reuse_proven": any_exact_reuse,
            "requires_at_least_one_new_pose": requires_new_pose,
            "admission_rule": (
                "Register only players with exact approved same-player stock-RGBA reuse. "
                "Any unmatched player remains Original until one distinct authored pose "
                "passes the ordinary dossier, review, temporal and hash-bound shipping gates."
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
    args = parser.parse_args()

    report = build_report(
        args.rom.read_bytes(),
        json.loads(args.registry.read_text(encoding="utf-8")),
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
