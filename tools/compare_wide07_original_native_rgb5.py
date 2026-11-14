#!/usr/bin/env python3
"""Compare real USA Snes9x vs native fixed/wide course raster checkpoints.

Accept only independently downloaded, source-bound GitHub Actions archives.
Same scripted checkpoint labels are NOT absolute emulator-frame alignment.
SNES RGB5 comparisons here are a bounded visual observation, never a
45-course qualification, audio parity, or original widened-margin oracle.
No third-party image dependencies are required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zipfile
from pathlib import Path

TAGS = ("ws-product-main-menu", "ws-product-race", "ws-product-after-scroll")
SCHEMA = "ur-wide07-usa-original-native-rgb5-checkpoint-comparison/1"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bmp24(data: bytes) -> tuple[int, int, list[tuple[int, int, int]]]:
    if len(data) < 54 or data[:2] != b"BM":
        raise ValueError("Expected a complete Windows 24-bit BMP")
    size, offset = struct.unpack_from("<I", data, 2)[0], struct.unpack_from("<I", data, 10)[0]
    dib_size, width, height, planes, bpp, comp = struct.unpack_from("<IiiHHI", data, 14)
    if (size != len(data) or dib_size != 40 or planes != 1 or bpp != 24
            or comp != 0 or not (0 < width <= 512 and 0 < abs(height) <= 512)
            or offset != 54):
        raise ValueError("Unexpected BMP header/dimensions/codec")
    stride = ((width * 3 + 3) // 4) * 4
    if len(data) != offset + stride * abs(height):
        raise ValueError("Truncated or oversized BMP pixel data")
    pixels: list[tuple[int, int, int]] = []
    for y in range(abs(height)):
        row_index = y if height < 0 else abs(height) - 1 - y
        begin = offset + row_index * stride
        for x in range(width):
            b, g, r = data[begin + x * 3:begin + x * 3 + 3]
            pixels.append((r, g, b))
    return width, abs(height), pixels


def crop_center(width: int, height: int, pixels: list[tuple[int, int, int]]
                ) -> list[tuple[int, int, int]]:
    if (width, height) == (256, 224):
        return pixels
    if (width, height) != (342, 224):
        raise ValueError("Expected a 256- or 342-wide course framebuffer")
    return [pixel for y in range(height)
            for pixel in pixels[y * width + 43:y * width + 43 + 256]]


def high5(pixel: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(channel >> 3 for channel in pixel)


def blue_overlay(pixel: tuple[int, int, int]) -> bool:
    r, g, b = pixel
    return b > 240 and r < 130 and g < 130


def compare_images(original: list[tuple[int, int, int]],
                   fixed: list[tuple[int, int, int]],
                   wide: list[tuple[int, int, int]]) -> dict:
    if not len(original) == len(fixed) == len(wide) == 256 * 224:
        raise ValueError("Expected three 256x224 framebuffer views")
    rgb5_diff = [i for i, (o, n) in enumerate(zip(original, fixed))
                 if high5(o) != high5(n)]
    native_diff = sum(high5(a) != high5(b) for a, b in zip(fixed, wide))
    rgb8_diff = sum(a != b for a, b in zip(original, fixed))
    maximum = max(abs(a[c] - b[c]) for a, b in zip(original, fixed) for c in range(3))
    original_blue = [blue_overlay(p) for p in original]
    native_blue = [blue_overlay(p) for p in fixed]
    blue_xor = [a != b for a, b in zip(original_blue, native_blue)]
    differing_set = set(rgb5_diff)
    shifted_native = [False] * (256 * 224)
    shifted_native[256:] = native_blue[:-256]
    return {
        "pixels": 256 * 224,
        "rgb5_equal": 256 * 224 - len(rgb5_diff),
        "rgb5_differing": len(rgb5_diff),
        "native_fixed_vs_wide_center_rgb5_differing": native_diff,
        "rgb8_differing": rgb8_diff,
        "max_absolute_rgb8_channel_delta": maximum,
        "first_rgb5_differences": [
            {"x": i % 256, "y": i // 256} for i in rgb5_diff[:10]],
        "blue_overlay_xor_exactly_covers_rgb5_differences":
            blue_xor == [i in differing_set for i in range(256 * 224)],
        "blue_overlay_source_pixels": sum(original_blue),
        "blue_overlay_native_pixels": sum(native_blue),
        "blue_overlay_mask_shift_down_one_residual_pixels":
            sum(a != b for a, b in zip(original_blue, shifted_native)),
    }


def archive(path: Path) -> tuple[str, dict[str, bytes]]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 128 * 1024 * 1024:
        raise ValueError("Expected regular bounded artifact archive")
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate member in artifact")
        wanted = [name for name in names if name.startswith("evidence/")
                  or name == "execution-receipt.json"]
        if any(z.getinfo(name).file_size > 2 * 1024 * 1024 for name in wanted):
            raise ValueError("Unbounded experiment evidence member")
        return sha(path.read_bytes()), {name: z.read(name) for name in wanted}


def analyze(original_zip: Path, native_zip: Path) -> dict:
    original_zip_sha, original = archive(original_zip)
    native_zip_sha, native = archive(native_zip)
    orig = json.loads(original["evidence/original-usa-ppu-observation.json"])
    nat = json.loads(native["evidence/matched-centre-observation.json"])
    orig_exec = json.loads(original["execution-receipt.json"])
    nat_exec = json.loads(native["execution-receipt.json"])
    if (orig["schema"] != "ur-wide07-genuine-original-usa-ppu-capture/1"
            or nat["schema"] != "ur-wide07-hosted-fixed-wide-matched-frames/1"
            or orig["source_sha"] != orig_exec["source_sha"]
            or nat["source_sha"] != nat_exec["source_sha"]
            or not orig["original_snes9x_executed"]
            or orig_exec["execution_step_outcome"] != "success"
            or nat_exec["execution_step_outcome"] != "success"):
        raise ValueError("Missing original/native source-bound successful provenance")
    results = {}
    for tag in TAGS:
        original_bytes = original["evidence/frames/" + tag + ".fb.bmp"]
        fixed_bytes = native["evidence/original/" + tag + ".fb.bmp"]
        wide_bytes = native["evidence/16x9/" + tag + ".fb.bmp"]
        if sha(original_bytes) != orig["checkpoints"][tag]["framebuffer_sha256"]:
            raise ValueError("Original emulator BMP disagrees with its receipt")
        if tag in nat["frame_pairs"]:
            if (sha(fixed_bytes) != nat["frame_pairs"][tag]["original_sha256"]
                    or sha(wide_bytes) != nat["frame_pairs"][tag]["wide_sha256"]):
                raise ValueError("Native BMP disagrees with its receipt")
        ow, oh, o = bmp24(original_bytes)
        fw, fh, f = bmp24(fixed_bytes)
        ww, wh, w = bmp24(wide_bytes)
        if (ow, oh) != (256, 224) or (fw, fh) != (256, 224):
            raise ValueError("Invalid original or fixed original-view dimensions")
        comparison = compare_images(o, f, crop_center(ww, wh, w))
        comparison.update({
            "original_script_frame": orig["checkpoints"][tag]["metadata"]["frame"],
            "native_script_frame": nat["frame_pairs"].get(tag, {}).get("guest_frame"),
            "original_bmp_sha256": sha(original_bytes),
            "native_fixed_bmp_sha256": sha(fixed_bytes),
            "native_wide_bmp_sha256": sha(wide_bytes),
        })
        results[tag] = comparison
    return {
        "schema": SCHEMA,
        "original_archive_sha256": original_zip_sha,
        "native_archive_sha256": native_zip_sha,
        "original_source_sha": orig["source_sha"],
        "native_source_sha": nat["source_sha"],
        "checkpoints": results,
        "frame_alignment": "same deterministic script checkpoints; exact emulator clocks not independently registered",
        "original_widened_margin_oracle": False,
        "complete_usa_course_accepted": False,
        "usa_course_credit": 0,
        "windows_gate_credit": 0,
        "next_experiment": "Register source/native scene frame phase using original WRAM/PPU/HDMA and then resolve one-pixel blue directional-arrow offset and original world-tile margin edge provenance.",
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-zip", type=Path, required=True)
    p.add_argument("--native-zip", type=Path, required=True)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    result = json.dumps(analyze(args.original_zip, args.native_zip), indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(result, end="")
    else:
        if args.out.exists() or args.out.is_symlink():
            raise SystemExit("Refusing to overwrite preexisting comparison receipt")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(result, encoding="utf-8")


if __name__ == "__main__":
    main()
