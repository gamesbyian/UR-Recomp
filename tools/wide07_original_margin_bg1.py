#!/usr/bin/env python3
"""Independently predict WIDE-07 opaque BG1 margin pixels from original USA RAM.

Input: two untouched original Snes9x/native GHA evidence ZIPs. The original
Snes9x's bank-$7F course tables, VRAM 4bpp characters, CGRAM colours and PPU
registers are the ONLY inputs to the prediction and camera calibration. Native
widescreen BMP pixels are consulted only AFTER the source-only calibration.

This proves neither transparent BG1 pixels (other layers), sprite ownership,
HDMA colour compositing, exact emulator frame clocks nor a complete USA course.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from compare_wide07_original_native_rgb5 import archive, bmp24, source_course_tile

TAGS = ("ws-product-race", "ws-product-after-scroll")
SOURCE_WIDTH, HEIGHT, WIDE_WIDTH, CROP = 256, 224, 342, 43
SCHEMA = "ur-wide07-original-usa-derived-bg1-margin-pixels/1"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def raw_word(memory: bytes, offset: int) -> int:
    if not 0 <= offset < len(memory) - 1:
        raise ValueError("out-of-range source word")
    return memory[offset] | memory[offset + 1] << 8


def source_scanline_scroll_stable(ppuw: bytes, frame: int) -> bool:
    """No original BG1 scroll, character or tilemap register changes in V1..224."""
    lines = ppuw.decode("ascii").splitlines()
    if not lines or lines[0] != "#frame\tvcounter\thcounter\taddr\tvalue\tsource":
        raise ValueError("original PPU write journal lacks authenticated format")
    watched = {"2105", "2107", "210B", "210D", "210E"}
    for line in lines[1:]:
        if line.startswith("#"):
            raise ValueError("truncated/ambiguous original PPU write journal")
        fields = line.split("\t")
        if len(fields) != 6 or int(fields[0]) != frame:
            raise ValueError("source PPU journal frame not bound")
        v = int(fields[1])
        if not 0 <= v <= 261:
            raise ValueError("source PPU journal beam outside frame")
        if 1 <= v <= 224 and fields[3] in watched:
            return False
    return True


def bg1_pixel(tileword: int, x: int, y: int, vram: bytes,
              cgram: bytes, char_base: int) -> tuple[int, int, int] | None:
    """Opaque 4bpp SNES Mode-1 16x16 BG1 sample, BGR555 to RGB5."""
    xx, yy = x & 15, y & 15
    if tileword & 0x4000:
        xx = 15 - xx
    if tileword & 0x8000:
        yy = 15 - yy
    glyph = (tileword & 0x3ff) + (xx >> 3) + ((yy >> 3) << 4)
    plane = (char_base * 2 + glyph * 32 + (yy & 7) * 2) & 0xffff
    bit = 7 - (xx & 7)
    index = sum(((vram[(plane + offset) & 0xffff] >> bit) & 1) << i
                for i, offset in enumerate((0, 1, 16, 17)))
    if index == 0:  # BG1 is transparent here: BG2/OBJ/colour math can own output.
        return None
    palette_index = 16 * ((tileword >> 10) & 7) + index
    colour = raw_word(cgram, palette_index * 2)
    return colour & 31, (colour >> 5) & 31, (colour >> 10) & 31


def calibrate_source_only(wram: bytes, vram: bytes, *, camera_x: int,
                          camera_y: int, scroll_x: int, scroll_y: int,
                          map_base: int) -> tuple[int, int, int]:
    """Use ORIGINAL PPU VRAM map for source course geometry; never native BMP.

    Search only 16-pixel tile offsets near the PPU-dictated fractional phase.
    A unique perfect match over the entire 256x224 source view is required.
    This refuses a convenient alignment chosen for a native margin picture.
    """
    fractional_x = (scroll_x - camera_x) % 16
    fractional_y = (scroll_y + 1 - camera_y) % 16
    matches = []
    # Each source BG1 cell spans 16x16 pixels. Check every world cell at
    # every source raster pixel, including rows and columns crossing a cell.
    for dx in (fractional_x - 32, fractional_x - 16, fractional_x,
               fractional_x + 16, fractional_x + 32):
        for dy in (fractional_y - 16, fractional_y, fractional_y + 16):
            correct = 0
            for y in range(HEIGHT):
                native_y = ((y + scroll_y + 1) & 511) // 16
                source_y = (camera_y + y + dy) // 16
                for x in range(SOURCE_WIDTH):
                    native_x = ((x + scroll_x) & 511) // 16
                    map_offset = 2 * (map_base + native_x + native_y * 32)
                    original_map_word = raw_word(vram, map_offset)
                    original_course_word = source_course_tile(
                        wram, (camera_x + x + dx) // 16, source_y)
                    correct += original_course_word == original_map_word
            if correct == SOURCE_WIDTH * HEIGHT:
                matches.append((dx, dy))
    if len(matches) != 1:
        raise ValueError(f"Original course/PPU map alignment ambiguous: {matches}")
    return matches[0][0], matches[0][1], SOURCE_WIDTH * HEIGHT


def compare_pixels(source_zip: Path, native_zip: Path) -> dict:
    original_hash, original = archive(source_zip)
    native_hash, native = archive(native_zip)
    ref = json.loads(original["evidence/original-usa-ppu-observation.json"])
    nat = json.loads(native["evidence/matched-centre-observation.json"])
    ref_receipt = json.loads(original["execution-receipt.json"])
    nat_receipt = json.loads(native["execution-receipt.json"])
    if (ref.get("schema") != "ur-wide07-genuine-original-usa-ppu-capture/1"
            or nat.get("schema") != "ur-wide07-hosted-fixed-wide-matched-frames/1"
            or ref.get("source_sha") != ref_receipt.get("source_sha")
            or nat.get("source_sha") != nat_receipt.get("source_sha")
            or ref_receipt.get("execution_step_outcome") != "success"
            or nat_receipt.get("execution_step_outcome") != "success"
            or not ref.get("original_snes9x_executed")):
        raise ValueError("authentic, successful source-bound producers required")
    results = {}
    for tag in TAGS:
        old = "evidence/frames/" + tag + "."
        new = "evidence/16x9/" + tag + "."
        wram = original[old + "wram.bin"]
        vram = original[old + "vram.bin"]
        cgram = original[old + "cgram.bin"]
        if any((len(wram) != 131072, len(vram) != 65536, len(cgram) != 512)):
            raise ValueError("original full WRAM/VRAM/CGRAM source missing")
        if sha(wram) != ref["checkpoints"][tag]["wram_sha256"]:
            raise ValueError("original WRAM disagrees with producer")
        if native[new + "vram.bin"] != vram or native[new + "cgram.bin"] != cgram:
            raise ValueError("original/native graphics RAM differs at source checkpoint")
        regs = json.loads(original[old + "regs.json"])
        bg = regs["ppu"]["bg"][0]
        if (regs["ppu"]["bgmode"] != 1 or bg["tile16"] != 1
                or bg["scsize"] != 0 or regs["ppu"]["inidisp"]["brightness"] != 15):
            raise ValueError("original BG1 mode/brightness unsupported")
        info = json.loads(original[old + "info.json"])
        if not source_scanline_scroll_stable(original[old + "ppuw.tsv"], info["frame"]):
            raise ValueError("visible original BG1 PPU scroll changed per scanline")
        map_base = int(bg["scbase"], 16)
        char_base = int(bg["namebase"], 16)
        camx = raw_word(wram, 0x419)
        camy = raw_word(wram, 0x41d)
        sx, sy = int(bg["hofs"]), int(bg["vofs"])
        dx, dy, words = calibrate_source_only(
            wram, vram, camera_x=camx, camera_y=camy,
            scroll_x=sx, scroll_y=sy, map_base=map_base)
        ow, oh, old_pixels = bmp24(original[old + "fb.bmp"])
        nw, nh, wide_pixels = bmp24(native[new + "fb.bmp"])
        if (ow, oh, nw, nh) != (SOURCE_WIDTH, HEIGHT, WIDE_WIDTH, HEIGHT):
            raise ValueError("source/native raster dimensions inconsistent")
        if sha(original[old + "fb.bmp"]) != ref["checkpoints"][tag]["framebuffer_sha256"]:
            raise ValueError("original framebuffer not authentic")
        if sha(native[new + "fb.bmp"]) != nat["frame_pairs"][tag]["wide_sha256"]:
            raise ValueError("native wide framebuffer not authentic")
        metrics = {}
        for region, left, right in (("left", 0, CROP),
                                    ("center", CROP, CROP + SOURCE_WIDTH),
                                    ("right", CROP + SOURCE_WIDTH, WIDE_WIDTH)):
            eligible = equal = 0
            first = []
            for y in range(HEIGHT):
                world_y = camy + y + dy
                for x in range(left, right):
                    source_x = x - CROP
                    world_x = camx + source_x + dx
                    tile = source_course_tile(wram, world_x // 16, world_y // 16)
                    if tile is None:
                        continue
                    prediction = bg1_pixel(tile, sx + source_x, sy + 1 + y,
                                           vram, cgram, char_base)
                    if prediction is None:
                        continue
                    observed = (old_pixels[y * SOURCE_WIDTH + source_x]
                                if region == "center" else wide_pixels[y * WIDE_WIDTH + x])
                    actual = tuple(v >> 3 for v in observed)
                    eligible += 1
                    if prediction == actual:
                        equal += 1
                    elif len(first) < 12:
                        first.append({"x_wide": x, "y": y,
                                      "original_bg1_rgb5": prediction,
                                      "observed_rgb5": actual})
            metrics[region] = {
                "source_predicted_opaque_bg1_pixels": eligible,
                "matching_rgb5_pixels": equal,
                "differing_rgb5_pixels": eligible - equal,
                "first_differences": first,
            }
        if not metrics["left"]["source_predicted_opaque_bg1_pixels"] or not metrics["right"]["source_predicted_opaque_bg1_pixels"]:
            raise ValueError("no opaque BG1 pixels in a margin; cannot claim test")
        results[tag] = {"source_calibration": {
            "original_ppu_vram_map_words_matching": words,
            "original_ppu_vram_map_words_compared": SOURCE_WIDTH * HEIGHT,
            "original_only_world_offset_x": dx,
            "original_only_world_offset_y": dy,
            "source_camera_x": camx, "source_camera_y": camy,
            "original_bg1_scroll_x": sx, "original_bg1_scroll_y": sy,
            "original_ppu_visible_bg1_scroll_stable": True,
            "original_wram_sha256": sha(wram),
            "original_vram_sha256": sha(vram),
            "original_cgram_sha256": sha(cgram),
        }, "regions": metrics}
    margin_compared = sum(results[tag]["regions"][s]["source_predicted_opaque_bg1_pixels"]
                          for tag in TAGS for s in ("left", "right"))
    margin_matching = sum(results[tag]["regions"][s]["matching_rgb5_pixels"]
                          for tag in TAGS for s in ("left", "right"))
    return {"schema": SCHEMA, "original_artifact_sha256": original_hash,
            "native_artifact_sha256": native_hash,
            "original_source_sha": ref["source_sha"],
            "native_source_sha": nat["source_sha"],
            "margin_source_predicted_opaque_bg1_pixels": margin_compared,
            "margin_matching_rgb5_pixels": margin_matching,
            "margin_differing_rgb5_pixels": margin_compared - margin_matching,
            "source_only_calibration": True,
            "transparent_bg1_or_other_layers_qualified": False,
            "frame_clock_and_live_snes_offscreen_raster_proven": False,
            "widescreen_qualified": False, "usa_course_credit": 0,
            "release_gate_credit": 0, "checkpoints": results}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip", type=Path, required=True)
    parser.add_argument("--native-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--require-margin-parity", action="store_true")
    args = parser.parse_args()
    report = compare_pixels(args.original_zip, args.native_zip)
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        if args.out.exists() or args.out.is_symlink():
            raise SystemExit("refusing overwrite of previous acceptance evidence")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output)
    else:
        print(output, end="")
    if args.require_margin_parity and report["margin_differing_rgb5_pixels"]:
        raise SystemExit("original-derived opaque BG1 margin pixel mismatch")


if __name__ == "__main__":
    main()
