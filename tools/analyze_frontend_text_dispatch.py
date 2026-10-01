#!/usr/bin/env python3
"""Decode the bank-80 frontend/text command dispatch table from the canonical ROM."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TABLE_CPU = "80:C3CB"
TABLE_OFFSET = 0x43CB
VALID_COMMANDS = tuple(range(0xFF, 0xEE, -1))  # FF..EF inclusive


def decode_table(data: bytes, offset: int = TABLE_OFFSET) -> dict:
    need = offset + (len(VALID_COMMANDS) + 1) * 2
    if len(data) < need:
        raise ValueError(f"ROM too small for dispatch table: need 0x{need:X} bytes")

    entries = []
    for i, command in enumerate(VALID_COMMANDS):
        lo = data[offset + i * 2]
        hi = data[offset + i * 2 + 1]
        target = lo | (hi << 8)
        entries.append(
            {
                "command": f"0x{command:02X}",
                "index": i,
                "target": f"80:{target:04X}",
                "target_word": f"0x{target:04X}",
                "rom_code_target": target >= 0x8000,
            }
        )

    # EE satisfies the parser's >= EE comparison, but the next word is not
    # part of the valid handler table. Preserve it as an analyzer-range clue.
    i = len(VALID_COMMANDS)
    ee_word = data[offset + i * 2] | (data[offset + i * 2 + 1] << 8)

    return {
        "table_cpu": TABLE_CPU,
        "table_rom_offset": f"0x{offset:06X}",
        "valid_command_range": "0xFF..0xEF",
        "entries": entries,
        "ee_fallthrough_word": f"0x{ee_word:04X}",
        "ee_rom_code_target": ee_word >= 0x8000,
        "interpretation": (
            "FF..EF form the valid 17-entry dispatch domain. EE reaches the "
            "comparison threshold but the following bytes do not encode another "
            "valid ROM handler pointer, so EE requires a caller/parser invariant "
            "rather than being treated as an eighteenth table command."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = decode_table(args.rom.read_bytes())
    text = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
