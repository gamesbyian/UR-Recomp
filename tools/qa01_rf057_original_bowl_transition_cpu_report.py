#!/usr/bin/env python3
"""RF057 fail-closed qualified executed opcode receipt from real Bowl replay.

No inferred native PC or assigned original/native CPU clock registration.
"""
from __future__ import annotations
import argparse, json, re, zipfile
from collections import Counter
from pathlib import Path

TAG="QA01RF057ORIGCPU "
KV=re.compile(r"(\w+)=([^\s]+)")
CANDIDATES={
    "post-race-menu":(0xADD4,0xAF0C),
    "menu-confirm":(0xB6BE,0xB926),
    "wait-input":(0xC1F5,0xC23B),
    "read-pads":(0xD1DB,0xD1F9),
    "wait-frames-or-button":(0xF7E5,0xF805),
}
EXPECTED_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
def inspect(log:str)->dict:
    if "QA01RF057ORIGCPU_TRUNCATED" in log:
        raise ValueError("RF057 actual source CPU opcode records truncated")
    rows=[]
    last={}
    for line in log.splitlines():
        if not line.startswith(TAG):continue
        f=dict(KV.findall(line))
        required=("frame","seq","pc","next","op","pre_h","pre_v","post_h",
                  "post_v","a0","a1","p0","p1","s0","s1","c0","z0","n0","o0","c1","z1","n1","o1","joy72","joy73",
                  "joy74","joy75","latch8f","raw30d","raw30f")
        if any(k not in f for k in required):
            raise ValueError("RF057 missing original executed CPU context")
        frame=int(f["frame"])
        pc=int(f["pc"].split(":")[-1],16)
        bank=int(f["pc"].split(":")[0],16)
        group=next((name for name,(a,b) in CANDIDATES.items() if a<=pc<=b),None)
        if (frame not in range(4686,4695) or bank not in (0,0x80)
                or group is None or int(f["seq"])!=last.get(frame,0)+1):
            raise ValueError("RF057 actual original CPU PC/frame/sequence invalid")
        last[frame]=int(f["seq"])
        rows.append((frame,pc,group,f))
    if not rows:
        raise ValueError("RF057 no original source executed menu instructions observed")
    by_group=Counter(r[2] for r in rows)
    frame_counts=Counter(r[0] for r in rows)
    return {
       "schema":"rf057-executed-retail-USA-original-bowl-menu-instruction-boundary-v1",
       "recorded_original_executed_CPU_instruction_count":len(rows),
       "original_actual_cpu_guest_frame_histogram":{str(k):v for k,v in sorted(frame_counts.items())},
       "original_decoded_executed_candidate_group_count":dict(sorted(by_group.items())),
       "first_original_guest_executed_candidate_row":rows[0][3],
       "last_original_guest_executed_candidate_row":rows[-1][3],
       "source_original_opcode_dispatch_repeated_or_reordered":False,
       "native_generated_PC_executed_witness_proven":False,
       "original_native_absolute_CPU_NMI_epoch_registered":False,
       "actual_CPU_controller_register_read_proven":False,
       "first_transition_writer_predicate_proven":False,
       "original_native_full_event_equivalence_proven":False,
       "accepted_complete_USA_events":0,
    }

def case(path:Path)->dict:
    with zipfile.ZipFile(path) as z:
        items=z.namelist()
        if len(items)<50 or not any(x.endswith("/replay/reference.log") for x in items):
            raise ValueError("RF057 full authentic Bowl original/native case archive missing")
        logname=next(x for x in items if x.endswith("/replay/reference.log"))
        producer=next(x for x in items if x.endswith("/bowl-report.json") or x=="bowl-report.json")
        data=json.loads(z.read(producer))
        if data.get("rom_sha256")!=EXPECTED_SHA or data.get("course_id")!="course:03":
            raise ValueError("RF057 original USA ROM/course source identity changed")
        result=inspect(z.read(logname).decode("utf8","replace"))
        result["source_2014_rom_sha256"]=EXPECTED_SHA
        result["producer_case_name"]=data.get("name")
        return result
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case",type=Path)
    p.add_argument("--out",type=Path)
    x=p.parse_args()
    obj=json.dumps(case(x.case),indent=2,sort_keys=True)+"\n"
    if x.out:x.out.write_text(obj,encoding="utf8")
    else:print(obj,end="")
if __name__=="__main__":main()
