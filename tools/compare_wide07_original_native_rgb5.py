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
import re
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



MEMORY_COMPONENT_SIZES = {
    "wram.bin": 131072, "sram.bin": 8192, "vram.bin": 65536,
    "cgram.bin": 512, "oam.bin": 544,
}
SRAM_MIRROR_OFFSET = 0x0E6B


def compare_memory(tag: str, original: dict[str, bytes],
                   native: dict[str, bytes], original_observation: dict,
                   native_observation: dict) -> dict:
    """Rehash full raw state; compare without masking or granting acceptance."""
    original_components, fixed_components, wide_components = {}, {}, {}
    result = {}
    for ext, size in MEMORY_COMPONENT_SIZES.items():
        old_path = f"evidence/frames/{tag}.{ext}"
        fix_path = f"evidence/original/{tag}.{ext}"
        wide_path = f"evidence/16x9/{tag}.{ext}"
        if any(path not in origin for path, origin in
               ((old_path, original), (fix_path, native), (wide_path, native))):
            raise ValueError("Incomplete genuine original/native memory capture: " + ext)
        ref, fixed, wide = original[old_path], native[fix_path], native[wide_path]
        if len(ref) != size or len(fixed) != size or len(wide) != size:
            raise ValueError("Unexpected guest memory image size: " + ext)
        field = {"wram.bin": "wram_sha256", "sram.bin": "sram_sha256"}.get(ext)
        if field and sha(ref) != original_observation["checkpoints"][tag][field]:
            raise ValueError("Original guest memory disagrees with source receipt: " + ext)
        if ext == "wram.bin":
            witness = native_observation["result"][tag]["producer"]
            if (sha(fixed) != witness["original"]["wram_sha256"] or
                    sha(wide) != witness["16x9"]["wram_sha256"]):
                raise ValueError("Native guest WRAM disagrees with producer receipt")
        differences = [i for i, (a, b) in enumerate(zip(ref, fixed)) if a != b]
        native_differences = sum(a != b for a, b in zip(fixed, wide))
        result[ext] = {
            "bytes": size, "original_native_differing_bytes": len(differences),
            "native_fixed_wide_differing_bytes": native_differences,
            "first_differences": [
                {"offset": i, "original": ref[i], "native": fixed[i]}
                for i in differences[:24]],
            "original_sha256": sha(ref),
            "native_fixed_sha256": sha(fixed),
            "native_wide_sha256": sha(wide),
        }
        original_components[ext], fixed_components[ext], wide_components[ext] = ref, fixed, wide
    ref_wram, native_wram = original_components["wram.bin"], fixed_components["wram.bin"]
    ref_sram, native_sram = original_components["sram.bin"], fixed_components["sram.bin"]
    mirrored = []
    for i, (a, b) in enumerate(zip(ref_wram, native_wram)):
        j = i + SRAM_MIRROR_OFFSET
        if (a != b and j < len(ref_sram) and ref_sram[j] == a and native_sram[j] == b):
            mirrored.append({"wram_offset": i, "sram_offset": j})
    result["observed_plus_0x0e6b_wram_sram_correspondence"] = mirrored
    result["wram_sram_mirroring_causally_proven"] = False
    result["original_native_emulator_clocks_equated"] = False
    return result



MARGIN_TRACE_PATTERN = re.compile(
    r"^URWS_SHADOW_EXT provider=course-runtime margin=48 "
    r"column=([2-6]) camx=(\d+) edge=([0-9A-F]+) "
    r"count=(\d+) payload=([0-9A-F]+) camy=(\d+) "
    r"finex=(\d+) finey=(\d+)(?:\s.*)?$"
)


def source_course_tile(wram: bytes, cell_x: int, cell_y: int) -> int | None:
    """Recover an original Snes9x bank-$7F course tile word, without native RAM.

    The original game stores coarse 64-pixel sectors and fine 16-pixel tile
    records in bank $7F. This is the documented source table format, not a
    rendering oracle or proof that a word was presented on a screen.
    """
    if len(wram) != 131072:
        raise ValueError("Actual full 128-KiB original WRAM required")
    def word(offset: int) -> int:
        if not 0 <= offset < len(wram) - 1:
            raise ValueError("Course table pointer outside original source RAM")
        return wram[offset] | (wram[offset + 1] << 8)
    coarse_w, coarse_h = word(0x04F1), word(0x04F3)
    if (not coarse_w or not coarse_h or cell_x < 0 or cell_y < 0 or
            cell_x >= 4 * coarse_w or cell_y >= 4 * coarse_h):
        return None
    coarse_address = 0x000F + 2 * ((cell_y >> 2) * coarse_w + (cell_x >> 2))
    if coarse_address > 0xFFFE:
        return None
    record = word(0x10000 + coarse_address)
    fine_address = (0x800F + 32 * record +
                    2 * (((cell_y & 3) * 4) + (cell_x & 3)))
    if fine_address > 0xFFFE:
        return 0
    return word(0x10000 + fine_address)


