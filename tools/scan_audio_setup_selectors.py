#!/usr/bin/env python3
"""Scan Uniracers audio setup selectors around JSL $82:807E.

The known package callers have a recurring form:
    LDX #selector
    JSL $82:807E
    LDX #table
    JSL $82:82A5

This tool finds every exact setup call and every exact setup+package pair. It
does not assign semantics to selector values; that requires independent runtime
or asset evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from tools.analyze_audio_packages import file_to_cpu, fmt_cpu
    from tools.inspect_audio_block_pool import DEFAULT_TABLES
except ModuleNotFoundError:
    from analyze_audio_packages import file_to_cpu, fmt_cpu
    from inspect_audio_block_pool import DEFAULT_TABLES

SETUP_WRAPPER = bytes((0x22, 0x7E, 0x80, 0x82))
TRANSFER_WRAPPER = bytes((0x22, 0xA5, 0x82, 0x82))


def scan_setup_calls(rom: bytes, context: int = 10) -> list[dict]:
    rows = []
    for pos in range(max(0, len(rom) - 7)):
        if rom[pos] != 0xA2 or rom[pos + 3:pos + 7] != SETUP_WRAPPER:
            continue
        selector = int.from_bytes(rom[pos + 1:pos + 3], "little")
        a = max(0, pos - context)
        b = min(len(rom), pos + 7 + context)
        rows.append({
            "rom_offset": pos,
            "rom_offset_hex": f"0x{pos:06X}",
            "caller_cpu": fmt_cpu(file_to_cpu(pos)),
            "selector": selector,
            "selector_hex": f"0x{selector:04X}",
            "context_start_hex": f"0x{a:06X}",
            "context_hex": rom[a:b].hex(" "),
        })
    return rows


def scan_setup_package_pairs(rom: bytes, table_cpus=DEFAULT_TABLES) -> list[dict]:
    tables = {cpu & 0xFFFF: cpu for cpu in table_cpus}
    rows = []
    # 7-byte setup call immediately followed by 7-byte package call.
    for pos in range(max(0, len(rom) - 14)):
        if rom[pos] != 0xA2 or rom[pos + 3:pos + 7] != SETUP_WRAPPER:
            continue
        if rom[pos + 7] != 0xA2 or rom[pos + 10:pos + 14] != TRANSFER_WRAPPER:
            continue
        selector = int.from_bytes(rom[pos + 1:pos + 3], "little")
        seed = int.from_bytes(rom[pos + 8:pos + 10], "little")
        table = tables.get(seed)
        if table is None:
            continue
        rows.append({
            "rom_offset": pos,
            "rom_offset_hex": f"0x{pos:06X}",
            "caller_cpu": fmt_cpu(file_to_cpu(pos)),
            "selector": selector,
            "selector_hex": f"0x{selector:04X}",
            "table_cpu": f"0x{table:06X}",
            "table_seed_hex": f"0x{seed:04X}",
        })
    return rows


def build_report(rom: bytes) -> dict:
    calls = scan_setup_calls(rom)
    pairs = scan_setup_package_pairs(rom)
    values = sorted({r["selector"] for r in calls})
    paired_values = sorted({r["selector"] for r in pairs})
    interesting = list(range(0x38, 0x43))
    return {
        "schema_version": 1,
        "setup_calls": calls,
        "setup_package_pairs": pairs,
        "selector_values": values,
        "selector_values_hex": [f"0x{x:04X}" for x in values],
        "paired_selector_values": paired_values,
        "paired_selector_values_hex": [f"0x{x:04X}" for x in paired_values],
        "selector_38_42_presence": {
            f"0x{x:02X}": {
                "setup_call": x in values,
                "paired_with_known_table": x in paired_values,
            }
            for x in interesting
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = build_report(args.rom.read_bytes())
    for row in report["setup_package_pairs"]:
        print(row["caller_cpu"], row["selector_hex"], row["table_cpu"])
    print("38..42", json.dumps(report["selector_38_42_presence"], sort_keys=True))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
