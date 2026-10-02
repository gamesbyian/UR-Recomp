#!/usr/bin/env python3
"""Compare stock and +8 preparation-only strip scheduling traces."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

RX = re.compile(
    r"WSDMA margin=(?P<margin>\d+) frame=(?P<frame>\d+) v=(?P<v>\d+) cycles=(?P<cycles>-?\d+) "
    r"pc=(?P<pc>[0-9A-Fa-f]{6}) camx=(?P<camx>\d+) camy=(?P<camy>\d+) "
    r"px=(?P<px>\d+) py=(?P<py>\d+) xs=(?P<xs>-?\d+) ys=(?P<ys>-?\d+) pitch=(?P<pitch>\d+) "
    r"contact=(?P<contact>\d+) laps=(?P<laps>\d+) checkpoint=(?P<checkpoint>\d+) "
    r"finish=(?P<finish>\d+) edgex=(?P<edgex>\d+) edgey=(?P<edgey>\d+) desc=(?P<desc>.*)$"
)

def parse_descs(raw: str) -> list[dict]:
    out = []
    for item in raw.split(","):
        parts = item.split(":")
        if len(parts) != 7:
            continue
        slot, ready, dest, src, size, vmain, payload = parts
        out.append({
            "slot": int(slot),
            "ready": int(ready),
            "vram": int(dest, 16),
            "source": int(src, 16),
            "size": int(size, 16),
            "vmain": int(vmain, 16),
            "payload_hex": payload.upper(),
        })
    return out

def parse(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = RX.search(line)
        if not m:
            continue
        g = m.groupdict()
        row = {k:int(g[k]) for k in (
            "margin","frame","v","cycles","camx","camy","px","py","xs","ys","pitch",
            "contact","laps","checkpoint","finish","edgex","edgey"
        )}
        row["pc"] = int(g["pc"], 16)
        row["site"] = "after_build" if row["pc"] == 0x81A59D else "before_consume"
        row["descriptors"] = parse_descs(g["desc"])
        row["ready"] = [d for d in row["descriptors"] if d["ready"]]
        row["gameplay"] = {k:row[k] for k in (
            "px","py","xs","ys","pitch","contact","laps","checkpoint","finish"
        )}
        rows.append(row)
    if not rows:
        raise SystemExit(f"no WSDMA rows in {path}")
    return rows

def signature(d: dict) -> tuple:
    return (d["vram"], d["size"], d["vmain"], d["payload_hex"])

def build_events(rows: list[dict]) -> list[dict]:
    out=[]
    for r in rows:
        if r["site"] != "after_build":
            continue
        for d in r["ready"]:
            if d["size"] == 0x20 and d["vmain"] == 0x81:
                out.append({
                    "frame":r["frame"],"camera_x":r["camx"],"edge_x":r["edgex"],
                    "gameplay":r["gameplay"],"descriptor":d,
                })
    return out

def consumed_same_frame(rows: list[dict]) -> set[tuple]:
    seen=set()
    for r in rows:
        if r["site"] != "before_consume":
            continue
        for d in r["ready"]:
            seen.add((r["frame"], signature(d)))
    return seen

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("control",type=Path)
    ap.add_argument("plus8",type=Path)
    ap.add_argument("--json-out",type=Path)
    ap.add_argument("--md-out",type=Path)
    args=ap.parse_args()

    control_rows=parse(args.control)
    plus8_rows=parse(args.plus8)
    c_events=build_events(control_rows)
    w_events=build_events(plus8_rows)
    c_cons=consumed_same_frame(control_rows)
    w_cons=consumed_same_frame(plus8_rows)

    control_by_sig=defaultdict(list)
    for e in c_events:
        control_by_sig[signature(e["descriptor"])].append(e)

    matches=[]
    for w in w_events:
        sig=signature(w["descriptor"])
        future=[c for c in control_by_sig.get(sig,[]) if c["camera_x"] >= w["camera_x"]]
        if not future:
            continue
        c=min(future,key=lambda x:(x["camera_x"]-w["camera_x"],x["frame"]))
        delta=c["camera_x"]-w["camera_x"]
        if 1 <= delta <= 16:
            matches.append({
                "plus8":w,"control_future":c,"camera_x_advance":delta,
                "plus8_same_frame_consumed":(w["frame"],sig) in w_cons,
                "control_same_frame_consumed":(c["frame"],sig) in c_cons,
            })

    c_by_frame={r["frame"]:r for r in control_rows if r["site"]=="after_build"}
    w_by_frame={r["frame"]:r for r in plus8_rows if r["site"]=="after_build"}
    common=sorted(set(c_by_frame)&set(w_by_frame))
    gameplay_diffs=[]
    camera_restore_diffs=[]
    for f in common:
        c,w=c_by_frame[f],w_by_frame[f]
        if c["gameplay"] != w["gameplay"]:
            gameplay_diffs.append({"frame":f,"control":c["gameplay"],"plus8":w["gameplay"]})
        if (c["camx"],c["camy"]) != (w["camx"],w["camy"]):
            camera_restore_diffs.append({
                "frame":f,"control":[c["camx"],c["camy"]],"plus8":[w["camx"],w["camy"]]
            })

    success_matches=[
        m for m in matches
        if m["plus8_same_frame_consumed"] and m["control_same_frame_consumed"]
        and m["plus8"]["descriptor"]["payload_hex"]
        and m["plus8"]["descriptor"]["payload_hex"] == m["control_future"]["descriptor"]["payload_hex"]
    ]

    report={
        "schema_version":1,
        "control_horizontal_build_events":len(c_events),
        "plus8_horizontal_build_events":len(w_events),
        "future_stock_payload_matches":matches,
        "successful_future_stock_matches":len(success_matches),
        "gameplay_common_frames":len(common),
        "gameplay_differences":gameplay_diffs,
        "camera_restore_differences":camera_restore_diffs,
        "additional_strip_prepared":bool(success_matches),
        "expected_descriptor_consumed_by_nmi":bool(success_matches),
        "widened_edge_matches_future_stock_data":bool(success_matches),
        "authoritative_gameplay_state_equal":not gameplay_diffs and bool(common),
        "camera_state_restored":not camera_restore_diffs and bool(common),
    }
    report["success"]=all([
        report["additional_strip_prepared"],
        report["expected_descriptor_consumed_by_nmi"],
        report["widened_edge_matches_future_stock_data"],
        report["authoritative_gameplay_state_equal"],
        report["camera_state_restored"],
    ])

    lines=[
        "# Widescreen +8 strip-scheduling experiment","",
        f"- additional/future strip observed early: **{report['additional_strip_prepared']}**",
        f"- matching descriptor consumed by NMI in same frame: **{report['expected_descriptor_consumed_by_nmi']}**",
        f"- +8 payload equals later stock payload: **{report['widened_edge_matches_future_stock_data']}**",
        f"- authoritative gameplay sample equal on {len(common)} common frames: **{report['authoritative_gameplay_state_equal']}**",
        f"- camera restored outside preparation window: **{report['camera_state_restored']}**",
        f"- qualifying future-stock matches: **{len(success_matches)}**","",
    ]
    if success_matches:
        lines += ["| +8 frame | +8 camera X | stock frame | stock camera X | advance px | VRAM | source | bytes |",
                  "|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for m in success_matches[:40]:
            w=m["plus8"]; c=m["control_future"]; d=w["descriptor"]
            lines.append(
                f"| {w['frame']} | {w['camera_x']} | {c['frame']} | {c['camera_x']} | "
                f"{m['camera_x_advance']} | {d['vram']:04X} | {d['source']:04X} | {d['size']} |"
            )
    if gameplay_diffs:
        lines += ["","First gameplay difference:", json.dumps(gameplay_diffs[0],indent=2)]

    payload=json.dumps(report,indent=2)+"\n"
    md="\n".join(lines)+"\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(payload,encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True,exist_ok=True)
        args.md_out.write_text(md,encoding="utf-8")
    print(md,end="")
    return 0 if report["success"] else 2

if __name__=="__main__":
    raise SystemExit(main())
