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
    r"pc=(?P<pc>[0-9A-Fa-f]{6}) camx=(?P<camx>\d+) camy=(?P<camy>\d+) camdx=(?P<camdx>-?\d+) camdy=(?P<camdy>-?\d+) "
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
            "margin","frame","v","cycles","camx","camy","camdx","camdy","px","py","xs","ys","pitch",
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
    out = []
    for r in rows:
        if r["site"] != "after_build":
            continue
        for d in r["ready"]:
            if d["size"] == 0x20 and d["vmain"] == 0x81:
                out.append({
                    "frame":r["frame"],
                    "camera_x":r["camx"],
                    "edge_x":r["edgex"],
                    "gameplay":r["gameplay"],
                    "descriptor":d,
                })
    return out

def consumed_same_frame(rows: list[dict]) -> set[tuple]:
    seen = set()
    for r in rows:
        if r["site"] != "before_consume":
            continue
        for d in r["ready"]:
            seen.add((r["frame"], signature(d)))
    return seen

def analyze_rows(control_rows: list[dict], plus8_rows: list[dict]) -> tuple[dict, list[dict]]:
    c_events = build_events(control_rows)
    w_events = build_events(plus8_rows)
    c_cons = consumed_same_frame(control_rows)
    w_cons = consumed_same_frame(plus8_rows)

    control_by_sig = defaultdict(list)
    for event in c_events:
        control_by_sig[signature(event["descriptor"])].append(event)

    matches = []
    for widened in w_events:
        sig = signature(widened["descriptor"])
        future = [
            control for control in control_by_sig.get(sig, [])
            if control["camera_x"] > widened["camera_x"]
        ]
        if not future:
            continue
        control = min(
            future,
            key=lambda row:(row["camera_x"] - widened["camera_x"], row["frame"]),
        )
        delta = control["camera_x"] - widened["camera_x"]
        if 1 <= delta <= 16:
            matches.append({
                "plus8":widened,
                "control_future":control,
                "camera_x_advance":delta,
                "plus8_same_frame_consumed":(widened["frame"], sig) in w_cons,
                "control_same_frame_consumed":(control["frame"], sig) in c_cons,
            })

    c_by_frame = {r["frame"]:r for r in control_rows if r["site"] == "after_build"}
    w_by_frame = {r["frame"]:r for r in plus8_rows if r["site"] == "after_build"}
    common = sorted(set(c_by_frame) & set(w_by_frame))
    gameplay_diffs = []
    camera_restore_diffs = []
    for frame in common:
        control, widened = c_by_frame[frame], w_by_frame[frame]
        if control["gameplay"] != widened["gameplay"]:
            gameplay_diffs.append({
                "frame":frame,
                "control":control["gameplay"],
                "plus8":widened["gameplay"],
            })
        if (
            control["camx"], control["camy"], control["camdx"], control["camdy"]
        ) != (
            widened["camx"], widened["camy"], widened["camdx"], widened["camdy"]
        ):
            camera_restore_diffs.append({
                "frame":frame,
                "control":[control["camx"], control["camy"], control["camdx"], control["camdy"]],
                "plus8":[widened["camx"], widened["camy"], widened["camdx"], widened["camdy"]],
            })

    success_matches = [
        match for match in matches
        if match["plus8_same_frame_consumed"]
        and match["control_same_frame_consumed"]
        and match["plus8"]["descriptor"]["payload_hex"]
        and match["plus8"]["descriptor"]["payload_hex"]
            == match["control_future"]["descriptor"]["payload_hex"]
    ]

    report = {
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
    report["success"] = all([
        report["additional_strip_prepared"],
        report["expected_descriptor_consumed_by_nmi"],
        report["widened_edge_matches_future_stock_data"],
        report["authoritative_gameplay_state_equal"],
        report["camera_state_restored"],
    ])
    return report, success_matches

def render_markdown(report: dict, success_matches: list[dict]) -> str:
    lines = [
        "# Widescreen +8 strip-scheduling experiment","",
        f"- additional/future strip observed early: **{report['additional_strip_prepared']}**",
        f"- matching descriptor consumed by NMI in same frame: **{report['expected_descriptor_consumed_by_nmi']}**",
        f"- +8 payload equals later stock payload: **{report['widened_edge_matches_future_stock_data']}**",
        f"- authoritative gameplay sample equal on {report['gameplay_common_frames']} common frames: **{report['authoritative_gameplay_state_equal']}**",
        f"- camera restored outside preparation window: **{report['camera_state_restored']}**",
        f"- qualifying future-stock matches: **{len(success_matches)}**","",
    ]
    if success_matches:
        lines += [
            "| +8 frame | +8 camera X | stock frame | stock camera X | advance px | VRAM | source | bytes |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for match in success_matches[:40]:
            widened = match["plus8"]
            control = match["control_future"]
            desc = widened["descriptor"]
            lines.append(
                f"| {widened['frame']} | {widened['camera_x']} | {control['frame']} | "
                f"{control['camera_x']} | {match['camera_x_advance']} | {desc['vram']:04X} | "
                f"{desc['source']:04X} | {desc['size']} |"
            )
    if report["gameplay_differences"]:
        lines += [
            "",
            "First gameplay difference:",
            json.dumps(report["gameplay_differences"][0], indent=2),
        ]
    return "\n".join(lines) + "\n"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("control", type=Path)
    ap.add_argument("plus8", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()

    report, success_matches = analyze_rows(parse(args.control), parse(args.plus8))
    payload = json.dumps(report, indent=2) + "\n"
    markdown = render_markdown(report, success_matches)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(markdown, encoding="utf-8")
    print(markdown, end="")
    return 0 if report["success"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
