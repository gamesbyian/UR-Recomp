#!/usr/bin/env python3
"""Compare raw snesref BGRX8888 framebuffer checkpoints."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def compare_frames(
    a: bytes,
    b: bytes,
    *,
    width: int = 256,
    bytes_per_pixel: int = 4,
) -> dict:
    if len(a) != len(b):
        raise ValueError(f"frame sizes differ: {len(a)} != {len(b)}")
    if bytes_per_pixel < 1 or len(a) % bytes_per_pixel:
        raise ValueError("framebuffer byte length does not match pixel size")
    pixels = len(a) // bytes_per_pixel
    changed = []
    for i in range(pixels):
        p = i * bytes_per_pixel
        if a[p:p + bytes_per_pixel] != b[p:p + bytes_per_pixel]:
            changed.append(i)
    if changed:
        xs = [i % width for i in changed]
        ys = [i // width for i in changed]
        bbox = [min(xs), min(ys), max(xs), max(ys)]
    else:
        bbox = None
    return {
        "bytes": len(a),
        "pixels": pixels,
        "changed_pixels": len(changed),
        "changed_fraction": len(changed) / pixels if pixels else 0.0,
        "bbox": bbox,
        "a_sha256": hashlib.sha256(a).hexdigest(),
        "b_sha256": hashlib.sha256(b).hexdigest(),
    }


def compare_dirs(a_dir: Path, b_dir: Path) -> dict:
    rows = []
    for a in sorted(a_dir.glob("*.fb.bgrx")):
        name = a.name
        b = b_dir / name
        if not b.is_file():
            continue
        row = compare_frames(
            a.read_bytes(),
            b.read_bytes(),
            width=256,
            bytes_per_pixel=4,
        )
        row["checkpoint"] = name.removesuffix(".fb.bgrx")
        rows.append(row)
    return {"schema_version": 1, "checkpoints": rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("a_dir", type=Path)
    ap.add_argument("b_dir", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = compare_dirs(args.a_dir, args.b_dir)
    if not report["checkpoints"]:
        raise SystemExit("no matching *.fb.bgrx checkpoint pairs found")
    for row in report["checkpoints"]:
        print(
            f"{row['checkpoint']}: changed={row['changed_pixels']}/"
            f"{row['pixels']} bbox={row['bbox']}"
        )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
