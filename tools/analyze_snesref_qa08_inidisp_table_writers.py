#!/usr/bin/env python3
"""Executed original 65816 source investigation of channel7 INIDISP table.

Trace only real after-instruction 7E:2064..2069 changes in already pinned
Snes9x 2P source route and verify the original actual GO/t480 WRAM bytes.
Neither WRAM writes nor source headers alone are final PPU register effects.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

PATTERN = re.compile(
    r"^UR_QA08_INIDISP_TABLE_WRITER frame=(\d+) v=(\d+) "
    r"pc=([0-9A-F]{6}) addr=7E:([0-9A-F]{4}) "
    r"before=([0-9A-F]{2}) after=([0-9A-F]{2})$"
)
TABLE_BASE = 0x2064
TABLE_LENGTH = 6
WRAM_LENGTH = 0x20000
TRUE_SOURCES = {0x2065: 15, 0x2067: 0, 0x2069: 15}
HANDOFF_SCHEMA = "qa08-original-native-2p-live-inidisp-hdma-source-paired-handoff/1"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def anchored_handoff(handoff: dict) -> None:
    original = handoff.get("original", {})
    native = handoff.get("native", {})
    pixels = handoff.get("finished_source_frame_reference", {})
    if (handoff.get("schema") != HANDOFF_SCHEMA
        or original.get("run_id") != 38546562780
        or original.get("archive_SHA256") !=
            "4127ca46f83c19de07af4f808522f447ba7f6ce8109febf74ec0e93e0e898ee6"
        or native.get("run_id") != 38545867736
        or native.get("writer_HDMA_channel") != 7
        or original.get("writer_HDMA_channel") != 7
        or original.get("writer_mode") != 0
        or original.get("writer_indirect") is not False
        or [(x.get("v"), x.get("source"), x.get("INIDISP"))
            for x in original.get("write_values", [])] != [
            (0, "7E:2065", "0x0F"), (111, "7E:2067", "0x00"),
            (113, "7E:2069", "0x0F")]
        or pixels.get("identical_after_Snes9x_RGB565_G6_to_native_G5") != 56832):
        raise ValueError("hash-qualified original/native INIDISP source handoff changed")


def report(log: str, go: bytes, t480: bytes, handoff: dict) -> dict:
    anchored_handoff(handoff)
    if len(go) != WRAM_LENGTH or len(t480) != WRAM_LENGTH:
        raise ValueError("original source snapshots require complete 128 KiB WRAM")
    go_sources = {addr: go[addr] for addr in TRUE_SOURCES}
    if go_sources != TRUE_SOURCES:
        raise ValueError("original GO WRAM table values disagree with live original channel7 transfer")
    lines = log.splitlines()
    if any("UR_QA08_INIDISP_TABLE_WRITER_OVERFLOW" in x for x in lines):
        raise ValueError("original instruction trace overflowed bounded collection")
    found = [x for x in lines if "UR_QA08_INIDISP_TABLE_WRITER " in x]
    if len(found) > 4096 * 10:
        raise ValueError("executed 65816 source log is over bounded ten-window size")
    rows = []
    for line in found:
        match = PATTERN.fullmatch(line)
        if match is None:
            raise ValueError("malformed original executed 65816 brightness writer")
        frame, v, pc, addr, before, after = match.groups()
        frame, v = int(frame), int(v)
        offset = int(addr, 16)
        if (not 0 <= frame <= 2559 or not 0 <= v <= 261
            or not TABLE_BASE <= offset < TABLE_BASE + TABLE_LENGTH
            or before == after):
            raise ValueError("out-of-window or impossible source 65816 RAM writer")
        rows.append({
            "original_emulator_frame": frame,
            "original_beam_V_tag_not_native": v,
            "executed_original_65816_PC": pc,
            "original_WRAM_byte": f"7E:{addr}",
            "previous_original_byte": "0x" + before,
            "new_original_byte": "0x" + after,
            "is_original_HDMA_transferred_value_address":
                offset in TRUE_SOURCES,
        })
    counts = Counter(row["executed_original_65816_PC"] for row in rows)
    changed_addresses = sorted({row["original_WRAM_byte"] for row in rows})
    pc_by_address = {
        f"7E:{addr:04X}": sorted({
            row["executed_original_65816_PC"] for row in rows
            if row["original_WRAM_byte"] == f"7E:{addr:04X}"
        }) for addr in range(TABLE_BASE, TABLE_BASE + TABLE_LENGTH)
    }
    def window(data: bytes):
        return {f"7E:{addr:04X}": f"0x{data[addr]:02X}"
                for addr in range(TABLE_BASE, TABLE_BASE + TABLE_LENGTH)}
    return {
        "schema": "qa08-original-snes9x-executed-65816-channel7-INIDISP-table/1",
        "status": ("executed-65816-table-write-observed" if rows
                   else "original-source-table-snapshot-only-no-writer-executed-in-windows"),
        "original_reference_run": 38546562780,
        "original_native_frame_pairing_from_existing_independent_handoff_only": True,
        "original_source_GO_complete_WRAM_SHA256": sha(go),
        "original_source_t480_complete_WRAM_SHA256": sha(t480),
        "original_GO_actual_7E_2064_to_2069_bytes": window(go),
        "original_t480_actual_7E_2064_to_2069_bytes": window(t480),
        "original_GO_six_byte_table_SHA256": sha(go[TABLE_BASE:TABLE_BASE + TABLE_LENGTH]),
        "channel7_original_live_PPU_INIDISP_transferred_values": [
            {"original_beam_V": 0, "source": "7E:2065", "value": "0x0F"},
            {"original_beam_V": 111, "source": "7E:2067", "value": "0x00"},
            {"original_beam_V": 113, "source": "7E:2069", "value": "0x0F"},
        ],
        "trace_coverage_original_emulator_frame_windows": "0..2559, ten disjoint 256-frame bounded independent source runs",
        "executed_instruction_WRAM_byte_change_events": len(rows),
        "distinct_executed_instruction_PC_counts": dict(sorted(counts.items())),
        "original_65816_PC_candidates_by_table_byte": pc_by_address,
        "changed_source_WRAM_addresses_observed": changed_addresses,
        "observed_source_events": rows[:1024],
        "source_event_report_cap": 1024,
        "source_event_rows_truncated": len(rows) > 1024,
        "original_ROM_instruction_bytes_proven_from_disassembly": False,
        "original_65816_instruction_which_configured_DMA7_proven": False,
        "source_table_values_direct_HDMA_not_independent_native_inference": True,
        "original_table_descriptor_header_semantics_proven": False,
        "original_native_full_multichannel_same_scanline_pixels_proven": False,
        "source_writes_automatically_equal_effective_raster_pixels": False,
        "physical_SNES_hardware_validation": False,
        "HD_art_approved": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--original-go-wram", required=True, type=Path)
    parser.add_argument("--original-t480-wram", required=True, type=Path)
    parser.add_argument("--original-source-handoff", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = report(
        args.log.read_text(encoding="utf-8", errors="replace"),
        args.original_go_wram.read_bytes(),
        args.original_t480_wram.read_bytes(),
        json.loads(args.original_source_handoff.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print("QA08_ORIGINAL_INIDISP_TABLE_EXECUTED_SOURCE "
          f"writes={result['executed_instruction_WRAM_byte_change_events']} "
          f"PCs={len(result['distinct_executed_instruction_PC_counts'])} "
          f"go_headers={[result['original_GO_actual_7E_2064_to_2069_bytes'][f'7E:{a:04X}'] for a in (0x2064,0x2066,0x2068)]} "
          "native_corrected_pixels=not_executed")


if __name__ == "__main__":
    main()
