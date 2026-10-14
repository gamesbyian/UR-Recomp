#!/usr/bin/env python3
"""Cross-check retained independent QA-08 source, HDMA and pixel evidence.

All input artifacts are *previously accepted* compact witness records. This
checker cannot manufacture a fresh original PPU render or prove original/native
same-frame parity. It verifies the byte/address/line/colour links between those
records, rejecting stale SETINI assumptions and forged implied pixel states.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

LAYOUT = "qa08-original-2p-channel5-HDMA-executed-opcode-source-layout/1"
CENSUS = "qa08-original-Snes9x-2P-WRAM-colour-HDMA-executed-writer-census/1"
NATIVE = "qa08-original-native-channel5-coldata-source-handoff/1"
PIXELS = "qa08-original-native-2p-bg3-obj-26-pixel-palette-fingerprint/1"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate evidence JSON key: {key}")
        result[key] = value
    return result


def read(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object)
    if not isinstance(result, dict):
        raise ValueError("evidence JSON root must be an object")
    return result


def _byte(value: str) -> int:
    if not isinstance(value, str) or len(value) != 2:
        raise ValueError("invalid source byte")
    return int(value, 16)


def _colour_write(current: int, byte: int) -> int:
    """Native PPU $2132 individual RGB-channel enable bits (not RGB332)."""
    for mask, shift in ((0x20, 0), (0x40, 5), (0x80, 10)):
        if byte & mask:
            current = (current & ~(31 << shift)) | ((byte & 31) << shift)
    return current


def check(layout: dict, census: dict, native: dict, pixel: dict) -> dict:
    if (layout.get("schema") != LAYOUT or census.get("schema") != CENSUS or
            native.get("schema") != NATIVE or pixel.get("schema") != PIXELS):
        raise ValueError("wrong source, original census, native or pixel schema")
    if (layout.get("original_USA_ROM_SHA256") != ROM_SHA or
            census.get("original_USA_ROM_SHA256") != ROM_SHA or
            layout.get("original_guest_frame") != 1781 or
            census.get("source_writes_frames_observed") != [1781] or
            layout.get("original_2P_input_script_SHA256") !=
            census.get("original_Snesref_converted_script_SHA256") or
            layout.get("original_full_t480_WRAM_SHA256") !=
            census.get("original_2P_t480_WRAM_SHA256") or
            layout.get("original_independently_executed_writer_PCs") != 18 or
            layout.get("original_executed_instructions_captured") != 55 or
            census.get("source_changed_WRAM_byte_record_count") != 18 or
            census.get("independent_original_processes") != 10 or
            layout.get("original_Snes9x_opcode_run") != 38516727525 or
            native.get("original_native_AOT_run") != 38504531564 or
            pixel.get("source_native_run") != 38502862996 or
            native.get("native_PPU_2P_guest_frame") != 2208 or
            pixel.get("guest_frame") != 2208 or
            pixel.get("source_original_RGBA_SHA256") !=
            "f9ca59c19dc3e8d51c7ca1dbce25d5dc14e56ba36011128abbadee8cec0e7b4a" or
            native.get("identical_original_guest_CRC_records") != 2473 or
            pixel.get("native_guest_crc_records") != 2473 or
            any(d.get("full_original_native_same_input_frame_parity_proven") is not False
                for d in (layout, census))):
        raise ValueError("original/native ROM, route, frame or candidate provenance differs")

    seq = layout.get("original_source_opcode_sequence")
    writers = layout.get("original_executed_65816_writer_PC_and_WRAM_target")
    changes = census.get("source_byte_changes")
    if (not isinstance(seq, list) or len(seq) != 55 or
            not isinstance(writers, list) or len(writers) != 18 or
            not isinstance(changes, list) or len(changes) != 18):
        raise ValueError("55 original opcodes / 18 executed writer PCs required")
    opmap = {s["original_PC"]: s["actual_ROM_instruction_hex"] for s in seq}
    if len(opmap) != 55:
        raise ValueError("duplicate executed original CPU PC")
    source_bytes = {}
    for writer, change in zip(writers, changes):
        pc = writer["original_PC"]
        hexcode = writer["ROM_instruction_hex"]
        addr = writer["WRAM"]
        if (opmap.get(pc) != hexcode or len(hexcode) != 8 or
                hexcode[:2] != "8F" or hexcode[-2:] != "7E" or
                addr != f"7E:{int(hexcode[4:6]+hexcode[2:4],16):04X}" or
                pc.replace(":", "") != change["executed_65816_PC"] or
                addr[3:] != change["WRAM_address"] or
                writer["observed_byte"] != change["after"] or
                change["WRAM_bank"] != "7E" or
                change["original_Snes9x_frame"] != 1781):
            raise ValueError("executed original STA-long source/PC/WRAM mismatch")
        if addr in source_bytes:
            raise ValueError("duplicate original WRAM writer destination")
        source_bytes[addr] = writer["observed_byte"]
    if set(source_bytes) != {f"7E:{i:04X}" for i in range(0x2084, 0x2096)}:
        raise ValueError("18 original source-table addresses incomplete")
    # Actually executed lookup and branch only: do not decode the untaken
    # alternate branch or infer any other racer's palette.
    control = {"82:D5CD":"AF480777", "82:D5D4":"BF2AD582",
               "82:D60C":"AF500777", "82:D610":"8908",
               "82:D612":"F006", "82:D614":"AF490777",
               "82:D618":"8004", "82:D621":"BF2AD582"}
    if (any(opmap.get(pc) != op for pc, op in control.items()) or
            layout.get("ROM_LUT_base") != "82:D52A" or
            layout.get("first_viewport_selector_address") != "77:0748" or
            layout.get("second_viewport_selected_source_address_on_observed_path") != "77:0749"):
        raise ValueError("actual original 65816 palette lookup/branch differs")

    triples = layout.get("original_table_triplets")
    if not isinstance(triples, list) or len(triples) != 6:
        raise ValueError("six executed original HDMA descriptors required")
    expected_addresses = []
    expected_bytes = []
    for i, row in enumerate(triples):
        start = 0x2084 + 3 * i
        if (row["entry"] != i or row["viewport"] != ("upper" if i < 3 else "lower") or
                row["start"] != f"7E:{start:04X}"):
            raise ValueError("original HDMA descriptor order/viewport mismatch")
        actual = [source_bytes[f"7E:{start+j:04X}"] for j in range(3)]
        documented = [row[k] for k in ("line_count_byte", "cgadsub", "coldata")]
        if (actual != documented or documented[0] != ("6D" if i % 3 == 2 else "01") or
                documented[1] != "04"):
            raise ValueError("original executed HDMA descriptor byte mismatch")
        expected_addresses.append(f"7E:{start+2:04X}")
        expected_bytes.append(documented[2])

    if (native.get("HDMA_channel") != 5 or native.get("HDMA_mode") != 1 or
            native.get("HDMA_indirect") is not False or
            native.get("A_bus_WRAM_bank") != "$7E" or
            native.get("PPU_BBUS_register") != "$2132" or
            native.get("source_overlay_BG3_OBJ_pixels_native_accepted") != 26):
        raise ValueError("native HDMA channel/register/PPU source gate differs")
    records = native.get("native_writes")
    if not isinstance(records, list) or len(records) != 7:
        raise ValueError("exactly seven genuine native COLDATA writes required")
    index_order = [0, 0, 1, 2, 3, 4, 5]  # first-line prime repeated in HDMA
    tags = [0, 2, 3, 4, 113, 114, 115]
    states = []
    for i, (record, index, tag) in enumerate(zip(records, index_order, tags)):
        val = _byte(expected_bytes[index])
        fixed = int(record["fixed_RGB15_after_write"], 16)
        if (record["ordinal"] != i or
                record["A_bus_byte_address"] != expected_addresses[index] or
                record["COLDATA_value"] != f"0x{val:02X}" or
                record["native_write_log_tag"] != tag or not 0 <= fixed <= 0x7FFF):
            raise ValueError("actual native channel-5 byte/address/beam tag differs")
        if i == 0 and fixed & 31 != 15:
            raise ValueError("first live native COLDATA red selector not applied")
        if i and _colour_write(states[-1], val) != fixed:
            raise ValueError("native live PPU fixed RGB15 contradicts preceding HDMA write")
        states.append(fixed)

    def at_row(y: int) -> int:
        # Pinned native renderer: normal transfer tag L is made after row
        # L-2 and before row L-1; tag0 is a separate first-line prime.
        return states[max(i for i, tag in enumerate(tags)
                          if tag == 0 or (2 <= tag <= y + 1))]

    if (at_row(50) != 0x000F or at_row(162) != 0x0260 or
            native.get("upper_output_row50_live_fixed_RGB15") != "0x000F" or
            native.get("lower_output_row162_live_fixed_RGB15") != "0x0260" or
            pixel.get("upper_live_fixed_RGB15") != "0x000F" or
            pixel.get("lower_live_fixed_RGB15") != "0x0260" or
            pixel.get("source_pairs_each_viewport") != 13 or
            pixel.get("cross_viewport_unchanged_src_final_RGB5_pairs") != 13 or
            pixel.get("stock_BG3_main_OBJ_subscreen_26_accepted") is not True or
            pixel.get("bg3_main_RGB15") != "0x000D" or
            pixel.get("upper_after_front98_removed_RGB5") != [28, 0, 0] or
            pixel.get("lower_after_front96_removed_RGB5") != [13, 19, 0]):
        raise ValueError("native HDMA-to-live-register-to-26-pixel PPU observation mismatch")
    histogram = pixel.get("shade_histogram_each_viewport")
    if (not isinstance(histogram, list) or sum(h["pixels"] for h in histogram) != 13):
        raise ValueError("observed original OBJ/BG3 source shade histogram incomplete")
    for h in histogram:
        rgb = h["source_RGB5"]
        if (not isinstance(rgb, list) or len(rgb) != 3 or
                rgb[0] | (rgb[1] << 5) | (rgb[2] << 10) != int(h["source_RGB15"], 16) or
                h["normal_final_RGB5"] != [rgb[0]+13, rgb[1], rgb[2]] or
                max(h["normal_final_RGB5"]) > 31):
            raise ValueError("observed original PPU RGB5 source/final arithmetic differs")

    return {
        "schema": "qa08-original-writer-native-channel5-live-colour-pixel-crosswalk/1",
        "evidence_class": "cross-validation of previously source-accepted independent records",
        "original_ROM_SHA256": ROM_SHA,
        "original_65816_frame": 1781,
        "native_2P_PPU_frame": 2208,
        "original_executed_opcode_count": 55,
        "original_executed_WRAM_store_count": 18,
        "original_direct_HDMA_descriptor_count": 6,
        "native_live_COLDATA_writes": 7,
        "native_HDMA_first_byte_primed_twice": True,
        "native_channel5_mode1_direct_CGADSUB_source_values": ["0x04"]*6,
        "native_source_colour_writes": [
            {"row_after_transfer": None if tag == 0 else tag-1,
             "write_tag": tag, "source": expected_addresses[index],
             "COLDATA": f"0x{_byte(expected_bytes[index]):02X}",
             "live_fixed_RGB15_after_write": f"0x{state:04X}"}
            for tag, index, state in zip(tags, index_order, states)],
        "observed_native_row50_live_fixed_RGB15": f"0x{at_row(50):04X}",
        "observed_native_row162_live_fixed_RGB15": f"0x{at_row(162):04X}",
        "original_native_BG3_OBJ_overlap_pixels_independently_observed": 26,
        "final_RGB5_26_pixel_fingerprint_revalidated": True,
        "source_CPU_journal_is_live_HDMA": False,
        "original_native_same_input_frame_parity_proven": False,
        "physical_SNES_pixel_timing_proven": False,
        "all_racer_pixels_covered": False,
        "HD_character_likeness_approved": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layout", type=Path, required=True)
    parser.add_argument("--census", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--pixels", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = check(read(args.layout), read(args.census),
                   read(args.native), read(args.pixels))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2)+"\n", encoding="utf8")
    print("QA08_CHANNEL5_SOURCE_TO_PIXEL_CROSSWALK_ACCEPTED "
          "original_writers=18 native_live_hdma=7 observed_native_pixels=26 "
          "full_original_native_parity=0")


if __name__ == "__main__":
    main()
