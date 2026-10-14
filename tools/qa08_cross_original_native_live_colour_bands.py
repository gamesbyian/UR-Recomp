#!/usr/bin/env python3
"""Independent original Snes9x/live native colour-source band adjudicator.

Checks the SAME six guest-built channel5 descriptor entries as actually
written by both interpreters, without pretending original Snes9x V tags
are Baldosa's renderer tags or that frames/finished pixels are aligned.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ORIGINAL = "qa08-original-2p-channel5-two-source-original-Snes9x-PPU-handoff/1"
NATIVE = "qa08-original-native-channel5-coldata-source-handoff/1"
PIXELS = "qa08-original-native-2p-bg3-obj-26-pixel-palette-fingerprint/1"
ROM = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
REFZIP = "17380f2e8d5c7d2f43eac5bd98cf5661d9fb1c3900cd7cafb1b9479784ada234"
RPT = "cb48890b00c9247a20cf5ec0aeec44bd06fec709120c86a36c5b9ad5b8b39ef9"

def read(path: Path) -> dict:
    def unique(pairs):
        out={}
        for k,v in pairs:
            if k in out:
                raise ValueError("duplicate original/native register source JSON key")
            out[k]=v
        return out
    return json.loads(path.read_text(encoding="utf8"), object_pairs_hook=unique)

def check(original: dict,native: dict,pixel: dict) -> dict:
    if (original.get("schema")!=ORIGINAL or native.get("schema")!=NATIVE or
            pixel.get("schema")!=PIXELS or
            original.get("original_USA_ROM_sha256")!=ROM or
            original.get("downloaded_zip_sha256")!=REFZIP or
            original.get("live_ppu_after_write_report_sha256")!=RPT or
            original.get("original_source_workflow_run")!=38521827670 or
            native.get("original_native_AOT_run")!=38504531564 or
            pixel.get("source_native_run")!=38502862996 or
            native.get("native_PPU_2P_guest_frame")!=2208 or
            pixel.get("guest_frame")!=2208 or
            original.get("real_original_Snes9x_live_register_writes")!=96 or
            original.get("channel5_mode1_direct_31_32_pairs")!=48 or
            original.get("source_WRAM_equals_BBUS_writes")!=96 or
            original.get("source_bytes_match_executed_original_table")!=96 or
            original.get("original_sampled_cpu_frames")!=
            [1988,1989,1990,2231,2232,2233,2471,2472] or
            original.get("six_pairs_each_sampled_cpu_frame") is not True or
            native.get("HDMA_channel")!=5 or native.get("HDMA_mode")!=1 or
            native.get("HDMA_indirect") is not False or
            native.get("A_bus_WRAM_bank")!="$7E" or
            native.get("identical_original_guest_CRC_records")!=2473 or
            pixel.get("native_guest_crc_records")!=2473 or
            pixel.get("stock_BG3_main_OBJ_subscreen_26_accepted") is not True):
        raise ValueError("independent original Snes9x/native source provenance missing")

    orig=original.get("register_pairs_each_frame")
    writes=native.get("native_writes")
    if not isinstance(orig,list) or len(orig)!=6 or not isinstance(writes,list) or len(writes)!=7:
        raise ValueError("six original source register pairs and seven native writes required")
    if not (writes[0]["ordinal"]==0 and writes[1]["ordinal"]==1 and
            writes[0]["A_bus_byte_address"]==writes[1]["A_bus_byte_address"] and
            writes[0]["COLDATA_value"]==writes[1]["COLDATA_value"] and
            writes[0]["fixed_RGB15_after_write"]==writes[1]["fixed_RGB15_after_write"] and
            writes[0]["native_write_log_tag"]==0 and
            writes[1]["native_write_log_tag"]==2):
        raise ValueError("native first-line priming is not source confirmed")
    pairs=[]
    for i,row in enumerate(orig):
        seen=writes[i+1]
        exp=0x2084+3*i
        src=f"7E:{exp+2:04X}"
        first=f"7E:{exp+1:04X}"
        value="0x"+row["COLDATA"]
        fixed="0x"+row["fixed_RGB15_after_COLDATA"]
        if (row["original_beam_v"] not in (0,1,2,111,112,113) or
            row["original_beam_v"]!=[0,1,2,111,112,113][i] or
            row["original_WRAM_CGADSUB"]!=first or
            row["original_WRAM_COLDATA"]!=src or
            row["CGADSUB"]!="04" or
            seen["ordinal"]!=i+1 or
            seen["A_bus_byte_address"]!=src or
            seen["COLDATA_value"]!=value or
            seen["fixed_RGB15_after_write"]!=fixed or
            seen["native_write_log_tag"]!=row["original_beam_v"]+2):
            raise ValueError("real original/native HDMA source, byte, live fixed RGB or tag relation differs")
        pairs.append({
            "index":i, "original_emulator_source_V":row["original_beam_v"],
            "native_renderer_write_tag":seen["native_write_log_tag"],
            "tag_difference_native_minus_original":2,
            "source_CGADSUB":first, "source_COLDATA":src,
            "original_and_native_CGADSUB":"0x04",
            "original_and_native_COLDATA":value,
            "original_and_native_after_write_fixed_RGB15":fixed})
    # The two known native PPU output rows are strictly within stable
    # descriptor bands, not on either renderer's boundary/HDMA tag.
    if (not (2<50<111 and 113<162<224) or
            pairs[2]["original_and_native_after_write_fixed_RGB15"]!="0x000F" or
            pairs[5]["original_and_native_after_write_fixed_RGB15"]!="0x0260" or
            native.get("upper_output_row50_live_fixed_RGB15")!="0x000F" or
            native.get("lower_output_row162_live_fixed_RGB15")!="0x0260" or
            pixel.get("upper_live_fixed_RGB15")!="0x000F" or
            pixel.get("lower_live_fixed_RGB15")!="0x0260" or
            pixel.get("source_pairs_each_viewport")!=13 or
            pixel.get("cross_viewport_unchanged_src_final_RGB5_pairs")!=13 or
            pixel.get("bg3_main_RGB15")!="0x000D" or
            pixel.get("upper_after_front98_removed_RGB5")!=[28,0,0] or
            pixel.get("lower_after_front96_removed_RGB5")!=[13,19,0]):
        raise ValueError("original/native register bands or authentic native PPU RGB5 source disagrees")
    return {
        "schema":"qa08-independent-original-native-channel5-live-register-band-parity/1",
        "status":"six-original-live-PPU-source-transfers-match-six-native-HDMA-descriptors",
        "original_source_run":38521827670,"native_source_run":38504531564,
        "independent_native_pixel_source_run":38502862996,
        "six_real_original_native_source_bytes_and_fixed_RGB15_match":True,
        "native_extra_first-line_prime_confirmed":True,
        "native_source_tags_offset_from_original_by_two":True,
        "native_pure_bg3_obj_26_pixel_compose_report_preserved":True,
        "native_upper_row50_fixed_RGB15":"0x000F",
        "native_lower_row162_fixed_RGB15":"0x0260",
        "same_input_frame_counters_and_camera_verified":False,
        "original_Snes9x_row50_and_row162_final_pixel_RGB_authenticated":False,
        "original_native_final_pixels_equal":False,
        "physical_SNES_HBlank_timing_verified":False,
        "HD_remastered_art_approved":False,
        "source_pairs":pairs
    }

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("original","native","pixels","out"):
        p.add_argument("--"+key,type=Path,required=True)
    a=p.parse_args()
    report=check(read(a.original),read(a.native),read(a.pixels))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("QA08_ORIGINAL_NATIVE_LIVE_HDMA_SOURCE_BANDS_ACCEPTED pairs=6 "
          "native_priming=1 tags_differ_by_2 final_original_native_RGB=unproved")

if __name__=="__main__":
    main()
