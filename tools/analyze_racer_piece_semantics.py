#!/usr/bin/env python3
"""Inspect racer frame occupancy bits, packed words, and renderer code bytes.

This is deliberately a narrow evidence tool. It preserves exact encoded frame
bytes, exposes both candidate bit traversals without naming payload fields, and
emits comparative deltas for selected ordinary-race frames.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FRAME_TABLE = 0x208000
FRAME_BANK_BASE = 0x23
FRAME_IDS = (0x0540, 0x0542, 0x0544, 0x057E)
RENDERER_START = 0x83F2BB
RENDERER_END = 0x83F4D1


def lorom_offset(addr24: int) -> int:
    bank = (addr24 >> 16) & 0xFF
    addr = addr24 & 0xFFFF
    if addr < 0x8000:
        raise ValueError(f"not LoROM: {addr24:06X}")
    return ((bank & 0x7F) << 15) | (addr & 0x7FFF)


def read_linear(rom: bytes, addr24: int, length: int) -> bytes:
    out = bytearray()
    bank, addr = (addr24 >> 16) & 0xFF, addr24 & 0xFFFF
    for _ in range(length):
        out.append(rom[lorom_offset((bank << 16) | addr)])
        addr += 1
        if addr > 0xFFFF:
            bank = (bank + 1) & 0xFF
            addr = 0x8000
    return bytes(out)


def frame_pointer(rom: bytes, frame_id: int) -> tuple[int, bytes]:
    ent = read_linear(rom, FRAME_TABLE + frame_id * 3, 3)
    return (((ent[2] + FRAME_BANK_BASE) << 16) | int.from_bytes(ent[:2], "little")), ent


def set_bits(header: bytes) -> list[int]:
    return [i for i in range(32) if header[i // 8] & (1 << (i % 8))]


def frame_record(rom: bytes, frame_id: int) -> dict:
    ptr, ent = frame_pointer(rom, frame_id)
    nxt, _ = frame_pointer(rom, frame_id + 1)
    table_len = (nxt & 0xFFFF) - (ptr & 0xFFFF) if (nxt >> 16) == (ptr >> 16) else None
    header = read_linear(rom, ptr, 4)
    bits = set_bits(header)
    exact_len = 4 + 2 * len(bits)
    raw = read_linear(rom, ptr, exact_len)
    words = [int.from_bytes(raw[i:i+2], "little") for i in range(4, len(raw), 2)]
    rebuilt = header + b"".join(w.to_bytes(2, "little") for w in words)
    assert rebuilt == raw
    if table_len is not None:
        assert table_len == exact_len, (frame_id, table_len, exact_len)
    low = [{"bit": b, "word_index": i, "word": f"0x{words[i]:04X}"} for i, b in enumerate(bits)]
    high_bits = list(reversed(bits))
    high = [{"bit": b, "word_index": i, "word": f"0x{words[i]:04X}"} for i, b in enumerate(high_bits)]
    return {
        "frame_id": f"0x{frame_id:04X}",
        "pointer": f"{ptr:06X}",
        "pointer_entry_hex": ent.hex(),
        "header_hex": header.hex(),
        "set_bits": bits,
        "popcount": len(bits),
        "packed_words": [f"0x{x:04X}" for x in words],
        "record_length": exact_len,
        "table_bounded_length": table_len,
        "record_hex": raw.hex(),
        "record_sha256": hashlib.sha256(raw).hexdigest(),
        "roundtrip_equal": rebuilt == raw,
        "candidate_low_to_high": low,
        "candidate_high_to_low": high,
    }


def compare(a: dict, b: dict) -> dict:
    abit, bbit = set(a["set_bits"]), set(b["set_bits"])
    return {
        "a": a["frame_id"],
        "b": b["frame_id"],
        "bits_removed": sorted(abit - bbit),
        "bits_added": sorted(bbit - abit),
        "shared_bits": sorted(abit & bbit),
        "word_count_delta": b["popcount"] - a["popcount"],
        "a_words": a["packed_words"],
        "b_words": b["packed_words"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    rom = args.rom.read_bytes()
    frames = [frame_record(rom, fid) for fid in FRAME_IDS]
    byid = {x["frame_id"]: x for x in frames}
    renderer = read_linear(rom, RENDERER_START, RENDERER_END - RENDERER_START + 1)
    report = {
        "schema_version": 1,
        "purpose": "Finite correspondence evidence for racer frame header bits and packed piece words.",
        "frames": frames,
        "comparisons": [
            compare(byid["0x0540"], byid["0x0542"]),
            compare(byid["0x0542"], byid["0x0544"]),
            compare(byid["0x0540"], byid["0x057E"]),
        ],
        "renderer": {
            "start": "83:F2BB",
            "end": "83:F4D1",
            "length": len(renderer),
            "sha256": hashlib.sha256(renderer).hexdigest(),
            "hex": renderer.hex(),
        },
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
