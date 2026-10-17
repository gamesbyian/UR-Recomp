#!/usr/bin/env python3
"""Authentic Windows RF017 complete-input finish layer and brightness probe."""
from __future__ import annotations
import argparse
import hashlib,json,os,re
from pathlib import Path
try:
    from tools.baldosa_windows_native_pause_route import run_route
except ImportError:
    from baldosa_windows_native_pause_route import run_route

ROM="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
ROUTE="ef74ec51fa585aa76652f4a14d2727f0074434b3925522ab2607e3bd29aa0194"
GUEST="b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568"
SAMPLES={(1856,96,0):(132,165,165),(1856,97,0):(132,165,165),
         (3680,92,0):(53,69,69),(3680,93,0):(49,65,65),
         (3680,96,0):(38,53,53),(3680,97,0):(34,49,49),
         (3792,121,165):(53,26,3),(3872,121,165):(53,26,3)}
ORIGINAL={(1856,96,0):(16,20,20),(1856,97,0):(16,20,20),
          (3680,92,0):(7,8,8),(3680,93,0):(6,8,8),
          (3680,96,0):(5,7,7),(3680,97,0):(4,6,6),
          (3792,121,165):(6,3,0),(3872,121,165):(6,3,0)}
FIELDS={"frame","x","y","main","sub","math","window","pre_main","pre_sub",
        "post_math","final","inidisp","cgadsub","cgwsel","tm","ts"}
def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def triples(s:str,low:int=-1,high:int=31)->tuple[int,int,int]:
    bits=s.split(",")
    if len(bits)!=3:raise ValueError("corrupt existing native PPU RGB operand")
    vals=tuple(int(x) for x in bits)
    if any(x<low or x>high for x in vals):
        raise ValueError("out-of-range actual original PPU operand")
    return vals
def inspect(log:str,crcs:list[str])->dict:
    if len(crcs)!=5484 or any(re.fullmatch(r"0x[0-9a-fA-F]{8}",x) is None for x in crcs):
        raise ValueError("missing complete native route CRC")
    crc=sha(("\n".join(x.lower() for x in crcs)+"\n").encode())
    if crc!=GUEST:raise ValueError("current exact native RF017 guest source changed")
    lines={}
    for line in log.splitlines():
        if not line.startswith("UR_QA08_FINISH_OPERAND "):continue
        parts=line[len("UR_QA08_FINISH_OPERAND "):].split()
        if any(s.count("=")!=1 for s in parts):
            raise ValueError("malformed original PPU source fields")
        row=dict(s.split("=",1) for s in parts)
        if len(row)!=len(parts) or set(row)!=FIELDS:
            raise ValueError("invalid/duplicate PPU source fields")
        k=tuple(int(row[i]) for i in ("frame","x","y"))
        if k not in SAMPLES or k in lines:
            raise ValueError("extra/duplicate unqualified source pixel")
        rgb=triples(row["final"],0,255)
        if rgb!=SAMPLES[k]:raise ValueError("actual native PPU source pixel drift")
        if tuple(v>>3 for v in rgb)!= (ORIGINAL[k] if k[0] in (1856,3792,3872) else
                                       tuple(v>>3 for v in SAMPLES[k])):
            raise ValueError("control / already-sourced finish RGB5 mismatch")
        if int(row["math"]) not in (0,1) or int(row["window"]) not in (0,1):
            raise ValueError("invalid actual PPU math/window state")
        if not all(0<=int(row[r],16)<=255 for r in ("inidisp","cgadsub","cgwsel","tm","ts")):
            raise ValueError("invalid PPU output register")
        triples(row["pre_main"]);triples(row["pre_sub"]);triples(row["post_math"],0,31)
        lines[k]=row
    if set(lines)!=set(SAMPLES):
        raise ValueError("eight actual finish/control PPU pixel owners absent")
    result=[]
    for k in sorted(lines):
        v=lines[k]
        result.append({"frame":k[0],"xy":[k[1],k[2]],"main":int(v["main"]),
                       "sub":int(v["sub"]),"math_enabled":int(v["math"]),
                       "colour_window":int(v["window"]),
                       "pre_main_RGB5":triples(v["pre_main"]),
                       "pre_sub_RGB5":triples(v["pre_sub"]),
                       "post_math_RGB5":triples(v["post_math"],0,31),
                       "actual_native_final_RGB8":triples(v["final"],0,255),
                       "original_same_source_pixel_RGB5":ORIGINAL[k],
                       "native_inidisp":v["inidisp"],
                       "cgadsub":v["cgadsub"],"cgwsel":v["cgwsel"],
                       "tm":v["tm"],"ts":v["ts"]})
    return {"schema":"qa08-RF017-real-Windows-finish-postmath-operand-samples/1",
            "real_complete_two_pad_guest_frames":len(crcs),
            "current_source_guest_CRC_SHA256":crc,
            "current_source_256x224_archive_registers_expected":True,
            "sample_pixel_count":8,"source_samples":result,
            "native_output_pixels_modified":False,
            "original_2014_same_PPU_operand_source_proven":False,
            "source_guest_CPU_equivalence_proven":False,
            "graphics_QA08_QA10_or_release_accepted":False}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for a in ("exe","rom","script","out"):p.add_argument("--"+a,type=Path,required=True)
    p.add_argument("--timeout",type=int,default=300)
    args=p.parse_args()
    if sha(args.rom.read_bytes())!=ROM or sha(args.script.read_bytes())!=ROUTE:
        p.error("source USA ROM/input route changed")
    args.out.mkdir(parents=True,exist_ok=True)
    k="UR_QA08_RF017_FINISH_OPERAND_TRACE";prior=os.environ.get(k)
    os.environ[k]="1"
    try:
        crcs,log=run_route(args.exe.resolve(),args.rom.resolve(),args.script.resolve(),
                           args.out,pause=False,video="windows",timeout=args.timeout)
    finally:
        if prior is None:os.environ.pop(k,None)
        else:os.environ[k]=prior
    receipt=inspect(log,crcs)
    receipt["actual_win32_PE_sha256"]=sha(args.exe.read_bytes())
    receipt["real_two_pad_script_sha256"]=ROUTE
    (args.out/"qa08-finish-operands.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("QA08_FINISH_REAL_PPU_OPERANDS",len(receipt["source_samples"]),
          "CRC",receipt["current_source_guest_CRC_SHA256"],"release=0")
if __name__=="__main__":main()
