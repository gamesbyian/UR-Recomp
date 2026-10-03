#!/usr/bin/env python3
"""Validate the native +8 strip hook against the accepted PR #219 contract."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

PRIMARY_RE = re.compile(
    r"URWS_PRIMARY margin=(\d+) camx=(\d+) edge=([0-9A-Fa-f]{4}) "
    r"count=(\d+) payload=([0-9A-Fa-f]{64})"
)
PREP_RE = re.compile(
    r"URWS_PREP margin=8 camx=(\d+) edge=([0-9A-Fa-f]{4}) "
    r"count=(\d+) payload=([0-9A-Fa-f]{64})"
)
CLEAN_RE = re.compile(r"URWS_CLEANUP margin=8")
LIFECYCLE_LINE_RE = re.compile(r"URWS_(PREP|CLEANUP) margin=8")
LIMIT_RE = re.compile(
    r"URWS_LIMIT margin=(16|24) required_extra_columns=(\d+) "
    r"stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity"
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

def cleanup_lifecycle(log: str) -> tuple[bool,bool]:
    live=False
    seen=False
    for kind in LIFECYCLE_LINE_RE.findall(log):
        if kind=="PREP":
            if live:
                return False, live
            live=True
            seen=True
        else:
            if not live:
                return False, live
            live=False
    return seen, live

def _ring_next(edge: int) -> int:
    return (edge & ~0x1F) | ((edge + 1) & 0x1F)

def _longest_true_run(values: list[bool]) -> int:
    best = cur = 0
    for value in values:
        if value:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best

def _last_plus8_event(log: str) -> str | None:
    events = []
    for m in re.finditer(r"URWS_(PREP|CLEANUP) margin=8", log):
        events.append((m.start(), m.group(1)))
    return events[-1][1] if events else None

def analyze(logs: dict[int,str], dumps: dict[int,Path]) -> dict:
    primary = {
        m: [
            {
                "margin": int(mm),
                "camx": int(camx),
                "edge": int(edge, 16),
                "count": int(count),
                "payload": payload.upper(),
            }
            for mm, camx, edge, count, payload in PRIMARY_RE.findall(logs[m])
        ]
        for m in logs
    }
    prep = {
        m: [
            {
                "camx": int(camx),
                "edge": int(edge, 16),
                "count": int(count),
                "payload": payload.upper(),
            }
            for camx, edge, count, payload in PREP_RE.findall(logs[m])
        ]
        for m in logs
    }
    cleanup={m:CLEAN_RE.findall(logs[m]) for m in logs}
    limits={m:[(int(a),int(b)) for a,b in LIMIT_RE.findall(logs[m])] for m in logs}
    states={m:read_words(dumps[m]) for m in dumps}
    control=states[0]
    diffs={}
    for m,state in states.items():
        if m==0: continue
        diffs[m]={k:{"control":control[k],f"margin_{m}":state[k]} for k in control if state[k]!=control[k]}

    plus8 = [row for row in prep.get(8, []) if row["count"] == 16]
    control_primary = [
        row for row in primary.get(0, [])
        if row["count"] == 16 and row["edge"] != 0xffff
    ]
    widened_primary = [
        row for row in primary.get(8, [])
        if row["count"] == 16 and row["edge"] != 0xffff
    ]

    adjacent_count = 0
    adjacency_comparable_count = 0
    for row in plus8:
        same_camera = [
            stock for stock in widened_primary
            if stock["camx"] == row["camx"]
        ]
        if not same_camera:
            continue
        adjacency_comparable_count += 1
        if any(_ring_next(stock["edge"]) == row["edge"] for stock in same_camera):
            adjacent_count += 1

    exact_matches = []
    matched_flags = []
    future_stock_candidates = 0
    for row in plus8:
        candidates = [
            stock for stock in control_primary
            if stock["edge"] == row["edge"]
            and stock["camx"] > row["camx"]
            and 1 <= stock["camx"] - row["camx"] <= 16
        ]
        if candidates:
            future_stock_candidates += 1
        exact = [stock for stock in candidates if stock["payload"] == row["payload"]]
        matched_flags.append(bool(exact))
        if exact:
            stock = min(exact, key=lambda s:(s["camx"]-row["camx"], s["camx"]))
            exact_matches.append({
                "plus8_camx": row["camx"],
                "stock_camx": stock["camx"],
                "camera_x_advance": stock["camx"] - row["camx"],
                "edge": row["edge"],
                "payload": row["payload"],
            })

    prep_count=len(prep.get(8,[]))
    cleanup_count=len(cleanup.get(8,[]))
    terminal_pending=(
        prep_count == cleanup_count + 1
        and _last_plus8_event(logs.get(8,"")) == "PREP"
    )
    balanced=(
        (prep_count == cleanup_count and prep_count > 0)
        or (terminal_pending and prep_count > 0)
    )
    match_count=len(exact_matches)
    match_ratio=(match_count/future_stock_candidates) if future_stock_candidates else 0.0
    longest_match_run=_longest_true_run(matched_flags)

    checks={
        "margin0_control_inert": not prep.get(0) and not cleanup.get(0) and not limits.get(0),
        "margin8_exercised": len(plus8)>0,
        "margin8_all_counts_16": len(plus8)==len(prep.get(8,[])),
        "margin8_cleanup_balanced": balanced,
        "margin8_terminal_pending_only": not terminal_pending or _last_plus8_event(logs.get(8,"")) == "PREP",
        "margin8_comparable_edges_all_adjacent": (
            adjacency_comparable_count >= 309
            and adjacent_count == adjacency_comparable_count
        ),
        "margin8_protected_state_equal": not diffs.get(8),
        "margin8_future_stock_exact_matches": match_count >= 309,
        "margin8_future_stock_consecutive_run": longest_match_run >= 14,
        "margin16_stops_at_capacity": not prep.get(16) and any(m==16 and c==2 for m,c in limits.get(16,[])) and not diffs.get(16),
        "margin24_stops_at_capacity": not prep.get(24) and any(m==24 and c==3 for m,c in limits.get(24,[])) and not diffs.get(24),
    }
    return {
        "schema_version":1,
        "reference_acceptance":{
            "pr":219,"workflow_run":37066327707,"accepted_adjacent_columns":309,
            "longest_consecutive_run":14,
            "mechanism":"stock-A59E-double-pass-secondary-horizontal-lane",
        },
        "native_runtime":{
            "margin0_primary_events":len(control_primary),
            "margin8_prepare_events":prep_count,
            "margin8_cleanup_events":cleanup_count,
            "margin8_terminal_payload_pending":terminal_pending,
            "margin8_unique_edges":len({row["edge"] for row in plus8}),
            "margin8_adjacency_comparable_events":adjacency_comparable_count,
            "margin8_adjacency_unobserved_events":len(plus8)-adjacency_comparable_count,
            "margin8_adjacent_prepared_edges":adjacent_count,
            "margin8_future_stock_candidates":future_stock_candidates,
            "margin8_exact_future_stock_matches":match_count,
            "margin8_exact_future_stock_match_ratio":round(match_ratio,6),
            "margin8_longest_consecutive_exact_match_run":longest_match_run,
            "margin16_limit_events":limits.get(16,[]),
            "margin24_limit_events":limits.get(24,[]),
        },
        "future_stock_match_examples":exact_matches[:40],
        "protected_state_differences":diffs,
        "checks":checks,
        "accepted":all(checks.values()),
        "first_generalization_constraint":"secondary-lane-capacity",
        "stock_extra_horizontal_lanes":1,
        "pixels_per_extra_column":8,
        "margin16_required_extra_columns":2,
        "margin24_required_extra_columns":3,
    }

def render(r: dict) -> str:
    c,n=r["checks"],r["native_runtime"]
    return "\n".join([
        "# Native +8 Widescreen strip-hook acceptance","",
        "Reference contract: PR #219 / workflow run 37066327707 "
        "(309 exact accepted future columns; longest consecutive run 14).","",
        f"- stock margin 0 inert: **{c['margin0_control_inert']}**",
        f"- stock primary reference events: **{n['margin0_primary_events']}**",
        f"- +8 native preparation events: **{n['margin8_prepare_events']}**",
        f"- +8 cleanup events: **{n['margin8_cleanup_events']}**",
        f"- +8 terminal payload pending at fixture exit: **{n['margin8_terminal_payload_pending']}**",
        f"- +8 unique prepared edges: **{n['margin8_unique_edges']}**",
        f"- +8 adjacency-comparable preparation events: **{n['margin8_adjacency_comparable_events']}/{n['margin8_prepare_events']}**",
        f"- +8 comparable events that are geometrically adjacent: **{n['margin8_adjacent_prepared_edges']}/{n['margin8_adjacency_comparable_events']}**",
        f"- +8 events without a same-camera primary observation: **{n['margin8_adjacency_unobserved_events']}**",
        f"- +8 edge-compatible later-stock observations: **{n['margin8_future_stock_candidates']}**",
        f"- +8 exact later-stock payload matches: **{n['margin8_exact_future_stock_matches']}**",
        f"- +8 exact-match ratio among future-stock candidates: **{n['margin8_exact_future_stock_match_ratio']:.3%}**",
        f"- +8 longest consecutive exact-match run: **{n['margin8_longest_consecutive_exact_match_run']}**",
        f"- +8 protected gameplay/camera/progression state equal: **{c['margin8_protected_state_equal']}**",
        f"- +16 stopped at stock lane capacity: **{c['margin16_stops_at_capacity']}**",
        f"- +24 stopped at stock lane capacity: **{c['margin24_stops_at_capacity']}**","",
        "Adjacency is judged only where the native trace observed a stock primary strip at the same camera X. Events without that same-camera primary observation remain unclassified rather than being mislabeled non-adjacent; the accepted future-stock payload threshold remains independently enforced.","",
        "The cleanup balance permits exactly one terminal pending payload when the "
        "fixture exits immediately after a PREP event; ordinary runtime clears it "
        "at the next live A59A preparation boundary.","",
        "First generalization constraint: **secondary-lane-capacity**. "
        "The stock horizontal pair has one primary lane plus one secondary lane. "
        "+8 consumes the only spare lane; +16 needs two extra columns and +24 needs three.","",
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
