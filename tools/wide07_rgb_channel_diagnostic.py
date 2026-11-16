#!/usr/bin/env python3
"""WIDE-07: compare genuine Snes9x BGRX frames with native 24-bit BMPs.

No spatial alignment, channel tolerance or race equivalence is assumed.
Each frame pair must be registered independently by its caller.
"""
import argparse
import collections
import json
import struct
from pathlib import Path


def original_pixels(path):
    data = Path(path).read_bytes()
    if len(data) != 256 * 224 * 4:
        raise ValueError("ORIGINAL_BGRX_LENGTH")
    return [tuple(data[i + k] for k in (2, 1, 0)) for i in range(0, len(data), 4)]


def native_pixels(path):
    data = Path(path).read_bytes()
    if data[:2] != b"BM" or len(data) < 54:
        raise ValueError("NATIVE_BMP_HEADER")
    offset = struct.unpack_from("<I", data, 10)[0]
    dib_size = struct.unpack_from("<I", data, 14)[0]
    planes = struct.unpack_from("<H", data, 26)[0]
    width, height = struct.unpack_from("<ii", data, 18)
    depth = struct.unpack_from("<H", data, 28)[0]
    compression = struct.unpack_from("<I", data, 30)[0]
    if (dib_size < 40 or planes != 1 or offset < 14 + dib_size or
            (width, abs(height), depth, compression) != (256, 224, 24, 0)):
        raise ValueError("NATIVE_BMP_GEOMETRY")
    stride = (width * 3 + 3) & ~3
    if len(data) < offset + stride * abs(height):
        raise ValueError("NATIVE_BMP_TRUNCATED")
    rows = []
    for y in range(224):
        source_y = 223 - y if height > 0 else y
        start = offset + source_y * stride
        rows.extend(tuple(data[i + k] for k in (2, 1, 0))
                    for i in range(start, start + width * 3, 3))
    return rows


def analyze(original, native):
    if len(original) != len(native):
        raise ValueError("PIXEL_COUNT_MISMATCH")
    hist = [collections.Counter() for _ in range(3)]
    mismatch = [0, 0, 0]
    first = None
    for i, (a, b) in enumerate(zip(original, native)):
        if a != b and first is None:
            first = {"xy": [i % 256, i // 256], "original_rgb": a, "native_rgb": b}
        for c in range(3):
            d = b[c] - a[c]
            hist[c][d] += 1
            mismatch[c] += d != 0
    return {
        "schema": "wide07-rgb-channel-diagnostic/1",
        "pixel_count": len(original),
        "mismatch_by_rgb_channel": dict(zip(("red", "green", "blue"), mismatch)),
        "signed_native_minus_original_histograms": {
            name: dict(sorted(h.items()))
            for name, h in zip(("red", "green", "blue"), hist)
        },
        "first_mismatch": first,
        "exact_rgb_pixels": sum(a == b for a, b in zip(original, native)),
        "pixel_parity_proven": all(v == 0 for v in mismatch),
        "course_acceptance": 0,
    }


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        original = [(12, 24, 36)] * (256 * 224)
        bgrx = bytes((b, g, r, 0) for r, g, b in [])  # empty construction sanity
        assert bgrx == b""
        (d / "original.bgrx").write_bytes(bytes([36, 24, 12, 0]) * (256 * 224))
        # Positive-height BMP must be bottom-up, not top-down.
        row = bytes([36, 25, 12]) * 256
        header = bytearray(54)
        header[:2] = b"BM"
        struct.pack_into("<I", header, 2, 54 + 224 * len(row))
        struct.pack_into("<I", header, 10, 54)
        struct.pack_into("<I", header, 14, 40)
        struct.pack_into("<ii", header, 18, 256, 224)
        struct.pack_into("<H", header, 26, 1)
        struct.pack_into("<H", header, 28, 24)
        (d / "native.bmp").write_bytes(header + row * 224)
        result = analyze(original_pixels(d / "original.bgrx"), native_pixels(d / "native.bmp"))
        assert result["mismatch_by_rgb_channel"] == {"red": 0, "green": 57344, "blue": 0}
        assert result["signed_native_minus_original_histograms"]["green"] == {1: 57344}
        assert result["first_mismatch"]["xy"] == [0, 0]
        assert not result["pixel_parity_proven"]
        # Prove scanline orientation, not merely uniform-colour equivalence.
        raw = bytearray((d / "native.bmp").read_bytes())
        raw[54:57] = bytes([1, 2, 3])
        (d / "native.bmp").write_bytes(raw)
        assert native_pixels(d / "native.bmp")[-256] == (3, 2, 1)
        # A malicious offset into the BMP header must not be read as pixels.
        malformed = bytearray((d / "native.bmp").read_bytes())
        struct.pack_into("<I", malformed, 10, 0)
        (d / "bad-offset.bmp").write_bytes(malformed)
        try:
            native_pixels(d / "bad-offset.bmp")
        except ValueError as exc:
            assert str(exc) == "NATIVE_BMP_GEOMETRY"
        else:
            raise AssertionError("BMP_HEADER_OVERLAP_ACCEPTED")
        try:
            native_pixels(d / "original.bgrx")
        except ValueError as exc:
            assert str(exc) == "NATIVE_BMP_HEADER"
        else:
            raise AssertionError("INVALID_BMP_ACCEPTED")
    print("WIDE07_RGB_DIAGNOSTIC_SELFTEST_PASS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-bgrx", type=Path)
    parser.add_argument("--native-bmp", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.original_bgrx or not args.native_bmp:
        parser.error("both frame paths required")
    result = analyze(original_pixels(args.original_bgrx), native_pixels(args.native_bmp))
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.write_text(output)
    print(output, end="")


if __name__ == "__main__":
    main()
