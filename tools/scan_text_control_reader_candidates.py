#!/usr/bin/env python3
"""Find candidate 65816 text/control readers from Sayans control-byte grammar.

The recovered Spanish patch exposes a small high-byte control vocabulary:
F2, F3, F8, FB, FC, FE, FF. A reader/parser routine is more likely to contain
several immediate comparisons against these values within a small code window
than an unrelated routine is.

This is a heuristic static scanner. It does not disassemble control flow or
prove semantics; it ranks candidate ROM windows for follow-up disassembly.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

try:
    from tools.inspect_audio_block_pool import file_to_cpu  # type: ignore[attr-defined]
except Exception:
    def file_to_cpu(offset: int) -> int:
        bank = offset // 0x8000
        addr = 0x8000 + (offset % 0x8000)
        return (bank << 16) | addr


CONTROL_VALUES = (0xF2, 0xF3, 0xF8, 0xFB, 0xFC, 0xFE, 0xFF)
CMP_IMMEDIATE = 0xC9


def fmt_cpu(cpu: int) -> str:
    return f"{(cpu >> 16) & 0xFF:02X}:{cpu & 0xFFFF:04X}"


def scan_cmp_sites(rom: bytes, controls=CONTROL_VALUES) -> list[dict]:
    wanted = set(controls)
    rows = []
    for pos in range(len(rom) - 1):
        if rom[pos] == CMP_IMMEDIATE and rom[pos + 1] in wanted:
            rows.append({
                "rom_offset": pos,
                "rom_offset_hex": f"0x{pos:06X}",
                "cpu": fmt_cpu(file_to_cpu(pos)),
                "value": rom[pos + 1],
                "value_hex": f"0x{rom[pos + 1]:02X}",
            })
    return rows


def cluster_sites(sites: list[dict], radius: int = 96) -> list[dict]:
    if not sites:
        return []
    clusters = []
    for i, seed in enumerate(sites):
        center = seed["rom_offset"]
        members = [
            row for row in sites
            if abs(row["rom_offset"] - center) <= radius
        ]
        values = sorted({row["value"] for row in members})
        if len(values) < 2:
            continue
        start = min(row["rom_offset"] for row in members)
        end = max(row["rom_offset"] for row in members) + 2
        clusters.append({
            "seed_offset": center,
            "seed_cpu": seed["cpu"],
            "start_offset": start,
            "start_hex": f"0x{start:06X}",
            "start_cpu": fmt_cpu(file_to_cpu(start)),
            "end_exclusive": end,
            "end_exclusive_hex": f"0x{end:06X}",
            "site_count": len(members),
            "unique_controls": [f"0x{x:02X}" for x in values],
            "unique_control_count": len(values),
            "sites": members,
        })

    # Deduplicate equivalent member sets.
    unique = {}
    for row in clusters:
        key = tuple((s["rom_offset"], s["value"]) for s in row["sites"])
        unique[key] = row

    ranked = list(unique.values())
    ranked.sort(
        key=lambda r: (
            -r["unique_control_count"],
            -r["site_count"],
            r["start_offset"],
        )
    )
    return ranked


def add_context(rom: bytes, clusters: list[dict], padding: int = 32) -> None:
    for row in clusters:
        a = max(0, row["start_offset"] - padding)
        b = min(len(rom), row["end_exclusive"] + padding)
        row["context_start_hex"] = f"0x{a:06X}"
        row["context_start_cpu"] = fmt_cpu(file_to_cpu(a))
        row["context_hex"] = rom[a:b].hex(" ")


def analyze(rom: bytes, radius: int = 96) -> dict:
    sites = scan_cmp_sites(rom)
    clusters = cluster_sites(sites, radius=radius)
    add_context(rom, clusters)
    by_value = defaultdict(int)
    for row in sites:
        by_value[row["value_hex"]] += 1
    return {
        "schema_version": 1,
        "control_values": [f"0x{x:02X}" for x in CONTROL_VALUES],
        "cmp_site_count": len(sites),
        "cmp_sites_by_value": dict(sorted(by_value.items())),
        "cluster_radius": radius,
        "clusters": clusters,
        "interpretation_guardrails": [
            "CMP #control clusters are heuristic reader candidates only",
            "65816 accumulator width is not reconstructed by this byte scan",
            "candidate windows require real disassembly/control-flow validation",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--radius", type=int, default=96)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = analyze(args.rom.read_bytes(), radius=args.radius)
    print(f"cmp_sites={report['cmp_site_count']} clusters={len(report['clusters'])}")
    for row in report["clusters"][:20]:
        print(
            f"{row['start_cpu']}..{fmt_cpu(file_to_cpu(row['end_exclusive']-1))} "
            f"controls={','.join(row['unique_controls'])} sites={row['site_count']}"
        )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
