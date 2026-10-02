#!/usr/bin/env python3
"""Emit a bounded static listing around the active 81:F3xx VRAM scroll emitter."""
from __future__ import annotations

import json
from pathlib import Path

from compare_europe_usa_snes2asm_homologs import ROOT, cpu_to_offset, offset_to_cpu
from align_pal_snes2asm_windows import trace

ROM = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
OUT_JSON = ROOT / "analysis/generated/active-vram-scroll-emitter-static.json"
OUT_MD = ROOT / "analysis/generated/active-vram-scroll-emitter-static.md"

START = cpu_to_offset("81:F2E0")
END = cpu_to_offset("81:F380")


def main() -> int:
    data = ROM.read_bytes()
    d = trace(data)
    # This path is reached in the stock race; use analyzer-established opcode
    # boundaries rather than inventing a new semantic entry point.
    opcode_offsets = [
        off for off in range(START, END + 1)
        if d.code_map[off] & d.OP_CODE
    ]
    if not opcode_offsets:
        raise SystemExit("snes2asm did not recover code in 81:F2E0..F380")

    d.decode(START, END + 1)
    decoded = [
        (off, ins)
        for off, ins in d.code.item_range(START, END + 1)
        if d.code_map[off] & d.OP_CODE
    ]
    rows = []
    for i, (off, ins) in enumerate(decoded):
        next_off = decoded[i + 1][0] if i + 1 < len(decoded) else min(END + 1, off + 4)
        rows.append({
            "cpu": offset_to_cpu(off),
            "offset": off,
            "bytes": data[off:next_off].hex(" "),
            "text": ins.text(),
        })

    interesting = [
        r for r in rows
        if any(x in r["text"].lower() for x in (
            "$2116", "$2118", "$0419", "$04f5", "$0505", "$050d",
            "$0dcd", "$0dcf", "$0d8d", "$0dad", "$0d6d", "$0d7d"
        ))
    ]
    report = {
        "schema_version": 1,
        "range": "81:F2E0..81:F380",
        "rows": rows,
        "interesting_rows": interesting,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Active 81:F3xx VRAM scroll emitter static listing",
        "",
        "Bounded listing around the CPU-direct emitter proven live by the deterministic scroll fixture.",
        "",
        "| CPU | bytes | instruction |",
        "|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| `{r['cpu']}` | `{r['bytes']}` | `{r['text']}` |")
    lines += ["", "## Directly relevant references", ""]
    if interesting:
        for r in interesting:
            lines.append(f"- `{r['cpu']}` `{r['text']}`")
    else:
        lines.append("- none in this bounded range")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT_MD.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
