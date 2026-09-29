#!/usr/bin/env python3
"""Find candidate 65C816 instructions that access selected SNES MMIO registers.

This is deliberately a byte-pattern candidate generator, not a disassembler.
Absolute 16-bit operands are DB-sensitive, and scanning unaligned ROM bytes can
produce false positives. Dynamic MMIO traces remain authoritative.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# opcode -> (mnemonic, operand_bytes, addressing, access)
OPS = {
    0x8D: ("STA", 2, "abs", "write"),
    0x9D: ("STA", 2, "abs,X", "write"),
    0x99: ("STA", 2, "abs,Y", "write"),
    0x8F: ("STA", 3, "long", "write"),
    0x9F: ("STA", 3, "long,X", "write"),
    0x8E: ("STX", 2, "abs", "write"),
    0x8C: ("STY", 2, "abs", "write"),
    0x9C: ("STZ", 2, "abs", "write"),
    0x9E: ("STZ", 2, "abs,X", "write"),
    0xAD: ("LDA", 2, "abs", "read"),
    0xBD: ("LDA", 2, "abs,X", "read"),
    0xB9: ("LDA", 2, "abs,Y", "read"),
    0xAF: ("LDA", 3, "long", "read"),
    0xBF: ("LDA", 3, "long,X", "read"),
    0xAE: ("LDX", 2, "abs", "read"),
    0xBE: ("LDX", 2, "abs,Y", "read"),
    0xAC: ("LDY", 2, "abs", "read"),
    0xBC: ("LDY", 2, "abs,X", "read"),
    0x2C: ("BIT", 2, "abs", "read"),
    0x3C: ("BIT", 2, "abs,X", "read"),
    0xCD: ("CMP", 2, "abs", "read"),
    0xDD: ("CMP", 2, "abs,X", "read"),
    0xD9: ("CMP", 2, "abs,Y", "read"),
    0xCF: ("CMP", 3, "long", "read"),
    0xDF: ("CMP", 3, "long,X", "read"),
    0xEC: ("CPX", 2, "abs", "read"),
    0xCC: ("CPY", 2, "abs", "read"),
    0xEE: ("INC", 2, "abs", "read-write"),
    0xFE: ("INC", 2, "abs,X", "read-write"),
    0xCE: ("DEC", 2, "abs", "read-write"),
    0xDE: ("DEC", 2, "abs,X", "read-write"),
    0x0E: ("ASL", 2, "abs", "read-write"),
    0x1E: ("ASL", 2, "abs,X", "read-write"),
    0x4E: ("LSR", 2, "abs", "read-write"),
    0x5E: ("LSR", 2, "abs,X", "read-write"),
    0x2E: ("ROL", 2, "abs", "read-write"),
    0x3E: ("ROL", 2, "abs,X", "read-write"),
    0x6E: ("ROR", 2, "abs", "read-write"),
    0x7E: ("ROR", 2, "abs,X", "read-write"),
    0x0C: ("TSB", 2, "abs", "read-write"),
    0x1C: ("TRB", 2, "abs", "read-write"),
}


def lorom_cpu_address(offset: int) -> str:
    bank = offset // 0x8000
    addr = 0x8000 + (offset % 0x8000)
    return f"{bank:02X}:{addr:04X}"


def is_hw_mirror_bank(bank: int) -> bool:
    return 0x00 <= bank <= 0x3F or 0x80 <= bank <= 0xBF


def scan(data: bytes, target: int, context: int = 12) -> list[dict]:
    if not 0 <= target <= 0xFFFF:
        raise ValueError("MMIO target must be a 16-bit address")
    found: list[dict] = []
    for pos, opcode in enumerate(data):
        spec = OPS.get(opcode)
        if spec is None:
            continue
        mnemonic, n, mode, access = spec
        end = pos + 1 + n
        if end > len(data):
            continue
        operand = int.from_bytes(data[pos + 1:end], "little")

        if n == 2:
            if operand != target:
                continue
            db_sensitive = True
            explicit_bank = None
        else:
            if (operand & 0xFFFF) != target:
                continue
            explicit_bank = (operand >> 16) & 0xFF
            if not is_hw_mirror_bank(explicit_bank):
                continue
            db_sensitive = False

        a = max(0, pos - context)
        b = min(len(data), end + context)
        found.append(
            {
                "rom_offset": pos,
                "rom_offset_hex": f"0x{pos:06X}",
                "cpu_lorom": lorom_cpu_address(pos),
                "opcode": f"0x{opcode:02X}",
                "mnemonic": mnemonic,
                "mode": mode,
                "access": access,
                "operand": f"0x{operand:0{n * 2}X}",
                "db_sensitive": db_sensitive,
                "explicit_bank": (
                    f"0x{explicit_bank:02X}" if explicit_bank is not None else None
                ),
                "context_start_hex": f"0x{a:06X}",
                "context_hex": data[a:b].hex(" "),
            }
        )
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("addresses", nargs="+", help="16-bit MMIO addresses")
    ap.add_argument("--context", type=int, default=12)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    data = args.rom.read_bytes()
    report = {
        "schema_version": 1,
        "rom": str(args.rom),
        "method": "unaligned opcode/operand candidate scan; absolute hits remain DB-sensitive",
        "targets": {},
    }
    for raw in args.addresses:
        target = int(raw, 0)
        hits = scan(data, target, args.context)
        key = f"0x{target:04X}"
        report["targets"][key] = hits
        print(f"{key}: {len(hits)} encoded access candidate(s)")
        for hit in hits:
            db = " DB-sensitive" if hit["db_sensitive"] else ""
            print(
                f"  {hit['rom_offset_hex']} ({hit['cpu_lorom']}) "
                f"{hit['mnemonic']} {hit['operand']} {hit['mode']} "
                f"{hit['access']}{db}"
            )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
