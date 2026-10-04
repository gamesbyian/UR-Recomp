#!/usr/bin/env python3
"""Check that a widened product frame preserves the stock picture and state.

The Widescreen feature may add columns at the sides, but the authored 256-wide
picture must stay pixel-identical to the matched stock (Original view) frame,
and guest WRAM may differ only inside the documented guest +8 lane: the
descriptor slot table and the strip staging buffer. Anything else is leakage
from the presentation-only second pass.

Inputs are retained dump BMPs (24/32-bit, either row order) and WRAM images
captured at the same script checkpoint in matched stock and widened runs.
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Any

try:
    from tools.evidence_contract import assertion, make_envelope
except ModuleNotFoundError:
    from evidence_contract import assertion, make_envelope

# Guest +8 lane surfaces (docs/WIDESCREEN-RECONNAISSANCE.md): the shared
# descriptor slot table at $0399..$03E0 and the strip staging buffer that the
# accepted payload is written into ($0433..$04B6, covering the split-screen
# P1/P2 staging as well).
ALLOWED_WRAM_RANGES = ((0x0399, 0x03E0), (0x0433, 0x04B6))

# Bytes that differ between otherwise matched native runs regardless of
# Widescreen. They are reported, never counted as leaks.
#   $0069: accumulator written by 82:8082 through the $0063 long pointer;
#          already run-variant between matched native routes before any
#          input divergence (RESEARCH-LEDGER R-SEED-018).
RUN_VARIANT_WRAM = (0x0069,)


def read_bmp(path: Path) -> tuple[int, int, list[bytes]]:
    raw = path.read_bytes()
    if raw[:2] != b"BM" or len(raw) < 54:
        raise ValueError(f"{path}: not a BMP")
    offset = struct.unpack_from("<I", raw, 10)[0]
    width = struct.unpack_from("<i", raw, 18)[0]
    height_signed = struct.unpack_from("<i", raw, 22)[0]
    bpp = struct.unpack_from("<H", raw, 28)[0]
    if bpp not in (24, 32):
        raise ValueError(f"{path}: unsupported {bpp}-bit BMP")
    height = abs(height_signed)
    bytes_pp = bpp // 8
    stride = (width * bytes_pp + 3) & ~3
    rows = []
    for y in range(height):
        src_y = y if height_signed < 0 else height - 1 - y
        start = offset + src_y * stride
        row = raw[start:start + width * bytes_pp]
        # Normalise to 3-byte BGR so 24/32-bit captures compare equal.
        rows.append(b"".join(row[i:i + 3] for i in range(0, len(row), bytes_pp)))
    return width, height, rows


def compare_center(stock: Path, wide: Path) -> dict[str, Any]:
    sw, sh, srows = read_bmp(stock)
    ww, wh, wrows = read_bmp(wide)
    result: dict[str, Any] = {
        "stock_geometry": [sw, sh],
        "wide_geometry": [ww, wh],
    }
    if sh != wh or ww < sw or (ww - sw) % 2:
        result["comparable"] = False
        return result
    off = (ww - sw) // 2
    diffs = 0
    bbox = None
    for y in range(sh):
        a = srows[y]
        b = wrows[y][off * 3:(off + sw) * 3]
        if a == b:
            continue
        for x in range(sw):
            if a[x * 3:x * 3 + 3] != b[x * 3:x * 3 + 3]:
                diffs += 1
                if bbox is None:
                    bbox = [x, y, x, y]
                else:
                    bbox = [min(bbox[0], x), min(bbox[1], y),
                            max(bbox[2], x), max(bbox[3], y)]
    result.update({"comparable": True, "center_offset": off,
                   "differing_pixels": diffs, "bbox": bbox})
    return result


def allowed(addr: int) -> bool:
    return any(lo <= addr <= hi for lo, hi in ALLOWED_WRAM_RANGES)


def compare_wram(stock: Path, wide: Path) -> dict[str, Any]:
    a = stock.read_bytes()
    b = wide.read_bytes()
    leaks = []
    lane = 0
    run_variant = []
    for addr in range(min(len(a), len(b))):
        if a[addr] == b[addr]:
            continue
        if allowed(addr):
            lane += 1
        elif addr in RUN_VARIANT_WRAM:
            run_variant.append(addr)
        else:
            leaks.append(addr)
    return {
        "sizes": [len(a), len(b)],
        "lane_differences": lane,
        "run_variant_differences": [f"0x{x:05X}" for x in run_variant],
        "leaked_bytes": len(leaks),
        "first_leaks": [f"0x{x:05X}" for x in leaks[:16]],
    }


def check(pairs: list[tuple[str, Path, Path, Path, Path]]) -> dict[str, Any]:
    checks = []
    metrics: dict[str, Any] = {}
    for tag, stock_fb, wide_fb, stock_wram, wide_wram in pairs:
        center = compare_center(stock_fb, wide_fb)
        wram = compare_wram(stock_wram, wide_wram)
        metrics[tag] = {"center": center, "wram": wram}
        checks.append(assertion(
            f"{tag}-center-matches-stock",
            center.get("comparable") is True and center.get("differing_pixels") == 0,
            center,
        ))
        checks.append(assertion(
            f"{tag}-wram-confined-to-guest-lane",
            wram["sizes"][0] == wram["sizes"][1] and wram["leaked_bytes"] == 0,
            wram,
        ))
    return make_envelope(
        evidence_type="widescreen-product-parity",
        producer="tools/check_widescreen_product_parity.py",
        subject={"checkpoints": [p[0] for p in pairs]},
        inputs={"allowed_wram_ranges": [[f"0x{lo:04X}", f"0x{hi:04X}"] for lo, hi in ALLOWED_WRAM_RANGES]},
        metrics=metrics,
        assertions=checks,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stock-dumps", required=True, type=Path)
    parser.add_argument("--wide-dumps", required=True, type=Path)
    parser.add_argument("--checkpoint", action="append", required=True,
                        help="dump tag present in both directories as <tag>.fb.bmp and <tag>.wram.bin")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    pairs = [
        (tag,
         args.stock_dumps / f"{tag}.fb.bmp", args.wide_dumps / f"{tag}.fb.bmp",
         args.stock_dumps / f"{tag}.wram.bin", args.wide_dumps / f"{tag}.wram.bin")
        for tag in args.checkpoint
    ]
    envelope = check(pairs)
    rendered = json.dumps(envelope, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered, end="")
    return 0 if envelope["outcome"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
