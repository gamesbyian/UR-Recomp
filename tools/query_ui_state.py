#!/usr/bin/env python3
"""Query the compact Uniracers UI menu-state index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def norm_menu_id(value: str) -> str:
    n = int(value, 0)
    if not 0 <= n <= 0xFF:
        raise argparse.ArgumentTypeError("menu ID must fit in one byte")
    return f"0x{n:02X}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=Path, default=Path("analysis/ui-menu-index.json"))
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--menu-id", type=norm_menu_id, help="menu byte, e.g. 0x99 or 153")
    group.add_argument("--state", help="conceptual state ID, case-insensitive")
    group.add_argument("--all", action="store_true", help="show every indexed menu state")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    data = json.loads(args.index.read_text())
    entries = data["entries"]

    if args.menu_id:
        matches = [e for e in entries if e["value"].upper() == args.menu_id.upper()]
    elif args.state:
        key = args.state.upper()
        matches = [e for e in entries if e["state_id"].upper() == key]
    else:
        matches = entries

    if args.as_json:
        print(json.dumps(matches, indent=2))
        return 0 if matches else 1

    if not matches:
        print("no matching UI state")
        return 1

    print(f"currentMenu address: {data['address']}")
    for e in matches:
        bits = [e["value"], e["state_id"], e["status"]]
        if e.get("variant"):
            bits.append(f"variant={e['variant']}")
        print("  ".join(bits))
        print(f"  source: {e['source']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
