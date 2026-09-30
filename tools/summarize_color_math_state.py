#!/usr/bin/env python3
"""Summarize color-math/subscreen state from snesref register snapshots.

This is deliberately descriptive. It records the raw SNES PPU register state
needed to investigate Uniracers' historical empty-subscreen color-addition seam
without prematurely deciding whether backdrop or fixed-color fallback is correct.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def summarize(regs_path: Path, frame_path: Path | None = None) -> dict:
    regs = json.loads(regs_path.read_text(encoding="utf-8"))
    ppu = regs["ppu"]
    row = {
        "checkpoint": regs_path.name.removesuffix(".regs.json"),
        "frame_tag": regs.get("frame_tag"),
        "tm": ppu["tm"],
        "ts": ppu["ts"],
        "tmw": ppu["tmw"],
        "tsw": ppu["tsw"],
        "cgwsel": ppu["cgwsel"],
        "cgadsub": ppu["cgadsub"],
        "fixed_color": ppu["fixed_color"],
        "brightness": ppu["inidisp"]["brightness"],
        "forced_blank": bool(ppu["inidisp"]["forced_blank"]),
    }
    cgwsel = int(ppu["cgwsel"], 16)
    cgadsub = int(ppu["cgadsub"], 16)
    ts = int(ppu["ts"], 16)
    row["subscreen_math_selected"] = bool(cgwsel & 0x02)
    row["color_math_layer_mask"] = cgadsub & 0x3F
    row["half"] = bool(cgadsub & 0x40)
    row["subtract"] = bool(cgadsub & 0x80)
    row["subscreen_layer_mask"] = ts & 0x1F
    if frame_path is not None and frame_path.is_file():
        raw = frame_path.read_bytes()
        row["frame_sha256"] = hashlib.sha256(raw).hexdigest()
        row["frame_bytes"] = len(raw)
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump_dir", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    rows = []
    for regs in sorted(args.dump_dir.glob("*.regs.json")):
        stem = regs.name.removesuffix(".regs.json")
        frame = args.dump_dir / f"{stem}.fb.bin"
        rows.append(summarize(regs, frame))
    for row in rows:
        print(
            f"{row['checkpoint']}: tm={row['tm']} ts={row['ts']} "
            f"cgwsel={row['cgwsel']} cgadsub={row['cgadsub']} "
            f"subscreen_math={int(row['subscreen_math_selected'])} "
            f"sub_layers=0x{row['subscreen_layer_mask']:02X} "
            f"math_layers=0x{row['color_math_layer_mask']:02X}"
        )
    report = {"schema_version": 1, "checkpoints": rows}
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
