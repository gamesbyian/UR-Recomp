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
except (ModuleNotFoundError, ImportError):
    import qa08_verify_112field_grey_pixel_budget as source

WIDTH, HEIGHT, TILE = 256, 224, 8
COLS, ROWS = WIDTH // TILE, HEIGHT // TILE
EXACT, CYCLE, OTHER_GRAY, CHROMATIC = range(4)
CLASS_NAMES = ("exact", "four_cycle", "other_grayscale_wrong",
               "non_grayscale_wrong")
LATE_BRACKET = tuple(range(5136, 5233, 16))


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


def classify_cycle_pair_map(original: bytes, native: bytes) -> bytearray:
    """Four original->native gray identities per source pixel; zero elsewhere.

    Genuine image member hashes are checked separately by analyze(), and this
    local classification still validates the full raster/fourth-channel shape.
    """
    classes = classify_frame(original, native)
    result = bytearray(WIDTH * HEIGHT)
    offset = len(source.P7_HEADER)
    labels = {pair: k + 1 for k, pair in enumerate(source.CYCLE)}
    for pixel, kind in enumerate(classes):
        if kind != CYCLE:
            continue
        pos = pixel * 4
        pair = (original[pos + 2] >> 3, native[offset + pos] >> 3)
        if pair not in labels:
            raise ValueError("gray-cycle pixels must retain exact RGB5 pairs")
        result[pixel] = labels[pair]
    return result


def summarize_cycle_pair_identity(pair_frames: list[bytearray]) -> dict:
    """Observe class identity at one coordinate through all 13 sampled fields.

    A pixel may be correct at some fields (zero), but if it is ever a
    four-state gray mismatch, the original->native substitution class must
    never silently turn into another class. This is measured, not a palette
    ingestion or winning-layer attribution.
    """
    if len(pair_frames) != len(source.SPIKES) or any(
        len(frame) != WIDTH * HEIGHT for frame in pair_frames
    ):
        raise ValueError("exactly 13 complete cycle-class source maps required")
    if any(value > len(source.CYCLE) for frame in pair_frames for value in frame):
        raise ValueError("unknown cycle-class pixel value")
    entries = []
    ever = bytearray(WIDTH * HEIGHT)
    totals = Counter()
    for label, frame in zip(source.SPIKES, pair_frames):
        counts = Counter(frame)
        totals.update(counts)
        for i, kind in enumerate(frame):
            if kind and ever[i] and ever[i] != kind:
                raise ValueError("a source coordinate changed its gray-cycle class")
            if kind:
                ever[i] = kind
        entries.append({"native_guest": label,
                        "observed_four_state_cycle_pixels": sum(counts[k]
                            for k in range(1, len(source.CYCLE) + 1))})
    regions = []
    for k, pair in enumerate(source.CYCLE, 1):
        union = [i for i, v in enumerate(ever) if v == k]
        stable = [i for i in union if all(frame[i] == k for frame in pair_frames)]
        regions.append({
            "original_to_native_RGB5": f"{pair[0]}->{pair[1]}",
            "sampled_pixel_occurrences": totals[k],
            "union_source_positions": len(union),
            "intersection_source_positions_all_13": len(stable),
            "intersection_source_position_uint32le_sha256": hashlib.sha256(
                b"".join(i.to_bytes(4, "little") for i in stable)
            ).hexdigest(),
            "upper_raster_intersection_source_positions": sum(
                i < WIDTH * 112 for i in stable),
            "lower_raster_intersection_source_positions": sum(
                i >= WIDTH * 112 for i in stable),
        })
    return {
        "schema": "QA08-112field-authentic-fixed-gray-cycle-class/1",
        "observed_sample_count": len(pair_frames),
        "all_frame_observed_cycle_pixels": sum(totals[k] for k in range(1,5)),
        "union_positions": sum(x["union_source_positions"] for x in regions),
        "intersection_positions_all_13": sum(
            x["intersection_source_positions_all_13"] for x in regions),
        "cross_class_coordinate_conflicts": 0,
        "per_gray_pair": regions,
        "frames": entries,
        "CGRAM_effective_pixel_index_proven": False,
        "original_native_beam_instruction_clock_equivalent": False,
        "global_recolour_or_frame_shift_authorized": False,
        "release_QA08_QA10_accepted": False,
    }


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


