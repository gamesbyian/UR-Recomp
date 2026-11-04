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
from tools.art.mesen_rider_wram_probe import (capture as capture_rider_wram,
    validate as validate_rider_wram, start_watches as start_rider_watches,
    recent_writes as rider_recent_writes, validate_recent_writes as validate_rider_writes,
    source_dma_queue as capture_rider_DMA_queue, validate_dma_queue as validate_rider_DMA_queue)

SCHEMA="UR-ART4K-MESENCE-LIVE-RAW-SNES-PPU-STATES/1"
ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
MESEN_REVISION="a60e79feb4d6dcced5922d636f9211837d01e381"
REGIONS={"oam":("snesSpriteRam",544),"vram":("snesVideoRam",65536),
         "cgram":("snesCgRam",512)}
MAX_CHUNK=1024
MAX_DISPLAY_AXIS=1024
MAX_SPARSE_SNAPSHOTS=24
MAX_SPARSE_TICK=2500


def validate_capture_ticks(ticks:tuple[int,...])->tuple[int,...]:
    """Validate an ordered, bounded set of real executed Mesen bridge ticks."""
    if (type(ticks) is not tuple or
            not 1<=len(ticks)<=MAX_SPARSE_SNAPSHOTS or
            any(type(t) is not int or not 1<=t<=MAX_SPARSE_TICK
                for t in ticks) or
            any(b<=a for a,b in zip(ticks,ticks[1:]))):
        raise ValueError("sparse original capture ticks must increase, 1..2500, at most 24")
    return ticks


def parse_capture_ticks(text:str)->tuple[int,...]:
    """Parse CLI decimal-only tick selection; do not infer duplicate ticks."""
    if (not isinstance(text,str) or not text or
            len(text)>6*MAX_SPARSE_SNAPSHOTS or
            any(not part.isascii() or not part.isdecimal()
                for part in text.split(","))):
        raise ValueError("capture ticks must be comma-separated decimal bridge frames")
    return validate_capture_ticks(tuple(int(t,10) for t in text.split(",")))


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


def inspect_held_ppm(raw: bytes, reply: dict, requested_path: str) -> dict:
    """Validate actual Mesen P6 screen-buffer bytes without conversion or crop."""
    if (not isinstance(reply,dict) or reply.get("format")!="P6" or
            reply.get("path")!=requested_path):
        raise ValueError("original emulator video.export_frame identity differs")
    width,height=reply.get("width"),reply.get("height")
    if (type(width) is not int or type(height) is not int or
            not 1<=width<=MAX_DISPLAY_AXIS or
            not 1<=height<=MAX_DISPLAY_AXIS or
            type(reply.get("pixels")) is not int or
            reply["pixels"]!=width*height):
        raise ValueError("original source screen size or pixel count invalid")
    header=f"P6\n{width} {height}\n255\n".encode("ascii")
    if (not isinstance(raw,bytes) or not raw.startswith(header) or
            len(raw)!=len(header)+3*width*height):
        raise ValueError("original emulator P6 RGB file/header/length invalid")
    return {
        "source_format":"P6",
        "source_display_width":width,
        "source_display_height":height,
        "source_framebuffer_RGB_sha256":sha(raw[len(header):]),
        "source_rgb_byte_length":3*width*height,
        "sha256":sha(raw),
        "byte_size":len(raw),
    }


