#!/usr/bin/env python3
"""Bound direct calls from the stock tour-result window to known generation consumers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

RESULT_BANK = 0x83
RESULT_START = 0x8700
RESULT_END = 0x8840

KNOWN_GENERATION_CONSUMERS = {
    (0x80, 0xB315): "ordinary opponent generation",
    (0x80, 0xBC15): "medal/snapshot reconciliation",
    (0x80, 0xBC79): "medal/snapshot reconciliation",
    (0x80, 0xE8F0): "frontend generation label",
    (0x80, 0xEAA6): "generation reconciliation",
    (0x80, 0xEAB9): "generation reconciliation",
}


def mirror_bank(bank: int) -> int:
    return bank & 0x7F


def lorom_offset(bank: int, addr: int) -> int:
    return mirror_bank(bank) * 0x8000 + (addr - 0x8000)


def cpu_addr(offset: int) -> tuple[int, int]:
    return 0x80 | ((offset // 0x8000) & 0x7F), 0x8000 + (offset % 0x8000)


def scan(rom: bytes, context: int = 12) -> dict:
    lo = lorom_offset(RESULT_BANK, RESULT_START)
    hi = lorom_offset(RESULT_BANK, RESULT_END)
    calls = []
    generation_calls = []
    raw_10d1 = []

    target_bytes = bytes((0xD1, 0x10, 0x77))
    pos = lo
    while True:
        p = rom.find(target_bytes, pos, hi)
        if p < 0:
            break
        bank, addr = cpu_addr(max(lo, p - 1))
        raw_10d1.append({
            "cpu_address": f"{bank:02X}:{addr:04X}",
            "opcode": f"0x{rom[p - 1]:02X}" if p > lo else None,
        })
        pos = p + 1

    for pos in range(lo, min(hi, len(rom))):
        op = rom[pos]
        source_bank, source_addr = cpu_addr(pos)
        target_bank = None
        target_addr = None
        kind = None
        size = 0

        if op == 0x20 and pos + 2 < hi:
            target_bank = source_bank
            target_addr = int.from_bytes(rom[pos + 1:pos + 3], "little")
            kind = "JSR"
            size = 3
        elif op == 0x22 and pos + 3 < hi:
            raw = int.from_bytes(rom[pos + 1:pos + 4], "little")
            target_bank = (raw >> 16) & 0xFF
            target_addr = raw & 0xFFFF
            kind = "JSL"
            size = 4
        else:
            continue

        if target_addr is None or target_addr < 0x8000:
            continue
        key = (0x80 | mirror_bank(target_bank), target_addr)
        entry = {
            "source_cpu": f"{source_bank:02X}:{source_addr:04X}",
            "kind": kind,
            "target_cpu": f"{key[0]:02X}:{key[1]:04X}",
            "known_generation_role": KNOWN_GENERATION_CONSUMERS.get(key),
            "source_bytes": rom[pos:pos + size].hex(" "),
        }
        calls.append(entry)
        if entry["known_generation_role"]:
            generation_calls.append(entry)

    return {
        "schema_version": 1,
        "purpose": "Bound whether stock qualifying-tour result logic directly invokes known generation consumers.",
        "result_window": f"{RESULT_BANK:02X}:{RESULT_START:04X}-{RESULT_END:04X}",
        "known_generation_consumers": [
            f"{b:02X}:{a:04X} {role}"
            for (b, a), role in KNOWN_GENERATION_CONSUMERS.items()
        ],
        "direct_10d1_operands_in_result_window": raw_10d1,
        "direct_calls_to_known_generation_consumers": generation_calls,
        "all_candidate_direct_calls": calls,
        "window_hex": rom[lo:hi].hex(" "),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    report = scan(args.rom.read_bytes())
    payload = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
