#!/usr/bin/env python3
"""RF058 executed original 65816 opcode-boundary WRAM mutation report.

The executed opcode interval is NOT asserted to be a unique memory-bus
writer; NMI/DMA might intervene. The original 2014 movie and fresh original
are different, and native event acceptance is independently owned.
"""
from __future__ import annotations
import argparse, hashlib, json, re, zipfile
from collections import Counter
from pathlib import Path

BEAT="QA01RF058CPUHEART "
CHANGE="QA01RF058OPWRAM "
KV=re.compile(r"([A-Za-z][A-Za-z0-9_]*)=([^\s]+)")
BASE_SHA="c2262b40e43b4e167cbdf291623b0e34207561187e103af39eca7a46fa4b0edc"
ACTUAL_SHA="2248cf04d75208a4b55da83fd18af11b57ddf37148b7ddf4b9446e39f880cd04"
ORIGINAL_INSTRUMENTED_CORE_SHA="aeaa1c2d89f60f25bed39507291eecf1e90efb57bb9f30d87dadf377e5ad1e69"
ORIGINAL_UNMODIFIED_CORE_SHA="0182cfc3446e5a2c1d00453928b857b3d1d9c23148486c7339c895c4facc25c5"
WATCH={0x0:(0x20,0x02),0x57:(0xe2,0x00),0x6f:(0x0f,0x00),0x83:(0x86,0x94)}
FRAMES=list(range(4687,4694))

def inspect(log:str)->dict:
    if "QA01RF058OPWRAM_TRUNCATED" in log or "QA01RF058CPUHEART_TRUNCATED" in log:
        raise ValueError("RF058 genuine original CPU WRAM mutation trace truncated")
    beats=[]
    changes=[]
    for row in log.splitlines():
        if not row.startswith((BEAT,CHANGE)):
            continue
        d=dict(KV.findall(row))
        if row.startswith(BEAT):
            if not all(k in d for k in ("frame","v","h","pc")):
                raise ValueError("RF058 real original CPU heartbeat incomplete")
            f=int(d["frame"]); bank,pc=d["pc"].split(":")
            if f<4686 or f>4694 or int(bank,16)>255 or int(pc,16)>65535:
                raise ValueError("RF058 original 65816 core-frame/bank-PC anomaly")
            beats.append((f,d))
        else:
            cols=("seq","frame","pre_v","pre_h","pc","op","a","x","y",
                  "post_v","post_h","nextpc","addr","old","new")
            if not all(k in d for k in cols):
                raise ValueError("RF058 actual original opcode delta row missing context")
            if int(d["seq"])!=len(changes)+1:
                raise ValueError("RF058 actual original CPU mutation row ordinal gap")
            a=d["addr"].split(":")
            if len(a)!=2 or int(a[0],16)!=0x7E or int(a[1],16) not in WATCH:
                raise ValueError("RF058 observed address not in exactly four first transition bytes")
            bf,af=int(d["old"],16),int(d["new"],16)
            if bf==af or not (0<=bf<=255 and 0<=af<=255):
                raise ValueError("RF058 original raw byte mutation malformed")
            f=int(d["frame"])
            if f<4686 or f>4694 or len(d["pc"].split(":"))!=2:
                raise ValueError("RF058 executed original CPU opcode/frame missing")
            changes.append((int(a[1],16),f,d))
    if [f for f,_ in beats] != list(range(4686,4695)):
        raise ValueError("RF058 actual original CPU dispatch not observed for each handoff frame")
    if not changes:
        # Do not call the transition non-CPU-authored just because this
        # sampled opcode-only watchpoint saw no change.
        raise ValueError("RF058 actual original source CPU opcode boundary mutations not captured")
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
        "schema":"rf058-genuine-USA-bowl-first-original-CPU-opcode-boundary-WRAM-change-v1",
        "true_original_CPU_dispatch_frame_heartbeats":len(beats),
        "actual_source_CPU_frames_at_handoff":[f for f,_ in beats],
        "actual_source_65816_opcode_interval_mutation_count":len(changes),
        "actual_source_opcodes_with_raw_WRAM_byte_changes":[
            {k:v for k,v in d.items()} for _,_,d in changes[:800]
        ],
        "actual_memory_change_candidate_address_census":dict(byaddr),
        "real_full_frame_original_WRAM_end_state_transitions":target,
        "source_gameplay_mutation_occurs_within_observed_opcode_interval":True,
        "unique_CPU_memory_bus_write_by_that_opcode_proven":False,
        "source_joypad_4218_register_consumption_proven":False,
        "native_guest_65816_opcode_execution_proven":False,
        "original_native_CPU_clock_registration_proven":False,
        "accepted_complete_USA_events":0,
    }

