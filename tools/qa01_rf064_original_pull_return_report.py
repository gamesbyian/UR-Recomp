#!/usr/bin/env python3
"""RF064: real RF045 pull-return joins against RF063 *one* getset entry.

The source return is directly observed by the real original PullB/PullW
macro; its RF063 entry sample is only attributed if no other eligible bus
entry occurred during that invocation. All ambiguous/changed data is held.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import qa01_rf063_original_sequence_report as rf63

BUS="QA01RF063ORIGBUS "
MACRO="QA01RF045ORIGSTACK "
PULL="QA01RF064ORIGPULL "

def extract(raw: str, prefix: str) -> list[dict[str,str]]:
    out=[]
    for line in raw.splitlines():
        if prefix in line and not line.startswith(prefix):
            raise ValueError("RF064 mixed original recorder lines")
        if line.startswith(prefix):
            out.append(rf63.fields(line))
    return out

def check(raw: str) -> dict:
    # Requires actual original RF044 NMI matching physical bytes and source
    # ordinal continuity before attempting to attribute a single pull.
    original=rf63.inspect(raw)
    if "QA01RF064ORIGPULL_TRUNCATED" in raw or "QA01RF045ORIGSTACK_TRUNCATED" in raw:
        raise ValueError("RF064 original stack observer truncated")
    buses=extract(raw,BUS)
    macros=extract(raw,MACRO)
    pulls=extract(raw,PULL)
    if not macros or not pulls:
        raise ValueError("RF064 real original stack pull and macro records required")
    if [int(x["seq"]) for x in macros] != list(range(1,len(macros)+1)):
        raise ValueError("RF064 original RF045 macro-local ordinal gaps")
    bus_by_seq={int(row["seq"]):row for row in buses}
    macro_counts=Counter(
        (m.get("f"),m.get("kind"),m.get("addr"),m.get("width"),m.get("value"))
        for m in macros if m.get("kind") in ("pullB","pullW"))
    qualified=0
    ambiguous=0
    for row in pulls:
        try:
            before=int(row["before"])
            after=int(row["after"])
            width=int(row["width"])
            frame=int(row["f"])
            base=int(row["base"],16)
            value=int(row["returned"],16)
            unique=int(row["unique"])
        except (ValueError,KeyError) as e:
            raise ValueError("RF064 incomplete genuine post-call return") from e
        kind=row.get("kind")
        if kind not in ("pullB","pullW") or width!=(1 if kind=="pullB" else 2):
            raise ValueError("RF064 source pull operation identity invalid")
        if not 1017<=frame<=1025 or not 0x01ed<=base<=0x01f1 or base+width-1>0x01f1:
            raise ValueError("RF064 source pull outside bounded physical stack")
        key=(str(frame),kind,f"{base:04X}",str(width),f"{value:04X}")
        # RF045 may print a byte as "0026" or "26" (%04X always 0026).
        if macro_counts[key]<=0:
            raise ValueError("RF064 post-call value not independently RF045 witnessed")
        macro_counts[key]-=1
        is_unique=int(after==before+1 and after<=8192)
        if unique!=is_unique:
            raise ValueError("RF064 claimed unique getset contradicts actual sequence")
        if not is_unique:
            ambiguous+=1
            continue
        bus=bus_by_seq.get(after)
        if bus is None:
            raise ValueError("RF064 return has no sequenced actual getset entry")
        if bus.get("kind")!=("rb" if kind=="pullB" else "rw") or \
           bus.get("f")!=str(frame) or bus.get("addr")!=f"{base:04X}" or \
           bus.get("width")!=str(width):
            raise ValueError("RF064 return and real source bus entry disagree")
        # This is comparison of real returned macro value with separately
        # sampled RAM at the unique WRAM getset entry, NOT a derived return.
        if int(bus.get("sampled","-1"),16)!=value:
            raise ValueError("RF064 consumed original pull differs from bus-entry RAM sample")
        qualified+=1
    if any(count != 0 for count in macro_counts.values()):
        raise ValueError("RF064 missing source-original post-call records for RF045 true pulls")
    return {
        "schema":"ur-qa01-rf064-original-consumed-pull-join/1",
        "sequenced_original_bus_entries":original["sequenced_original_bus_entries"],
        "original_post_nmi_unmasked_stack":original["checkpoint_actual_unmasked_stack_01ed_to_01f1"],
        "post_call_actual_original_pull_count":len(pulls),
        "actual_returns_with_unique_source_bus_entry":qualified,
        "ambiguous_or_reentrant_original_pulls":ambiguous,
        "original_return_join_all_qualified":qualified==len(pulls),
        "source_sample_and_real_return_values_compared":True,
        "original_native_clocks_aligned":False,
        "source_native_full_memory_causal_ready":False,
        "accepted_USA_events":0
    }

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_log",type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    report=check(a.original_log.read_bytes().decode("utf8"))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("RF064 genuine original stack return evidence retained; no USA admission")

if __name__=="__main__":
    main()
