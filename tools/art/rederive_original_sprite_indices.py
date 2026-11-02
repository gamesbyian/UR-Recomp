#!/usr/bin/env python3
"""Reproduce the numeric original-ROM 4bpp lookup from authenticated source PNGs.

Reads frozen original PNG/source-audit bytes without invoking an emulator.
Refuses ambiguous opaque palettes and cannot recover index-zero tile visitation.
Never associates a 4bpp index with a 1994 3D physical part.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import tempfile
from zipfile import ZipFile

try:
    from tools.art.racer_source_pixels import decode_rgba_png
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from racer_source_pixels import decode_rgba_png
    from no_replace_report import publish_text_once

REPORT_SHA = "b6f59fc5f9030b44ca9345bf308e5df83901f8b9534a6f33b215fa39f8e3079e"
MANIFEST_SHA = "e26193f767d22280ab65b0549e707fa05ef246a903a4cebd47411f75726dc66e"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
REGISTRY_SHA = "05372395d04d5403c7b80859c171f06d754f1322a676d66f4ce5d7b3aec948ad"
SCHEMA = "UR-ART4K-SOURCE-RGBA-TO-4BPP-INDEX-LOOKUP/1"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def reconstruct(rgba: bytes, palette: dict, expected: str) -> bytes:
    if (not isinstance(rgba, bytes) or len(rgba) != 64 * 64 * 4 or
        not re.fullmatch(r"[0-9a-f]{64}", expected) or
        not isinstance(palette, dict) or not palette or
        any(not re.fullmatch(r"[0-9a-f]{6}", k) or type(v) is not int
            or not 1 <= v <= 15 for k, v in palette.items()) or
        len(set(palette.values())) != len(palette)):
        raise ValueError("invalid original 4bpp palette/raster identity")
    plane = bytearray(4096)
    for q in range(4096):
        offset = 4 * q
        r, g, b, a = rgba[offset:offset + 4]
        if a == 0:
            continue
        if a != 255:
            raise ValueError("nonbinary source alpha")
        colour = f"{r:02x}{g:02x}{b:02x}"
        if colour not in palette:
            raise ValueError("original RGB cannot be inverted to a unique index")
        plane[q] = palette[colour]
    if digest(plane) != expected:
        raise ValueError("reconstructed index map does not match original ROM hash")
    return bytes(plane)


def build(source_zip: Path, index_report: Path) -> dict:
    report_bytes = index_report.read_bytes()
    if digest(report_bytes) != REPORT_SHA:
        raise ValueError("full original-ROM census SHA mismatch")
    report = json.loads(report_bytes)
    if (report.get("original_USA_ROM_sha256") != ROM_SHA or
        report.get("canonical_original_source_corpus_sha256") != MANIFEST_SHA or
        report.get("original_registry_sha256") != REGISTRY_SHA or
        report.get("registered_original_representations") != 59 or
        report.get("unique_source_RGBA_images") != 41 or
        report.get("unique_source_binary_silhouettes") != 35 or
        report.get("same_rgba_with_multiple_index_planes") != 0 or
        report.get("same_binary_mask_with_multiple_index_planes") != 0 or
        report.get("source_index_to_1994_physical_part_correspondence_verified") is not False):
        raise ValueError("source identity / 2D evidence class changed")
    rows = report["per_original_representation"]
    if len(rows) != 59:
        raise ValueError("expected 59 registered originals")
    ids = {r["registered_original_representation_id"] for r in rows}
    if len(ids) != 59:
        raise ValueError("duplicate source registration")
    with ZipFile(source_zip) as z:
        manifest_raw = z.read("source-corpus.json")
        if digest(manifest_raw) != MANIFEST_SHA:
            raise ValueError("source manifest SHA mismatch")
        manifest = json.loads(manifest_raw)
        sources = manifest["source_representations"]
        if (set(sources) != ids or manifest["source_rom_sha256"] != ROM_SHA or
            manifest["source_registry_sha256"] != REGISTRY_SHA):
            raise ValueError("source corpus/registry is not identical")
        indexed = {}
        representations = {}
        shapes = defaultdict(set)
        with tempfile.TemporaryDirectory(prefix="ur-4bpp-source-") as tmp:
            target = Path(tmp) / "original.png"
            for row in rows:
                identity = row["registered_original_representation_id"]
                ref = sources[identity]
                name = ref["local_file"]
                if not re.fullmatch(r"stock/source-[0-9a-f]{64}\.png", name):
                    raise ValueError("unsafe source ZIP entry")
                data = z.read(name)
                if digest(data) != ref["local_png_sha256"]:
                    raise ValueError("original source PNG SHA mismatch")
                target.write_bytes(data)
                w, h, rgba, png_sha = decode_rgba_png(target)
                if ((w, h) != (64, 64) or png_sha != ref["local_png_sha256"] or
                    digest(rgba) != row["source_rgba_sha256"] or
                    digest(rgba[3::4]) != ref["source_alpha_sha256"] or
                    digest(bytes(int(a != 0) for a in rgba[3::4])) != row["source_binary_mask_sha256"] or
                    ref["source_binary_mask_sha256"] != row["source_binary_mask_sha256"] or
                    ref["source_rgba_sha256"] != row["source_rgba_sha256"]):
                    raise ValueError("original PNG/alpha/source hash mismatch")
                mapping = {}
                for key, item in row["palette_index_census"]["opaque_palette_indices"].items():
                    n = int(key)
                    colour = item["source_rgba8"]
                    if (type(item["original_4bpp_palette_index"]) is not int or
                        n != item["original_4bpp_palette_index"] or not 1 <= n <= 15 or
                        len(colour) != 4 or colour[3] != 255):
                        raise ValueError("invalid source palette index")
                    rgb = bytes(colour[:3]).hex()
                    if rgb in mapping:
                        raise ValueError("opaque palette RGB collision")
                    mapping[rgb] = n
                plane = reconstruct(rgba, mapping, row["original_4bpp_index_plane_sha256"])
                for key, item in row["palette_index_census"]["opaque_palette_indices"].items():
                    if plane.count(int(key)) != item["opaque_source_pixels"]:
                        raise ValueError("indexed pixel count differs from real-ROM census")
                candidate = {
                    "original_4bpp_index_plane_sha256": digest(plane),
                    "source_binary_mask_sha256": row["source_binary_mask_sha256"],
                    "palette_rgb_to_index": dict(sorted(mapping.items())),
                }
                previous = indexed.setdefault(row["source_rgba_sha256"], candidate)
                if previous != candidate:
                    raise ValueError("same source RGBA has two index definitions")
                representations[identity] = row["source_rgba_sha256"]
                shapes[row["source_binary_mask_sha256"]].add(digest(plane))
    if len(indexed) != 41 or len(shapes) != 35 or any(len(g) != 1 for g in shapes.values()):
        raise ValueError("source index equivalence groups no longer match")
    return {
        "schema": SCHEMA,
        "authenticated_full_index_report_sha256": REPORT_SHA,
        "original_usa_rom_sha256": ROM_SHA,
        "original_source_manifest_sha256": MANIFEST_SHA,
        "original_source_registry_sha256": REGISTRY_SHA,
        "source_images_verified": 41,
        "unique_index_planes_verified": 35,
        "original_3d_part_identity_verified": False,
        "original_live_ppu_timing_verified": False,
        "owner_likeness_approved": False,
        "representations": dict(sorted(representations.items())),
        "rgba_to_index": dict(sorted(indexed.items())),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-zip", type=Path, required=True)
    ap.add_argument("--index-report", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--verify-committed", type=Path)
    args = ap.parse_args()
    result = build(args.source_zip, args.index_report)
    if args.verify_committed and json.loads(args.verify_committed.read_text()) != result:
        raise ValueError("committed immutable 4bpp index lookup differs from rederivation")
    publish_text_once(args.out, json.dumps(result, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
