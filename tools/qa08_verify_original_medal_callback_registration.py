#!/usr/bin/env python3
"""Exact original 2014 Snes9x medal painter-to-output callback verification.

Consumes two immutable original-source CI ZIPs, never an inferred native
frame or an emulator script written to change rendering. No ROM bytes shipped.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ORIGINAL_ZIP_SHA = "72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
PAINTER_ZIP_SHA = "8387c413d42cf8d2da2a61ba3ec67e8375394f938171dc4d73a3e4ba567920e4"
INPUT_SHA = "9c9072123a8eadceb7af228088a51bf074e362f81772500daf3ac83a382aa4f0"
PIXELS = ((207, 91), (205, 115), (205, 139), (225, 96), (225, 120))
FRAMES = (4031, 4175)
STAGES = ("OBJ", "BG:0", "BG:1", "FINAL")
STAGES_PATH = "qa08-original-medal/original-layer-stages.log"
CALLS_PATH = "qa08-original-medal/active-tile-candidates.log"
PAINTER_LOG = "qa08-original-medal/original.log"
LAYER = re.compile(
    r"^UR_QA08_ORIGINAL_MEDAL_LAYER frame=(\d+) range=(\d+),(\d+) "
    r"x=(\d+) y=(\d+) stage=(\w+) bg=(-?\d+) bgmode=(\d+) "
    r"depth=([0-9a-f]{2}) rgb565=([0-9a-f]{4}) "
    r"source_callback_proven=0 native_frame_proven=0$"
)
CALL = re.compile(
    r"^UR_QA08_ORIGINAL_ACTIVE_MEDAL_TILE frame=(\d+) y=(\d+) x=(\d+) "
    r"slot=(\d+) objname=([0-9a-f]+) palette=(\d+) priority=(\d+) "
    r"src_tile=([0-9a-f]+).* changed_z=([01]) changed_rgb=([01]) "
    r"original_guest_phase_proven=0$"
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def consumed_input(log: bytes) -> tuple[str, int]:
    lines = [x for x in log.decode("utf-8").splitlines() if x.startswith("[input] ")]
    return digest(("\n".join(lines) + "\n").encode()), len(lines)


def rgb565_to_rgb8(value: int) -> tuple[int, int, int]:
    """Same integer 5/6-bit expansion as the original Snes9x output."""
    r, g, b = (value >> 11) & 31, (value >> 5) & 63, value & 31
    return (r << 3 | r >> 2, g << 2 | g >> 4, b << 3 | b >> 2)


def verify(original: Path, painter: Path) -> dict:
    if digest(original.read_bytes()) != ORIGINAL_ZIP_SHA:
        raise ValueError("wrong original 263-callback archive")
    if digest(painter.read_bytes()) != PAINTER_ZIP_SHA:
        raise ValueError("wrong source-original sprite-painter archive")

    with zipfile.ZipFile(original) as o, zipfile.ZipFile(painter) as p:
        if o.testzip() is not None or p.testzip() is not None:
            raise ValueError("archive member CRC failed")
        manifest = json.loads(o.read("qa08-original-2p-fullroute.json"))
        if manifest["actual_callbacks_captured"] != 263 or manifest["actual_script_quit_frame"] != 5484:
            raise ValueError("noncanonical 263-frame original route")
        if digest(o.read("original.script")) != manifest["exact_original_two_pad_route_LF_without_turbo_sha256"]:
            raise ValueError("original script differs from bound source")
        if (consumed_input(o.read("original.log")) != (INPUT_SHA, 26) or
                consumed_input(p.read(PAINTER_LOG)) != (INPUT_SHA, 26)):
            raise ValueError("original consumed input logs not identical")

        stage_lines = p.read(STAGES_PATH).decode("ascii").splitlines()
        tile_lines = p.read(CALLS_PATH).decode("ascii").splitlines()
        if len(stage_lines) != 360 or len(tile_lines) != 252:
            raise ValueError("real source observation population changed")
        stages: dict[tuple[int, int, int, str], tuple[int, int]] = {}
        for line in stage_lines:
            match = LAYER.fullmatch(line)
            if match is None:
                raise ValueError("malformed genuine Snes9x stage record")
            f, first, last, x, y, name, bg, mode, depth, rgb = match.groups()
            f, first, last, x, y, bg, mode = map(int, (f, first, last, x, y, bg, mode))
            label = f"BG:{bg}" if name == "BG" else name
            key = (f, x, y, label)
            if ((first, last) != (0, 223) or mode != 3 or (x, y) not in PIXELS or
                    label not in STAGES or key in stages):
                raise ValueError("source stage geometry, mode or uniqueness invalid")
            stages[key] = int(depth, 16), int(rgb, 16)
        if len(stages) != 360:
            raise ValueError("duplicate/missing source stage")

        candidates: dict[tuple[int, int, int], list[tuple[int, bool]]] = {}
        for line in tile_lines:
            match = CALL.fullmatch(line)
            if match is None:
                raise ValueError("malformed original sprite-painter record")
            f, y, x, slot, _name, _pal, _prio, _tile, changed, _changedrgb = match.groups()
            f, x, y = int(f), int(x), int(y)
            if (x, y) not in PIXELS:
                raise ValueError("sprite witness outside registered source positions")
            candidates.setdefault((f, x, y), []).append((int(slot), changed == "1"))

        callbacks = {entry["real_original_snes9x_callback_frame"]: entry
                     for entry in manifest["each_authentic_callback"]}
        if len(callbacks) != 263:
            raise ValueError("callback frame duplication")
        matches = []
        for frame in FRAMES:
            entry = callbacks.get(frame)
            if entry is None or entry["original_1based_frame"] != frame + 1:
                raise ValueError("mismatched original internal-vs-one-based callback label")
            data = o.read(f"frames/frame_{frame:06d}_256x224.raw")
            if len(data) != 256 * 224 * 4 or digest(data) != entry["original_unchanged_BGRX_sha256"]:
                raise ValueError("source original BGRX image identity/shape invalid")

            for x, y in PIXELS:
                series = [stages.get((frame, x, y, stage)) for stage in STAGES]
                if any(value is None for value in series):
                    raise ValueError("missing source-original PPU stage")
                depth, color = series[-1]
                if depth not in (0x27, 0x28):
                    raise ValueError("unexpected source-original final owner depth")
                pos = (y * 256 + x) * 4
                b, g, r, alpha = data[pos:pos + 4]
                rgb = rgb565_to_rgb8(color)
                if alpha != 0 or rgb != (r, g, b):
                    raise ValueError(f"original painter/callback disagree frame={frame} x={x} y={y}")
                changed = [slot for slot, wrote in candidates.get((frame, x, y), ()) if wrote]
                if depth == 0x28:
                    if not changed or any(item[0] != 0x28 for item in series):
                        raise ValueError("original OBJ ownership not maintained through BG layers")
                    owner = f"OBJ{changed[-1]}"
                else:
                    if ([item[0] for item in series] != [0, 0x27, 0x27, 0x27] or changed):
                        raise ValueError("original BG0 visible pixel has unsupported sprite writer")
                    owner = "BG0"
                matches.append({
                    "original_internal_frame": frame,
                    "archived_callback_label": frame,
                    "original_1based_output_frame": frame + 1,
                    "pixel": [x, y], "owner": owner, "depth": f"{depth:02x}",
                    "rgb8": list(rgb)
                })
        return {
            "schema": "QA08-original-Snes9x-painter-callback/1",
            "source_only": True, "native_frame_registration_proven": False,
            "original_archive_sha256": ORIGINAL_ZIP_SHA,
            "painter_archive_sha256": PAINTER_ZIP_SHA,
            "canonical_consumed_original_input_sha256": INPUT_SHA,
            "matched_pixels": len(matches), "wrong_pixels": 0, "pixels": matches
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--painter", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    options = parser.parse_args()
    try:
        result = verify(options.original, options.painter)
    except (OSError, ValueError, KeyError, IndexError, UnicodeError, zipfile.BadZipFile) as exc:
        parser.exit(2, f"QA08_ORIGINAL_CALLBACK_REFUSED: {exc}\n")
    report = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if options.out:
        options.out.write_text(report, encoding="utf-8")
    else:
        print(report)
    print(f"QA08_ORIGINAL_CALLBACK_OK matched={result['matched_pixels']} wrong=0 native_registered=0")


if __name__ == "__main__":
    main()
