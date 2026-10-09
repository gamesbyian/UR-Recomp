#!/usr/bin/env python3
"""Admit non-destructive per-OAM-slot native Baldosa widescreen OBJ evidence.

The pinned PPU is told to export *one* of slots 96..99 without RemoveFromGame.
Its true isolated alpha emission and filename/frame/slot provenance must agree
with native logs, and every independently captured full 342x224 frame must
remain byte-identical to the uninstrumented 1x source-world raster.

A positive OBJ source plane does not prove final BG/window visibility or
license a host-authored replacement. Empty source slots are legitimate.
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
from tools.check_baldosa_wide_density_parity import capture_files

WIDTH, HEIGHT = 342, 224
HEADER = (
    b"P7\nWIDTH 342\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
    b"TUPLTYPE RGB_ALPHA\nENDHDR\n"
)
SOURCE_NAME = re.compile(
    r"ur-baldosa-ws342-obj-slot(9[6-9])-frame(\d{6})\.pam")
SOURCE_LOG = re.compile(
    r"UR_RACER_HD_WIDE_SOURCE frame=(\d+) slot=(\d+) "
    r"status=(source|empty|io-error) top_alpha=(\d+) bottom_alpha=(\d+) "
    r"bbox=(-?\d+),(-?\d+),(-?\d+),(-?\d+) path=(\S+)")


def read_source(path: Path, expected_slot: int) -> dict:
    match = SOURCE_NAME.fullmatch(path.name)
    if not match or int(match[1]) != expected_slot:
        raise ValueError(f"Incorrect source frame/slot filename: {path}")
    content = path.read_bytes()
    if not content.startswith(HEADER) or len(content) != len(HEADER) + WIDTH * HEIGHT * 4:
        raise ValueError(f"Malformed real per-slot 342x224 PPU OBJ plane: {path}")
    data = memoryview(content)[len(HEADER):]
    top = bottom = 0
    min_x, min_y, max_x, max_y = WIDTH, HEIGHT, -1, -1
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if data[(y * WIDTH + x) * 4 + 3] == 0:
                continue
            if y < 112:
                top += 1
            else:
                bottom += 1
            min_x, min_y = min(min_x, x), min(min_y, y)
            max_x, max_y = max(max_x, x), max(max_y, y)
    return {
        "slot": expected_slot,
        "guest_frame": int(match[2]),
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "top_opaque_source_pixels": top,
        "bottom_opaque_source_pixels": bottom,
        "bbox": [min_x, min_y, max_x, max_y],
        "source_nonempty": (top + bottom) != 0,
    }


def assess(reference: dict[int, bytes], observed: dict[int, bytes],
           source: dict, log: str, min_shared_frames: int = 4) -> dict:
    if source["slot"] not in (96, 97, 98, 99):
        raise ValueError("Only proven original racer slots 96..99")
    frames = sorted(reference.keys() & observed.keys())
    identical = [
        f for f in frames if reference[f] == observed[f]
    ]
    digest = {
        f: hashlib.sha256(reference[f]).hexdigest()
        for f in frames
    }
    diagnostics = [
        m for m in SOURCE_LOG.finditer(log)
        if int(m[2]) == source["slot"] and
        int(m[1]) == source["guest_frame"]
    ]
    log_matches = False
    if len(diagnostics) == 1:
        m = diagnostics[0]
        expected_status = "source" if source["source_nonempty"] else "empty"
        log_matches = (
            m[3] == expected_status and
            int(m[4]) == source["top_opaque_source_pixels"] and
            int(m[5]) == source["bottom_opaque_source_pixels"] and
            [int(m[i]) for i in range(6, 10)] == source["bbox"] and
            Path(m[10]).name ==
            f"ur-baldosa-ws342-obj-slot{source['slot']}-"
            f"frame{source['guest_frame']:06d}.pam"
        )
    passed = (
        len(frames) >= min_shared_frames and len(identical) == len(frames)
        and len({digest[f] for f in identical}) >= 2
        and source["guest_frame"] in frames and log_matches
    )
    return {
        "schema_version": 1,
        "status": "passed" if passed else "unproven",
        "source": source,
        "source_log_matches_pam": log_matches,
        "shared_full_frame_guest_ids": frames,
        "source_frame_main_raster_sha256": digest.get(source["guest_frame"]),
        "identical_complete_original_342_rasters": len(identical),
        "differing_original_rasters": [f for f in frames if f not in identical],
        "minimum_shared_frames": min_shared_frames,
        "guest_crc_comparison": "Externally enforced byte-exact in native workflow",
        "source_visibility_limit": (
            "Single original OAM slot isolated pre-BG/window priority; "
            "not proof of final screen visibility or safe HD replacement."),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--original-dir", type=Path, required=True)
    p.add_argument("--probe-dir", type=Path, required=True)
    p.add_argument("--source-file", type=Path, required=True)
    p.add_argument("--log", type=Path, required=True)
    p.add_argument("--slot", type=int, choices=(96, 97, 98, 99), required=True)
    p.add_argument("--min-shared", type=int, default=4)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = assess(
        capture_files(args.original_dir, 1),
        capture_files(args.probe_dir, 1),
        read_source(args.source_file, args.slot),
        args.log.read_text(encoding="utf-8", errors="replace"),
        args.min_shared,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    src = result["source"]
    print(
        f"UR_BALDOSA_WS342_SINGLE_SLOT {result['status']} "
        f"slot={src['slot']} frame={src['guest_frame']} "
        f"top={src['top_opaque_source_pixels']} "
        f"bottom={src['bottom_opaque_source_pixels']} "
        f"main_frames={result['identical_complete_original_342_rasters']}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
