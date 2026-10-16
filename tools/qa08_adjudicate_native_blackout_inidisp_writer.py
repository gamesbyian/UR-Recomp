#!/usr/bin/env python3
"""Source-authentic original/native blackout $2100 CPU and raster replay.

Verify exact 2014 original Snes9x $2100 writer records vs ACTUAL Windows
native guest and source=3 host replay writes. Require 263 unchanged real
Windows Original P7 images, unchanged 5484 guest CRC, raw V230/V231/V225
beam evidence, and no CPU/guest/frame shift or brightness renderer edit.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ORIGINAL_ZIP="8d7b3a65b8b40bb24ac39fb0b5c87c93d44cba3b6e189126f00604b5fa6818d6"
BASELINE_ZIP="4b55a33917a5941e87d507ceb8af01391c01fc4574a2543fab3f0b3cf35402f0"
NATIVE_ZIP="6da48bb07a52878c1ed77ddb077b037837379e7d3ebbd78aa4ee67211907373a"
REAL_NATIVE_EXE="577e397a7ab98759c08ecf9e2baf07e961300835f7aae84f88107933d1df9db8"
GUEST_CRC="c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876"
VALUES=("02","04","06","08","0a","0c","0e")
ORIGINAL_FRAMES=tuple(range(4017,4024))
CPU_FRAMES=tuple(range(4015,4022))
REPLAY_FRAMES=tuple(range(4016,4023))
ORIGINAL_V=(230,230,230,230,230,230,231)
SCHEMA="qa08-real-original-native-2P-INIDISP-CPU-versus-raster-replay-chronology/1"

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def opened(path:Path,identity:str)->zipfile.ZipFile:
    if sha(path.read_bytes())!=identity:
        raise ValueError("not exact signed original/native source archive")
    return zipfile.ZipFile(path)


def adjudicate(original:zipfile.ZipFile,before:zipfile.ZipFile,
               current:zipfile.ZipFile)->dict:
    source=json.loads(original.read("qa08-original-blackout-INIDISP-source.json"))
    old=json.loads(before.read("qa08-windows-2p-fullroute.json"))
    win=json.loads(current.read("qa08-windows-2p-fullroute.json"))
    if (source.get("original_263_callbacks_byte_equal_to_untouched_Snes9x") is not True
        or source.get("original_blackout_frame_all_57344_RGB_pixels_black") is not True
        or source.get("actual_original_script_quit_frame")!=5484
        or win.get("actual_source_count")!=263 or old.get("actual_source_count")!=263
        or win.get("source_geometry")!=[256,224] or old.get("source_geometry")!=[256,224]
        or win.get("actual_native_simulations")!=5484
        or win.get("actual_native_guest_CRC_sha256")!=old.get("actual_native_guest_CRC_sha256")
        or win.get("actual_native_guest_CRC_sha256")!=GUEST_CRC
        or win.get("actual_windows_PE_sha256")!=REAL_NATIVE_EXE
        or win.get("release_quality_ledger_admitted") is not False):
        raise ValueError("authentic previous/native 2P guest/video evidence changed")
    snapshots=source["source_original_blackout_register_snapshots"]
    if ([x["original_actual_source_dump_frame"] for x in snapshots]!=[4015,4016,4017]
        or [x["original_input_port_INIDISP_2100_byte"] for x in snapshots]!=["80","80","02"]):
        raise ValueError("real original Snes9x $2100 forced blank chronology differs")
    original_writes=source["source_original_2100_write_journal"][
        "original_2100_actual_CPU_DMA_HDMA_beam_writes"]
    if ([(r["frame"],r["value"].lower(),r["v"],r["source"]) for r in original_writes]
        !=list(zip(ORIGINAL_FRAMES,VALUES,ORIGINAL_V,("cpu",)*7))):
        raise ValueError("authentic original source CPU V230/V231 INIDISP writes drifted")
    observed=win.get("read_only_native_INIDISP_2100_write_chronology",{})
    rows=observed.get("native_2100_actual_port_write_history",[])
    if (observed.get("actual_bounded_native_2100_writes")!=14
        or len(rows)!=14 or observed.get("actual_native_CPU_source_enum_zero_writes")!=7
        or observed.get("CPU_DMA_HDMA_raster_replay_tags_remain_distinct") is not True):
        raise ValueError("real native CPU/host $2100 provenance incomplete")
    cpu=[r for r in rows if r["native_writer_source_enum"]==0]
    replay=[r for r in rows if r["native_writer_source_enum"]==3]
    if len(cpu)!=7 or len(replay)!=7 or len(rows)!=len(cpu)+len(replay):
        raise ValueError("native guest CPU vs host raster replay writers conflated")
    pairs=[]
    for i,(c,r,o) in enumerate(zip(cpu,replay,original_writes)):
        val=VALUES[i]
        oldval="80" if i==0 else VALUES[i-1]
        if (c["real_native_guest_frame"]!=CPU_FRAMES[i]
            or r["real_native_guest_frame"]!=REPLAY_FRAMES[i]
            or c["native_2100_value"].lower()!=val
            or r["native_2100_value"].lower()!=val
            or c["native_PPU_INIDISP_before_write"].lower()!=oldval
            or r["native_PPU_INIDISP_before_write"].lower()!=oldval
            or c["native_beam_vcounter"]!=ORIGINAL_V[i]
            or r["native_beam_vcounter"]!=225
            or r["native_beam_hcounter"]!=0
            or o["frame"]-c["real_native_guest_frame"]!=2):
            raise ValueError(f"native guest CPU/PPU source phase differs at {val}")
        pairs.append({
            "original_source_CPU_write_frame":o["frame"],
            "original_source_CPU_vcounter":o["v"],
            "native_actual_CPU_write_frame":c["real_native_guest_frame"],
            "native_actual_CPU_vcounter":c["native_beam_vcounter"],
            "native_host_raster_replay_frame":r["real_native_guest_frame"],
            "native_host_replay_vcounter":r["native_beam_vcounter"],
            "unchanged_original_and_native_register_value":val,
            "both_native_writes_pre_register_value":oldval,
        })
    original_hash=old["source_frame_P7_SHA256_by_guest"]
    new_hash=win["source_frame_P7_SHA256_by_guest"]
    if len(original_hash)!=263 or original_hash!=new_hash:
        raise ValueError("opt-in native $2100 logger changed real Windows raster hashes")
    for frame in range(1280,5473,16):
        filename=f"source/ur-baldosa-original-source-{frame:06d}.pam"
        if (sha(before.read(filename))!=original_hash.get(str(frame)) or
            sha(current.read(filename))!=new_hash.get(str(frame))):
            raise ValueError(f"full original-size P7 frame unexpectedly changed {frame}")
    previous=win["read_only_native_PPU_registers"]["per_line_native_PPU_state"]
    by_frame={}
    for frame,visible in [(4015,"80"),(4016,"02"),(4017,"04"),(4022,"0e")]:
        current_lines=[r for r in previous if r["actual_native_snes_frame"]==frame]
        if (len(current_lines)!=3 or
            {v["ppu_line"] for v in current_lines}!={1,112,114} or
            {v["inidisp"] for v in current_lines}!={visible}):
            raise ValueError("native PPU 2P source 2100 field does not match writers")
        by_frame[str(frame)]=visible
    return {
        "schema":SCHEMA,
        "disposition":"real_native_CPU_original_port_values_and_V_phase_match_source_two_guest_frame_labels_early_with_host_replay_next_field",
        "original_blackout_source_artifact_id":12017762924,
        "original_blackout_source_ZIP_sha256":ORIGINAL_ZIP,
        "preobserver_native_windows_artifact_id":12017392389,
        "preobserver_native_windows_ZIP_sha256":BASELINE_ZIP,
        "compiled_live_native_windows_run_id":38834290175,
        "compiled_live_native_windows_artifact_id":12019455335,
        "compiled_live_native_windows_ZIP_sha256":NATIVE_ZIP,
        "compiled_live_native_windows_PE_SHA256":REAL_NATIVE_EXE,
        "unaltered_original_source_263_callbacks_verified":True,
        "new_native_source_P7_full_256x224_images_unchanged":263,
        "unaltered_5484_native_guest_CRC_SHA256":GUEST_CRC,
        "authentic_original_2100_CPU_writes":7,
        "actual_native_CPU_2100_writes":7,
        "actual_native_host_raster_replay_2100_writes":7,
        "native_CPU_source_enum":0,
        "native_host_raster_replay_source_enum":3,
        "directly_observed_original_CPU_write_frame_minus_native_guest_write_frame":2,
        "native_raster_replay_frame_minus_native_CPU_write_frame":1,
        "native_raster_replay_vertical_phase":225,
        "source_original_CPU_write_vertical_phases":list(ORIGINAL_V),
        "original_native_2100_write_values_equal":True,
        "actual_CPU_replay_and_original_paired_frame_writes":pairs,
        "native_visible_INIDISP_by_frame":by_frame,
        "native_emulated_CPU_instruction_count_phase_or_frame_label_root_proven":False,
        "physical_7to6_widescreen_4x_or_release_approved":False,
        "guest_CPU_APU_clock_timing_or_PPU_raster_edit_approved":False,
        "graphics_QA08_10_and_HD_art_likeness_approved":False,
        "next_source_adjudicator":"CPU/APU and original-gameplay verifiers reconcile source CPU opcode/WRAM/NMI and original native frame/field registration before a graphics-only scanout adjustment",
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-blackout",required=True,type=Path)
    p.add_argument("--old-native",required=True,type=Path)
    p.add_argument("--actual-native",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    with opened(a.original_blackout,ORIGINAL_ZIP) as o, \
         opened(a.old_native,BASELINE_ZIP) as b, \
         opened(a.actual_native,NATIVE_ZIP) as n:
        verdict=adjudicate(o,b,n)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(verdict,indent=2,sort_keys=True)+"\n")
    print("QA08_NATIVE_2100_CPU_AND_RASTER_REPLAY",
          "original=7 native_CPU=7 replay=7 unchanged_P7=263",
          "CPU_frame_label_delta=2 host_field_delay=1 clock_cause_unaccepted=1")


if __name__=="__main__":
    main()
