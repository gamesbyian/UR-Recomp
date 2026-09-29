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


def le(value: int, width: int) -> bytes:
    return value.to_bytes(width, "little")


def encodings(off: int, corpus_base: int) -> dict[str, bytes]:
    lo = lorom24(off)
    return {
        "lorom24_le": le(lo, 3),
        "file24_le": le(off, 3),
        "file32_le": le(off, 4),
        "lorom16_le": le(lo & 0xFFFF, 2),
        "corpus_rel24_le": le(off - corpus_base, 3),
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
    corpus_base = min(offsets)

    report = {
        "rom": str(args.rom),
        "stream_count": len(offsets),
        "stream_range": [min(offsets), max(offsets)],
        "modes": {},
    }

    for mode in ("lorom24_le", "file24_le", "file32_le", "lorom16_le", "corpus_rel24_le"):
        needles = [encodings(off, corpus_base)[mode] for off in offsets]
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
    for mode in ("lorom24_le", "file24_le", "file32_le", "corpus_rel24_le"):
        needles = [encodings(off, corpus_base)[mode] for off in offsets]
        per = [occurrences(data, n) for n in needles]
        width = len(needles[0])
        for stride in range(width + 1, 13):
            report["modes"][f"{mode}_stride_{stride}"] = {
                "pointer_width": width,
                "record_stride": stride,
                "runs_length_3_plus": find_runs(per, stride)[:50],
            }

    # Split address/bank layouts are common on 65816: one table holds 16-bit
    # addresses while a parallel table holds banks. The address-only scan
    # above already catches the former. Search the bank sequence separately,
    # with a higher minimum run length because individual bank bytes are noisy.
    bank_needles = [bytes([(lorom24(off) >> 16) & 0xFF]) for off in offsets]
    bank_per = [occurrences(data, n) for n in bank_needles]
    report["modes"]["lorom_bank_bytes"] = {
        "pointer_width": 1,
        "runs_length_8_plus": find_runs(bank_per, 1, min_len=8)[:50],
    }

    # Descriptor/index tables may carry sizes rather than pointers. Search
    # packed and unpacked 16-bit values in stream order, both tightly packed
    # and inside small fixed-width records.
    for field in ("packed_size", "unpacked_size"):
        vals = [int(x[field]) for x in streams]
        needles = [le(v, 2) for v in vals]
        per = [occurrences(data, n) for n in needles]
        report["modes"][f"{field}_16_le"] = {
            "value_width": 2,
            "total_occurrences": sum(len(x) for x in per),
            "runs_length_3_plus": find_runs(per, 2)[:50],
        }
        for stride in range(3, 13):
            report["modes"][f"{field}_16_le_stride_{stride}"] = {
                "value_width": 2,
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
