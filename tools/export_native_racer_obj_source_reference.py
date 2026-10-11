#!/usr/bin/env python3
"""Lossless native original-PPU OBJ reference, never a fabricated HD asset.

Consumes an independently native-validated source OBJ PAM and report. Emits
a cropped, unresampled RGBA PNG for a genuinely opaque native sprite and a
machine-readable source provenance sidecar. An all-transparent native source
creates NO invented art image and records an honest source-empty negative.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

try:
    from tools.check_baldosa_wide_single_slot_source import (
        read_source, HEADER, WIDTH, HEIGHT,
    )
except ModuleNotFoundError:
    from check_baldosa_wide_single_slot_source import (
        read_source, HEADER, WIDTH, HEIGHT,
    )


def chunk(name: bytes, data: bytes) -> bytes:
    if len(name) != 4:
        raise ValueError("invalid PNG chunk name")
    return (
        struct.pack(">I", len(data)) + name + data +
        struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)
    )


def lossless_png(data: bytes, width: int, height: int) -> bytes:
    if not (1 <= width <= WIDTH and 1 <= height <= HEIGHT) or (
        len(data) != width * height * 4
    ):
        raise ValueError("non-native or malformed cropped source reference")
    raw = b"".join(
        b"\x00" + data[y * width * 4:(y + 1) * width * 4]
        for y in range(height)
    )
    return (
        b"\x89PNG\r\n\x1a\n" +
        chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) +
        chunk(b"IDAT", zlib.compress(raw, level=9)) +
        chunk(b"IEND", b"")
    )


def make_reference(source_path: Path, report_path: Path,
                   slot: int = 97, frame: int = 2208) -> tuple[dict, bytes | None]:
    if slot not in (97, 98, 99) or frame != 2208:
        raise ValueError("only genuine original source 1P OAM slots97..99/frame2208 are in scope")
    native = read_source(source_path, slot)
    if native["guest_frame"] != frame:
        raise ValueError("native source OBJ frame identity mismatch")
    proof = json.loads(report_path.read_text(encoding="utf-8"))
    if slot == 97:
        # Preserve the accepted isolated source-empty bottom slot97 report
        # contract. Never allow a top-slot pair report to forge this proof.
        if proof.get("status") != "native-1p-source-obj-slot97-frame2208-verified" or (
            proof.get("native_guest_crcs_identical") != 5447
        ) or proof.get("independent_one_x_four_x_source_image_pairs") != 7 or (
            proof.get("isolated_original_ppu_obj_slot") != slot
        ) or proof.get("guest_frame") != frame or (
            proof.get("no_remove_from_game") is not True
        ) or proof.get("widescreen_hd_replacement_admitted") is not False or (
            proof.get("actual_bg_window_final_winner_proven") is not False
        ):
            raise ValueError("native source OBJ provenance report does not authorize a reference")
        proven_source = proof.get("source_obj_alpha", {})
    else:
        # The top slot98/99 planes are captured by separate REAL 1P
        # guest processes. Require the five-way CRC and all full 342-wide
        # Original source raster witnesses, and exact per-slot identity.
        # The two per-slot records contain original PPU source RGBA,
        # not guessed semantics or screen geometry. No final BG priority
        # or authored HD admission is permitted by this report.
        if proof.get("status") != "native-1p-paired-top-oam-source-truth" or (
            proof.get("native_guest_frame") != frame
        ) or proof.get("native_original_guest_crc_identical") != 5447 or (
            proof.get("native_1x_and_4x_source_frames_identical") != 7
        ) or proof.get("independent_original_guest_processes") != 5 or (
            proof.get("no_sprite_removal_or_guest_mutation") is not True
        ) or proof.get("source_slot_emission_accepted") is not True or (
            proof.get("individual_final_bg_or_obj_priority_accepted") is not False
        ) or proof.get("authored_hd_or_wide_replacement_accepted") is not False or (
            proof.get("windows_beta_accepted") is not False
        ):
            raise ValueError("native TOP source OBJ provenance report does not authorize a reference")
        records = proof.get("original_top_slot98_and_slot99_sources")
        if not isinstance(records, list) or len(records) != 2 or (
            [rec.get("original_oam_slot") for rec in records
             if isinstance(rec, dict)] != [98, 99]
        ) or any(
            rec.get("original_1x_and_4x_remained_pixel_identical") is not True
            for rec in records
        ):
            raise ValueError("original top source slot attribution is incomplete or forged")
        selected = next(rec for rec in records if rec["original_oam_slot"] == slot)
        proven_source = selected.get("native_source", {})
        if selected.get("rgba_sha256") != native["source_sha256"]:
            raise ValueError("native top isolated OBJ source digest is inconsistent")

    if not isinstance(proven_source, dict) or (
        proven_source.get("source_sha256") != native["source_sha256"]
    ) or proven_source.get("bbox") != native["bbox"] or (
        proven_source.get("top_opaque_source_pixels") != native["top_opaque_source_pixels"]
    ) or proven_source.get("bottom_opaque_source_pixels") != native["bottom_opaque_source_pixels"]:
        raise ValueError("native isolated source alpha differs from authoritative PPU evidence")
    content = source_path.read_bytes()
    if not content.startswith(HEADER) or len(content) != len(HEADER) + WIDTH * HEIGHT * 4:
        raise ValueError("native source PAM damaged")
    pixels = content[len(HEADER):]
    bbox = native["bbox"]
    total_alpha = native["top_opaque_source_pixels"] + native["bottom_opaque_source_pixels"]
    png = None
    crop_sha = None
    crop_dims = None
    colors: dict[str, int] = {}
    if total_alpha:
        left, top, right, bottom = bbox
        if not (0 <= left <= right < WIDTH and 0 <= top <= bottom < HEIGHT):
            raise ValueError("unbounded real PPU source-OBJ rectangle")
        w, h = right - left + 1, bottom - top + 1
        cropped = b"".join(
            pixels[(y * WIDTH + left) * 4:(y * WIDTH + right + 1) * 4]
            for y in range(top, bottom + 1)
        )
        if len(cropped) != w * h * 4:
            raise ValueError("cropped actual source pixels are incomplete")
        visible = 0
        for i in range(0, len(cropped), 4):
            if not cropped[i + 3]:
                continue
            visible += 1
            label = cropped[i:i + 4].hex().upper()
            colors[label] = colors.get(label, 0) + 1
        if visible != total_alpha:
            raise ValueError("cropped pixel alpha does not match native source count")
        png = lossless_png(cropped, w, h)
        crop_sha = hashlib.sha256(cropped).hexdigest()
        crop_dims = [w, h]
    elif bbox != [WIDTH, HEIGHT, -1, -1]:
        raise ValueError("native empty source improperly reports nonempty bounding box")
    return ({
        "schema_version": 1,
        "status": "original-ppu-source-reference" if total_alpha else "source-empty-no-image",
        "native_isolated_obj_slot": slot,
        "actual_guest_frame": frame,
        "native_source_logical_frame": [WIDTH, HEIGHT],
        "native_original_source_rgba_sha256": native["source_sha256"],
        "native_original_source_bbox": bbox,
        "native_original_source_opaque_pixels": total_alpha,
        "cropped_rgba_dimensions": crop_dims,
        "cropped_raw_rgba_sha256": crop_sha,
        "lossless_png_sha256": hashlib.sha256(png).hexdigest() if png else None,
        "original_visible_rgba_color_counts": dict(sorted(colors.items())),
        "png_rendered_from_original_source": png is not None,
        "new_4x_authored_art_approved": False,
        "final_bg_window_priority_proven": False,
        "widescreen_hd_admission": False,
        "limits": (
            "Pixel-perfect original source OBJ crop *before* native BG/window "
            "priority, with original RGBA and zero inferred pixels. This is "
            "NOT an HD racer or permission to remove an original source slot."
        ),
    }, png)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-file", type=Path, required=True)
    p.add_argument("--validated-report", type=Path, required=True)
    p.add_argument("--slot", type=int, choices=(97, 98, 99), default=97)
    p.add_argument("--output-prefix", type=Path, required=True)
    a = p.parse_args()
    result, image = make_reference(a.source_file, a.validated_report, slot=a.slot)
    dest = a.output_prefix
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.with_suffix(".json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output = dest.with_suffix(".png")
    if image is not None:
        output.write_bytes(image)
    elif output.exists():
        output.unlink()  # Never leave a stale PNG claiming an empty source.
    print("UR_RACER_NATIVE_OBJ_REFERENCE "
          f"status={result['status']} opaque={result['native_original_source_opaque_pixels']} "
          f"cropped={result['cropped_rgba_dimensions']} release_art=0")


if __name__ == "__main__":
    main()
