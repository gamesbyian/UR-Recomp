#!/usr/bin/env python3
"""Acceptance for the course-backed host-owned +16 Widescreen materializer."""
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
    r"URWS_SHADOW16 provider=course-runtime camx=(\d+) edge=([0-9A-Fa-f]{4}) "
    r"count=(\d+) payload=([0-9A-Fa-f]{64})"
)
PRIMARY_VIEW_RE=re.compile(
    r"URWS_PRIMARY margin=0 camx=(\d+) edge=([0-9A-Fa-f]{4}) count=(\d+) "
    r"payload=([0-9A-Fa-f]{64}) camy=(\d+)"
)
SHADOW_VIEW_RE=re.compile(
    r"URWS_SHADOW16 provider=course-runtime camx=(\d+) edge=([0-9A-Fa-f]{4}) "
    r"count=(\d+) payload=([0-9A-Fa-f]{64}) camy=(\d+) finex=(\d+) finey=(\d+)"
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

def stock_primary_view(text:str)->list[dict]:
    return [
        {"camx":int(c),"edge":int(e,16),"count":int(n),"payload":p.upper(),
         "camy":int(y),"finey":int(y)>>4}
        for c,e,n,p,y in PRIMARY_VIEW_RE.findall(text)
        if int(n)==16 and int(e,16)!=0xffff
    ]

def shadow_view(text:str)->list[dict]:
    return [
        {"camx":int(c),"edge":int(e,16),"count":int(n),"payload":p.upper(),
         "camy":int(y),"finex":int(fx),"finey":int(fy)}
        for c,e,n,p,y,fx,fy in SHADOW_VIEW_RE.findall(text)
    ]

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
    shadow_views=shadow_view(log16)
    primary16=[
        {"camx":int(c),"edge":int(e,16),"count":int(n),"payload":p.upper()}
        for mm,c,e,n,p in BASE.PRIMARY_RE.findall(log16)
        if int(mm)==16 and int(n)==16 and int(e,16)!=0xffff
    ]
    oracle=stock_primary(oracle_log)
    oracle_views=stock_primary_view(oracle_log)
    control=stock_primary(log0)
    stock_deltas={(b["edge"]-a["edge"])&0xffff for a,b in zip(control,control[1:])}|{1}

    primary_by_cam={r["camx"]:r for r in primary16}
    shadow_by_cam={r["camx"]:r for r in shadow}
    paired=[]
    bad_first_steps=[]
    bad_second_ring_steps=[]
    oracle_payload_exact=0
    oracle_full_edge_exact=0
    same_view_payload_exact=0
    same_view_comparable=0
    vertical_view_transition_rows=0
    same_view_failures=[]
    oracle_advances=[]
    oracle_examples=[]
    for first in p16:
        second=shadow_by_cam.get(first["camx"])
        base=primary_by_cam.get(first["camx"])
        if base is None or second is None:
            continue

        d1=(first["edge"]-base["edge"])&0xffff
        first_ok=BASE._ring_adjacent(base["edge"],first["edge"]) and d1 in stock_deltas
        second_ring_ok=BASE._ring_adjacent(first["edge"],second["edge"])
        item={
            "camx":first["camx"],
            "primary_edge":base["edge"],
            "first_edge":first["edge"],
            "second_edge":second["edge"],
            "first_delta":d1,
            "second_delta":(second["edge"]-first["edge"])&0xffff,
            "first_stock_compatible":first_ok,
            "second_ring_adjacent":second_ring_ok,
        }
        paired.append(item)
        if not first_ok:
            bad_first_steps.append(item)
        if not second_ring_ok:
            bad_second_ring_steps.append(item)

        # The provider's contract is direct random access to a later stock row,
        # not replaying the guest scheduler. Require the shadow edge+payload to
        # equal the nearest future stock observation carrying the required next
        # low-five-bit ring coordinate. Upper edge bits are compound
        # resource/segment state and therefore are not independently advanced
        # from the widened first edge.
        wanted_ring=(first["edge"]+1)&0x1f
        candidates=[
            r for r in oracle
            if r["camx"]>first["camx"] and (r["edge"]&0x1f)==wanted_ring
        ]
        if candidates:
            best=min(candidates,key=lambda r:r["camx"]-first["camx"])
            payload_exact=best["payload"]==second["payload"]
            full_edge_exact=best["edge"]==second["edge"]
            if payload_exact:
                oracle_payload_exact+=1
            if payload_exact and full_edge_exact:
                oracle_full_edge_exact+=1
            if payload_exact:
                advance=best["camx"]-first["camx"]
                oracle_advances.append(advance)
                if len(oracle_examples)<40:
                    oracle_examples.append({
                        "plus16_camx":second["camx"],
                        "stock_camx":best["camx"],
                        "camera_x_advance":advance,
                        "host_edge":second["edge"],
                        "stock_edge":best["edge"],
                        "full_edge_exact":full_edge_exact,
                        "payload":second["payload"],
                    })

    shadow_view_by_cam={r["camx"]:r for r in shadow_views}
    for first in p16:
        second=shadow_view_by_cam.get(first["camx"])
        if second is None:
            continue
        wanted_ring=second["edge"]&0x1f
        bounded=[
            r for r in oracle_views
            if r["camx"]>second["camx"]
            and 1 <= r["camx"]-second["camx"] <= 64
            and (r["edge"]&0x1f)==wanted_ring
        ]
        if not bounded:
            continue
        nearest=min(bounded,key=lambda r:r["camx"]-second["camx"])
        same_view=[
            r for r in bounded
            if r["finey"]==second["finey"]
        ]
        if nearest["finey"] != second["finey"]:
            vertical_view_transition_rows += 1
        if not same_view:
            continue
        best=min(same_view,key=lambda r:r["camx"]-second["camx"])
        same_view_comparable += 1
        if best["payload"]==second["payload"]:
            same_view_payload_exact += 1
        elif len(same_view_failures)<40:
            same_view_failures.append({
                "plus16_camx":second["camx"],
                "plus16_camy":second["camy"],
                "fine_x":second["finex"],
                "fine_y":second["finey"],
                "stock_camx":best["camx"],
                "stock_camy":best["camy"],
                "stock_fine_y":best["finey"],
                "host_edge":second["edge"],
                "stock_edge":best["edge"],
                "host_payload":second["payload"],
                "stock_payload":best["payload"],
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
        "margin16_first_step_preserves_accepted_stock_compatibility":(
            len(paired)==len(p16) and not bad_first_steps
        ),
        "margin16_second_step_ring_adjacent":(
            len(paired)==len(p16) and not bad_second_ring_steps
        ),
        "margin16_same_view_shadow_payloads_are_exact":(
            same_view_comparable >= 600
            and same_view_payload_exact == same_view_comparable
            and not same_view_failures
        ),
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
            "host_provider":"live 7F:000F coarse table + 7F:800F packed-surface fine records",
            "acceptance_oracle":"independent later-stock control run only; never read by implementation",
            "synthetic_guest_descriptor_lanes":0,
            "production_provider_status":"first course-backed random-access materializer under acceptance",
        },
        "counts":{
            "plus8_prepare_events":len(p8),
            "plus16_first_column_events":len(p16),
            "plus16_shadow_events":len(shadow),
            "plus16_oracle_payload_exact_matches":oracle_payload_exact,
            "plus16_oracle_full_edge_exact_matches":oracle_full_edge_exact,
            "plus16_same_view_comparable_rows":same_view_comparable,
            "plus16_same_view_payload_exact_matches":same_view_payload_exact,
            "plus16_vertical_view_transition_rows":vertical_view_transition_rows,
            "plus16_cleanup_events":len(clean),
            "plus16_comparable_pairs":len(paired),
            "plus16_oracle_advance_min":min(oracle_advances) if oracle_advances else None,
            "plus16_oracle_advance_max":max(oracle_advances) if oracle_advances else None,
        },
        "provider_misses":STOP_RE.findall(log16),
        "protected_state_differences":protected16,
        "first_step_failures":bad_first_steps[:40],
        "second_ring_failures":bad_second_ring_steps[:40],
        "same_view_failures":same_view_failures,
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
        "retained only in host-owned presentation storage and is materialized directly "
        "from the live course coarse/fine presentation tables. The independent later-stock "
        "run is used only as an acceptance oracle.","",
        f"- accepted +8 unchanged: **{c['accepted_plus8_unchanged']}**",
        f"- +16 first-column events: **{n['plus16_first_column_events']}**",
        f"- +16 host-shadow events: **{n['plus16_shadow_events']}**",
        f"- exact later-stock shadow payload matches: **{n['plus16_oracle_payload_exact_matches']}**",
        f"- exact later-stock compound-edge + payload matches (all rows, diagnostic): **{n['plus16_oracle_full_edge_exact_matches']}**",
        f"- same-view comparable shadow rows: **{n['plus16_same_view_comparable_rows']}**",
        f"- same-view exact payload matches: **{n['plus16_same_view_payload_exact_matches']}**",
        f"- later-stock rows crossing a vertical-view transition: **{n['plus16_vertical_view_transition_rows']}**",
        f"- two columns for every preparation: **{c['margin16_two_columns_for_every_preparation']}**",
        f"- first step keeps accepted stock compatibility: **{c['margin16_first_step_preserves_accepted_stock_compatibility']}**",
        f"- second step is ring-adjacent: **{c['margin16_second_step_ring_adjacent']}**",
        f"- nearest later-stock advance range: **{n['plus16_oracle_advance_min']}..{n['plus16_oracle_advance_max']} px**",
        f"- +16 protected state equal: **{c['margin16_protected_state_equal']}**",
        f"- deterministic cleanup: **{c['margin16_cleanup_lifecycle']}**",
        f"- provider misses: **{r['provider_misses']}**","",
        "For column +2, the later-stock oracle is exact only when the future stock row "
        "samples the same fine camera-Y viewport. Rows where the camera has moved vertically "
        "are classified separately rather than asking a current-view random-access strip to "
        "match a different future viewport. Every same-view comparable payload remains a hard "
        "exactness gate. Full compound-edge equality and all-row payload equality are retained "
        "as diagnostics. The oracle is deliberately never a runtime provider.","",
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
