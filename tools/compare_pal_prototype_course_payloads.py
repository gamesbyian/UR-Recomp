#!/usr/bin/env python3
"""Compare all PAL prototype and PAL retail course payloads in placed world space.

A changed fine-record byte is not necessarily a changed course cell, and a
reordered fine-record table need not change the placed world at all. This
reuses the ROM-validated coarse/fine parser from the USA/Europe comparator,
without borrowing its USA/Europe interpretation or presumed behavior labels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from analyze_course_resource_lists import parse_course_resource_list
from compare_regional_course_payloads import (
    COURSE_CORPUS, decoded_streams, effective_surface_delta,
    regions, compare_header_world_landmarks,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc"
PAL_RETAIL = ROOT / "reference/roms/retail/Unirally_Europe.sfc"


def _named_pair_fields(value):
    """Convert inherited USA/Europe comparator labels to actual build roles."""
    if isinstance(value, list):
        return [_named_pair_fields(x) for x in value]
    if isinstance(value, dict):
        renamed = {}
        for key, item in value.items():
            key = str(key).replace("usa", "prototype").replace("europe", "retail")
            renamed[key] = _named_pair_fields(item)
        return renamed
    return value


def summarize_pair(prototype: bytes, retail: bytes, stream_index: int,
                   course_name: str) -> dict:
    proto = parse_course_resource_list(prototype)
    eur = parse_course_resource_list(retail)
    rp = regions(prototype, proto)
    rr = regions(retail, eur)
    changed_parts = [name for name in rp if rp[name] != rr[name]]
    # Only the coarse+fine lookup establishes placed packed-word identity.
    placed = _named_pair_fields(
        effective_surface_delta(prototype, retail, proto, eur)
    ) if prototype != retail else {
        "comparable": True,
        "changed_world_sectors": 0,
        "changed_world_cells": 0,
        "changed_c000_selectors": 0,
        "changed_unclassified_upper_word_bits": 0,
        "raw_coarse_reference_id_changes": 0,
        "first_12_changed_cells": [],
    }
    landmarks = _named_pair_fields(
        compare_header_world_landmarks(proto, eur)
    )
    result = {
        "stream_index": stream_index,
        "course_name": course_name,
        "decoded_identical": prototype == retail,
        "decoded_sizes": {"prototype": len(prototype), "retail": len(retail)},
        "sha256": {
            "prototype": hashlib.sha256(prototype).hexdigest(),
            "retail": hashlib.sha256(retail).hexdigest(),
        },
        "changed_regions": changed_parts,
        "header": {
            "prototype": {
                "stunt_time_or_mode": proto["stunt_time_or_mode"],
                "layout_dims": proto["layout_dims"],
                "resource_cursor": proto["resource_cursor_initial"],
            },
            "retail": {
                "stunt_time_or_mode": eur["stunt_time_or_mode"],
                "layout_dims": eur["layout_dims"],
                "resource_cursor": eur["resource_cursor_initial"],
            },
        },
        "candidate_world_landmarks": landmarks,
        "resource_ids": {
            "prototype": proto["resource_ids"],
            "retail": eur["resource_ids"],
        },
        "resource_list_identical": rp["resource_list"] == rr["resource_list"],
        "placed_surface": placed,
    }
    return result


def build_report(prototype_rom: Path = PROTOTYPE,
                 retail_rom: Path = PAL_RETAIL) -> dict:
    prototype = decoded_streams(prototype_rom)
    retail = decoded_streams(retail_rom)
    if len(prototype) != 45 or len(retail) != 45:
        raise ValueError(
            "expected 45 decoded course streams in both PAL builds; "
            f"found {len(prototype)} and {len(retail)}"
        )
    corpus = json.loads(COURSE_CORPUS.read_text(encoding="utf-8"))
    by_index = {int(row["stream_index"]): row for row in corpus["courses"]}
    if set(by_index) != set(range(1, 46)):
        raise ValueError("canonical course corpus must identify all 45 stream indices")
    rows = [
        summarize_pair(a, b, i, by_index[i]["name"])
        for i, (a, b) in enumerate(zip(prototype, retail), 1)
    ]
    changed = [r for r in rows if not r["decoded_identical"]]
    resource_changed = [r["stream_index"] for r in changed
                        if not r["resource_list_identical"]]
    world_changed = [r["stream_index"] for r in changed
                     if r["placed_surface"]["comparable"]
                     and r["placed_surface"]["changed_world_cells"] > 0]
    return {
        "schema_version": 1,
        "builds": {
            "baseline": "pal-prototype-1994-11-29",
            "target": "europe-retail",
        },
        "course_count": 45,
        "changed_stream_indices": [r["stream_index"] for r in changed],
        "changed_stream_count": len(changed),
        "resource_list_changed_stream_indices": resource_changed,
        "placed_packed_word_changed_stream_indices": world_changed,
        "classification_guardrail": (
            "ROM-decoded cell geometry, known C000 selector identity, and "
            "unclassified packed-word bits are reported separately. No "
            "checkpoint, collision, race-selection, or gameplay behavior "
            "difference is asserted without a matching runtime trace. "
            "Coordinate-pair labels do not establish P1/P2 spawn ownership."
        ),
        "courses": rows,
    }


def markdown(report: dict) -> str:
    lines = [
        "# PAL prototype versus Europe retail: placed course content",
        "",
        "Generated by tools/compare_pal_prototype_course_payloads.py.",
        "",
        report["classification_guardrail"],
        "",
        f"Decoded courses: **{report['course_count']}**; changed streams: "
        f"**{report['changed_stream_count']}**.",
        "",
        "| # | Course | Decoded | Region changes | Resources | Placed cells | Slot changes |",
        "|---:|---|---|---|---|---:|---:|",
    ]
    for row in report["courses"]:
        surf = row["placed_surface"]
        d = "identical" if row["decoded_identical"] else "changed"
        res = "same" if row["resource_list_identical"] else "changed"
        if surf["comparable"]:
            world = str(surf["changed_world_cells"])
            slots = str(surf["changed_c000_selectors"])
        else:
            world = slots = "dimensions differ"
        lines.append(
            f"| {row['stream_index']} | {row['course_name']} | {d} | "
            f"{', '.join(row['changed_regions']) or 'none'} | {res} | "
            f"{world} | {slots} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prototype-rom", type=Path, default=PROTOTYPE)
    ap.add_argument("--retail-rom", type=Path, default=PAL_RETAIL)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()
    report = build_report(args.prototype_rom, args.retail_rom)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(markdown(report), encoding="utf-8")
    if not args.json_out and not args.md_out:
        print(markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
