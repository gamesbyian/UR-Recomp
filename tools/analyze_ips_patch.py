#!/usr/bin/env python3
"""Inspect an IPS patch as reverse-engineering evidence.

The tool is deliberately ROM-agnostic. It can summarize an IPS patch on its own,
or, when given a local base image, report which writes actually change bytes and
what output image would result. It never modifies the base image in place.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


IPS_HEADER = b"PATCH"
IPS_EOF = b"EOF"


@dataclass(frozen=True)
class IpsRecord:
    offset: int
    data: bytes
    encoding: str

    @property
    def end(self) -> int:
        return self.offset + len(self.data)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_u24(data: bytes, offset: int) -> int:
    if offset + 3 > len(data):
        raise ValueError("truncated IPS 24-bit field")
    return int.from_bytes(data[offset : offset + 3], "big")


def _read_u16(data: bytes, offset: int) -> int:
    if offset + 2 > len(data):
        raise ValueError("truncated IPS 16-bit field")
    return int.from_bytes(data[offset : offset + 2], "big")


def parse_ips(data: bytes) -> tuple[list[IpsRecord], int | None]:
    if not data.startswith(IPS_HEADER):
        raise ValueError("not an IPS patch: missing PATCH header")

    cursor = len(IPS_HEADER)
    records: list[IpsRecord] = []
    truncate_to: int | None = None

    while True:
        if cursor + 3 > len(data):
            raise ValueError("truncated IPS patch before EOF marker")
        if data[cursor : cursor + 3] == IPS_EOF:
            cursor += 3
            remaining = len(data) - cursor
            if remaining == 3:
                truncate_to = _read_u24(data, cursor)
                cursor += 3
            elif remaining != 0:
                raise ValueError(f"unexpected {remaining} trailing byte(s) after IPS EOF")
            break

        record_offset = _read_u24(data, cursor)
        cursor += 3
        size = _read_u16(data, cursor)
        cursor += 2

        if size:
            end = cursor + size
            if end > len(data):
                raise ValueError("truncated IPS literal record")
            payload = data[cursor:end]
            cursor = end
            records.append(IpsRecord(record_offset, payload, "literal"))
            continue

        rle_size = _read_u16(data, cursor)
        cursor += 2
        if rle_size == 0:
            raise ValueError("invalid zero-length IPS RLE record")
        if cursor >= len(data):
            raise ValueError("truncated IPS RLE value")
        value = data[cursor]
        cursor += 1
        records.append(IpsRecord(record_offset, bytes([value]) * rle_size, "rle"))

    return records, truncate_to


def coalesce_ranges(records: Iterable[IpsRecord]) -> list[tuple[int, int]]:
    spans = sorted((record.offset, record.end) for record in records)
    if not spans:
        return []
    out: list[list[int]] = [[spans[0][0], spans[0][1]]]
    for start, end in spans[1:]:
        current = out[-1]
        if start <= current[1]:
            current[1] = max(current[1], end)
        else:
            out.append([start, end])
    return [(start, end) for start, end in out]


def lorom_cpu_address(file_offset: int, header_size: int = 0) -> str | None:
    """Map a file offset to a canonical FastROM/LoROM mirror ($80-$BF:$8000-$FFFF)."""
    rom_offset = file_offset - header_size
    if rom_offset < 0:
        return None
    bank_index = rom_offset // 0x8000
    if bank_index > 0x3F:
        return None
    addr = 0x8000 + (rom_offset % 0x8000)
    return f"{0x80 + bank_index:02X}:{addr:04X}"


def detect_header_size(base_size: int) -> int:
    mod = base_size % 0x8000
    if mod == 0:
        return 0
    if mod == 512:
        return 512
    raise ValueError(
        f"cannot infer copier-header size from {base_size} bytes; use --header-size 0 or 512"
    )


def apply_records(base: bytes, records: Iterable[IpsRecord], truncate_to: int | None) -> bytes:
    output = bytearray(base)
    for record in records:
        if record.offset < 0:
            raise ValueError("negative IPS offset")
        if record.end > len(output):
            output.extend(b"\x00" * (record.end - len(output)))
        output[record.offset : record.end] = record.data
    if truncate_to is not None:
        if truncate_to < 0:
            raise ValueError("negative IPS truncate size")
        if truncate_to < len(output):
            del output[truncate_to:]
        elif truncate_to > len(output):
            output.extend(b"\x00" * (truncate_to - len(output)))
    return bytes(output)


def analyze_patch(patch: bytes, base: bytes | None = None, header_size: int | None = None) -> dict:
    records, truncate_to = parse_ips(patch)
    if base is not None and header_size is None:
        header_size = detect_header_size(len(base))
    if header_size is None:
        header_size = 0
    if header_size not in (0, 512):
        raise ValueError("header size must be 0 or 512 bytes")

    coalesced = coalesce_ranges(records)
    summary: dict = {
        "schema_version": 1,
        "format": "IPS",
        "patch_size": len(patch),
        "patch_sha256": sha256(patch),
        "record_count": len(records),
        "literal_records": sum(record.encoding == "literal" for record in records),
        "rle_records": sum(record.encoding == "rle" for record in records),
        "encoded_write_bytes": sum(len(record.data) for record in records),
        "truncate_to": truncate_to,
        "header_size": header_size,
        "ranges": [
            {
                "start": start,
                "start_hex": f"0x{start:06X}",
                "end_exclusive": end,
                "end_exclusive_hex": f"0x{end:06X}",
                "length": end - start,
                "lorom_start": lorom_cpu_address(start, header_size),
                "lorom_end": lorom_cpu_address(end - 1, header_size),
            }
            for start, end in coalesced
        ],
        "records": [
            {
                "offset": record.offset,
                "offset_hex": f"0x{record.offset:06X}",
                "length": len(record.data),
                "encoding": record.encoding,
                "data_sha256": sha256(record.data),
                "lorom": lorom_cpu_address(record.offset, header_size),
            }
            for record in records
        ],
    }

    if base is not None:
        output = apply_records(base, records, truncate_to)
        actual_changed = 0
        for i in range(max(len(base), len(output))):
            before = base[i] if i < len(base) else None
            after = output[i] if i < len(output) else None
            if before != after:
                actual_changed += 1
        summary["base"] = {
            "size": len(base),
            "sha256": sha256(base),
        }
        summary["result"] = {
            "size": len(output),
            "sha256": sha256(output),
            "actual_changed_bytes": actual_changed,
        }

    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("patch", type=Path, help="IPS patch to inspect")
    ap.add_argument("--base", type=Path, help="optional local base image for actual-byte diffing")
    ap.add_argument(
        "--header-size",
        type=int,
        choices=(0, 512),
        help="override copier-header size; inferred from --base when omitted",
    )
    ap.add_argument("--output", type=Path, help="optional JSON report path")
    args = ap.parse_args()

    patch = args.patch.read_bytes()
    base = args.base.read_bytes() if args.base else None
    report = analyze_patch(patch, base=base, header_size=args.header_size)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
