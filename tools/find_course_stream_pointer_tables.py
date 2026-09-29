#!/usr/bin/env python3
"""Search the USA ROM for tables that point at the 45 known RNC course streams."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def lorom24(off: int) -> int:
    bank = off // 0x8000
    addr = 0x8000 + (off % 0x8000)
    return (bank << 16) | addr


def encodings(off: int) -> dict[str, bytes]:
    lo = lorom24(off)
    return {
        "lorom24_le": bytes((lo & 0xFF, (lo >> 8) & 0xFF, (lo >> 16) & 0xFF)),
        "file24_le": bytes((off & 0xFF, (off >> 8) & 0xFF, (off >> 16) & 0xFF)),
        "lorom16_le": bytes((lo & 0xFF, (lo >> 8) & 0xFF)),
    }


def occurrences(data: bytes, needle: bytes) -> list[int]:
    out = []
    start = 0
    while True:
        p = data.find(needle, start)
        if p < 0:
            return out
        out.append(p)
        start = p + 1


def find_runs(per_stream: list[list[int]], stride: int, min_len: int = 3) -> list[dict]:
    # A run means stream i pointer occurs at p, stream i+1 at p+stride, etc.
    lookup = [set(xs) for xs in per_stream]
    runs = []
    for i, starts in enumerate(per_stream):
        for pos in starts:
            n = 1
            while i + n < len(lookup) and pos + n * stride in lookup[i + n]:
                n += 1
            if n >= min_len:
                runs.append({
                    "first_stream": i + 1,
                    "last_stream": i + n,
                    "length": n,
                    "rom_offset": pos,
                })
    # Keep maximal unique runs.
    runs.sort(key=lambda x: (-x["length"], x["rom_offset"], x["first_stream"]))
    kept = []
    covered = set()
    for r in runs:
        key = (r["rom_offset"], r["first_stream"])
        if key in covered:
            continue
        kept.append(r)
        for d in range(r["length"]):
            covered.add((r["rom_offset"] + d * stride, r["first_stream"] + d))
    return kept


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", type=Path, default=Path("reference/roms/retail/Uniracers_USA.sfc"))
    ap.add_argument("--manifest", type=Path, default=Path("analysis/generated/rnc-stream-manifest.json"))
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    data = args.rom.read_bytes()
    manifest = json.loads(args.manifest.read_text())
    streams = manifest["roms"]["usa-retail"]["streams"]
    offsets = [int(x["offset"]) for x in streams]

    report = {
        "rom": str(args.rom),
        "stream_count": len(offsets),
        "stream_range": [min(offsets), max(offsets)],
        "modes": {},
    }

    for mode in ("lorom24_le", "file24_le", "lorom16_le"):
        needles = [encodings(off)[mode] for off in offsets]
        per = [occurrences(data, n) for n in needles]
        stride = len(needles[0])
        runs = find_runs(per, stride)
        report["modes"][mode] = {
            "pointer_width": stride,
            "total_occurrences": sum(len(x) for x in per),
            "streams_with_hits": sum(bool(x) for x in per),
            "runs_length_3_plus": runs[:50],
            "per_stream_hit_counts": [len(x) for x in per],
        }

    # Also inspect common fixed-width table strides where each pointer may have
    # a one-byte tag/padding field beside it.
    for mode in ("lorom24_le", "file24_le"):
        needles = [encodings(off)[mode] for off in offsets]
        per = [occurrences(data, n) for n in needles]
        for stride in (4, 5, 6, 8):
            report["modes"][f"{mode}_stride_{stride}"] = {
                "pointer_width": len(needles[0]),
                "record_stride": stride,
                "runs_length_3_plus": find_runs(per, stride)[:50],
            }

    print(json.dumps(report, indent=2))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