def images(z:zipfile.ZipFile)->dict[str,bytes]:
    return {p:z.read(p) for p in z.namelist() if p.startswith(("bowl/replay/ref/",
           "bowl/replay/native/","bowl/source/")) and p.endswith((".wram.bin",".sram.bin"))}

def case(actual:Path,reference:Path)->dict:
    if hashlib.sha256(reference.read_bytes()).hexdigest()!=BASE_SHA:
        raise ValueError("RF058 independently pinned original 2014 USA Bowl reference ZIP changed")
    if hashlib.sha256(actual.read_bytes()).hexdigest()!=ACTUAL_SHA:
        raise ValueError("RF058 actual genuine executed-original case ZIP SHA256 changed")
    with zipfile.ZipFile(actual) as z,zipfile.ZipFile(reference) as r:
        if "bowl/replay/reference.log" not in z.namelist():
            raise ValueError("RF058 actual source opcode trace missing")
        t=inspect(z.read("bowl/replay/reference.log").decode("utf8","replace"))
        a=json.loads(z.read("bowl-report.json"));b=json.loads(r.read("bowl-report.json"))
        # Instrumenting the actual original Snes9x source must change its
        # binary digest. A newer diagnostics producer also appends precisely
        # one false Dragster metadata flag. Everything ELSE, not just a
        # handpicked list of source keys, must remain bit-for-bit identical.
        if (a.get("reference_core_sha256")!=ORIGINAL_INSTRUMENTED_CORE_SHA or
            b.get("reference_core_sha256")!=ORIGINAL_UNMODIFIED_CORE_SHA):
            raise ValueError("RF058 actual original source core was not exactly the pinned patch")
        diagnostic_key="bounded_dragster_to_zoo_diagnostic_without_full_event_parity"
        a_cmp=a.get("comparison");b_cmp=b.get("comparison")
        if (not isinstance(a_cmp,dict) or not isinstance(b_cmp,dict) or
            diagnostic_key in b_cmp or
            a_cmp.get(diagnostic_key) is not False or
            {k:v for k,v in a_cmp.items() if k!=diagnostic_key}!=b_cmp):
            raise ValueError("RF058 original/native Bowl comparison drift or unexpected metadata")
        allowed={"reference_core_sha256","comparison"}
        if set(a)!=set(b) or any(a[k]!=b[k] for k in a if k not in allowed):
            raise ValueError("RF058 genuine source ROM/input/SRAM/guest producer fields drifted")
        fresh,ref=images(z),images(r)
        if set(fresh)!=set(ref) or len(ref)!=64:
            raise ValueError("RF058 missing one of 64 exact original/native/movie memory images")
        for path,raw in ref.items():
            if len(raw)!=(131072 if path.endswith(".wram.bin") else 8192):
                raise ValueError("RF058 truncated genuine full guest image")
            if raw!=fresh[path]:
                raise ValueError("RF058 actual original/native/movie guest images changed: "+path)
    t["actual_replayed_case_zip_sha256"]=ACTUAL_SHA
    t["instrumented_original_core_sha256"]=ORIGINAL_INSTRUMENTED_CORE_SHA
    t["unmodified_original_core_sha256"]=ORIGINAL_UNMODIFIED_CORE_SHA
    t["only_report_metadata_delta"]="bounded_dragster_to_zoo_diagnostic_without_full_event_parity=false"
    t["source_ROM_movie_seed_SRAM_script_and_full_handoff_unchanged"]=True
    t["all_64_original_native_historical_movie_full_memory_images_byte_exact"]=True
    t["unmasked_mem_bytes_excluded"]=0
    return t

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("actual_case",type=Path)
    p.add_argument("--baseline",required=True,type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    out=json.dumps(case(a.actual_case,a.baseline),sort_keys=True,indent=2)+"\n"
    if a.out:a.out.write_text(out,encoding="utf8")
    else:print(out,end="")
if __name__=="__main__":main()
