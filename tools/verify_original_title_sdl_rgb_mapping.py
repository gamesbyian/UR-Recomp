#!/usr/bin/env python3
"""Independently audit original guest P6 -> final Windows SDL P7 RGB mapping.

Only validates source/presentation pixel mapping of a *single retained source
frame*. It does not verify gameplay, timing, original-title artistic identity,
asset rights, physical 4K, or release readiness. SDL alpha is not compared:
this native SDL3 readback cohort reports alpha zero even for visible RGB.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import stat
import zipfile

SOURCE_SIZE = (256, 224)
# 7:6 original source PAR: 256x224 -> 4:3 1024x768 or 960x720 + matte.
CASES = {
    "wide": ((1280, 720), (160, 0, 960, 720)),
    "4by3": ((1024, 768), (0, 0, 1024, 768)),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _ppm(data: bytes) -> bytes:
    header = b"P6\n256 224\n255\n"
    if not data.startswith(header) or len(data) != len(header) + 256 * 224 * 3:
        raise ValueError("Original guest P6 dimensions/format/length invalid")
    return data[len(header):]


def _pam(data: bytes, dimensions: tuple[int, int]) -> bytes:
    w, h = dimensions
    header = (f"P7\nWIDTH {w}\nHEIGHT {h}\nDEPTH 4\nMAXVAL 255\n"
              "TUPLTYPE RGB_ALPHA\nENDHDR\n").encode("ascii")
    if not data.startswith(header) or len(data) != len(header) + w * h * 4:
        raise ValueError("Final SDL P7 dimensions/format/length invalid")
    return data[len(header):]


def compare(source: bytes, final: bytes, mode: str) -> dict:
    dimensions, (left, top, viewport_w, viewport_h) = CASES[mode]
    src = _ppm(source)
    host = _pam(final, dimensions)
    host_w, host_h = dimensions
    mismatches = 0
    matte_nonblack = 0
    nonblack_source = sum(any(src[i:i+3]) for i in range(0, len(src), 3))
    for y in range(host_h):
        inside_y = top <= y < top + viewport_h
        sy = ((2 * (y - top) + 1) * SOURCE_SIZE[1]) // (2 * viewport_h) if inside_y else 0
        for x in range(host_w):
            i = (y * host_w + x) * 4
            pixel = host[i:i+3]
            if inside_y and left <= x < left + viewport_w:
                sx = ((2 * (x - left) + 1) * SOURCE_SIZE[0]) // (2 * viewport_w)
                j = (sy * SOURCE_SIZE[0] + sx) * 3
                if pixel != src[j:j+3]:
                    mismatches += 1
            elif any(pixel):
                matte_nonblack += 1
    if not nonblack_source:
        raise ValueError("Original title source frame is blank")
    if mismatches or matte_nonblack:
        raise ValueError(f"Original-to-SDL RGB mismatch: {mode}: viewport={mismatches}, matte={matte_nonblack}")
    return {"mode": mode, "source_raster": list(SOURCE_SIZE),
            "host_drawable": list(dimensions), "viewport": [left, top, viewport_w, viewport_h],
            "source_nonblack_pixels": nonblack_source,
            "host_rgb_pixels_checked": host_w * host_h,
            "viewport_rgb_mismatches": 0, "matte_nonblack_pixels": 0,
            "sdl_alpha_compared": False, "release_gate_credit": 0}


def audit(archive: Path, expected_archive_sha256: str,
          expected_source_sha: str, expected_pe_sha: str) -> dict:
    raw = archive.read_bytes()
    if digest(raw) != expected_archive_sha256:
        raise ValueError("Artifact ZIP differs from independently pinned archive hash")
    results = []
    source_frame_digests = []
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP member")
        for mode in CASES:
            prefix = f"modern-title-original-attract-sdl-{mode}-pr2043/"
            base = prefix + "original-title/"
            for name in (base + "original-presdl.ppm", base + "native-sdl.pam",
                         base + "original-title-source-vs-sdl.json",
                         prefix + "real-stock-title-demo-wake-sdl-receipt.json"):
                info = z.getinfo(name)
                if stat.S_ISLNK(info.external_attr >> 16) or info.file_size > 6_000_000:
                    raise ValueError("Redirected or oversized evidence member")
            src = z.read(base + "original-presdl.ppm")
            source_frame_digests.append(digest(src))
            host = z.read(base + "native-sdl.pam")
            witness = json.loads(z.read(base + "original-title-source-vs-sdl.json"))
            receipt = json.loads(z.read(prefix + "real-stock-title-demo-wake-sdl-receipt.json"))
            if (receipt.get("exact_native_source_sha") != expected_source_sha
                    or receipt.get("one_actual_windows_aot_pe_sha256") != expected_pe_sha
                    or witness.get("guest_frame") != 1200
                    or witness.get("original_rendered_before_sdl", {}).get("sha256") != digest(src)
                    or witness.get("actual_sdl_pixel_buffer_sha256") != digest(_pam(host, CASES[mode][0]))
                    or receipt.get("actual_native_sdl_output") != list(CASES[mode][0])):
                raise ValueError("Source/PE/frame/byte provenance mismatch")
            rows = receipt.get("real_original_guest_and_controller_source_stage_log", [])
            title = [r for r in rows if r.get("stage") == "original-title"]
            if len(title) != 1 or title[0].get("sdl_raw_p7_sha256") != digest(host):
                raise ValueError("Missing or substituted original-title SDL source receipt")
            results.append(compare(src, host, mode))
    if len(set(source_frame_digests)) != 1:
        raise ValueError("Original guest P6 source frame differs across host geometries")
    if len({r["source_nonblack_pixels"] for r in results}) != 1:
        raise ValueError("Source title contents diverge across host geometry")
    return {"schema": "ur-original-title-p6-to-sdl-p7-rgb/1",
            "archive_sha256": expected_archive_sha256,
            "exact_source_sha": expected_source_sha, "windows_pe_sha256": expected_pe_sha,
            "results": results, "original_native_guest_parity_proven": False,
            "human_art_approved": False, "physical_4k_approved": False,
            "release_gate_credit": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--pe-sha256", required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.archive, args.archive_sha256,
                           args.source_sha, args.pe_sha256), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
