#!/usr/bin/env python3
"""QA-01: qualify the raw $009F terminal signature against archived USA source.

Source-only crosswalk. The historically used 'menu 0x84/0x16' label is a
single raw WRAM byte; imported symbolic name wTextPos is provisional/context-
dependent. It cannot alone prove scene identity or a gameplay rule change.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK80 = ROOT / "reference/imported/reverse-engineering/nitrodon/bank 80.txt"
BANK83 = ROOT / "reference/imported/reverse-engineering/nitrodon/bank 83.txt"
RAM = ROOT / "reference/imported/reverse-engineering/baldosa-uniracers-recomp/decomp/ram.txt"
SCHEMA = "UR-QA01-ORIGINAL-RESULT-RAW-009F-RESTORE-STATIC-CONTRACT/1"
TEXT_POSITION_ADDRESS = 0x009F
TEXT_POSITION_WIDTH = 2
RESTORE_LAST_WORD_INDEX = 0x00CE
RESTORE_START = 0
WORD_BYTES = 2

TEXT_SOURCE = (
    "80/A18E: A9 84        LDA #$84",
    "80/A190: 85 9F        STA $9F",
)
TEXT_LAYOUT = (
    "80/C432: E6 9F        INC $9F",
    "80/C434: E6 9F        INC $9F",
    "80/C49E: 85 9F        STA $9F",
)
# Direct archived call chain: save direct-page image, reset video,
# then restore the direct-page words. This is a static direct call-site census,
# not an executed original result-boundary caller receipt.
STATIC_RESTORE_CALLER = (
    "80/9A27: 22 94 98 83  JSR $839894",
    "80/9A37: 20 8B A0     JSR $A08B",
    "80/9A3A: 20 FD D1     JSR $D1FD",
    "80/9A3F: 22 7D 98 83  JSR $83987D",
    "80/9A43: 20 A4 98     JSR $98A4",
)
RESTORE_SOURCE = (
    "83/987D: 08           PHP",
    "83/987E: C2 20        REP #$20",
    "83/9880: A2 00 00     LDX #$0000",
    "83/9883: A0 CE 00     LDY #$00CE",
    "83/9886: BF 6B 0E 77  LDA $770E6B,X",
    "83/988A: 9D 00 00     STA $0000,X",
    "83/988D: E8           INX",
    "83/988E: E8           INX",
    "83/988F: 88           DEY",
    "83/9890: 10 F4        BPL $9886",
    "83/9892: 28           PLP",
    "83/9893: 6B           RTL",
)


def attest_order(archive: str, operands: tuple[str, ...], context: str) -> None:
    # Source comments/spacing may vary; require exact archived address,
    # opcode bytes and primary disassembly mnemonic, not extra annotation.
    ordered = []
    for instruction in operands:
        hits = [idx for idx, line in enumerate(archive.splitlines())
                if line.startswith(instruction)]
        if len(hits) != 1:
            raise ValueError(f"{context}: missing, duplicate or rewritten original opcode: {instruction}")
        ordered.append(hits[0])
    if sorted(ordered) != ordered or len(set(ordered)) != len(ordered):
        raise ValueError(f"{context}: original opcode order changed")


def write_owner(offset: int) -> dict:
    if not RESTORE_START <= offset < WORD_BYTES * (RESTORE_LAST_WORD_INDEX + 1):
        raise ValueError("target byte outside original 207-word SRAM restore footprint")
    x = offset - (offset % WORD_BYTES)
    return {
        "byte_offset_hex": f"7E:{offset:04X}",
        "indexed_word_start": f"7E:{x:04X}",
        "word_byte_index": offset % WORD_BYTES,
        "loop_iteration_one_based": x // WORD_BYTES + 1,
    }


def report(bank80: str, bank83: str, ram: str) -> dict:
    named = [line for line in ram.splitlines() if line.startswith("7E009F ")]
    if len(named) != 1 or named[0].split()[:3] != ["7E009F", "wTextPos", "2"]:
        raise ValueError("source symbol at $009F not the archived two-byte text position")
    attest_order(bank80, TEXT_SOURCE, "bank-80 text initializer")
    attest_order(bank80, TEXT_LAYOUT, "bank-80 text cursor consumer")
    attest_order(bank80, STATIC_RESTORE_CALLER, "bank-80 SRAM direct-page restore caller")
    attest_order(bank83, RESTORE_SOURCE, "bank-83 SRAM direct-page restore")
    # Across archived bank 80, the only immediate 65816 JSL operand
    # for this direct restore destination is 22 7D 98 83 at 80:9A3F.
    # This excludes neither indirect dispatch nor other-bank callers.
    if bank80.count("22 7D 98 83") != 1:
        raise ValueError("archived bank-80 direct restore call-site count changed")
    start = bank83.index(RESTORE_SOURCE[1])
    end = bank83.index(RESTORE_SOURCE[-1])
    if "SEP #$20" in bank83[start:end]:
        raise ValueError("original restore accumulator width was changed")
    low = write_owner(TEXT_POSITION_ADDRESS)
    high = write_owner(TEXT_POSITION_ADDRESS + TEXT_POSITION_WIDTH - 1)
    if low["indexed_word_start"] == high["indexed_word_start"]:
        raise ValueError("this archived odd-address word should straddle two restore stores")
    return {
        "schema": SCHEMA,
        "raw_result_signature_address": "7E:009F",
        "source_catalogue_symbol": "wTextPos",
        "source_catalogue_symbol_width_bytes": 2,
        "source_text_initializer_load_immediate": "80:A18E",
        "source_text_initializer_store": "80:A190",
        "source_text_layout_writer": "80:C49E",
        "archived_bank80_direct_restore_callsite": "80:9A3F",
        "source_save_direct_page_call_before": "80:9A27",
        "source_video_reset_call_before_restore": "80:9A37",
        "source_input_or_setup_call_before_restore": "80:9A3A",
        "original_result_boundary_executed_this_callsite_proven": False,
        "source_restore_loop_entry": "83:987D",
        "source_restore_word_writer": "83:988A",
        "source_restore_loop_branch": "83:9890",
        "restore_word_writes_per_execution": RESTORE_LAST_WORD_INDEX + 1,
        "restore_total_bytes_if_Wram_DBR": (RESTORE_LAST_WORD_INDEX + 1) * WORD_BYTES,
        "restore_byte_range_if_Wram_DBR": ["7E:0000", "7E:019D"],
        "text_position_field_restore_owners": [low, high],
        "observed_0x84_to_0x16_proves_actual_scene_change": False,
        "observed_0x84_to_0x16_proves_83_988A_executed": False,
        "source_operand_proves_DBR_Wram_at_runtime": False,
        "cpu_beam_frame_phase_original_native_aligned": False,
        "complete_usa_events_strict_admitted": 0,
        "interpretation": (
            "The single raw low byte $009F used as a terminal phase signature "
            "is also the first byte of source wTextPos and is written by text "
            "initialization/layout code. A source bank-83 16-bit loop could "
            "restore its two-byte word across two different STA $0000,X "
            "instructions if the actual DBR targets WRAM. This does not by "
            "itself establish runtime writer PC, text cursor semantics at "
            "this scene, or a genuine results-state decision divergence."),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = report(BANK80.read_text(encoding="utf-8"),
                    BANK83.read_text(encoding="utf-8"),
                    RAM.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "raw_signature": "7E:009F",
        "source_restore_words": result["restore_word_writes_per_execution"],
        "two_stores_for_text_word": True,
        "release_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
