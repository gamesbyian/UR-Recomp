#!/usr/bin/env python3
"""Summarize CPU-direct VRAM writer provenance during the deterministic scroll."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

TRACE_RE = re.compile(
    r"PPUPCTRACE frame=(?P<frame>\d+) v=(?P<v>\d+) cycles=(?P<cycles>-?\d+) "
    r"pc=(?P<pc>[0-9A-Fa-f]{6}) addr=(?P<addr>[0-9A-Fa-f]{4}) "
    r"val=(?P<val>[0-9A-Fa-f]{2}) ca=(?P<ca>\d+) cb=(?P<cb>\d+) "
    r"camx=(?P<camx>\d+) camy=(?P<camy>\d+) edgex=(?P<edgex>\d+) "
    r"edgey=(?P<edgey>\d+) camdx=(?P<camdx>\d+)"
)
SCROLL_RE = re.compile(r"script f=(\d+) dump prep-emission-before-scroll(?:\s|$)")


def parse(path: Path) -> tuple[int, list[dict]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = SCROLL_RE.search(text)
    if not m:
        raise SystemExit("could not identify scroll-start frame")
    start = int(m.group(1))
    rows = []
    for line in text.splitlines():
        m = TRACE_RE.search(line)
        if not m:
            continue
        g = m.groupdict()
        row = {
            "frame": int(g["frame"]),
            "v": int(g["v"]),
            "cycles": int(g["cycles"]),
            "pc": int(g["pc"], 16),
            "address": int(g["addr"], 16),
            "value": int(g["val"], 16),
            "count_a": int(g["ca"]),
            "count_b": int(g["cb"]),
            "camera_x": int(g["camx"]),
            "camera_y": int(g["camy"]),
            "camera_edge_x": int(g["edgex"]),
            "camera_edge_y": int(g["edgey"]),
            "camera_dx_raw": int(g["camdx"]),
        }
        if row["frame"] >= start:
            rows.append(row)
    return start, rows


def quads(rows: list[dict]) -> list[dict]:
    out = []
    for i in range(len(rows) - 3):
        group = rows[i:i + 4]
        if [r["address"] for r in group] != [0x2116, 0x2117, 0x2118, 0x2119]:
            continue
        if len({r["frame"] for r in group}) != 1:
            continue
        out.append({
            "frame": group[0]["frame"],
            "v": group[0]["v"],
            "destination": group[0]["value"] | (group[1]["value"] << 8),
            "write_2118": group[2]["value"],
            "write_2119": group[3]["value"],
            "pc_after_2116": group[0]["pc"],
            "pc_after_2118": group[2]["pc"],
            "count_a": group[0]["count_a"],
            "count_b": group[0]["count_b"],
            "camera_x": group[0]["camera_x"],
            "camera_y": group[0]["camera_y"],
            "camera_edge_x": group[0]["camera_edge_x"],
            "camera_edge_y": group[0]["camera_edge_y"],
            "camera_dx_raw": group[0]["camera_dx_raw"],
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()

    scroll_start, rows = parse(args.log)
    direct = quads(rows)
    writers = Counter((r["address"], r["pc"]) for r in rows)
    nonzero_count_writes = [r for r in rows if r["count_a"] or r["count_b"]]
    report = {
        "schema_version": 1,
        "fixture": "preparation-emission-race",
        "scroll_start_frame": scroll_start,
        "trace_rows_after_scroll_start": len(rows),
        "direct_vram_quads": direct,
        "direct_vram_quad_count": len(direct),
        "first_direct_vram_quad": direct[0] if direct else None,
        "nonzero_compact_count_ppu_writes": len(nonzero_count_writes),
        "writer_counts": [
            {"address": addr, "pc": pc, "count": count}
            for (addr, pc), count in sorted(writers.items())
        ],
    }

    lines = [
        "# CPU-direct VRAM writer provenance",
        "",
        f"- scroll start frame: **{scroll_start}**",
        f"- traced CPU-direct 2116-2119 writes after scroll start: **{len(rows)}**",
        f"- contiguous 2116/2117/2118/2119 quads: **{len(direct)}**",
        f"- PPU writes seeing non-zero compact counts: **{len(nonzero_count_writes)}**",
        "",
        "| addr | PC after write | count |",
        "|---|---|---:|",
    ]
    for (addr, pc), count in sorted(writers.items()):
        lines.append(f"| {addr:04X} | {pc:06X} | {count} |")
    if direct:
        q = direct[0]
        lines += [
            "",
            "First direct VRAM quad:",
            "",
            f"- frame {q['frame']} v={q['v']}; destination {q['destination']:04X}; "
            f"data {q['write_2118']:02X} {q['write_2119']:02X}",
            f"- camera x={q['camera_x']} edge-x={q['camera_edge_x']} "
            f"camera-dx-raw={q['camera_dx_raw']}",
            f"- compact counts at emission: A={q['count_a']} B={q['count_b']}",
        ]

    payload = json.dumps(report, indent=2) + "\n"
    md = "\n".join(lines) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(md, encoding="utf-8")
    print(md, end="")
    return 0 if direct else 2


if __name__ == "__main__":
    raise SystemExit(main())
