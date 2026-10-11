#!/usr/bin/env python3
"""Search pinned Baldosa USA and malmazuke PAL research in one read-only overlay.

This tool is a bulk *discovery* index. No PAL address projection or upstream
name is an authoritative USA symbol, test oracle, or shipping gameplay change.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

from query_baldosa_symbols import PIN as BALDOSA_PIN, load as load_baldosa

ROOT = Path(__file__).resolve().parents[1]
MARK_ROOT = ROOT / "reference/imported/reverse-engineering/malmazuke-unirally-reconstruction/docs/map/static"
LINKS = ROOT / "analysis/data/malmazuke-pal-structural-links-20261010.json"
MARK_PIN = "42d444594641d23f5d3c15da7b7c454bb5180e43"
HEX = re.compile(r"^(?:\$|0[xX])?([0-9a-fA-F]{2}):?([0-9a-fA-F]{4})$")


def address(raw: str) -> str:
    """Normalize LoROM $00..$03 ROM mirrors, but never guess PAL/USA offsets."""
    if not isinstance(raw, str):
        raise ValueError("address must be a string")
    m = HEX.fullmatch(raw.strip())
    if not m:
        raise ValueError(f"invalid banked address: {raw!r}")
    bank, offset = int(m.group(1), 16), int(m.group(2), 16)
    if bank <= 3 and offset >= 0x8000:
        bank |= 0x80
    return f"{bank:02X}:{offset:04X}"


def mark_rows(native: dict, labels: list[dict], links: dict) -> list[dict]:
    """Join all indexed PAL native references and labels without inventing matches."""
    if not isinstance(native, dict) or not isinstance(native.get("addresses"), list):
        raise ValueError("malmazuke native-symbols must contain addresses")
    if not isinstance(labels, list) or links.get("schema_version") != 1:
        raise ValueError("malmazuke labels/links schema mismatch")
    if links.get("source", {}).get("commit") != MARK_PIN:
        raise ValueError("malmazuke structural links are not pinned to this source")
    rows: dict[str, dict] = {}

    def row_for(raw: str) -> dict:
        key = address(raw)
        if key not in rows:
            rows[key] = {
                "source": "malmazuke", "region": "PAL", "address": key,
                "name": "", "kind": "unknown", "description": "",
                "native": [], "source_records": [],
                "correspondence": {"status": "not-assessed"},
                "source_commit": MARK_PIN,
            }
        return rows[key]

    for entry in native["addresses"]:
        row = row_for(entry["address"])
        for ref in entry.get("native", []):
            if ref not in row["native"]:
                row["native"].append(ref)
    for entry in labels:
        row = row_for(entry["address"])
        # A label is a source observation and may be unknown or provisional.
        row["name"] = str(entry.get("label", ""))
        row["kind"] = str(entry.get("class", "unknown"))
        row["description"] = str(entry.get("comment", ""))
        for ref in entry.get("native", []):
            if ref not in row["native"]:
                row["native"].append(ref)
        for ref in entry.get("source_records", []):
            if ref not in row["source_records"]:
                row["source_records"].append(ref)
    seen_links = set()
    for entry in links.get("entries", []):
        key = address(entry["pal"])
        if key in seen_links:
            raise ValueError(f"duplicate PAL correspondence: {key}")
        seen_links.add(key)
        row = row_for(key)
        corr = entry["correspondence"].copy()
        if "usa" in corr:
            corr["usa"] = address(corr["usa"])
        row["correspondence"] = corr
        for ref in entry.get("mark_native", []):
            if ref not in row["native"]:
                row["native"].append(ref)
        if not row["name"]:
            row["name"] = entry.get("pal_label", "")
        if row["kind"] == "unknown":
            row["kind"] = entry.get("pal_symbol_class", "unknown")
    return sorted(rows.values(), key=lambda x: x["address"])


def baldosa_rows(entries: list[dict]) -> list[dict]:
    out = []
    for entry in entries:
        row = {
            "source": "baldosa", "region": "USA",
            "address": address(entry["address"]), "name": entry["name"],
            "kind": entry["kind"], "description": entry.get("description", ""),
            "source_commit": BALDOSA_PIN,
        }
        if "width" in entry:
            row["width"] = entry["width"]
        out.append(row)
    return out


def load() -> list[dict]:
    native = json.loads((MARK_ROOT / "native-symbols.json").read_text(encoding="utf-8"))
    labels = json.loads((MARK_ROOT / "labels.json").read_text(encoding="utf-8"))
    links = json.loads(LINKS.read_text(encoding="utf-8"))
    return sorted(baldosa_rows(load_baldosa()) + mark_rows(native, labels, links),
                  key=lambda x: (x["region"], x["address"], x["source"], x["name"]))


def search(rows: list[dict], *, exact: str | None = None,
           usa: str | None = None, pattern: str | None = None,
           source: str = "all", region: str = "both") -> list[dict]:
    """USA-candidate queries include only explicit code-region projections."""
    wanted = address(exact) if exact is not None else None
    target = address(usa) if usa is not None else None
    regex = re.compile(pattern, re.IGNORECASE) if pattern is not None else None
    result = []
    for row in rows:
        if source != "all" and source != row["source"]:
            continue
        if region != "both" and region != row["region"]:
            continue
        if wanted is not None and row["address"] != wanted:
            continue
        if target is not None:
            if row["region"] == "USA":
                if row["address"] != target:
                    continue
            else:
                corr = row.get("correspondence", {})
                if corr.get("status") != "structural-interval-candidate" or corr.get("usa") != target:
                    continue
        haystack = " ".join([
            row.get("name", ""), row.get("kind", ""), row.get("description", ""),
            *row.get("native", []), *row.get("source_records", []),
        ])
        if regex is not None and not regex.search(haystack):
            continue
        result.append(row)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selector = parser.add_mutually_exclusive_group()
    selector.add_argument("--address", help="literal PAL/USA address; displayed regions remain distinct")
    selector.add_argument("--usa-address", help="USA address plus explicitly projected PAL code candidates")
    parser.add_argument("--match", help="case-insensitive regex over names, comments and native references")
    parser.add_argument("--source", choices=("all", "baldosa", "malmazuke"), default="all")
    parser.add_argument("--region", choices=("both", "USA", "PAL"), default="both")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--summary", action="store_true", help="show full-corpus source counts")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")
    if not (args.address or args.usa_address or args.match or args.summary):
        parser.error("provide --address, --usa-address, --match or --summary")
    if args.usa_address and args.region == "PAL":
        parser.error("--usa-address with --region PAL excludes original USA matches; use both")
    try:
        found = search(load(), exact=args.address, usa=args.usa_address,
                       pattern=args.match, source=args.source, region=args.region)
    except (ValueError, re.error, KeyError, TypeError) as exc:
        parser.error(str(exc))
    counts = Counter(x["source"] for x in found)
    if args.summary:
        print(json.dumps({"matched": len(found), "by_source": dict(sorted(counts.items())),
                          "policy": "upstream research only; no automatic USA semantic promotion"},
                         indent=2))
        return 0
    selection = found[:args.limit]
    if args.json:
        print(json.dumps({
            "schema_version": 1, "upstream_pins": {"baldosa": BALDOSA_PIN, "malmazuke": MARK_PIN},
            "authority": "advisory; PAL offset candidates are never verified USA homologs",
            "matched": len(found), "truncated": len(selection) < len(found), "entries": selection,
        }, indent=2, ensure_ascii=False))
    else:
        print(f"Upstream advisory index: {len(found)} matches ({len(selection)} shown)")
        for row in selection:
            print(f"{row['source']} [{row['region']}] {row['address']} {row['kind']} {row['name']}")
            if row.get("description") and row["description"] != "unknown":
                print(f"  {row['description']}")
            for native_ref in row.get("native", [])[:4]:
                print(f"  native: {native_ref}")
            corr = row.get("correspondence", {})
            if corr.get("status") == "structural-interval-candidate":
                print(f"  USA *candidate only*: {corr['usa']} ({corr.get('region', '?')})")
            elif corr.get("status") != "not-assessed" and corr:
                print(f"  PAL/USA correspondence: {corr['status']}")
        if len(selection) < len(found):
            print(f"... {len(found) - len(selection)} more; increase --limit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
