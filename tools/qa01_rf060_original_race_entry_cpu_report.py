#!/usr/bin/env python3
"""RF060 qualified *executed original* 65816 Race_Main entry/caller receipt.

Original source frame and PB:PC only. The logged immediate preceding decoded
CPU opcode is not yet the causal branch if interrupts occurred or host-frame
epochs differ. Never infer a native recomp instruction PC from this report.
"""
from __future__ import annotations
import argparse,json,re
from collections import Counter
from pathlib import Path

HEART="QA01RF060HEART "
ROW="QA01RF060ORIGCPU "
KV=re.compile(r"([a-zA-Z]\w*)=([^\s]+)")
FRAMES=list(range(4686,4695))
TARGET_PCS=("83:CAC4","83:CBE2","83:CC1C","83:CC47")
REQUIRED=("seq","frame","pre_v","pre_h","pc","op","prev","prevop",
          "prevframe","prev_v","prev_h","enter","a","x","y","s","p",
          "c","z","n","o","next","post_v","post_h",
          "a1","x1","y1","s1","c1","z1","n1","o1")
def splitpc(s:str)->tuple[int,int]:
    a=s.split(":")
    if len(a)!=2 or len(a[0])!=2 or len(a[1])!=4:
        raise ValueError("RF060 malformed original guest bank:PC")
    return int(a[0],16),int(a[1],16)

def inspect(log:str)->dict:
    if "QA01RF060ORIGCPU_TRUNCATED" in log or "QA01RF060HEART_TRUNCATED" in log:
        raise ValueError("RF060 original source CPU trace truncated")
    beats=[];rows=[]
    for line in log.splitlines():
        if line.startswith(HEART):
            d=dict(KV.findall(line))
            if any(x not in d for x in ("frame","pbpc","op","v","h")):
                raise ValueError("RF060 source CPU dispatch heartbeat incomplete")
            splitpc(d["pbpc"])
            beats.append((int(d["frame"]),d))
        elif line.startswith(ROW):
            d=dict(KV.findall(line))
            if any(x not in d for x in REQUIRED):
                raise ValueError("RF060 true original CPU pre/post context absent")
            f=int(d["frame"])
            if (int(d["seq"])!=len(rows)+1 or f not in FRAMES
                or not (0xC8E0<=splitpc(d["pc"])[1]<=0xCC70)
                or splitpc(d["pc"])[0]!=0x83
                or int(d["enter"]) not in (0,1)):
                raise ValueError("RF060 genuine original opcode count/PC/frame/entry invalid")
            prev=splitpc(d["prev"])
            if int(d["enter"])==1 and (prev[0]==0x83 and 0xC8E0<=prev[1]<=0xCC70):
                raise ValueError("RF060 claimed entry from inside same CPU code range")
            if int(d["enter"])==0 and not (prev[0]==0x83 and 0xC8E0<=prev[1]<=0xCC70):
                raise ValueError("RF060 missed genuine cross-range source entry")
            splitpc(d["next"])
            rows.append(d)
    if [f for f,_ in beats]!=FRAMES:
        raise ValueError("RF060 source CPU frame heartbeat coverage incomplete")
    if not rows:
        raise ValueError("RF060 no original 65816 Race_Main opcode executed")
    pcs=Counter(d["pc"] for d in rows)
    first=rows[0]
    must_have={k:next((d for d in rows if d["pc"]==k and int(d["frame"])==4688),None)
               for k in TARGET_PCS}
    if any(v is None for v in must_have.values()):
        raise ValueError("RF060 genuine source scene writer opcode not observed in frame4688")
    entries=[d for d in rows if int(d["enter"])==1]
    return {
        "schema":"rf060-retail-USA-Bowl-original-RaceMain-executed-entry-with-preceding-opcode-v1",
        "source_original_true_CPU_frame_heartbeats":[f for f,_ in beats],
        "true_original_Race_Main_range_executed_opcode_rows":len(rows),
        "first_true_original_CPU_Race_Main_interval_opcode":first,
        "real_cross_range_CPU_entry_rows":entries[:150],
        "all_actual_cross_range_CPU_entry_count":len(entries),
        "real_source_original_scene_setup_opcode_records":must_have,
        "original_actual_opcodes_in_C8E0_CC70_unique":len(pcs),
        "source_original_executed_CPU_site_counts":dict(sorted(pcs.items())),
        "first_150_original_executed_CPU_instruction_rows":rows[:150],
        "original_65816_source_to_native_guest_PC_equivalence_proven":False,
        "physical_CPU_memory_bus_writer_for_scene_fields_proven_by_this_probe":False,
        "controller_register_4218_read_condition_proven":False,
        "absolute_original_native_CPU_NMI_clock_epoch_registered":False,
        "independent_USA_complete_events_accepted":0,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_source_reference_log",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    text=json.dumps(inspect(a.original_source_reference_log.read_text(encoding="utf8",errors="replace")),indent=2,sort_keys=True)+"\n"
    if a.out:a.out.write_text(text,encoding="utf8")
    else:print(text,end="")
if __name__=="__main__":main()
