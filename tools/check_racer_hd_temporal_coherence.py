#!/usr/bin/env python3
"""Check temporal coherence of registered racer-HD replacement candidates.

This is an artifact-side gate. It reconstructs each registered stock racer
frame, derives the current deterministic replacement candidate, and compares
pairwise frame-to-frame alpha evolution within each player sequence. It does
not mutate guest state and it does not invent animation adjacency beyond the
registry order.
"""

from __future__ import annotations

import argparse
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
    build_remastered_candidate,
    build_stock_rgba,
    nearest_rgba,
)


def alpha_mask(rgba: bytes) -> list[int]:
    return [1 if rgba[i] else 0 for i in range(3, len(rgba), 4)]


def xor_count(a: list[int], b: list[int]) -> int:
    if len(a) != len(b):
        raise ValueError("alpha masks must have equal length")
    return sum(x != y for x, y in zip(a, b))


def entry_summary(rom: bytes, entry: dict) -> dict:
    stock = build_stock_rgba(rom, entry)
    candidate, cw, ch = build_remastered_candidate(stock, entry)
    density = int(entry["remastered_candidate"]["density_scale"])
    anchors = entry["registration"]["semantic_anchors"]
    return {
        "semantic_frame_id": entry["semantic_frame_id"],
        "player": entry["player"],
        "logical_canvas_pixels": entry["registration"]["logical_canvas_pixels"],
        "density_scale": density,
        "fixed_point_scale": int(anchors["fixed_point_scale"]),
        "pivot_x2_y2": anchors["flip_pivot_x2_y2"],
        "contact_x2_y2": anchors["wheel_contact_x2_y2"],
        "stock_alpha_bounds": alpha_bounds(stock, W, H),
        "candidate_alpha_bounds": alpha_bounds(candidate, cw, ch),
        "_stock_mask": alpha_mask(stock),
        "_candidate_mask": alpha_mask(candidate),
    }


def build_report(rom: bytes, registry: dict) -> dict:
    groups: dict[str, list[dict]] = {}
    for entry in registry["entries"]:
        groups.setdefault(entry["player"], []).append(entry_summary(rom, entry))

    sequences = {}
    all_pairs_exact = True
    shared_basis = True

    for player, frames in groups.items():
        pairs = []
        for a, b in zip(frames, frames[1:]):
            density = a["density_scale"]
            if density != b["density_scale"]:
                shared_basis = False
                expected_candidate_change = None
            else:
                stock_change = xor_count(a["_stock_mask"], b["_stock_mask"])
                candidate_change = xor_count(a["_candidate_mask"], b["_candidate_mask"])
                expected_candidate_change = stock_change * density * density
                exact = candidate_change == expected_candidate_change
                all_pairs_exact &= exact
                pairs.append({
                    "from": a["semantic_frame_id"],
                    "to": b["semantic_frame_id"],
                    "stock_alpha_changed_pixels": stock_change,
                    "candidate_alpha_changed_pixels": candidate_change,
                    "expected_candidate_alpha_changed_pixels": expected_candidate_change,
                    "alpha_transition_exact": exact,
                    "contact_delta_x2_y2": [
                        b["contact_x2_y2"][0] - a["contact_x2_y2"][0],
                        b["contact_x2_y2"][1] - a["contact_x2_y2"][1],
                    ],
                    "stock_bounds_delta": [
                        y - x for x, y in zip(a["stock_alpha_bounds"], b["stock_alpha_bounds"])
                    ],
                })

        visible = []
        for frame in frames:
            shared_basis &= (
                frame["logical_canvas_pixels"] == [64, 64]
                and frame["density_scale"] == 4
                and frame["fixed_point_scale"] == 2
                and frame["pivot_x2_y2"] == [63, 63]
            )
            visible.append({k: v for k, v in frame.items() if not k.startswith("_")})
        sequences[player] = {"frames": visible, "pairs": pairs}

    return {
        "schema_version": 1,
        "family": registry["family"],
        "sequence_order": "registry order within player; diagnostic until explicit animation adjacency is promoted",
        "sequences": sequences,
        "validation": {
            "shared_registration_basis": shared_basis,
            "candidate_alpha_transition_matches_stock": all_pairs_exact,
            "no_shipping_art_claim": True,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "analysis/data/racer-hd-replacement-prototype.json",
    )
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    report = build_report(
        args.rom.read_bytes(),
        json.loads(args.registry.read_text(encoding="utf-8")),
    )
    if not all(report["validation"].values()):
        raise SystemExit(json.dumps(report, indent=2, sort_keys=True))
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