def classify_late_writer_bracket(
    cycle_frames: list[bytearray], controls: dict[int, bytearray]
) -> dict:
    """Observe identical source coordinates over seven actual adjacent P7 samples.

    Selection is conditioned on positions wrong in all 13 grayscale-cycle
    frames; all controls still use the unshifted original f-1/native f pairing.
    """
    if (len(cycle_frames) != len(source.SPIKES) or
        set(controls) != set(LATE_BRACKET) or
        any(len(row) != WIDTH * HEIGHT for row in (*cycle_frames, *controls.values()))):
        raise ValueError("late-packet temporal raster window is incomplete")
    shared = set(range(WIDTH * HEIGHT))
    for frame in cycle_frames:
        shared.intersection_update(i for i, kind in enumerate(frame) if kind == CYCLE)
    if not shared:
        raise ValueError("no persistent source-cycle positions")
    digest = hashlib.sha256(
        b"".join(i.to_bytes(4, "little") for i in sorted(shared))
    ).hexdigest()
    rows = []
    for guest in LATE_BRACKET:
        counts = Counter(controls[guest][pos] for pos in shared)
        if any(kind > CHROMATIC for kind in counts):
            raise ValueError("invalid temporal mismatch class")
        rows.append({
            "native_guest": guest, "original_callback": guest - 1,
            "exact_RGB5": counts[EXACT],
            "four_cycle_wrong_RGB5": counts[CYCLE],
            "other_gray_wrong_RGB5": counts[OTHER_GRAY],
            "non_grayscale_wrong_RGB5": counts[CHROMATIC],
        })
    return {
        "persistent_source_positions": len(shared),
        "persistent_positions_uint32le_sha256": digest,
        "correctly_registered_seven_fields": rows,
        "PPU_CGRAM_or_beam_causality_proven": False,
        "video_frame_shift_or_palette_patch_authorized": False,
    }


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
    phase_pair_maps = []
    late_control = {}
    late_member_hashes = {}
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
                phase_pair_maps.append(classify_cycle_pair_map(ref, now))
            original_manifest = json.loads(original.read("qa08-original-2p-fullroute.json"))
            win_report = json.loads(outer.read("qa08-premath-full263-ab.json"))
            original_by_frame = {row["real_original_snes9x_callback_frame"]: row
                                 for row in original_manifest["each_authentic_callback"]}
            native_by_guest = {row["guest"]: row for row in win_report["per_frame"]}
            if len(original_by_frame) != 263 or len(native_by_guest) != 263:
                raise ValueError("original/native per-frame identity collapsed")
            for guest in LATE_BRACKET:
                callback = guest - 1
                old_ref = original_by_frame.get(callback)
                new_ref = native_by_guest.get(guest)
                if (not old_ref or not new_ref or
                    old_ref["original_1based_frame"] != guest or
                    new_ref["original_callback"] != callback):
                    raise ValueError("late CGRAM field source alignment changed")
                o = original.read(f"frames/frame_{callback:06}_256x224.raw")
                n = win32.read(f"source/ur-baldosa-original-source-{guest:06}.pam")
                old_sha = source.sha(o)
                new_sha = source.sha(n)
                if (old_sha != old_ref["original_unchanged_BGRX_sha256"] or
                    new_sha != new_ref["experimental_P7_sha256"]):
                    raise ValueError("late source window pixel member SHA changed")
                late_control[guest] = classify_frame(o, n)
                late_member_hashes[guest] = {
                    "original_BGRX_sha256": old_sha, "native_P7_sha256": new_sha,
                }
    result = summarize_classes(classified)
    identity = summarize_cycle_pair_identity(phase_pair_maps)
    expected = (53658, 107868, 52716, 104533)
    if ([x["sampled_pixel_occurrences"] for x in identity["per_gray_pair"]] != list(expected) or
        identity["all_frame_observed_cycle_pixels"] != 318775 or
        identity["union_positions"] != 24940 or
        identity["intersection_positions_all_13"] != 24096):
        raise ValueError("authentic source cycle identity counts changed")
    result["four_state_cycle_spatial_identity"] = identity
    bracket = classify_late_writer_bracket(classified, late_control)
    if (bracket["persistent_source_positions"] != 24096 or
        bracket["persistent_positions_uint32le_sha256"] !=
            "4646f2123c596b1e9bbca6813d92b1ae3b9a4a53e08e300c17bf2e5f2ebb7b95"):
        raise ValueError("late source-cycle intersection differs from real archive")
    for row in bracket["correctly_registered_seven_fields"]:
        guest = row["native_guest"]
        if ((guest == 5184 and (row["four_cycle_wrong_RGB5"] != 24096 or
                                row["exact_RGB5"] != 0)) or
            (guest != 5184 and (row["exact_RGB5"] != 24096 or
                                row["four_cycle_wrong_RGB5"] != 0)) or
            row["other_gray_wrong_RGB5"] or row["non_grayscale_wrong_RGB5"]):
            raise ValueError("late source-consumed RGB5 temporal pulse changed")
        row.update(late_member_hashes[guest])
    result["late_writer_temporal_bracket"] = bracket
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
