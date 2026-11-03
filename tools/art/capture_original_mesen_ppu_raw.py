#!/usr/bin/env python3
"""Capture genuine consecutive MesenCE SNES OAM/VRAM/CGRAM *raw* state.

Original ROM runs under pinned source-built MesenCE, with controller replay.
No binary player alpha, authentic source-to-rig pose registration, captured
1994 camera, or complete final PPU pixel ownership is inferred from raw RAM.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from tools.art.no_replace_report import publish_text_once
from tools.capture_racer_composition_mesen import load_mesen_class, buttons_for_mask
from tools.controller_input import load_controller_runs, masks_at

SCHEMA="UR-ART4K-MESENCE-LIVE-RAW-SNES-PPU-STATES/1"
ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
MESEN_REVISION="a60e79feb4d6dcced5922d636f9211837d01e381"
REGIONS={"oam":("snesSpriteRam",544),"vram":("snesVideoRam",65536),
         "cgram":("snesCgRam",512)}
MAX_CHUNK=1024


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def valid_bytes(reply,region:str,at:int,n:int)->bytes:
    if not isinstance(reply,dict) or reply.get("address")!=at or reply.get("length")!=n or reply.get("memoryType")!=region:
        raise ValueError("emulator PPU byte span metadata mismatch")
    data=reply.get("bytes")
    if not isinstance(data,list) or len(data)!=n or any(type(b) is not int or not 0<=b<=255 for b in data):
        raise ValueError("non-physical SNES PPU bytes returned")
    return bytes(data)


def read_region(mesen,memtype:str,total:int)->bytes:
    if type(total) is not int or total<=0 or total>65536:
        raise ValueError("unsupported bounded PPU region size")
    parts=[]
    for pos in range(0,total,MAX_CHUNK):
        n=min(MAX_CHUNK,total-pos)
        parts.append(valid_bytes(
            mesen.tool("cpu.read_memory",memoryType=memtype,address=pos,length=n),
            memtype,pos,n))
    data=b"".join(parts)
    if len(data)!=total:
        raise ValueError("incomplete emulator PPU memory dump")
    return data


def capture_states(mesen,controller_runs,advance:int,count:int,output:Path)->dict:
    if (type(advance) is not int or not 0<=advance<=2500 or
            type(count) is not int or not 1<=count<=5):
        raise ValueError("bounded original emulator capture range required")
    if output.exists() and any(output.iterdir()):
        raise ValueError("source evidence output must be a fresh empty directory")
    output.mkdir(parents=True,exist_ok=True)
    previous=(None,None)
    frames=[]
    for step in range(advance+count):
        current=masks_at(controller_runs,step)
        for port,mask in enumerate(current):
            if mask!=previous[port]:
                mesen.tool("input.set",port=port,subport=0,buttons=buttons_for_mask(mask))
        previous=current
        response=mesen.tool("run.step_frames",frames=1,reset=(step==0))
        status=mesen.tool("run.status")
        expected=step+1
        if (not isinstance(status,dict) or type(status.get("frame")) is not int or
                status["frame"]!=expected or
                not isinstance(response,dict) or
                response.get("status",{}).get("frame")!=expected):
            raise ValueError("actual emulator bridge frame tick is not consecutive")
        if step<advance:
            continue
        raw={}
        # Enforce one held frame for every region; a live unrequested emulator
        # step between OAM/VRAM/CGRAM invalidates this source identity.
        for name,(memtype,size) in REGIONS.items():
            if mesen.tool("run.status").get("frame")!=expected:
                raise ValueError("emulator advanced during PPU snapshot")
            data=read_region(mesen,memtype,size)
            filename=f"frame-{expected:06d}-{name}.bin"
            target=output/filename
            with target.open("xb") as stream:
                stream.write(data)
            raw[name]={"relative_file":filename,"sha256":sha(data),
                       "byte_size":len(data),"mesen_memory_type":memtype}
        if mesen.tool("run.status").get("frame")!=expected:
            raise ValueError("emulator advanced between PPU source regions")
        frames.append({
            "emulator_bridge_frame":expected,
            "replayed_controller_step_index":step,
            "p1_controller_mask":current[0],
            "p2_controller_mask":current[1],
            "raw_original_snes_ppu_memory":raw,
        })
    if len(frames)!=count or any(frames[i]["emulator_bridge_frame"]!=frames[i-1]["emulator_bridge_frame"]+1 for i in range(1,len(frames))):
        raise ValueError("missing original emulator state frame")
    return {"schema":SCHEMA,"emulator_source_revision":MESEN_REVISION,
            "original_USA_ROM_sha256":ROM_SHA,
            "authentic_live_emulator_bridge_step_counter_verified":True,
            "actual_raw_SNES_sprite_RAM_VRAM_CGRAM_snapshots":len(frames),
            "source_regional_memory_bytes_sha_bound":True,
            "live_original_per_player_64x64_alpha_composition_verified":False,
            "source_original_live_OAM_sprite_to_racer_identity_verified":False,
            "source_original_SNES_PPU_final_draw_order_verified":False,
            "source_original_3d_camera_or_articulated_rig_verified":False,
            "original_source_to_experimental_GLb_pose_correspondence_verified":False,
            "owner_likeness_approved":False,
            "frames":frames}


def validate_snapshot_files(directory:Path,manifest:dict)->None:
    if (not isinstance(manifest,dict) or manifest.get("schema")!=SCHEMA or
            manifest.get("original_USA_ROM_sha256")!=ROM_SHA or
            manifest.get("emulator_source_revision")!=MESEN_REVISION or
            manifest.get("source_original_live_OAM_sprite_to_racer_identity_verified") is not False):
        raise ValueError("invalid provenance or overclaimed original PPU capture")
    frames=manifest.get("frames")
    if (not isinstance(frames,list) or not frames or
            manifest.get("actual_raw_SNES_sprite_RAM_VRAM_CGRAM_snapshots")!=len(frames)):
        raise ValueError("raw original SNES PPU frame count incorrect")
    seen=set()
    last=None
    for frame in frames:
        n=frame.get("emulator_bridge_frame")
        step=frame.get("replayed_controller_step_index")
        if (type(n) is not int or type(step) is not int or n!=step+1 or
                (last is not None and n!=last+1) or
                set(frame.get("raw_original_snes_ppu_memory",{}))!=set(REGIONS)):
            raise ValueError("source bridge frame sequence or PPU region invalid")
        last=n
        for region,(_,size) in REGIONS.items():
            record=frame["raw_original_snes_ppu_memory"][region]
            name=record.get("relative_file")
            expected=f"frame-{n:06d}-{region}.bin"
            if name!=expected or name in seen:
                raise ValueError("ambiguous raw original source memory path")
            seen.add(name)
            file=directory/name
            if file.is_symlink() or not file.is_file():
                raise ValueError("missing or linked source memory evidence")
            raw=file.read_bytes()
            if (len(raw)!=size or record.get("byte_size")!=size or
                    record.get("mesen_memory_type")!=REGIONS[region][0] or
                    sha(raw)!=record.get("sha256")):
                raise ValueError("actual emulator original PPU region SHA mismatch")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom",required=True,type=Path)
    p.add_argument("--input-file",required=True,type=Path)
    p.add_argument("--mesen-for-ai-repo",type=Path,required=True)
    p.add_argument("--mesen-executable",type=Path,required=True)
    p.add_argument("--advance-frames",type=int,default=1218)
    p.add_argument("--capture-frames",type=int,default=2)
    p.add_argument("--out-dir",required=True,type=Path)
    args=p.parse_args()
    if sha(args.rom.read_bytes())!=ROM_SHA:
        p.error("original USA ROM SHA256 mismatch")
    if not args.mesen_executable.is_file():
        p.error("real emulator executable not present")
    import os
    os.environ["MESEN_BIN"]=str(args.mesen_executable.resolve())
    Mesen=load_mesen_class(args.mesen_for_ai_repo.resolve())
    runs=load_controller_runs(args.input_file)
    with Mesen(repo=str(args.mesen_for_ai_repo.resolve())) as mesen:
        mesen.load_rom(str(args.rom.resolve()),timeout=180)
        report=capture_states(mesen,runs,args.advance_frames,args.capture_frames,args.out_dir)
    report["original_input_replay_sha256"]=sha(args.input_file.read_bytes())
    report["actual_emulator_executable_sha256"]=sha(args.mesen_executable.read_bytes())
    validate_snapshot_files(args.out_dir,report)
    publish_text_once(args.out_dir/"manifest.json",json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"schema":SCHEMA,"emulator_ticks":[x["emulator_bridge_frame"] for x in report["frames"]],
                      "captured_regions":list(REGIONS),
                      "live_source_racer_alpha_reconstructed":False},sort_keys=True))


if __name__=="__main__":
    main()
