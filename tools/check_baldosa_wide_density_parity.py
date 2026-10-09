#!/usr/bin/env python3
"""Exact cross-process Baldosa 342-wide Original parity at density 1 vs 4.

The independently captured native 342x224 1x world output must be identical
at each shared *guest frame* to the logical image recovered from the actual
1368x896 4x output. This catches uniform-but-wrong 4x color/source pixels,
which a nearest-block validation alone cannot detect.

Native CRC equivalence, calibration and authentic world margins are validated
by the existing upstream reports; this script adds the missing image oracle.
It cannot certify original-emulator parity, per-OBJ visibility or 4K output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.baldosa_ws24_presentation_report import restore_logical_nearest

LOGICAL_WIDTH = 342
LOGICAL_HEIGHT = 224
DENSITY = 4
NAME = re.compile(r"ur-baldosa-ws342-(\d{6})\.pam")
HEADER1 = (
    b"P7\nWIDTH 342\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
    b"TUPLTYPE RGB_ALPHA\nENDHDR\n"
)
HEADER4 = (
    b"P7\nWIDTH 1368\nHEIGHT 896\nDEPTH 4\nMAXVAL 255\n"
    b"TUPLTYPE RGB_ALPHA\nENDHDR\n"
)


def capture_files(directory: Path, density: int) -> dict[int, bytes]:
    header = HEADER1 if density == 1 else HEADER4
    expected_pixels = LOGICAL_WIDTH * LOGICAL_HEIGHT * density * density * 4
    frames: dict[int, bytes] = {}
    for file in sorted(directory.glob("ur-baldosa-ws342-*.pam")):
        m = NAME.fullmatch(file.name)
        if m is None:
            raise ValueError(f"Malformed source-frame identity: {file.name}")
        frame = int(m.group(1))
        if frame in frames:
            raise ValueError(f"Duplicate source-frame capture: {frame}")
        data = file.read_bytes()
        if not data.startswith(header) or len(data) != len(header) + expected_pixels:
            raise ValueError(
                f"Invalid native {density}x raster dimensions/bytes: {file}")
        frames[frame] = data[len(header):]
    if not frames:
        raise ValueError(f"Missing real native {density}x captures: {directory}")
    return frames


def assess(one_x: dict[int, bytes], four_x: dict[int, bytes],
           min_shared_frames: int = 4) -> dict:
    if min_shared_frames < 2:
        raise ValueError("Need at least two independent moving guest frames")
    shared = sorted(one_x.keys() & four_x.keys())
    aligned = []
    for frame in shared:
        original = one_x[frame]
        physical = four_x[frame]
        logical, exact_nearest = restore_logical_nearest(
            physical, LOGICAL_WIDTH, LOGICAL_HEIGHT, DENSITY)
        # Every RGB/alpha byte is authoritative, not selected pixels or
        # perceptual similarity. A changed logical color may still form a
        # perfect 4x4 block, hence the independent 1x comparison.
        pixel_exact = exact_nearest and logical == original
        aligned.append({
            "guest_frame": frame,
            "logical_1x_sha256": hashlib.sha256(original).hexdigest(),
            "recovered_4x_logical_sha256": hashlib.sha256(logical).hexdigest(),
            "physical_4x_sha256": hashlib.sha256(physical).hexdigest(),
            "all_4x4_blocks_exact": exact_nearest,
            "all_logical_pixels_identical": pixel_exact,
        })
    good = [x for x in aligned if x["all_logical_pixels_identical"]]
    passed = (
        len(shared) >= min_shared_frames and len(good) == len(shared)
        and len({x["logical_1x_sha256"] for x in good}) >= 2
    )
    return {
        "schema_version": 1,
        "status": "passed" if passed else "unproven",
        "logical_source": [LOGICAL_WIDTH, LOGICAL_HEIGHT],
        "raster_one_x": [LOGICAL_WIDTH, LOGICAL_HEIGHT],
        "raster_four_x": [LOGICAL_WIDTH * DENSITY, LOGICAL_HEIGHT * DENSITY],
        "one_x_captured_frames": len(one_x),
        "four_x_captured_frames": len(four_x),
        "shared_guest_frames": len(shared),
        "exact_image_pairs": len(good),
        "minimum_shared_frames": min_shared_frames,
        "compared_frames": aligned,
        "independent_crc_and_world_calibration": (
            "validated separately by Baldosa native workflow; not repeated here"),
        "limits": (
            "Exact 1x-vs-4x same-guest-frame original widescreen output only; "
            "does not admit authored 342-wide OBJ replacement, source-PPU "
            "layer priority, complete events or physical 3840x2160 output."),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--one-x", type=Path, required=True)
    parser.add_argument("--four-x", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--min-shared", type=int, default=4)
    args = parser.parse_args()
    outcome = assess(
        capture_files(args.one_x, 1), capture_files(args.four_x, 4),
        args.min_shared)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(
        f"UR_BALDOSA_WS342_DENSITY_PARITY {outcome['status']} "
        f"frames={outcome['shared_guest_frames']} "
        f"pixel_exact={outcome['exact_image_pairs']}")
    return 0 if outcome["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
