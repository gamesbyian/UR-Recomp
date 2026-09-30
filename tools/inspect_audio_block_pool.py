#!/usr/bin/env python3
"""Inspect Uniracers' ROM-side APU block pool and 64-byte package tables.

The retail transfer resolver at 02:812A maps numeric block IDs onto a contiguous
length-prefixed packed record pool beginning at CPU 10:8000. Each record's first
little-endian word is its total length including that two-byte header. Direct
setup callers prove the resolver is used through at least ID 0x42.

APU_StreamTransfer at 02:82A9 consumes 64-byte package tables whose populated
entries use only the 0x00-0x31 prefix (or 0xFF sentinels). DEFAULT_BLOCK_COUNT
therefore names the package-table block universe, not the full resolver range.
This tool makes that package prefix and the six tables explicit; callers may
request a larger count when inspecting later records.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

DEFAULT_POOL_CPU = 0x108000
DEFAULT_BLOCK_COUNT = 0x32
DEFAULT_TABLES = (0x03FAD5, 0x03FB15, 0x03FB55, 0x03FB95, 0x03FBD5, 0x03FC15)


def parse_cpu(value: str) -> int:
    value = value.strip().replace(":", "")
    return int(value, 16)


def lorom_file_offset(cpu: int) -> int:
    bank = (cpu >> 16) & 0x7F
    addr = cpu & 0xFFFF
    if addr < 0x8000:
        raise ValueError(f"LoROM CPU address must be in high half: {cpu:06X}")
    return bank * 0x8000 + (addr - 0x8000)


def file_to_cpu(offset: int) -> int:
    bank = offset // 0x8000
    addr = 0x8000 + (offset % 0x8000)
    return (bank << 16) | addr


def parse_block_pool(rom: bytes, *, pool_cpu: int = DEFAULT_POOL_CPU, count: int = DEFAULT_BLOCK_COUNT) -> dict:
    cursor = lorom_file_offset(pool_cpu)
    start = cursor
    blocks = []
    for block_id in range(count):
        if cursor + 2 > len(rom):
            raise ValueError(f"block {block_id:02X} header outside ROM at {cursor:06X}")
        total_len = int.from_bytes(rom[cursor:cursor + 2], "little")
        if total_len < 2 or cursor + total_len > len(rom):
            raise ValueError(f"implausible block {block_id:02X} length {total_len} at {cursor:06X}")
        record = rom[cursor:cursor + total_len]
        payload = record[2:]
        blocks.append({
            "id": block_id,
            "id_hex": f"0x{block_id:02X}",
            "cpu_address": f"0x{file_to_cpu(cursor):06X}",
            "file_offset": f"0x{cursor:06X}",
            "total_length": total_len,
            "payload_length": len(payload),
            "record_sha256": hashlib.sha256(record).hexdigest(),
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
            "payload_prefix_hex": payload[:32].hex(" "),
            "payload_suffix_hex": payload[-16:].hex(" "),
        })
        cursor += total_len
    return {
        "pool_start_cpu": f"0x{pool_cpu:06X}",
        "pool_start_file_offset": f"0x{start:06X}",
        "pool_end_file_offset": f"0x{cursor:06X}",
        "pool_byte_length": cursor - start,
        "blocks": blocks,
    }


def parse_selector_table(rom: bytes, cpu: int, blocks: list[dict]) -> dict:
    off = lorom_file_offset(cpu)
    raw = rom[off:off + 64]
    if len(raw) != 64:
        raise ValueError(f"selector table {cpu:06X} truncated")
    ids = [value for value in raw if value != 0xFF]
    if any(value >= len(blocks) for value in ids):
        raise ValueError(f"selector table {cpu:06X} references block outside parsed pool")
    return {
        "cpu_address": f"0x{cpu:06X}",
        "file_offset": f"0x{off:06X}",
        "bytes_hex": raw.hex(" "),
        "block_ids": ids,
        "block_ids_hex": [f"0x{x:02X}" for x in ids],
        "non_ff_count": len(ids),
        "unique_non_ff_count": len(set(ids)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "selected_payload_bytes": sum(blocks[x]["payload_length"] for x in ids),
        "expected_port3_bytes_including_64_selectors": 64 + sum(blocks[x]["payload_length"] for x in ids),
    }


def build_report(rom: bytes, *, pool_cpu: int = DEFAULT_POOL_CPU, count: int = DEFAULT_BLOCK_COUNT, table_cpus=DEFAULT_TABLES) -> dict:
    pool = parse_block_pool(rom, pool_cpu=pool_cpu, count=count)
    tables = [parse_selector_table(rom, cpu, pool["blocks"]) for cpu in table_cpus]
    union = sorted({x for table in tables for x in table["block_ids"]})
    return {
        "schema_version": 1,
        "canonical_rom_sha256": hashlib.sha256(rom).hexdigest(),
        **{k: v for k, v in pool.items() if k != "blocks"},
        "block_count": len(pool["blocks"]),
        "blocks": pool["blocks"],
        "selector_tables": tables,
        "selector_id_union": union,
        "selector_id_union_hex": [f"0x{x:02X}" for x in union],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--pool-cpu", type=parse_cpu, default=DEFAULT_POOL_CPU)
    ap.add_argument("--block-count", type=lambda x: int(x, 0), default=DEFAULT_BLOCK_COUNT)
    ap.add_argument("--selector-table", action="append", type=parse_cpu, dest="tables")
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = build_report(
        args.rom.read_bytes(),
        pool_cpu=args.pool_cpu,
        count=args.block_count,
        table_cpus=tuple(args.tables) if args.tables else DEFAULT_TABLES,
    )
    print(f"blocks={report['block_count']} pool_bytes={report['pool_byte_length']} union={len(report['selector_id_union'])}")
    for row in report["selector_tables"]:
        print(
            f"  {row['cpu_address']}: ids={row['non_ff_count']} "
            f"payload={row['selected_payload_bytes']} port3={row['expected_port3_bytes_including_64_selectors']}"
        )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
