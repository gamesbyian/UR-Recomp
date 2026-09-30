#!/usr/bin/env python3
"""Inventory an IPS patch and optionally compare records against a LoROM image.\n\nUsed by the Canoe compatibility-patch archaeology workflow; it deliberately\nkeeps IPS parsing independent of any disassembler.\n"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def parse_ips(data: bytes) -> list[dict]:
    if not data.startswith(b"PATCH"):
        raise ValueError("missing IPS PATCH header")
    pos = 5
    rows = []
    while True:
        if data[pos:pos + 3] == b"EOF":
            pos += 3
            break
        if pos + 5 > len(data):
            raise ValueError("truncated IPS record header")
        offset = int.from_bytes(data[pos:pos + 3], "big")
        size = int.from_bytes(data[pos + 3:pos + 5], "big")
        pos += 5
        if size == 0:
            if pos + 3 > len(data):
                raise ValueError("truncated IPS RLE record")
            run = int.from_bytes(data[pos:pos + 2], "big")
            value = data[pos + 2]
            pos += 3
            payload = bytes([value]) * run
            kind = "rle"
        else:
            if pos + size > len(data):
                raise ValueError("truncated IPS literal record")
            payload = data[pos:pos + size]
            pos += size
            kind = "literal"
        rows.append({
            "offset": offset,
            "offset_hex": f"0x{offset:06X}",
            "length": len(payload),
            "kind": kind,
            "data_hex": payload.hex(" "),
        })
    if pos != len(data):
        raise ValueError(f"unexpected {len(data)-pos} byte(s) after EOF")
    return rows


def lorom_cpu(offset: int) -> str:
    bank = (offset // 0x8000) & 0x7F
    addr = 0x8000 + (offset % 0x8000)
    return f"{bank:02X}:{addr:04X}"


def analyze(patch: bytes, rom: bytes | None = None, context: int = 8) -> dict:
    rows = parse_ips(patch)
    for row in rows:
        row["lorom_cpu"] = lorom_cpu(row["offset"])
        if rom is not None:
            start = row["offset"]
            end = start + row["length"]
            if end > len(rom):
                raise ValueError(f"record {row['offset_hex']} extends past ROM")
            row["original_hex"] = rom[start:end].hex(" ")
            a = max(0, start - context)
            b = min(len(rom), end + context)
            row["context_start_hex"] = f"0x{a:06X}"
            row["original_context_hex"] = rom[a:b].hex(" ")
    return {
        "schema_version": 1,
        "patch_size": len(patch),
        "patch_sha256": hashlib.sha256(patch).hexdigest(),
        "record_count": len(rows),
        "records": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("patch", type=Path)
    ap.add_argument("--rom", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--context", type=int, default=8)
    args = ap.parse_args()
    report = analyze(
        args.patch.read_bytes(),
        args.rom.read_bytes() if args.rom else None,
        context=args.context,
    )
    print(f"records={report['record_count']} patch_sha256={report['patch_sha256']}")
    for row in report["records"]:
        before = f" original={row['original_hex']}" if "original_hex" in row else ""
        context = (
            f" context@{row['context_start_hex']}={row['original_context_hex']}"
            if "original_context_hex" in row else ""
        )
        print(
            f"{row['offset_hex']} {row['lorom_cpu']} len={row['length']} "
            f"patched={row['data_hex']}{before}{context}"
        )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
