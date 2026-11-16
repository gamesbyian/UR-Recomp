#!/usr/bin/env python3
"""WIDE-07 genuine framebuffer green LUT discriminator (original BGRX, native BMP).

Frames must be independently phase-qualified; matching dimensions is not phase proof.
No course acceptance is implied.
"""
import argparse
import collections
import json
import struct
from pathlib import Path

def original_bgrx(data, width, height):
    if len(data) != width * height * 4:
        raise ValueError("ORIGINAL_BRGX_LENGTH_MISMATCH")
    return [tuple(data[i + j] for j in (2, 1, 0)) for i in range(0, len(data), 4)]

def native_bmp(data, width, height):
    if len(data) < 54 or data[:2] != b"BM":
        raise ValueError("BMP_HEADER_INVALID")
    offset = struct.unpack_from("<I", data, 10)[0]
    dib = struct.unpack_from("<I", data, 14)[0]
    w, h, planes, bpp, compression = struct.unpack_from("<iiHHI", data, 18)
    if dib < 40 or offset < 14 + dib or planes != 1 or bpp != 24 or compression != 0:
        raise ValueError("BMP_FORMAT_INVALID")
    if w != width or abs(h) != height or h == 0:
        raise ValueError("BMP_DIMENSIONS_MISMATCH")
    stride = (width * 3 + 3) & ~3
    if offset + stride * height > len(data):
        raise ValueError("BMP_PIXELS_TRUNCATED")
    rows = []
    for y in range(height):
        source_y = y if h < 0 else height - 1 - y
        start = offset + source_y * stride
        rows.extend(tuple(data[i + j] for j in (2, 1, 0))
                    for i in range(start, start + width * 3, 3))
    return rows

def compare(original, native):
    if len(original) != len(native):
        raise ValueError("FRAME_LENGTH_MISMATCH")
    mapping = collections.defaultdict(set)
    histogram = collections.Counter()
    non_green = 0
    for (r, g, b), (nr, ng, nb) in zip(original, native):
        mapping[g].add(ng)
        histogram[ng - g] += 1
        non_green += (r != nr or b != nb)
    conflicts = {str(k): sorted(v) for k, v in sorted(mapping.items()) if len(v) > 1}
    return {
        "schema": "wide07-real-frame-green/1",
        "pixels": len(original),
        "red_or_blue_mismatch_pixels": non_green,
        "green_delta_histogram": {str(k): v for k, v in sorted(histogram.items())},
        "observed_green_mapping": {str(k): next(iter(v)) for k, v in sorted(mapping.items()) if len(v) == 1},
        "conflicting_green_values": conflicts,
        "deterministic_on_observed_values": not bool(conflicts),
        "unobserved_green_values": [i for i in range(256) if i not in mapping],
        "phase_equivalence_proven": False,
        "course_acceptance": 0,
    }

def selftest():
    def bmp(rows, top_down=False):
        height = len(rows)
        width = len(rows[0])
        stride = (width * 3 + 3) & ~3
        pixel_rows = rows if top_down else list(reversed(rows))
        payload = b"".join(b"".join(bytes((b,g,r)) for r,g,b in row).ljust(stride, b"\\0") for row in pixel_rows)
        return (b"BM" + struct.pack("<IHHI", 54 + len(payload), 0, 0, 54)
                + struct.pack("<IiiHHIIiiII", 40, width, -height if top_down else height, 1, 24, 0, len(payload), 0, 0, 0, 0)
                + payload)
    original = [(12,105,40),(12,134,40),(12,166,40),(12,105,40)]
    native = [(12,107,40),(12,132,40),(12,165,40),(12,107,40)]
    raw = b"".join(bytes((b,g,r,0)) for r,g,b in original)
    assert original_bgrx(raw, 2, 2) == original
    for orientation in (False, True):
        assert native_bmp(bmp([native[:2],native[2:]], orientation),2,2) == native
    report = compare(original, native)
    assert report["deterministic_on_observed_values"]
    assert report["observed_green_mapping"] == {"105":107,"134":132,"166":165}
    assert report["red_or_blue_mismatch_pixels"] == 0
    assert compare(original, native[:3]+[(12,106,40)])["conflicting_green_values"] == {"105":[106,107]}
    for bad in (bmp([native[:2],native[2:]])[:53], b"BAD" + bmp([native[:2],native[2:]])[3:]):
        try: native_bmp(bad,2,2)
        except ValueError: pass
        else: raise AssertionError("MALFORMED_BMP_ACCEPTED")
    print("WIDE07_REAL_FRAME_LUT_SELFTEST_PASS")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path)
    parser.add_argument("--native", type=Path)
    parser.add_argument("--width", type=int, default=256)
    parser.add_argument("--height", type=int, default=224)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.original or not args.native or args.width <= 0 or args.height <= 0:
        parser.error("real original/native files and positive dimensions required")
    report = compare(original_bgrx(args.original.read_bytes(), args.width, args.height),
                     native_bmp(args.native.read_bytes(), args.width, args.height))
    text = json.dumps(report, indent=2, sort_keys=True) + "\\n"
    if args.json_out:
        args.json_out.write_text(text)
    print(text, end="")

if __name__ == "__main__":
    main()
