#!/usr/bin/env python3
"""Classify four-ROM byte differences by build-agreement lineage.

The comparison deliberately excludes bytes occupied by valid RNC streams in any
build. Those compressed course assets have their own established analysis lane.

For every remaining offset where the four builds are not identical, this tool:
- records the equality partition among USA retail, Europe retail, legacy beta,
  and the 1994-11-29 PAL prototype;
- coalesces adjacent offsets with the same equality partition;
- ranks compact/high-density runs separately from broad churn;
- cross-classifies the sparse USA-vs-beta differences by which other build
  agrees with each side.

These are structural facts, not claims about chronology or authorship.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

NAMES = ("usa", "europe", "beta", "prototype")
DEFAULTS = {
    "usa": Path("reference/roms/retail/Uniracers_USA.sfc"),
    "europe": Path("reference/roms/retail/Unirally_Europe.sfc"),
    "beta": Path("reference/roms/prototypes/Uniracers_Beta_legacy.sfc"),
    "prototype": Path("reference/roms/prototypes/Unirally_1994-11-29_PAL_prototype.sfc"),
}


def rnc_ranges(data: bytes) -> list[tuple[int, int]]:
    out = []
    pos = 0
    while True:
        i = data.find(b"RNC", pos)
        if i < 0:
            break
        if i + 18 <= len(data) and data[i + 3] in (1, 2):
            packed = int.from_bytes(data[i + 8:i + 12], "big")
            unpacked = int.from_bytes(data[i + 4:i + 8], "big")
            end = i + 18 + packed
            if packed > 0 and unpacked > 0 and end <= len(data):
                out.append((i, end))
        pos = i + 1
    return out


def excluded_mask(blobs: dict[str, bytes]) -> bytearray:
    n = max(map(len, blobs.values()))
    mask = bytearray(n)
    for data in blobs.values():
        for a, b in rnc_ranges(data):
            mask[a:b] = bytes([1]) * (b - a)
    return mask


def equality_signature(values: tuple[int | None, ...]) -> str:
    groups = []
    seen = set()
    for i, value in enumerate(values):
        if i in seen:
            continue
        group = [i]
        seen.add(i)
        for j in range(i + 1, len(values)):
            if j not in seen and values[j] == value:
                group.append(j)
                seen.add(j)
        groups.append(group)
    return "|".join("+".join(NAMES[i] for i in g) for g in groups)


def changed_rows(blobs: dict[str, bytes], mask: bytearray) -> list[dict]:
    n = max(map(len, blobs.values()))
    rows = []
    for off in range(n):
        if mask[off]:
            continue
        vals = tuple(blobs[name][off] if off < len(blobs[name]) else None for name in NAMES)
        if len(set(vals)) == 1:
            continue
        rows.append({
            "offset": off,
            "signature": equality_signature(vals),
            "values": {
                name: (None if vals[i] is None else f"0x{vals[i]:02X}")
                for i, name in enumerate(NAMES)
            },
        })
    return rows


def coalesce(rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    runs = []
    start = prev = rows[0]["offset"]
    sig = rows[0]["signature"]
    vals = [rows[0]]
    for row in rows[1:]:
        if row["offset"] == prev + 1 and row["signature"] == sig:
            prev = row["offset"]
            vals.append(row)
            continue
        runs.append(make_run(start, prev, sig, vals))
        start = prev = row["offset"]
        sig = row["signature"]
        vals = [row]
    runs.append(make_run(start, prev, sig, vals))
    return runs


def make_run(start: int, end: int, signature: str, rows: list[dict]) -> dict:
    return {
        "start": start,
        "end_inclusive": end,
        "start_hex": f"0x{start:06X}",
        "end_hex": f"0x{end:06X}",
        "length": end - start + 1,
        "signature": signature,
        "first_values": rows[0]["values"],
        "last_values": rows[-1]["values"],
    }


def beta_delta_classes(blobs: dict[str, bytes], mask: bytearray) -> dict:
    usa, beta = blobs["usa"], blobs["beta"]
    n = min(len(usa), len(beta))
    counts: dict[str, int] = {}
    examples: dict[str, list[dict]] = {}
    for off in range(n):
        if mask[off] or usa[off] == beta[off]:
            continue
        u, b = usa[off], beta[off]
        e = blobs["europe"][off] if off < len(blobs["europe"]) else None
        p = blobs["prototype"][off] if off < len(blobs["prototype"]) else None
        relations = []
        for other_name, value in (("europe", e), ("prototype", p)):
            if value == u:
                relations.append(f"{other_name}=usa")
            elif value == b:
                relations.append(f"{other_name}=beta")
            else:
                relations.append(f"{other_name}=other")
        key = ",".join(relations)
        counts[key] = counts.get(key, 0) + 1
        examples.setdefault(key, [])
        if len(examples[key]) < 20:
            examples[key].append({
                "offset": off,
                "offset_hex": f"0x{off:06X}",
                "usa": f"0x{u:02X}",
                "beta": f"0x{b:02X}",
                "europe": None if e is None else f"0x{e:02X}",
                "prototype": None if p is None else f"0x{p:02X}",
            })
    return {"counts": counts, "examples": examples}


def build_report(paths: dict[str, Path]) -> dict:
    blobs = {name: paths[name].read_bytes() for name in NAMES}
    mask = excluded_mask(blobs)
    rows = changed_rows(blobs, mask)
    runs = coalesce(rows)
    sig_counts: dict[str, int] = {}
    for row in rows:
        sig_counts[row["signature"]] = sig_counts.get(row["signature"], 0) + 1
    compact = sorted(
        (r for r in runs if r["length"] <= 32),
        key=lambda r: (r["length"], r["start"]),
    )
    largest = sorted(runs, key=lambda r: (-r["length"], r["start"]))[:100]
    return {
        "schema_version": 1,
        "roms": {
            name: {
                "path": str(paths[name]),
                "size": len(blobs[name]),
                "sha256": hashlib.sha256(blobs[name]).hexdigest(),
                "rnc_ranges": [
                    {"start_hex": f"0x{a:06X}", "end_exclusive_hex": f"0x{b:06X}"}
                    for a, b in rnc_ranges(blobs[name])
                ],
            }
            for name in NAMES
        },
        "excluded_rnc_bytes_union": int(sum(mask)),
        "changed_non_rnc_bytes": len(rows),
        "signature_byte_counts": dict(sorted(sig_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "run_count": len(runs),
        "compact_runs_le_32": compact[:1000],
        "rare_signature_rows": {
            sig: [
                row for row in rows if row["signature"] == sig
            ]
            for sig, count in sig_counts.items()
            if count <= 512
        },
        "largest_runs": largest,
        "usa_beta_delta_classes": beta_delta_classes(blobs, mask),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for name in NAMES:
        ap.add_argument(f"--{name}", type=Path, default=DEFAULTS[name])
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    paths = {name: getattr(args, name) for name in NAMES}
    report = build_report(paths)
    print("changed_non_rnc_bytes", report["changed_non_rnc_bytes"])
    print("run_count", report["run_count"])
    print("top signatures")
    for sig, count in list(report["signature_byte_counts"].items())[:15]:
        print(f"  {count:8d} {sig}")
    print("USA-vs-beta cross-build classes")
    for key, count in sorted(report["usa_beta_delta_classes"]["counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {count:4d} {key}")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
