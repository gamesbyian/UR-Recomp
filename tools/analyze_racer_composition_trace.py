#!/usr/bin/env python3
"""Analyze synchronized RaceRenderF0BB cache-composition traces."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from extract_racer_presentation_family import extract_frame, packed_word_source

LINE_RE = re.compile(
    r"RACERCOMP frame=(?P<frame>\d+) pc=83(?P<pc>[0-9A-F]{4}) "
    r"ids=(?P<ids>[0-9A-F,]+) sel=(?P<sel>[0-9A-F,]+) "
    r"pm=(?P<pm>[0-9A-F,]+) um=(?P<um>[0-9A-F,]+) "
    r"off=(?P<off>[0-9A-F,]+) stage=(?P<stage>.*)$"
)

ANCHORS = (1220, 1420, 1470, 1520, 1570, 1620)


def parse_hex_list(text: str) -> list[int]:
    return [int(x, 16) for x in text.split(",")]


def parse_stage(text: str) -> list[tuple[int, int, int]]:
    if not text:
        return []
    out = []
    for item in text.split(","):
        bank, src, dest = item.split(":")
        out.append((int(bank, 16), int(src, 16), int(dest, 16)))
    return out


def stream_sources(rom: bytes, fid: int) -> list[tuple[int, int]]:
    if fid == 0:
        return []
    frame = extract_frame(rom, fid)
    return [packed_word_source(int(p["word_hex"], 16)) for p in frame["pieces"]]


def analyze_event(rom: bytes, row: dict) -> dict:
    p1, p2, c1, c2 = row["ids"]
    offsets = row["offsets"]
    streams = {
        "p1_primary": stream_sources(rom, p1),
        "p2_primary": stream_sources(rom, p2),
        "p1_companion": stream_sources(rom, c1),
        "p2_companion": stream_sources(rom, c2),
    }
    cursor = {
        "p1_primary": max(0, (offsets[0] - 4) // 2),
        "p2_primary": max(0, (offsets[1] - 4) // 2),
        "p1_companion": max(0, (offsets[2] - 4) // 2),
        "p2_companion": max(0, (offsets[3] - 4) // 2),
    }
    cells = []
    mismatches = []
    stage = row["stage"]
    if len(stage) != 70:
        mismatches.append({"kind": "stage_length", "actual": len(stage), "expected": 70})

    for cell_index in range(min(70, len(stage))):
        r = cell_index // 14
        col = cell_index % 14
        x = 13 - col
        bit = 0x8000 >> col
        player = "p1" if (x & 0x08) else "p2"
        primary_name = f"{player}_primary"
        companion_name = f"{player}_companion"
        primary_occupied = bool(row["primary_masks"][r] & bit)
        union_occupied = bool(row["union_masks"][r] & bit)
        actual = stage[cell_index][:2]
        choice = "blank"
        predicted = (0x27, 0x8000)
        companion_occupied = False

        if union_occupied:
            if not primary_occupied:
                companion_occupied = True
            else:
                ci = cursor[companion_name]
                companion_next = streams[companion_name][ci] if ci < len(streams[companion_name]) else None
                if companion_next == actual:
                    companion_occupied = True

            if companion_occupied:
                if primary_occupied:
                    cursor[primary_name] += 1
                ci = cursor[companion_name]
                predicted = streams[companion_name][ci] if ci < len(streams[companion_name]) else None
                cursor[companion_name] += 1
                choice = companion_name
            elif primary_occupied:
                pi = cursor[primary_name]
                predicted = streams[primary_name][pi] if pi < len(streams[primary_name]) else None
                cursor[primary_name] += 1
                choice = primary_name
            else:
                predicted = None
        elif primary_occupied:
            # The live union mask is the post-loop OR of both streams, so this is impossible.
            predicted = None

        ok = predicted == actual
        if not ok:
            mismatches.append({
                "kind": "source",
                "cell": cell_index,
                "row": r,
                "column": col,
                "player": player,
                "choice": choice,
                "primary_occupied": primary_occupied,
                "union_occupied": union_occupied,
                "actual": None if actual is None else [f"0x{actual[0]:02X}", f"0x{actual[1]:04X}"],
                "predicted": None if predicted is None else [f"0x{predicted[0]:02X}", f"0x{predicted[1]:04X}"],
            })
        cells.append({
            "index": cell_index,
            "row": r,
            "column": col,
            "player": player,
            "primary_occupied": primary_occupied,
            "companion_occupied": companion_occupied,
            "choice": choice,
            "source_matches": ok,
            "destination": f"0x{stage[cell_index][2]:04X}",
        })

    return {
        **row,
        "cells": cells,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "final_cursors": cursor,
        "stream_lengths": {k: len(v) for k, v in streams.items()},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()

    raw = []
    for line in args.log.read_text(errors="replace").splitlines():
        m = LINE_RE.search(line)
        if not m:
            continue
        raw.append({
            "frame": int(m.group("frame")),
            "pc": int(m.group("pc"), 16),
            "ids": parse_hex_list(m.group("ids")),
            "selectors": parse_hex_list(m.group("sel")),
            "primary_masks": parse_hex_list(m.group("pm")),
            "union_masks": parse_hex_list(m.group("um")),
            "offsets": parse_hex_list(m.group("off")),
            "stage": parse_stage(m.group("stage")),
        })
    if not raw:
        raise SystemExit("no RACERCOMP lines found")

    pending = {}
    pairs = []
    for row in raw:
        key = row["frame"]
        if row["pc"] == 0xF129:
            pending[key] = row
        elif row["pc"] == 0xF292 and key in pending:
            pre = pending.pop(key)
            pairs.append({
                "frame": key,
                "ids": pre["ids"],
                "selectors": pre["selectors"],
                "primary_masks": pre["primary_masks"],
                "union_masks": pre["union_masks"],
                "offsets": pre["offsets"],
                "stage": row["stage"],
                "post_masks": {
                    "primary": row["primary_masks"],
                    "union": row["union_masks"],
                },
            })
    if not pairs:
        raise SystemExit("no paired F129/F292 RACERCOMP events found")

    rom = args.rom.read_bytes()
    analyzed = [analyze_event(rom, row) for row in pairs]
    nearest = {}
    for anchor in ANCHORS:
        nearest[str(anchor)] = min(analyzed, key=lambda r: abs(r["frame"] - anchor))

    report = {
        "schema_version": 2,
        "purpose": "Synchronize untouched F129 racer composition masks/cursors with the same-frame F292 staging output.",
        "raw_event_count": len(raw),
        "paired_event_count": len(analyzed),
        "events": analyzed,
        "nearest_anchor_events": nearest,
        "all_events_source_exact": all(r["mismatch_count"] == 0 for r in analyzed),
    }

    lines = [
        "# Synchronized racer cache composition",
        "",
        f"Raw trace events: {len(raw)}",
        f"Paired F129/F292 events: {len(analyzed)}",
        f"All paired events source-exact: {report['all_events_source_exact']}",
        "",
        "| anchor | frame | ids | selectors | mismatches |",
        "|---:|---:|---|---|---:|",
    ]
    for anchor in ANCHORS:
        r = nearest[str(anchor)]
        lines.append(
            f"| {anchor} | {r['frame']} | "
            + "/".join(f"0x{x:04X}" for x in r["ids"])
            + " | "
            + "/".join(f"0x{x:04X}" for x in r["selectors"])
            + f" | {r['mismatch_count']} |"
        )
    lines.append("")
    for anchor in ANCHORS:
        r = nearest[str(anchor)]
        lines.append(f"## Anchor {anchor}, captured frame {r['frame']}")
        lines.append("")
        lines.append("Primary masks @F129: " + " ".join(f"0x{x:04X}" for x in r["primary_masks"]))
        lines.append("Union masks @F129: " + " ".join(f"0x{x:04X}" for x in r["union_masks"]))
        lines.append("Offsets @F129: " + " ".join(f"0x{x:04X}" for x in r["offsets"]))
        for rr in range(5):
            choices = [
                c["choice"].replace("p1_", "1:").replace("p2_", "2:")
                for c in r["cells"]
                if c["row"] == rr
            ]
            lines.append(f"row {rr}: " + " | ".join(choices))
        if r["mismatches"]:
            lines.append("Mismatches: " + json.dumps(r["mismatches"][:5], sort_keys=True))
        lines.append("")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
