#!/usr/bin/env python3
"""Correlate the retained Dragster C000=8 finish event with decoded spatial cells.

The default event is copied from the accepted 2026-10-02 guest-frame-2903
object-activation trace. --activation-json can ingest its full original
analyzer report instead. Correlation is x/packed-word/slot exact but does
not infer the exact contacted Y cell or the collision footprint.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPATIAL = ROOT / "analysis/generated/dragster-presentation-spatial-contract.json"
EVENT_SOURCE = "analysis/generated/object-activation-runtime-boundary-2026-10-02.md"
DEFAULT_EVENT = {
    "frame": 2903,
    "player_x": 25256,
    "collision_word": 0x2020,
    "object_index": 8,
    "object_code": 0x14,
    "source": EVENT_SOURCE,
}


def surface_slot(word: int) -> int | None:
    if not word & 0x03FF:
        return None
    return ((word & 0x000F) >> 1) + ((word & 0x03F0) >> 2)


def distance_x(x: int, lo: int, hi: int) -> int:
    return max(lo - x, x - hi, 0)


def correlate(contract: dict, event: dict) -> dict:
    slot = event["object_index"]
    word = event["collision_word"]
    player_x = event["player_x"]
    if surface_slot(word) != slot:
        raise ValueError("collision word does not decode to the observed C000 index")
    if event["object_code"] != 0x14:
        raise ValueError("not a confirmed checkpoint/finish object-code event")
    cp = contract["resources"]["checkpoint_finish"]
    lo, hi = cp["c000_range"]
    if not lo <= slot <= hi:
        raise ValueError("observed C000 index is outside checkpoint resource span")
    extent_x = contract["world_contract"]["world_extent"][0]
    if not 0 <= player_x < extent_x:
        raise ValueError("observed player X is outside course world extent")
    historical_finish_x = contract["course"]["historical_finish_x_probe"]
    if not 0 <= historical_finish_x < extent_x:
        raise ValueError("historical finish-X lead outside course world extent")

    matching = []
    for sector in cp["coarse_sector_placements"]:
        for cell in sector["checkpoint_local_cells"]:
            if cell["c000_slot"] != slot or int(cell["word_hex"], 16) != word:
                continue
            x0 = sector["world_rect"][0] + cell["local_x"] * 16
            y0 = sector["world_rect"][1] + cell["local_y"] * 16
            matching.append({
                "world_rect": [x0, y0, x0 + 15, y0 + 15],
                "coarse_sector": [sector["x_sector"], sector["y_sector"]],
                "fine_record_id": sector["record_id"],
                "c000_slot": slot,
                "packed_word": f"{word:04X}",
                "finish_x_distance": distance_x(historical_finish_x, x0, x0 + 15),
                "player_x_distance": distance_x(player_x, x0, x0 + 15),
            })
    if not matching:
        raise ValueError("no ROM-derived course cell matches the observed word and C000 index")
    matching.sort(key=lambda v: (
        v["finish_x_distance"], v["player_x_distance"],
        v["world_rect"][0], v["world_rect"][1],
    ))
    best = matching[0]["finish_x_distance"]
    near = [v for v in matching if v["finish_x_distance"] == best]
    return {
        "schema_version": 1,
        "event": dict(event),
        "historical_finish_x": historical_finish_x,
        "resource_family": "0x24",
        "behavior_code": "0x14",
        "matched_packed_word": f"{word:04X}",
        "matched_c000_slot": slot,
        "all_matching_cells": matching,
        "matching_cell_count": len(matching),
        "closest_historical_finish_x_distance": best,
        "nearest_finish_x_cells": near,
        "nearest_finish_x_cell_count": len(near),
        "player_to_nearest_cell_x_distance": min(
            x["player_x_distance"] for x in near
        ),
        "limits": (
            "Packed-word/slot/world-X triangulation only. Without verified "
            "contact Y and contact footprint, this does not choose a unique "
            "16x16 cell or prove the historical finish-X is the collision plane."
        ),
    }


def event_from_activation_json(path: Path) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    row = report.get("first_progress_change")
    if not isinstance(row, dict):
        raise ValueError("activation report has no first_progress_change event")
    return {
        "frame": row["frame"],
        "player_x": row["player_x"],
        "player_y": row["player_y"],
        "collision_word": row["collision_word"],
        "object_index": row["object_index"],
        "object_code": row["object_code"],
        "source": str(path),
    }


def markdown(report: dict) -> str:
    e = report["event"]
    lines = [
        "# Dragster finish-event / ROM spatial triangulation",
        "",
        "Derived from tools/correlate_dragster_finish_spatial_event.py.",
        "",
        f"- Guest frame: {e['frame']}; player X: {e['player_x']}.",
        f"- Contact word / C000 index / behavior: {report['matched_packed_word']} "
        f"/ {report['matched_c000_slot']} / {report['behavior_code']}.",
        f"- Historical finish-X lead: {report['historical_finish_x']}.",
        f"- Exact-word/slot candidate cells: {report['matching_cell_count']}.",
        f"- Closest finish-X gap: {report['closest_historical_finish_x_distance']} world units.",
        f"- Player-X distance to nearest candidate: {report['player_to_nearest_cell_x_distance']} units.",
        "",
        "| world cell | coarse sector | packed word | distance to historical X |",
        "|---|---|---|---:|",
    ]
    for cell in report["nearest_finish_x_cells"]:
        lines.append(
            f"| {cell['world_rect']} | {cell['coarse_sector']} | "
            f"{cell['packed_word']} | {cell['finish_x_distance']} |"
        )
    lines += ["", report["limits"], ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spatial-json", type=Path, default=SPATIAL)
    ap.add_argument("--activation-json", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()

    contract = json.loads(args.spatial_json.read_text(encoding="utf-8"))
    event = (
        event_from_activation_json(args.activation_json)
        if args.activation_json else dict(DEFAULT_EVENT)
    )
    result = correlate(contract, event)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(markdown(result), encoding="utf-8")
    if not args.json_out and not args.md_out:
        print(markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
