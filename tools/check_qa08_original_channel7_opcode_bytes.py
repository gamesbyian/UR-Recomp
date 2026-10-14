#!/usr/bin/env python3
"""Join real original Snes9x instruction bytes to independent channel7 writers."""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re

RX = re.compile(
    r"^UR_QA08_INIDISP_TABLE_OPCODE frame=(\d+) v=(\d+) "
    r"pc=([0-9A-F]{6}) op=([0-9A-F]{2}) oplen=(\d+) "
    r"bytes=([0-9A-F]{8}) mapped=([01]) fetched=([01])$"
)
HANDOFF = "qa08-original-snes9x-channel7-writer-artifact-handoff/1"
WRITERS = "qa08-original-snes9x-executed-65816-channel7-INIDISP-table/1"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"


def check(log: str, writer: dict, handoff: dict) -> dict:
    if (handoff.get("schema") != HANDOFF
        or handoff.get("original_source_workflow_run") != 38615121956
        or handoff.get("original_source_artifact_id") != 11919775789
        or handoff.get("original_source_artifact_zip_sha256") !=
           "f3fe49c7c14f28474c2a8f9dcfa713ff2e8bb811b6189e13f7c575c00b00007a"
        or handoff.get("original_USA_ROM_sha256") != ROM_SHA
        or writer.get("schema") != WRITERS
        or writer.get("original_GO_six_byte_table_SHA256") !=
            handoff.get("original_GO_table_six_byte_sha256")
        or writer.get("original_GO_actual_7E_2064_to_2069_bytes") !=
            handoff.get("original_GO_table_bytes")
        or writer.get("executed_instruction_WRAM_byte_change_events") !=
            handoff.get("original_source_executed_writer_events")
        or writer.get("distinct_executed_instruction_PC_counts") !=
            handoff.get("original_source_distinct_writer_PCs")
        or writer.get("executed_instruction_WRAM_byte_change_events") != 1403
        or writer.get("status") != "executed-65816-table-write-observed"):
        raise ValueError("independent original Snes9x executed channel7 writer source changed")
    expected = set(handoff["original_source_distinct_writer_PCs"])
    pc_address = defaultdict(set)
    for address, pcs in writer["original_65816_PC_candidates_by_table_byte"].items():
        for pc in pcs:
            pc_address[pc].add(address)
    if set(pc_address) != expected:
        raise ValueError("source PC to actual changed WRAM address registration changed")
    if "UR_QA08_INIDISP_TABLE_OPCODE_OVERFLOW" in log:
        raise ValueError("original executed opcode byte probe overflow")
    rows = [x for x in log.splitlines() if x.startswith("UR_QA08_INIDISP_TABLE_OPCODE")]
    if not 8 <= len(rows) <= 80:
        raise ValueError("missing or overbounded original real opcode records")
    seen = {}
    duplicates = defaultdict(int)
    for line in rows:
        m = RX.fullmatch(line)
        if m is None:
            raise ValueError("malformed real executed 65816 opcode byte witness")
        frame, v, pc, opcode, length, raw, mapped, fetched = m.groups()
        frame, v, length = int(frame), int(v), int(length)
        if (pc not in expected or not 0 <= frame <= 2559 or not 0 <= v <= 261
            or not 1 <= length <= 4 or mapped != "1" or fetched != "1"
            or raw[:2] != opcode):
            raise ValueError("wrong original source PC, clock, mapped byte or opcode")
        identity = (opcode, length, raw)
        if pc in seen and seen[pc]["identity"] != identity:
            raise ValueError("identical pinned original ROM PC yielded different instruction bytes")
        duplicates[pc] += 1
        if pc in seen:
            continue
        long_address = (
            f"{int(raw[6:8],16):02X}:{int(raw[4:6],16):02X}{int(raw[2:4],16):02X}"
            if opcode == "8F" and length == 4 else None
        )
        seen[pc] = {
            "executed_original_65816_PC": pc,
            "observed_first_original_Snes9x_frame": frame,
            "observed_first_beam_V": v,
            "actual_fetched_opcode": "0x" + opcode,
            "actual_ROM_instruction_bytes": raw[:2 * length],
            "actual_trailing_ROM_preview_bytes": raw[2 * length:],
            "executed_CPU_mode_oplength": length,
            "long_STA_WRAM_destination_if_applicable": long_address,
            "independently_changed_source_WRAM_addresses": sorted(pc_address[pc]),
            "fetched_opcode_destination_matches_actual_writer":
                long_address in pc_address[pc] if long_address is not None else False,
            "identity": identity,
        }
    if set(seen) != expected:
        raise ValueError("not every independently observed writer PC has actual fetched source ROM bytes")
    output = []
    for pc in sorted(seen):
        row = seen[pc]
        row.pop("identity")
        row["independent_original_route_window_observations"] = duplicates[pc]
        output.append(row)
    return {
        "schema": "qa08-original-2p-executed-channel7-writer-opcode-byte-crosswalk/1",
        "original_wram_writer_workflow_run": 38615121956,
        "original_rom_sha256": ROM_SHA,
        "actual_unique_original_65816_writer_PCs": len(output),
        "actual_opcode_observation_records": len(rows),
        "every_executed_writer_PC_ROM_bytes_observed": True,
        "all_store_destinations_match_original_WRAM_changes":
            all(row["fetched_opcode_destination_matches_actual_writer"] for row in output),
        "actual_original_executed_ROM_source": output,
        "original_65816_CPU_mode_oplength_is_source_observed": True,
        "HDMA_original_table_assembly_source_proven_but_final_RBG_pixels_not_from_WRAM_writes": True,
        "native_original_PPU_scanline_timing_or_global_DMA_correction_proven": False,
        "physical_SNES_hardware_or_HD_art_approved": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log", type=Path, required=True)
    p.add_argument("--writer-report", type=Path, required=True)
    p.add_argument("--source-handoff", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    report = check(a.log.read_text(encoding="utf-8", errors="replace"),
                   json.loads(a.writer_report.read_text()),
                   json.loads(a.source_handoff.read_text()))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("QA08_ORIGINAL_CHANNEL7_EXECUTED_ROM_BYTES_CAPTURED "
          f"PCs={report['actual_unique_original_65816_writer_PCs']} "
          f"events={report['actual_opcode_observation_records']} "
          f"STA_target_proven={report['all_store_destinations_match_original_WRAM_changes']} "
          "final_raster=unproven")


if __name__ == "__main__":
    main()
