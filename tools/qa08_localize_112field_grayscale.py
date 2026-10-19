#!/usr/bin/env python3
"""Read-only QA08 grayscale spatial analysis of immutable original/native rasters.

Delegates every archive, CRC, image and total census qualification to the
already merged source verifier. Adds independent 8x8-cell/scanline localization
and temporal position overlap; never emits copyrighted pixel values.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import zipfile

try:
    from tools import qa08_verify_112field_grey_pixel_budget as source
except ModuleNotFoundError:
    import qa08_verify_112field_grey_pixel_budget as source

WIDTH, HEIGHT, TILE = 256, 224, 8
COLS, ROWS = WIDTH // TILE, HEIGHT // TILE
EXACT, CYCLE, OTHER_GRAY, CHROMATIC = range(4)
CLASS_NAMES = ("exact", "four_cycle", "other_grayscale_wrong",
               "non_grayscale_wrong")


def classify_frame(original: bytes, native: bytes) -> bytearray:
    """Full 256x224 BGRX source vs P7 RGBA native, RGB5 on all three channels."""
    if (len(original) != WIDTH * HEIGHT * 4 or
        len(native) != len(source.P7_HEADER) + len(original) or
        not native.startswith(source.P7_HEADER)):
        raise ValueError("complete original/native source raster shape or header changed")
    kinds = bytearray(WIDTH * HEIGHT)
    header = len(source.P7_HEADER)
    for pixel in range(WIDTH * HEIGHT):
        pos = pixel * 4
        b, g, r, reserved = original[pos:pos + 4]
        nr, ng, nb, reserved_native = native[header + pos:header + pos + 4]
        if reserved or reserved_native:
            raise ValueError("original/native fourth channel no longer zero")
        ref = (r >> 3, g >> 3, b >> 3)
        got = (nr >> 3, ng >> 3, nb >> 3)
        if ref == got:
            continue
        if ref[0] == ref[1] == ref[2] and got[0] == got[1] == got[2]:
            kinds[pixel] = CYCLE if (ref[0], got[0]) in source.CYCLE else OTHER_GRAY
        else:
            kinds[pixel] = CHROMATIC
    return kinds


def summarize_classes(classified: list[bytearray]) -> dict:
    """Locate real errors without changing registration or source pixels."""
    if len(classified) != len(source.SPIKES) or any(
        len(frame) != WIDTH * HEIGHT for frame in classified
    ):
        raise ValueError("exactly 13 full-size source classifications required")
    if any(value > CHROMATIC for frame in classified for value in frame):
        raise ValueError("invalid RGB5 mismatch classification")
    tiles = [[0] * (COLS * ROWS) for _ in CLASS_NAMES[1:]]
    scanlines = [[0] * HEIGHT for _ in CLASS_NAMES[1:]]
    union = set()
    intersection = None
    frames = []
    counts = Counter()
    for field, frame in zip(source.SPIKES, classified):
        local = Counter(frame)
        locations = {i for i, kind in enumerate(frame) if kind == CYCLE}
        union.update(locations)
        intersection = locations if intersection is None else intersection & locations
        frames.append({
            "native_guest": field, "original_callback": field - 1,
            "wrong_rgb5": len(frame) - local[EXACT],
            "four_cycle_wrong_rgb5": local[CYCLE],
            "other_grayscale_wrong_rgb5": local[OTHER_GRAY],
            "non_grayscale_wrong_rgb5": local[CHROMATIC],
            "cycle_location_sha256": hashlib.sha256(
                b"".join(i.to_bytes(4, "little") for i in sorted(locations))
            ).hexdigest(),
        })
        counts.update(local)
        for i, kind in enumerate(frame):
            if kind == EXACT:
                continue
            y, x = divmod(i, WIDTH)
            scanlines[kind - 1][y] += 1
            tiles[kind - 1][(y // TILE) * COLS + x // TILE] += 1
    result = {
        "schema": "QA08-112field-authentic-RGB5-spatial-localization/1",
        "full_source_width": WIDTH, "full_source_height": HEIGHT,
        "sampled_native_guest_stride": 112,
        "source_registration": "2014 Snes9x callback f-1 to compiled Win32 guest f",
        "eight_by_eight_grid": {"columns": COLS, "rows": ROWS},
        "class_counts": {CLASS_NAMES[k]: counts[k] for k in range(4)},
        "cycle_position_union": len(union),
        "cycle_position_intersection_all_13": len(intersection or set()),
        "scanline_counts": {CLASS_NAMES[k]: scanlines[k - 1] for k in range(1, 4)},
        "tile_8x8_counts": {CLASS_NAMES[k]: tiles[k - 1] for k in range(1, 4)},
        "frames": frames,
        "original_native_consumed_inputs_and_beam_equivalent": False,
        "CGRAM_ingestion_or_register_root_cause_proven": False,
        "global_frame_shift_palette_recolour_or_brightness_patch_authorized": False,
        "QA08_QA10_or_release_accepted": False,
    }
    for kind in range(1, 4):
        if (sum(scanlines[kind - 1]) != counts[kind] or
            sum(tiles[kind - 1]) != counts[kind]):
            raise ValueError("spatial classification conservation failed")
    return result


def analyze(original_path: Path, native_path: Path) -> dict:
    pinned = source.verify(original_path, native_path)
    if (pinned["independent_graphics_or_release_acceptance"] is not False or
        pinned["CGRAM_ingestion_root_cause_proven"] is not False or
        pinned["same_original_native_consumed_input_beam_proven"] is not False):
        raise ValueError("inherited source-only proof boundary changed")
    original_bytes = original_path.read_bytes()
    native_bytes = native_path.read_bytes()
    if (source.sha(original_bytes) != source.ORIGINAL_INNER_SHA or
        source.sha(native_bytes) != source.NATIVE_OUTER_SHA):
        raise ValueError("source archives changed after identity verification")
    classified = []
    with zipfile.ZipFile(io.BytesIO(original_bytes)) as original, \
         zipfile.ZipFile(io.BytesIO(native_bytes)) as outer:
        nested = outer.read("qa08-premath-source-images.zip")
        if source.sha(nested) != source.NATIVE_INNER_SHA:
            raise ValueError("source image container changed")
        with zipfile.ZipFile(io.BytesIO(nested)) as win32:
            for guest in source.SPIKES:
                ref = original.read(f"frames/frame_{guest-1:06}_256x224.raw")
                now = win32.read(f"source/ur-baldosa-original-source-{guest:06}.pam")
                classified.append(classify_frame(ref, now))
    result = summarize_classes(classified)
    for actual, recorded in zip(result["frames"], pinned["frames"]):
        if (actual["native_guest"] != recorded["native_guest"] or
            actual["wrong_rgb5"] != recorded["total_wrong_rgb5"] or
            actual["four_cycle_wrong_rgb5"] != recorded["four_cycle_wrong_rgb5"] or
            actual["four_cycle_wrong_rgb5"] +
            actual["other_grayscale_wrong_rgb5"] != recorded["gray_to_gray_wrong_rgb5"]):
            raise ValueError("spatial classifier disagrees with verified pixel census")
    counts = result["class_counts"]
    if (counts["four_cycle"] != pinned["spike_four_cycle_wrong_RGB5"] or
        counts["four_cycle"] + counts["other_grayscale_wrong"] !=
            pinned["spike_both_gray_wrong_RGB5"] or
        sum(counts[k] for k in CLASS_NAMES[1:]) != pinned["spike_total_wrong_RGB5"]):
        raise ValueError("spatial classifier does not conserve genuine 13-field budget")
    result["original_archive_sha256"] = source.ORIGINAL_INNER_SHA
    result["native_archive_sha256"] = source.NATIVE_OUTER_SHA
    result["actual_native_guest_CRC_sha256"] = source.NATIVE_CRC_SHA
    result["all_263_rgb5_wrong_baseline"] = pinned["entire_263_source_wrong_RGB5"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--out", type=Path, help="JSON counts only; never source pixels")
    args = parser.parse_args()
    try:
        result = analyze(args.original, args.native)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        parser.exit(2, "QA08_GRAY_SPATIAL_REFUSED: " + str(exc) + "\n")
    output = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.out:
        if args.out.exists():
            parser.exit(2, "QA08_GRAY_SPATIAL_REFUSED: output exists\n")
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output)
    print("QA08_GRAY_SPATIAL_SOURCE_ONLY no_raster_change=1 no_release_credit=1")


if __name__ == "__main__":
    main()
