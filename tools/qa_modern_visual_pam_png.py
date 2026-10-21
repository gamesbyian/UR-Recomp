#!/usr/bin/env python3
"""Losslessly wrap captured P7 SDL drawable pixels in an ordinary PNG.

This tool DOES NOT perform an SDL readback. It accepts only one strictly
bounded, complete RGB_ALPHA 8-bit P7 raster and emits a row-exact 8-bit RGBA
PNG with no resampling, alpha repair, colorspace adjustment or cropping.
Its receipt binds input/output SHA256 but grants zero screenshot-source,
visual, Authentic, physical-device or release acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import zlib

MAX_RASTER = 3840 * 2160 * 4
HEADER = re.compile(rb"\AP7\nWIDTH ([0-9]+)\nHEIGHT ([0-9]+)\nDEPTH 4\n"
                    rb"MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n\Z")
SIGNATURE = b"\x89PNG\r\n\x1a\n"


class RasterError(ValueError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_chunk(tag: bytes, payload: bytes) -> bytes:
    return (struct.pack(">I", len(payload)) + tag + payload +
            struct.pack(">I", zlib.crc32(tag + payload) & 0xffffffff))


def convert(source: Path, dest: Path, expected_size: tuple[int, int] | None = None) -> dict:
    if (not source.is_file() or source.is_symlink() or dest.exists() or
            dest.is_symlink() or source.resolve() == dest.resolve()):
        raise RasterError("input missing/redirected or PNG destination already exists")
    if source.stat().st_size > MAX_RASTER + 256:
        raise RasterError("P7 exceeds maximum drawable size")
    with source.open("rb") as stream:
        # Capture producer has a deterministic header; reject any commentary,
        # reordered tags or guessed depth/colour type.
        header = b""
        while not header.endswith(b"ENDHDR\n") and len(header) < 128:
            c = stream.read(1)
            if not c:
                break
            header += c
        match = HEADER.fullmatch(header)
        if not match:
            raise RasterError("invalid/noncanonical P7 RGB_ALPHA header")
        w, h = [int(x) for x in match.groups()]
        if not (1 <= w <= 3840 and 1 <= h <= 2160 and w * h * 4 <= MAX_RASTER):
            raise RasterError("invalid P7 drawable geometry")
        if expected_size is not None and (w, h) != expected_size:
            raise RasterError("observed drawable dimensions differ from requested size")
        if source.stat().st_size != len(header) + w * h * 4:
            raise RasterError("truncated or trailing P7 raster")
        # Temporary output is always on the same volume for atomic publication.
        temp = dest.with_name(dest.name + ".part")
        if temp.exists() or temp.is_symlink():
            raise RasterError("PNG temporary destination already exists")
        try:
            with temp.open("xb") as out:
                out.write(SIGNATURE)
                out.write(png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)))
                compressor = zlib.compressobj(level=6)
                for y in range(h):
                    row = stream.read(w * 4)
                    if len(row) != w * 4:
                        raise RasterError(f"P7 raster truncated at row {y}")
                    block = compressor.compress(b"\x00" + row)
                    if block:
                        out.write(png_chunk(b"IDAT", block))
                tail = compressor.flush()
                if tail:
                    out.write(png_chunk(b"IDAT", tail))
                out.write(png_chunk(b"IEND", b""))
            if dest.exists() or dest.is_symlink():
                raise RasterError("PNG destination appeared during conversion")
            os.replace(temp, dest)
        finally:
            if temp.exists():
                temp.unlink()
    return {
        "source_p7_sha256": sha256(source),
        "converted_png_sha256": sha256(dest),
        "source_bytes": source.stat().st_size,
        "png_bytes": dest.stat().st_size,
        "pixels": [w, h],
        "transform": "row-exact-P7-RGBA-to-filter0-PNG-RGBA",
        "actual_sdl_proven": False,
        "visual_approved": False,
        "hardware_approved": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("p7", type=Path)
    parser.add_argument("png", type=Path)
    parser.add_argument("--expect", help="Required observed output dimensions, e.g. 1920x1080")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    try:
        size = None
        if args.expect is not None:
            if not re.fullmatch(r"[0-9]{1,5}x[0-9]{1,5}", args.expect):
                raise RasterError("invalid --expect dimensions")
            size = tuple(int(x) for x in args.expect.split("x"))
        result = convert(args.p7, args.png, size)
        if args.receipt:
            if args.receipt.exists() or args.receipt.is_symlink():
                raise RasterError("receipt already exists")
            args.receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 0
    except (RasterError, OSError, ValueError) as exc:
        print("UR_MODERN_VISUAL_PAM_PNG_REJECTED:", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
