#!/usr/bin/env python3
"""Reconcile fixed-offset TCRF Uniracers unused-content claims against a ROM."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def lorom_file_offset(cpu_address: int) -> int:
    bank = (cpu_address >> 16) & 0xFF
    address = cpu_address & 0xFFFF
    if address < 0x8000:
        raise ValueError(f"not a LoROM ROM-window address: {cpu_address:06X}")
    return ((bank & 0x7F) * 0x8000) + (address & 0x7FFF)


def printable_runs(data: bytes, min_length: int = 4) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    start = None
    for i, b in enumerate(data + b"\x00"):
        printable = 0x20 <= b <= 0x7E
        if printable and start is None:
            start = i
        elif not printable and start is not None:
            if i - start >= min_length:
                out.append({
                    "relative_offset": start,
                    "length": i - start,
                    "text": data[start:i].decode("ascii"),
                })
            start = None
    return out


def all_occurrences(data: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    start = 0
    while True:
        pos = data.find(needle, start)
        if pos < 0:
            return offsets
        offsets.append(pos)
        start = pos + 1


def window(data: bytes, offset: int, length: int) -> dict[str, object]:
    chunk = data[offset:offset + length]
    return {
        "offset": offset,
        "length": len(chunk),
        "sha256": hashlib.sha256(chunk).hexdigest(),
        "hex": chunk.hex(),
        "printable_runs": printable_runs(chunk),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    version = b"ASJIver3.30"
    version_offset = 0x18000
    build_date_offset = 0x541
    combo9_offset = 0x0BD679

    report = {
        "schema_version": 1,
        "rom": {
            "path": str(args.rom),
            "size": len(rom),
            "sha256": hashlib.sha256(rom).hexdigest(),
        },
        "claims": {
            "version_string": {
                "reported_file_offset": version_offset,
                "reported_cpu_address": "83:8000",
                "computed_lorom_file_offset": lorom_file_offset(0x838000),
                "expected_ascii": version.decode("ascii"),
                "bytes_at_offset_hex": rom[version_offset:version_offset + len(version)].hex(),
                "matches_expected": rom[version_offset:version_offset + len(version)] == version,
                "all_rom_occurrences": all_occurrences(rom, version),
            },
            "build_date_window": window(rom, build_date_offset, 96),
            "unused_combo_message_set_window": window(rom, combo9_offset, 160),
        },
        "string_searches": {
            key: all_occurrences(rom, needle)
            for key, needle in {
                "ASJIver3.30": b"ASJIver3.30",
                "Unavailable": b"Unavailable",
                "Error Tour": b"Error Tour",
                "used by decomp": b"used by decomp",
            }.items()
        },
        "interpretation": {
            "version_mapping_consistent": (
                lorom_file_offset(0x838000) == version_offset
                and rom[version_offset:version_offset + len(version)] == version
            ),
            "scope": (
                "This report mechanically validates fixed ROM offsets, byte windows and literal "
                "strings only. Runtime reachability, SRAM-copy behavior, graphics decode semantics "
                "and music selector behavior require separate evidence."
            ),
        },
    }

    payload = json.dumps(report, indent=2) + "\n"
    print(payload, end="")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
