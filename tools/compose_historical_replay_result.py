#!/usr/bin/env python3
"""Compose a compact canonical result for an exact historical replay."""

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


def parse_native_json(path: Path) -> dict[int, tuple[int, ...]]:
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


def _u16(blob: bytes, addr: int) -> int:
    return blob[addr] | (blob[addr + 1] << 8)


def _s16(blob: bytes, addr: int) -> int:
    value = _u16(blob, addr)
    return value - 0x10000 if value & 0x8000 else value


def parse_native_dumps(path: Path) -> dict[int, tuple[int, ...]]:
    out = {}
    for dump in sorted(path.glob("frame-*.wram.bin")):
        m = re.fullmatch(r"frame-(\d+)\.wram\.bin", dump.name)
        if not m:
            continue
        frame = int(m.group(1))
        blob = dump.read_bytes()
        if len(blob) < 0x20000:
            raise SystemExit(f"{dump}: expected 128 KiB WRAM, got {len(blob)}")
        out[frame] = (
            blob[0x009F],
            blob[0x0313],
            blob[0x00CE],
            _u16(blob, 0x0411),
            _u16(blob, 0x0415),
            _s16(blob, 0x04B7),
            _s16(blob, 0x04BB),
            blob[0x0545],
            _u16(blob, 0x04C7) & 0x3F,
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smv-meta", type=Path, required=True)
    ap.add_argument("--trace-summary", type=Path, required=True)
    ap.add_argument("--reference-tsv", type=Path, required=True)
    native_group = ap.add_mutually_exclusive_group(required=True)
    native_group.add_argument("--native-json", type=Path)
    native_group.add_argument("--native-dump-dir", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    smv = json.loads(args.smv_meta.read_text())
    trace = json.loads(args.trace_summary.read_text())
    ref = parse_ref(args.reference_tsv)
    native = (
        parse_native_json(args.native_json)
        if args.native_json is not None
        else parse_native_dumps(args.native_dump_dir)
    )

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

    first_race = trace.get("first_in_race_frame")
    first_results = trace.get("first_race_results_frame")
    native_race_state = native.get(first_race) if first_race is not None else None
    native_results_state = native.get(first_results) if first_results is not None else None

    result = {
        "source_movie": smv.get("path"),
        "sample_count": smv.get("sample_count"),
        "event_runs": smv.get("event_runs"),
        "reset_anchored": smv.get("reset_anchored"),
        "embedded_sram_sha256": smv.get("embedded_sram_sha256"),
        "emitted_sram_size": smv.get("emitted_sram_size"),
        "emitted_sram_sha256": smv.get("emitted_sram_sha256"),
        "first_in_race_frame": first_race,
        "first_race_results_frame": first_results,
        "shared_sampled_frames": shared,
        "sampled_mismatch_count": len(mismatches),
        "first_sampled_mismatch_frame": mismatches[0]["frame"] if mismatches else None,
        "sampled_mismatches": mismatches,
        "reference_reached_race": first_race is not None,
        "reference_reached_results": first_results is not None,
        "native_in_race_at_reference_entry": (
            native_race_state is not None and native_race_state[1] == 1
        ),
        "native_results_at_reference_results": (
            native_results_state is not None and native_results_state[0] == 0x99
        ),
        "sampled_native_reference_match": not mismatches,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
