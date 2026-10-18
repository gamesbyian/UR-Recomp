#!/usr/bin/env python3
"""Native RF017 late CGRAM input writer discriminator, source-only and unmasked."""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
try:
    from tools.baldosa_windows_native_pause_route import run_route
except ImportError:
    from baldosa_windows_native_pause_route import run_route

ROM = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SCRIPT = "ef74ec51fa585aa76652f4a14d2727f0074434b3925522ab2607e3bd29aa0194"
GUEST = "b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568"
TAG = "UR_QA08_WIN_LATE_CGRAM_WRITE "
ORIGINAL_SOURCE = (5157, 5164, 5171, 5178)

def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()

def parse(log: str) -> dict:
    rows = defaultdict(list)
    for line in log.splitlines():
        if not line.startswith(TAG):
            continue
        v = {}
        for word in line[len(TAG):].split():
            if word.count("=") != 1:
                raise ValueError("malformed PPU source token")
            a, b = word.split("=", 1)
            if a in v:
                raise ValueError("duplicate PPU source key")
            v[a] = b
        if set(v) != {"frame","v","h","adr","val","src","ptr","second"}:
            raise ValueError("missing real CGRAM port readback")
        f = int(v["frame"])
        r = dict(frame=f, v=int(v["v"]), h=int(v["h"]),
                 port=int(v["adr"],16), value=int(v["val"],16),
                 source=int(v["src"]), pointer=int(v["ptr"],16),
                 second=int(v["second"]))
        if (not 5152 <= f <= 5195 or not 0 <= r["v"] <= 262 or
            not 0 <= r["h"] <= 2000 or r["port"] not in (33,34) or
            not 0 <= r["value"] <= 255 or r["source"] != 0 or
            not 0 <= r["pointer"] <= 255 or r["second"] not in (0,1)):
            raise ValueError("native writer is not a qualified CPU source port event")
        rows[f].append(r)
        if len(rows[f]) > 12:
            raise ValueError("extra PPU writer event in one host field")
    if not 4 <= len(rows) <= 8:
        raise ValueError("late current-epoch CGRAM writer packet population absent")
    frames = sorted(rows)
    if any(b-a != 7 for a,b in zip(frames,frames[1:])):
        raise ValueError("real native writer period is not seven result fields")
    output=[]
    for f in frames:
        events=rows[f]
        if len(events) != 12:
            raise ValueError("incomplete four-color true port writer packet")
        words=[]
        for j in range(4):
            addr,low,high=events[3*j:3*j+3]
            if ([addr["port"],low["port"],high["port"]] != [33,34,34] or
                addr["value"] != 0x6c+j):
                raise ValueError("real source CGRAM data order/address unexpected")
            words.append(f"{(low['value'] | (high['value']<<8)) & 0x7fff:04x}")
        output.append({"native_CPU_input_host_frame":f,
                       "colour_words_6c_to_6f_RGB15":words,
                       "actual_twelve_port_events":events})
    return {"actual_native_writer_frame_sequence":frames,
            "genuine_CPU_input_CGRAM_port_events":sum(map(len,rows.values())),
            "palette_6c_to_6f_by_frame":output,
            "previously_archived_genuine_2014_Snes9x_source_writer_frame_labels":
               list(ORIGINAL_SOURCE),
            "original_CPU_or_NMI_instruction_clock_equivalence_proven":False,
            "source_original_CGRAM_values_rejoined_in_this_instrument":False,
            "guest_or_palette_renderer_fix_authorized":False}

def verify(log: str, crcs: list[str]) -> dict:
    if len(crcs) != 5484 or any(not re.fullmatch(r"0x[0-9a-fA-F]{8}",s) for s in crcs):
        raise ValueError("5484 actual guest source CRC entries missing")
    actual=digest(("\n".join(x.lower() for x in crcs)+"\n").encode("ascii"))
    if actual != GUEST:
        raise ValueError("RF017 native CPU source or route changed: "+actual)
    return {"schema":"QA08-current-RF017-real-Win32-late-CGRAM-input/1",
            "authentic_two_pad_route_SHA256":SCRIPT,"retail_USA_ROM_SHA256":ROM,
            "actual_native_guest_frames":5484,"actual_guest_CRC_sha256":actual,
            "live_CGRAM":parse(log),
            "original_Snes9x_full_256x224_frame_parity_proven":False,
            "CPU_clock_phase_fix_authorized":False,
            "physical_4k_or_HD_art_release_accepted":False}

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("exe","rom","script","out"):
        p.add_argument("--"+k,required=True,type=Path)
    p.add_argument("--timeout",type=int,default=300)
    a=p.parse_args()
    if digest(a.rom.read_bytes())!=ROM or digest(a.script.read_bytes())!=SCRIPT:
        p.error("ROM or actual unchanged authentic 2P controller input mismatch")
    a.out.mkdir(parents=True,exist_ok=True)
    env="UR_QA08_WINDOWS_LATE_CGRAM_TRACE"
    old=os.environ.get(env);os.environ[env]="1"
    try:
        crcs,log=run_route(a.exe.resolve(),a.rom.resolve(),a.script.resolve(),
                           a.out,pause=False,video="windows",timeout=a.timeout)
    finally:
        if old is None:os.environ.pop(env,None)
        else:os.environ[env]=old
    result=verify(log,crcs)
    result["actual_compiled_Windows_PE_sha256"]=digest(a.exe.read_bytes())
    (a.out/"qa08-current-rf017-late-cgram.json").write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("QA08_LATE_CGRAM",result["live_CGRAM"]["actual_native_writer_frame_sequence"],
          "read_only=1 release=0")
if __name__=="__main__":
    main()
