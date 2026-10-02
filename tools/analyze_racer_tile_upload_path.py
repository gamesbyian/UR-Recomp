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
REGISTER_TARGETS = {
    "DMAP0": 0x4300,
    "BBAD0": 0x4301,
    "DMASRC0L": 0x4302,
    "DMASRC0B": 0x4304,
    "DMALEN0L": 0x4305,
    "VMAIN": 0x2115,
    "VMADDL": 0x2116,
    "VMDATAL": 0x2118,
    "VMDATAH": 0x2119,
    "MDMAEN": 0x420B,
}
WRITE_OPS = {
    0x8D: "STA abs",
    0x8E: "STX abs",
    0x8C: "STY abs",
    0x9C: "STZ abs",
}

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



def register_write_sites(rom: bytes) -> list[dict]:
    """Find literal absolute writes to DMA/VRAM control registers.

    Keep raw candidates as evidence even when the static tracer does not mark
    the surrounding code reachable from the narrow racer seeds.
    """
    d = trace(rom)
    seed_entries(d, [cpu_to_offset(x) for x in SEEDS])
    rows = []
    by_addr = {addr: name for name, addr in REGISTER_TARGETS.items()}
    for off in range(len(rom) - 2):
        op = rom[off]
        if op not in WRITE_OPS:
            continue
        addr = rom[off + 1] | (rom[off + 2] << 8)
        if addr not in by_addr:
            continue
        status = d.code_map[off] if off < len(d.code_map) else 0
        rows.append({
            "cpu": f"{(off // 0x8000) | 0x80:02X}:{0x8000 + (off % 0x8000):04X}",
            "register": by_addr[addr],
            "address": f"0x{addr:04X}",
            "mnemonic": WRITE_OPS[op],
            "bytes": rom[off:off + 3].hex(" "),
            "tracer_executable": bool(status & d.OP_CODE),
        })
    return rows


def nearby_register_setup(rom: bytes, writes: list[dict]) -> list[dict]:
    """Decode bounded context around candidate control-register writes."""
    d = trace(rom)
    seed_entries(d, [cpu_to_offset(x) for x in SEEDS])
    out = []
    # Prefer bank-82 candidates because both racer DMA consumers live there.
    for row in writes:
        if not row["cpu"].startswith("82:"):
            continue
        off = cpu_to_offset(row["cpu"])
        bank_start = (off // 0x8000) * 0x8000
        bank_end = bank_start + 0x8000
        start = max(bank_start, off - 24)
        end = min(bank_end, off + 32)
        try:
            d.decode(start, end)
        except Exception:
            pass
        ctx = []
        for q, ins in d.code.item_range(start, end):
            try:
                size = d.opSize(rom[q])
            except Exception:
                size = 1
            ctx.append({
                "cpu": f"{(q // 0x8000) | 0x80:02X}:{0x8000 + (q % 0x8000):04X}",
                "text": ins.text(),
                "bytes": rom[q:q + size].hex(" "),
            })
        out.append({"write": row, "context": ctx})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    writes = register_write_sites(rom)
    report = {
        "schema_version": 2,
        "purpose": "Bound racer presentation staging -> DMA/VRAM upload semantics.",
        "ranges": decoded_ranges(rom),
        "register_write_sites": writes,
        "bank82_register_write_contexts": nearby_register_setup(rom, writes),
    }
    md = ["# Racer tile-upload path", ""]
    md += ["## Literal DMA/VRAM control-register writes", ""]
    for row in report["register_write_sites"]:
        md.append(
            f"- \`{row['cpu']}\` {row['mnemonic']} -> {row['register']} "
            f"({row['address']}), bytes \`{row['bytes']}\`, "
            f"tracer_executable={row['tracer_executable']}"
        )
    md.append("")
    md += ["## Bank-82 setup contexts", ""]
    for block in report["bank82_register_write_contexts"]:
        row = block["write"]
        md.append(f"### {row['cpu']} -> {row['register']}")
        md.append("")
        for ctx in block["context"]:
            md.append(f"    {ctx['cpu']}  {ctx['text']}    ; {ctx['bytes']}")
        md.append("")

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
