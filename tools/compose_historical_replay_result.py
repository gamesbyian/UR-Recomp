#!/usr/bin/env python3
"""Compose a compact canonical result for the historical 2008 Dragster replay."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

LINE = re.compile(
    r"^(\d+)\tmenu=0x([0-9A-F]+)\tinRace=0x([0-9A-F]+)"
    r"\ttrack=(\d+)\tx=(-?\d+)\ty=(-?\d+)"
    r"\tvx=(-?\d+)\tvy=(-?\d+)\tair=(\d+)\tpitch=(\d+)$"
)
NSNAP = re.compile(
    r"^SNAP (\d+) menu=([0-9A-F]+) inRace=([0-9A-F]+)"
    r" track=(\d+) x=(-?\d+) y=(-?\d+) vx=(-?\d+) vy=(-?\d+)"
    r" air=(\d+) pitch=(\d+)$"
)


def parse_ref(path: Path) -> dict[int, tuple[int, ...]]:
    out = {}
    for line in path.read_text().splitlines():
        m = LINE.match(line)
        if not m:
            continue
        out[int(m.group(1))] = (
            int(m.group(2), 16),
            int(m.group(3), 16),
            *[int(x) for x in m.groups()[3:]],
        )
    return out


def parse_native(path: Path) -> dict[int, tuple[int, ...]]:
    payload = json.loads(path.read_text())
    out = {}
    for line in payload.get("snapshots", []):
        m = NSNAP.match(line)
        if not m:
            continue
        out[int(m.group(1))] = (
            int(m.group(2), 16),
            int(m.group(3), 16),
            *[int(x) for x in m.groups()[3:]],
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smv-meta", type=Path, required=True)
    ap.add_argument("--trace-summary", type=Path, required=True)
    ap.add_argument("--reference-tsv", type=Path, required=True)
    ap.add_argument("--native-json", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    smv = json.loads(args.smv_meta.read_text())
    trace = json.loads(args.trace_summary.read_text())
    ref = parse_ref(args.reference_tsv)
    native = parse_native(args.native_json)

    shared = sorted(set(ref) & set(native))
    mismatches = []
    for frame in shared:
        if ref[frame] != native[frame]:
            mismatches.append(
                {
                    "frame": frame,
                    "reference": ref[frame],
                    "native": native[frame],
                }
            )

    result = {
        "source_movie": smv.get("path"),
        "sample_count": smv.get("sample_count"),
        "event_runs": smv.get("event_runs"),
        "reset_anchored": smv.get("reset_anchored"),
        "embedded_sram_sha256": smv.get("embedded_sram_sha256"),
        "emitted_sram_size": smv.get("emitted_sram_size"),
        "emitted_sram_sha256": smv.get("emitted_sram_sha256"),
        "first_in_race_frame": trace.get("first_in_race_frame"),
        "first_race_results_frame": trace.get("first_race_results_frame"),
        "shared_sampled_frames": shared,
        "sampled_mismatch_count": len(mismatches),
        "first_sampled_mismatch_frame": mismatches[0]["frame"] if mismatches else None,
        "sampled_mismatches": mismatches,
        "reference_reached_race": trace.get("first_in_race_frame") is not None,
        "reference_reached_results": trace.get("first_race_results_frame") is not None,
        "sampled_native_reference_match": not mismatches,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
