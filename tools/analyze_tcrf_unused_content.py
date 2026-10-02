#!/usr/bin/env python3
"""Reconcile fixed-offset TCRF Uniracers claims against a canonical ROM."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROM_SIZE = 0x200000
VERSION_OFFSET = 0x18000
BUILD_DATE_OFFSET = 0x0541
COMBO_SET_OFFSET = 0x0BD679

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def lorom_to_file(bank: int, address: int) -> int:
    if address < 0x8000:
        raise ValueError("LoROM ROM address must be >= $8000")
    return ((bank & 0x7F) * 0x8000) + (address - 0x8000)

def ascii_runs(data: bytes, minimum: int = 4) -> list[dict]:
    rows: list[dict] = []
    start: int | None = None
    for i, value in enumerate(data + b"\x00"):
        printable = 0x20 <= value <= 0x7E
        if printable and start is None:
            start = i
        elif not printable and start is not None:
            if i - start >= minimum:
                rows.append({
                    "offset": start,
                    "length": i - start,
                    "text": data[start:i].decode("ascii"),
                })
            start = None
    return rows

def window(rom: bytes, offset: int, length: int) -> dict:
    blob = rom[offset:offset + length]
    return {
        "offset": offset,
        "offset_hex": f"0x{offset:06X}",
        "length": len(blob),
        "sha256": sha256(blob),
        "hex": blob.hex(),
        "ascii_runs": ascii_runs(blob),
    }

def analyze(rom: bytes) -> dict:
    if len(rom) != ROM_SIZE:
        raise ValueError(f"expected {ROM_SIZE} byte ROM, got {len(rom)}")
    version = rom[VERSION_OFFSET:VERSION_OFFSET + 32]
    version_text = version.split(b"\x00", 1)[0].decode("ascii", "replace")
    mapped = lorom_to_file(0x83, 0x8000)
    return {
        "schema_version": 1,
        "purpose": "Mechanically reconcile fixed-offset claims from TCRF's Uniracers article against the canonical USA ROM.",
        "rom": {"size": len(rom), "sha256": sha256(rom)},
        "claims": {
            "bank_83_8000_mapping": {
                "cpu_address": "83:8000",
                "file_offset": mapped,
                "file_offset_hex": f"0x{mapped:06X}",
                "matches_reported_version_offset": mapped == VERSION_OFFSET,
            },
            "version_string": {
                "reported_offset": VERSION_OFFSET,
                "reported_offset_hex": f"0x{VERSION_OFFSET:06X}",
                "decoded": version_text,
                "starts_with_ASJIver3_30": version.startswith(b"ASJIver3.30"),
                "window": window(rom, VERSION_OFFSET, 64),
            },
            "build_date_area": {
                "reported_offset": BUILD_DATE_OFFSET,
                "reported_offset_hex": f"0x{BUILD_DATE_OFFSET:06X}",
                "window": window(rom, BUILD_DATE_OFFSET, 128),
            },
            "unused_combo_message_set_9": {
                "reported_offset": COMBO_SET_OFFSET,
                "reported_offset_hex": f"0x{COMBO_SET_OFFSET:06X}",
                "window": window(rom, COMBO_SET_OFFSET, 256),
                "status": "fingerprinted_only_pending_table-structure reconciliation",
            },
        },
        "interpretation": {
            "version_and_antipiracy_link": (
                "LoROM CPU address 83:8000 maps exactly to file offset 0x18000. "
                "If the reported SRAM anti-piracy comparison reads ROM 83:8000, "
                "it is reading from the same location as the reported ASJIver3.30 payload."
            ),
            "limitations": [
                "Fixed-offset presence does not by itself prove runtime reachability.",
                "The Error Tour, boot-graphic overwrite, combo-message table semantics, and music selector reachability require separate structural or runtime checks.",
            ],
        },
    }

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    report = analyze(args.rom.read_bytes())
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
