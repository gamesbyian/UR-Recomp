#!/usr/bin/env python3
"""Inspect the standard SNES CPU->SPC upload stream used by SNESRecomp HLE.

Stream grammar:
    repeated:
        uint16 little-endian payload_length
        uint16 little-endian APU target
        payload[payload_length]
    terminator:
        payload_length == 0
        target field is the final SPC PC used by IPL-style first upload

For later live transfers the terminator target may be semantically benign, but
it is still part of the serialized stream.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def parse_stream(data: bytes, start: int = 0, max_blocks: int = 512) -> dict:
    cursor = start
    blocks = []
    terminator = None

    for index in range(max_blocks):
        if cursor + 4 > len(data):
            return {
                "schema_version": 1,
                "start": start,
                "blocks": blocks,
                "terminator": terminator,
                "complete": False,
                "stop_reason": "truncated_header",
                "next_offset": cursor,
            }

        length = data[cursor] | (data[cursor + 1] << 8)
        target = data[cursor + 2] | (data[cursor + 3] << 8)
        header_offset = cursor
        cursor += 4

        if length == 0:
            terminator = {
                "header_offset": header_offset,
                "target_final_pc": target,
                "target_final_pc_hex": f"0x{target:04X}",
            }
            return {
                "schema_version": 1,
                "start": start,
                "blocks": blocks,
                "terminator": terminator,
                "complete": True,
                "stop_reason": "terminator",
                "next_offset": cursor,
            }

        payload_start = cursor
        payload_end = cursor + length
        available = max(0, min(len(data), payload_end) - payload_start)
        payload = data[payload_start : min(payload_end, len(data))]
        complete_payload = payload_end <= len(data)
        row = {
            "index": index,
            "header_offset": header_offset,
            "header_offset_hex": f"0x{header_offset:X}",
            "length": length,
            "length_hex": f"0x{length:04X}",
            "target": target,
            "target_hex": f"0x{target:04X}",
            "payload_start": payload_start,
            "payload_end_exclusive": payload_end,
            "available_payload_bytes": available,
            "payload_complete": complete_payload,
            "payload_sha256": (
                hashlib.sha256(payload).hexdigest() if complete_payload else None
            ),
        }
        blocks.append(row)
        if not complete_payload:
            return {
                "schema_version": 1,
                "start": start,
                "blocks": blocks,
                "terminator": None,
                "complete": False,
                "stop_reason": "truncated_payload",
                "next_offset": payload_start + available,
            }
        cursor = payload_end

    return {
        "schema_version": 1,
        "start": start,
        "blocks": blocks,
        "terminator": None,
        "complete": False,
        "stop_reason": "max_blocks",
        "next_offset": cursor,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("binary", type=Path)
    ap.add_argument("--offset", type=lambda x: int(x, 0), default=0)
    ap.add_argument("--max-blocks", type=int, default=512)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    data = args.binary.read_bytes()
    if args.offset < 0 or args.offset > len(data):
        raise SystemExit("offset outside input")
    report = parse_stream(data, args.offset, args.max_blocks)

    print(
        f"blocks={len(report['blocks'])} "
        f"complete={report['complete']} "
        f"reason={report['stop_reason']} "
        f"next=0x{report['next_offset']:X}"
    )
    for row in report["blocks"]:
        print(
            f"  #{row['index']:02d} "
            f"len={row['length']} "
            f"target={row['target_hex']} "
            f"payload=0x{row['payload_start']:X}-"
            f"0x{row['payload_end_exclusive'] - 1:X} "
            f"complete={row['payload_complete']}"
        )
    if report["terminator"]:
        print(
            "  terminator final_pc="
            + report["terminator"]["target_final_pc_hex"]
        )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
