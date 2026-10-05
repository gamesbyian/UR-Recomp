#!/usr/bin/env python3
"""Find canonical ROM call targets into the tour-confirm generation-writer neighborhood."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TARGET_BANK = 0x80
TARGET_START = 0xE680
TARGET_END = 0xE6BF


def mirror_bank(bank: int) -> int:
    return bank & 0x7F


def lorom_cpu(offset: int) -> tuple[int, int]:
    bank = 0x80 | ((offset // 0x8000) & 0x7F)
    addr = 0x8000 + (offset % 0x8000)
    return bank, addr


def lorom_offset(bank: int, addr: int) -> int:
    if addr < 0x8000:
        raise ValueError("LoROM ROM address must be >= $8000")
    return (mirror_bank(bank) * 0x8000) + (addr - 0x8000)


def scan(rom: bytes, context: int = 32) -> dict:
    calls = []
    seen_targets = set()
    for pos, opcode in enumerate(rom):
        source_bank, source_addr = lorom_cpu(pos)
        target_bank = None
        target_addr = None
        kind = None
        size = 0

        if opcode == 0x20 and pos + 2 < len(rom):
            # JSR abs stays in the current program bank.
            target_bank = source_bank
            target_addr = int.from_bytes(rom[pos + 1:pos + 3], "little")
            kind = "JSR"
            size = 3
        elif opcode == 0x22 and pos + 3 < len(rom):
            raw = int.from_bytes(rom[pos + 1:pos + 4], "little")
            target_bank = (raw >> 16) & 0xFF
            target_addr = raw & 0xFFFF
            kind = "JSL"
            size = 4
        else:
            continue

        if (
            mirror_bank(target_bank) != mirror_bank(TARGET_BANK)
            or not (TARGET_START <= target_addr <= TARGET_END)
        ):
            continue

        target_off = lorom_offset(target_bank, target_addr)
        lo = max(0, target_off - context)
        hi = min(len(rom), target_off + context)
        calls.append({
            "source_cpu": f"{source_bank:02X}:{source_addr:04X}",
            "source_offset": f"0x{pos:06X}",
            "kind": kind,
            "target_cpu": f"{TARGET_BANK:02X}:{target_addr:04X}",
            "target_offset": f"0x{target_off:06X}",
            "source_bytes": rom[pos:pos + size].hex(" "),
            "target_window_start": f"0x{lo:06X}",
            "target_window_hex": rom[lo:hi].hex(" "),
        })
        seen_targets.add(target_addr)

    return {
        "schema_version": 1,
        "purpose": "Bound callable entries into the stock tour-confirm generation-writer neighborhood.",
        "target_range": f"{TARGET_BANK:02X}:{TARGET_START:04X}-{TARGET_END:04X}",
        "writer": "80:E6BF STA.l $77:10D1",
        "call_targets": [f"{TARGET_BANK:02X}:{addr:04X}" for addr in sorted(seen_targets)],
        "calls": calls,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--context", type=int, default=32)
    args = ap.parse_args()

    report = scan(args.rom.read_bytes(), args.context)
    payload = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
