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
    cursor = parsed["resource_cursor_initial"]
    terminator = parsed["resource_terminator_offset"]
    coarse_end = min(COARSE_END, len(decoded))
    fine_start = min(FINE_START, len(decoded))
    fine_end = min(cursor, len(decoded))
    post_list_start = min(terminator + 1, len(decoded))
    return {
        "header": decoded[:min(HEADER_END, len(decoded))],
        "coarse_table": decoded[min(HEADER_END, len(decoded)):coarse_end],
        "fine_record_region": decoded[fine_start:fine_end],
        "resource_list": decoded[min(cursor, len(decoded)):post_list_start],
        "post_resource_list": decoded[post_list_start:],
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
                "regions": region_diffs,
            }
        )

    return {
        "schema_version": 1,
        "purpose": (
            "Mechanical decoded-region comparison for the retail course payloads "
            "that differ between USA and Europe."
        ),
        "classification_guardrail": (
            "Region membership narrows the investigation but does not itself "
            "classify a change as visual, collision/topology, spawn, or timing."
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
