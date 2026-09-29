#!/usr/bin/env python3
"""Export understood symbol rows from docs/SYMBOLS.md as machine-readable JSON.

The Markdown document remains the human-owned authority. This exporter deliberately
skips TBD rows so downstream tools only consume asserted symbols.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "SYMBOLS.md"
DEFAULT_OUTPUT = ROOT / "analysis" / "generated" / "symbols.json"


def clean(cell: str) -> str:
    cell = cell.strip()
    if cell.startswith("`") and cell.endswith("`"):
        cell = cell[1:-1]
    return cell


def parse() -> dict:
    section = None
    headers: list[str] = []
    entries: list[dict] = []
    for raw in SOURCE.read_text(encoding="utf-8").splitlines():
        if raw.startswith("## "):
            section = raw[3:].strip().lower()
            headers = []
            continue
        if not raw.startswith("|") or section not in {"functions", "ram"}:
            continue
        cells = [clean(x) for x in raw.strip().strip("|").split("|")]
        if not headers:
            headers = [re.sub(r"\s+", "_", x.lower()) for x in cells]
            continue
        if all(set(x) <= {"-", ":"} for x in cells):
            continue
        row = dict(zip(headers, cells))
        address = row.get("address", "")
        if not address or address.upper() == "TBD":
            continue
        entry = {"kind": "function" if section == "functions" else "ram"}
        entry.update(row)
        if "confidence" in entry:
            try:
                entry["confidence"] = int(entry["confidence"])
            except ValueError:
                pass
        entries.append(entry)
    return {
        "schema_version": 1,
        "source": "docs/SYMBOLS.md",
        "generated": True,
        "entries": entries,
    }


def render() -> str:
    return json.dumps(parse(), indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    expected = render()
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != expected:
            print(f"{args.output.relative_to(ROOT)} is stale; run tools/export_symbols.py", file=sys.stderr)
            return 1
        print(f"{args.output.relative_to(ROOT)} is current.")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(expected, encoding="utf-8")
    print(args.output.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
