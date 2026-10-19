#!/usr/bin/env python3
"""RF067: independently audit real original source stack PUSH->PULL macro lineage.

A PullB/PullW *actual returned value* is source-real RF045. A preceding RF045
PushB/PushW is source-real, not an inferred writer. This reconstructs only
the bounded ordered stack-MACRO stream; intervening nonmacro writes, DMA,
true mid-call bus phases and native timing are NOT proven absent. Preserve
unknown initial bytes and any mismatches instead of rewriting memory.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

SCHEMA="ur-qa01-rf067-original-stack-macro-lineage/1"
TAG="QA01RF045ORIGSTACK "
REAL_CASE_SHA="7891a24124c67f414e9b00ed2bb1dbe2e59e4a2b6c50b558e920c25d885e63ea"
REAL_ORIGINAL_LOG_SHA="0dfe14195cffc9fc2e044adb372f81c9440e94e4b0e5330671906934d475bfad"
LOG="work/zoom-zoo/replay/reference.log"
TARGET=range(0x01ed,0x01f2)
KINDS={"pullB":(1,1),"pullW":(2,1),"pushB":(1,-1),"pushW":(2,-1)}

def require(ok:bool,why:str)->None:
    if not ok:
        raise ValueError(why)

def parse(raw:str)->list[dict]:
    if "QA01RF045ORIGSTACK_TRUNCATED" in raw:
        raise ValueError("real original RF045 stack recorder truncated")
    entries=[]
    for line in raw.splitlines():
        if TAG in line and not line.startswith(TAG):
            raise ValueError("original macro witness buried within another writer line")
        if not line.startswith(TAG):
            continue
        f=dict(x.split("=",1) for x in line.split()[1:] if "=" in x)
        try:
            seq=int(f["seq"]);frame=int(f["f"])
            kind=f["kind"];addr=int(f["addr"],16)
            width=int(f["width"]);value=int(f["value"],16)
            sp0=int(f["sp0"],16);sp1=int(f["sp1"],16)
            pb,pc=f["pc"].split(":")
            int(pb,16);int(pc,16)
        except (KeyError,ValueError) as e:
            raise ValueError("real original macro lacks source provenance") from e
        require(seq==len(entries)+1 and 1017<=frame<=1025 and kind in KINDS,
                "RF045 macro sequence, frame or kind invalid")
        require(width==KINDS[kind][0] and 0<=value<(1<<(8*width)),
                "real macro width/value invalid")
        require(0<=addr<=0xffff and 0<=sp0<=0xffff and 0<=sp1<=0xffff,
                "real macro stack physical value invalid")
        require(addr<=0x01f1 and addr+width-1>=0x01ed,
                "source macro escaped bounded physically mapped stack")
        expect_sp1=(sp0+KINDS[kind][1]*width)&0xffff
        expect_addr=((sp0 - (1 if kind=="pushW" else 0)) if kind.startswith("push")
                     else (sp0+1)) & 0xffff
        require(sp1==expect_sp1 and addr==expect_addr,
                "source macro post-operation SP/address disagrees with actual stack semantics")
        entries.append({"seq":seq,"frame":frame,"kind":kind,"address":addr,
                        "width":width,"value":value,"sp0":sp0,"sp1":sp1,
                        "pc":f["pc"]})
    if not entries:
        raise ValueError("original true macro source events missing")
    return entries

def audit(entries:list[dict])->dict:
    # Macro completion order, not a claimed total bus order across interrupts.
    last={}
    kind_count=Counter()
    unknown=[]
    matches=0
    mismatches=[]
    status=[]
    last_frame=None
    for n,e in enumerate(entries,1):
        if e["seq"]!=n or (last_frame is not None and e["frame"]<last_frame):
            raise ValueError("original macro execution order missing/regressed")
        last_frame=e["frame"]
        kind=e["kind"]
        if kind not in KINDS or KINDS[kind][0]!=e["width"]:
            raise ValueError("source stack operation class/width inconsistent")
        kind_count[kind]+=1
        a=e["address"];w=e["width"];v=e["value"]
        expected=[(v>>(8*i))&255 for i in range(w)]
        if kind.startswith("push"):
            for i,byte in enumerate(expected):
                last[a+i]={"value":byte,"source_macro_seq":e["seq"],
                           "frame":e["frame"],"kind":kind,"pc":e["pc"]}
        else:
            prior=[last.get(a+i) for i in range(w)]
            if any(x is None for x in prior):
                unknown.append({"pull_seq":e["seq"],"frame":e["frame"],
                                "address":f"{a:04X}","width":w,
                                "returned":f"{v:04X}",
                                "missing_addresses":[f"{a+i:04X}" for i,x in enumerate(prior)
                                                     if x is None]})
            else:
                differing=[{"address":f"{a+i:04X}","returned":f"{expected[i]:02X}",
                            "observed_prior_macro_value":f"{x['value']:02X}",
                            "source_writer_seq":x["source_macro_seq"]}
                           for i,x in enumerate(prior) if expected[i]!=x["value"]]
                if differing:
                    mismatches.append({"pull_seq":e["seq"],"frame":e["frame"],
                                      "address":f"{a:04X}","width":w,
                                      "returned":f"{v:04X}","raw_differences":differing})
                else:
                    matches+=1
            if kind=="pullB" and a==0x01ed:
                status.append({"frame":e["frame"],"pull_seq":e["seq"],
                               "returned":f"{v:02X}","post_call_pc":e["pc"],
                               "preceding_macro_write":
                                   ({"kind":prior[0]["kind"],
                                     "value":f"{prior[0]['value']:02X}",
                                     "source_seq":prior[0]["source_macro_seq"],
                                     "pc":prior[0]["pc"],"frame":prior[0]["frame"]}
                                    if prior[0] else None)})
    pulls=kind_count["pullB"]+kind_count["pullW"]
    return {
        "schema":SCHEMA,
        "source_observation_phase":"RF045 completed original Snes9x stack macro",
        "all_macro_seq_contiguous":True,
        "macro_counts":{k:kind_count[k] for k in sorted(KINDS)},
        "total_actual_stack_macro_operations":len(entries),
        "total_actual_macro_pulls":pulls,
        "pulls_with_all_bytes_preceded_by_a_macro_writer_and_exact_return":matches,
        "pulls_with_unobserved_initial_byte_or_writer":len(unknown),
        "unknown_original_macro_pulls":unknown,
        "pulls_with_conflicting_last_macro_writer":len(mismatches),
        "raw_conflicting_original_macro_pulls":mismatches,
        "source_status_01ed_pulls":status,
        "source_status_01ed_value_counts":dict(sorted(Counter(x["returned"] for x in status).items())),
        "stack_writer_and_reader_population_complete_outside_RF045_macros":False,
        "native_guest_consumption_order_qualified":False,
        "cpu_bus_cycle_clock_registered":False,
        "causal_window_or_all_USA_event_admission":False,
        "accepted_USA_events":0
    }

def authenticated_case(path:Path, expected_digest:str=REAL_CASE_SHA)->dict:
    raw_zip=path.read_bytes()
    digest=hashlib.sha256(raw_zip).hexdigest()
    require(digest==expected_digest,"RF067 frozen real original case artifact digest drift")
    with zipfile.ZipFile(path) as z:
        require(z.testzip() is None,"RF067 real case ZIP corrupt")
        require(len(z.namelist())==len(set(z.namelist())),"RF067 duplicate archive member ambiguous")
        required=(LOG,"case-result.json","producer-report.json",
                  "rf064-original-pulls.json","qa01-zoo-independent-raw-audit.json")
        require(all(x in z.namelist() for x in required),"RF067 missing original immutable producer controls")
        original=z.read(LOG)
        require(hashlib.sha256(original).hexdigest()==REAL_ORIGINAL_LOG_SHA,
                "RF067 original authentic macro source log hash changed")
        case=json.loads(z.read("case-result.json"))
        producer=json.loads(z.read("producer-report.json"))
        receipt=json.loads(z.read("rf064-original-pulls.json"))
        qa=json.loads(z.read("qa01-zoo-independent-raw-audit.json"))
    require(case["disposition"]=="strict_candidate" and case["release_credit"]==0 and
            case["evidence"]["original_event_frames"]==5163 and
            case["evidence"]["next_bowl_bounded"]["fresh_original_entry_offset"]==267 and
            case["evidence"]["next_bowl_bounded"]["fresh_native_entry_offset"]==267,
            "RF067 real archived gameplay controls changed")
    require(producer["zoo_race_mesh"]["mesh_checkpoint_count"]==78 and
            producer["zoo_race_mesh"]["masked_or_excluded_wram_bytes"]==0 and
            qa["full_zoo_mesh_exact_pairs"]==51 and
            qa["full_zoo_mesh_unmasked_differing_byte_occurrences"]==92 and
            receipt["original_post_nmi_unmasked_stack"]=="26F0D48226",
            "RF067 real unmasked original/native physical-memory control changed")
    entries=parse(original.decode("utf8"))
    summary=audit(entries)
    require(summary["total_actual_stack_macro_operations"]==1806 and
            summary["total_actual_macro_pulls"]==903 and
            receipt["post_call_actual_original_pull_count"]==903 and
            receipt["actual_returns_with_unique_source_bus_entry"]==0,
            "RF067 actual source population differs from independent source log")
    summary.update({
        "actual_case_zip_sha256":digest,
        "actual_original_log_sha256":hashlib.sha256(original).hexdigest(),
        "source_exact_case_sha":case["source_sha"],
        "source_guest_rom_sha256":case["evidence"]["rom_sha256"],
        "source_original_movie_sha256":case["evidence"]["movie_sha256"],
        "actual_original_native_full_wram_pairs":78,
        "actual_unmasked_byte_difference_occurrences":92,
        "observed_zoo_result_offset":5163,
        "fresh_original_native_next_bowl_offset":267,
        "original_source_read_getset_helper_join_proven":False,
    })
    return summary

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case_zip",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=authenticated_case(a.case_zip)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("RF067 authentic original macro ancestry audited; no causal-window/gameplay gate credit")

if __name__=="__main__":
    main()
