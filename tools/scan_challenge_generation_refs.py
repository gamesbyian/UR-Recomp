#!/usr/bin/env python3
"""Find direct 65C816 long-address references to SRAM $77:10D1.

This is deliberately a bounded discriminator helper, not a general
disassembler. It finds literal little-endian D1 10 77 operands, records the
preceding opcode byte, maps LoROM file offsets to CPU addresses, and emits a
small surrounding byte window for follow-up against the known tour/result
routines.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TARGET = bytes((0xD1, 0x10, 0x77))

# 65C816 opcodes with a 24-bit absolute-long operand. The target may appear in
# data, so classification remains "candidate" until the opcode/context agrees.
LONG_OPCODES = {
    0x0F: "ORA.l",
    0x1F: "ORA.l,X",
    0x2F: "AND.l",
    0x3F: "AND.l,X",
    0x4F: "EOR.l",
    0x5F: "EOR.l,X",
    0x6F: "ADC.l",
    0x7F: "ADC.l,X",
    0x8F: "STA.l",
    0x9F: "STA.l,X",
    0xAF: "LDA.l",
    0xBF: "LDA.l,X",
    0xCF: "CMP.l",
    0xDF: "CMP.l,X",
    0xEF: "SBC.l",
    0xFF: "SBC.l,X",
}


def lorom_cpu_address(offset: int) -> str:
    # UR-Recomp documents executable LoROM through its high-bank mirror
    # (80:xxxx, 81:xxxx, ...), matching the recovered stock routine names.
    bank = 0x80 | (offset // 0x8000)
    addr = 0x8000 + (offset % 0x8000)
    return f"{bank:02X}:{addr:04X}"


def semantic_hint(cpu_address: str, opcode: int | None) -> str | None:
    # These labels intentionally stop at what retained stock evidence plus
    # local instruction shape establishes. Unknown consumers remain unknown.
    if cpu_address == "80:B315" and opcode == 0xAF:
        return "ordinary-opponent-index: generation + 0x11, capped at 0x13"
    if cpu_address == "80:E6BF" and opcode == 0x8F:
        return "tour-confirm snapshot writer from active persistent medal"
    if cpu_address in {"80:BC15", "80:BC79"} and opcode == 0xCF:
        return "persistent-medal versus generation-snapshot comparison"
    if cpu_address == "80:E8F0" and opcode == 0xAF:
        return "frontend generation-label consumer"
    if cpu_address in {"80:EAA6", "80:EAB9"}:
        return "generation reconciliation read/write path"
    return None


def scan(rom: bytes) -> list[dict]:
    out = []
    start = 0
    while True:
        pos = rom.find(TARGET, start)
        if pos < 0:
            break
        opcode_pos = pos - 1
        opcode = rom[opcode_pos] if opcode_pos >= 0 else None
        lo = max(0, opcode_pos - 16)
        hi = min(len(rom), pos + len(TARGET) + 16)
        cpu_address = lorom_cpu_address(opcode_pos)
        out.append({
            "file_offset": f"0x{opcode_pos:06X}",
            "cpu_address": cpu_address,
            "opcode": None if opcode is None else f"0x{opcode:02X}",
            "mnemonic": LONG_OPCODES.get(opcode),
            "recognized_long_address_instruction": opcode in LONG_OPCODES,
            "semantic_hint": semantic_hint(cpu_address, opcode),
            "window_start": f"0x{lo:06X}",
            "window_hex": rom[lo:hi].hex(" "),
        })
        start = pos + 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("rom", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    refs = scan(args.rom.read_bytes())
    report = {
        "schema_version": 1,
        "target": "77:10D1",
        "purpose": "Bound direct consumers of the stock tour-confirm medal-generation snapshot.",
        "references": refs,
        "recognized_count": sum(
            1 for r in refs if r["recognized_long_address_instruction"]),
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
