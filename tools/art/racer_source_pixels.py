#!/usr/bin/env python3
"""Decode a tightly bounded lossless RGBA PNG for exact original-racer review.

No ImageMagick, model inference or Pillow; never resample or invent input pixels.
Only the format written by UR's retained 64x64 source stock export is needed.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1024 * 1024
MAX_DIMENSION = 512


def decode_rgba_png(path: Path) -> tuple[int, int, bytes, str]:
    data = path.read_bytes()
    file_hash = hashlib.sha256(data).hexdigest()
    if not data.startswith(PNG_SIGNATURE) or len(data) > MAX_BYTES:
        raise ValueError("invalid or oversized PNG input")
    offset, dimensions, idat = len(PNG_SIGNATURE), None, bytearray()
    found_end, in_idat, closed_idat = False, False, False
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        size = struct.unpack_from(">I", data, offset)[0]
        tag = data[offset+4:offset+8]
        offset += 8
        if size > MAX_BYTES or offset + size + 4 > len(data):
            raise ValueError("invalid PNG chunk length")
        payload = data[offset:offset+size]
        actual_crc = struct.unpack_from(">I", data, offset+size)[0]
        if (zlib.crc32(tag + payload) & 0xffffffff) != actual_crc:
            raise ValueError("PNG CRC mismatch")
        offset += size+4
        if dimensions is None and tag != b"IHDR":
            raise ValueError("IHDR must be first")
        if tag == b"IHDR":
            if dimensions is not None or size != 13:
                raise ValueError("invalid PNG IHDR")
            w, h, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if (not 0 < w <= MAX_DIMENSION or not 0 < h <= MAX_DIMENSION or
                    (depth, color, compression, filtering, interlace) != (8, 6, 0, 0, 0)):
                raise ValueError("expected bounded, 8-bit noninterlaced RGBA")
            dimensions = (w, h)
        elif tag == b"IDAT":
            if closed_idat:
                raise ValueError("noncontiguous PNG IDAT")
            in_idat = True
            idat.extend(payload)
            if len(idat) > MAX_BYTES:
                raise ValueError("oversized PNG IDAT")
        elif tag == b"IEND":
            if not in_idat or size != 0 or offset != len(data):
                raise ValueError("missing IDAT or trailing bytes after IEND")
            found_end = True
            break
        elif tag and (tag[0] & 32) == 0:
            raise ValueError("unsupported PNG critical chunk")
        if in_idat and tag != b"IDAT":
            closed_idat = True
    if not found_end or dimensions is None:
        raise ValueError("missing PNG IEND or IHDR")
    width, height = dimensions
    stride = width * 4
    required = height * (stride + 1)
    inflater = zlib.decompressobj()
    scan = inflater.decompress(bytes(idat), required + 1)
    if (len(scan) != required or not inflater.eof or inflater.unused_data or
            inflater.unconsumed_tail or inflater.flush()):
        raise ValueError("incorrect or oversized PNG scanline data")
    rgba = bytearray()
    prior = bytes(stride)
    cursor = 0
    for _ in range(height):
        filter_type = scan[cursor]
        cursor += 1
        if filter_type > 4:
            raise ValueError("unsupported PNG filter")
        row = bytearray(scan[cursor:cursor+stride])
        cursor += stride
        for i in range(stride):
            left = row[i-4] if i >= 4 else 0
            up = prior[i]
            upper_left = prior[i-4] if i >= 4 else 0
            if filter_type == 1:
                prediction = left
            elif filter_type == 2:
                prediction = up
            elif filter_type == 3:
                prediction = (left + up) // 2
            elif filter_type == 4:
                p = left + up - upper_left
                a, b, c = abs(p-left), abs(p-up), abs(p-upper_left)
                prediction = left if a <= b and a <= c else up if b <= c else upper_left
            else:
                prediction = 0
            row[i] = (row[i] + prediction) & 255
        rgba.extend(row)
        prior = row
    return width, height, bytes(rgba), file_hash


def alpha_metrics(rgba: bytes, width: int, height: int) -> dict:
    if len(rgba) != width * height * 4:
        raise ValueError("invalid RGBA raster length")
    alpha = rgba[3::4]
    mask = bytes(1 if value else 0 for value in alpha)
    occupied = [i for i, value in enumerate(mask) if value]
    if not occupied:
        raise ValueError("source racer unexpectedly has no visible alpha")
    xx = [index % width for index in occupied]
    yy = [index // width for index in occupied]
    return {
        "source_rgba_sha256": hashlib.sha256(rgba).hexdigest(),
        "source_alpha_sha256": hashlib.sha256(alpha).hexdigest(),
        "binary_mask_sha256": hashlib.sha256(mask).hexdigest(),
        "nonzero_alpha_pixels": len(occupied),
        "alpha_bbox_xyxy_inclusive": [min(xx), min(yy), max(xx), max(yy)],
    }
