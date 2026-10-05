#!/usr/bin/env python3
"""Compare ROM-side audio packages between USA and Europe retail builds."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from inspect_audio_block_pool import (
    DEFAULT_BLOCK_COUNT,
    DEFAULT_POOL_CPU,
    DEFAULT_TABLES,
    parse_block_pool,
    parse_selector_table,
)

USA = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
EUROPE = ROOT / "reference/roms/retail/Unirally_Europe.sfc"

EXPECTED_SHA256 = {
    "usa": "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
    "europe": "a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e",
}


def checked_rom(path: Path, label: str) -> bytes:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256[label]:
        raise ValueError(
            f"{label} retail SHA-256 mismatch: {digest} != "
            f"{EXPECTED_SHA256[label]}"
        )
    return data


def compare_blocks(usa_pool: dict, europe_pool: dict) -> list[dict]:
    out = []
    usa_blocks = usa_pool["blocks"]
    eur_blocks = europe_pool["blocks"]
    for idx in range(max(len(usa_blocks), len(eur_blocks))):
        u = usa_blocks[idx] if idx < len(usa_blocks) else None
        e = eur_blocks[idx] if idx < len(eur_blocks) else None
        row = {
            "id": idx,
            "id_hex": f"0x{idx:02X}",
            "usa_present": u is not None,
            "europe_present": e is not None,
        }
        if u and e:
            row.update(
                {
                    "record_identical": u["record_sha256"] == e["record_sha256"],
                    "payload_identical": u["payload_sha256"] == e["payload_sha256"],
                    "usa_total_length": u["total_length"],
                    "europe_total_length": e["total_length"],
                    "length_delta": e["total_length"] - u["total_length"],
                    "usa_record_sha256": u["record_sha256"],
                    "europe_record_sha256": e["record_sha256"],
                }
            )
        out.append(row)
    return out


def safe_selector_tables(rom: bytes, blocks: list[dict]) -> dict:
    rows = []
    errors = []
    for cpu in DEFAULT_TABLES:
        try:
            rows.append(parse_selector_table(rom, cpu, blocks))
        except Exception as exc:
            errors.append(
                {
                    "cpu_address": f"0x{cpu:06X}",
                    "error": str(exc),
                }
            )
    return {"tables": rows, "errors": errors}


def compare_selectors(usa: dict, europe: dict) -> list[dict]:
    eur_by_addr = {row["cpu_address"]: row for row in europe["tables"]}
    out = []
    for u in usa["tables"]:
        e = eur_by_addr.get(u["cpu_address"])
        out.append(
            {
                "cpu_address": u["cpu_address"],
                "europe_present_at_same_address": e is not None,
                "identical": bool(e and u["sha256"] == e["sha256"]),
                "usa_sha256": u["sha256"],
                "europe_sha256": e["sha256"] if e else None,
                "usa_block_ids_hex": u["block_ids_hex"],
                "europe_block_ids_hex": e["block_ids_hex"] if e else None,
            }
        )
    return out


def build_report(
    usa_data: bytes,
    europe_data: bytes,
) -> dict:
    usa_pool = parse_block_pool(
        usa_data, pool_cpu=DEFAULT_POOL_CPU, count=DEFAULT_BLOCK_COUNT
    )
    eur_pool = parse_block_pool(
        europe_data, pool_cpu=DEFAULT_POOL_CPU, count=DEFAULT_BLOCK_COUNT
    )
    blocks = compare_blocks(usa_pool, eur_pool)

    usa_selectors = safe_selector_tables(usa_data, usa_pool["blocks"])
    eur_selectors = safe_selector_tables(europe_data, eur_pool["blocks"])
    selectors = compare_selectors(usa_selectors, eur_selectors)

    pool_start = int(usa_pool["pool_start_file_offset"], 16)
    usa_pool_end = int(usa_pool["pool_end_file_offset"], 16)
    eur_pool_end = int(eur_pool["pool_end_file_offset"], 16)
    common_end = min(usa_pool_end, eur_pool_end)

    return {
        "schema_version": 1,
        "purpose": (
            "Mechanical comparison of the known ROM-side APU package pool and "
            "known USA selector-table addresses across both retail builds."
        ),
        "guardrail": (
            "Same-address selector mismatch or parse failure does not prove "
            "different music: PAL executable/data layout may relocate selectors. "
            "Block-pool identity is stronger because the pool is parsed from its "
            "known length-prefixed structure."
        ),
        "pool": {
            "cpu_start": f"0x{DEFAULT_POOL_CPU:06X}",
            "usa_start": usa_pool["pool_start_file_offset"],
            "usa_end": usa_pool["pool_end_file_offset"],
            "europe_start": eur_pool["pool_start_file_offset"],
            "europe_end": eur_pool["pool_end_file_offset"],
            "usa_byte_length": usa_pool["pool_byte_length"],
            "europe_byte_length": eur_pool["pool_byte_length"],
            "common_prefix_region_sha256": {
                "usa": hashlib.sha256(usa_data[pool_start:common_end]).hexdigest(),
                "europe": hashlib.sha256(
                    europe_data[pool_start:common_end]
                ).hexdigest(),
            },
        },
        "blocks": {
            "count": len(blocks),
            "identical_records": sum(
                1 for row in blocks if row.get("record_identical")
            ),
            "changed_ids": [
                row["id"]
                for row in blocks
                if row.get("record_identical") is False
            ],
            "rows": blocks,
        },
        "selector_tables": {
            "usa_parse_errors": usa_selectors["errors"],
            "europe_parse_errors": eur_selectors["errors"],
            "same_address_rows": selectors,
            "identical_same_address_count": sum(
                1 for row in selectors if row["identical"]
            ),
        },
    }


def markdown(report: dict) -> str:
    lines = [
        "# Regional Retail Audio Package Comparison",
        "",
        "Generated by tools/compare_regional_audio_packages.py.",
        "",
        report["guardrail"],
        "",
        "## Package pool",
        "",
        f"- parsed blocks: {report['blocks']['count']}",
        f"- byte-identical records: {report['blocks']['identical_records']}/"
        f"{report['blocks']['count']}",
        "- changed block IDs: "
        + (
            ", ".join(f"0x{x:02X}" for x in report["blocks"]["changed_ids"])
            if report["blocks"]["changed_ids"]
            else "none"
        ),
        f"- USA parsed range: {report['pool']['usa_start']}.."
        f"{report['pool']['usa_end']}",
        f"- Europe parsed range: {report['pool']['europe_start']}.."
        f"{report['pool']['europe_end']}",
        "",
        "## Known selector-table addresses",
        "",
        f"- identical at the six known USA addresses: "
        f"{report['selector_tables']['identical_same_address_count']}/6",
        f"- USA parse errors: {len(report['selector_tables']['usa_parse_errors'])}",
        f"- Europe parse errors: "
        f"{len(report['selector_tables']['europe_parse_errors'])}",
        "",
        "| address | identical | Europe present/parseable |",
        "|---|:---:|:---:|",
    ]
    for row in report["selector_tables"]["same_address_rows"]:
        lines.append(
            f"| {row['cpu_address']} | "
            f"{'yes' if row['identical'] else 'no'} | "
            f"{'yes' if row['europe_present_at_same_address'] else 'no'} |"
        )
    lines += [
        "",
        "## Interpretation rule",
        "",
        "If all 50 package records are byte-identical, the preserved ROM-side "
        "audio payload universe is strongly conserved even if PAL code relocates "
        "or rewrites selector tables. If package records differ, the changed IDs "
        "must be correlated to the existing SPC/package signatures before any "
        "regional audio presentation behavior is proposed.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--usa-rom", type=Path, default=USA)
    ap.add_argument("--europe-rom", type=Path, default=EUROPE)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()

    report = build_report(
        checked_rom(args.usa_rom, "usa"),
        checked_rom(args.europe_rom, "europe"),
    )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(markdown(report), encoding="utf-8")
    if not args.json_out and not args.md_out:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