def capture_states(mesen,controller_runs,advance:int,count:int,output:Path,
                   include_held_framebuffer:bool=False,
                   source_snes_frame_skipping_disabled_requested:bool=False,
                   *,source_capture_ticks:tuple[int,...]|None=None,
                   include_rider_wram:bool=False)->dict:
    if (type(source_snes_frame_skipping_disabled_requested) is not bool or
            type(include_held_framebuffer) is not bool or
            type(include_rider_wram) is not bool or
            type(advance) is not int or not 0<=advance<=2500 or
            type(count) is not int or not 1<=count<=5):
        raise ValueError("bounded original emulator capture range required")
    requested=(validate_capture_ticks(source_capture_ticks)
               if source_capture_ticks is not None else
               tuple(range(advance+1,advance+count+1)))
    if output.exists() and any(output.iterdir()):
        raise ValueError("source evidence output must be a fresh empty directory")
    output.mkdir(parents=True,exist_ok=True)
    previous=(None,None)
    frames=[]
    requested_set=set(requested)
    watch_handles=None
    for step in range(requested[-1]):
        if include_rider_wram and step==max(0,requested[0]-2):
            watch_handles=start_rider_watches(mesen)
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
        if expected not in requested_set:
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
        display=None
        if include_held_framebuffer:
            if mesen.tool("run.status").get("frame")!=expected:
                raise ValueError("original emulator advanced before held display read")
            filename=f"frame-{expected:06d}-held-display.ppm"
            target=output/filename
            if target.exists():
                raise ValueError("original held-framebuffer output must not exist")
            requested_path=str(target.resolve())
            response=mesen.tool("video.export_frame",path=requested_path)
            if not target.is_file() or target.is_symlink():
                raise ValueError("original emulator screen buffer file not produced")
            display=inspect_held_ppm(target.read_bytes(),response,requested_path)
            display["relative_file"]=filename
            if mesen.tool("run.status").get("frame")!=expected:
                raise ValueError("original emulator advanced during held display read")
        rider_wram=(capture_rider_wram(mesen,expected) if include_rider_wram else None)
        frame_row={
            "original_emulator_held_display_P6":display,
            "emulator_bridge_frame":expected,
            "replayed_controller_step_index":step,
            "p1_controller_mask":current[0],
            "p2_controller_mask":current[1],
            "raw_original_snes_ppu_memory":raw,
        }
        if include_rider_wram:
            if watch_handles is None:
                raise ValueError("source original writer watches not installed")
            frame_row["source_original_rider_WRAM_at_bridge_boundary"]=rider_wram
            frame_row["source_original_DMA_queue_at_bridge_boundary"]=capture_rider_DMA_queue(mesen,expected)
            frame_row["source_original_rider_writer_events"]=rider_recent_writes(
                mesen,watch_handles,expected)
        frames.append(frame_row)
    if [frame["emulator_bridge_frame"] for frame in frames]!=list(requested):
        raise ValueError("missing requested original emulator source frame")
    record={"schema":SCHEMA,"emulator_source_revision":MESEN_REVISION,
            "original_USA_ROM_sha256":ROM_SHA,
            "authentic_live_emulator_bridge_step_counter_verified":True,
            "actual_raw_SNES_sprite_RAM_VRAM_CGRAM_snapshots":len(frames),
            "original_held_framebuffer_P6_exported":include_held_framebuffer,
            "source_original_snes_frame_skipping_disabled_requested":source_snes_frame_skipping_disabled_requested,
            "original_PPU_RGB_to_source_OBJ_pixel_ownership_verified":False,
            "source_held_display_to_current_PPU_scanout_phase_independently_aligned":False,
            "source_held_display_RGB_reproducibility_across_runs_independently_verified":False,
            "source_regional_memory_bytes_sha_bound":True,
            "source_original_rider_WRAM_at_bridge_boundary_exported":include_rider_wram,
            "source_original_rider_WRAM_callback_events_exported":include_rider_wram,
            "source_original_DMA_queue_entries_exported":include_rider_wram,
            "original_rider_CPU_WRAM_writers_dynamically_identified":False,
            "live_original_per_player_64x64_alpha_composition_verified":False,
            "source_original_live_OAM_sprite_to_racer_identity_verified":False,
            "source_original_SNES_PPU_final_draw_order_verified":False,
            "source_original_3d_camera_or_articulated_rig_verified":False,
            "original_source_to_experimental_GLb_pose_correspondence_verified":False,
            "owner_likeness_approved":False,
            "frames":frames}
    if source_capture_ticks is not None:
        record["source_requested_capture_ticks"]=list(requested)
    return record


