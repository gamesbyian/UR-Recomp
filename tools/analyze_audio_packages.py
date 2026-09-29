#!/usr/bin/env python3
"""Map Uniracers audio package selector tables to direct transfer callers.

This analysis is intentionally mechanical:
- parse the 50-record audio block pool and six known 64-byte selector tables;
- find exact 16-bit LDX #table followed immediately by JSL $82:82A5;
- retain nearby bytes and LoROM caller addresses for later semantic attribution;
- compute pairwise selector-table slot differences and subset relationships;
- scan for raw 16-bit table-address operands as weaker reference candidates.

Exact LDX/JSL matches are strong static evidence for direct package callers.
Raw-word references are only candidates and require control-flow/disassembly or
runtime evidence before promotion.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from tools.inspect_audio_block_pool import DEFAULT_TABLES, build_report
except ModuleNotFoundError:
    from inspect_audio_block_pool import DEFAULT_TABLES, build_report


TRANSFER_WRAPPER = bytes((0x22, 0xA5, 0x82, 0x82))


def file_to_cpu(offset: int) -> int:
    bank = offset // 0x8000
    addr = 0x8000 + (offset % 0x8000)
    return (bank << 16) | addr


def fmt_cpu(cpu: int) -> str:
    return f"{(cpu >> 16) & 0xFF:02X}:{cpu & 0xFFFF:04X}"


def scan_direct_callers(rom: bytes, table_cpus=DEFAULT_TABLES, context: int = 12) -> list[dict]:
    seeds = {cpu & 0xFFFF: cpu for cpu in table_cpus}
    rows: list[dict] = []
    # A2 ll hh = LDX #imm16 when X is 16-bit, followed immediately by
    # 22 A5 82 82 = JSL $82:82A5.
    for pos in range(0, max(0, len(rom) - 7)):
        if rom[pos] != 0xA2 or rom[pos + 3 : pos + 7] != TRANSFER_WRAPPER:
            continue
        seed = int.from_bytes(rom[pos + 1 : pos + 3], "little")
        table_cpu = seeds.get(seed)
        if table_cpu is None:
            continue
        a = max(0, pos - context)
        b = min(len(rom), pos + 7 + context)
        rows.append(
            {
                "rom_offset": pos,
                "rom_offset_hex": f"0x{pos:06X}",
                "caller_cpu": fmt_cpu(file_to_cpu(pos)),
                "table_cpu": f"0x{table_cpu:06X}",
                "table_seed": f"0x{seed:04X}",
                "pattern": "LDX #imm16 ; JSL $82:82A5",
                "context_start_hex": f"0x{a:06X}",
                "context_hex": rom[a:b].hex(" "),
            }
        )
    return rows


def scan_raw_seed_references(rom: bytes, table_cpus=DEFAULT_TABLES, context: int = 8) -> list[dict]:
    rows: list[dict] = []
    for cpu in table_cpus:
        seed = cpu & 0xFFFF
        needle = seed.to_bytes(2, "little")
        start = 0
        while True:
            pos = rom.find(needle, start)
            if pos < 0:
                break
            a = max(0, pos - context)
            b = min(len(rom), pos + 2 + context)
            rows.append(
                {
                    "rom_offset": pos,
                    "rom_offset_hex": f"0x{pos:06X}",
                    "cpu_near": fmt_cpu(file_to_cpu(pos)),
                    "table_cpu": f"0x{cpu:06X}",
                    "table_seed": f"0x{seed:04X}",
                    "context_start_hex": f"0x{a:06X}",
                    "context_hex": rom[a:b].hex(" "),
                }
            )
            start = pos + 1
    return rows


def table_relationships(table_rows: list[dict]) -> list[dict]:
    parsed = []
    for row in table_rows:
        raw = bytes.fromhex(row["bytes_hex"])
        parsed.append((row["cpu_address"], raw))

    out = []
    for i, (addr_a, a) in enumerate(parsed):
        for addr_b, b in parsed[i + 1 :]:
            diffs = [
                {
                    "slot": idx,
                    "slot_1based": idx + 1,
                    "a": f"0x{x:02X}",
                    "b": f"0x{y:02X}",
                }
                for idx, (x, y) in enumerate(zip(a, b))
                if x != y
            ]
            ids_a = {x for x in a if x != 0xFF}
            ids_b = {x for x in b if x != 0xFF}
            out.append(
                {
                    "a": addr_a,
                    "b": addr_b,
                    "different_slots": len(diffs),
                    "differences": diffs,
                    "a_only_ids": [f"0x{x:02X}" for x in sorted(ids_a - ids_b)],
                    "b_only_ids": [f"0x{x:02X}" for x in sorted(ids_b - ids_a)],
                    "a_is_subset_of_b": ids_a <= ids_b,
                    "b_is_subset_of_a": ids_b <= ids_a,
                    "same_relative_slots_for_shared_ids": all(
                        x == y or x == 0xFF or y == 0xFF for x, y in zip(a, b)
                    ),
                }
            )
    return out


def build_package_report(rom: bytes, table_cpus=DEFAULT_TABLES) -> dict:
    base = build_report(rom, table_cpus=table_cpus)
    callers = scan_direct_callers(rom, table_cpus=table_cpus)
    raw_refs = scan_raw_seed_references(rom, table_cpus=table_cpus)

    by_table = {row["cpu_address"]: [] for row in base["selector_tables"]}
    for row in callers:
        by_table[row["table_cpu"]].append(row["caller_cpu"])

    tables = []
    for row in base["selector_tables"]:
        addr = row["cpu_address"]
        tables.append(
            {
                **row,
                "direct_callers": by_table[addr],
                "direct_caller_count": len(by_table[addr]),
            }
        )

    return {
        "schema_version": 1,
        "canonical_rom_sha256": base["canonical_rom_sha256"],
        "block_pool": {
            "pool_start_cpu": base["pool_start_cpu"],
            "pool_start_file_offset": base["pool_start_file_offset"],
            "pool_end_file_offset": base["pool_end_file_offset"],
            "pool_byte_length": base["pool_byte_length"],
            "block_count": base["block_count"],
            "selector_id_union_hex": base["selector_id_union_hex"],
        },
        "selector_tables": tables,
        "direct_callers": callers,
        "raw_seed_references": raw_refs,
        "relationships": table_relationships(base["selector_tables"]),
        "method_notes": [
            "direct caller requires exact A2 ll hh 22 A5 82 82 byte sequence",
            "raw 16-bit seed references are weak candidates only",
            "table relationships compare 64 physical slots, preserving FF sentinels",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    report = build_package_report(args.rom.read_bytes())
    print(f"direct_callers={len(report['direct_callers'])}")
    for table in report["selector_tables"]:
        print(
            f"  {table['cpu_address']}: "
            f"callers={table['direct_caller_count']} ids={table['non_ff_count']}"
        )

    for rel in report["relationships"]:
        if (
            rel["a_is_subset_of_b"]
            or rel["b_is_subset_of_a"]
            or rel["different_slots"] <= 4
        ):
            print(
                f"  relation {rel['a']} vs {rel['b']}: "
                f"slots={rel['different_slots']} "
                f"a_only={rel['a_only_ids']} b_only={rel['b_only_ids']}"
            )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
