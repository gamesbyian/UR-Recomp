#!/usr/bin/env python3
"""Collect source SNES PPU serializer register diagnostics on real Mesen ticks.

A source register snapshot does not establish screen scanout phase, original
OBJ pixel identity or an original 1994 3D unicycle pose.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

from tools.art.capture_original_mesen_ppu_raw import capture_states, sha, ROM_SHA, MESEN_REVISION
from tools.capture_racer_composition_mesen import load_mesen_class
from tools.controller_input import load_controller_runs
from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-AUTHENTIC-MESEN-PPU-REGISTER-CENSUS/1"
# Pinned original upstream SNES SnesPpu::Serialize fields, with source
# variable separators/qualifiers resolved via exact suffix check.
FIELD_NAMES=("OamMode","OamBaseAddress","OamAddressOffset","OamRamAddress",
    "EnableOamPriority","ScreenBrightness","ForcedBlank","BgMode",
    "MainScreenLayers","SubScreenLayers","HiResMode","ScreenInterlace",
    "ObjInterlace","OverscanMode","FixedColor","ColorMathEnabled",
    "scanline","frameCount")


def select_source_state(raw:dict)->dict:
    if not isinstance(raw,dict) or not 0<len(raw)<300000:
        raise ValueError("original Mesen serialized console map malformed")
    selected={}
    for field in FIELD_NAMES:
        matches=[(key,value) for key,value in raw.items()
                 if isinstance(key,str) and len(key)<=200 and
                 key.startswith("ppu.") and
                 key.replace("_","").lower().endswith("."+field.lower())]
        if len(matches)>1:
            raise ValueError("ambiguous source Mesen PPU register "+field)
        if len(matches)==1:
            key,value=matches[0]
            if type(value) not in (int,bool) or (type(value) is int and abs(value)>(1<<48)):
                raise ValueError("non-physical Mesen serialized PPU register "+field)
            selected[field]={"source_serialized_name":key,"original_value":value}
    required=("OamMode","OamBaseAddress","OamAddressOffset","scanline","frameCount")
    if any(key not in selected for key in required):
        raise ValueError("missing mandatory original PPU register identity")
    return selected


class RegisterSpy:
    def __init__(self,original,advance):
        self.original=original
        self.advance=advance
        self.holds=[]
    def tool(self,name,**kwargs):
        reply=self.original.tool(name,**kwargs)
        if name=="run.step_frames":
            frame=reply.get("status",{}).get("frame")
            if type(frame) is int and frame>self.advance:
                serial=self.original.tool("console.state")
                selected=select_source_state(serial)
                if self.original.tool("run.status").get("frame")!=frame:
                    raise ValueError("source Mesen advanced during serialized PPU read")
                self.holds.append({"original_bridge_tick":frame,
                                   "source_total_serialized_fields":len(serial),
                                   "exact_source_PPU_register_fields":selected})
        return reply


def capture_registers(mesen,runs,advance,count,out):
    spy=RegisterSpy(mesen,advance)
    evidence=capture_states(spy,runs,advance,count,out,
                            source_snes_frame_skipping_disabled_requested=True)
    if [x["original_bridge_tick"] for x in spy.holds]!=[x["emulator_bridge_frame"] for x in evidence["frames"]]:
        raise ValueError("source serialized PPU register frame mismatch")
    return {"schema":SCHEMA,"original_mesen_revision":MESEN_REVISION,
            "original_USA_ROM_sha256":ROM_SHA,
            "source_frame_skipping_disabled_requested":True,
            "actual_original_emulator_frame_states":spy.holds,
            "source_PPU_serialized_register_names_probed":True,
            "source_PPU_screen_phase_correspondence_verified":False,
            "original_racer_sprite_pixel_ownership_verified":False,
            "original_3D_unicycle_rig_camera_verified":False,
            "owner_likeness_approved":False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ("rom","input-file","mesen-for-ai-repo","mesen-executable","out-dir"):
        p.add_argument("--"+arg,required=True,type=Path)
    p.add_argument("--advance-frames",type=int,default=1218)
    p.add_argument("--capture-frames",type=int,default=2)
    args=p.parse_args()
    if sha(args.rom.read_bytes())!=ROM_SHA or not args.mesen_executable.is_file():
        p.error("source ROM/binary not verified")
    if os.environ.get("MESEN_SNES_DISABLE_FRAME_SKIPPING")!="1":
        p.error("SNES source register census requires no-skip setting")
    os.environ["MESEN_BIN"]=str(args.mesen_executable.resolve())
    cls=load_mesen_class(args.mesen_for_ai_repo.resolve())
    with cls(repo=str(args.mesen_for_ai_repo.resolve())) as mesen:
        mesen.load_rom(str(args.rom.resolve()),timeout=180)
        record=capture_registers(mesen,load_controller_runs(args.input_file),
                                 args.advance_frames,args.capture_frames,args.out_dir)
    record["original_input_replay_sha256"]=sha(args.input_file.read_bytes())
    record["emulator_executable_sha256"]=sha(args.mesen_executable.read_bytes())
    publish_text_once(args.out_dir/"selected-original-ppu-registers.json",
                      json.dumps(record,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"schema":SCHEMA,"held_ticks":[x["original_bridge_tick"] for x in record["actual_original_emulator_frame_states"]],
                      "selected_original_fields":[list(x["exact_source_PPU_register_fields"]) for x in record["actual_original_emulator_frame_states"]],
                      "original_visible_pixel_ownership_verified":False},sort_keys=True))


if __name__=="__main__":
    main()
