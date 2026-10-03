#!/usr/bin/env python3
"""Report direct ROM call references into the native Widescreen preparation entry."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

try:
    from tools.verify_europe_semantic_edges import find_call_refs
    from tools.compare_europe_usa_snes2asm_homologs import trace, seed_entries, cpu_to_offset
except ModuleNotFoundError:
    from verify_europe_semantic_edges import find_call_refs
    from compare_europe_usa_snes2asm_homologs import trace, seed_entries, cpu_to_offset

TARGETS = {
    "long_wrapper": "81:A52B",
    "per_frame_entry": "81:A52F",
}

def _classify_refs(blob: bytes, cpu: str, disasm) -> dict:
    bank = cpu.split(":", 1)[0].upper()
    raw = find_call_refs(blob, cpu)
    jsr = [r for r in raw["jsr"] if r["cpu"].split(":", 1)[0].upper() == bank]
    def classify(rows):
        out = []
        for row in rows:
            off = row["file_offset"]
            executable = bool(disasm.code_map[off] & disasm.OP_CODE)
            out.append({**row, "executable": executable})
        return out
    return {"jsr": classify(jsr), "jsl": classify(raw["jsl"])}

def report(rom: Path) -> dict:
    blob = rom.read_bytes()
    disasm = trace(blob)
    trusted = [cpu_to_offset("83:CBCC"), cpu_to_offset("81:A52B")]
    seed_entries(disasm, trusted)
    refs = {name: {"target": cpu, **_classify_refs(blob, cpu, disasm)}
            for name, cpu in TARGETS.items()}
    return {
        "schema_version": 1,
        "rom": str(rom),
        "targets": refs,
        "trusted_trace_seeds": ["83:CBCC", "81:A52B"],
        "direct_reference_count": sum(
            len(v["jsr"]) + len(v["jsl"]) for v in refs.values()
        ),
    }

def render(data: dict) -> str:
    lines = ["# Native Widescreen preparation reachability", "",
             "Static code-role classification is seeded from trusted entries `83:CBCC` and `81:A52B`.", ""]
    for name, item in data["targets"].items():
        lines.append(f"## {name} ({item['target']})")
        lines.append("")
        lines.append(f"- JSR references: **{len(item['jsr'])}**")
        for ref in item["jsr"]:
            lines.append(
                f"  - {ref['cpu']} (ROM 0x{ref['file_offset']:06X}; executable={ref['executable']})"
            )
        lines.append(f"- JSL references: **{len(item['jsl'])}**")
        for ref in item["jsl"]:
            lines.append(
                f"  - {ref['cpu']} (ROM 0x{ref['file_offset']:06X}; executable={ref['executable']})"
            )
        lines.append("")
    return "\n".join(lines)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()
    data = report(args.rom)
    md = render(data)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(md + "\n", encoding="utf-8")
    print(md)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
