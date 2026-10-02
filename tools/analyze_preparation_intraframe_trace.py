#!/usr/bin/env python3
"""Summarize intra-frame producer/consumer observations for compact VRAM lists."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

LINE_RE = re.compile(
    r"PREPTRACE frame=(?P<frame>\d+) v=(?P<v>\d+) cycles=(?P<cycles>-?\d+) "
    r"pc=(?P<pc>[0-9A-Fa-f]{6}) y=(?P<y>[0-9A-Fa-f]{4}) "
    r"ca=(?P<ca>\d+) cb=(?P<cb>\d+) camx=(?P<camx>\d+) camy=(?P<camy>\d+) "
    r"edgex=(?P<edgex>\d+) edgey=(?P<edgey>\d+) camdx=(?P<camdx>\d+) "
    r"a=(?P<a>[^ ]*) b=(?P<b>[^ ]*)"
)

PC_NAMES = {
    0xA8FF: "list_a_count_store",
    0xAA34: "list_b_count_store",
    0xD37F: "list_consumer_entry",
}


def parse_entries(text: str) -> list[dict]:
    if not text:
        return []
    out = []
    for item in text.split(","):
        if not item:
            continue
        parts = item.split(":")
        if len(parts) < 2:
            continue
        row = {
            "destination": int(parts[0], 16),
            "selector": int(parts[1], 16),
        }
        if len(parts) >= 3:
            row["source_word"] = int(parts[2], 16)
            source = row["source_word"]
            swapped = ((source & 0xFF) << 8) | (source >> 8)
            row["write_2118"] = swapped & 0xFF
            row["write_2119"] = (swapped >> 8) & 0xFF
        out.append(row)
    return out


def parse_log(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = LINE_RE.search(line)
        if not m:
            continue
        g = m.groupdict()
        pc = int(g["pc"], 16)
        pcw = pc & 0xFFFF
        rows.append({
            "frame": int(g["frame"]),
            "v": int(g["v"]),
            "cycles": int(g["cycles"]),
            "pc": pc,
            "pcw": pcw,
            "site": PC_NAMES.get(pcw, "unknown"),
            "y": int(g["y"], 16),
            "count_a": int(g["ca"]),
            "count_b": int(g["cb"]),
            "camera_x": int(g["camx"]),
            "camera_y": int(g["camy"]),
            "camera_edge_x": int(g["edgex"]),
            "camera_edge_y": int(g["edgey"]),
            "camera_dx_raw": int(g["camdx"]),
            "list_a": parse_entries(g["a"]),
            "list_b": parse_entries(g["b"]),
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()

    rows = parse_log(args.log)
    if not rows:
        raise SystemExit("no PREPTRACE rows found; instrumentation did not execute")

    per_site = {}
    for pcw, name in PC_NAMES.items():
        site = [r for r in rows if r["pcw"] == pcw]
        per_site[name] = {
            "observations": len(site),
            "first": site[0] if site else None,
            "first_nonzero": next(
                (r for r in site if r["count_a"] or r["count_b"]), None
            ),
            "max_count_a": max((r["count_a"] for r in site), default=0),
            "max_count_b": max((r["count_b"] for r in site), default=0),
        }

    nonzero = [r for r in rows if r["count_a"] or r["count_b"]]
    consumers = [r for r in rows if r["pcw"] == 0xD37F]
    nonzero_consumers = [r for r in consumers if r["count_a"] or r["count_b"]]
    report = {
        "schema_version": 2,
        "fixture": "preparation-emission-race",
        "observation": "intra-frame PC trace at compact-list producer stores and consumer entry",
        "total_observations": len(rows),
        "nonzero_observations": len(nonzero),
        "first_nonzero": nonzero[0] if nonzero else None,
        "first_nonzero_consumer": nonzero_consumers[0] if nonzero_consumers else None,
        "sites": per_site,
        "rows": rows,
    }

    lines = [
        "# Intra-frame compact preparation-list trace",
        "",
        f"- observations: **{len(rows)}**",
        f"- non-zero list observations: **{len(nonzero)}**",
        f"- non-zero consumer observations: **{len(nonzero_consumers)}**",
        f"- first non-zero: **{nonzero[0]['site'] + ' frame ' + str(nonzero[0]['frame']) if nonzero else 'none'}**",
        "",
        "| site | observations | max A | max B | first non-zero |",
        "|---|---:|---:|---:|---|",
    ]
    for name, site in per_site.items():
        first = site["first_nonzero"]
        marker = (
            f"frame {first['frame']} v={first['v']} cycles={first['cycles']} "
            f"cam={first['camera_x']},{first['camera_y']} "
            f"edge={first['camera_edge_x']},{first['camera_edge_y']}"
            if first else "none"
        )
        lines.append(
            f"| {name} | {site['observations']} | {site['max_count_a']} | "
            f"{site['max_count_b']} | {marker} |"
        )

    payload = json.dumps(report, indent=2) + "\n"
    md = "\n".join(lines) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(md, encoding="utf-8")
    print(md, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
