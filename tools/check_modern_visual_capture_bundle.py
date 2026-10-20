#!/usr/bin/env python3
"""Fail-closed *structural* audit of actual native Modern UI capture bundles.

This verifies retained executable, P7, lossless PNG and route-log bytes,
fixed presentation sizes, exact case metadata and per-file SHA256. It does not infer that an image
was produced by that executable, that its pixels are correct, or that hardware
or human visual acceptance has occurred. See docs/MODERN-VISUAL-ACCEPTANCE.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "analysis/modern-visual-acceptance-matrix.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ASPECTS = {"16:9": (16, 9), "4:3": (4, 3)}
INPUTS = {"pad-p1": "native-semantic-pad", "pad-p2": "native-semantic-pad",
          "keyboard": "native-keyboard"}
PNG_SIG = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 100 * 1024 * 1024


class CaptureError(ValueError):
    pass


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_file(root: Path, rel: object) -> Path:
    if not isinstance(rel, str) or not rel or "\\" in rel:
        raise CaptureError("file path must be a nonempty portable relative path")
    p = PurePosixPath(rel)
    if p.is_absolute() or any(part in (".", "..") for part in p.parts):
        raise CaptureError("absolute or traversal file path")
    current = root.resolve()
    for part in p.parts:
        current = current / part
        if current.is_symlink():
            raise CaptureError("symlink in evidence path")
    if not current.is_file():
        raise CaptureError("missing evidence file: " + rel)
    if current.stat().st_size > MAX_BYTES:
        raise CaptureError("oversized evidence file: " + rel)
    return current


def checked_hash(root: Path, rel: object, expected: object) -> Path:
    if not isinstance(expected, str) or not HEX64.fullmatch(expected):
        raise CaptureError("missing/noncanonical SHA256 for " + str(rel))
    path = safe_file(root, rel)
    if digest(path) != expected:
        raise CaptureError("SHA256 mismatch: " + str(rel))
    return path


def png_pixels(data: bytes) -> tuple[int, int]:
    """Verify CRC-checked PNG envelope and unambiguous RGBA/RGB IHDR dimensions.

    Structural check only: visual pixel comparison and content inspection are
    independent steps. No PIL/decompression dependency on QA runners.
    """
    if len(data) < 57 or not data.startswith(PNG_SIG):
        raise CaptureError("not a complete PNG")
    pos, size = len(PNG_SIG), len(data)
    dims = None
    saw_idat = False
    closed_idat = False
    compressed = bytearray()
    channels = 0
    while pos < size:
        if size - pos < 12:
            raise CaptureError("truncated PNG chunk")
        n = struct.unpack_from(">I", data, pos)[0]
        tag = data[pos + 4:pos + 8]
        end = pos + 12 + n
        if end > size or n > MAX_BYTES:
            raise CaptureError("invalid PNG chunk extent")
        payload = data[pos + 8:pos + 8 + n]
        crc = struct.unpack_from(">I", data, pos + 8 + n)[0]
        if zlib.crc32(tag + payload) & 0xFFFFFFFF != crc:
            raise CaptureError("bad PNG chunk CRC")
        if dims is None:
            if tag != b"IHDR" or n != 13:
                raise CaptureError("PNG must start with IHDR")
            w, h, bit, color, comp, filt, interlace = struct.unpack(">IIBBBBB", payload)
            if (not w or not h or w > 16384 or h > 16384 or
                    bit != 8 or color not in (2, 6) or
                    comp != 0 or filt != 0 or interlace != 0):
                raise CaptureError("unsupported PNG raster")
            dims = (w, h)
            channels = 3 if color == 2 else 4
        elif tag == b"IHDR":
            raise CaptureError("duplicate PNG IHDR")
        if tag == b"IDAT":
            if closed_idat:
                raise CaptureError("out-of-order PNG IDAT")
            compressed.extend(payload)
            if len(compressed) > MAX_BYTES:
                raise CaptureError("oversized PNG compressed data")
            saw_idat = True
        elif saw_idat:
            closed_idat = True
        if tag == b"IEND":
            if n != 0 or end != size or not saw_idat:
                raise CaptureError("incomplete/trailing PNG")
            # A valid chunk envelope alone can contain garbage IDAT bytes.
            # Decode bounded raster bytes and check scanline filter syntax,
            # still WITHOUT claiming a visual-content or native-source verdict.
            width, height = dims
            scanline = 1 + width * channels
            expected_raw = scanline * height
            if expected_raw > MAX_BYTES:
                raise CaptureError("PNG decoded raster too large")
            try:
                decoder = zlib.decompressobj()
                raw = decoder.decompress(bytes(compressed), expected_raw + 1)
            except zlib.error as exc:
                raise CaptureError("invalid PNG image data") from exc
            if (len(raw) != expected_raw or not decoder.eof or
                    decoder.unused_data or decoder.unconsumed_tail):
                raise CaptureError("invalid/truncated PNG image raster")
            if any(raw[y * scanline] > 4 for y in range(height)):
                raise CaptureError("invalid PNG scanline filter")
            return dims
        pos = end
    raise CaptureError("PNG missing IEND")


def check_lossless_sdl_conversion(
    root: Path, shot: dict, pixels: tuple[int, int],
    png_path: Path, route_log: str,
) -> None:
    """Independently prove retained SDL-P7 bytes equal screenshot RGBA rows.

    A capture's *origin* still requires same-process/PE source verification.
    Both this check and the PNG byte scanner cannot infer genuine native
    origin from plausible strings alone, and confer no visual approval.
    """
    w, h = pixels
    source = checked_hash(
        root, shot.get("capture_p7"), shot.get("capture_p7_sha256"))
    expected_header = (
        f"P7\nWIDTH {w}\nHEIGHT {h}\nDEPTH 4\n"
        f"MAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"
    ).encode("ascii")
    data = source.read_bytes()
    if (not data.startswith(expected_header) or
            len(data) != len(expected_header) + w * h * 4):
        raise CaptureError("SDL readback P7 geometry, format or length invalid")
    # The diagnostic writes exactly once; require its actual observed
    # dimensions and SDL readback method on the SAME retained route log.
    native_lines = [
        line for line in route_log.splitlines()
        if "UR_MODERN_VISUAL_SDL_CAPTURE status=saved " in line
        and f" output={w}x{h} source=SDL_RenderReadPixels" in line
    ]
    if len(native_lines) != 1:
        raise CaptureError("missing/ambiguous actual SDL readback route log")

    converted = checked_hash(
        root, shot.get("conversion_receipt"), shot.get("conversion_receipt_sha256"))
    try:
        receipt = json.loads(converted.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise CaptureError("invalid SDL PNG conversion receipt") from exc
    if (not isinstance(receipt, dict) or
            receipt.get("source_p7_sha256") != shot.get("capture_p7_sha256") or
            receipt.get("converted_png_sha256") != shot.get("png_sha256") or
            receipt.get("pixels") != [w, h] or
            receipt.get("source_bytes") != len(data) or
            receipt.get("png_bytes") != png_path.stat().st_size or
            receipt.get("transform") != "row-exact-P7-RGBA-to-filter0-PNG-RGBA" or
            receipt.get("visual_approved") is not False or
            receipt.get("actual_sdl_proven") is not False or
            receipt.get("release_gate_credit") != 0):
        raise CaptureError("SDL PNG conversion receipt mismatch/nonapproval invariant")

    encoded = png_path.read_bytes()
    if (encoded[25] != 6 or encoded[24] != 8):  # RGBA, 8-bit
        raise CaptureError("SDL screenshot PNG must be 8-bit RGBA")
    pos, compressed = len(PNG_SIG), bytearray()
    while pos < len(encoded):
        n = struct.unpack_from(">I", encoded, pos)[0]
        if encoded[pos + 4:pos + 8] == b"IDAT":
            compressed.extend(encoded[pos + 8:pos + 8 + n])
        pos += 12 + n
    # png_pixels() has already bounded, decoded and CRC-verified these
    # chunks. Re-inflate only the already-validated source size to compare
    # filter-0 RGBA bytes byte-for-byte with retained P7 raw sample order.
    raw = zlib.decompress(bytes(compressed))
    stride = w * 4
    if len(raw) != (stride + 1) * h:
        raise CaptureError("unexpected decoded SDL PNG raster length")
    for y in range(h):
        if (raw[y * (stride + 1)] != 0 or
                raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)] !=
                data[len(expected_header) + y * stride:
                     len(expected_header) + (y + 1) * stride]):
            raise CaptureError("SDL P7/PNG exact RGBA pixel mismatch")


def read_matrix(matrix: dict) -> dict:
    if matrix.get("schema_version") != 1 or not isinstance(matrix.get("cases"), list):
        raise CaptureError("unsupported visual case matrix")
    out = {}
    for row in matrix["cases"]:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            raise CaptureError("invalid matrix case")
        ident = row["id"]
        if ident in out:
            raise CaptureError("duplicate matrix case: " + ident)
        aspect = row.get("aspect")
        pixels = row.get("pixels")
        if (aspect not in ASPECTS or not isinstance(pixels, list) or len(pixels) != 2
                or any(type(v) is not int or v <= 0 for v in pixels)
                or pixels[0] * ASPECTS[aspect][1] != pixels[1] * ASPECTS[aspect][0]):
            raise CaptureError("case has incompatible aspect/pixel geometry: " + ident)
        if row.get("input") not in INPUTS or row.get("mode") not in ("modern", "authentic"):
            raise CaptureError("case has unsupported input/mode: " + ident)
        out[ident] = row
    if not out:
        raise CaptureError("empty visual case matrix")
    return out


def audit(matrix: dict, bundle: dict, evidence_root: Path) -> dict:
    cases = read_matrix(matrix)
    if bundle.get("schema_version") != 1:
        raise CaptureError("unsupported capture manifest")
    source, binary_sha = bundle.get("source_sha"), bundle.get("exe_sha256")
    if not isinstance(source, str) or not HEX40.fullmatch(source):
        raise CaptureError("source_sha must be the exact lowercase Git commit")
    if not isinstance(binary_sha, str) or not HEX64.fullmatch(binary_sha):
        raise CaptureError("exe_sha256 must be full lowercase SHA256")
    if bundle.get("capture_runtime") != "native-sdl-final-output":
        raise CaptureError("mock/producer-only capture is not native final output")
    checked_hash(evidence_root, bundle.get("executable"), binary_sha)
    captures = bundle.get("captures")
    if not isinstance(captures, list):
        raise CaptureError("captures must be a list")
    seen = set()
    checked = []
    for shot in captures:
        if not isinstance(shot, dict) or not isinstance(shot.get("case_id"), str):
            raise CaptureError("invalid capture entry")
        key = shot["case_id"]
        if key not in cases or key in seen:
            raise CaptureError("unknown/duplicate capture case: " + key)
        seen.add(key)
        expected = cases[key]
        for name in ("mode", "input", "state", "screen"):
            if shot.get(name) != expected[name]:
                raise CaptureError(key + ": mismatched " + name)
        if shot.get("source_sha") != source or shot.get("exe_sha256") != binary_sha:
            raise CaptureError(key + ": source/executable changed within bundle")
        if shot.get("driver") != INPUTS[expected["input"]]:
            raise CaptureError(key + ": wrong native input route driver")
        frame = checked_hash(evidence_root, shot.get("png"), shot.get("png_sha256"))
        actual = png_pixels(frame.read_bytes())
        if list(actual) != expected["pixels"]:
            raise CaptureError(key + ": screenshot output size " + str(actual) +
                               " != " + str(expected["pixels"]))
        log = checked_hash(evidence_root, shot.get("route_log"), shot.get("route_log_sha256"))
        observed = log.read_text(encoding="utf-8", errors="replace")
        markers = shot.get("route_markers")
        if (not isinstance(markers, list) or not markers or
                any(not isinstance(m, str) or len(m) < 12 or m not in observed
                    for m in markers)):
            raise CaptureError(key + ": route marker absent from retained native log")
        check_lossless_sdl_conversion(evidence_root, shot, actual, frame, observed)
        checked.append(key)
    missing = sorted(set(cases) - seen)
    return {
        "schema_version": 1,
        "source_sha": source,
        "exe_sha256": binary_sha,
        "checked_structural": sorted(checked),
        "missing_capture_cases": missing,
        "structurally_complete": not missing,
        "visual_approved": False,
        "hardware_approved": False,
        "authentic_isolation_approved": False,
        "release_gate_credit": 0,
        "scope": "actual SDL-log marker, byte-bound P7/PNG lossless rows, executable/hash/route metadata; independent source and human review pending",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("bundle", type=Path, help="Capture manifest JSON")
    p.add_argument("--matrix", type=Path, default=MATRIX)
    p.add_argument("--require-complete", action="store_true")
    p.add_argument("--json-out", type=Path)
    args = p.parse_args()
    try:
        matrix = json.loads(args.matrix.read_text(encoding="utf-8"))
        bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
        result = audit(matrix, bundle, args.bundle.parent)
        if args.json_out:
            args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 2 if args.require_complete and not result["structurally_complete"] else 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print("MODERN_VISUAL_CAPTURE_REJECTED:", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
