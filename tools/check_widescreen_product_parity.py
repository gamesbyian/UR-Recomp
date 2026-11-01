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
import hashlib
import json
import struct
from pathlib import Path
from typing import Any

try:
    from tools.evidence_contract import assertion, make_envelope
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from evidence_contract import assertion, make_envelope
    from art.no_replace_report import publish_text_once

# Guest +8 lane surfaces (docs/WIDESCREEN-RECONNAISSANCE.md): the shared
# descriptor slot table at $0399..$03E0 and the strip staging buffer that the
# accepted payload is written into ($0433..$04B6, covering the split-screen
# P1/P2 staging as well).
ALLOWED_WRAM_RANGES = ((0x0399, 0x03E0), (0x0433, 0x04B6))

# Known cross-run variant, retained separately from other leak diagnostics.
# $0069 differed before the B-button intervention in R-SEED-018, which proves
# only that the B pulse did not cause it. The same address is identified as the
# sound-transfer counter in CPU/APU research (#1689). Neither observation proves
# downstream semantic irrelevance to audio. Do not let a difference here pass
# strict WIDE-07 WRAM parity without a separately reviewed consumer witness.
RUN_VARIANT_WRAM = (0x0069,)


def _read_bmp_with_identity(path: Path) -> tuple[int, int, list[bytes], dict[str, Any]]:
    raw = path.read_bytes()
    if raw[:2] != b"BM" or len(raw) < 54:
        raise ValueError(f"{path}: not a BMP")
    declared_size = struct.unpack_from("<I", raw, 2)[0]
    dib_size = struct.unpack_from("<I", raw, 14)[0]
    offset = struct.unpack_from("<I", raw, 10)[0]
    width = struct.unpack_from("<i", raw, 18)[0]
    height_signed = struct.unpack_from("<i", raw, 22)[0]
    planes = struct.unpack_from("<H", raw, 26)[0]
    bpp = struct.unpack_from("<H", raw, 28)[0]
    compression = struct.unpack_from("<I", raw, 30)[0]
    # Empty, compressed, malformed or truncated captures must never pass a
    # source-centre parity check merely because both decoded rows are empty.
    if (dib_size < 40 or 14 + dib_size > len(raw) or
        width <= 0 or height_signed in (0, -(1 << 31)) or
        planes != 1 or bpp not in (24, 32) or compression != 0 or
        offset < 14 + dib_size or declared_size != len(raw)):
        raise ValueError(f"{path}: invalid BMP geometry or header")
    height = abs(height_signed)
    bytes_pp = bpp // 8
    stride = (width * bytes_pp + 3) & ~3
    if offset + height * stride > len(raw):
        raise ValueError(f"{path}: truncated BMP pixels")
    rows = []
    for y in range(height):
        src_y = y if height_signed < 0 else height - 1 - y
        start = offset + src_y * stride
        row = raw[start:start + width * bytes_pp]
        # Normalise to 3-byte BGR so 24/32-bit captures compare equal.
        rows.append(b"".join(row[i:i + 3] for i in range(0, len(row), bytes_pp)))
    return width, height, rows, {"sha256": hashlib.sha256(raw).hexdigest(), "size": len(raw)}


def read_bmp(path: Path) -> tuple[int, int, list[bytes]]:
    width, height, rows, _ = _read_bmp_with_identity(path)
    return width, height, rows


def compare_center(stock: Path, wide: Path) -> dict[str, Any]:
    sw, sh, srows, stock_id = _read_bmp_with_identity(stock)
    ww, wh, wrows, wide_id = _read_bmp_with_identity(wide)
    result: dict[str, Any] = {
        "stock_geometry": [sw, sh],
        "wide_geometry": [ww, wh],
        "input_identities": {"stock": stock_id, "wide": wide_id},
    }
    if sh != wh or ww <= sw or (ww - sw) % 2:
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
        "input_identities": {
            "stock": {"sha256": hashlib.sha256(a).hexdigest(), "size": len(a)},
            "wide": {"sha256": hashlib.sha256(b).hexdigest(), "size": len(b)},
        },
        "complete_wram_images": len(a) == 0x20000 and len(b) == 0x20000,
        "lane_differences": lane,
        "run_variant_differences": [f"0x{x:05X}" for x in run_variant],
        "leaked_bytes": len(leaks),
        "first_leaks": [f"0x{x:05X}" for x in leaks[:16]],
    }



def _require_distinct_capture_files(pairs: list[tuple[str, Path, Path, Path, Path]]) -> None:
    """Reject one physical capture file supplied for two independent roles.

    Byte-identical WRAM from separately retained captures is legitimate; a
    repeated pathname, symlink or hardlink to the *same file* is not a second
    source observation.  Check all roles across all checkpoint tags, not just
    the four-hash tuple, which can change when only one reused role changes.
    """
    seen_files: list[tuple[str, Path]] = []
    for tag, stock_fb, wide_fb, stock_wram, wide_wram in pairs:
        for role, path in (("stock_fb", stock_fb), ("wide_fb", wide_fb),
                           ("stock_wram", stock_wram), ("wide_wram", wide_wram)):
            for prior_role, prior_path in seen_files:
                if path.samefile(prior_path):
                    raise ValueError(f"capture source reused: {tag}/{role} aliases {prior_role}")
            seen_files.append((f"{tag}/{role}", path))


def check(pairs: list[tuple[str, Path, Path, Path, Path]]) -> dict[str, Any]:
    if not pairs:
        raise ValueError("at least one real checkpoint pair is required")
    tags = [pair[0] for pair in pairs]
    if any(not isinstance(tag, str) or not tag.strip() for tag in tags):
        raise ValueError("checkpoint tags must be nonempty strings")
    if len(tags) != len(set(tags)):
        raise ValueError("duplicate checkpoint tag cannot identify distinct evidence")
    _require_distinct_capture_files(pairs)
    seen_inputs: set[tuple[str, ...]] = set()
    checks = []
    metrics: dict[str, Any] = {}
    for tag, stock_fb, wide_fb, stock_wram, wide_wram in pairs:
        center = compare_center(stock_fb, wide_fb)
        # Only the canonical stock/wide source rasters qualify this envelope.
        # A perfectly matched 1x1 or cropped BMP is not a WIDE-07 witness.
        center["expected_source_geometry"] = (
            center.get("stock_geometry") == [256, 224]
            and center.get("wide_geometry") == [342, 224]
        )
        wram = compare_wram(stock_wram, wide_wram)
        fingerprint = tuple(
            section["input_identities"][side]["sha256"]
            for section in (center, wram) for side in ("stock", "wide")
        )
        if fingerprint in seen_inputs:
            raise ValueError("identical capture bytes reused under different checkpoint tags")
        seen_inputs.add(fingerprint)
        metrics[tag] = {"center": center, "wram": wram}
        checks.append(assertion(
            f"{tag}-center-matches-stock",
            center["expected_source_geometry"] is True
            and center.get("comparable") is True
            and center.get("differing_pixels") == 0,
            center,
        ))
        checks.append(assertion(
            f"{tag}-wram-confined-to-guest-lane",
            wram["complete_wram_images"] and wram["leaked_bytes"] == 0
            and not wram["run_variant_differences"],
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
        publish_text_once(args.out, rendered)
    print(rendered, end="")
    return 0 if envelope["outcome"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
