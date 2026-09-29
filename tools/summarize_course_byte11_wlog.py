#!/usr/bin/env python3
"""Summarize exact-PC write-log records for the live course header byte 11."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

LINE = re.compile(
    r"^f(?P<frame>\d+)\s+"
    r"(?P<bank>[0-9A-Fa-f]{2}):(?P<addr>[0-9A-Fa-f]{4})="
    r"(?P<value>[0-9A-Fa-f]+)\s+w(?P<width>\d+)\s+"
    r"(?P<scope>\S+)"
    r"(?:.*?\sIPC=(?P<ipc>[0-9A-Fa-f]{6}))?"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("--json-out", type=Path, required=True)
    args = ap.parse_args()

    rows = []
    for raw in args.log.read_text(encoding="utf-8", errors="replace").splitlines():
        m = LINE.match(raw)
        if not m:
            continue
        bank = int(m.group("bank"), 16)
        addr = int(m.group("addr"), 16)
        if bank != 0x7F or addr != 0x000B:
            continue
        rows.append({
            "frame": int(m.group("frame")),
            "value": int(m.group("value"), 16) & 0xFF,
            "width": int(m.group("width")),
            "scope": m.group("scope"),
            "ipc": int(m.group("ipc"), 16) if m.group("ipc") else None,
            "raw": raw,
        })

    if not rows:
        raise SystemExit("no 7F:000B writes found in address log")

    report = {
        "address": "7F:000B",
        "writes": rows,
        "values": [r["value"] for r in rows],
        "unique_ipcs": sorted({r["ipc"] for r in rows if r["ipc"] is not None}),
        "unique_scopes": sorted({r["scope"] for r in rows}),
    }

    print(json.dumps(report, indent=2))
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
