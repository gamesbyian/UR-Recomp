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
RACE_RENDER_START = 0x83F0BB
RACE_RENDER_END = 0x83F295
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


def occupancy_scan_positions(header: bytes) -> list[dict]:
    """30 logical cells: five six-cell majors, MSB-first; final two bits excluded."""
    scan = []
    scan_index = 0
    for byte_index, value in enumerate(header):
        low_bit = 2 if byte_index == 3 else 0
        for bit_in_byte in range(7, low_bit - 1, -1):
            scan.append({
                "scan_index": scan_index,
                "major_slot": scan_index // 6,
                "minor_slot": scan_index % 6,
                "byte_index": byte_index,
                "bit_in_byte": bit_in_byte,
                "global_lsb_bit": byte_index * 8 + bit_in_byte,
                "set": bool(value & (1 << bit_in_byte)),
            })
            scan_index += 1
    assert len(scan) == 30
    return scan


def table_boundary_scan(rom: bytes) -> dict:
    max_id = ((0x10000 - FRAME_TABLE) // 3) - 2
    comparable = 0
    match30 = 0
    match32 = 0
    control_nonzero = 0
    control_nonzero_examples = []
    for frame_id in range(max_id + 1):
        try:
            ptr, _ = frame_pointer(rom, frame_id)
            nxt, _ = frame_pointer(rom, frame_id + 1)
        except (IndexError, ValueError):
            continue
        if (ptr >> 16) != (nxt >> 16):
            continue
        length = (nxt & 0xFFFF) - (ptr & 0xFFFF)
        if length < 4 or length > 68 or (length - 4) % 2:
            continue
        header = read_linear(rom, ptr, 4)
        words = (length - 4) // 2
        occ30 = sum(cell["set"] for cell in occupancy_scan_positions(header))
        all32 = sum(x.bit_count() for x in header)
        comparable += 1
        match30 += words == occ30
        match32 += words == all32
        ctl = header[3] & 0x03
        if ctl:
            control_nonzero += 1
            if len(control_nonzero_examples) < 12:
                control_nonzero_examples.append({
                    "frame_id": f"0x{frame_id:04X}",
                    "header_hex": header.hex(),
                    "control_low2": ctl,
                    "word_count": words,
                    "occupancy30_popcount": occ30,
                    "all32_popcount": all32,
                    "matches_30": words == occ30,
                    "matches_32": words == all32,
                })
    return {
        "comparable_monotonic_records": comparable,
        "matches_30_cell_popcount": match30,
        "matches_all_32_popcount": match32,
        "control_low2_nonzero_records": control_nonzero,
        "control_low2_examples": control_nonzero_examples,
    }


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
    scan = occupancy_scan_positions(header)
    occupied = [cell for cell in scan if cell["set"]]
    scan_mapping = []
    for i, cell in enumerate(occupied):
        if i >= len(words):
            break
        word = words[i]
        scan_mapping.append({
            **cell,
            "word_index": i,
            "word": f"0x{word:04X}",
            "word_high_byte": word >> 8,
            "word_low_byte": word & 0xFF,
            "staged_1645_value": f"0x{(0x8000 | ((word >> 8) << 5)) & 0xFFFF:04X}",
            "staged_15a1_value": f"0x{0x27 + ((word & 0x00FC) >> 2):04X}",
            "word_low2_unresolved": word & 0x03,
        })
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
        "occupancy_scan_order": "byte0 bit7..0, byte1 bit7..0, byte2 bit7..0, byte3 bit7..2; five groups of six",
        "control_low2": header[3] & 0x03,
        "occupancy_cells_set": len(occupied),
        "scan_mapping": scan_mapping,
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
    race_render = read_linear(rom, RACE_RENDER_START, RACE_RENDER_END - RACE_RENDER_START + 1)
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
        "race_render_body": {
            "start": "83:F0BB",
            "end": "83:F295",
            "length": len(race_render),
            "sha256": hashlib.sha256(race_render).hexdigest(),
            "hex": race_render.hex(),
        },
        "table_boundary_scan": table_boundary_scan(rom),
        "static_decode_proof": {
            "header_grouping": "83:F338..F3C6 and 83:F441..F4CF reshape the 30 MSB-first header bits into five six-cell major groups; byte3 bits1..0 are not included in these masks.",
            "prefix_count": "83:F2D1..F2F5 and 83:F30A..F32E test 04,08,10,20,40,80 and add two bytes per set bit for a mode-selected leading group.",
            "piece_consumption": "83:F1AE initializes $28=$8000; 83:F1DC..F270 shifts it right one position per constructed slot. Occupied slots read one 16-bit packed word and increment the selected record pointer twice.",
            "word_fields": "83:F20F..F227 stages high_byte*32 | $8000 at $1645,Y and $27+((low_byte&$FC)>>2) at $15A1,Y. Low-byte bits1..0 are not named by this proof.",
            "oam_layer": "82:ACA5 is a later OAM composition layer; packed occupancy records feed generated/staged racer tile content beneath stable OAM tile identities rather than mapping one-record-per-OAM-entry.",
        },
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
