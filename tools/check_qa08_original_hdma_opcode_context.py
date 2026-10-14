#!/usr/bin/env python3
"""Strict executed-original USA 65816 opcode source around accepted 18 WRAM writers.

Matches *all 18* formerly independently source-proven original Snes9x guest
WRAM writer PCs with actual fetched opcode and ROM bytes. This is opcode
provenance, not physical SNES timing or a same-frame native acceptance claim.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

RX = re.compile(
    r"^UR_QA08_ORIGINAL_HDMA_OPCODE frame=(\d+) "
    r"pc=([0-9A-F]{6}) op=([0-9A-F]{2}) "
    r"oplen=(\d+) bytes=([0-9A-F]{8}) "
    r"mapped=([01]) fetched=([01])$"
)
MARK = "UR_QA08_ORIGINAL_HDMA_OPCODE"
CENSUS_SCHEMA = "qa08-original-Snes9x-2P-WRAM-colour-HDMA-executed-writer-census/1"


def check(log: Path, census_path: Path) -> dict:
    census = json.loads(census_path.read_text(encoding="utf8"))
    original = census.get("source_byte_changes")
    if (census.get("schema") != CENSUS_SCHEMA or
            census.get("original_USA_ROM_SHA256") !=
            "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478" or
            census.get("original_Snes9x_source_run") != 38510398955 or
            census.get("source_changed_WRAM_byte_record_count") != 18 or
            len(original or []) != 18 or
            census.get("original_frame_coverage_start") != 0 or
            census.get("original_frame_coverage_end_inclusive") != 2559 or
            census.get("full_original_native_same_input_parity_proven") is not False):
        raise ValueError("authentic original USA executed WRAM writer census missing")
    writer_pcs = [x["executed_65816_PC"].upper() for x in original]
    if len(set(writer_pcs)) != 18 or any(not (0x82D5C0 <= int(pc,16) <= 0x82D66F)
                                       for pc in writer_pcs):
        raise ValueError("original independently executed writer PC registration changed")
    text = log.read_text(encoding="utf8",errors="replace").splitlines()
    if any(MARK+"_OVERFLOW" in line for line in text):
        raise ValueError("bounded original opcode source witness overflow")
    matching = [line for line in text if MARK in line]
    if len(matching) < 18 or len(matching) > 512:
        raise ValueError("incomplete or overflowing original opcode source records")
    events = []
    for ordinal, line in enumerate(matching):
        m = RX.fullmatch(line)
        if not m:
            raise ValueError("malformed original-executed opcode source record")
        frame, pc, opcode, length, raw, mapped, fetched = m.groups()
        if (int(frame) != 1781 or int(pc,16) < 0x82D5C0 or
                int(pc,16) > 0x82D66F or not 1 <= int(length) <= 4 or
                mapped != "1" or fetched != "1" or raw[:2] != opcode):
            raise ValueError("unmapped, wrong-frame, or mismatched original opcode read")
        events.append({
            "ordinal":ordinal, "original_emulator_frame":int(frame),
            "executed_65816_PC":pc, "fetched_opcode_hex":opcode,
            "actual_ROM_bytes_at_PC_hex":raw,
            "opcode_length_in_executed_CPU_mode":int(length),
            "actual_instruction_bytes_hex":raw[:2*int(length)],
            "actual_trailing_preview_bytes_not_proven_instruction":
                raw[2*int(length):],
        })
    seen = {}
    for row in events:
        seen.setdefault(row["executed_65816_PC"], []).append(row)
    missing = sorted(set(writer_pcs)-set(seen))
    if missing:
        raise ValueError("executed opcode trace omits accepted original writer PCs: "+
                         ",".join(missing))
    # These 18 previously source-observed actual WRAM change PCs are expected
    # to appear in the same deterministic stream order as the opcode captures.
    positions = [seen[pc][0]["ordinal"] for pc in writer_pcs]
    if positions != sorted(positions):
        raise ValueError("original opcode trace contradicts original WRAM writer order")
    attached = []
    for entry in original:
        pc = entry["executed_65816_PC"].upper()
        att = seen[pc][0]
        attached.append({
            "executed_65816_PC":pc,
            "actual_written_WRAM_address":"7E:"+entry["WRAM_address"],
            "original_executed_WRAM_written_byte":entry["after"],
            "native_COLDATA_source_observed":
                entry["matches_accepted_native_COLDATA_source"],
            "fetched_opcode_hex":att["fetched_opcode_hex"],
            "actual_instruction_bytes_hex":att["actual_instruction_bytes_hex"],
            "opcode_length_in_executed_CPU_mode":
                att["opcode_length_in_executed_CPU_mode"],
        })
    return {
        "schema":"qa08-original-2p-executed-82d5c0-82d66f-opcode-byte-census/1",
        "status":"original-source-CPU-fetched-ROM-opcodes-for-all-18-executed-WRAM-writers",
        "original_Snes9x_frame":1781,
        "original_USA_ROM_SHA256":census["original_USA_ROM_SHA256"],
        "independently_source_accepted_WRAM_writer_PCs":18,
        "actual_executed_original_opcode_records":len(events),
        "every_independently_WITNESSED_WRAM_writer_has_fetched_original_ROM_bytes":True,
        "original_emulator_oplength_depends_on_executed_M_X_flags":True,
        "original_native_same_input_frame_parity_proven":False,
        "physical_SNES_console_execution_proven":False,
        "original_HD_racer_likeness_approved":False,
        "actual_opcode_sequence":events,
        "independently_executed_original_WRAM_writer_PC_opcode_crosswalk":attached,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log",type=Path,required=True)
    p.add_argument("--original-writer-census",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=check(a.log,a.original_writer_census)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("QA08_ORIGINAL_WRITER_OPCODE_SOURCE_ACCEPTED "
          "original_writer_PCs=18 "
          f"executed_original_opcodes={report['actual_executed_original_opcode_records']} "
          "source_ROM_bytes=1 native_same_frame=0 physical_SNES=0")


if __name__=="__main__":
    main()
