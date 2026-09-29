#!/usr/bin/env python3
"""Compare named 128 KiB WRAM checkpoint dumps from two deterministic runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_CHECKPOINTS = [
    "main-menu-ready",
    "rider-select-ready",
    "tours-ready",
    "tracks-ready",
    "after-track-confirm",
    "now-playing-ready",
    "race-entered",
]


def summarize_diff(a: bytes, b: bytes, limit: int) -> dict:
    if len(a) != len(b):
        return {
            "same": False,
            "size_a": len(a),
            "size_b": len(b),
            "diff_count": None,
            "first_differences": [],
        }

    diffs = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    first = [
        {"offset": f"0x{i:05X}", "a": f"0x{a[i]:02X}", "b": f"0x{b[i]:02X}"}
        for i in diffs[:limit]
    ]
    return {
        "same": not diffs,
        "size_a": len(a),
        "size_b": len(b),
        "diff_count": len(diffs),
        "first_differences": first,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("a", type=Path, help="first dump directory")
    ap.add_argument("b", type=Path, help="second dump directory")
    ap.add_argument("--label-a", default="native")
    ap.add_argument("--label-b", default="reference")
    ap.add_argument("--checkpoint", action="append", dest="checkpoints")
    ap.add_argument("--limit", type=int, default=24)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument(
        "--require-identical",
        action="store_true",
        help="exit nonzero if any checkpoint differs",
    )
    args = ap.parse_args()

    checkpoints = args.checkpoints or DEFAULT_CHECKPOINTS
    report = {
        "label_a": args.label_a,
        "label_b": args.label_b,
        "checkpoints": {},
        "missing": [],
    }
    any_diff = False

    for name in checkpoints:
        pa = args.a / f"{name}.wram.bin"
        pb = args.b / f"{name}.wram.bin"
        if not pa.is_file() or not pb.is_file():
            report["missing"].append(
                {
                    "checkpoint": name,
                    args.label_a: str(pa) if pa.is_file() else None,
                    args.label_b: str(pb) if pb.is_file() else None,
                }
            )
            any_diff = True
            print(f"{name}: MISSING checkpoint dump")
            continue

        result = summarize_diff(pa.read_bytes(), pb.read_bytes(), args.limit)
        report["checkpoints"][name] = result
        if result["same"]:
            print(f"{name}: IDENTICAL ({result['size_a']} bytes)")
        else:
            any_diff = True
            if result["diff_count"] is None:
                print(
                    f"{name}: SIZE MISMATCH "
                    f"{args.label_a}={result['size_a']} {args.label_b}={result['size_b']}"
                )
            else:
                print(
                    f"{name}: {result['diff_count']} differing byte(s) "
                    f"of {result['size_a']}"
                )
                for d in result["first_differences"]:
                    print(
                        f"  {d['offset']}: "
                        f"{args.label_a}={d['a']} {args.label_b}={d['b']}"
                    )

    report["all_identical"] = not any_diff

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if report["missing"]:
        return 2
    if args.require_identical and any_diff:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
