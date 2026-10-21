#!/usr/bin/env python3
"""Audit user-local original menu atlas PNGs against a source-bundle receipt.

This is NOT a game-asset redistribution mechanism and cannot prove that a
source capture came from a licensed original ROM. It verifies that the four
PNG files handed to a downstream native presenter match their independently
retained source-consistency manifest, image geometry and decoded byte layout.

Supported PNGs are intentionally limited to the first-party extractor's
8-bit, non-interlaced RGBA output with scanline filter 0. No Pillow or
external dependencies, no source art packaged or checked in.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

EXPECTED = {
    "heading": (640, 16),
    "detail": (360, 16),
    "cursor": (624, 39),
    "bg1": (256, 224),
}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_PNG_BYTES = 4 * 1024 * 1024
SOURCE_FIXTURE = "tests/input/menu-visual-language.script"
SOURCE_MAIN_TAG = "mvl-idle-000"
SOURCE_PPU_FIELDS = frozenset((
    "main_vram", "main_cgram", "detail_vram", "detail_cgram",
))


def read_png_rgba(path: Path, width: int, height: int,
                  max_png_bytes: int = MAX_PNG_BYTES) -> bytes:
    """Read only first-party filter-zero RGBA PNG; bound compressed input.

    The source-asset verifier retains its 4 MiB default. SDL output review
    may explicitly allow a larger capture, without changing original-art
    distribution or bundle admission policy.
    """
    if (width <= 0 or height <= 0 or width > 4096 or height > 4096 or
            max_png_bytes < 1024 or max_png_bytes > 64 * 1024 * 1024):
        raise ValueError("invalid original-art or SDL PNG geometry/limit")
    if path.stat().st_size > max_png_bytes:
        raise ValueError(f"{path.name}: reference PNG unexpectedly large")
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError(f"{path.name}: missing PNG signature")
    offset = len(PNG_SIGNATURE)
    chunks = []
    while offset + 12 <= len(data):
        count = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + count
        if end > len(data):
            raise ValueError(f"{path.name}: truncated PNG chunk")
        payload = data[offset + 8:offset + 8 + count]
        crc = struct.unpack(">I", data[offset + 8 + count:end])[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != crc:
            raise ValueError(f"{path.name}: invalid PNG chunk CRC")
        chunks.append((kind, payload))
        offset = end
        if kind == b"IEND":
            break
    if offset != len(data) or len(chunks) != 3:
        raise ValueError(f"{path.name}: unsupported PNG chunk sequence")
    if [k for k, _ in chunks] != [b"IHDR", b"IDAT", b"IEND"]:
        raise ValueError(f"{path.name}: PNG chunk order must be IHDR/IDAT/IEND")
    hdr = chunks[0][1]
    if hdr != struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0):
        raise ValueError(f"{path.name}: not the expected RGBA geometry")
    if chunks[-1][1]:
        raise ValueError(f"{path.name}: invalid IEND content")
    row = width * 4
    expected = height * (row + 1)
    inflate = zlib.decompressobj()
    raw = inflate.decompress(chunks[1][1], expected + 1)
    if (len(raw) != expected or not inflate.eof or inflate.unconsumed_tail or
            inflate.unused_data or inflate.flush()):
        raise ValueError(f"{path.name}: invalid or oversize PNG scanline stream")
    pixels = bytearray(row * height)
    for y in range(height):
        base = y * (row + 1)
        if raw[base] != 0:
            raise ValueError(f"{path.name}: unsupported PNG scanline filter")
        pixels[y * row:(y + 1) * row] = raw[base + 1:base + 1 + row]
    return bytes(pixels)


def verify_local_source_ppu_dumps(receipt: dict, directory: Path) -> None:
    """Rehash user-local original capture bytes; never publish those bytes.

    This optional original-snapshot consistency witness does not prove ROM
    identity, source ownership or distribution rights. A complete textual
    receipt alone cannot provide the underlying PPU-byte evidence.
    """
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError("source PPU dump directory missing or redirected")
    roots = (
        ("main_vram", receipt["source_main_tag"], "vram", 65536),
        ("main_cgram", receipt["source_main_tag"], "cgram", 512),
        ("detail_vram", receipt["source_detail_tag"], "vram", 65536),
        ("detail_cgram", receipt["source_detail_tag"], "cgram", 512),
    )
    for digest_key, tag, segment, expected_size in roots:
        path = directory / f"{tag}.{segment}.bin"
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"source PPU {digest_key}: capture file absent or redirected")
        # A too-large malicious input is never read into memory, and a
        # truncated file cannot pass via a prefix hash.
        with path.open("rb") as handle:
            raw = handle.read(expected_size + 1)
        if len(raw) != expected_size:
            raise ValueError(f"source PPU {digest_key}: exact dump length mismatch")
        if hashlib.sha256(raw).hexdigest() != receipt["source_ppu_sha256"][digest_key]:
            raise ValueError(f"source PPU {digest_key}: captured bytes disagree with receipt")


def verify_source_art_bundle(receipt: dict, paths: dict[str, Path],
                             source_dump_dir: Path | None = None) -> dict:
    """Verify source-affinity receipt, optional PPU bytes and image inputs."""
    if not isinstance(receipt, dict) or receipt.get("schema_version") != 1:
        raise ValueError("unsupported original art bundle receipt")
    if receipt.get("reference_only") is not True or (
            receipt.get("asset_distribution_approved") is not False or
            receipt.get("native_render_and_visual_acceptance") is not False):
        raise ValueError("source-only rights and acceptance flags must remain false")
    # The first-party exporter always supplies the source capture family,
    # exact main-frame anchor and four original VRAM/CGRAM SHA256 digests.
    # The old verifier accidentally admitted receipts with NONE of these.
    # Requiring a complete, well-formed claim does not cryptographically
    # establish that those PPU bytes came from a licensed source ROM: that
    # remains an independent upstream capture/provenance responsibility.
    if (receipt.get("source_fixture") != SOURCE_FIXTURE or
            receipt.get("source_main_tag") != SOURCE_MAIN_TAG or
            not isinstance(receipt.get("source_detail_tag"), str) or
            re.fullmatch(r"mvl-track-[0-9]{2,3}",
                         receipt["source_detail_tag"]) is None):
        raise ValueError("source capture fixture or original frame tags missing")
    ppu = receipt.get("source_ppu_sha256")
    if not isinstance(ppu, dict) or set(ppu) != SOURCE_PPU_FIELDS or any(
            not isinstance(v, str) or
            re.fullmatch(r"[0-9a-f]{64}", v) is None
            for v in ppu.values()):
        raise ValueError("source PPU VRAM/CGRAM digest receipt incomplete")
    if source_dump_dir is not None:
        verify_local_source_ppu_dumps(receipt, source_dump_dir)
    if set(paths) != set(EXPECTED):
        raise ValueError("supply all four named PNG source sheets")
    hashes = receipt.get("asset_png_sha256")
    dims = receipt.get("output_dimensions")
    if not isinstance(hashes, dict) or not isinstance(dims, dict):
        raise ValueError("source receipt lacks image metadata")
    checked = {}
    for name, (width, height) in EXPECTED.items():
        path = paths[name]
        if path.stat().st_size > MAX_PNG_BYTES:
            raise ValueError(f"{name}: source PNG too large")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if (not isinstance(hashes.get(name), str) or
                digest != hashes[name] or dims.get(name) != [width, height]):
            raise ValueError(f"{name}: image hash or dimensions disagree with receipt")
        rgba = read_png_rgba(path, width, height)
        if any(a not in (0, 255) for a in rgba[3::4]):
            raise ValueError(f"{name}: invalid intermediate alpha")
        if not any(a == 255 for a in rgba[3::4]):
            raise ValueError(f"{name}: completely transparent original asset")
        checked[name] = {"png_sha256": digest, "pixels": width * height}
    # The source exporter specifically duplicates numeral zero as letter O,
    # H-flips '(' as ')' and emits an entirely empty space slot. Check these
    # invariants before a host labels the detail atlas "source-verified."
    small = read_png_rgba(paths["detail"], *EXPECTED["detail"])
    pitch = 360 * 4

    def detail_cell(n: int) -> tuple[bytes, ...]:
        return tuple(small[y * pitch + n * 32:y * pitch + (n + 1) * 32]
                     for y in range(16))

    if detail_cell(0) != detail_cell(35):
        raise ValueError("detail: zero/O duplicated original glyph does not match")
    left, right = detail_cell(38), detail_cell(43)
    for a, b in zip(left, right):
        if b != b"".join(a[x:x + 4] for x in range(28, -1, -4)):
            raise ValueError("detail: ')' is not a horizontal mirror of '('")
    if not any(any(x for x in line[3::4]) for line in detail_cell(38)):
        raise ValueError("detail: source parenthesis glyph is blank")
    if any(any(v for v in line) for line in detail_cell(44)):
        raise ValueError("detail: original blank-space glyph has ink")
    cursor = read_png_rgba(paths["cursor"], *EXPECTED["cursor"])
    for n in range(16):
        has_ink = any(cursor[(y * 624 + n * 39 + x) * 4 + 3] == 255
                      for y in range(39) for x in range(39))
        if not has_ink:
            raise ValueError(f"cursor: source phase {n} is blank")
    return {
        "source_bundle_verified": True,
        "local_ppu_dump_hashes_verified": source_dump_dir is not None,
        "rom_identity_verified": False,
        "reference_only": True,
        "distribution_approved": False,
        "final_native_capture_approved": False,
        "assets": checked,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", required=True, type=Path)
    ap.add_argument("--source-dumps", type=Path,
                    help="Optional private PPU dump directory: rehash exact "
                         "main/detail VRAM and CGRAM bytes (no ROM approval)")
    for key in EXPECTED:
        ap.add_argument("--" + key, required=True, type=Path)
    args = ap.parse_args()
    receipt = json.loads(args.bundle.read_text())
    result = verify_source_art_bundle(
        receipt, {key: getattr(args, key) for key in EXPECTED},
        source_dump_dir=args.source_dumps)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
