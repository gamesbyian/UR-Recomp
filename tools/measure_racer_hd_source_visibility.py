#!/usr/bin/env python3
"""QA-08: measure actual stock OBJ emission and viewport HD suppression in motion.

Source OBJ counts are captured after PPU rasterization, before HD painting.
A selected OAM/WRAM rider can be absent from that original raster. Do not
interpret a registration as an actual source sprite pixel.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

SOURCE = re.compile(
    r"^UR_RACER_HD_SOURCE_OBJ frame=(\d+) top_opaque=(\d+) "
    r"bottom_opaque=(\d+) top_painted=([01]) bottom_painted=([01])$",
    re.MULTILINE,
)
PRESENT = re.compile(
    r"^UR_RACER_HD_CENSUS frame=(\d+) phase=present status=hd reason=([\w-]+)$",
    re.MULTILINE,
)


def analyze(log: str, first: int, last: int) -> dict:
    if first < 0 or last < first:
        raise ValueError("invalid inclusive frame interval")
    sources: dict[int, tuple[int, int, int, int]] = {}
    for hit in SOURCE.finditer(log):
        frame = int(hit[1])
        if not first <= frame <= last:
            continue
        if frame in sources:
            raise ValueError(f"duplicate OBJ source witness for frame {frame}")
        source_top, source_bottom, drawn_top, drawn_bottom = (
            int(hit[i]) for i in range(2, 6)
        )
        if drawn_top != int(source_top > 0) or drawn_bottom != int(source_bottom > 0):
            raise ValueError(f"source-empty viewport was painted at {frame}")
        sources[frame] = (source_top, source_bottom, drawn_top, drawn_bottom)
    presented = [
        int(hit[1]) for hit in PRESENT.finditer(log)
        if first <= int(hit[1]) <= last
    ]
    if not presented:
        raise ValueError("no real HD host presents in selected moving window")
    if len(set(presented)) != len(presented) or set(presented) != set(sources):
        raise ValueError("source witness does not match actual HD host presents")

    counts = {
        "hd_guest_frames": len(presented),
        "top_obj_absent_frames": 0,
        "bottom_obj_absent_frames": 0,
        "both_obj_absent_frames": 0,
        "both_obj_present_frames": 0,
        "top_only_obj_frames": 0,
        "bottom_only_obj_frames": 0,
    }
    examples = {"top_obj_absent": [], "bottom_obj_absent": [], "both_obj_absent": []}
    for f in sorted(presented):
        t, z, _, _ = sources[f]
        if not t:
            counts["top_obj_absent_frames"] += 1
            if len(examples["top_obj_absent"]) < 16:
                examples["top_obj_absent"].append(f)
        if not z:
            counts["bottom_obj_absent_frames"] += 1
            if len(examples["bottom_obj_absent"]) < 16:
                examples["bottom_obj_absent"].append(f)
        if not t and not z:
            counts["both_obj_absent_frames"] += 1
            if len(examples["both_obj_absent"]) < 16:
                examples["both_obj_absent"].append(f)
        elif t and z:
            counts["both_obj_present_frames"] += 1
        elif t:
            counts["top_only_obj_frames"] += 1
        else:
            counts["bottom_only_obj_frames"] += 1

    adjacent_edges = 0
    switches_top = switches_bottom = 0
    for f in sorted(sources):
        if f - 1 not in sources:
            continue
        adjacent_edges += 1
        switches_top += int(bool(sources[f][0]) != bool(sources[f - 1][0]))
        switches_bottom += int(bool(sources[f][1]) != bool(sources[f - 1][1]))
    counts.update(
        adjacent_hd_guest_edges=adjacent_edges,
        top_source_visibility_switches=switches_top,
        bottom_source_visibility_switches=switches_bottom,
    )
    if (
        counts["both_obj_absent_frames"]
        + counts["both_obj_present_frames"]
        + counts["top_only_obj_frames"]
        + counts["bottom_only_obj_frames"] != counts["hd_guest_frames"]
    ):
        raise ValueError("source visibility category denominator drift")
    return {
        "schema_version": 1,
        "window": [first, last],
        "measurement": counts,
        "examples": examples,
        "scope": (
            "actual post-PPU captured OBJ alpha and HD paint suppression per "
            "split viewport, not isolated OAM-slot ownership or foreground BG priority"
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("--from-frame", type=int, required=True)
    ap.add_argument("--to-frame", type=int, required=True)
    ap.add_argument("--json-out", type=Path)
    a = ap.parse_args()
    report = analyze(
        a.log.read_text(encoding="utf-8", errors="replace"),
        a.from_frame, a.to_frame,
    )
    if a.json_out:
        a.json_out.parent.mkdir(parents=True, exist_ok=True)
        a.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    m = report["measurement"]
    print(
        "UR_RACER_HD_SOURCE_VISIBILITY PASS "
        f"hd={m['hd_guest_frames']} "
        f"top_missing={m['top_obj_absent_frames']} "
        f"bottom_missing={m['bottom_obj_absent_frames']} "
        f"both_missing={m['both_obj_absent_frames']} "
        f"top_switches={m['top_source_visibility_switches']} "
        f"bottom_switches={m['bottom_source_visibility_switches']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
