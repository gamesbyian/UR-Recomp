#!/usr/bin/env python3
"""Recover original rotating 32x32 Uniracers menu cursor source pixels.

Input: the actual 64 mvl-idle-* source PPU dumps produced by
tests/input/menu-visual-language.script. Reuse the established BG/OBJ
decoder and registered 16 tile addresses and palette, never draw synthetic
arrows or invent rotations. Output is an experimental source-bound atlas
and precise capture manifest, NOT an in-game cursor without native approval.

The source PPU dumps are not checked into Git. Require the canonical USA
ROM identity separately and retain dump SHA256 for independent correlation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import extract_menu_visual_language as mvl
from extract_racer_presentation_family import encode_png_rgba

REFERENCE = ROOT / "analysis/generated/menu-visual-language.json"
SOURCE = ROOT / "analysis/generated/racer-presentation-family.json"
ROM = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
SIDE = 32
SHADOW_OFFSET = 7
CANVAS = SIDE + SHADOW_OFFSET
FRAMES = 16


def rgba_color(cgram: bytes, index: int) -> tuple[int, int, int, int]:
    if len(cgram) != 512 or not 0 <= index < 256:
        raise ValueError("original CGRAM must have 256 2-byte colours")
    r, g, b = mvl.bgr555(cgram, index)
    return r, g, b, 255


def png_frame(rgba: bytes) -> bytes:
    if len(rgba) != CANVAS * CANVAS * 4:
        raise ValueError("original cursor RGBA frame must be 39x39")
    return encode_png_rgba(CANVAS, CANVAS, rgba)


def original_obj_base_word(dump: mvl.Dump, tile: int = 0) -> int:
    field = dump.fillram.get("2101")
    if not isinstance(field, str) or len(field) != 2:
        raise ValueError("missing exact $2101 OBJ name-base register")
    obsel = int(field, 16)
    if not 0 <= tile < 512:
        raise ValueError("invalid source OAM name table tile index")
    # SNES $2101 name-base bits select a 16 KiB-aligned block:
    # 0x2000 VRAM WORDS per step. This differs from the secondary-name
    # offset, which advances in 0x1000-word (8 KiB) increments.
    # Independent hardware spec: SNESdev OBJSEL / Fullsnes OBSEL; also
    # cross-checked against the source-grammar owner's OBJ decoder.
    base = (obsel & 7) * 0x2000
    if tile & 0x100:
        base += (((obsel >> 3) & 3) + 1) * 0x1000
    return base


def source_sprite_flips(d: mvl.Dump, sprite: dict) -> tuple[bool, bool]:
    """Read the actual OAM H/V attributes, not an inferred CHR rotation.

    The older first-party mvl.sprites() contract exposes tile, size and
    palette but may omit attr bit6/7. Resolve the exact visible OAM record
    with its high-table X and size bits. Ambiguity is a source failure.
    """
    if len(d.oam) != 544:
        raise ValueError("original OAM source must contain 544 bytes")
    matches = []
    for i in range(128):
        x, y, tile_low, attr = d.oam[4 * i:4 * i + 4]
        high = (d.oam[512 + i // 4] >> ((i % 4) * 2)) & 3
        x |= (high & 1) << 8
        if x >= 256:
            x -= 512
        tile = tile_low | ((attr & 1) << 8)
        if (x == sprite["x"] and y == sprite["y"] and
                tile == sprite["tile"] and
                ((attr >> 1) & 7) == sprite["palette"] and
                (high >> 1) == sprite["large"] and
                ((attr >> 4) & 3) == sprite["priority"]):
            matches.append((bool(attr & 0x40), bool(attr & 0x80)))
    if len(matches) != 1:
        raise ValueError("unmatched or ambiguous source OAM cursor flags")
    return matches[0]


def draw_sprite(d: mvl.Dump, sprite: dict, frame: bytearray,
                ox: int, oy: int) -> None:
    if len(d.vram) != 65536 or len(d.cgram) != 512:
        raise ValueError("wrong original PPU dump geometry")
    field = d.fillram.get("2101")
    if not isinstance(field, str) or len(field) != 2:
        raise ValueError("missing exact $2101 OBJ name-base register")
    obsel = int(field, 16)
    # OAM's "large" bit does not, by itself, prove a 32x32 sprite.
    # Source OBJ size pairs 1, 3 and 7 are the only large-32 modes.
    if (sprite["large"] != 1 or (obsel >> 5) not in (1, 3, 7) or
            not 0 <= sprite["tile"] < 512):
        raise ValueError("unsupported or non-source 32x32 cursor OBJ")
    horizontal_flip, vertical_flip = source_sprite_flips(d, sprite)
    for ty in range(4):
        for tx in range(4):
            # 32x32 OBJ subtiles advance on a 16-tile row; preserve the
            # upper name-table page and wrap only the low 8 tile bits.
            tile = (sprite["tile"] & 256) | (
                (sprite["tile"] + ty * 16 + tx) & 255)
            base_word = original_obj_base_word(d, tile)
            raster = mvl.tile_pixels(d.vram, base_word, tile & 255, 4)
            for py, row in enumerate(raster):
                for px, ci in enumerate(row):
                    if ci == 0:
                        continue
                    # H/V flip applies to the COMPLETE 32x32 sprite,
                    # not individually to each 8x8 CHR tile.
                    src_x = tx * 8 + px
                    src_y = ty * 8 + py
                    x = ox + (SIDE - 1 - src_x if horizontal_flip else src_x)
                    y = oy + (SIDE - 1 - src_y if vertical_flip else src_y)
                    if not 0 <= x < CANVAS or not 0 <= y < CANVAS:
                        raise ValueError("original cursor OBJ escaped review canvas")
                    loc = (y * CANVAS + x) * 4
                    frame[loc:loc+4] = bytes(rgba_color(
                        d.cgram, 128 + sprite["palette"] * 16 + ci))


def verify_source_frames(dumps: list[mvl.Dump], contract: dict) -> list[dict]:
    cursor = contract["cursor"]
    expected_tiles = cursor["spin_cycle_tiles"]
    if len(expected_tiles) != FRAMES or len(dumps) != 64:
        raise ValueError("unqualified source OBJ spin cycle or source dump count")
    if cursor["shadow_offset_px"] != [SHADOW_OFFSET, SHADOW_OFFSET] or \
       cursor["spin_period_frames"] != 32 or \
       cursor["spin_frames_per_tile"] != [2]:
        raise ValueError("original cursor spin/shadow timing changed")
    report = []
    for i, d in enumerate(dumps):
        if d.tag != f"mvl-idle-{i:03d}":
            raise ValueError("source frame sequence reordered or missing")
        sprites = mvl.sprites(d.oam)
        arrow = next((obj for obj in sprites if obj["palette"] == 7), None)
        shadow = next((obj for obj in sprites if obj["palette"] == 5), None)
        if not arrow or not shadow or \
           arrow["tile"] != expected_tiles[(i // 2) % FRAMES] or \
           arrow["x"] + SHADOW_OFFSET != shadow["x"] or \
           arrow["y"] + SHADOW_OFFSET != shadow["y"]:
            raise ValueError("source OAM cursor tile/pose/shadow mismatch")
        if [mvl.bgr555(d.cgram, 128 + 7 * 16 + j) for j in range(16)] != \
           cursor["arrow_palette_rgb"]:
            raise ValueError("original cursor palette drifted")
        arrow_flip = source_sprite_flips(d, arrow)
        shadow_flip = source_sprite_flips(d, shadow)
        if i % 2 and (arrow_flip != report[-1]["arrow_flip"] or
                      shadow_flip != report[-1]["shadow_flip"]):
            raise ValueError("two-frame source cursor hold changed OAM flipping")
        if i >= 32 and (arrow_flip != report[i - 32]["arrow_flip"] or
                        shadow_flip != report[i - 32]["shadow_flip"]):
            raise ValueError("second source cursor cycle OAM flips diverged")
        report.append({"frame": i, "tile": arrow["tile"],
                       "arrow_xy": [arrow["x"], arrow["y"]],
                       "shadow_xy": [shadow["x"], shadow["y"]],
                       "arrow_flip": arrow_flip,
                       "shadow_flip": shadow_flip})
    return report


def reconstruct(dumps: list[mvl.Dump], contract: dict) -> tuple[list[bytes], list[dict]]:
    records = verify_source_frames(dumps, contract)
    frames = []
    for phase in range(FRAMES):
        index = phase * 2
        d = dumps[index]
        sprites = mvl.sprites(d.oam)
        arrow = next(obj for obj in sprites if obj["palette"] == 7)
        shadow = next(obj for obj in sprites if obj["palette"] == 5)
        buffer = bytearray(CANVAS * CANVAS * 4)
        draw_sprite(d, shadow, buffer, SHADOW_OFFSET, SHADOW_OFFSET)
        draw_sprite(d, arrow, buffer, 0, 0)
        frames.append(bytes(buffer))
        records[index]["rgba_sha256"] = hashlib.sha256(buffer).hexdigest()
        records[index]["opaque_pixels"] = sum(
            buffer[j] != 0 for j in range(3, len(buffer), 4))
        if records[index]["opaque_pixels"] < 64:
            raise ValueError("unpopulated source OBJ sprite")
    if len({hashlib.sha256(frame).hexdigest() for frame in frames}) < 8:
        raise ValueError("original source cursor rotation unexpectedly static")
    return frames, records


def export(dirpath: Path, output: Path, manifest_path: Path) -> dict:
    expected = json.loads(REFERENCE.read_text(encoding="utf-8"))
    canonical = json.loads(SOURCE.read_text(encoding="utf-8"))["rom_sha256"]
    if hashlib.sha256(ROM.read_bytes()).hexdigest() != canonical:
        raise ValueError("canonical original USA ROM identity mismatch")
    dumps = mvl.series(dirpath, "idle")
    frames, records = reconstruct(dumps, expected)
    output.mkdir(parents=True, exist_ok=True)
    files = []
    for i, frame in enumerate(frames):
        image = png_frame(frame)
        dest = output / f"original-menu-cursor-phase-{i:02d}.png"
        dest.write_bytes(image)
        files.append({"phase": i, "filename": dest.name,
                      "png_sha256": hashlib.sha256(image).hexdigest(),
                      "rgba_sha256": hashlib.sha256(frame).hexdigest()})
    fingerprints = []
    for d in dumps:
        base = dirpath / d.tag
        fingerprints.append({
            "tag": d.tag,
            **{kind+"_sha256": hashlib.sha256(
                Path(f"{base}.{kind}.bin").read_bytes()).hexdigest()
               for kind in ("vram", "cgram", "oam")}
        })
    result = {
        "schema_version": 1,
        "status": "original OBJ review atlas; native integration and visual approval HOLD",
        "canonical_rom_sha256": canonical,
        "capture_script": "tests/input/menu-visual-language.script",
        "capture_backend": "snesref source dump; independently attest actual run",
        "source_contract": REFERENCE.relative_to(ROOT).as_posix(),
        "cursor_canvas": [CANVAS, CANVAS],
        "source_obj_geometry": [SIDE, SIDE],
        "shadow_xy": [SHADOW_OFFSET, SHADOW_OFFSET],
        "palette": "stock original OBJ palette 7 arrow + 5 shadow",
        "period_60hz_frames": 32,
        "records": records,
        "source_files": fingerprints,
        "generated_review_images": files,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(result, indent=2)+"\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    result = export(args.dump_dir, args.out_dir, args.manifest)
    print("ORIGINAL_CURSOR_RECOVERED phases=" +
          str(len(result["generated_review_images"])) +
          " sha_bound=1 admission=review_only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
