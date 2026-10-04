#!/usr/bin/env python3
"""Gate temporal coherence of the explicitly reviewed authored Racer HD strip.

Unlike the earlier contract-candidate diagnostic, this checker follows the
promoted frame-by-frame motion-review sequence and samples the actual authored
4x assets at gameplay logical-pixel centres. It verifies per-frame stock
geometry/contact, exact stillness on stock-static edges, preserved motion on
stock-dynamic edges, and a deliberately broad authored/stock transition-size
band measured from the completed 1205-1220 sequence.
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

from prototype_racer_hd_replacement import W, H, build_stock_rgba
from build_racer_hd_asset_dossier import authored_candidate_rgba_for_entry


def alpha_mask(rgba: bytes) -> list[int]:
    return [1 if rgba[i] else 0 for i in range(3, len(rgba), 4)]


def logical_center_alpha_mask(authored_rgba: bytes, density: int = 4) -> list[int]:
    expected = W * density * H * density * 4
    if len(authored_rgba) != expected:
        raise ValueError(f"unexpected authored RGBA length: {len(authored_rgba)} != {expected}")
    out = []
    stride = W * density
    centre = density // 2
    for y in range(H):
        for x in range(W):
            index = (((y * density + centre) * stride) + (x * density + centre)) * 4 + 3
            out.append(1 if authored_rgba[index] else 0)
    return out


def xor_count(a: list[int], b: list[int]) -> int:
    if len(a) != len(b):
        raise ValueError("alpha masks must have equal length")
    return sum(x != y for x, y in zip(a, b))


def mask_bounds(mask: list[int]) -> list[int]:
    points = [(i % W, i // W) for i, bit in enumerate(mask) if bit]
    if not points:
        raise ValueError("alpha mask is empty")
    return [
        min(x for x, _ in points),
        min(y for _, y in points),
        max(x for x, _ in points),
        max(y for _, y in points),
    ]


def mask_contact_x2_y2(mask: list[int]) -> list[int]:
    points = [(i % W, i // W) for i, bit in enumerate(mask) if bit]
    if not points:
        raise ValueError("alpha mask is empty")
    bottom = max(y for _, y in points)
    xs = [x for x, y in points if y == bottom]
    return [min(xs) + max(xs), bottom * 2]


def evaluate_transition(
    a: dict,
    b: dict,
    ratio_min: float,
    ratio_max: float,
) -> dict:
    stock_change = xor_count(a["_stock_mask"], b["_stock_mask"])
    authored_change = xor_count(a["_authored_mask"], b["_authored_mask"])
    static_edge = stock_change == 0
    ratio = None if static_edge else authored_change / stock_change
    return {
        "from_frame": a["frame"],
        "to_frame": b["frame"],
        "from_representation_id": a["representation_id"],
        "to_representation_id": b["representation_id"],
        "stock_alpha_changed_pixels": stock_change,
        "authored_alpha_changed_pixels": authored_change,
        "transition_class": "static" if static_edge else "dynamic",
        "static_edge_preserved": (authored_change == 0) if static_edge else True,
        "dynamic_edge_preserved": (authored_change > 0) if not static_edge else True,
        "authored_to_stock_change_ratio": ratio,
        "transition_ratio_within_bounds": (
            True if static_edge else ratio_min <= ratio <= ratio_max
        ),
        "stock_contact_delta_x2_y2": [
            b["stock_contact_x2_y2"][0] - a["stock_contact_x2_y2"][0],
            b["stock_contact_x2_y2"][1] - a["stock_contact_x2_y2"][1],
        ],
        "authored_contact_delta_x2_y2": [
            b["authored_contact_x2_y2"][0] - a["authored_contact_x2_y2"][0],
            b["authored_contact_x2_y2"][1] - a["authored_contact_x2_y2"][1],
        ],
    }


def build_report(rom: bytes, registry: dict) -> dict:
    review = registry.get("motion_review_sequence")
    if not isinstance(review, dict):
        raise ValueError("registry lacks motion_review_sequence")

    start = int(review["window_start"])
    end = int(review["window_end"])
    rows = review["frames"]
    expected_frames = list(range(start, end + 1))
    actual_frames = [int(row["frame"]) for row in rows]
    if actual_frames != expected_frames:
        raise ValueError(f"motion-review sequence is not exact/contiguous: {actual_frames}")

    acceptance = review["acceptance"]
    ratio_min = float(acceptance["dynamic_transition_ratio_min"])
    ratio_max = float(acceptance["dynamic_transition_ratio_max"])
    entries = {entry["representation_id"]: entry for entry in registry["entries"]}

    sequences: dict[str, dict] = {}
    all_authored = True
    exact_bounds = True
    exact_contacts = True
    static_preserved = True
    dynamic_preserved = True
    ratio_bounded = True
    contact_delta_exact = True

    for player in ("p1", "p2"):
        frames = []
        key = f"{player}_representation_id"
        for row in rows:
            rid = row[key]
            entry = entries.get(rid)
            if entry is None:
                raise ValueError(f"unregistered motion-review representation: {rid}")
            authored_meta = entry.get("authored_candidate")
            all_authored &= authored_meta is not None
            if authored_meta is None:
                raise ValueError(f"motion-review representation lacks authored art: {rid}")

            stock = build_stock_rgba(rom, entry)
            authored, _generator, _sampler = authored_candidate_rgba_for_entry(entry)
            stock_mask = alpha_mask(stock)
            authored_mask = logical_center_alpha_mask(authored)
            stock_bounds = mask_bounds(stock_mask)
            authored_bounds = mask_bounds(authored_mask)
            stock_contact = mask_contact_x2_y2(stock_mask)
            authored_contact = mask_contact_x2_y2(authored_mask)

            exact_bounds &= authored_bounds == stock_bounds
            exact_contacts &= authored_contact == stock_contact
            exact_contacts &= authored_contact == entry["registration"]["semantic_anchors"]["wheel_contact_x2_y2"]

            frames.append({
                "frame": int(row["frame"]),
                "representation_id": rid,
                "semantic_frame_id": entry["semantic_frame_id"],
                "stock_alpha_bounds": stock_bounds,
                "authored_alpha_bounds": authored_bounds,
                "stock_contact_x2_y2": stock_contact,
                "authored_contact_x2_y2": authored_contact,
                "_stock_mask": stock_mask,
                "_authored_mask": authored_mask,
            })

        pairs = [
            evaluate_transition(a, b, ratio_min, ratio_max)
            for a, b in zip(frames, frames[1:])
        ]
        for pair in pairs:
            static_preserved &= pair["static_edge_preserved"]
            dynamic_preserved &= pair["dynamic_edge_preserved"]
            ratio_bounded &= pair["transition_ratio_within_bounds"]
            contact_delta_exact &= (
                pair["stock_contact_delta_x2_y2"] == pair["authored_contact_delta_x2_y2"]
            )

        visible = [
            {k: v for k, v in frame.items() if not k.startswith("_")}
            for frame in frames
        ]
        sequences[player] = {"frames": visible, "pairs": pairs}

    return {
        "schema_version": 2,
        "family": registry["family"],
        "sequence_order": "explicit promoted motion_review_sequence frame order",
        "window": [start, end],
        "sampling": review["sampling"],
        "acceptance": acceptance,
        "sequences": sequences,
        "validation": {
            "all_review_frames_authored": all_authored,
            "authored_bounds_match_stock": exact_bounds,
            "authored_contact_matches_stock": exact_contacts,
            "static_edges_remain_static": static_preserved,
            "dynamic_edges_remain_dynamic": dynamic_preserved,
            "dynamic_transition_ratio_within_bounds": ratio_bounded,
            "authored_contact_deltas_match_stock": contact_delta_exact,
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
