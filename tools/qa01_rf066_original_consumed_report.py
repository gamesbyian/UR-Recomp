#!/usr/bin/env python3
"""Independent RF066 real original macro-return/WRAM source-order verifier.

All RF063 getset entries, actual post-NMI checkpoint and RF066 real post-call
stack returns must form ONE contiguous source-local sequence. This never
promotes the post-return marker to the getter's bus entry or assumes clocks
between native and original are synchronized. RF045 and RF064 are separately
required independent returned-value controls.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import qa01_rf063_original_sequence_report as rf63
import qa01_rf064_original_pull_return_report as rf64

TAG="QA01RF066ORIGCONSUMED "
WATCH=(rf63.BUS,rf63.CHECK,TAG)
TRUNC=("QA01RF063ORIGBUS_TRUNCATED","QA01RF063ORIGCHECKPOINT_TRUNCATED",
       "QA01RF064ORIGPULL_TRUNCATED","QA01RF066ORIGCONSUMED_TRUNCATED",
       "QA01RF045ORIGSTACK_TRUNCATED","QA01RF044ORIGBUS_TRUNCATED")

def examine(raw: str) -> dict:
    if any(t in raw for t in TRUNC):
        raise ValueError("RF066 original observer overflow")
    events=[]
    pulls=[]
    for line in raw.splitlines():
        for prefix in WATCH:
            if prefix in line and not line.startswith(prefix):
                raise ValueError("RF066 source record embedded in unrelated logging")
        if not any(line.startswith(x) for x in WATCH):
            continue
        f=rf63.fields(line)
        try:
            seq=int(f["seq"])
            frame=int(f["f"])
        except (ValueError,KeyError) as e:
            raise ValueError("RF066 source local sequence missing") from e
        if seq != len(events)+1 or not 1017<=frame<=1025:
            raise ValueError("RF066 source original sequence gap, duplicate or frame drift")
        tag = next(x for x in WATCH if line.startswith(x))
        events.append((tag,f))
        if tag==TAG:
            pulls.append((seq,f))
    if not events or not pulls:
        raise ValueError("RF066 real returned stack read witness missing")
    b=[f for tag,f in events if tag==rf63.BUS]
    checkpoints=[(i+1,f) for i,(tag,f) in enumerate(events) if tag==rf63.CHECK]
    if not b or len(checkpoints)!=1:
        raise ValueError("RF066 real original bus entries and exactly one NMI snapshot required")
    cp_seq, cp=checkpoints[0]
    if cp.get("f")!="1017" or cp.get("phase")!="post_real_nmi_push" or not rf63.HEX5.fullmatch(cp.get("stack","")):
        raise ValueError("RF066 original NMI checkpoint not physically bound")
    nmi=[rf63.fields(x) for x in raw.splitlines() if x.startswith(rf63.NMI)]
    if len([x for x in nmi if x.get("f")=="1017" and x.get("new")==cp["stack"]]) != 1:
        raise ValueError("RF066 source checkpoint not independent RF044 original NMI bytes")
    for row in b:
        if row.get("kind") not in ("rb","rw","wb","ww"):
            raise ValueError("RF066 invalid actual source getset class")
        if row.get("width") not in ("1","2") or not rf63.HEX4.fullmatch(row.get("sampled","")):
            raise ValueError("RF066 incomplete RF063 source bus witness")
        try:
            addr=int(row["addr"],16)
            bank=int(row["bank"],16)
        except (KeyError,ValueError) as e:
            raise ValueError("RF066 invalid source bus physical stack address") from e
        width=int(row["width"])
        if addr>0x01f1 or addr+width-1<0x01ed or not (bank==0x7e or ((bank&0x7f)<0x40 and addr<0x2000)):
            raise ValueError("RF066 source bus address outside physically gated original stack")
    rf45=rf64.extract(raw,rf64.MACRO)
    rf64_rows=rf64.extract(raw,rf64.PULL)
    if not rf45 or not rf64_rows:
        raise ValueError("RF066 real source RF045 and RF064 post-call controls missing")
    if [int(x["seq"]) for x in rf45] != list(range(1,len(rf45)+1)):
        raise ValueError("RF066 source actual macro recorder-local sequence incomplete")
    def key(m:dict, label:str) -> tuple:
        try:
            width=int(m["width"])
            value=int(m[label],16)
            base=int(m.get("base",m.get("addr","")),16)
            frame=int(m["f"])
        except (KeyError,ValueError) as e:
            raise ValueError("RF066 missing real original post-call physical identity") from e
        kind=m.get("kind")
        if kind not in ("pullW","pullB") or width!=(2 if kind=="pullW" else 1):
            raise ValueError("RF066 original stack return width/type contradiction")
        if not 1017<=frame<=1025 or base>0x01f1 or base+width-1<0x01ed:
            raise ValueError("RF066 original return address outside actual window")
        return frame,kind,base,width,value
    orig_count=Counter(key(x,"value") for x in rf45 if x.get("kind") in ("pullW","pullB"))
    rf64_count=Counter(key(x,"returned") for x in rf64_rows)
    if not orig_count or orig_count!=rf64_count or len(rf64_rows)!=len(pulls):
        raise ValueError("RF066 population differs from genuine RF045 / RF064 returned stack operations")
    # Multiset agreement cannot qualify a *source-ordered* returned-read
    # producer: repeated 0x26/0x81 values could be swapped between actual
    # guest PC contexts or V/H clock positions without changing Counters.
    # Preserve the original encounter order, original-local frame/V/H clocks,
    # physical stack address, width, true returned value and *post-call*
    # PB:PCw snapshots across all three independently logged producers.
    pull_macros=[x for x in rf45 if x.get("kind") in ("pullW","pullB")]
    if len(pull_macros)!=len(rf64_rows) or len(rf64_rows)!=len(pulls):
        raise ValueError("RF066 source return ordinal population incomplete")
    for ordinal,(macro,prior,(_,now)) in enumerate(
            zip(pull_macros,rf64_rows,pulls),1):
        if any(macro.get(k)!=prior.get(k) or prior.get(k)!=now.get(k)
               for k in ("f","v","h","kind","width")):
            raise ValueError("RF066 source clock or operation order moved at pull " + str(ordinal))
        if macro.get("addr")!=prior.get("base") or prior.get("base")!=now.get("base"):
            raise ValueError("RF066 physical source stack address reordered")
        if any(key(row,label)!=key(macro,"value") for row,label in
               ((prior,"returned"),(now,"returned"))):
            raise ValueError("RF066 returned data not ordered with RF045 macro")
        pc=macro.get("pc")
        if pc is None or prior.get("pc")!=pc or (
                now.get("postPB")+":"+now.get("postPC") if
                now.get("postPB") is not None and now.get("postPC") is not None
                else None)!=pc:
            raise ValueError("RF066 original post-call PB:PCw context reordered")
    rf64_identified=Counter((key(x,"returned"),int(x["before"]),int(x["after"])) for x in rf64_rows)
    consumed=Counter()
    no_interleaving=0
    with_interleaving=0
    for seq,f in pulls:
        try:
            before=int(f["before"]);after=int(f["after"])
            flag=int(f["bounded"])
        except (ValueError,KeyError) as e:
            raise ValueError("RF066 missing real original getter lifetime bounds") from e
        if before<0 or after<before or after+1!=seq or flag!=int(before==after):
            raise ValueError("RF066 returned read ordering or interval bound fabricated")
        if f.get("phase")!="post_real_stack_getter_return":
            raise ValueError("RF066 reported bus entry as real post-call value")
        if len(f.get("postPB",""))!=2 or len(f.get("postPC",""))!=4:
            raise ValueError("RF066 missing original post-call PC context")
        try:
            int(f["postPB"],16);int(f["postPC"],16)
        except ValueError as e:
            raise ValueError("RF066 original post-call PC malformed") from e
        ident=(key(f,"returned"),before,after)
        consumed[ident]+=1
        if before==after:
            no_interleaving+=1
        else:
            with_interleaving+=1
    if consumed!=rf64_identified:
        raise ValueError("RF066 source return differs from RF064 independent actual macro observation")
    if Counter(key(f,"returned") for _,f in pulls)!=orig_count:
        raise ValueError("RF066 real return missing in original RF045 actual macro control")
    return {
        "schema":"ur-qa01-rf066-actual-original-stack-return-order/1",
        "source_log_sha256":hashlib.sha256(raw.encode()).hexdigest(),
        "source_original_event_seq_contiguous":True,
        "total_sequenced_original_source_events":len(events),
        "sequenced_source_getset_entries":len(b),
        "sequenced_source_getset_read_entries":sum(x["kind"].startswith("r") for x in b),
        "sequenced_source_getset_write_entries":sum(x["kind"].startswith("w") for x in b),
        "real_source_original_post_NMI_checkpoint_seq":cp_seq,
        "real_source_original_post_NMI_raw_5_stack_bytes":cp["stack"].upper(),
        "actual_original_post_getter_return_count":len(pulls),
        "actual_original_returns_with_no_other_RF063_event_inside_getter":no_interleaving,
        "actual_original_returns_with_intervening_RF063_events":with_interleaving,
        "real_original_return_matches_RF045_and_RF064":True,
        "all_original_returns_strictly_positional_across_RF045_RF064_RF066":True,
        "strict_source_clock_domain_original_only":True,
        "getset_entry_time_return_value_proven":False,
        "read_value_physically_observed_post_call":True,
        "complete_original_and_native_bus_read_population_proven":False,
        "original_native_clock_axes_rebased":False,
        "eligible_for_qa01_causal_window":False,
        "accepted_USA_events":0,
    }

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_log",type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=examine(a.original_log.read_bytes().decode("utf8"))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("RF066 source original real post-call stack reads witnessed; full causal parity HOLD")

if __name__=="__main__":
    main()
