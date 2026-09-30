#!/usr/bin/env python3
"""Summarize Uniracers presentation geometry and framebuffer edge content."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def row_metrics(raw: bytes, width: int, height: int, rows: int = 16) -> dict:
    bpp = 4
    expected = width * height * bpp
    if len(raw) != expected:
        raise ValueError(f"expected {expected} BGRX bytes, got {len(raw)}")
    rows = min(rows, height)

    def region(y0: int, y1: int) -> dict:
        chunk = raw[y0 * width * bpp : y1 * width * bpp]
        pixels = [
            chunk[i:i+bpp]
            for i in range(0, len(chunk), bpp)
        ]
        return {
            "rows": [y0, y1 - 1],
            "sha256": hashlib.sha256(chunk).hexdigest(),
            "unique_colors": len(set(pixels)),
            "nonzero_pixels": sum(1 for p in pixels if p[:3] != b"\x00\x00\x00"),
            "pixels": len(pixels),
        }

    per_row = []
    for y in range(height):
        chunk = raw[y * width * bpp : (y + 1) * width * bpp]
        pixels = [chunk[i:i+bpp] for i in range(0, len(chunk), bpp)]
        per_row.append({
            "y": y,
            "sha256": hashlib.sha256(chunk).hexdigest(),
            "unique_colors": len(set(pixels)),
            "nonzero_pixels": sum(1 for p in pixels if p[:3] != b"\x00\x00\x00"),
        })

    return {
        "top": region(0, rows),
        "bottom": region(height - rows, height),
        "last_row": per_row[-1],
        "per_row": per_row,
    }


def summarize_dump(root: Path, tag: str) -> dict:
    info = json.loads((root / f"{tag}.info.json").read_text(encoding="utf-8"))
    regs_path = root / f"{tag}.regs.json"
    raw = (root / f"{tag}.fb.bgrx").read_bytes()
    width = int(info["fb_width"])
    height = int(info["fb_height"])
    ppu_summary = None
    if regs_path.is_file():
        regs = json.loads(regs_path.read_text(encoding="utf-8"))
        ppu = regs["ppu"]
        ppu_summary = {
            "setini": ppu["setini"],
            "screen_height": ppu["screen_height"],
            "interlace": ppu["interlace"],
            "pseudo_hires": ppu["pseudo_hires"],
            "brightness": ppu["inidisp"]["brightness"],
            "forced_blank": ppu["inidisp"]["forced_blank"],
            "bgmode": ppu["bgmode"],
            "mosaic_size": ppu["mosaic_size"],
            "tm": ppu["tm"],
            "ts": ppu["ts"],
            "tmw": ppu["tmw"],
            "tsw": ppu["tsw"],
            "cgwsel": ppu["cgwsel"],
            "cgadsub": ppu["cgadsub"],
        }
    return {
        "checkpoint": tag,
        "frame": int(info["frame"]),
        "core_name": info.get("core_name"),
        "core_version": info.get("core_version"),
        "framebuffer": {
            "width": width,
            "height": height,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "edges": row_metrics(raw, width, height),
        },
        "ppu": ppu_summary,
    }


def summarize_dir(root: Path) -> dict:
    tags = sorted(
        p.name.removesuffix(".info.json")
        for p in root.glob("*.info.json")
        if (root / f"{p.name.removesuffix('.info.json')}.fb.bgrx").is_file()
    )
    return {"schema_version": 1, "checkpoints": [summarize_dump(root, t) for t in tags]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump_dir", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = summarize_dir(args.dump_dir)
    if not report["checkpoints"]:
        raise SystemExit("no complete checkpoint dumps found")
    for row in report["checkpoints"]:
        p = row["ppu"]
        b = row["framebuffer"]["edges"]["bottom"]
        ppu_text = (
            f"setini={p['setini']} screen_height={p['screen_height']} bgmode={p['bgmode']}"
            if p is not None else "ppu=unavailable"
        )
        print(
            f"{row['checkpoint']}: {row['framebuffer']['width']}x{row['framebuffer']['height']} "
            f"{ppu_text} bottom_nonzero={b['nonzero_pixels']}/{b['pixels']} "
            f"bottom_colors={b['unique_colors']}"
        )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
