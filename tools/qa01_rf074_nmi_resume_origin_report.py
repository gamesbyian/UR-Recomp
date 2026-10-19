#!/usr/bin/env python3
"""RF074: strictly validate executed native NMI resume publication provenance.

This checks only the guest *scheduler's published resume PC origin* from the
existing bridge resume ring, read before NMI stack push. It NEVER re-labels a
scheduler PC as a fetched opcode PC nor accepts a host-frame match as parity.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

TAG="QA01RF047NATIVE seq="
ROW=re.compile(r"QA01RF047NATIVE seq=(\d+) (.*)$")
ITEM=re.compile(r"([A-Za-z][A-Za-z0-9]*)=([^\s]+)")
FRAMES=range(1017,1026)
SCHEMA="ur-qa01-rf074-native-NMI-scheduler-resume-origin/1"
KNOWN_SITES={
 "irq_pending","deadline","d9_irq","d9_deadline","quiescent","stable_poll",
 "joypad_wait","nested_handoff","yield_flag","wai","deadline_unwind",
 "yield_unwind","yield_primitive","step_cap","external","rollback"
}

def require(ok:bool,why:str)->None:
    if not ok:raise ValueError(why)

def parse(raw:str)->list[dict]:
    require("QA01RF047NATIVE_TRUNCATED" not in raw,
            "native shared event stream overflow")
    ev=[]
    for line in raw.splitlines():
        if TAG not in line: continue
        require(line.count(TAG)==1,"multiple native events in one physical row")
        m=ROW.fullmatch(line[line.index(TAG):])
        require(m is not None,"truncated native event suffix")
        pairs=ITEM.findall(m.group(2))
        require(" ".join(f"{k}={v}" for k,v in pairs)==m.group(2),
                "native event tokens malformed")
        f=dict(pairs)
        require(len(f)==len(pairs),"native repeated key malformed")
        seq=int(m.group(1))
        require(seq==len(ev)+1,"native source event sequence gap or reorder")
        try: frame=int(f["f"])
        except (ValueError,KeyError) as e:
            raise ValueError("native source event frame missing") from e
        require(frame in FRAMES,"RF074 native event outside research window")
        f["seq"]=seq
        ev.append(f)
    require(bool(ev),"no genuine native source events")
    return ev

def inspect(raw:str)->dict:
    events=parse(raw)
    per_frame={frame:[] for frame in FRAMES}
    for row in events:
        per_frame[int(row["f"])].append(row)
    results=[]
    for frame in FRAMES:
        rows=per_frame[frame]
        stage=[(i,row) for i,row in enumerate(rows)
               if row.get("stage") in ("entry","resume_origin","after_push",
                                       "compiled_rti","interp_rti","handler_return")]
        require([x[1]["stage"] for x in stage]==
                ["entry","resume_origin","after_push","compiled_rti","handler_return"],
                "native source NMI resume provenance bracket not fully observed")
        (i_entry,entry),(i_orig,orig),(i_push,push),(_,rti),(_,done)=stage
        require(i_orig==i_entry+1 and i_push==i_orig+1,
                "native resume provenance not immediately before original push")
        require(orig["phase"]=="before_real_interrupt_push",
                "native resume origin phase changed")
        require(orig.get("sourceFound")=="1" and orig.get("originMatches")=="1",
                "native resume origin ring missing or does not own published PC")
        require(orig.get("kind") in ("set","restore") and orig.get("site") in KNOWN_SITES,
                "native resume provenance assignment site/kind unqualified")
        try:
            ring_total=int(orig["ringTotal"])
            ring_seq=int(orig["ringSeq"])
            origin_frame=int(orig["sourceFrame"])
            source_sp=int(orig["sourceS"],16)
            prev_pc=int(orig["oldPC"],16)
            emitted_pc=int(orig["newPC"],16)
            scheduler_pc=int(orig["resume"],16)
            vector=int(orig["vector"],16)
            master=int(orig["master"])
            beam_v=int(orig["beamV"])
            beam_h=int(orig["beamH"])
            source_bridge=int(orig["bridgeDepth"])
            source_sched=int(orig["schedDepth"])
            wai=int(orig["waiHalted"])
        except (ValueError,KeyError) as e:
            raise ValueError("native resume source assignment/context fields missing") from e
        require(0<=ring_seq<ring_total and ring_total-ring_seq<=1024 and
                origin_frame<=frame and 0<=source_sp<=0xffff and
                0<=prev_pc<=0xffffff and 0<=scheduler_pc<=0xffffff and
                scheduler_pc==emitted_pc and
                -128<=source_bridge<=127 and -128<=source_sched<=127 and
                wai in (0,1) and beam_v>=0 and beam_h>=0,
                "native last resume ring assignment value/age inconsistent")
        require(orig["resume"]==entry["resume"]==push["resume"] and
                orig["vector"]==entry["vector"]==push["vector"] and
                int(entry["master"])==master==int(push["master"]) and
                entry["S"]=="01F0" and push["S"]=="01EC",
                "native scheduler resume origin not bound to actual real interrupt push")
        require(done["resume"]==entry["resume"] and rti["stage"]=="compiled_rti",
                "native NMI end-of-bracket semantic identity incomplete")
        results.append({
            "host_frame":frame,
            "native_entry_seq":entry["seq"],
            "native_resume_assignment_seq":orig["seq"],
            "native_after_real_push_seq":push["seq"],
            "native_return_seq":rti["seq"],
            "scheduler_resume_PC":f"{scheduler_pc:06X}",
            "last_resume_ring_assignment_old_PC":f"{prev_pc:06X}",
            "last_resume_ring_assignment_new_PC":f"{emitted_pc:06X}",
            "last_resume_ring_assignment_kind":orig["kind"],
            "last_resume_ring_assignment_site":orig["site"],
            "last_resume_ring_assignment_frame":origin_frame,
            "last_resume_ring_source_SP":f"{source_sp:04X}",
            "last_resume_ring_seq":ring_seq,
            "last_resume_ring_total":ring_total,
            "original_native_equivalent_instruction_phase_proven":False,
            "actual_guest_opcode_fetch_at_scheduler_resume_PC_proven":False
        })
    return {
        "schema":SCHEMA,
        "native_RF047_sequenced_event_count":len(events),
        "actual_original_source_2014_NMI_sampled_in_this_capture":False,
        "native_resume_assignment_bound_to_actual_NMI_before_push_count":len(results),
        "native_resume_published_PC_kind":"scheduler_or_LLE_resume_assignment",
        "every_native_resume_origin_is_an_independently_executed_opcode_PC":False,
        "original_native_same_NMI_semantic_phase_proven":False,
        "actual_differing_stack_byte_consumption_proven":False,
        "accepted_USA_events":0,
        "per_frame":results,
    }

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("actual_native_log",type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=inspect(a.actual_native_log.read_bytes().decode("utf8"))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("RF074 real scheduler resume assignment before actual native NMI push qualified; fetched opcode parity HOLD")

if __name__=="__main__":
    main()
