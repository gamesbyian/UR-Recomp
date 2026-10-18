#!/usr/bin/env python3
"""Execute a real source-pinned Windows 2P route and inspect bounded PPU logs."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from baldosa_windows_native_pause_route import run_route

ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
ROUTE_SHA="ef74ec51fa585aa76652f4a14d2727f0074434b3925522ab2607e3bd29aa0194"
CRC="b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568"
FRAMES=(4032,4048,4064,4080,4176)
COORDS=((207,91),(205,115),(205,139),(225,96),(225,120))
SLOTS=(96,97,98,99,112,113,114)
def sha(b: bytes)->str: return hashlib.sha256(b).hexdigest()
def row(line: str, tag: str)->dict[str,str]:
    if not line.startswith(tag+" "): raise ValueError("unexpected source record")
    data={}
    for token in line[len(tag)+1:].split():
        if token.count("=")!=1:raise ValueError("malformed token")
        k,v=token.split("=",1)
        if k in data:raise ValueError("duplicate source field")
        data[k]=v
    return data
def inspect(log: str, crcs: list[str])->dict:
    if len(crcs)!=5484 or any(re.fullmatch(r"0x[0-9a-fA-F]{8}",x) is None for x in crcs):
        raise ValueError("missing 5484 actual guest frames")
    crc=sha(("\n".join(x.lower() for x in crcs)+"\n").encode("ascii"))
    if crc!=CRC:raise ValueError("RF-017 / route changed; read-only attribution invalid: "+crc)
    pixels={}; oam={}; cgram=[]
    for line in log.splitlines():
        if line.startswith("UR_QA08_WIN_PIXEL_OWNER "):
            v=row(line,"UR_QA08_WIN_PIXEL_OWNER")
            k=(int(v["frame"]),int(v["x"]),int(v["raster_y"]))
            if k in pixels or k[0] not in FRAMES or k[1:] not in COORDS or int(v["ppu_line"])!=k[2]+1:
                raise ValueError("unsolicited/duplicate effective owner pixel")
            if set(("main","sub","obj","obj_cgram_index","obj_word","cgadsub","inidisp","final"))-set(v):
                raise ValueError("incomplete original PPU pixel info")
            pixels[k]=v
        elif line.startswith("UR_QA08_WIN_OAM_LINE "):
            v=row(line,"UR_QA08_WIN_OAM_LINE")
            k=(int(v["frame"]),int(v["x"]),int(v["ppu_line"]),int(v["slot"]))
            if k in oam or k[0] not in FRAMES or k[3] not in SLOTS:
                raise ValueError("duplicate / unexpected effective OAM")
            oam[k]=v
        elif line.startswith("UR_QA08_WIN_CURRENT_CGRAM_WRITE "):
            v=row(line,"UR_QA08_WIN_CURRENT_CGRAM_WRITE")
            if set(("frame","v","h","adr","val","src","ptr","second"))!=set(v):
                raise ValueError("invalid original/native CGRAM writer")
            f=int(v["frame"])
            if f<4024 or f>4184 or v["adr"] not in ("21","22"):
                raise ValueError("out of window colour writer")
            cgram.append(v)
    if set(pixels)!={(f,x,y) for f in FRAMES for x,y in COORDS}:
        raise ValueError("selected true original PPU pixels missing")
    if len(oam)!=len(FRAMES)*len(COORDS)*len(SLOTS):
        raise ValueError("true OAM line records missing")
    if not cgram or len(cgram)>5000:
        raise ValueError("absent or unbounded actual CPU/DMA CGRAM writers")
    return {"schema":"qa08-current-RF017-original-native-PPU-owners-readonly/1",
            "selected_frame_source_epoch":list(FRAMES),
            "real_2p_guest_frames":len(crcs),"real_guest_CRC_SHA256":crc,
            "selected_true_pixel_owners":len(pixels),"real_OAM_records":len(oam),
            "CGRAM_port_writes":len(cgram),
            "pixels":[{"frame":f,"xy":[x,y],
                       "main":pixels[f,x,y]["main"],"sub":pixels[f,x,y]["sub"],
                       "rgb":pixels[f,x,y]["final"],
                       "obj_cgram_index":pixels[f,x,y]["obj_cgram_index"],
                       "obj_word":pixels[f,x,y]["obj_word"],
                       "inidisp":pixels[f,x,y]["inidisp"],
                       "cgadsub":pixels[f,x,y]["cgadsub"]}
                      for f in FRAMES for x,y in COORDS],
            "oam":[{"frame":f,"x":x,"line":y+1,"slot":slot,
                     "xy":oam[f,x,y+1,slot]["xy"],
                     "attrs":oam[f,x,y+1,slot]["attrs"],
                     "high":oam[f,x,y+1,slot]["high"]}
                    for f in FRAMES for x,y in COORDS for slot in SLOTS],
            "cgram_port_input_events":cgram,
            "source_original_same_field_ownership_proven":False,
            "guest_CPU_instruction_phase_or_PPU_fix_proven":False,
            "source_P7_image_parity_not_proven":True,"release_approved":False}
def main()->None:
    a=argparse.ArgumentParser(description=__doc__)
    for k in ("exe","rom","script","out"):a.add_argument("--"+k,type=Path,required=True)
    a.add_argument("--timeout",type=int,default=300)
    v=a.parse_args()
    if sha(v.rom.read_bytes())!=ROM_SHA or sha(v.script.read_bytes())!=ROUTE_SHA:
        a.error("ROM/input identity mismatch")
    v.out.mkdir(parents=True,exist_ok=True)
    keys={"UR_QA08_WINDOWS_PIXEL_OWNER_TRACE":"1",
          "UR_QA08_WINDOWS_CURRENT_CGRAM_TRACE":"1",
          "UR_QA08_WINDOWS_OBJ_FETCH_TRACE":"1"}
    previous={k:os.environ.get(k) for k in keys}
    os.environ.update(keys)
    try:crc,log=run_route(v.exe.resolve(),v.rom.resolve(),v.script.resolve(),
                          v.out,pause=False,video="windows",timeout=v.timeout)
    finally:
        for k,x in previous.items():
            if x is None:os.environ.pop(k,None)
            else:os.environ[k]=x
    report=inspect(log,crc)
    from qa08_join_current_medal_obj_fetch import joined
    report["genuine_native_4bpp_medal_winners"] = joined(log,report)
    report["actual_windows_PE_sha256"]=sha(v.exe.read_bytes())
    report["controller_script_sha256"]=ROUTE_SHA
    (v.out/"qa08-current-result-owners.json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("QA08_CURRENT_PPU_OWNERS",len(report["pixels"]),
          "OAM",len(report["oam"]),"CGRAM",len(report["cgram_port_input_events"]),
          "guest",report["real_guest_CRC_SHA256"],"release=0")
if __name__=="__main__":main()
