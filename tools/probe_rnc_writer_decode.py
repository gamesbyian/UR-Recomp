#!/usr/bin/env python3
"""Decode the shipped USA RNC1 routine with snesrecomp's authoritative v2 decoder.

This is deliberately a probe, not a home-grown disassembler. It asks the same
decoder used for recompilation whether the two dynamically traced writer PCs
belong to the control-flow graph rooted at the known RNC1 entry and prints the
nearby decoded instructions when they do.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECOMPILER = ROOT / "snesrecomp" / "recompiler"
V2 = RECOMPILER / "v2"
sys.path.insert(0, str(RECOMPILER))
sys.path.insert(0, str(V2))

from decoder import decode_function  # type: ignore  # noqa: E402

ENTRY_BANK = 0x01
ENTRY_PC = 0xB8F1
WRITERS = {
    "course-byte-increment": 0x01BA96,
    "decoded-output-write": 0x01BB73,
}


def fmt(di) -> str:
    pc = di.key.pc
    return (
        f"${(pc >> 16) & 0xFF:02X}:{pc & 0xFFFF:04X} "
        f"[M={di.key.m} X={di.key.x}] "
        f"{di.insn.mnem:<5} {di.insn._fmt()}"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "rom",
        type=Path,
        nargs="?",
        default=Path("reference/roms/retail/Uniracers_USA.sfc"),
    )
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    graph = decode_function(
        rom,
        bank=ENTRY_BANK,
        start=ENTRY_PC,
        entry_m=0,
        entry_x=0,
    )

    rows = sorted(
        graph.insns.values(),
        key=lambda d: (d.key.pc, d.key.m, d.key.x),
    )
    report = {
        "entry": f"{ENTRY_BANK:02X}:{ENTRY_PC:04X}",
        "decoded_states": len(rows),
        "writer_sites": {},
    }

    for label, target in WRITERS.items():
        matches = [d for d in rows if d.key.pc == target]
        item = {"reachable_from_entry": bool(matches), "variants": []}
        if matches:
            all_index = {id(d): i for i, d in enumerate(rows)}
            for di in matches:
                idx = all_index[id(di)]
                context = rows[max(0, idx - 8):idx + 9]
                item["variants"].append(
                    {
                        "m": di.key.m,
                        "x": di.key.x,
                        "instruction": fmt(di),
                        "context": [fmt(x) for x in context],
                    }
                )
        report["writer_sites"][label] = item

    print(json.dumps(report, indent=2))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
