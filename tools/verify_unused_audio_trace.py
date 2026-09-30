#!/usr/bin/env python3
"""Verify that a counterfactual unused-song body was streamed through APU port $2143."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.inspect_audio_block_pool import parse_block_pool
except ModuleNotFoundError:
    from inspect_audio_block_pool import parse_block_pool


def expected_song_body(rom: bytes, selector: int) -> bytes:
    pool = parse_block_pool(rom, count=selector + 1)
    row = pool["blocks"][selector]
    off = int(row["file_offset"], 16)
    total = row["total_length"]
    record = rom[off:off + total]
    payload = record[2:]
    if len(payload) < 4:
        raise ValueError("audio record too short for song framing")
    if payload[:4] != bytes.fromhex("00 04 00 1d"):
        raise ValueError(
            f"selector 0x{selector:02X} does not use expected song framing: "
            f"{payload[:4].hex(' ')}"
        )
    return payload[4:]


def port3_stream(trace: dict) -> bytes:
    values = []
    for event in trace.get("events", []):
        address = event.get("address")
        if address is None:
            raw = event.get("address_hex")
            address = int(raw, 16) if raw is not None else None
        if address != 0x2143:
            continue
        value = event.get("value")
        if value is None:
            value = int(event["value_hex"], 16)
        values.append(int(value) & 0xFF)
    return bytes(values)


def verify(rom: bytes, trace: dict, selector: int) -> dict:
    expected = expected_song_body(rom, selector)
    stream = port3_stream(trace)
    pos = stream.find(expected)
    return {
        "schema_version": 1,
        "selector": selector,
        "selector_hex": f"0x{selector:02X}",
        "expected_body_length": len(expected),
        "expected_body_sha256": hashlib.sha256(expected).hexdigest(),
        "port_2143_bytes": len(stream),
        "port_2143_sha256": hashlib.sha256(stream).hexdigest(),
        "match_offset": pos if pos >= 0 else None,
        "match_offset_hex": f"0x{pos:X}" if pos >= 0 else None,
        "exact_body_found": pos >= 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("trace_json", type=Path)
    ap.add_argument("selector", type=lambda x: int(x, 0))
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = verify(
        args.rom.read_bytes(),
        json.loads(args.trace_json.read_text(encoding="utf-8")),
        args.selector,
    )
    print(json.dumps(report, indent=2))
    if not report["exact_body_found"]:
        return 1
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
