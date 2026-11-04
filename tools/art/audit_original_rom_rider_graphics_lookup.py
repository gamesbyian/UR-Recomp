#!/usr/bin/env python3
"""SHA-locked original-ROM rider phase/angle graphics lookup, not a 3D rig."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from tools.art.no_replace_report import publish_text_once

ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
ROM_LENGTH = 2_097_152
SCHEMA = "UR-ART4K-EXACT-ROM-RIDER-PRESENTATION-PATH/1"

# Actual opcode bytes at original 65816 CPU PCs, independently cross-checked
# against the exact SHA-pinned USA retail ROM, not merely decompiler comments.
FINGERPRINTS = {
    "animation_update_calls_angle": (0x83, 0xED33, "2010ef"),
    "phase_plus_delta": (0x83, 0xEE53, "ad830f186500"),
    "wrap_positive_at_24": (0x83, 0xEE5E, "c91800300c38e9180080f0"),
    "wrap_negative_at_24": (0x83, 0xEE69, "1869180080ea"),
    "phase_store": (0x83, 0xEE6F, "8d830f"),
    "six_shifts_times_64": (0x83, 0xEED9, "ad830f0a0a0a0a0a0a"),
    "plus_six_bit_orientation": (0x83, 0xEEE6, "186d770f"),
    "store_selected_graphics": (0x83, 0xEF0C, "8c970f"),
    "orientation_mask_3f": (0x83, 0xF086, "293f008d770f"),
    "lookup_index_tripled": (0x83, 0xF296, "e21085000a18650018690080"),
    "lookup_table_bank_20": (0x83, 0xF2A4, "8ba0205aab"),
    "pointer_bank_plus_23": (0x83, 0xF2A9, "a002e220b100186923"),
    "pointer_address_lookup": (0x83, 0xF2B3, "c220a000b100ab60"),
    "players_to_queue": (0x83, 0xF0D7, "ace90f8c0002aceb0f8c0402"),
    "queue_source_address": (0x83, 0xF21A, "994516"),
    "queue_source_bank": (0x83, 0xF227, "99a115"),
    "queue_vram_destination": (0x83, 0xF26B, "99e916"),
    "queue_pending": (0x83, 0xF290, "a0018c0603"),
    "nmi_pending_read": (0x82, 0xB8AF, "ad0603d003"),
    "nmi_clear_pending": (0x82, 0xB8B7, "9c0603"),
    "nmi_vram_increment": (0x82, 0xB8BD, "a9808d1521"),
    "nmi_dma_to_2118": (0x82, 0xB8C2, "a9018d0043a9188d0143"),
    "nmi_dma_32_bytes": (0x82, 0xB8D5, "a020"),
    "nmi_dma_source_bank": (0x82, 0xB8E3, "aea115"),
    "nmi_dma_source_addr": (0x82, 0xB8EE, "ad45168d0243"),
    "nmi_dma_vram_dest": (0x82, 0xB8F4, "ade916898000"),
    "nmi_trigger_channel_zero": (0x82, 0xB902, "a2018e0b42"),
}

def rom_offset(bank: int, addr: int) -> int:
    if type(bank) is not int or type(addr) is not int:
        raise ValueError("expected SNES integer bank/address")
    if not (0x80 <= bank <= 0xFF and 0x8000 <= addr <= 0xFFFF):
        raise ValueError("LoROM CPU address outside upper-half ROM banks")
    result = ((bank & 0x7F) << 15) + (addr & 0x7FFF)
    if result >= ROM_LENGTH:
        raise ValueError("outside exact 2MiB retail USA ROM")
    return result

def default_index(phase: int, orientation: int) -> int:
    """Only 83:EED9's ordinary path; special overlay branches differ."""
    if type(phase) is not int or type(orientation) is not int:
        raise ValueError("integer ROM source states required")
    if not 0 <= phase < 24 or not 0 <= orientation < 64:
        raise ValueError("phase modulo 24, orientation masked to 6 bits")
    return (phase << 6) + orientation

def pointer(rom: bytes, index: int) -> dict:
    if type(index) is not int or not 0 <= index < 1536:
        raise ValueError("ordinary presentation index out of 1536")
    # 83:F296 triples index into pointer table $20:8000; bank $A0
    # is the LoROM CPU mirror of data-bank $20.
    address = 0x8000 + 3 * index
    at = rom_offset(0xA0, address)
    raw = rom[at:at + 3]
    if len(raw) != 3:
        raise ValueError("truncated graphics pointer record")
    return {"index": index, "table_address": f"20:{address:04X}",
            "pointer_bytes": raw.hex(),
            "source_bank": f"{(raw[2] + 0x23) & 255:02X}",
            "source_address": f"{int.from_bytes(raw[:2], 'little'):04X}"}

def audit(rom: bytes) -> dict:
    if len(rom) != ROM_LENGTH or hashlib.sha256(rom).hexdigest() != ROM_SHA:
        raise ValueError("wrong original USA ROM identity")
    checked = []
    for name, (bank, addr, hex_bytes) in FINGERPRINTS.items():
        expected = bytes.fromhex(hex_bytes)
        at = rom_offset(bank, addr)
        if rom[at:at + len(expected)] != expected:
            raise ValueError("ROM instruction fingerprint mismatch: " + name)
        checked.append({"label": name, "CPU_PC": f"{bank:02X}:{addr:04X}",
                        "ROM_offset": at, "hex": hex_bytes})
    all_indices = {default_index(p, a) for p in range(24) for a in range(64)}
    if all_indices != set(range(1536)):
        raise ValueError("ordinary source indexing no longer bijective")
    table = [pointer(rom, index) for index in range(1536)]
    return {
        "schema": SCHEMA, "ROM_SHA256": ROM_SHA, "ROM_bytes": ROM_LENGTH,
        "source_instruction_fingerprints": checked,
        "phase_modulus": 24, "orientation_states": 64,
        "ordinary_index_formula": "(phase << 6) + orientation",
        "ordinary_phase_orientation_pairs": 1536,
        "ordinary_distinct_presentation_indices": len(all_indices),
        "pointer_table_address_range": "20:8000..20:91FF",
        "pointer_entry_bytes": 3, "pointer_entries": len(table),
        "pointer_examples": [table[i] for i in (0, 1, 31, 32, 63, 64, 127, 255, 511, 799, 1023, 1535)],
        "special_rider_presentation_override_paths_exist": True,
        "original_executed_rider_runtime_PC_trace": False,
        "original_writer_cause_1994_3D_geometry_approved": False,
        "owner_likeness_or_shipping_art_approved": False,
    }

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = audit(args.rom.read_bytes())
    publish_text_once(args.out, json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"fingerprints": len(result["source_instruction_fingerprints"]),
                      "graphics_indices": result["ordinary_distinct_presentation_indices"]}))

if __name__ == "__main__":
    main()