def validate_snapshot_files(directory:Path,manifest:dict)->None:
    if (not isinstance(manifest,dict) or manifest.get("schema")!=SCHEMA or
            manifest.get("original_USA_ROM_sha256")!=ROM_SHA or
            manifest.get("emulator_source_revision")!=MESEN_REVISION or
            manifest.get("source_original_live_OAM_sprite_to_racer_identity_verified") is not False or
            type(manifest.get("source_original_snes_frame_skipping_disabled_requested",False)) is not bool or
            manifest.get("original_PPU_RGB_to_source_OBJ_pixel_ownership_verified",False) is not False or
            manifest.get("source_held_display_to_current_PPU_scanout_phase_independently_aligned",False) is not False or
            manifest.get("source_held_display_RGB_reproducibility_across_runs_independently_verified",False) is not False):
        raise ValueError("invalid provenance or overclaimed original PPU capture")
    frames=manifest.get("frames")
    if (not isinstance(frames,list) or not frames or
            manifest.get("actual_raw_SNES_sprite_RAM_VRAM_CGRAM_snapshots")!=len(frames)):
        raise ValueError("raw original SNES PPU frame count incorrect")
    sparse=None
    if "source_requested_capture_ticks" in manifest:
        requested=manifest["source_requested_capture_ticks"]
        if type(requested) is not list:
            raise ValueError("sparse original capture tick manifest malformed")
        try:
            sparse=validate_capture_ticks(tuple(requested))
        except ValueError as exc:
            raise ValueError("sparse original capture tick manifest malformed") from exc
        if [row.get("emulator_bridge_frame") for row in frames]!=list(sparse):
            raise ValueError("sparse original capture tick manifest disagrees with frames")
    elif len(frames)>5:
        raise ValueError("legacy source capture cannot exceed five frames")
    seen=set()
    last=None
    for frame in frames:
        n=frame.get("emulator_bridge_frame")
        step=frame.get("replayed_controller_step_index")
        if (type(n) is not int or type(step) is not int or n!=step+1 or
                (sparse is None and last is not None and n!=last+1) or
                set(frame.get("raw_original_snes_ppu_memory",{}))!=set(REGIONS)):
            raise ValueError("source bridge frame sequence or PPU region invalid")
        last=n
        include_rider=manifest.get("source_original_rider_WRAM_at_bridge_boundary_exported",False)
        rider=frame.get("source_original_rider_WRAM_at_bridge_boundary")
        if include_rider is True:
            validate_rider_wram(rider,n)
            if manifest.get("source_original_rider_WRAM_callback_events_exported") is not True:
                raise ValueError("original callback event evidence missing")
            validate_rider_writes(frame.get("source_original_rider_writer_events"),n)
            if manifest.get("source_original_DMA_queue_entries_exported") is not True:
                raise ValueError("source original DMA queue evidence missing")
            validate_rider_DMA_queue(frame.get("source_original_DMA_queue_at_bridge_boundary"),n)
        elif (rider is not None or include_rider is not False or
              "source_original_rider_writer_events" in frame or
              "source_original_DMA_queue_at_bridge_boundary" in frame or
              manifest.get("source_original_DMA_queue_entries_exported",False) is not False or
              manifest.get("source_original_rider_WRAM_callback_events_exported",False) is not False):
            raise ValueError("unclaimed original rider WRAM or malformed capture flag")
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
        display=frame.get("original_emulator_held_display_P6")
        if manifest.get("original_held_framebuffer_P6_exported") is True:
            if not isinstance(display,dict):
                raise ValueError("original held framebuffer missing")
            name=f"frame-{n:06d}-held-display.ppm"
            if display.get("relative_file")!=name or name in seen:
                raise ValueError("original held framebuffer path/identity invalid")
            seen.add(name)
            path=directory/name
            if path.is_symlink() or not path.is_file():
                raise ValueError("original emulator P6 framebuffer absent or linked")
            width,height=display.get("source_display_width"),display.get("source_display_height")
            if type(width) is not int or type(height) is not int:
                raise ValueError("original source held P6 dimensions malformed")
            response={
                "format":display.get("source_format"),
                "path":str(path.resolve()),
                "width":width,
                "height":height,
                "pixels":width*height,
            }
            actual=inspect_held_ppm(path.read_bytes(),response,str(path.resolve()))
            for key,value in actual.items():
                if display.get(key)!=value:
                    raise ValueError("original source held P6 framebuffer SHA/metadata changed")
        elif display is not None:
            raise ValueError("unclaimed original held screen pixels in source receipt")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom",required=True,type=Path)
    p.add_argument("--input-file",required=True,type=Path)
    p.add_argument("--mesen-for-ai-repo",type=Path,required=True)
    p.add_argument("--mesen-executable",type=Path,required=True)
    p.add_argument("--advance-frames",type=int)
    p.add_argument("--capture-frames",type=int)
    p.add_argument("--capture-ticks",type=str,help="1..24 increasing decimal ticks, one replay")
    p.add_argument("--include-held-framebuffer",action="store_true")
    p.add_argument("--include-rider-wram",action="store_true",
                   help="11 bounded 16-bit original rider/DMA WRAM values per selected tick")
    p.add_argument("--out-dir",required=True,type=Path)
    args=p.parse_args()
    if args.capture_ticks is not None and (args.advance_frames is not None or args.capture_frames is not None):
        p.error("--capture-ticks cannot be combined with contiguous capture options")
    try:
        sparse_ticks=parse_capture_ticks(args.capture_ticks) if args.capture_ticks is not None else None
    except ValueError as exc:
        p.error(str(exc))
    advance=1218 if args.advance_frames is None else args.advance_frames
    count=2 if args.capture_frames is None else args.capture_frames
    if sha(args.rom.read_bytes())!=ROM_SHA:
        p.error("original USA ROM SHA256 mismatch")
    if not args.mesen_executable.is_file():
        p.error("real emulator executable not present")
    import os
    os.environ["MESEN_BIN"]=str(args.mesen_executable.resolve())
    disable_request=os.environ.get("MESEN_SNES_DISABLE_FRAME_SKIPPING","0") == "1"
    Mesen=load_mesen_class(args.mesen_for_ai_repo.resolve())
    runs=load_controller_runs(args.input_file)
    with Mesen(repo=str(args.mesen_for_ai_repo.resolve())) as mesen:
        mesen.load_rom(str(args.rom.resolve()),timeout=180)
        report=capture_states(mesen,runs,advance,count,args.out_dir,
                              include_held_framebuffer=args.include_held_framebuffer,
                              source_snes_frame_skipping_disabled_requested=disable_request,
                              source_capture_ticks=sparse_ticks,
                              include_rider_wram=args.include_rider_wram)
    report["original_input_replay_sha256"]=sha(args.input_file.read_bytes())
    report["actual_emulator_executable_sha256"]=sha(args.mesen_executable.read_bytes())
    validate_snapshot_files(args.out_dir,report)
    publish_text_once(args.out_dir/"manifest.json",json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"schema":SCHEMA,"emulator_ticks":[x["emulator_bridge_frame"] for x in report["frames"]],
                      "captured_regions":list(REGIONS),
                      "original_source_rider_WRAM_sampled":args.include_rider_wram,
                      "live_source_racer_alpha_reconstructed":False,
                      "original_held_emulator_screen_exported":args.include_held_framebuffer,
                      "source_no_frameskip_explicitly_requested":disable_request},sort_keys=True))


if __name__=="__main__":
    main()
