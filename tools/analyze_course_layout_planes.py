#!/usr/bin/env python3
"""Characterize fixed 1024-byte regions after each decoded course header.

Header bytes 13/14 form a 45/45 product-1024 invariant (with 0 encoding 256).
This probe tests the smallest structural consequence without naming semantics:
whether one or more immediate 1024-byte regions have index/map-like statistics.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

from rnc_method1 import parse_header, unpack_method1


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    c = Counter(data)
    n = len(data)
    return -sum((v/n) * math.log2(v/n) for v in c.values())


def neighbor_stats(data: bytes, width: int, height: int) -> dict:
    if width * height != len(data):
        return {
            "horizontal_equal_fraction": None,
            "vertical_equal_fraction": None,
            "horizontal_mean_abs_delta": None,
            "vertical_mean_abs_delta": None,
        }
    h_pairs = []
    v_pairs = []
    for y in range(height):
        row = y * width
        for x in range(width - 1):
            h_pairs.append((data[row + x], data[row + x + 1]))
    for y in range(height - 1):
        row = y * width
        nxt = (y + 1) * width
        for x in range(width):
            v_pairs.append((data[row + x], data[nxt + x]))

    def eqfrac(pairs):
        return round(sum(a == b for a, b in pairs) / len(pairs), 6) if pairs else None

    def meandelta(pairs):
        return round(sum(abs(a - b) for a, b in pairs) / len(pairs), 6) if pairs else None

    return {
        "horizontal_equal_fraction": eqfrac(h_pairs),
        "vertical_equal_fraction": eqfrac(v_pairs),
        "horizontal_mean_abs_delta": meandelta(h_pairs),
        "vertical_mean_abs_delta": meandelta(v_pairs),
    }


def stats(data: bytes, width: int | None = None, height: int | None = None) -> dict:
    c = Counter(data)
    out = {
        "length": len(data),
        "zero_fraction": round(c.get(0, 0) / len(data), 6) if data else 0.0,
        "distinct_bytes": len(c),
        "min": min(data) if data else None,
        "max": max(data) if data else None,
        "entropy_bits_per_byte": round(entropy(data), 6),
        "fraction_lt_16": round(sum(v < 16 for v in data) / len(data), 6) if data else 0.0,
        "fraction_lt_64": round(sum(v < 64 for v in data) / len(data), 6) if data else 0.0,
        "top_values": [[k, v] for k, v in c.most_common(12)],
    }
    if width is not None and height is not None:
        out.update(neighbor_stats(data, width, height))
    return out


def streams(data: bytes) -> list[tuple[int, bytes]]:
    out = []
    p = 0
    while True:
        p = data.find(b"RNC\x01", p)
        if p < 0:
            return out
        h = parse_header(data[p:p+18])
        end = p + 18 + h.packed_size
        if h.packed_size and h.unpacked_size and end <= len(data):
            out.append((p, unpack_method1(data[p:end])))
        p += 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", type=Path, default=Path("reference/roms/retail/Uniracers_USA.sfc"))
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    args = ap.parse_args()

    decoded = streams(args.rom.read_bytes())
    result = {"schema_version": 1, "streams": []}
    for i, (rom_off, d) in enumerate(decoded, 1):
        dim_a = d[13] or 256
        dim_b = d[14] or 256
        regions = []
        for plane in range(4):
            start = 16 + plane * 1024
            end = min(start + 1024, len(d))
            regions.append({
                "index": plane,
                "offset": start,
                **stats(d[start:end], dim_a, dim_b),
            })
        result["streams"].append({
            "index": i,
            "rom_offset": rom_off,
            "decoded_size": len(d),
            "dim13": dim_a,
            "dim14": dim_b,
            "dimension_product": dim_a * dim_b,
            "post_header_remainder_mod_1024": (len(d) - 16) % 1024,
            "regions": regions,
        })

    # Corpus summaries make the output useful without manually reading 180 rows.
    summary = {}
    for plane in range(4):
        rows = [s["regions"][plane] for s in result["streams"]]
        summary[str(plane)] = {
            "mean_zero_fraction": round(sum(r["zero_fraction"] for r in rows) / len(rows), 6),
            "mean_distinct_bytes": round(sum(r["distinct_bytes"] for r in rows) / len(rows), 3),
            "mean_entropy_bits_per_byte": round(sum(r["entropy_bits_per_byte"] for r in rows) / len(rows), 6),
            "mean_fraction_lt_64": round(sum(r["fraction_lt_64"] for r in rows) / len(rows), 6),
            "mean_horizontal_equal_fraction": round(sum(r["horizontal_equal_fraction"] for r in rows if r["horizontal_equal_fraction"] is not None) / len([r for r in rows if r["horizontal_equal_fraction"] is not None]), 6),
            "mean_vertical_equal_fraction": round(sum(r["vertical_equal_fraction"] for r in rows if r["vertical_equal_fraction"] is not None) / len([r for r in rows if r["vertical_equal_fraction"] is not None]), 6),
        }
    result["region_summary"] = summary

    print(json.dumps(result, indent=2))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.md_out:
        lines = [
            "# Course 1024-Unit Region Probe",
            "",
            "Mechanical statistics for the first four 1024-byte regions after the 16-byte decoded header. No region is assigned a semantic meaning by this report.",
            "",
            "| region | mean zero fraction | mean distinct bytes | mean entropy | mean byte<64 | mean H equal | mean V equal |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for plane in range(4):
            s = summary[str(plane)]
            lines.append(
                f'| {plane} | {s["mean_zero_fraction"]:.6f} | {s["mean_distinct_bytes"]:.3f} | '
                f'{s["mean_entropy_bits_per_byte"]:.6f} | {s["mean_fraction_lt_64"]:.6f} | '
                f'{s["mean_horizontal_equal_fraction"]:.6f} | {s["mean_vertical_equal_fraction"]:.6f} |'
            )
        lines += ["", "## Per-stream first-region statistics", "",
                  "| # | dims | decoded bytes | rem mod 1024 | zero | distinct | entropy | <64 | H equal | V equal |",
                  "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for s in result["streams"]:
            r = s["regions"][0]
            lines.append(
                f'| {s["index"]} | {s["dim13"]}×{s["dim14"]} | {s["decoded_size"]} | '
                f'{s["post_header_remainder_mod_1024"]} | {r["zero_fraction"]:.6f} | '
                f'{r["distinct_bytes"]} | {r["entropy_bits_per_byte"]:.6f} | {r["fraction_lt_64"]:.6f} | '
                f'{r["horizontal_equal_fraction"]:.6f} | {r["vertical_equal_fraction"]:.6f} |'
            )
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
