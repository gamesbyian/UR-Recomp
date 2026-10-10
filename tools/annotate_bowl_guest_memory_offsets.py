#!/usr/bin/env python3
"""Annotate read-only Bowl tally WRAM disagreement addresses from pinned RAM map.

Input is the *offset-only* report from the existing original/native
tally-phase producer. Never reads, stores or redistributes guest memory
contents, and never treats tentative reverse-engineered names as proven
CPU/NMI/physics causality.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAM_SYMBOLS = ROOT / (
    "reference/imported/reverse-engineering/baldosa-uniracers-recomp/decomp/ram.txt"
)
HEX_OFFSET = re.compile(r"0x[0-9A-Fa-f]{5}$")


def parse_ram_symbols(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split(";", 1)[0].split()
        if len(parts) < 3 or not re.fullmatch(r"[0-9A-Fa-f]{6}", parts[0]):
            raise ValueError("invalid pinned RAM declaration")
        addr, symbol, length = parts[:3]
        if not length.isdigit():
            raise ValueError("invalid pinned RAM span length")
        bank = int(addr[:2], 16)
        if bank not in (0x7E, 0x7F):
            continue
        offset = int(addr[2:], 16) + (bank - 0x7E) * 0x10000
        size = int(length)
        if size <= 0 or offset + size > 0x20000:
            raise ValueError("invalid pinned WRAM span")
        rows.append({"name": symbol, "start": offset, "size": size})
    return rows


def lookup(offset: int, symbols: list[dict]) -> dict:
    matches = [row for row in symbols
               if row["start"] <= offset < row["start"] + row["size"]]
    matches.sort(key=lambda x: (x["size"], abs(offset - x["start"]),
                                x["name"]))
    exact = [x["name"] for x in matches if x["start"] == offset]
    return {
        "offset": f"0x{offset:05X}",
        "snes_wram": f"{0x7E + offset // 0x10000:02X}:{offset % 0x10000:04X}",
        "exact_start_symbols": exact,
        "most_specific_containing_symbols": [
            {"name": x["name"], "span_bytes": x["size"],
             "offset_inside_symbol": offset - x["start"]}
            for x in matches[:4]],
        "interpretation": "source labels, not validated active runtime ownership",
    }


def annotate(report: dict, symbols: list[dict]) -> dict:
    if report.get("schema") != "UR-QA01-BOWL-TALLY-ANCHORED-PHASE/1":
        raise ValueError("not a full Bowl tally phase offset report")
    if report.get("release_complete_event_credit") != 0:
        raise ValueError("source-only annotation must retain zero acceptance")
    if report.get("retains_raw_guest_memory") is not False:
        raise ValueError("input must attest no raw guest contents retained")
    if report.get("offset_profile_cap_per_memory_class") != 128:
        raise ValueError("unrecognized bounded offset profile")
    samples = report.get("same_host_frame_samples")
    if not isinstance(samples, list) or len(samples) != 8:
        raise ValueError("require eight source-observed tally-relative samples")
    result = []
    for row in samples:
        field = row.get("differing_byte_offsets_by_memory_class", {}).get("wram")
        if not isinstance(field, dict):
            raise ValueError("missing WRAM offset profile")
        total, addresses, truncated = (field.get("total"),
                                       field.get("addresses"),
                                       field.get("truncated"))
        if (type(total) is not int or total < 0 or total > 0x20000
                or type(truncated) is not bool or not isinstance(addresses, list)
                or len(addresses) != min(total, 128)
                or truncated != (total > 128)):
            raise ValueError("inconsistent bounded WRAM difference profile")
        offsets = []
        for value in addresses:
            if not isinstance(value, str) or not HEX_OFFSET.fullmatch(value):
                raise ValueError("not a WRAM offset")
            offset = int(value, 16)
            if offset >= 0x20000 or f"0x{offset:05X}" != value:
                raise ValueError("noncanonical or out-of-range WRAM offset")
            offsets.append(offset)
        if offsets != sorted(set(offsets)):
            raise ValueError("offsets must be unique and ascending")
        if row.get("different_guest_bytes", {}).get("wram") != total:
            raise ValueError("offset count does not match full-memory delta")
        result.append({
            "tally_relative_frame": row["offset_from_actual_tally_host_frame"],
            "absolute_host_frame": row["absolute_host_frame"],
            "wram_offset_count": total,
            "address_profile_truncated": truncated,
            "mapped_addresses": [lookup(offset, symbols) for offset in offsets],
        })
    return {
        "schema": "UR-QA01-BOWL-WRAM-OFFSET-SOURCE-LABELS/1",
        "origin": "eight original/native Bowl same-host guest WRAM snapshots",
        "symbol_origin": str(RAM_SYMBOLS.relative_to(ROOT)),
        "frames": result,
        "any_incomplete_address_profile": any(
            r["address_profile_truncated"] for r in result),
        "read_only": True,
        "raw_guest_memory_included": False,
        "confidence": "tentative reverse-engineered symbol labels only",
        "release_complete_event_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", type=Path, required=True,
                    help="bowl-report.json from opted-in address-offset CI")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    source = json.loads(args.report.read_text(encoding="utf-8"))
    phase = source.get("tally_anchored_guest_phase", source)
    labelled = annotate(phase, parse_ram_symbols(RAM_SYMBOLS.read_text()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(labelled, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "samples": len(labelled["frames"]),
        "incomplete_address_profile": labelled["any_incomplete_address_profile"],
        "release_complete_event_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
