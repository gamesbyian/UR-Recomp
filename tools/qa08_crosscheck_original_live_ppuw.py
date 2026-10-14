#!/usr/bin/env python3
"""Cross-check two independently recorded surfaces of ONE original Snes9x frame.

Original PPU-write ring (.ppuw.tsv) and read-only original S9xSetPPU
after-write observer must agree on all 12 channel-5 $2131/$2132
events at authentic 2P GO, including frame, V, register, byte, and
source. This cannot align the original frame with native guest2208.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.qa08_original_snesref_raster_source import read_frame
except ImportError:
    from qa08_original_snesref_raster_source import read_frame

SCHEMA="qa08-original-Snes9x-executed-channel5-live-PPU-HDMA/1"
MARK="qa08-original-2p-channel5-PPU-dual-observer-source-at-GO/1"
EXPECTED_V=(0,1,2,111,112,113)
EXPECTED_BYTES=("04","2F","04","40","04","80","04","20","04","53","04","80")
EXPECTED_SRCS=("7E:2085","7E:2086","7E:2088","7E:2089","7E:208B","7E:208C",
               "7E:208E","7E:208F","7E:2091","7E:2092","7E:2094","7E:2095")


def unique_keys(pairs):
    result={}
    for key,val in pairs:
        if key in result:
            raise ValueError("duplicated original source report field")
        result[key]=val
    return result


def check(root: Path, live_json: Path, expected_sha: dict | None = None) -> dict:
    source=live_json.read_bytes()
    report=json.loads(source,object_pairs_hook=unique_keys)
    if (report.get("schema")!=SCHEMA or
        report.get("actual_original_PPU_2131_2132_writes")!=96 or
        report.get("actual_original_channel5_register_pairs")!=48 or
        report.get("source_expected_byte_matches")!=96 or
        report.get("actual_WRAM_PPU_byte_matches")!=96 or
        report.get("real_original_native_identical_frame_input_PPU_parity") is not False or
        report.get("actual_original_Snes9x_finished_PPU_RGB_pixels_sampled") is not False):
        raise ValueError("genuine original source live HDMA report required")
    original_go=read_frame(root,"go")
    original_t480=read_frame(root,"t480")
    path=root/"go.ppuw.tsv"
    raw=path.read_bytes()
    prefix="#frame\tvcounter\thcounter\taddr\tvalue\tsource\n"
    lines=raw.decode("ascii").splitlines()
    if not raw.startswith(prefix.encode()) or len(lines)<=1:
        raise ValueError("invalid full original GO register journal")
    ppuw=[]
    for s in lines[1:]:
        if s.startswith("#"):
            raise ValueError("truncated or unauthenticated original PPUW data")
        cols=s.split("\t")
        if len(cols)!=6:
            raise ValueError("bad PPUW source event")
        frame,v,h,reg,value,origin=cols
        if origin=="hdma" and reg in ("2131","2132"):
            ppuw.append({
                "frame":int(frame), "v":int(v), "h":int(h),
                "register":"$"+reg,"value":"0x"+value})
    observed=[e for e in report.get("source_event_records",[])
              if e.get("original_emulator_frame")==1989]
    if len(observed)!=12 or len(ppuw)!=12:
        raise ValueError("exact original GO twelve 2131/2132 HDMA journal events required")
    output=[]
    for i,(a,b) in enumerate(zip(observed,ppuw)):
        expected_reg="$2131" if i%2==0 else "$2132"
        if (a.get("ordinal")!=i+sum(
                    1 for e in report["source_event_records"]
                    if e["original_emulator_frame"]<1989)
                or a.get("original_emulator_frame")!=1989
                or a.get("original_beam_v")!=b["v"]
                or b["frame"]!=1989
                or a.get("original_live_PPU_register")!=expected_reg
                or b["register"]!=expected_reg
                or a.get("source")!=EXPECTED_SRCS[i]
                or a.get("observed_original_HDMA_PPU_written_byte")!="0x"+EXPECTED_BYTES[i]
                or b["value"]!="0x"+EXPECTED_BYTES[i]
                or a.get("original_Wram_equals_BBus_value") is not True
                or a.get("observed_byte_matches_prior_executed_original_table") is not True):
            raise ValueError("real original GO PPU register journal and live after-write source differ")
        if (b["v"] != EXPECTED_V[i//2] or
            not 0<=b["h"]<=339 or
            i%2 and (b["h"]<=ppuw[i-1]["h"] or b["h"]-ppuw[i-1]["h"]>16)):
            raise ValueError("original horizontal/vertical HDMA byte ordering differs")
        output.append({
            "ordinal":i,"original_frame":1989,
            "original_v":b["v"],"original_h":b["h"],
            "register":expected_reg,"original_source":a["source"],
            "observed_original_BBUS_byte":b["value"],
            "original_live_after_write_fixed_RGB15":
                a["original_live_PPU_fixed_RGB15_after_write"],
        })
    if expected_sha is not None:
        if (hashlib.sha256(source).hexdigest()!=expected_sha.get("live_ppu")
            or hashlib.sha256(raw).hexdigest()!=expected_sha.get("go_ppuw")
            or original_go["original_RGB_raw_B_G_R_X_SHA256"]!=expected_sha.get("go_rgb")
            or original_t480["original_RGB_raw_B_G_R_X_SHA256"]!=expected_sha.get("t480_rgb")):
            raise ValueError("authenticated source emulator output sha changed")
    return {
        "schema":MARK,"status":"same-original-frame-two-observers-exact-register-and-byte-agreement",
        "original_emulator_frame":1989,
        "original_live_source_report_SHA256":hashlib.sha256(source).hexdigest(),
        "original_ppuw_SHA256":hashlib.sha256(raw).hexdigest(),
        "original_GO_frame_RGB_B_G_R_X_SHA256":original_go["original_RGB_raw_B_G_R_X_SHA256"],
        "original_t480_frame_RGB_B_G_R_X_SHA256":original_t480["original_RGB_raw_B_G_R_X_SHA256"],
        "original_GO_PPU_register_records_crosschecked":len(output),
        "actual_original_channel5_HDMA_mode1_pairs_crosschecked":len(output)//2,
        "actual_original_h_b_bus_word_separation_bounded":True,
        "per_original_GO_PPU_write":output,
        "same_original_source_frame_and_registers_confirmed":True,
        "source_core_is_independent_of_Baldosa_native_PPU":True,
        "independent_physical_SNESCycle_acceleration_or_timing_proven":False,
        "original_Snes9x_frame_to_native_guest_frame_aligned":False,
        "original_native_256vs342_crop_and_pixel_RGB_parity_proven":False,
        "new_HD_character_art_authorized":False,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--live-original",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--source-sha",type=Path)
    a=p.parse_args()
    pins=json.loads(a.source_sha.read_text()) if a.source_sha else None
    data=check(a.root,a.live_original,pins)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
    print("QA08_ORIGINAL_GO_LIVE_VS_PPUW_ACCEPTED original_frame=1989 "
          "observed_live_register_pairs=6 real_native_same_input=0")


if __name__=="__main__":
    main()
