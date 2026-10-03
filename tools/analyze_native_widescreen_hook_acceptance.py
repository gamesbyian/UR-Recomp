#!/usr/bin/env python3
"""Validate the accepted +8 hook and the host-owned +16 capacity prototype."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

PRIMARY_RE = re.compile(
    r"URWS_PRIMARY margin=(\d+) camx=(\d+) edge=([0-9A-Fa-f]{4}) "
    r"count=(\d+) payload=([0-9A-Fa-f]{64})"
)
PREP8_RE = re.compile(
    r"URWS_PREP margin=8 camx=(\d+) edge=([0-9A-Fa-f]{4}) "
    r"count=(\d+) payload=([0-9A-Fa-f]{64})"
)
PREP16_RE = re.compile(
    r"URWS_PREP16 camx=(\d+) edge=([0-9A-Fa-f]{4}) "
    r"count=(\d+) payload=([0-9A-Fa-f]{64})"
)
SHADOW16_RE = re.compile(
    r"URWS_SHADOW16 camx=(\d+) edge=([0-9A-Fa-f]{4}) "
    r"count=(\d+) payload=([0-9A-Fa-f]{64})"
)
CLEAN8_RE = re.compile(r"URWS_CLEANUP margin=8")
CLEAN16_RE = re.compile(r"URWS_CLEANUP16 shadow=(\d+)")
STOP16_RE = re.compile(r"URWS_STOP margin=16 reason=([^\s]+)")
LIMIT24_RE = re.compile(
    r"URWS_LIMIT margin=24 required_extra_columns=3 "
    r"guest_extra_horizontal_lanes=1 host_shadow_columns=1 "
    r"first_constraint=host-shadow-capacity"
)

PROTECTED_WORDS = {
    "player_x":0x0411,"player_y":0x0415,"camera_x":0x0419,"camera_y":0x041D,
    "camera_dx":0x04F5,"camera_dy":0x04F9,"x_speed":0x04B7,"y_speed":0x04BB,
    "pitch":0x04C7,"contact":0x0E95,"laps":0x0EF1,"checkpoint":0x1199,"finish":0x119D,
}

def read_words(path: Path) -> dict[str,int]:
    raw=path.read_bytes()
    if len(raw)<0x1200:
        raise ValueError(f"{path}: WRAM dump too small ({len(raw)} bytes)")
    return {name: raw[a] | (raw[a+1]<<8) for name,a in PROTECTED_WORDS.items()}

def _rows(pattern: re.Pattern[str], log: str) -> list[dict]:
    return [
        {"camx":int(camx),"edge":int(edge,16),"count":int(count),"payload":payload.upper()}
        for camx,edge,count,payload in pattern.findall(log)
    ]

def _ring_column(edge:int)->int:
    return edge & 0x1F

def _ring_adjacent(a:int,b:int)->bool:
    return ((_ring_column(a)+1)&0x1F)==_ring_column(b)

def _longest_true_run(values:list[bool])->int:
    best=cur=0
    for value in values:
        if value:
            cur+=1; best=max(best,cur)
        else:
            cur=0
    return best

def _stock_matches(rows:list[dict], control:list[dict], max_advance:int=24)->tuple[list[dict],int,int]:
    examples=[]; flags=[]; candidates=0
    for row in rows:
        possible=[
            stock for stock in control
            if stock["edge"]==row["edge"]
            and stock["camx"]>row["camx"]
            and 1<=stock["camx"]-row["camx"]<=max_advance
        ]
        if possible:
            candidates+=1
        exact=[stock for stock in possible if stock["payload"]==row["payload"]]
        flags.append(bool(exact))
        if exact:
            stock=min(exact,key=lambda x:(x["camx"]-row["camx"],x["camx"]))
            examples.append({
                "prepared_camx":row["camx"],"stock_camx":stock["camx"],
                "camera_x_advance":stock["camx"]-row["camx"],
                "edge":row["edge"],"payload":row["payload"],
            })
    return examples,candidates,_longest_true_run(flags)

def analyze(logs:dict[int,str], dumps:dict[int,Path])->dict:
    primary={
        m:[
            {"margin":int(mm),"camx":int(camx),"edge":int(edge,16),
             "count":int(count),"payload":payload.upper()}
            for mm,camx,edge,count,payload in PRIMARY_RE.findall(logs[m])
        ] for m in logs
    }
    prep8={m:_rows(PREP8_RE,logs[m]) for m in logs}
    prep16={m:_rows(PREP16_RE,logs[m]) for m in logs}
    shadow16={m:_rows(SHADOW16_RE,logs[m]) for m in logs}
    clean8={m:len(CLEAN8_RE.findall(logs[m])) for m in logs}
    clean16={m:[int(x) for x in CLEAN16_RE.findall(logs[m])] for m in logs}
    stop16={m:STOP16_RE.findall(logs[m]) for m in logs}
    limit24={m:bool(LIMIT24_RE.search(logs[m])) for m in logs}

    states={m:read_words(dumps[m]) for m in dumps}
    control_state=states[0]
    diffs={}
    for m,state in states.items():
        if m==0: continue
        diffs[m]={k:{"control":control_state[k],f"margin_{m}":state[k]}
                  for k in control_state if state[k]!=control_state[k]}

    control=[
        row for row in primary.get(0,[])
        if row["count"]==16 and row["edge"]!=0xffff
    ]
    stock_deltas={(b["edge"]-a["edge"])&0xffff for a,b in zip(control,control[1:])}|{1}

    # Preserve the accepted +8 contract exactly.
    p8=[row for row in prep8.get(8,[]) if row["count"]==16]
    p8_primary={row["camx"]:row for row in primary.get(8,[])
                if row["count"]==16 and row["edge"]!=0xffff}
    p8_bad=[]
    p8_comp=0
    for row in p8:
        base=p8_primary.get(row["camx"])
        if base is None: continue
        p8_comp+=1
        delta=(row["edge"]-base["edge"])&0xffff
        if not _ring_adjacent(base["edge"],row["edge"]) or delta not in stock_deltas:
            p8_bad.append({"camx":row["camx"],"delta":delta})
    p8_matches,p8_candidates,p8_run=_stock_matches(p8,control,16)
    p8_terminal=(len(p8)==clean8.get(8,0)+1)
    p8_balanced=(len(p8)>0 and (len(p8)==clean8.get(8,0) or p8_terminal))

    # +16: first extra column uses the same real guest secondary lane; second is host-only.
    p16=[row for row in prep16.get(16,[]) if row["count"]==16]
    s16=[row for row in shadow16.get(16,[]) if row["count"]==16]
    p16_primary={row["camx"]:row for row in primary.get(16,[])
                 if row["count"]==16 and row["edge"]!=0xffff}
    pairs=[]
    pair_bad=[]
    shadow_by_cam={row["camx"]:row for row in s16}
    for first in p16:
        second=shadow_by_cam.get(first["camx"])
        if second is None:
            continue
        base=p16_primary.get(first["camx"])
        if base is None:
            continue
        d1=(first["edge"]-base["edge"])&0xffff
        d2=(second["edge"]-first["edge"])&0xffff
        ok1=_ring_adjacent(base["edge"],first["edge"]) and d1 in stock_deltas
        ok2=_ring_adjacent(first["edge"],second["edge"]) and d2 in stock_deltas
        pairs.append({"camx":first["camx"],"first_delta":d1,"second_delta":d2,
                      "first_ok":ok1,"second_ok":ok2})
        if not (ok1 and ok2):
            pair_bad.append(pairs[-1])

    p16_matches,p16_candidates,p16_run=_stock_matches(p16,control,24)
    # The second future column is naturally farther ahead in camera space than
    # the first. The observed steady-scroll cadence is roughly 14 px/column,
    # so use a bounded 64 px lookup window without relaxing edge/payload identity.
    s16_matches,s16_candidates,s16_run=_stock_matches(s16,control,64)
    p16_terminal=(len(p16)==len(clean16.get(16,[]))+1)
    p16_balanced=(
        len(p16)>0 and len(p16)==len(s16)
        and (len(p16)==len(clean16.get(16,[])) or p16_terminal)
        and all(x==1 for x in clean16.get(16,[]))
    )

    checks={
        "margin0_control_inert":(
            not prep8.get(0) and not prep16.get(0) and not shadow16.get(0)
            and clean8.get(0,0)==0 and not clean16.get(0) and not limit24.get(0)
        ),
        "margin8_exercised":len(p8)>0,
        "margin8_all_counts_16":len(p8)==len(prep8.get(8,[])),
        "margin8_cleanup_balanced":p8_balanced,
        "margin8_ring_adjacent_and_stock_compatible":p8_comp>=309 and not p8_bad,
        "margin8_future_stock_exact_matches":len(p8_matches)>=309,
        "margin8_future_stock_consecutive_run":p8_run>=14,
        "margin8_protected_state_equal":not diffs.get(8),

        "margin16_exercised":len(p16)>0 and len(s16)>0,
        "margin16_two_columns_per_event":len(p16)==len(s16),
        "margin16_cleanup_balanced":p16_balanced,
        "margin16_no_structural_stop":not stop16.get(16),
        "margin16_both_steps_ring_adjacent_and_stock_compatible":len(pairs)>=100 and not pair_bad,
        "margin16_first_column_future_stock_matches":len(p16_matches)>=100 and p16_run>=14,
        "margin16_second_column_future_stock_matches":len(s16_matches)>=100 and s16_run>=14,
        "margin16_protected_state_equal":not diffs.get(16),

        "margin24_stops_at_host_shadow_capacity":(
            limit24.get(24) and not prep8.get(24) and not prep16.get(24)
            and not shadow16.get(24) and not diffs.get(24)
        ),
    }

    return {
        "schema_version":2,
        "reference_acceptance":{
            "plus8_pr":219,"plus8_workflow_run":37066327707,
            "native_plus8_pr":228,"native_plus8_workflow_run":37081391730,
            "mechanism":"stock-A59E-replay-with-one-real-secondary-lane",
        },
        "architecture":{
            "margin8":"unchanged accepted guest secondary-lane staging",
            "margin16":"same first extra guest lane plus one host-owned shadow column",
            "guest_extra_horizontal_lanes":1,
            "host_shadow_columns":1,
            "synthetic_guest_descriptor_lanes":0,
            "margin24_first_constraint":"host-shadow-capacity",
        },
        "runtime":{
            "margin0_primary_events":len(control),
            "margin8_prepare_events":len(p8),
            "margin8_cleanup_events":clean8.get(8,0),
            "margin8_stock_comparable_steps":p8_comp,
            "margin8_exact_future_stock_matches":len(p8_matches),
            "margin8_future_stock_candidates":p8_candidates,
            "margin8_longest_exact_run":p8_run,
            "margin16_first_column_events":len(p16),
            "margin16_shadow_column_events":len(s16),
            "margin16_cleanup_events":len(clean16.get(16,[])),
            "margin16_stock_comparable_pairs":len(pairs),
            "margin16_first_exact_future_stock_matches":len(p16_matches),
            "margin16_first_future_stock_candidates":p16_candidates,
            "margin16_first_longest_exact_run":p16_run,
            "margin16_second_exact_future_stock_matches":len(s16_matches),
            "margin16_second_future_stock_candidates":s16_candidates,
            "margin16_second_longest_exact_run":s16_run,
            "margin16_stop_reasons":stop16.get(16,[]),
            "margin24_limit_reported":limit24.get(24,False),
        },
        "plus8_future_stock_examples":p8_matches[:20],
        "plus16_first_column_future_stock_examples":p16_matches[:20],
        "plus16_second_column_future_stock_examples":s16_matches[:20],
        "plus16_step_examples":pairs[:40],
        "protected_state_differences":diffs,
        "checks":checks,
        "accepted":all(checks.values()),
        "next_capacity_constraint":"host-shadow-capacity",
    }

def render(r:dict)->str:
    c,n=r["checks"],r["runtime"]
    return "\n".join([
        "# Native Widescreen preparation-capacity acceptance","",
        "The accepted +8 guest path is preserved. +16 reuses that same first "
        "secondary lane and retains only the second stock-prepared column in host-owned shadow storage.","",
        f"- stock margin 0 inert: **{c['margin0_control_inert']}**",
        f"- +8 preparation events: **{n['margin8_prepare_events']}**",
        f"- +8 exact later-stock matches: **{n['margin8_exact_future_stock_matches']}**",
        f"- +8 protected state equal: **{c['margin8_protected_state_equal']}**",
        f"- +16 first-column events: **{n['margin16_first_column_events']}**",
        f"- +16 host-shadow events: **{n['margin16_shadow_column_events']}**",
        f"- +16 comparable adjacent pairs: **{n['margin16_stock_comparable_pairs']}**",
        f"- +16 first-column exact later-stock matches: **{n['margin16_first_exact_future_stock_matches']}**",
        f"- +16 second-column exact later-stock matches: **{n['margin16_second_exact_future_stock_matches']}**",
        f"- +16 first-column longest exact run: **{n['margin16_first_longest_exact_run']}**",
        f"- +16 second-column longest exact run: **{n['margin16_second_longest_exact_run']}**",
        f"- +16 protected state equal: **{c['margin16_protected_state_equal']}**",
        f"- +16 no structural stop: **{c['margin16_no_structural_stop']}**",
        f"- +24 stops at host-shadow capacity: **{c['margin24_stops_at_host_shadow_capacity']}**","",
        "No synthetic guest descriptor lane is introduced. The second +16 column "
        "exists only as host-owned presentation data after the stock helper has advanced "
        "inside the snapshotted replay state; authoritative CPU/WRAM is restored before "
        "normal execution resumes.","",
        f"Overall accepted: **{r['accepted']}**",""
    ])

def main()->int:
    ap=argparse.ArgumentParser()
    for m in (0,8,16,24):
        ap.add_argument(f"--log-{m}",type=Path,required=True)
        ap.add_argument(f"--dump-{m}",type=Path,required=True)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    args=ap.parse_args()
    logs={m:getattr(args,f"log_{m}").read_text(encoding="utf-8",errors="replace") for m in (0,8,16,24)}
    dumps={m:getattr(args,f"dump_{m}") for m in (0,8,16,24)}
    report=analyze(logs,dumps)
    md=render(report)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True,exist_ok=True)
        args.md_out.write_text(md,encoding="utf-8")
    print(md,end="")
    return 0 if report["accepted"] else 2

if __name__=="__main__":
    raise SystemExit(main())
