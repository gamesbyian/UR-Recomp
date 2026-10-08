#!/usr/bin/env python3
"""Structurally compare the seven changed USA/Europe retail course payloads."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from analyze_course_resource_lists import parse_course_resource_list
from analyze_rnc_streams import find_streams
from rnc_method1 import unpack_method1

USA = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
EUROPE = ROOT / "reference/roms/retail/Unirally_Europe.sfc"
COURSE_CORPUS = ROOT / "analysis/data/course-corpus.json"

HEADER_END = 0x000F
COARSE_END = 0x800F
FINE_START = 0x800F


def diff_stats(a: bytes, b: bytes) -> dict:
    common = min(len(a), len(b))
    changed = sum(x != y for x, y in zip(a[:common], b[:common]))
    prefix = 0
    while prefix < common and a[prefix] == b[prefix]:
        prefix += 1
    suffix = 0
    while (
        suffix < common - prefix
        and a[len(a) - 1 - suffix] == b[len(b) - 1 - suffix]
    ):
        suffix += 1
    return {
        "usa_length": len(a),
        "europe_length": len(b),
        "length_delta": len(b) - len(a),
        "common_length": common,
        "changed_bytes_in_common": changed,
        "identical": a == b,
        "identical_prefix": prefix,
        "identical_suffix": suffix,
        "usa_sha256": hashlib.sha256(a).hexdigest(),
        "europe_sha256": hashlib.sha256(b).hexdigest(),
    }


def decoded_streams(path: Path) -> list[bytes]:
    rom = path.read_bytes()
    return [unpack_method1(packed) for _off, packed, _header in find_streams(rom)]


def regions(decoded: bytes, parsed: dict) -> dict[str, bytes]:
    """Partition a validated course payload without silently clipping bad bounds.

    The 0x8000-byte coarse table and 32-byte fine records are established
    materialization boundaries. Comparing clipped/shifted regions can falsely
    attribute a malformed course to a legitimate regional content change.
    """
    cursor = parsed["resource_cursor_initial"]
    terminator = parsed["resource_terminator_offset"]
    if len(decoded) < FINE_START:
        raise ValueError("course payload truncated before end of coarse table")
    if cursor < FINE_START or cursor > len(decoded):
        raise ValueError("resource cursor outside course fine-record boundary")
    if (cursor - FINE_START) % 32:
        raise ValueError("fine-record region is not 32-byte aligned")
    if not cursor <= terminator < len(decoded):
        raise ValueError("resource terminator outside course resource list")
    if decoded[terminator] != 0xFF:
        raise ValueError("course resource terminator is not FF")
    return {
        "header": decoded[:HEADER_END],
        "coarse_table": decoded[HEADER_END:COARSE_END],
        "fine_record_region": decoded[FINE_START:cursor],
        "resource_list": decoded[cursor:terminator + 1],
        "post_resource_list": decoded[terminator + 1:],
    }



def _surface_slot(word: int) -> int | None:
    """Return only the already-proven low-ten-bit C000 selector."""
    if not (word & 0x03FF):
        return None
    return ((word & 0x000F) >> 1) + ((word & 0x03F0) >> 2)


def effective_surface_delta(
    usa: bytes, europe: bytes, usa_parsed: dict, europe_parsed: dict
) -> dict:
    """Compare *placed* packed surface words, not fine-record byte offsets.

    Coarse entries are 16,384 u16 references to 32-byte/16-cell fine
    records. Record identities can change without changing a single world
    cell, and conversely one reused record can change many placements.
    This reports packed-word/selector equality only. It never claims a
    changed word necessarily modifies collision or checkpoint behavior.
    """
    u = regions(usa, usa_parsed)
    e = regions(europe, europe_parsed)
    dims_u = usa_parsed["layout_dims"]
    dims_e = europe_parsed["layout_dims"]
    if dims_u != dims_e:
        return {
            "comparable": False,
            "reason": "regional course dimensions differ",
            "usa_dims": dims_u,
            "europe_dims": dims_e,
        }
    cols, rows = dims_u[0] * 4, dims_u[1] * 4
    if cols * rows != 16384:
        raise ValueError("course dimensions do not define 16384 coarse sectors")

    def words(data: bytes) -> list[int]:
        if len(data) % 2:
            raise ValueError("unaligned u16 course table")
        return [data[i] | (data[i + 1] << 8) for i in range(0, len(data), 2)]

    uc = words(u["coarse_table"])
    ec = words(e["coarse_table"])
    uf = words(u["fine_record_region"])
    ef = words(e["fine_record_region"])
    if len(uc) != 16384 or len(ec) != 16384:
        raise ValueError("coarse sector table must contain 16384 entries")
    un, en = len(uf) // 16, len(ef) // 16
    if any(record >= un for record in uc) or any(record >= en for record in ec):
        raise ValueError("coarse sector points outside its fine-record table")

    # Memoize paired records. Repetition is meaningful in world-space
    # counts, but need not repeatedly decode the same 16 cell words.
    compared: dict[tuple[int, int], list[tuple[int, int, int]]] = {}
    changed_sectors = changed_cells = selector_changes = control_changes = 0
    raw_reference_changes = 0
    witnesses: list[dict] = []
    bounds: list[int] | None = None
    for index, (urid, erid) in enumerate(zip(uc, ec)):
        if urid != erid:
            raw_reference_changes += 1
        key = (urid, erid)
        if key not in compared:
            differences = []
            for cell in range(16):
                uw, ew = uf[urid * 16 + cell], ef[erid * 16 + cell]
                if uw != ew:
                    differences.append((cell, uw, ew))
            compared[key] = differences
        differences = compared[key]
        if not differences:
            continue
        changed_sectors += 1
        sx, sy = index % cols, index // cols
        changed_cells += len(differences)
        for cell, uw, ew in differences:
            if _surface_slot(uw) != _surface_slot(ew):
                selector_changes += 1
            if (uw & 0xFC00) != (ew & 0xFC00):
                control_changes += 1
            x, y = sx * 64 + (cell % 4) * 16, sy * 64 + (cell // 4) * 16
            if bounds is None:
                bounds = [x, y, x + 15, y + 15]
            else:
                bounds = [
                    min(bounds[0], x), min(bounds[1], y),
                    max(bounds[2], x + 15), max(bounds[3], y + 15),
                ]
            if len(witnesses) < 12:
                witnesses.append({
                    "world_cell_origin": [x, y],
                    "coarse_sector": [sx, sy],
                    "fine_record_id": {"usa": urid, "europe": erid},
                    "packed_word": {"usa": f"{uw:04X}", "europe": f"{ew:04X}"},
                    "c000_slot": {
                        "usa": _surface_slot(uw), "europe": _surface_slot(ew)
                    },
                })
    return {
        "comparable": True,
        "coarse_grid": [cols, rows],
        "world_extent": [cols * 64, rows * 64],
        "fine_record_counts": {"usa": un, "europe": en},
        "raw_coarse_reference_id_changes": raw_reference_changes,
        "changed_world_sectors": changed_sectors,
        "changed_world_cells": changed_cells,
        "total_world_cells": 16384 * 16,
        "changed_c000_selectors": selector_changes,
        "changed_unclassified_upper_word_bits": control_changes,
        "changed_world_cell_bounds": bounds,
        "first_12_changed_cells": witnesses,
    }


def build_report(usa_path: Path = USA, europe_path: Path = EUROPE) -> dict:
    usa_streams = decoded_streams(usa_path)
    eur_streams = decoded_streams(europe_path)
    if len(usa_streams) != 45 or len(eur_streams) != 45:
        raise ValueError(
            f"expected 45 decoded streams each, got "
            f"{len(usa_streams)} and {len(eur_streams)}"
        )

    corpus = json.loads(COURSE_CORPUS.read_text(encoding="utf-8"))
    by_stream = {
        int(row["stream_index"]): row for row in corpus["courses"]
    }

    rows = []
    for idx, (usa, eur) in enumerate(zip(usa_streams, eur_streams), 1):
        if usa == eur:
            continue
        u = parse_course_resource_list(usa)
        e = parse_course_resource_list(eur)
        u_regions = regions(usa, u)
        e_regions = regions(eur, e)
        region_diffs = {
            name: diff_stats(u_regions[name], e_regions[name])
            for name in u_regions
        }
        changed_regions = [
            name for name, stats in region_diffs.items() if not stats["identical"]
        ]
        course = by_stream[idx]
        rows.append(
            {
                "stream_index": idx,
                "course_id": course["id"],
                "course_name": course["name"],
                "tour": course["tour"],
                "track_kind": course["track_kind"],
                "decoded": diff_stats(usa, eur),
                "header_fields": {
                    "usa": {
                        "stunt_time_or_mode": u["stunt_time_or_mode"],
                        "spawn_or_landmark_a": u["spawn_or_landmark_a"],
                        "spawn_or_landmark_b": u["spawn_or_landmark_b"],
                        "layout_dims": u["layout_dims"],
                        "resource_cursor": u["resource_cursor_initial"],
                    },
                    "europe": {
                        "stunt_time_or_mode": e["stunt_time_or_mode"],
                        "spawn_or_landmark_a": e["spawn_or_landmark_a"],
                        "spawn_or_landmark_b": e["spawn_or_landmark_b"],
                        "layout_dims": e["layout_dims"],
                        "resource_cursor": e["resource_cursor_initial"],
                    },
                },
                "resource_ids": {
                    "usa": u["resource_ids"],
                    "europe": e["resource_ids"],
                },
                "changed_regions": changed_regions,
                "effective_surface": effective_surface_delta(usa, eur, u, e),
                "regions": region_diffs,
            }
        )

    return {
        "schema_version": 2,
        "purpose": (
            "Mechanical decoded-region comparison for the retail course payloads "
            "that differ between USA and Europe."
        ),
        "classification_guardrail": (
            "Region membership narrows the investigation but does not itself "
            "classify a change as visual, collision/topology, spawn, or timing. "
            "Effective surface comparison measures packed words and known C000 "
            "selectors after coarse-to-fine placement; these differences are "
            "not alone proof of changed physical track behavior."
        ),
        "changed_stream_count": len(rows),
        "changed_stream_indices": [row["stream_index"] for row in rows],
        "courses": rows,
    }


def markdown(report: dict) -> str:
    lines = [
        "# Regional Retail Course Payload Structure",
        "",
        "Generated by tools/compare_regional_course_payloads.py.",
        "",
        report["classification_guardrail"],
        "",
        "| # | Course | decoded delta | changed structural regions | resources |",
        "|---:|---|---:|---|---|",
    ]
    for row in report["courses"]:
        resources = (
            "same"
            if row["resource_ids"]["usa"] == row["resource_ids"]["europe"]
            else f"{row['resource_ids']['usa']} -> {row['resource_ids']['europe']}"
        )
        lines.append(
            f"| {row['stream_index']} | {row['course_name']} | "
            f"{row['decoded']['length_delta']:+d} | "
            f"{', '.join(row['changed_regions'])} | {resources} |"
        )

    lines += [
        "",
        "## Placed packed-surface comparison",
        "",
        "World-cell counts compare the actual coarse-sector -> fine-record",
        "lookup for each 16x16 cell. These are packed-word/known C000",
        "selector differences, **not** automatically collision/finish changes.",
        "Raw coarse record-ID edits can be nonzero while all placed",
        "world-cell words remain identical.",
        "",
        "| # | Course | coarse ID differences | changed sectors | changed world cells | changed C000 selectors | upper-word differences |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in report["courses"]:
        spatial = row["effective_surface"]
        if not spatial["comparable"]:
            lines.append(
                f'| {row["stream_index"]} | {row["course_name"]} | '
                f'{spatial["reason"]} | | | | |'
            )
            continue
        lines.append(
            f'| {row["stream_index"]} | {row["course_name"]} | '
            f'{spatial["raw_coarse_reference_id_changes"]} | '
            f'{spatial["changed_world_sectors"]} | '
            f'{spatial["changed_world_cells"]} | '
            f'{spatial["changed_c000_selectors"]} | '
            f'{spatial["changed_unclassified_upper_word_bits"]} |'
        )

    lines += ["", "## Region detail", ""]
    for row in report["courses"]:
        lines += [f"### #{row['stream_index']} {row['course_name']}", ""]
        for name, stats in row["regions"].items():
            lines.append(
                f"- {name}: identical={str(stats['identical']).lower()}, "
                f"USA={stats['usa_length']}, Europe={stats['europe_length']}, "
                f"delta={stats['length_delta']:+d}, "
                f"changed-common={stats['changed_bytes_in_common']}"
            )
        if row["header_fields"]["usa"] != row["header_fields"]["europe"]:
            lines.append(
                "- header fields: "
                + json.dumps(row["header_fields"], separators=(",", ":"))
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--usa-rom", type=Path, default=USA)
    ap.add_argument("--europe-rom", type=Path, default=EUROPE)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()

    report = build_report(args.usa_rom, args.europe_rom)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(markdown(report), encoding="utf-8")
    if not args.json_out and not args.md_out:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
