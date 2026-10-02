#!/usr/bin/env python3
"""Report direct ROM call references into the native Widescreen preparation entry."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from tools.verify_europe_semantic_edges import find_call_refs
except ModuleNotFoundError:
    from verify_europe_semantic_edges import find_call_refs

TARGETS = {
    "long_wrapper": "81:A52B",
    "per_frame_entry": "81:A52F",
}

def report(rom: Path) -> dict:
    blob = rom.read_bytes()
    refs = {name: {"target": cpu, **find_call_refs(blob, cpu)}
            for name, cpu in TARGETS.items()}
    return {
        "schema_version": 1,
        "rom": str(rom),
        "targets": refs,
        "direct_reference_count": sum(
            len(v["jsr"]) + len(v["jsl"]) for v in refs.values()
        ),
    }

def render(data: dict) -> str:
    lines = ["# Native Widescreen preparation reachability", ""]
    for name, item in data["targets"].items():
        lines.append(f"## {name} ({item['target']})")
        lines.append("")
        lines.append(f"- JSR references: **{len(item['jsr'])}**")
        for ref in item["jsr"]:
            lines.append(f"  - {ref['cpu']} (ROM 0x{ref['file_offset']:06X})")
        lines.append(f"- JSL references: **{len(item['jsl'])}**")
        for ref in item["jsl"]:
            lines.append(f"  - {ref['cpu']} (ROM 0x{ref['file_offset']:06X})")
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
