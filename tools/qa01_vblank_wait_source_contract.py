#!/usr/bin/env python3
"""QA-01: source-only original USA $4212 wait and cursor-counter contract.

This verifies preserved 65816 opcode bytes, branch polarities and the
independently imported RAM symbol. It does not execute either emulator or
establish which native host frame (if any) loses a *simulation* step.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK80 = ROOT / "reference/imported/reverse-engineering/nitrodon/bank 80.txt"
RAM = ROOT / "reference/imported/reverse-engineering/baldosa-uniracers-recomp/decomp/ram.txt"
SCHEMA = "UR-QA01-ORIGINAL-VBLANK-WAIT-SOURCE-CONTRACT/1"

# Preserve opcode bytes and polarity. The archived listing uses "JSR" for
# some long opcode 22 call sites; attest its verbatim spelling, not a decoded
# instruction length inferred from the displayed mnemonic.
WAIT_OPCODES = (
    "80/FAC5: 20 C9 FA     JSR $FAC9",
    "80/FAC9: 22 35 80 82  JSR $828035",
    "80/FACD: AD 12 42     LDA $4212",
    "80/FAD0: 30 F7        BMI $FAC9",
    "80/FAD2: 22 35 80 82  JSR $828035",
    "80/FAD6: AD 12 42     LDA $4212",
    "80/FAD9: 10 F7        BPL $FAD2",
    "80/FADB: 20 DF FA     JSR $FADF",
    "80/FADE: 60           RTS",
)
CONTINUATION_OPCODES = (
    "80/FADF: 08           PHP",
    "80/FAE0: E2 20        SEP #$20",
    "80/FAE2: C6 C6        DEC $C6",
    "80/FAE4: 10 04        BPL $FAEA",
    "80/FAE6: A9 1F        LDA #$1F",
    "80/FAE8: 85 C6        STA $C6",
    "80/FAEA: C2 20        REP #$20",
    "80/FAEC: A5 C6        LDA $C6",
    "80/FAEE: 4A           LSR",
    "80/FAEF: AA           TAX",
    "80/FAF0: E2 20        SEP #$20",
    "80/FAF2: BF AF FB 80  LDA $80FBAF,X",
    "80/FAF6: 8D DE 0B     STA $0BDE",
    "80/FAF9: 8D FE 0B     STA $0BFE",
)

def attest_opcode_sequence(archive: str, expected: tuple[str, ...]) -> None:
    lines = archive.splitlines()
    positions = []
    for expected_line in expected:
        addr = expected_line.split(":", 1)[0] + ":"
        matches = [(i, line) for i, line in enumerate(lines) if line.startswith(addr)]
        if len(matches) != 1 or not matches[0][1].startswith(expected_line):
            raise ValueError(f"missing, duplicate or changed original opcode: {expected_line}")
        positions.append(matches[0][0])
    if positions != sorted(set(positions)):
        raise ValueError("original instruction order changed")

def report(bank80: str, ram: str) -> dict:
    attest_opcode_sequence(bank80, WAIT_OPCODES)
    attest_opcode_sequence(bank80, CONTINUATION_OPCODES)
    if bank80.splitlines().index(next(
        line for line in bank80.splitlines() if line.startswith(WAIT_OPCODES[-1])
    )) >= bank80.splitlines().index(next(
        line for line in bank80.splitlines() if line.startswith(CONTINUATION_OPCODES[0])
    )):
        raise ValueError("wait did not fall through to the expected continuation")
    symbols = [line for line in ram.splitlines() if line.startswith("7E00C6 ")]
    if len(symbols) != 1 or symbols[0].split()[:3] != [
        "7E00C6", "wCursorAnimTimer", "1"
    ]:
        raise ValueError("archived $C6 cursor counter symbol or width changed")
    return {
        "schema": SCHEMA,
        "rom": "USA-retail archived opcode listing, not a runtime PC receipt",
        "wait_entry_pc": "80:FAC9",
        "wait_first_hvbjoy_read_pc": "80:FACD",
        "wait_for_vblank_clear_branch_pc": "80:FAD0",
        "wait_second_hvbjoy_read_pc": "80:FAD6",
        "wait_for_vblank_set_branch_pc": "80:FAD9",
        "after_second_edge_call_pc": "80:FADB",
        "called_continuation_pc": "80:FADF",
        "counter_decrement_pc": "80:FAE2",
        "counter_wrap_value": 31,
        "counter_symbol": "wCursorAnimTimer",
        "counter_symbol_width_bytes": 1,
        "counter_register": "7E:00C6",
        "animation_output_writer_pcs": ["80:FAF6", "80:FAF9"],
        "animation_output_addresses": ["7E:0BDE", "7E:0BFE"],
        "counter_is_universal_guest_simulation_frame_clock_proven": False,
        "counter_is_unmodified_by_other_routines_proven": False,
        "actual_original_wait_pc_executed_in_rf014_proven": False,
        "actual_native_wait_pc_executed_in_rf014_proven": False,
        "native_beam_model_causes_rf014_proven": False,
        "cpu_nmi_beam_sample_phase_correspondence_proven": False,
        "full_usa_events_accepted_by_this_check": 0,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = report(BANK80.read_text(encoding="utf-8"),
                    RAM.read_text(encoding="utf-8"))
    if args.out.exists():
        parser.error("refuse to replace previous evidence")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({"source_wait": result["wait_entry_pc"],
                      "continuation": result["counter_decrement_pc"],
                      "actual_native_frame_loss_proven": False,
                      "release_credit": 0}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
