#!/usr/bin/env python3
"""Read-only malmazuke PAL source/address lookup against pinned UR-Recomp evidence.

Never promotes interval projections to proved USA semantic correspondence.
No ROM, core, native executable, network access, or external dependencies required.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = "42d444594641d23f5d3c15da7b7c454bb5180e43"
IMPORTED = ROOT / "reference/imported/reverse-engineering/malmazuke-unirally-reconstruction/docs/map/static/native-symbols.json"
CROSSWALK = ROOT / "analysis/data/malmazuke-pal-structural-links-20261010.json"
HEX = re.compile(r"^(?:\\$|0x)?([0-9a-fA-F]{2}):?([0-9a-fA-F]{4})$")


def canonical_address(value: str) -> str:
    match = HEX.fullmatch(value.strip())
    if not match:
        raise ValueError("expected a complete 24-bit SNES address (e.g. 81:8050)")
    bank, addr = (int(part, 16) for part in match.groups())
    if 0 <= bank <= 3 and addr >= 0x8000:
        bank |= 0x80
    if bank == 0x7E and addr < 0x2000:
        return f"${addr:04X}"
    return f"{bank:02X}:{addr:04X}"


def load_inputs(source: Path = IMPORTED, crosswalk: Path = CROSSWALK) -> tuple[dict, dict]:
    symbols = json.loads(source.read_text(encoding="utf-8"))
    links = json.loads(crosswalk.read_text(encoding="utf-8"))
    if (symbols.get("schema_version") != 1 or links.get("schema_version") != 1
            or links.get("source", {}).get("commit") != PIN):
        raise ValueError("unrecognized or unpinned malmazuke evidence")
    return symbols, links


def query(symbols: dict, links: dict, *, address: str | None = None,
          usa: str | None = None, pattern: str | None = None, limit: int = 100) -> dict:
    if sum(x is not None for x in (address, usa, pattern)) != 1:
        raise ValueError("exactly one of address, usa or pattern is required")
    if limit < 1:
        raise ValueError("limit must be positive")
    needle = canonical_address(address) if address else None
    usa_needle = canonical_address(usa) if usa else None
    rx = re.compile(pattern, re.IGNORECASE) if pattern is not None else None
    joined = {row["pal"]: row for row in links["entries"]}
    rows = []
    for entry in symbols["addresses"]:
        a = entry["address"]
        normalized = canonical_address(a) if a.startswith(("$", "0x")) else a
        companion = joined.get(normalized)
        if needle and normalized != needle:
            continue
        if usa_needle and (not companion or companion["correspondence"].get("usa") != usa_needle):
            continue
        if rx and not rx.search(" ".join([a, *entry.get("native", []),
                                          companion.get("pal_label") or "" if companion else ""])):
            continue
        cross = companion["correspondence"] if companion else {"status": "not-indexed"}
        rows.append({
            "pal": normalized,
            "region": entry["region"],
            "native": entry.get("native", []),
            "range_ends": entry.get("range_ends", []),
            "label": companion.get("pal_label") if companion else None,
            "domains": companion.get("domains", []) if companion else [],
            "usa_candidate": cross.get("usa"),
            "correspondence_status": cross["status"],
            "region_evidence": cross.get("region"),
            "verified_usa_semantics": False,
        })
    return {"upstream": "malmazuke/unirally-reconstruction", "source_commit": PIN,
            "warning": "PAL source citation and geometric USA candidate only; verify original USA ROM independently",
            "total_matches": len(rows), "truncated": len(rows) > limit, "matches": rows[:limit]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pal", help="PAL ROM, WRAM, SRAM or I/O address")
    g.add_argument("--usa-candidate", help="USA address predicted by existing bounded structural interval")
    g.add_argument("--grep", help="case-insensitive regex over original address, C++ symbol and label")
    ap.add_argument("--limit", type=int, default=40)
    args = ap.parse_args(argv)
    try:
        symbols, links = load_inputs()
        result = query(symbols, links, address=args.pal, usa=args.usa_candidate,
                       pattern=args.grep, limit=args.limit)
    except (OSError, ValueError, KeyError, re.error) as exc:
        ap.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
