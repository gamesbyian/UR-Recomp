#!/usr/bin/env python3
"""Query independent USA-ROM symbols from Ema Guillén's pinned baldosa intake.

Read-only external evidence: results are leads, never promoted project symbols.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reference/imported/reverse-engineering/baldosa-uniracers-recomp/decomp"
PIN = "10b864b9d14a7b7416dd909eb7b054c88faef101"
ROW = re.compile(r"^\s*([A-Fa-f0-9]{6})\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s+(\d+))?\s*(?:;\s*(.*))?$")


def address(value: str) -> int:
    value = value.strip().replace("$", "").replace(":", "")
    if value.lower().startswith("0x"):
        value = value[2:]
    if not re.fullmatch(r"[A-Fa-f0-9]{1,6}", value):
        raise ValueError(f"invalid 24-bit hexadecimal address: {value!r}")
    return int(value, 16)


def parse_rows(text: str, kind: str) -> list[dict]:
    if kind not in {"function", "ram"}:
        raise ValueError("expected function or ram")
    result = []
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith(("#", ";")):
            continue
        m = ROW.match(line)
        if not m or (kind == "function" and m.group(3) is not None):
            continue
        if kind == "ram" and m.group(3) is None:
            continue
        item = {
            "kind": kind, "address": f"{int(m.group(1),16):06X}",
            "name": m.group(2), "description": m.group(4) or "",
            "line": line_no, "provenance": PIN,
        }
        if kind == "ram":
            item["width"] = int(m.group(3))
        result.append(item)
    return result


def load() -> list[dict]:
    result = []
    for kind, path in (
        ("function", SOURCE / "symbols.txt"),
        ("ram", SOURCE / "ram.txt"),
    ):
        result.extend(parse_rows(path.read_text(encoding="utf-8"), kind))
    return result


def query(rows: list[dict], addr: int | None = None, pattern: str | None = None,
          kind: str = "all") -> list[dict]:
    regex = re.compile(pattern, flags=re.IGNORECASE) if pattern else None
    return [
        item for item in rows
        if (kind == "all" or item["kind"] == kind)
        and (addr is None or int(item["address"], 16) == addr)
        and (regex is None or regex.search(item["name"] + " " + item["description"]))
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--address", type=address)
    parser.add_argument("--match", help="case-insensitive regex against name and comment")
    parser.add_argument("--kind", choices=("all", "function", "ram"), default="all")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")
    matches = query(load(), args.address, args.match, args.kind)
    shown = matches[:args.limit]
    if args.json:
        print(json.dumps({"source_commit": PIN, "total_matches": len(matches),
                          "truncated": len(shown) < len(matches),
                          "entries": shown}, indent=2))
    else:
        print(f"External named symbols, baldosa@{PIN[:12]}: {len(matches)} matches")
        for item in shown:
            a = item["address"]
            print(f"{a[:2]}:{a[2:]} {item['kind']} {item['name']}"
                  + (f" [{item['width']} bytes]" if item['kind'] == "ram" else "")
                  + (f" — {item['description']}" if item["description"] else ""))
        if len(matches) > len(shown):
            print(f"... {len(matches)-len(shown)} more (increase --limit)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
