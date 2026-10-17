#!/usr/bin/env python3
"""One actual source-CRC-authenticated Windows blackout $2100 diagnostic route."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
try:
    from tools.baldosa_windows_native_pause_route import run_route
except ImportError:
    from baldosa_windows_native_pause_route import run_route

ROM="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
ROUTE="ef74ec51fa585aa76652f4a14d2727f0074434b3925522ab2607e3bd29aa0194"
GUEST="b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568"
FRAMES=(4015,4016,4017,4022)
LINES=(1,112,114)
POINTS=((32,32),(128,112),(220,200))
def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def fields(line:str, tag:str,keys:set[str])->dict[str,str]:
    if not line.startswith(tag+" "):raise ValueError("unrecognized source tag")
    out={}
    for bit in line[len(tag)+1:].split():
        if bit.count("=")!=1:raise ValueError("malformed original PPU source field")
        k,v=bit.split("=",1)
        if not k or k in out:raise ValueError("duplicate source field")
        out[k]=v
    if set(out)!=keys:raise ValueError("missing/extra original PPU fields")
    return out

def inspect(log:str,crcs:list[str])->dict:
    if len(crcs)!=5484 or any(re.fullmatch(r"0x[0-9a-fA-F]{8}",c) is None for c in crcs):
        raise ValueError("real native 5484 guest route incomplete")
    ident=sha(("\n".join(c.lower() for c in crcs)+"\n").encode("ascii"))
    if ident!=GUEST:raise ValueError("native guest/source epoch mismatch "+ident)
    writes=[]; lines={}; pixels={}
    for raw in log.splitlines():
        if raw.startswith("UR_QA08_CURRENT_BLACKOUT_PORT "):
            x=fields(raw,"UR_QA08_CURRENT_BLACKOUT_PORT",
                {"frame","v","h","val","old","src"})
            f=int(x["frame"]); v=int(x["v"]);h=int(x["h"]);s=int(x["src"])
            if not 4008<=f<=4024 or not 0<=v<=262 or not 0<=h<=2000 or not 0<=s<=3:
                raise ValueError("out-of-window $2100 write/author")
            for q in ("val","old"):
                if re.fullmatch(r"[0-9a-f]{2}",x[q]) is None:
                    raise ValueError("bad native $2100 value")
            writes.append({"frame":f,"v":v,"h":h,"val":x["val"],
                           "before":x["old"],"source":s})
        elif raw.startswith("UR_QA08_CURRENT_BLACKOUT_LINE "):
            x=fields(raw,"UR_QA08_CURRENT_BLACKOUT_LINE",
                    {"frame","line","inidisp","brightness","forced_blank","cgadsub"})
            f,l=int(x["frame"]),int(x["line"]); k=(f,l)
            if (f not in FRAMES or l not in LINES or k in lines or
                int(x["brightness"])!=int(x["inidisp"],16)&15 or
                int(x["forced_blank"])!=(int(x["inidisp"],16)>>7) or
                re.fullmatch(r"[0-9a-f]{2}",x["cgadsub"]) is None):
                raise ValueError("bogus original raster brightness/line witness")
            lines[k]=x
        elif raw.startswith("UR_QA08_CURRENT_BLACKOUT_PIXEL "):
            x=fields(raw,"UR_QA08_CURRENT_BLACKOUT_PIXEL",
                     {"frame","x","y","inidisp","r","g","b"})
            f,px,py=int(x["frame"]),int(x["x"]),int(x["y"]); k=(f,px,py)
            if f!=4016 or (px,py) not in POINTS or k in pixels or any(
                    not 0<=int(x[c])<=255 for c in ("r","g","b")):
                raise ValueError("missing source registered original PPU pixel")
            pixels[k]=x
    if len(writes)<7 or len(writes)>200:
        raise ValueError("actual original PPU CPU/host port chronology absent/unbounded")
    if set(lines)!={(f,y) for f in FRAMES for y in LINES}:
        raise ValueError("real original raster $2100 state lines missing")
    if set(pixels)!={(4016,x,y) for x,y in POINTS}:
        raise ValueError("real native guest4016 pixel probe missing")
    sources=Counter(x["source"] for x in writes)
    if sources.get(0,0)<7 or sources.get(3,0)<7:
        raise ValueError("native CPU+host replay distinction not established")
    return {
        "schema":"qa08-live-RF017-original-PPU-blackout-source-writer-raster/1",
        "actual_windows_guest_simulations":5484,
        "actual_source_guest_CRC_SHA256":ident,
        "original_2014_snes9x_callback_4015_black_count":57344,
        "archived_original_source_INIDISP_fields":{"4015":"80","4016":"80","4017":"02"},
        "archived_original_source_CPU_2100_writes":{"frames":list(range(4017,4024)),
            "values":["02","04","06","08","0a","0c","0e"],
            "original_beam":{"v":230,"last_v":231}},
        "current_RF017_native_CPU_and_raster_replay_write_counts":
          {str(k):v for k,v in sorted(sources.items())},
        "native_actual_source_2100_ports":writes,
        "current_native_ppu_raster_line_registers":[
             {"frame":f,"line":line,"inidisp":lines[f,line]["inidisp"],
              "brightness":int(lines[f,line]["brightness"]),
              "forced_blank":int(lines[f,line]["forced_blank"])}
             for f in FRAMES for line in LINES],
        "actual_native_4016_pixel_RGB":[
            {"xy":[x,y],
             "rgb":[int(pixels[4016,x,y][c]) for c in ("r","g","b")],
             "inidisp":pixels[4016,x,y]["inidisp"]}
            for x,y in POINTS],
        "original_native_CPU_phase_equivalence_proven":False,
        "raster_or_global_brightness_correction_admitted":False,
        "graphics_release_accepted":False,
    }
def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    for s in ("exe","rom","script","out"):p.add_argument("--"+s,required=True,type=Path)
    p.add_argument("--timeout",type=int,default=300)
    a=p.parse_args()
    if sha(a.rom.read_bytes())!=ROM or sha(a.script.read_bytes())!=ROUTE:
        p.error("actual original USA ROM and complete 2P route fingerprints changed")
    a.out.mkdir(parents=True,exist_ok=True)
    before=os.environ.get("UR_QA08_CURRENT_BLACKOUT_TRACE")
    os.environ["UR_QA08_CURRENT_BLACKOUT_TRACE"]="1"
    try: crcs,log=run_route(a.exe.resolve(),a.rom.resolve(),a.script.resolve(),
                      a.out,pause=False,video="windows",timeout=a.timeout)
    finally:
        if before is None:os.environ.pop("UR_QA08_CURRENT_BLACKOUT_TRACE",None)
        else:os.environ["UR_QA08_CURRENT_BLACKOUT_TRACE"]=before
    value=inspect(log,crcs)
    value["actual_windows_PE_sha256"]=sha(a.exe.read_bytes())
    value["real_two_pad_route_sha256"]=ROUTE
    (a.out/"qa08-current-blackout-INIDISP.json").write_text(
        json.dumps(value,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("QA08_RF017_BLACKOUT_SOURCE",value["actual_source_guest_CRC_SHA256"],
          "INIDISP",value["current_RF017_native_CPU_and_raster_replay_write_counts"],
          "raster",len(value["current_native_ppu_raster_line_registers"]),"release=0")
if __name__=="__main__":main()
