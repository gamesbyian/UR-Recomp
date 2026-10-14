#!/usr/bin/env python3
"""Compare fourth REAL combined channel5+7 prime to accepted 2P sources.

Science gate, not shipping: a negative original RGB5 result is retained,
not masked, interpolated or called a production pass. Three earlier
stock/global/channel7 source controls must still pass intact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.qa08_compare_channel7_native_prime import (
        compare as prior_compare, decode_p7, pixels_changed,
        original_image, ORIGINAL_FILES, COUNTDOWN_ZIP_SHA,
        ORIGINAL_ZIP_SHA, FRAMES,
    )
    from tools.qa08_accept_original_native_split_seam import rgb5_match, W, H
except ModuleNotFoundError:
    from qa08_compare_channel7_native_prime import (
        compare as prior_compare, decode_p7, pixels_changed,
        original_image, ORIGINAL_FILES, COUNTDOWN_ZIP_SHA,
        ORIGINAL_ZIP_SHA, FRAMES,
    )
    from qa08_accept_original_native_split_seam import rgb5_match, W, H

SCHEMA = "qa08-real-original-native-combined-channel57-prime-4process/1"
KINDS = ("stock", "global", "channel7", "channel57")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compare(native: dict[str, dict[int, bytes]],
            originals: dict[int, bytes], crcs: dict[str, bytes],
            *, strict_reference: bool = True) -> dict:
    if set(native) != set(KINDS) or set(crcs) != set(KINDS):
        raise ValueError("four independently executed native source/CRC processes required")
    if set(native["channel57"]) != set(FRAMES):
        raise ValueError("combined channel57 must produce three real native original-source frames")
    if (not crcs["channel57"] or crcs["channel57"] != crcs["stock"]
        or len(crcs["channel57"].splitlines()) != 2473):
        raise ValueError("fourth real native guest CRC series differs from prior 2473 route")

    controls = prior_compare(
        {k: native[k] for k in ("stock", "global", "channel7")},
        originals,
        {k: crcs[k] for k in ("stock", "global", "channel7")},
        strict_reference=strict_reference,
    )
    scenes = []
    for frame in FRAMES:
        combined = decode_p7(native["channel57"][frame])
        global_pix = decode_p7(native["global"][frame])
        selective_pix = decode_p7(native["channel7"][frame])
        global_delta = pixels_changed(global_pix, combined)
        selective_delta = pixels_changed(selective_pix, combined)
        record = {
            "guest_frame": frame,
            "channel57_P7_SHA256": digest(native["channel57"][frame]),
            "global_to_channel57": global_delta,
            "channel7_to_channel57": selective_delta,
            "source_alpha_changed_from_global": global_delta["changed_alpha_pixels"] != 0,
        }
        if frame in originals:
            score = rgb5_match(originals[frame], combined, with_rows=True)
            record["original_callback"] = frame - 1
            record["original_Snes9x_RGB5_pixels_equal"] = score["identical_RGB5_expanded_pixels"]
            record["original_Snes9x_RGB5_wrong_pixels"] = score["different_pixels"]
            record["original_Snes9x_mismatching_rows"] = score[
                "different_pixels_by_original_output_row"]
        scenes.append(record)

    exact = all(
        row["original_Snes9x_RGB5_wrong_pixels"] == 0 for row in scenes[1:])
    frontend_unchanged = scenes[0]["global_to_channel57"]["changed_RGBA_pixels"] == 0
    alpha_unchanged = not any(r["source_alpha_changed_from_global"] for r in scenes)
    return {
        "schema": SCHEMA,
        "status": ("experimental_ch57_two_2P_source_scenes_equal"
                   if exact and frontend_unchanged and alpha_unchanged
                   else "experimental_ch57_real_source_divergence_observed"),
        "unchanged_three_process_source_controls": controls["status"],
        "real_native_processes": 4,
        "identical_guest_CRC_entries": 2473,
        "true_native_source_dimensions": [W, H],
        "original_Snes9x_unchanged_source_ZIP_SHA256": {
            "countdown": COUNTDOWN_ZIP_SHA,
            "postGO": ORIGINAL_ZIP_SHA,
        },
        "authentic_source_scene_dispositions": scenes,
        "both_original_2P_scenes_exact_RGB5": exact,
        "all_observed_source_alpha_unchanged_from_global": alpha_unchanged,
        "frontend_not_changed_from_global": frontend_unchanged,
        "other_HD_2P_moving_race_results_1P_proven": False,
        "executed_CPU_65816_HDMA_channels_fully_caused": False,
        "physical_SNES_scanline_or_cross_game_verified": False,
        "shipping_production_HDMA_correction_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for kind in KINDS:
        parser.add_argument("--" + kind + "-dir", type=Path, required=True)
        parser.add_argument("--" + kind + "-crc", type=Path, required=True)
    parser.add_argument("--original-countdown-zip", type=Path, required=True)
    parser.add_argument("--original-postgo-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    def actual(directory: Path) -> dict[int, bytes]:
        return {f: (directory / f"ur-baldosa-original-source-{f:06d}.pam").read_bytes()
                for f in FRAMES}
    native = {k: actual(getattr(args, k + "_dir")) for k in KINDS}
    originals = {
        1856: original_image(args.original_countdown_zip, COUNTDOWN_ZIP_SHA, ORIGINAL_FILES[1856]),
        2208: original_image(args.original_postgo_zip, ORIGINAL_ZIP_SHA, ORIGINAL_FILES[2208]),
    }
    crcs = {k: getattr(args, k + "_crc").read_bytes() for k in KINDS}
    result = compare(native, originals, crcs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("QA08_REAL_CH57_SOURCE_TEST " + result["status"] +
          " shipping_original_renderer_fix=not_authorized")


if __name__ == "__main__":
    main()
