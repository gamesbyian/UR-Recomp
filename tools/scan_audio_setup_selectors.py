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



def scan_all_setup_wrapper_calls(rom: bytes, context: int = 8) -> list[dict]:
    """Find every direct JSL $82:807E regardless of how X is prepared."""
    rows = []
    needle = SETUP_WRAPPER
    start = 0
    while True:
        pos = rom.find(needle, start)
        if pos < 0:
            break
        call_pos = pos
        a = max(0, call_pos - context)
        b = min(len(rom), call_pos + 4 + context)
        immediate = None
        if call_pos >= 3 and rom[call_pos - 3] == 0xA2:
            immediate = int.from_bytes(rom[call_pos - 2:call_pos], "little")
        rows.append({
            "rom_offset": call_pos,
            "rom_offset_hex": f"0x{call_pos:06X}",
            "caller_cpu": fmt_cpu(file_to_cpu(call_pos)),
            "preceding_ldx_immediate": immediate,
            "preceding_ldx_immediate_hex": (
                f"0x{immediate:04X}" if immediate is not None else None
            ),
            "context_start_hex": f"0x{a:06X}",
            "context_hex": rom[a:b].hex(" "),
        })
        start = pos + 1
    return rows


def scan_immediate_ldx_values(rom: bytes, values=(0x3B, 0x3D), context: int = 8) -> list[dict]:
    """Find every raw LDX #imm16 byte pattern for targeted values."""
    rows = []
    wanted = set(values)
    for pos in range(max(0, len(rom) - 3)):
        if rom[pos] != 0xA2:
            continue
        value = int.from_bytes(rom[pos + 1:pos + 3], "little")
        if value not in wanted:
            continue
        a = max(0, pos - context)
        b = min(len(rom), pos + 3 + context)
        rows.append({
            "rom_offset": pos,
            "rom_offset_hex": f"0x{pos:06X}",
            "cpu_near": fmt_cpu(file_to_cpu(pos)),
            "value": value,
            "value_hex": f"0x{value:04X}",
            "context_start_hex": f"0x{a:06X}",
            "context_hex": rom[a:b].hex(" "),
        })
    return rows


def scan_inner_upload_entries(rom: bytes, context: int = 8) -> list[dict]:
    """Find direct calls to the inner $02:8082 upload body."""
    rows = []
    jsr = bytes((0x20, 0x82, 0x80))
    jsl = bytes((0x22, 0x82, 0x80, 0x82))
    for pos in range(len(rom)):
        cpu = file_to_cpu(pos)
        kind = None
        width = 0
        if ((cpu >> 16) & 0xFF) == 0x02 and rom[pos:pos + 3] == jsr:
            kind = "JSR_8082_bank02"
            width = 3
        elif rom[pos:pos + 4] == jsl:
            kind = "JSL_828082"
            width = 4
        if kind is None:
            continue
        a = max(0, pos - context)
        b = min(len(rom), pos + width + context)
        rows.append({
            "kind": kind,
            "rom_offset": pos,
            "rom_offset_hex": f"0x{pos:06X}",
            "caller_cpu": fmt_cpu(cpu),
            "context_start_hex": f"0x{a:06X}",
            "context_hex": rom[a:b].hex(" "),
        })
    return rows

def build_report(rom: bytes) -> dict:
    calls = scan_setup_calls(rom)
    pairs = scan_setup_package_pairs(rom)
    wrapper_calls = scan_all_setup_wrapper_calls(rom)
    targeted_ldx = scan_immediate_ldx_values(rom)
    inner_entries = scan_inner_upload_entries(rom)
    values = sorted({r["selector"] for r in calls})
    paired_values = sorted({r["selector"] for r in pairs})
    interesting = list(range(0x38, 0x43))
    return {
        "schema_version": 1,
        "setup_calls": calls,
        "setup_package_pairs": pairs,
        "all_setup_wrapper_calls": wrapper_calls,
        "targeted_immediate_ldx": targeted_ldx,
        "inner_upload_entries": inner_entries,
        "unbound_setup_wrapper_calls": [r for r in wrapper_calls if r["preceding_ldx_immediate"] is None],
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
