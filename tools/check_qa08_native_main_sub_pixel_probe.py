#!/usr/bin/env python3
"""Accept a genuine same-guest native PPU main/sub pixel-composition witness.

Records real per-pixel PPU main and subscreen buffers, not a synthetic layer
observer. The three existing native 2P routes must already pass full CRC and
source-removal acceptance; this rechecks Original raster hashes and RGB.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

PAM = b"P7\nWIDTH 342\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"
EXPECTED = {(133, 50), (133, 162)}
PATTERN = re.compile(
    r"^UR_QA08_NATIVE_PPU_PIXEL frame=(\d+) x=(\d+) y=(\d+) "
    r"main=([0-9A-F]{4}) sub=([0-9A-F]{4}) "
    r"main15=([0-9A-F]{4}) sub15=([0-9A-F]{4}) "
    r"final=([0-9A-F]{6}) cgadsub=([0-9A-F]{2}) "
    r"cgwsel=([0-9A-F]{2}) fixed15=([0-9A-F]{4}) "
    r"math=([01]) rendered_sub=([01]) sub_present=([01]) "
    r"clip_main=([01])$"
)
STOCK_SHA = "f9ca59c19dc3e8d51c7ca1dbce25d5dc14e56ba36011128abbadee8cec0e7b4a"


def load_pam(path: Path, expected_sha: str) -> bytes:
    data = path.read_bytes()
    if not data.startswith(PAM) or len(data) != len(PAM) + 342*224*4:
        raise ValueError("not an exact 342x224 native Original P7 image")
    raw = data[len(PAM):]
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError("captured original PPU raster SHA differs")
    return raw


def read_samples(log: Path, rgba: bytes) -> dict:
    lines = [line for line in log.read_text(encoding="utf8", errors="replace").splitlines()
             if "UR_QA08_NATIVE_PPU_PIXEL" in line]
    if len(lines) != len(EXPECTED):
        raise ValueError("not two genuine PPU main/sub pixel source observations")
    result = {}
    for line in lines:
        match = PATTERN.fullmatch(line)
        if match is None:
            raise ValueError("malformed native PPU pixel line")
        frame,x,y=map(int,match.group(1,2,3))
        if frame != 2208 or (x,y) not in EXPECTED or (x,y) in result:
            raise ValueError("wrong/duplicate native pixel frame or coordinates")
        main,sub,main15,sub15,final,adsub,wsel,fixed15=[
            int(value,16) for value in match.group(4,5,6,7,8,9,10,11)]
        math,rendered,sub_present,clip=map(int,match.group(12,13,14,15))
        if (main15 > 0x7fff or sub15 > 0x7fff or fixed15 != 0x0260 or
                adsub != 0x04 or wsel != 0x02 or
                sub_present != int((sub & 255) != 0)):
            raise ValueError("native pixel record conflicts with field registers/PPU")
        offset=4*(342*y+x)
        pixel=rgba[offset:offset+4]
        if final != (pixel[0]<<16 | pixel[1]<<8 | pixel[2]):
            raise ValueError("native PPU composer final RGB disagrees with immutable Original")
        result[(x,y)] = {
            "main_zbuf":f"0x{main:04X}",
            "main_layer":(main>>8)&15,
            "main_palette_index":main&255,
            "main_RGB15":f"0x{main15:04X}",
            "sub_zbuf":f"0x{sub:04X}",
            "sub_layer":(sub>>8)&15,
            "sub_palette_index":sub&255,
            "sub_RGB15":f"0x{sub15:04X}",
            "final_RGB24":f"0x{final:06X}",
            "math_eligible_at_window_and_layer":bool(math),
            "subscreen_actually_drawn":bool(rendered),
            "subscreen_pixel_present":bool(sub_present),
            "main_colour_not_clipped":bool(clip),
        }
    return result


def verify(stock: Path, stock_log: Path, removed98: Path, removed98_log: Path,
           removed96: Path, removed96_log: Path, causal: Path, journal: Path) -> dict:
    evidence=json.loads(causal.read_text(encoding="utf8"))
    trace=json.loads(journal.read_text(encoding="utf8"))
    if (trace.get("full_native_guest_CRC_entries_equal") != 2473 or
            trace.get("full_original_342x224_RGBA_SHA256") != STOCK_SHA or
            evidence.get("guest_frame") != 2208):
        raise ValueError("original native full CRC/journal gate missing")
    for name in ("completed", "recording"):
        state=trace["field_register_journals"][name]["beam_order_colour_knowledge"]
        spans=state["visible_line_tag_intervals_after_same_line_final_write"]
        if spans != [{
            "first_visible_line_tag":0, "last_visible_line_tag":223,
            "cgadsub":"0x04", "cgwsel":"0x02",
            "fixed_R5_G5_B5":[0,19,0], "fixed_rgb15":"0x0260",
        }]:
            raise ValueError("native field state disagrees with PPU pixel probe")
    original=load_pam(stock, STOCK_SHA)
    result={"stock":read_samples(stock_log,original)}
    for slot,path,log in ((98,removed98,removed98_log),(96,removed96,removed96_log)):
        record=evidence["per_original_front_slot"][str(slot)]
        if (record["all_four_guest_crc_streams_equal_at_exact_frame_count"] != 2473 or
                record["authentic_native_arm_marker_one"] is not True):
            raise ValueError("original/native counterfactual guest CRC gate missing")
        rgba=load_pam(path, record["native_front_removed_original_sha256"])
        result[f"removed{slot}"]=read_samples(log,rgba)
    top=(133,50)
    bottom=(133,162)
    stock_top=result["stock"][top]
    stock_bottom=result["stock"][bottom]
    source_top=(stock_top["main_layer"]==2 and stock_top["sub_layer"]==4 and
                stock_top["math_eligible_at_window_and_layer"] and
                stock_top["subscreen_pixel_present"] and
                stock_top["subscreen_actually_drawn"])
    source_bottom=(stock_bottom["main_layer"]==2 and stock_bottom["sub_layer"]==4 and
                   stock_bottom["math_eligible_at_window_and_layer"] and
                   stock_bottom["subscreen_pixel_present"] and
                   stock_bottom["subscreen_actually_drawn"])
    return {
        "status":"original-native-2p-per-pixel-PPU-main-sub-source-observed",
        "guest_frame":2208,
        "original_raster_SHA256":STOCK_SHA,
        "full_guest_CRC_equal":2473,
        "native_exact_composition_rows":[50,162],
        "upper_BG3_main_OBJ_subscreen_observed":bool(source_top),
        "lower_BG3_main_OBJ_subscreen_observed":bool(source_bottom),
        "main_sub_selection_proven_at_other_pixels":False,
        "physical_SNES_PPU_priority_proven":False,
        "remastered_HD_art_approved":False,
        "positions":{
            name:{
                f"{x},{y}":sample for (x,y),sample in sorted(rows.items())
            } for name,rows in result.items()
        },
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ("stock","stock-log","removed98","removed98-log","removed96",
                 "removed96-log","causal","journal","out"):
        ap.add_argument("--"+name, required=True, type=Path)
    args=ap.parse_args()
    result=verify(args.stock,args.stock_log,args.removed98,args.removed98_log,
                  args.removed96,args.removed96_log,args.causal,args.journal)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("UR_QA08_NATIVE_PPU_MAIN_SUB_ACCEPTED guest=2208 "
          f"BG3_OBJ_top={int(result['upper_BG3_main_OBJ_subscreen_observed'])} "
          f"BG3_OBJ_bottom={int(result['lower_BG3_main_OBJ_subscreen_observed'])} "
          "source_pixel_observed=1 physical_console=0 HD_admitted=0")


if __name__ == "__main__":
    main()
