#!/usr/bin/env python3
"""RF044 genuine original/native stack bus and NMI first-cause classifier.

Only actual instrumented original Get/Set bus calls and existing native WRAM
writer journal may attribute a writer. Never infer writer from snapshots or
PC/candidate stack changes. A recorder gap is explicitly unresolved.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import zipfile
import qa01_rf043_zoo_first_stack_window as rf043

REF="work/zoom-zoo/replay/reference.log"
NATIVE="work/zoom-zoo/replay/native.log"
TARGETS=tuple(range(0x01ed,0x01f2))
NATIVE_WLOG=re.compile(r"^f\s*(\d+)\s+([0-9a-fA-F]{2}):([0-9a-fA-F]{4})=([0-9a-fA-F]{2,4})\s+w([12])\s+(\S+)(?:\s+.*)?$")
TRUNC=("QA01RF044ORIGBUS_TRUNCATED","QA01RF044NATIVEREAD_TRUNCATED")
def fields(line:str)->dict:
    return dict(part.split("=",1) for part in line.split()[1:] if "=" in part)
def actual_accesses(text:str, side:str):
    rows=[]
    for i,line in enumerate(text.splitlines()):
        if side=="original" and line.startswith("QA01RF044ORIGBUS "):
            x=fields(line)
            if not all(k in x for k in ("f","kind","addr","w","value","S","pc")):
                raise ValueError("RF044 incomplete original real bus row")
            f=int(x["f"]); addr=int(x["addr"],16);width=int(x["w"])
            if not 1017<=f<=1025 or addr>0x01f1 or addr+width-1<0x01ed:
                raise ValueError("RF044 original row outside exact observed frame/address")
            rows.append({"index":i,"frame":f,"address":addr,"width":width,
                         "value":x["value"],"kind":x["kind"],
                         "sp":x["S"],"pc":x["pc"],"side":side})
        if side=="native" and line.startswith("QA01RF044NATIVEREAD "):
            x=fields(line)
            if not all(k in x for k in ("f","addr","kind","value","S","IPC","scope")):
                raise ValueError("RF044 incomplete native genuine read")
            f=int(x["f"]);addr=int(x["addr"],16);width=int(x["kind"][1:])
            if not 1017<=f<=1025 or addr>0x01f1 or addr+width-1<0x01ed:
                raise ValueError("RF044 native read outside exact target")
            rows.append({"index":i,"frame":f,"address":addr,"width":width,
                         "value":x["value"],"kind":x["kind"],"sp":x["S"],
                         "pc":x["IPC"],"scope":x["scope"],"side":side})
        if side=="native":
            m=NATIVE_WLOG.match(line)
            if m and "rf044_S=" in line:
                frame=int(m[1]);addr=int(m[3],16);width=int(m[5])
                if not 1017<=frame<=1025 or addr>0x01f1 or addr+width-1<0x01ed:
                    raise ValueError("RF044 native writer framegate failure")
                sm=re.search(r"rf044_S=([0-9a-fA-F]+)\s+IPC=([0-9a-fA-F]+)",line)
                if not sm:raise ValueError("RF044 native WRAM writer missing S/IPC")
                rows.append({"index":i,"frame":frame,"address":addr,"width":width,
                             "value":m[4],"kind":"w"+m[5],"sp":sm[1],"pc":sm[2],
                             "scope":m[6],"side":side})
    return rows

def resolve(source:str,native:str)->dict:
    for sentinel in TRUNC:
        if sentinel in source or sentinel in native:
            raise ValueError("RF044 recorder overflow "+sentinel)
    a=actual_accesses(source,"original");b=actual_accesses(native,"native")
    orig_nmi=[{"index":i,**fields(line)} for i,line in enumerate(source.splitlines())
              if line.startswith("QA01RF044ORIGNMI ")]
    for row in orig_nmi:
        if not (1017<=int(row["f"])<=1025) or "old" not in row or "new" not in row:
            raise ValueError("RF044 invalid NMI provenance row")
    # Lack of an observed event is not proof that a stack byte is unused.
    # Distinguish before/after first snapshot, and later overwrites.
    def ancestry(rows):
        result={}
        for target in TARGETS:
            covering=[x for x in rows if x["address"]<=target<x["address"]+x["width"]]
            early=[x for x in covering if x["frame"] in (1017,1018) and x["kind"].startswith("w")]
            read=[x for x in covering if x["frame"] in (1017,1018) and x["kind"].startswith("r")]
            result[f"{target:04X}"]={
                "actual_early_write_events":len(early),
                "actual_early_read_attempts":len(read),
                "last_observed_early_write":early[-1] if early else None,
                "first_observed_early_read":read[0] if read else None,
                "no_masking_or_assumed_writer":True}
        return result
    have={"original":ancestry(a),"native":ancestry(b)}
    sufficient=all(v["actual_early_write_events"]>0
                   for side in have.values() for key,v in side.items()
                   if key in ("01ED","01EE","01EF","01F0"))
    return {
        "schema":"rf044-first-zoo-stack-real-bus-attribution-v1",
        "original_bus_events_count":len(a),
        "native_read_and_writer_events_count":len(b),
        "original_nmi_events_count":len(orig_nmi),
        "original_nmi_events":orig_nmi[:64],
        "actual_first_host1017_1018_bus_writers_and_readers":have,
        "all_four_stack_bytes_both_guest_early_writers_observed":sufficient,
        "complete_last_writer_and_next_reader_NMI_causality_proven":False,
        "physical_byte_comparison_masked":False,
        "complete_usa_events_accepted":0
    }
def report(path:Path)->dict:
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as z:
        original=z.read(REF).decode("utf8","replace")
        native=z.read(NATIVE).decode("utf8","replace")
        producer=json.loads(z.read("producer-report.json"))
        case=json.loads(z.read("case-result.json"))
    mesh=producer["zoo_race_mesh"]
    if not (mesh["mesh_checkpoint_count"]==78 and
            mesh["masked_or_excluded_wram_bytes"]==0 and
            case["release_credit"]==0):
        raise ValueError("RF044 altered strict full-WRAM controls")
    result=resolve(original,native)
    result["source_head"]=case["source_sha"]
    result["case_zip_sha256"]=digest
    result["same_first_divergence_as_rf043"]=all(
        int(s["race_relative_frame"])==i and
        s["original_native_full_wram_byte_difference"]["differing_byte_count"]==n
        for i,n in [(0,0),(1,4),(2,4),(4,4),(8,0)]
        for s in mesh["samples"] if int(s["race_relative_frame"])==i)
    if not result["same_first_divergence_as_rf043"]:
        raise ValueError("RF044 original/native first window changed")
    return result
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case_zip",type=Path)
    p.add_argument("--json-out",type=Path)
    a=p.parse_args()
    payload=json.dumps(report(a.case_zip),indent=2,sort_keys=True)+"\n"
    if a.json_out:
        a.json_out.parent.mkdir(parents=True,exist_ok=True)
        a.json_out.write_text(payload,encoding="utf8")
    else:print(payload,end="")
if __name__=="__main__":main()
