#!/usr/bin/env python3
"""Inspect the extended Uniracers audio-record prefix beyond package-table IDs.

The six package tables only reference records 0x00..0x31, but APU setup callers
directly request later records through at least 0x42. This tool parses the same
contiguous length-prefixed pool through 0x42 and exposes compact framing bytes
for 0x32..0x42 without requiring SPC reference material.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from tools.inspect_audio_block_pool import parse_block_pool
except ModuleNotFoundError:
    from inspect_audio_block_pool import parse_block_pool


def build_report(rom: bytes, first: int = 0x32, last: int = 0x42) -> dict:
    pool = parse_block_pool(rom, count=last + 1)
    rows = []
    for block in pool["blocks"][first:last + 1]:
        off = int(block["file_offset"], 16)
        total = block["total_length"]
        record = rom[off:off + total]
        payload = record[2:]
        prefix = payload[:16]
        rows.append({
            "id": block["id"],
            "id_hex": block["id_hex"],
            "cpu_address": block["cpu_address"],
            "file_offset": block["file_offset"],
            "total_length": total,
            "payload_length": block["payload_length"],
            "payload_prefix_hex": prefix.hex(" "),
            "first_word_le": int.from_bytes(payload[:2], "little") if len(payload) >= 2 else None,
            "second_word_le": int.from_bytes(payload[2:4], "little") if len(payload) >= 4 else None,
            "bytes_after_four_prefix_hex": payload[4:20].hex(" "),
        })
    song_rows = [row for row in rows if 0x38 <= row["id"] <= 0x42]
    song_headers = sorted({(row["first_word_le"], row["second_word_le"]) for row in song_rows})
    return {
        "schema_version": 2,
        "pool_start_cpu": pool["pool_start_cpu"],
        "parsed_record_count": last + 1,
        "first_extended_id": f"0x{first:02X}",
        "last_extended_id": f"0x{last:02X}",
        "song_family_header": {
            "ids": [row["id_hex"] for row in song_rows],
            "unique_word_pairs": [[a, b] for a, b in song_headers],
            "uniform": len(song_headers) == 1,
            "first_word_le": song_headers[0][0] if len(song_headers) == 1 else None,
            "second_word_le": song_headers[0][1] if len(song_headers) == 1 else None,
            "second_word_hex": f"0x{song_headers[0][1]:04X}" if len(song_headers) == 1 else None,
        },
        "records": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = build_report(args.rom.read_bytes())
    for row in report["records"]:
        print(
            f"{row['id_hex']} {row['cpu_address']} payload={row['payload_length']} "
            f"w0=0x{row['first_word_le']:04X} w1=0x{row['second_word_le']:04X} "
            f"prefix={row['payload_prefix_hex']}"
        )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
