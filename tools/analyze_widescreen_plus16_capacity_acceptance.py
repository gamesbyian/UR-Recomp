#!/usr/bin/env python3
"""Acceptance for the oracle-fed host-owned +16 Widescreen capacity seam."""
from __future__ import annotations
import argparse, importlib.util, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "ws_plus8", ROOT/"tools/analyze_native_widescreen_hook_acceptance.py"
)
BASE=importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(BASE)

ROW_RE=lambda tag: re.compile(
    tag + r" camx=(\d+) edge=([0-9A-Fa-f]{4}) count=(\d+) payload=([0-9A-Fa-f]{64})"
)
PREP16_RE=ROW_RE(r"URWS_PREP16")
SHADOW16_RE=re.compile(
    r"URWS_SHADOW16 provider=stock-oracle camx=(\d+) edge=([0-9A-Fa-f]{4}) "
    r"count=(\d+) payload=([0-9A-Fa-f]{64})"
)
STOP_RE=re.compile(r"URWS_STOP margin=16 reason=([^\s]+)")
CLEAN_RE=re.compile(r"URWS_CLEANUP16 shadow=(\d+)")
LIMIT24_RE=re.compile(
    r"URWS_LIMIT margin=24 required_extra_columns=3 "
    r"guest_extra_horizontal_lanes=1 host_shadow_columns=1 "
    r"first_constraint=host-shadow-capacity"
)

def rows(rx:re.Pattern[str], text:str)->list[dict]:
    return [
        {"camx":int(c),"edge":int(e,16),"count":int(n),"payload":p.upper()}
        for c,e,n,p in rx.findall(text)
    ]

def stock_primary(text:str)->list[dict]:
    out=[]
    for mm,c,e,n,p in BASE.PRIMARY_RE.findall(text):
        if int(mm)==0 and int(n)==16 and int(e,16)!=0xffff:
            out.append({"camx":int(c),"edge":int(e,16),"count":16,"payload":p.upper()})
    return out

def analyze(log0:str,log8:str,log16:str,log24:str,oracle_log:str,
            dump0:Path,dump8:Path,dump16:Path,dump24:Path)->dict:
    # Re-run the exact accepted +8 analyzer without asking the current +16/+24
    # experiment to satisfy the old capacity-stop expectations.
    fake16=(
        "URWS_LIMIT margin=16 required_extra_columns=2 "
        "stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity\n"
    )
    fake24=(
        "URWS_LIMIT margin=24 required_extra_columns=3 "
        "stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity\n"
    )
    plus8=BASE.analyze(
        {0:log0,8:log8,16:fake16,24:fake24},
        {0:dump0,8:dump8,16:dump0,24:dump0},
    )

    p8=[
        {"camx":int(c),"edge":int(e,16),"count":int(n),"payload":p.upper()}
        for c,e,n,p in BASE.PREP_RE.findall(log8)
    ]
    p16=rows(PREP16_RE,log16)
    shadow=rows(SHADOW16_RE,log16)
    primary16=[
        {"camx":int(c),"edge":int(e,16),"count":int(n),"payload":p.upper()}
        for mm,c,e,n,p in BASE.PRIMARY_RE.findall(log16)
        if int(mm)==16 and int(n)==16 and int(e,16)!=0xffff
    ]
    oracle=stock_primary(oracle_log)
    control=stock_primary(log0)
    stock_deltas={(b["edge"]-a["edge"])&0xffff for a,b in zip(control,control[1:])}|{1}

    primary_by_cam={r["camx"]:r for r in primary16}
    paired=[]
    bad_pairs=[]
    oracle_exact=0
    oracle_examples=[]
    for first,second in zip(p16,shadow):
        base=primary_by_cam.get(first["camx"])
        if base is None or second["camx"]!=first["camx"]:
            bad_pairs.append({"reason":"missing-primary-or-camera-mismatch","first":first,"second":second})
            continue
        d1=(first["edge"]-base["edge"])&0xffff
        d2=(second["edge"]-first["edge"])&0xffff
        ok1=BASE._ring_adjacent(base["edge"],first["edge"]) and d1 in stock_deltas
        ok2=BASE._ring_adjacent(first["edge"],second["edge"]) and d2 in stock_deltas
        item={"camx":first["camx"],"primary_edge":base["edge"],
              "first_edge":first["edge"],"second_edge":second["edge"],
              "first_delta":d1,"second_delta":d2,"first_ok":ok1,"second_ok":ok2}
        paired.append(item)
        if not (ok1 and ok2):
            bad_pairs.append(item)

        exact=[
            r for r in oracle
            if r["edge"]==second["edge"] and r["payload"]==second["payload"]
            and r["camx"]>second["camx"] and 1<=r["camx"]-second["camx"]<=24
        ]
        if exact:
            best=min(exact,key=lambda r:r["camx"]-second["camx"])
            oracle_exact+=1
            if len(oracle_examples)<40:
                oracle_examples.append({
                    "plus16_camx":second["camx"],"stock_camx":best["camx"],
                    "camera_x_advance":best["camx"]-second["camx"],
                    "edge":second["edge"],"payload":second["payload"],
                })

    states={0:BASE.read_words(dump0),8:BASE.read_words(dump8),
            16:BASE.read_words(dump16),24:BASE.read_words(dump24)}
    protected16={
        k:{"control":states[0][k],"margin_16":states[16][k]}
        for k in states[0] if states[0][k]!=states[16][k]
    }
    clean=[int(x) for x in CLEAN_RE.findall(log16)]
    terminal_pending=len(p16)==len(clean)+1
    cleanup_ok=(
        len(p16)>0 and (len(p16)==len(clean) or terminal_pending)
        and all(x==1 for x in clean)
    )
    plus8_signature=[(r["camx"],r["edge"],r["count"],r["payload"]) for r in p8]
    plus16_signature=[(r["camx"],r["edge"],r["count"],r["payload"]) for r in p16]

    checks={
        "accepted_plus8_unchanged":plus8["accepted"],
        "margin16_first_column_exactly_matches_plus8_path":plus16_signature==plus8_signature,
        "margin16_two_columns_for_every_preparation":len(p16)>0 and len(shadow)==len(p16),
        "margin16_no_provider_miss":not STOP_RE.findall(log16),
        "margin16_all_counts_16":all(r["count"]==16 for r in p16+shadow),
        "margin16_both_ring_steps_adjacent_and_stock_compatible":len(paired)==len(p16) and not bad_pairs,
        "margin16_every_shadow_is_exact_later_stock":oracle_exact==len(shadow) and len(shadow)>0,
        "margin16_cleanup_lifecycle":cleanup_ok,
        "margin16_protected_state_equal":not protected16,
        "margin24_stops_at_bounded_host_capacity":(
            bool(LIMIT24_RE.search(log24))
            and not rows(PREP16_RE,log24)
            and not rows(SHADOW16_RE,log24)
        ),
    }
    return {
        "schema_version":1,
        "architecture":{
            "guest_first_extra_column":"accepted PR #228 secondary lane",
            "host_second_extra_column":"host-owned WideStrip provider",
            "prototype_provider":"independent later-stock oracle",
            "synthetic_guest_descriptor_lanes":0,
            "production_provider_status":"open; course/resource random-access materializer is next",
        },
        "counts":{
            "plus8_prepare_events":len(p8),
            "plus16_first_column_events":len(p16),
            "plus16_shadow_events":len(shadow),
            "plus16_oracle_exact_matches":oracle_exact,
            "plus16_cleanup_events":len(clean),
            "plus16_comparable_pairs":len(paired),
        },
        "provider_misses":STOP_RE.findall(log16),
        "protected_state_differences":protected16,
        "pair_examples":paired[:40],
        "oracle_match_examples":oracle_examples,
        "checks":checks,
        "accepted":all(checks.values()),
    }

