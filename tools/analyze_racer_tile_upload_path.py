#!/usr/bin/env python3
"""Trace the racer presentation tile-upload path around staging and VRAM DMA.

This is intentionally narrow. It records executable instructions around the
known presentation staging consumers and the F2BB helper, highlighting PPU/DMA
register traffic and the recovered staging arrays. The goal is to resolve the
remaining ROM-source -> retained-VRAM byte-layout discrepancy without reopening
the already-closed occupancy/order contract.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from compare_europe_usa_snes2asm_homologs import cpu_to_offset, seed_entries, trace

RANGES = (
    ("dma_consumer_a", "82:B8D1", "82:B980"),
    ("dma_consumer_b", "82:C53A", "82:C5E0"),
    ("tile_pair_helper", "83:F2BB", "83:F4D1"),
)
SEEDS = ("82:B8D1", "82:C53A", "83:F2BB")
INTEREST = (
    "VMAIN", "VMADD", "VMDATA", "DMA", "MDMAEN",
    "$1645", "$15A1", "$16E9",
    "$1647", "$15A3", "$16EB",
    "$1649", "$15A5", "$16ED",
)


def decoded_ranges(rom: bytes) -> list[dict]:
    d = trace(rom)
    seed_entries(d, [cpu_to_offset(x) for x in SEEDS])
    out = []
    for name, start_cpu, end_cpu in RANGES:
        start = cpu_to_offset(start_cpu)
        end = cpu_to_offset(end_cpu) + 1
        d.decode(start, end)
        rows = []
        for off, ins in d.code.item_range(start, end):
            size = d.opSize(rom[off])
            text = ins.text()
            rows.append({
                "cpu": f"{(off // 0x8000) | 0x80:02X}:{0x8000 + (off % 0x8000):04X}",
                "text": text,
                "bytes": rom[off:off + size].hex(" "),
                "interesting": any(token.upper() in text.upper() for token in INTEREST),
            })
        out.append({
            "name": name,
            "start": start_cpu,
            "end": end_cpu,
            "rows": rows,
            "interesting_rows": [r for r in rows if r["interesting"]],
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()

    report = {
        "schema_version": 1,
        "purpose": "Bound racer presentation staging -> DMA/VRAM upload semantics.",
        "ranges": decoded_ranges(args.rom.read_bytes()),
    }
    md = ["# Racer tile-upload path", ""]
    for block in report["ranges"]:
        md += [f"## {block['name']} ({block['start']}..{block['end']})", ""]
        md.append("### PPU/DMA/staging references")
        md.append("")
        for row in block["interesting_rows"]:
            md.append(f"- \`{row['cpu']}\`  \`{row['bytes']}\`  {row['text']}")
        md.append("")
        md.append("### Full decoded range")
        md.append("")
        for row in block["rows"]:
            md.append(f"    {row['cpu']}  {row['text']}    ; {row['bytes']}")
        md.append("")

    js = json.dumps(report, indent=2, sort_keys=True) + "\n"
    text = "\n".join(md) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(js, encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
