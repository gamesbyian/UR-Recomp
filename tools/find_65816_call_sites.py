#!/usr/bin/env python3
"""Find candidate 65C816 JSR/JSL call sites for a LoROM CPU address.

This is a mechanical byte-pattern scanner, not a control-flow proof. JSR hits are
bank-local and JSL hits accept the low/high LoROM bank mirrors. Unaligned bytes
can still produce false positives, so every result remains a candidate until
bounded disassembly or runtime evidence confirms it.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CPU_RE = re.compile(r"^(?:0x)?([0-9a-fA-F]{1,2})[:]?([0-9a-fA-F]{4})$")


def parse_cpu_address(raw: str) -> tuple[int, int]:
    text = raw.strip()
    m = CPU_RE.fullmatch(text)
    if not m:
        value = int(text, 0)
        if not 0 <= value <= 0xFFFFFF:
            raise ValueError("target must fit in 24-bit CPU address space")
        return (value >> 16) & 0xFF, value & 0xFFFF
    return int(m.group(1), 16), int(m.group(2), 16)


def lorom_cpu_address(offset: int) -> tuple[int, int]:
    bank = (offset // 0x8000) & 0x7F
    addr = 0x8000 + (offset % 0x8000)
    return bank, addr


def mirror_bank(bank: int) -> int:
    return bank & 0x7F


def scan(data: bytes, target_bank: int, target_addr: int, context: int = 12) -> list[dict]:
    if target_addr < 0x8000:
        raise ValueError("scanner currently targets LoROM ROM addresses >= $8000")
    target_mirror = mirror_bank(target_bank)
    found: list[dict] = []

    for pos, opcode in enumerate(data):
        source_bank, source_addr = lorom_cpu_address(pos)
        kind = None
        operand = None
        operand_bank = None
        size = None

        if opcode == 0x20 and pos + 3 <= len(data):  # JSR abs
            operand = int.from_bytes(data[pos + 1 : pos + 3], "little")
            if source_bank != target_mirror or operand != target_addr:
                continue
            kind = "JSR"
            size = 3
        elif opcode == 0x22 and pos + 4 <= len(data):  # JSL long
            raw = int.from_bytes(data[pos + 1 : pos + 4], "little")
            operand = raw & 0xFFFF
            operand_bank = (raw >> 16) & 0xFF
            if operand != target_addr or mirror_bank(operand_bank) != target_mirror:
                continue
            kind = "JSL"
            size = 4
        else:
            continue

        a = max(0, pos - context)
        b = min(len(data), pos + size + context)
        found.append(
            {
                "rom_offset": pos,
                "rom_offset_hex": f"0x{pos:06X}",
                "source_cpu": f"{source_bank:02X}:{source_addr:04X}",
                "opcode": f"0x{opcode:02X}",
                "kind": kind,
                "target_cpu": f"{target_bank:02X}:{target_addr:04X}",
                "encoded_target_bank": (
                    f"0x{operand_bank:02X}" if operand_bank is not None else None
                ),
                "context_start_hex": f"0x{a:06X}",
                "context_hex": data[a:b].hex(" "),
            }
        )
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("target", help="LoROM CPU address, e.g. 02:8298 or 0x028298")
    ap.add_argument("--context", type=int, default=12)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    bank, addr = parse_cpu_address(args.target)
    data = args.rom.read_bytes()
    hits = scan(data, bank, addr, args.context)
    report = {
        "schema_version": 1,
        "rom": str(args.rom),
        "target_cpu": f"{bank:02X}:{addr:04X}",
        "method": "unaligned JSR/JSL operand candidate scan; results require control-flow or runtime confirmation",
        "hits": hits,
    }

    print(f"{report['target_cpu']}: {len(hits)} call-site candidate(s)")
    for hit in hits:
        extra = (
            f" encoded_bank={hit['encoded_target_bank']}"
            if hit["encoded_target_bank"] is not None
            else ""
        )
        print(
            f"  {hit['rom_offset_hex']} ({hit['source_cpu']}) "
            f"{hit['kind']} -> {hit['target_cpu']}{extra}"
        )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
