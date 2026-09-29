#!/usr/bin/env python3
"""Find candidate 65C816 instructions that can write selected WRAM offsets.

This is deliberately a candidate generator, not a disassembler. It scans ROM
bytes for absolute/long store and read-modify-write encodings whose operands
match target WRAM offsets. Dynamic writer traces remain authoritative.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# opcode -> (mnemonic, operand_bytes, addressing)
OPS = {
    0x8D: ("STA", 2, "abs"),
    0x9D: ("STA", 2, "abs,X"),
    0x99: ("STA", 2, "abs,Y"),
    0x8F: ("STA", 3, "long"),
    0x9F: ("STA", 3, "long,X"),
    0x8E: ("STX", 2, "abs"),
    0x8C: ("STY", 2, "abs"),
    0x9C: ("STZ", 2, "abs"),
    0x9E: ("STZ", 2, "abs,X"),
    0xEE: ("INC", 2, "abs"),
    0xFE: ("INC", 2, "abs,X"),
    0xCE: ("DEC", 2, "abs"),
    0xDE: ("DEC", 2, "abs,X"),
    0x0E: ("ASL", 2, "abs"),
    0x1E: ("ASL", 2, "abs,X"),
    0x4E: ("LSR", 2, "abs"),
    0x5E: ("LSR", 2, "abs,X"),
    0x2E: ("ROL", 2, "abs"),
    0x3E: ("ROL", 2, "abs,X"),
    0x6E: ("ROR", 2, "abs"),
    0x7E: ("ROR", 2, "abs,X"),
    0x0C: ("TSB", 2, "abs"),
    0x1C: ("TRB", 2, "abs"),
}


def lorom_cpu_address(offset: int) -> str:
    """Return one conventional LoROM CPU mirror for a file offset."""
    bank = offset // 0x8000
    addr = 0x8000 + (offset % 0x8000)
    return f"{bank:02X}:{addr:04X}"


def scan(data: bytes, target: int, context: int) -> list[dict]:
    found: list[dict] = []
    lo = target & 0xFFFF
    for pos, opcode in enumerate(data):
        spec = OPS.get(opcode)
        if spec is None:
            continue
        mnemonic, n, mode = spec
        if pos + 1 + n > len(data):
            continue
        operand = int.from_bytes(data[pos + 1 : pos + 1 + n], "little")
        match = False
        if n == 2:
            match = operand == lo
        else:
            # Long addressing can explicitly target either canonical WRAM bank.
            match = operand in ((0x7E << 16) | lo, (0x7F << 16) | lo)
        if not match:
            continue

        a = max(0, pos - context)
        b = min(len(data), pos + 1 + n + context)
        found.append(
            {
                "rom_offset": f"0x{pos:06X}",
                "cpu_lorom": lorom_cpu_address(pos),
                "opcode": f"0x{opcode:02X}",
                "mnemonic": mnemonic,
                "mode": mode,
                "operand": f"0x{operand:0{n * 2}X}",
                "context_start": f"0x{a:06X}",
                "context_hex": data[a:b].hex(" "),
            }
        )
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("addresses", nargs="+", help="WRAM offsets, e.g. 0x1d1")
    ap.add_argument("--context", type=int, default=12)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    data = args.rom.read_bytes()
    report = {"rom": str(args.rom), "targets": {}}
    for raw in args.addresses:
        target = int(raw, 0)
        if not 0 <= target < 0x20000:
            raise SystemExit(f"WRAM offset out of range: {raw}")
        hits = scan(data, target, args.context)
        key = f"0x{target:05X}"
        report["targets"][key] = hits
        print(f"{key}: {len(hits)} candidate encoded writer(s)")
        for h in hits:
            print(
                f"  {h['rom_offset']} ({h['cpu_lorom']}) "
                f"{h['mnemonic']} {h['operand']} {h['mode']}"
            )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
