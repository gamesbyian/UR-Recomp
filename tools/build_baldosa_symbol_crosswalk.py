#!/usr/bin/env python3
"""Build a non-authoritative address crosswalk: external baldosa names vs local vetted symbols.

Every external label is a lead. Matching addresses do NOT validate its meaning.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from query_baldosa_symbols import PIN, load as load_external

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "analysis/generated/symbols.json"
CPU_ADDR = re.compile(r"([0-9A-Fa-f]{2}):([0-9A-Fa-f]{4})")


def local_addresses(raw: str) -> set[str]:
    result = set()
    for bank, offset in CPU_ADDR.findall(str(raw)):
        b, a = int(bank, 16), int(offset, 16)
        # The original code in LoROM banks $80..$83 also appears through
        # the $00..$03 Fast/Slow mirrors. RAM $7E/$7F and SRAM $77 retain banks.
        if 0 <= b <= 3 and a >= 0x8000:
            b |= 0x80
        result.add(f"{b:02X}{a:04X}")
    return result


def crosswalk(local_entries: list[dict], external_entries: list[dict]) -> dict:
    local: dict[tuple[str, str], set[str]] = {}
    skipped = 0
    for entry in local_entries:
        keys = local_addresses(entry.get("address", ""))
        if not keys:
            skipped += 1
            continue
        for address in keys:
            local.setdefault((entry.get("kind", ""), address), set()).add(str(entry.get("name", "")))
    external: dict[tuple[str, str], set[str]] = {}
    for entry in external_entries:
        external.setdefault((entry["kind"], entry["address"]), set()).add(entry["name"])

    rows = []
    for kind, addr in sorted(set(local) | set(external)):
        local_names = sorted(local.get((kind, addr), set()))
        external_names = sorted(external.get((kind, addr), set()))
        if local_names and external_names:
            status = "same_name" if set(local_names) & set(external_names) else "different_names"
        elif external_names:
            status = "external_only"
        else:
            status = "local_only"
        rows.append({
            "kind": kind, "address": f"{addr[:2]}:{addr[2:]}",
            "status": status, "local_names": local_names, "external_names": external_names,
        })
    categories = {key: sum(row["status"] == key for row in rows) for key in
                  ("same_name", "different_names", "external_only", "local_only")}
    return {
        "schema_version": 1,
        "local_source": "analysis/generated/symbols.json (docs/SYMBOLS.md)",
        "external_source": "baldosa/uniracers-recomp",
        "external_commit": PIN,
        "interpretation": "Address matches and naming differences are independent research leads, never verified equivalence.",
        "skipped_local_unparseable_rows": skipped,
        "counts": categories,
        "rows": rows,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, help="write full JSON report (default prints a compact summary)")
    p.add_argument("--differences", action="store_true",
                   help="print only overlapping addresses with different names")
    args = p.parse_args()
    local = json.loads(LOCAL.read_text(encoding="utf-8"))
    if local.get("schema_version") != 1:
        raise SystemExit("unsupported local symbol schema")
    report = crosswalk(local["entries"], load_external())
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print("Independent baldosa/local symbol crosswalk:", json.dumps(report["counts"], sort_keys=True))
        print("Unparseable local address rows:", report["skipped_local_unparseable_rows"])
        if args.differences:
            for row in report["rows"]:
                if row["status"] == "different_names":
                    print(f"{row['kind']} {row['address']}: local={row['local_names']} external={row['external_names']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
