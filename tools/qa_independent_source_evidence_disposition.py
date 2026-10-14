#!/usr/bin/env python3
"""Read-only QA consistency audit of two retained source research witnesses.

This validates *published summaries* against their own executed source layout
and host-frame arithmetic. It does not independently replay original/native
binaries, turn registers into displayed pixels, or grant release acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRITER = ROOT / "analysis/data/qa08-original-2p-channel5-executed-opcode-table-layout.json"
FADE = ROOT / "analysis/data/zoo-original-native-return-ppu-fade-host-20261014.json"
HEXDIGEST = re.compile(r"[a-f0-9]{64}\Z")


def insist(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError("independent source evidence inconsistency: " + reason)


def valid_hash(value: object) -> bool:
    return type(value) is str and HEXDIGEST.fullmatch(value) is not None


def audit(writer: dict, fade: dict) -> dict:
    insist(type(writer) is dict and type(fade) is dict, "source reports not objects")
    insist(writer.get("schema") ==
           "qa08-original-2p-channel5-HDMA-executed-opcode-source-layout/1",
           "channel-5 source scope")
    insist(fade.get("schema") == "UR-QA01-ZOO-SOURCE-NATIVE-ABSOLUTE-HOST-PPU-FADE/1",
           "Zoo original/native source scope")
    for name in (
        "original_opcode_archive_zip_SHA256", "original_opcode_report_SHA256",
        "original_opcode_route_receipt_SHA256", "original_USA_ROM_SHA256",
        "original_instrumented_core_SHA256", "original_2P_input_script_SHA256",
    ):
        insist(valid_hash(writer.get(name)), "missing channel-5 " + name)
    for name in ("real_artifact_sha256", "source_pc_log_sha256"):
        insist(valid_hash(fade.get(name)), "missing Zoo " + name)
    insist(writer.get("original_independently_executed_writer_PCs") == 18 and
           writer.get("original_executed_instructions_captured") == 55 and
           writer.get("original_guest_frame") == 1781 and
           writer.get("original_guest_2P_second_camera_0DDB") == 1 and
           writer.get("original_guest_race_0313") == 1, "executed-original scope")
    insist(writer.get("writer_opcode") == "8F" and
           writer.get("CPU_65816_program_bank") == "82", "opcode type/bank")
    sequence = writer.get("original_source_opcode_sequence")
    observed = writer.get("original_executed_65816_writer_PC_and_WRAM_target")
    descriptors = writer.get("original_table_triplets")
    insist(type(sequence) is list and len(sequence) == 55, "55 instruction receipts")
    insist(type(observed) is list and len(observed) == 18, "18 writer receipts")
    insist(type(descriptors) is list and len(descriptors) == 6, "six source descriptors")
    instructions = {}
    for row in sequence:
        pc, op = row.get("original_PC"), row.get("actual_ROM_instruction_hex")
        insist(type(pc) is str and type(op) is str and pc not in instructions,
               "duplicate/invalid original instruction PC")
        try:
            raw = bytes.fromhex(op)
        except ValueError as exc:
            raise ValueError("invalid original executed opcode bytes") from exc
        insist(len(raw) > 0, "empty original opcode")
        instructions[pc] = raw
    target_values = {}
    pcs = set()
    for record in observed:
        pc, target, value = (record.get("original_PC"),
                             record.get("WRAM"), record.get("observed_byte"))
        insist(type(pc) is str and pc in instructions and pc not in pcs,
               "writer PC absent/duplicated in executed original")
        pcs.add(pc)
        try:
            op = bytes.fromhex(record["ROM_instruction_hex"])
            observed_byte = bytes.fromhex(value)
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError("invalid writer source bytes") from exc
        insist(len(op) == 4 and op[0] == 0x8F and
               instructions[pc] == op and len(observed_byte) == 1,
               "STA-long 4-byte opcode mismatch")
        decoded = f"{op[3]:02X}:{op[2]:02X}{op[1]:02X}"
        insist(target == decoded and target not in target_values,
               "STA-long instruction not mapped to claimed distinct WRAM")
        target_values[target] = observed_byte[0]
    expected_targets = {f"7E:{address:04X}" for address in range(0x2084, 0x2096)}
    insist(set(target_values) == expected_targets, "18 contiguous descriptor bytes")
    seen_starts = []
    for index, desc in enumerate(descriptors):
        start = f"7E:{0x2084 + 3 * index:04X}"
        insist(desc.get("entry") == index and desc.get("start") == start and
               desc.get("viewport") == ("upper" if index < 3 else "lower"),
               "source viewport descriptor order")
        address = 0x2084 + 3 * index
        for offset, field in enumerate(("line_count_byte", "cgadsub", "coldata")):
            byte = desc.get(field)
            insist(type(byte) is str and re.fullmatch(r"[A-Fa-f0-9]{2}", byte) is not None
                   and target_values[f"7E:{address+offset:04X}"] == int(byte, 16),
                   "descriptor byte not written by executed original source")
        insist(desc["cgadsub"] == "04", "six source CGADSUB bytes")
        seen_starts.append(start)
    insist(writer.get("native_channel5_mode1_CGADSUB_COLDATA_pairs_strictly_accepted") is True
           and writer.get("full_original_native_same_input_frame_parity_proven") is False
           and writer.get("physical_SNES_midline_timing_proven") is False
           and writer.get("HD_racer_character_approved") is False,
           "unsupported channel-5 release claim")

    orig_entry = fade.get("original_guest_entry_absolute_host")
    native_entry = fade.get("native_guest_entry_absolute_host")
    insist(type(orig_entry) is int and type(native_entry) is int and
           (orig_entry, native_entry) == (1604, 1606), "scene entry identities")
    blank = fade.get("first_persistent_ppu_blank")
    insist(type(blank) is dict and
           blank.get("original_relative") == blank.get("native_relative") == 5034
           and blank.get("original_absolute_host") == orig_entry + 5034
           and blank.get("native_absolute_host") == native_entry + 5034
           and blank.get("inidisp") == 128, "forced blank first onset")
    steps = fade.get("fade_brightness_steps")
    insist(type(steps) is list and len(steps) == 7, "seven PPU fade steps")
    exact_full_register_matches = 0
    for index, step in enumerate(steps):
        host = 6770 + index
        insist(step.get("ppu_brightness") == 2 + 2 * index and
               step.get("original_absolute_host") == host and
               step.get("native_absolute_host") == host and
               step.get("original_scene_relative") + orig_entry == host and
               step.get("native_scene_relative") + native_entry == host,
               "unaligned original/native PPU absolute-host brightness frame")
        first = step.get("original_ppu_regs_sha256")
        second = step.get("native_ppu_regs_sha256")
        insist(valid_hash(first) and valid_hash(second), "missing exact PPU register hashes")
        exact_full_register_matches += first == second
    interp = fade.get("interpretation")
    insist(type(interp) is dict and
           interp.get("seven_brightness_steps_exact_absolute_host_aligned") is True
           and interp.get("original_native_guest_cpu_ppu_scanline_phase_proven_equivalent") is False
           and interp.get("source_gameplay_finish_instruction_identified") is False
           and interp.get("original_native_race_return_fade_result_complete_event_strict_equal") is False
           and interp.get("approved_usa_events") == 0
           and interp.get("total_usa_events") == 45 and
           interp.get("source_result_menu_onset_guest_relative") == 5163
           and interp.get("native_result_menu_onset_guest_relative") == 5162,
           "original/native scored-event equivalence not established")

    return {
        "classification": "retained-source-summary-consistency-only",
        "original_source_writer_instructions_crosschecked": len(pcs),
        "original_source_opcode_records_crosschecked": len(instructions),
        "original_channel5_source_descriptors_crosschecked": len(seen_starts),
        "same_absolute_host_brightness_steps": len(steps),
        "full_original_native_ppu_register_hash_matches": exact_full_register_matches,
        "full_ppu_register_images_independently_replayed": False,
        "source_native_same_input_final_pixels_verified": False,
        "source_native_complete_course_accepted_from_these_files": False,
        "current_release_gate_credit_from_these_files": 0,
        "physical_hardware_verified_from_these_files": False,
        "source_original_2p_artifact_sha256_producer_recorded":
            writer["original_opcode_archive_zip_SHA256"],
        "source_zoo_artifact_sha256_producer_recorded": fade["real_artifact_sha256"],
        "outcome": "no-release-promotion",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, default=WRITER)
    parser.add_argument("--fade", type=Path, default=FADE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    original_bytes = args.original.read_bytes()
    fade_bytes = args.fade.read_bytes()
    result = audit(json.loads(original_bytes), json.loads(fade_bytes))
    result["channel5_retained_json_sha256"] = hashlib.sha256(original_bytes).hexdigest()
    result["zoo_fade_retained_json_sha256"] = hashlib.sha256(fade_bytes).hexdigest()
    body = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(body, encoding="utf-8")
    else:
        print(body, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
