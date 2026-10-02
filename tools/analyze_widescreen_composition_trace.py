#!/usr/bin/env python3
"""Align bounded x=255 composition traces to Dragster event-relative tags."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

TAGS = ("object-tail-167", "object-tail-168", "object-tail-169")
LINE_RE = re.compile(r"WS_EDGE (.*)")
OBJ_RE = re.compile(r"WS_OBJ_CAND (.*)")
KV_RE = re.compile(r"(\w+)=(-?\w+)")


def read_trace(path: Path) -> tuple[dict[tuple[int, int], dict], dict[tuple[int, int], list[dict]]]:
    comp = {}
    obj = {}
    for line in path.read_text(errors="replace").splitlines():
        m = LINE_RE.search(line)
        if m:
            row = {k: v for k, v in KV_RE.findall(m.group(1))}
            row["frame"] = int(row["frame"])
            row["y"] = int(row["y"])
            comp[(row["frame"], row["y"])] = row
            continue
        m = OBJ_RE.search(line)
        if m:
            row = {k: v for k, v in KV_RE.findall(m.group(1))}
            row["frame"] = int(row["frame"])
            row["line"] = int(row["line"])
            obj.setdefault((row["frame"], row["line"]), []).append(row)
    return comp, obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()

    parsed = {m: read_trace(args.root / f"margin-{m}" / "run.log") for m in (0, 8)}
    traces = {m: parsed[m][0] for m in (0, 8)}
    obj_traces = {m: parsed[m][1] for m in (0, 8)}
    rows = []
    for tag in TAGS:
        item = {"tag": tag, "margins": {}}
        for margin in (0, 8):
            d = args.root / f"margin-{margin}"
            info = json.loads((d / "state" / f"{tag}.info.json").read_text())
            frame = int(info["frame"])
            lines = {}
            for y in (144, 145):
                key = (frame, y)
                if key not in traces[margin]:
                    raise SystemExit(f"missing trace margin={margin} tag={tag} frame={frame} y={y}")
                lines[str(y)] = traces[margin][key]
            obj_lines = {
                "143": obj_traces[margin].get((frame, 143), []),
                "144": obj_traces[margin].get((frame, 144), []),
            }
            hashes = {}
            for suffix in ("vram.bin", "cgram.bin", "oam.bin"):
                path = d / "state" / f"{tag}.{suffix}"
                hashes[suffix] = hashlib.sha256(path.read_bytes()).hexdigest()
            item["margins"][str(margin)] = {
                "frame": frame,
                "lines": lines,
                "obj_candidates": obj_lines,
                "state_hashes": hashes,
            }
        item["guest_frame_delta"] = item["margins"]["8"]["frame"] - item["margins"]["0"]["frame"]
        rows.append(item)

    comparisons = {}
    for row in rows:
        tagcmp = {}
        for y in ("144", "145"):
            a = row["margins"]["0"]["lines"][y]
            b = row["margins"]["8"]["lines"][y]
            keys = ("main", "sub", "obj", "cgwsel", "cgadsub", "fixed",
                    "tm", "ts", "tmw", "tsw", "cwin_nr", "cwin_bits",
                    "cwin_span", "cwin_bit", "cwin_l", "cwin_r")
            tagcmp[y] = {
                "different_fields": [k for k in keys if a[k] != b[k]],
                "control": {k: a[k] for k in keys},
                "plus8": {k: b[k] for k in keys},
            }
        comparisons[row["tag"]] = tagcmp

    report = {"rows": rows, "comparisons": comparisons}
    lines = [
        "# +8 x=255 composition trace",
        "",
        "| tag | y | differing composition inputs |",
        "|---|---:|---|",
    ]
    for row in rows:
        for y in ("144", "145"):
            diffs = comparisons[row["tag"]][y]["different_fields"]
            lines.append(f"| {row['tag']} | {y} | {', '.join(diffs) if diffs else 'none'} |")
    lines += ["", "OBJ writes to logical x=255 at object-tail-168:"]
    target = next(r for r in rows if r["tag"] == "object-tail-168")
    for margin in ("0", "8"):
        writes = target["margins"][margin]["obj_candidates"]
        lines.append(f"- margin {margin}: line143={writes['143']} line144={writes['144']}")

    lines += [
        "",
        "Event-boundary presentation-memory equality at object-tail-168:",
    ]
    h0 = target["margins"]["0"]["state_hashes"]
    h8 = target["margins"]["8"]["state_hashes"]
    for key in ("vram.bin", "cgram.bin", "oam.bin"):
        lines.append(f"- {key}: {'match' if h0[key] == h8[key] else 'DIFF'}")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
