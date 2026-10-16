#!/usr/bin/env python3
"""Bounded actual two-pad Windows PPU source across full race and results.

An opt-in observer on the SAME compiled Windows Uniracers executable,
unchanged original 2P route and USA ROM. 263 source-size PPU callbacks.
No second emulator, synthetic pixels, guest timing, Modern, SRAM or UI edit.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re

from qa08_windows_full_oneplayer_source_coverage import (
    run_route, sha, SOURCE_HEADER, LOG, ROM_SHA,
)

FIRST,LAST,STEP=1280,5472,16
SCHEMA="qa08-real-windows-2p-split-fullroute-source-20261015/1"


STATE_LOG=re.compile(
    r"^UR_QA08_WIN_PPU_STATE frame=(\d+) line=(\d+) inidisp=([0-9a-f]{2}) "
    r"brightness=(\d+) forced_blank=(\d+) cgadsub=([0-9a-f]{2}) "
    r"cgwsel=([0-9a-f]{2}) fixedcolor=([0-9a-f]{4}) "
    r"cg6c=([0-9a-f]{4}) cg6d=([0-9a-f]{4}) "
    r"cg6e=([0-9a-f]{4}) cg6f=([0-9a-f]{4}) "
    r"cgram_fnv=([0-9a-f]{8})$",re.M
)


def inspect_native_ppu_registers(log:str)->dict:
    items=[]
    for vals in STATE_LOG.findall(log):
        frame,line,display,brightness,blank,math,window,fixed,slot6c,slot6d,slot6e,slot6f,palette=vals
        data={
            "actual_native_snes_frame":int(frame),
            "ppu_line":int(line),
            "inidisp":display,
            "brightness":int(brightness),
            "forced_blank":int(blank),
            "cgadsub":math,
            "cgwsel":window,
            "fixed_color":fixed,
            "real_native_CGRAM_slots_6c_to_6f":{
                "6c":slot6c,"6d":slot6d,"6e":slot6e,"6f":slot6f,
            },
            "cgram_full_512_byte_FNV1a":palette,
        }
        if (data["ppu_line"] not in (1,112,114)
            or not 0<=data["brightness"]<=15
            or data["forced_blank"] not in (0,1)):
            raise ValueError("real native INIDISP/PPU state line malformed")
        items.append(data)
    if not items:
        raise ValueError("actual Windows game never emitted opt-in PPU register state")
    if len({(r["actual_native_snes_frame"],r["ppu_line"]) for r in items})!=len(items):
        raise ValueError("duplicate native PPU register scene/line")
    if not any(3620<=r["actual_native_snes_frame"]<=3683 for r in items):
        raise ValueError("native finish brightness state was not observed")
    if not any(4000<=r["actual_native_snes_frame"]<=4080 for r in items):
        raise ValueError("native result CGRAM state was not observed")
    return {
        "schema":"qa08-opt-in-original-ppu-inidisp-cgram-readonly/1",
        "actual_state_line_count":len(items),
        "per_line_native_PPU_state":items,
        "source_only_no_original_register_equivalence_inferred":True,
        "release_gate_accepted":False,
    }



CGRAM_PORT_LOG=re.compile(
    r"^UR_QA08_WIN_CGRAM_WRITE frame=(\d+) v=(\d+) h=(\d+) "
    r"adr=(21|22) val=([0-9a-f]{2}) src=(\d+) ptr=([0-9a-f]{2}) second=([01])$",
    re.M,
)

def inspect_native_cgram_port_history(log:str)->dict:
    """Read-only original-mode native PPU data-port writes, not raster pixels."""
    rows=[]
    lines=[x for x in log.splitlines() if x.startswith("UR_QA08_WIN_CGRAM_WRITE")]
    if len(lines)!=len(CGRAM_PORT_LOG.findall(log)):
        raise ValueError("malformed or incomplete opt-in native $2121/$2122 port witness")
    for record in CGRAM_PORT_LOG.findall(log):
        frame,v,h,adr,value,src,ptr,second=record
        row={
            "real_native_snes_frame":int(frame),
            "host_beam_vcounter":int(v),
            "host_beam_hcounter":int(h),
            "native_PPU_data_port":adr,
            "original_unmodified_register_value":value,
            "host_writer_source_tag":int(src),
            "pointer_before_write":ptr,
            "second_byte_before_write":int(second),
        }
        if (not 5168<=row["real_native_snes_frame"]<=5190 or
            not 0<=row["host_beam_vcounter"]<=262 or
            not 0<=row["host_beam_hcounter"]<=2000 or
            not 0<=row["host_writer_source_tag"]<=255):
            raise ValueError("native CGRAM data-port observer frame/beam invalid")
        rows.append(row)
    if len(rows)<24 or len(set(x["real_native_snes_frame"] for x in rows))<2:
        raise ValueError("not enough real native 2P palette update transactions")
    return {
        "schema":"qa08-native-uniracers-original-result-CGRAM-PPU-write-observer/1",
        "actual_bounded_port_writes":len(rows),
        "write_frames":sorted(set(x["real_native_snes_frame"] for x in rows)),
        "actual_CPU_DMA_or_PPU_source_enum_not_renamed":True,
        "same_compiled_windows_guest_source":True,
        "unmodified_native_PPU_write_timing_and_data":True,
        "read_only_native_port_writes":rows,
        "original_guest_writer_phase_independently_proven":False,
        "raster_fix_approved":False,
        "release_gate_accepted":False,
    }


HDMA7_PRE=re.compile(
    r"^UR_QA08_WIN_HDMA7 frame=(\d+) phase=pre enable=(\d+) "
    r"terminated=(\d+) transfer=(\d+) aBank=([0-9a-f]{2}) "
    r"aAdr=([0-9a-f]{4}) tableAdr=([0-9a-f]{4}) rep=([0-9a-f]{2}) "
    r"bAdr=([0-9a-f]{2}) bytes=([0-9a-f]{16}) inidisp=([0-9a-f]{2})$",re.M)
HDMA7_POST=re.compile(
    r"^UR_QA08_WIN_HDMA7 frame=(\d+) phase=post enable=(\d+) "
    r"terminated=(\d+) transfer=(\d+) tableAdr=([0-9a-f]{4}) "
    r"rep=([0-9a-f]{2}) inidisp=([0-9a-f]{2})$",re.M)


def inspect_native_channel7_firstline(log:str)->dict:
    before=[]
    for t in HDMA7_PRE.findall(log):
        frame,en,term,transfer,bank,addr,table,rep,bus,mem,display=t
        before.append({"frame":int(frame),"enabled":int(en),"terminated":int(term),
            "transfer":int(transfer),"source_bank":bank,"descriptor_start":addr,
            "table_pointer":table,"repetition":rep,"BBus":bus,
            "live_WRAM_2064_to_206B":mem,"INIDISP_before":display})
    after=[]
    for t in HDMA7_POST.findall(log):
        frame,en,term,transfer,table,rep,display=t
        after.append({"frame":int(frame),"enabled":int(en),"terminated":int(term),
            "transfer":int(transfer),"table_pointer":table,
            "repetition":rep,"INIDISP_after":display})
    if not before or not any(x["frame"]==3683 for x in before):
        raise ValueError("no authentic channel-seven finish witness")
    if len(before)!=len(set(x["frame"] for x in before)):
        raise ValueError("duplicate channel-seven firstline records")
    if len(after)!=len(set(x["frame"] for x in after)):
        raise ValueError("duplicate channel-seven transfer records")
    if any(x["BBus"]!="00" for x in before):
        raise ValueError("channel-seven is not original INIDISP")
    if any(not 3620<=x["frame"]<=3690 for x in before+after):
        raise ValueError("firstline source probe outside bounded window")
    return {"schema":"qa08-source-exact-native-HDMA7-firstline/1",
            "live_channel7_before":before,"live_channel7_after":after,
            "read_only":True,"release_gate_accepted":False}


def inspect(source:Path,log:str,crcs:list[str])->dict:
    if not (LAST < len(crcs) <= 9504) or any(
        not re.fullmatch(r"0x[0-9a-fA-F]{8}",v) for v in crcs):
        raise ValueError("real original USA native two-pad route never reached finish")
    callbacks=[int(s) for s in LOG.findall(log)]
    expected=set(range(FIRST,LAST+1,STEP))
    if len(callbacks)!=263 or len(set(callbacks))!=263 or set(callbacks)!=expected:
        raise ValueError("missing, duplicated or fabricated two-pad source callback")
    if "UR_QA08_WINDOWS_SOURCE_REJECT" in log:
        raise ValueError("source PPU observer rejected a real two-player callback")
    files={x.name:x for x in source.iterdir() if x.is_file()}
    filenames={f"ur-baldosa-original-source-{f:06d}.pam" for f in expected}
    if set(files)!=filenames:
        raise ValueError("2P source artifacts differ from actual callback schedule")
    frames={}
    for frame in sorted(expected):
        raw=files[f"ur-baldosa-original-source-{frame:06d}.pam"].read_bytes()
        if not raw.startswith(SOURCE_HEADER) or len(raw)!=len(SOURCE_HEADER)+256*224*4:
            raise ValueError("2P source image cropped/corrupt or non-original-sized")
        frames[str(frame)]=sha(raw)
    return {
        "schema":SCHEMA,
        "source_geometry":[256,224],
        "original_USA_ROM_sha256":ROM_SHA,
        "actual_native_simulations":len(crcs),
        "actual_native_guest_CRC_sha256":sha(
            ("\n".join(v.lower() for v in crcs)+"\n").encode("ascii")),
        "source_frames_expected_and_observed":[FIRST,LAST,STEP],
        "actual_source_count":263,
        "true_split_screen_moving_frames":[v for v in sorted(expected) if 2016<=v<5136],
        "true_terminal_result_and_return_frames":[v for v in sorted(expected) if v>=5136],
        "source_frame_P7_SHA256_by_guest":frames,
        "no_216_high_crop_or_time_alignment":True,
        "original_snes9x_PPU_frame_RGB5_parity_unadjudicated":True,
        "2P_guest_OAM_camera_input_phase_parity_unadjudicated":True,
        "physical_device_widescreen_remastered_released":False,
        "release_quality_ledger_admitted":False,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    for x in ("exe","rom","script","out"):
        p.add_argument("--"+x,required=True,type=Path)
    p.add_argument("--timeout",type=int,default=300)
    a=p.parse_args()
    if sha(a.rom.read_bytes())!=ROM_SHA:
        p.error("incorrect USA retail source ROM")
    if a.out.exists():
        p.error("refusing to overwrite source raster run")
    a.out.mkdir(parents=True)
    folder=a.out/"source"
    folder.mkdir()
    env={
        "UR_QA08_WINDOWS_ORIGINAL_SOURCE_DIR":str(folder.resolve()),
        "UR_QA08_WINDOWS_ORIGINAL_SOURCE_CASE":"twoplayer-fullroute",
        "UR_QA08_WINDOWS_PPU_STATE_TRACE":"1",
        "UR_QA08_WINDOWS_CGRAM_PORT_TRACE":"1",
        "UR_QA08_WINDOWS_HDMA_FIRSTLINE_TRACE":"1",
    }
    previous={k:os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        crcs,log=run_route(a.exe.resolve(),a.rom.resolve(),a.script.resolve(),
                           a.out,pause=False,video="windows",timeout=a.timeout)
    finally:
        for k,v in previous.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
    report=inspect(folder,log,crcs)
    report["read_only_native_PPU_registers"]=inspect_native_ppu_registers(log)
    report["read_only_native_CGRAM_port_writer_chronology"]=inspect_native_cgram_port_history(log)
    report["read_only_native_HDMA7_firstline"]=inspect_native_channel7_firstline(log)
    report["actual_windows_PE_sha256"]=sha(a.exe.read_bytes())
    report["actual_two_pad_route_sha256"]=sha(a.script.read_bytes())
    (a.out/"qa08-windows-2p-fullroute.json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("QA08_WINDOWS_2P_SOURCE",
          "actual_guest="+str(len(crcs)),
          "actual_source_256x224=263",
          "independent_original_comparison=PENDING release=0")


if __name__=="__main__":
    main()
