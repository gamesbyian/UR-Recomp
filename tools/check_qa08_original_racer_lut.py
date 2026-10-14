#!/usr/bin/env python3
"""Bounded original Snes9x executed racer palette-selector/LUT proof.

Consumes four new read-only original CPU PC observations together with the
previously accepted 55-opcode + 18 actual WRAM-writer receipt. Exact CPU input,
ROM and game table values are necessary; a guessed selector is not evidence.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

MARK = "UR_QA08_ORIGINAL_RACER_LUT"
RX = re.compile(
    r"^UR_QA08_ORIGINAL_RACER_LUT frame=(\d+) "
    r"pc=(82[0-9A-F]{4}) kind=(selector|lookup) "
    r"a=([0-9A-F]{4}) x=([0-9A-F]{4})"
    r"(?: bytes=([0-9A-F]{8}))?$"
)
EXPECTED = (("82D5D1", "selector", "upper"),
            ("82D5D4", "lookup", "upper"),
            ("82D61E", "selector", "lower"),
            ("82D621", "lookup", "lower"))
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
LAYOUT = "qa08-original-2p-channel5-HDMA-executed-opcode-source-layout/1"
OPCODE = "qa08-original-2p-executed-82d5c0-82d66f-opcode-byte-census/1"


def _decode(path: Path) -> dict:
    def distinct(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate original lookup evidence key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf8"), object_pairs_hook=distinct)


def check(log: Path, opcode_path: Path, layout_path: Path,
          receipt_path: Path) -> dict:
    opcodes = _decode(opcode_path)
    layout = _decode(layout_path)
    receipt = _decode(receipt_path)
    if (layout.get("schema") != LAYOUT or opcodes.get("schema") != OPCODE
            or layout.get("original_USA_ROM_SHA256") != ROM_SHA
            or receipt.get("USA_ROM_SHA256") != ROM_SHA
            or receipt.get("original_script_SHA256") !=
            layout.get("original_2P_input_script_SHA256")
            or receipt.get("original_t480_WRAM_SHA256") !=
            layout.get("original_full_t480_WRAM_SHA256")
            or receipt.get("second_camera_0DDB") != 1
            or receipt.get("in_race_0313") != 1
            or receipt.get("source_65816_writer_PCs") != 18
            or opcodes.get("independently_source_accepted_WRAM_writer_PCs") != 18
            or opcodes.get("actual_executed_original_opcode_records") != 55
            or len(opcodes.get("actual_opcode_sequence", [])) != 55
            or layout.get("original_executed_instructions_captured") != 55
            or layout.get("ROM_LUT_base") != "82:D52A"
            or layout.get("original_guest_frame") != 1781
            or opcodes.get("original_Snes9x_frame") != 1781
            or opcodes.get("original_native_same_input_frame_parity_proven") is not False
            or layout.get("full_original_native_same_input_frame_parity_proven") is not False):
        raise ValueError("genuine original ROM/route/18 writer/55 executed PC source receipt absent")
    # Match the *entire* current original replay to all previously captured
    # fetched instruction bytes, rather than trusting only four new PC names.
    actual = opcodes["actual_opcode_sequence"]
    expected = layout["original_source_opcode_sequence"]
    if (len(expected) != 55 or any(
            got["executed_65816_PC"] != old["original_PC"].replace(":", "") or
            got["actual_instruction_bytes_hex"] != old["actual_ROM_instruction_hex"]
            for got, old in zip(actual, expected))):
        raise ValueError("executed original source opcodes differ from retained 55-code witness")

    raw = log.read_text(encoding="utf8", errors="replace").splitlines()
    if any(MARK+"_INVALID" in s or MARK+"_OVERFLOW" in s for s in raw):
        raise ValueError("invalid or truncated real original CPU source lookup")
    lines = [s for s in raw if MARK+" frame=" in s]
    if len(lines) != 4:
        raise ValueError("four unique executed source lookup events required")
    records = []
    for text, (pc, kind, viewport) in zip(lines, EXPECTED):
        m = RX.fullmatch(text)
        if not m or int(m.group(1)) != 1781 or m.group(2) != pc or m.group(3) != kind:
            raise ValueError("wrong original frame, executed source PC, or selector path order")
        a, x = int(m.group(4), 16), int(m.group(5), 16)
        value = m.group(6)
        if ((kind == "selector" and value is not None) or
                (kind == "lookup" and value is None)):
            raise ValueError("original selector and data reads conflated")
        records.append({
            "original_cpu_pc": f"82:{pc[2:]}", "viewport": viewport,
            "source_phase": kind, "actual_A_register": f"0x{a:04X}",
            "actual_X_register": f"0x{x:04X}",
            "actual_ROM_four_bytes": value,
        })
    views = []
    triplets = layout.get("original_table_triplets")
    if not isinstance(triplets, list) or len(triplets) != 6:
        raise ValueError("six original source descriptor triplets required")
    for i in range(2):
        first, second = records[2*i:2*i+2]
        selector = int(first["actual_A_register"], 16) & 0xFF
        x = int(second["actual_X_register"], 16)
        if selector > 63 or x != 4 * selector or 0xD52A + x + 3 > 0xD66F:
            raise ValueError("actual executed TAX index does not match original selector")
        table = triplets[3*i:3*i+3]
        expected_bytes = "".join([entry["coldata"] for entry in table] + ["04"])
        if (any(entry["viewport"] != first["viewport"] or entry["cgadsub"] != "04"
                for entry in table) or second["actual_ROM_four_bytes"] != expected_bytes):
            raise ValueError("actual original indexed ROM bytes contradict 18 executed WRAM stores")
        views.append({
            "viewport": first["viewport"],
            "selector_original_guest_address": "77:0748" if i == 0 else "77:0749",
            "source_at_selector_PC": first["original_cpu_pc"],
            "actual_original_selector_low8": selector,
            "actual_cpu_A_whole_register": first["actual_A_register"],
            "actual_effective_X_index_bytes": x,
            "actual_indexed_ROM_entry": f"82:{0xD52A+x:04X}",
            "original_ROM_palette_four_bytes": expected_bytes,
            "source_data_loaded_at_PC": second["original_cpu_pc"],
        })
    return {
        "schema": "qa08-original-2p-executed-palette-selector-indexed-ROM-values/1",
        "status": "actual-original-Snes9x-executed-A-X-and-indexed-LUT-read",
        "original_source_frame": 1781,
        "original_ROM_SHA256": ROM_SHA,
        "original_unmodified_route_SHA256": layout["original_2P_input_script_SHA256"],
        "original_full_WRAM_SHA256": layout["original_full_t480_WRAM_SHA256"],
        "original_emulator_55_opcode_bytes_same_as_prior_capture": True,
        "original_18_executed_WRAM_stores_same_as_prior_capture": True,
        "independent_source_register_observations": 4,
        "actual_original_palette_entries": views,
        "all_other_original_racer_palette_entries_recovered": False,
        "original_native_same_input_frame_parity_proven": False,
        "physical_SNES_timing_or_pixel_RGB_proven": False,
        "current_HD_racer_art_likeness_approved": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ("log", "opcodes", "layout", "receipt", "out"):
        p.add_argument("--"+arg, type=Path, required=True)
    a = p.parse_args()
    out = check(a.log, a.opcodes, a.layout, a.receipt)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=2, sort_keys=True)+"\n", encoding="utf8")
    print("QA08_ORIGINAL_RACER_LUT_EXECUTION_ACCEPTED frame=1781 "
          "source_selectors=2 actual_ROM_entries=2 same_frame_native=0 art_approved=0")


if __name__ == "__main__":
    main()
