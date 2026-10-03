#!/usr/bin/env python3
"""Summarize bounded native racer semantic traces.

The trace is sampled immediately after each guest frame from the same WRAM
composition snapshot consumed by the native replacement selector. It is
authoritative for host-frame semantic selection, not for raster-time sprite
identity inside the just-rendered frame.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

TRACE_RE = re.compile(
    r"UR_RACER_PRESENTATION_TRACE frame=(?P<frame>\d+) "
    r"p1_primary=(?P<p1>[0-9A-Fa-f]{4}) p2_primary=(?P<p2>[0-9A-Fa-f]{4}) "
    r"p1_companion=(?P<p1c>[0-9A-Fa-f]{4}) p2_companion=(?P<p2c>[0-9A-Fa-f]{4}) "
    r"p1_selector=(?P<p1s>[0-9A-Fa-f]{4}) p2_selector=(?P<p2s>[0-9A-Fa-f]{4}) "
    r"p1_gate=(?P<p1g>[0-9A-Fa-f]{4}) p2_gate=(?P<p2g>[0-9A-Fa-f]{4})"
)


def parse_trace(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        m = TRACE_RE.search(line)
        if not m:
            continue
        g = m.groupdict()
        rows.append({
            "frame": int(g["frame"]),
            "p1_primary": f"0x{g['p1'].upper()}",
            "p2_primary": f"0x{g['p2'].upper()}",
            "p1_companion": f"0x{g['p1c'].upper()}",
            "p2_companion": f"0x{g['p2c'].upper()}",
            "p1_selector": int(g["p1s"], 16),
            "p2_selector": int(g["p2s"], 16),
            "p1_gate": f"0x{g['p1g'].upper()}",
            "p2_gate": f"0x{g['p2g'].upper()}",
        })
    return rows


def runs_for(rows: list[dict], key: str) -> list[dict]:
    if not rows:
        return []
    out = []
    start = rows[0]["frame"]
    prev = rows[0]["frame"]
    value = rows[0][key]
    count = 1
    for row in rows[1:]:
        if row["frame"] != prev + 1 or row[key] != value:
            out.append({
                "start_frame": start,
                "end_frame": prev,
                "frames": count,
                "semantic_frame_id": value,
            })
            start = row["frame"]
            value = row[key]
            count = 1
        else:
            count += 1
        prev = row["frame"]
    out.append({
        "start_frame": start,
        "end_frame": prev,
        "frames": count,
        "semantic_frame_id": value,
    })
    return out


def transition_counts(rows: list[dict], key: str) -> list[dict]:
    counts = Counter()
    for a, b in zip(rows, rows[1:]):
        if b["frame"] != a["frame"] + 1:
            continue
        counts[(a[key], b[key])] += 1
    return [
        {"from": a, "to": b, "count": n}
        for (a, b), n in sorted(counts.items())
    ]


def build_report(rows: list[dict]) -> dict:
    frames = [r["frame"] for r in rows]
    contiguous = bool(rows) and frames == list(range(frames[0], frames[-1] + 1))
    players = {}
    for player in ("p1", "p2"):
        key = f"{player}_primary"
        players[player] = {
            "unique_primary_ids": sorted({r[key] for r in rows}),
            "runs": runs_for(rows, key),
            "transitions": transition_counts(rows, key),
        }
    return {
        "schema_version": 1,
        "source_semantics": "post-guest-frame WRAM composition used by native replacement selection",
        "raster_identity_authority": False,
        "timing_note": (
            "This trace does not collapse the known WRAM-vs-renderer timing seam; "
            "use it only for host-frame semantic selection and adjacency."
        ),
        "frame_window": [frames[0], frames[-1]] if rows else None,
        "frames_observed": len(rows),
        "contiguous": contiguous,
        "players": players,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    rows = parse_trace(args.log.read_text(encoding="utf-8", errors="replace"))
    report = build_report(rows)
    if not report["contiguous"]:
        raise SystemExit("dense racer semantic trace is missing frames")
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
