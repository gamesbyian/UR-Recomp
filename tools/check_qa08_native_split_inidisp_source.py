#!/usr/bin/env python3
"""Strict, true native AOT $2100 HDMA BBUS source transfer evidence.

Requires previously independently accepted native colour/PPU and original
finished source-pixel seam evidence, but does not predict transfer tags.
Distinguish DMA transfer, live PPU register readback and resulting pixels.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

PATTERN=re.compile(
    r"^UR_QA08_HDMA_INIDISP frame=(\d+) tagframe=(\d+) line=(-?\d+) "
    r"channel=(\d+) bbus=([0-9A-F]{2}) value=([0-9A-F]{2}) "
    r"src=([0-9A-F]{2}):([0-9A-F]{4}) mode=(\d+) indirect=(\d+) "
    r"table=([0-9A-F]{4}) bank=([0-9A-F]{2}) live_inidisp=([0-9A-F]{2})$"
)
SCHEMA="qa08-original-Snes9x-native-2P-256x224-split-band-pixel-source-handoff/1"


def read(path:Path)->dict:
    def unique(pairs):
        out={}
        for k,v in pairs:
            if k in out:raise ValueError("duplicate evidence field")
            out[k]=v
        return out
    return json.loads(path.read_text(encoding="utf8"),object_pairs_hook=unique)


def check(log:str, native:dict, seam:dict)->dict:
    if (native.get("schema")!="qa08-original-native-channel5-coldata-source-handoff/1"
            or native.get("original_native_AOT_run")!=38504531564
            or native.get("native_PPU_2P_guest_frame")!=2208
            or native.get("identical_original_guest_CRC_records")!=2473
            or native.get("HDMA_channel")!=5
            or native.get("HDMA_mode")!=1
            or native.get("source_overlay_BG3_OBJ_pixels_native_accepted")!=26
            or seam.get("schema")!=SCHEMA
            or seam.get("original_source_run")!=38543766102
            or seam.get("native_source_run")!=38504531564
            or seam.get("identical_pixels_after_channel_bit_depth_normalization")!=56832
            or seam.get("wrong_pixels_only_rows")!=[
                {"row":111,"count":256},{"row":113,"count":256}]
            or seam.get("original_PPUW_GO_1989_actual_INIDISP_HDMA_events")!=[
                {"original_beam_v":111,"reg":"$2100","value":"$00"},
                {"original_beam_v":113,"reg":"$2100","value":"$0F"}]):
        raise ValueError("independent native/original 2P source-pixel evidence not admitted")
    lines=log.splitlines()
    if any("UR_QA08_HDMA_INIDISP_OVERFLOW" in s for s in lines):
        raise ValueError("native actual PPU $2100 source witness exceeded limit")
    actual=[s for s in lines if "UR_QA08_HDMA_INIDISP " in s]
    if not 2<=len(actual)<=2048:
        raise ValueError("genuine native inidisp HDMA BBUS source and restore missing")
    records=[]
    for i,row in enumerate(actual):
        m=PATTERN.fullmatch(row)
        if not m:
            raise ValueError("malformed actual native inidisp PPU/HDMA transfer")
        (frame,tagframe,line,channel,bbus,value,bank,src,mode,indirect,
         table,tablebank,live)=m.groups()
        frame,tagframe,line,channel,mode,indirect=map(
            int,(frame,tagframe,line,channel,mode,indirect))
        if (frame!=2208 or tagframe!=2208 or line < -1 or line>261
                or channel not in range(8) or bbus!="00"
                or mode not in range(8) or indirect not in (0,1)
                or live!=value or int(table,16)>0xffff):
            raise ValueError("native INIDISP source/PPU readback frame or register mismatch")
        if records and line < records[-1]["native_source_log_tag"]:
            raise ValueError("native source HDMA INIDISP tags are not chronological")
        records.append({
            "ordinal":i,"native_guest_frame":frame,
            "native_source_log_tag":line,
            "channel":channel,"mode":mode,"indirect":bool(indirect),
            "source_ABus":bank+":"+src,"table_current":table,
            "table_bank":tablebank,"true_BBUS_register":"$2100",
            "actual_HDMA_byte":"0x"+value,
            "actual_PPU_INIDISP_after_write":"0x"+live
        })
    forced=[r for r in records if r["actual_HDMA_byte"]=="0x00"]
    restored=[r for r in records if r["actual_HDMA_byte"]=="0x0F"]
    if not forced or not restored or not any(
            r["native_source_log_tag"]>f["native_source_log_tag"]
            for f in forced for r in restored):
        raise ValueError("no actual native forced-blank then bright restore HDMA source")
    return {
        "schema":"qa08-native-2P-real-HDMA-2100-INIDISP-source-split-probe/1",
        "status":"true native source after-BBUS INIDISP HDMA register write witnessed",
        "native_guest_frame":2208,
        "actual_original_fully_normalized_pixel_mismatch_rows":[111,113],
        "original_Snes9x_INIDISP_forced_blank_V":[111,113],
        "actual_native_INIDISP_events":len(records),
        "real_native_source_register_writes":records,
        "first_native_forced_blank_tags":[x["native_source_log_tag"] for x in forced],
        "first_native_unblank_tags":[x["native_source_log_tag"] for x in restored],
        "source_writes_are_automatically_final_RBG_pixels":False,
        "native_register_log_tags_directly_physical_HBlank_certified":False,
        "native_render_row_vs_original_frame_phase_source_accepted":False,
        "original_native_pixel_colour_except_seam_originally_measured":True,
        "native_PPU_modified_for_this_probe":False,
        "hardware_Timing_or_HD_art_approved":False,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log",type=Path,required=True)
    p.add_argument("--native-evidence",type=Path,required=True)
    p.add_argument("--pixel-seam-evidence",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=check(a.log.read_text(encoding="utf8",errors="replace"),
                 read(a.native_evidence),read(a.pixel_seam_evidence))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("QA08_NATIVE_SPLIT_INIDISP_SOURCE_ACCEPTED "
          f"actual_writes={result['actual_native_INIDISP_events']} "
          "native_row_timing=unverified")

if __name__=="__main__":
    main()
