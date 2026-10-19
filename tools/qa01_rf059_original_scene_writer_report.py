#!/usr/bin/env python3
"""RF059 executed original 65816 opcode-boundary WRAM mutation report.

The executed opcode interval is NOT asserted to be a unique memory-bus
writer; NMI/DMA might intervene. The original 2014 movie and fresh original
are different, and native event acceptance is independently owned.
"""
from __future__ import annotations
import argparse, hashlib, json, re, zipfile
from collections import Counter
from pathlib import Path

BEAT="QA01RF059CPUHEART "
CHANGE="QA01RF059OPWRAM "
KV=re.compile(r"([A-Za-z][A-Za-z0-9_]*)=([^\s]+)")
BASE_SHA="c2262b40e43b4e167cbdf291623b0e34207561187e103af39eca7a46fa4b0edc"
ACTUAL_SHA="2248cf04d75208a4b55da83fd18af11b57ddf37148b7ddf4b9446e39f880cd04"
ORIGINAL_INSTRUMENTED_CORE_SHA="aeaa1c2d89f60f25bed39507291eecf1e90efb57bb9f30d87dadf377e5ad1e69"
ORIGINAL_UNMODIFIED_CORE_SHA="0182cfc3446e5a2c1d00453928b857b3d1d9c23148486c7339c895c4facc25c5"
WATCH={0x121f:(0x0,0x1),0x126b:(0x0,0x1),0x1277:(0x0,0x60),0x1359:(0x0,0xff),0x135b:(0x0,0x7f),0x135d:(0x0,0xff),0x135f:(0x0,0x7f),0x2000:(0x1,0x2),0x2002:(0x1,0x4),0x2004:(0x80,0x40),0x2007:(0x4,0xff),0x2008:(0x90,0x7f),0x2009:(0xf,0x2),0x2017:(0x2,0x8),0x2018:(0x3,0x7),0x2019:(0x2,0x1),0x2069:(0xf,0x60)}
FRAMES=list(range(4687,4694))

def inspect(log:str)->dict:
    if "QA01RF059OPWRAM_TRUNCATED" in log or "QA01RF059CPUHEART_TRUNCATED" in log:
        raise ValueError("RF059 genuine original CPU WRAM mutation trace truncated")
    beats=[]
    changes=[]
    for row in log.splitlines():
        if not row.startswith((BEAT,CHANGE)):
            continue
        d=dict(KV.findall(row))
        if row.startswith(BEAT):
            if not all(k in d for k in ("frame","v","h","pc")):
                raise ValueError("RF059 real original CPU heartbeat incomplete")
            f=int(d["frame"]); bank,pc=d["pc"].split(":")
            if f<4686 or f>4694 or int(bank,16)>255 or int(pc,16)>65535:
                raise ValueError("RF059 original 65816 core-frame/bank-PC anomaly")
            beats.append((f,d))
        else:
            cols=("seq","frame","pre_v","pre_h","pc","op","a","x","y",
                  "post_v","post_h","nextpc","addr","old","new")
            if not all(k in d for k in cols):
                raise ValueError("RF059 actual original opcode delta row missing context")
            if int(d["seq"])!=len(changes)+1:
                raise ValueError("RF059 actual original CPU mutation row ordinal gap")
            a=d["addr"].split(":")
            if len(a)!=2 or int(a[0],16)!=0x7E or int(a[1],16) not in WATCH:
                raise ValueError("RF059 observed address not in exactly four first transition bytes")
            bf,af=int(d["old"],16),int(d["new"],16)
            if bf==af or not (0<=bf<=255 and 0<=af<=255):
                raise ValueError("RF059 original raw byte mutation malformed")
            f=int(d["frame"])
            if f<4686 or f>4694 or len(d["pc"].split(":"))!=2:
                raise ValueError("RF059 executed original CPU opcode/frame missing")
            changes.append((int(a[1],16),f,d))
    if [f for f,_ in beats] != list(range(4686,4695)):
        raise ValueError("RF059 actual original CPU dispatch not observed for each handoff frame")
    if not changes:
        # Do not call the transition non-CPU-authored just because this
        # sampled opcode-only watchpoint saw no change.
        raise ValueError("RF059 actual original source CPU opcode boundary mutations not captured")
    byaddr=Counter(f"7E:{x:04X}" for x,f,d in changes)
    target={f"7E:{x:04X}":{
        "expected_between_stored_frames_old":f"{before:02X}",
        "expected_between_stored_frames_new":f"{after:02X}",
        "actual_direct_opcode_delta_with_those_two_values":any(
            n==x and int(d["old"],16)==before and int(d["new"],16)==after
            for n,f,d in changes),
        "actual_opcode_delta_count":byaddr.get(f"7E:{x:04X}",0)
    } for x,(before,after) in WATCH.items()}
    return {
        "schema":"rf059-executed-USA-original-Bowl-scene-construction-opcode-boundary-v1",
        "true_original_CPU_dispatch_frame_heartbeats":len(beats),
        "actual_source_CPU_frames_at_handoff":[f for f,_ in beats],
        "actual_source_65816_opcode_interval_mutation_count":len(changes),
        "actual_source_opcodes_with_raw_WRAM_byte_changes":[
            {k:v for k,v in d.items()} for _,_,d in changes[:800]
        ],
        "actual_memory_change_candidate_address_census":dict(byaddr),
        "actual_CPU_scene_change_first_by_address":{k:next((d for _,_,d in changes if d["addr"]==k),None) for k in byaddr},
        "actual_CPU_scene_change_last_by_address":{k:next((d for _,_,d in reversed(changes) if d["addr"]==k),None) for k in byaddr},
        "real_full_frame_original_WRAM_end_state_transitions":target,
        "source_gameplay_mutation_occurs_within_observed_opcode_interval":True,
        "unique_CPU_memory_bus_write_by_that_opcode_proven":False,
        "source_joypad_4218_register_consumption_proven":False,
        "native_guest_65816_opcode_execution_proven":False,
        "original_native_CPU_clock_registration_proven":False,
        "accepted_complete_USA_events":0,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_source_reference_log",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    value=json.dumps(inspect(a.original_source_reference_log.read_text(encoding="utf8",errors="replace")),indent=2,sort_keys=True)+"\n"
    if a.out:a.out.write_text(value,encoding="utf8")
    else:print(value,end="")
if __name__=="__main__":main()