def render(r:dict)->str:
    c=r["checks"]; n=r["counts"]
    return "\n".join([
        "# +16 Widescreen host-capacity acceptance","",
        "The accepted +8 guest path supplies column +1 unchanged. Column +2 is "
        "retained only in host-owned presentation storage and, for this controlled "
        "prototype, is supplied by an independent later-stock oracle.","",
        f"- accepted +8 unchanged: **{c['accepted_plus8_unchanged']}**",
        f"- +16 first-column events: **{n['plus16_first_column_events']}**",
        f"- +16 host-shadow events: **{n['plus16_shadow_events']}**",
        f"- exact later-stock shadow matches: **{n['plus16_oracle_exact_matches']}**",
        f"- two columns for every preparation: **{c['margin16_two_columns_for_every_preparation']}**",
        f"- both ring steps adjacent / stock-compatible: **{c['margin16_both_ring_steps_adjacent_and_stock_compatible']}**",
        f"- +16 protected state equal: **{c['margin16_protected_state_equal']}**",
        f"- deterministic cleanup: **{c['margin16_cleanup_lifecycle']}**",
        f"- provider misses: **{r['provider_misses']}**","",
        "This proves the capacity/ownership seam only. The oracle is deliberately "
        "not a production content generator; the next producer should be the "
        "course/resource random-access presentation materializer.","",
        f"Overall accepted: **{r['accepted']}**",""
    ])

def main()->int:
    ap=argparse.ArgumentParser()
    for m in (0,8,16,24):
        ap.add_argument(f"--log-{m}",type=Path,required=True)
        ap.add_argument(f"--dump-{m}",type=Path,required=True)
    ap.add_argument("--oracle-log",type=Path,required=True)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    a=ap.parse_args()
    r=analyze(
        a.log_0.read_text(encoding="utf-8",errors="replace"),
        a.log_8.read_text(encoding="utf-8",errors="replace"),
        a.log_16.read_text(encoding="utf-8",errors="replace"),
        a.log_24.read_text(encoding="utf-8",errors="replace"),
        a.oracle_log.read_text(encoding="utf-8",errors="replace"),
        a.dump_0,a.dump_8,a.dump_16,a.dump_24,
    )
    md=render(r)
    if a.json_out:
        a.json_out.parent.mkdir(parents=True,exist_ok=True)
        a.json_out.write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8")
    if a.md_out:
        a.md_out.parent.mkdir(parents=True,exist_ok=True)
        a.md_out.write_text(md,encoding="utf-8")
    print(md,end="")
    return 0 if r["accepted"] else 2

if __name__=="__main__":
    raise SystemExit(main())
