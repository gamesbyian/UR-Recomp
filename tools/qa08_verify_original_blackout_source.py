#!/usr/bin/env python3
"""Authenticate original 2P results blackout $2100 source without frame edits.

Run unmodified 2014 Snes9x with three host-only 4015..4017 snapshots and
an existing ring read of original $2100 writes 3998..4035. Reuse previous
strict 263/263 unchanged original BGRX and 5484 input-script comparison.
No source geometry shift, frame phase search or CPU/PPU/guest correction.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
try:
    from tools.qa08_original_results_port_chronology import verify as verify_source
except ImportError:
    from qa08_original_results_port_chronology import verify as verify_source

SCHEMA="qa08-authentic-original-Snes9x-2P-blackout-INIDISP-source-readback/1"
FRAMES=(4015,4016,4017)
START,END=3998,4035
BLACKOUT_CALLBACK=4015


def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()


def parse_inidisp_journal(raw:bytes)->dict:
    lines=raw.decode("ascii").splitlines()
    if lines[:2]!=["#original_frame_range=3998..4035",
                    "frame\tvcounter\thcounter\taddr\tvalue\tsource"]:
        raise ValueError("not the exact bounded original PPU $2100 ring")
    records=[]
    info={}
    for line in lines[2:]:
        if line.startswith("#"):
            key,val=line[1:].split("=",1)
            if key in info:
                raise ValueError("duplicate debug ring metadata")
            info[key]=val
            continue
        parts=line.split("\t")
        if len(parts)!=6:
            raise ValueError("malformed original PPU register trace")
        frame,v,h,reg,value,src=parts
        row={"frame":int(frame),"v":int(v),"h":int(h),
             "reg":reg,"value":value,"source":src}
        if (not START<=row["frame"]<=END or
            not 0<=row["v"]<=261 or not 0<=row["h"]<=340
            or reg!="2100" or len(value)!=2 or
            src not in ("cpu","dma","hdma")):
            raise ValueError("unauthentic original $2100 source writer/beam")
        records.append(row)
    if (set(info)!={"ring_earliest","write_count","scan_complete"}
        or info["scan_complete"]!="1"
        or int(info["ring_earliest"])>START
        or int(info["write_count"])!=len(records)
        or not records):
        raise ValueError("source $2100 ring was truncated or empty")
    byframe=Counter(r["frame"] for r in records)
    return {
        "original_source_frame_window":[START,END],
        "unaltered_original_register": "2100",
        "original_2100_port_write_records":len(records),
        "original_write_frames":sorted(byframe),
        "original_writes_per_frame":{str(k):v for k,v in sorted(byframe.items())},
        "original_2100_actual_CPU_DMA_HDMA_beam_writes":records,
        "original_2100_history_raw_SHA256":sha(raw),
        "source_ring_minimum_covered_original_frame":int(info["ring_earliest"]),
    }


def verify(root:Path, prior:Path, route:Path, rom:Path, core:Path)->dict:
    old=verify_source(root,prior,route,rom,core)
    log=(root/"original.log").read_text(errors="replace")
    register_rows=[]
    for frame in FRAMES:
        tag=f"qa08_blackout_{frame}"
        if re.findall(r"script f=(\d+) dump "+tag+r"\b",log)!=[str(frame)]:
            raise ValueError(f"original source blackout dump {frame} not at real callback")
        p=root/"registers"
        raw=(p/f"{tag}.regs.json").read_bytes()
        content=json.loads(raw)
        meta=json.loads((p/f"{tag}.info.json").read_text())
        ppu=content.get("ppu",{})
        display=ppu.get("inidisp",{})
        fill=content.get("fillram",{}).get("2100")
        if (content.get("frame_tag")!=frame or
            meta.get("frame")!=frame or meta.get("fb_frame")!=frame or
            meta.get("fb_width")!=256 or meta.get("fb_height")!=224 or
            meta.get("core_name")!="Snes9x" or
            display.get("forced_blank") not in (0,1) or
            not 0<=display.get("brightness",-1)<=15 or
            not re.fullmatch(r"[0-9a-fA-F]{2}",fill or "")):
            raise ValueError("original reference result-blackout PPU registers invalid")
        register_rows.append({
            "original_actual_source_dump_frame":frame,
            "original_input_port_INIDISP_2100_byte":fill,
            "original_source_PPU_brightness":display["brightness"],
            "original_source_PPU_forced_blank":display["forced_blank"],
            "original_source_CGADSUB":ppu.get("cgadsub"),
            "original_source_CGWSEL":ppu.get("cgwsel"),
            "original_readonly_register_SHA256":sha(raw),
        })
    history=parse_inidisp_journal(
        (root/"registers"/"qa08-original-blackout-3998-4035-INIDISP.tsv").read_bytes())
    original_black=(root/"frames"/"frame_004015_256x224.raw").read_bytes()
    if len(original_black)!=256*224*4 or any(original_black):
        raise ValueError("real unmasked original source callback 4015 not fully black")
    return {
        "schema":SCHEMA,
        "original_USA_ROM_sha256":old["original_ROM_sha256"],
        "2014_Snes9x_core_sha256":old["original_core_sha256"],
        "original_guest_input_script_sha256":old["unaltered_original_three_dump_script_sha256"],
        "original_263_callbacks_byte_equal_to_untouched_Snes9x":True,
        "actual_original_script_quit_frame":5484,
        "original_blackout_callback_frame":BLACKOUT_CALLBACK,
        "original_blackout_frame_all_57344_RGB_pixels_black":True,
        "source_original_blackout_register_snapshots":register_rows,
        "source_original_2100_write_journal":history,
        "original_native_register_frame_phase_independently_accepted":False,
        "original_native_guest_CPU_instruction_equivalence_accepted":False,
        "native_source_raster_correction_admitted":False,
        "graphics_release_ledger_admitted":False,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    for x in ("script","verify-root","prior-original","rom","core","result"):
        p.add_argument("--"+x,type=Path,required=True)
    a=p.parse_args()
    out=verify(a.verify_root,a.prior_original,a.script,a.rom,a.core)
    a.result.parent.mkdir(parents=True,exist_ok=True)
    a.result.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("QA08_SOURCE_ORIGINAL_BLACKOUT",
          "263_original_frames_unchanged=1",
          f"inidisp_writes={out['source_original_2100_write_journal']['original_2100_port_write_records']}",
          "original_video_callback_4015_black_pixels=57344",
          "native_clock_and_release=unaccepted")


if __name__=="__main__":
    main()