def compare_source_margin_words(tag: str, original: dict[str, bytes],
                                native: dict[str, bytes]) -> dict:
    """Compare native offscreen source-word trace against actual original RAM.

    Same camera-X does not independently establish the same original/native
    frame, camera-Y, CPU clock, HDMA raster or resulting screen pixels.
    """
    raw = original[f"evidence/frames/{tag}.wram.bin"]
    log = native["evidence/16x9/moving-course-run.log"]
    if len(raw) != 131072 or len(log) > 2 * 1024 * 1024:
        raise ValueError("Incomplete source RAM or oversized native trace")
    camera_x = raw[0x0419] | (raw[0x041A] << 8)
    camera_y = raw[0x041D] | (raw[0x041E] << 8)
    rows = {}
    for line in log.decode("ascii").splitlines():
        match = MARGIN_TRACE_PATTERN.fullmatch(line)
        if not match or int(match.group(2)) != camera_x:
            continue
        column = int(match.group(1))
        if column in rows:
            raise ValueError("Duplicate native offscreen trace for source camera-X")
        count = int(match.group(4))
        payload = bytes.fromhex(match.group(5))
        if count != 16 or len(payload) != 2 * count:
            raise ValueError("Incorrect native margin tile-word payload")
        cam_y, cell_x, cell_y = map(int, match.group(6, 7, 8))
        actual = [int.from_bytes(payload[i:i + 2], "little")
                  for i in range(0, len(payload), 2)]
        expected = [source_course_tile(raw, cell_x, cell_y + i)
                    for i in range(count)]
        if any(item is None for item in expected):
            raise ValueError("Source course index absent for native reported edge")
        rows[column] = {
            "source_camera_x": camera_x, "source_camera_y": camera_y,
            "native_trace_camera_y": cam_y,
            "native_trace_cell_x": cell_x, "native_trace_cell_y": cell_y,
            "compared_words": count,
            "matching_words": sum(a == b for a, b in zip(actual, expected)),
            "first_differing_word": next(
                ({"row_offset": i, "original_source_word": expected[i],
                  "native_emitted_word": actual[i]}
                 for i in range(count) if actual[i] != expected[i]), None),
            "source_predicted_words_sha256":
                sha(b"".join(int(w).to_bytes(2, "little") for w in expected)),
            "native_emitted_words_sha256": sha(payload),
        }
    if set(rows) != {2, 3, 4, 5, 6}:
        raise ValueError("Missing original-camera native margin columns")
    return {
        "source_original_wram_sha256": sha(raw),
        "native_margin_log_sha256": sha(log),
        "source_original_camera_x": camera_x,
        "source_original_camera_y": camera_y,
        "columns": rows,
        "total_compared_words": sum(v["compared_words"] for v in rows.values()),
        "total_matching_words": sum(v["matching_words"] for v in rows.values()),
        "source_ppu_per_scanline_margin_pixels_proven": False,
        "exact_original_native_frame_registration_proven": False,
        "complete_wide07_qualified": False,
        "usa_course_credit": 0,
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


def analyze(original_zip: Path, native_zip: Path, *, require_memory: bool = False) -> dict:
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
    margin_trace_present = "evidence/16x9/moving-course-run.log" in native
    memory_witness = native.get("evidence/paired-native-guest-state.json")
    memory_present = memory_witness is not None
    if require_memory and not memory_present:
        raise ValueError("Required native guest memory witness is absent")
    memory_observation = json.loads(memory_witness) if memory_present else None
    if memory_present and (
            memory_observation.get("schema") != "ur-wide07-native-paired-full-guest-state/1"
            or memory_observation.get("source_sha") != nat["source_sha"]):
        raise ValueError("Native guest memory witness is not source-bound")
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
        if memory_present:
            comparison["memory"] = compare_memory(
                tag, original, native, orig, memory_observation)
            if margin_trace_present and tag != "ws-product-main-menu":
                comparison["original_source_offscreen_tile_words"] = (
                    compare_source_margin_words(tag, original, native))
        results[tag] = comparison
    if memory_present:
        a = results["ws-product-race"]["memory"]
        b = results["ws-product-after-scroll"]["memory"]
        stable = all(
            a[ext]["first_differences"] == b[ext]["first_differences"] and
            a[ext]["original_native_differing_bytes"] ==
                b[ext]["original_native_differing_bytes"]
            for ext in MEMORY_COMPONENT_SIZES
        )
    else:
        stable = None
    return {
        "native_memory_evidence_present": memory_present,
        "sampled_race_and_after_scroll_memory_difference_sets_stable": stable,
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
    p.add_argument("--require-memory", action="store_true")
    args = p.parse_args()
    result = json.dumps(analyze(args.original_zip, args.native_zip, require_memory=args.require_memory), indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(result, end="")
    else:
        if args.out.exists() or args.out.is_symlink():
            raise SystemExit("Refusing to overwrite preexisting comparison receipt")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(result, encoding="utf-8")


if __name__ == "__main__":
    main()
