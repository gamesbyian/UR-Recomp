#!/usr/bin/env python3
"""Compare REAL channel6+7 consumed-prime native PPU to four source Snes9x scenes.

Requires previously accepted original and global-prime independent source
controls and five full genuine guest CRC streams. A nonexact experimental
image is a *reported negative*, not grounds for recolouring/cropping.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.qa08_compare_channel7_native_prime import (
        original_image, COUNTDOWN_ZIP_SHA, ORIGINAL_FILES,
        decode_p7, pixels_changed,
    )
    from tools.qa08_compare_original_moving_source_window import original_window
    from tools.qa08_accept_original_native_split_seam import rgb5_match, W, H
except ModuleNotFoundError:
    from qa08_compare_channel7_native_prime import (
        original_image, COUNTDOWN_ZIP_SHA, ORIGINAL_FILES,
        decode_p7, pixels_changed,
    )
    from qa08_compare_original_moving_source_window import original_window
    from qa08_accept_original_native_split_seam import rgb5_match, W, H

SCHEMA = "qa08-real-original-native-window-ch6-brightness-ch7-first-line/1"
FRAMES = (1856, 2192, 2208, 2224)
KINDS = ("stock", "global", "channel7", "channel57", "channel67")
PAIRS = {1856: 1855, 2192: 2191, 2208: 2207, 2224: 2223}
ACCEPTED_GLOBAL_P7 = {
    1856: "ed35731cde55e927165f173c1db29c27b3b7eeff19862fbca27db3467cb8bc87",
    2192: "fac9f37e04b752676346bd75345e6e988b88e5cf6703722618d8a968ec90b36c",
    2208: "bf8b4218fb72f94338b19da5c1386bd5ce09c0dc0c767093286e80895fa3353c",
    2224: "d64e7b2fee2ff9f21b5fad7f4e8618ea27ad8846c6b6047ca9c511583bde6bd8",
}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def assess(original: dict[int, bytes], native: dict[str, dict[int, bytes]],
           crcs: dict[str, bytes], *, enforce_accepted_global: bool = True) -> dict:
    if set(original) != set(FRAMES) or set(native) != set(KINDS):
        raise ValueError("requires four genuine original source frames and five native processes")
    if set(crcs) != set(KINDS) or any(set(frames) != set(FRAMES)
                                     for frames in native.values()):
        raise ValueError("requires four real frames and exact guest CRC from each of five native runs")
    first = crcs["stock"]
    if (not first or len(first.splitlines()) != 2473
        or any(blob != first for blob in crcs.values())
        or any(len(line) != 10 or not line.startswith(b"0x")
               or any(c not in b"0123456789ABCDEF" for c in line[2:])
               for line in first.splitlines())):
        raise ValueError("five full native 2473-frame guest CRC transcripts differ/malformed")
    decoded = {
        kind: {frame: decode_p7(p7) for frame, p7 in pix.items()}
        for kind, pix in native.items()
    }
    rows = []
    for frame in FRAMES:
        expected = original[frame]
        verified_global = native["global"][frame]
        if enforce_accepted_global and digest(verified_global) != ACCEPTED_GLOBAL_P7[frame]:
            raise ValueError("prior source-qualified original global-prime P7 changed")
        positive = rgb5_match(expected, decoded["global"][frame])
        if positive["different_pixels"]:
            raise ValueError("independently accepted original/global-prime pixel control regressed")
        candidate = rgb5_match(expected, decoded["channel67"][frame], with_rows=True)
        diff = pixels_changed(decoded["global"][frame], decoded["channel67"][frame])
        rows.append({
            "native_guest_frame": frame,
            "original_snes9x_callback": PAIRS[frame],
            "actual_original_Snes9x_source_sha256": digest(expected),
            "real_native_P7_sha256": {kind: digest(native[kind][frame]) for kind in KINDS},
            "candidate_ch67_wrong_original_RGB5_pixels": candidate["different_pixels"],
            "candidate_ch67_matching_original_RGB5_pixels": candidate["identical_RGB5_expanded_pixels"],
            "candidate_ch67_differing_rows": candidate["different_pixels_by_original_output_row"],
            "global_to_ch67_full_P7_RGBA_change": diff,
            "all_57344_RGB5_source_pixels_exact_ch67": candidate["different_pixels"] == 0,
        })
    return {
        "schema": SCHEMA,
        "status": ("experimental_ch67_all_four_real_source_scenes_exact"
                   if all(r["all_57344_RGB5_source_pixels_exact_ch67"] for r in rows)
                   else "experimental_ch67_genuine_original_source_negative"),
        "genuine_guest_processes": len(KINDS),
        "guest_CRC_records_equal": 2473,
        "source_pixel_geometry": [W, H],
        "source_snes9x_only_green6_to_green5_normalization": True,
        "original_source_observations": rows,
        "four_scenes_original_RGB5_exact_for_channel67": all(
            r["all_57344_RGB5_source_pixels_exact_ch67"] for r in rows),
        "source_guest_camera_input_65816_phase_fully_proven": False,
        "original_PPU_window_OAM_hardware_HBlank_fully_proven": False,
        "Gundam_Wing_cross_game_or_1P_results_verified": False,
        "production_HDMA_source_change_authorized": False,
        "approved_hd_racer_likeness": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-countdown-zip", required=True, type=Path)
    p.add_argument("--original-postgo-37zip", required=True, type=Path)
    for kind in KINDS:
        p.add_argument("--" + kind + "-dir", required=True, type=Path)
        p.add_argument("--" + kind + "-crc", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    countdown = original_image(
        args.original_countdown_zip, COUNTDOWN_ZIP_SHA, ORIGINAL_FILES[1856])
    postgo = original_window(args.original_postgo_37zip)
    original = {
        frame: countdown if frame == 1856 else postgo[PAIRS[frame]]
        for frame in FRAMES
    }
    def captures(directory: Path) -> dict[int, bytes]:
        return {
            frame: (directory /
                    f"ur-baldosa-original-source-{frame:06d}.pam").read_bytes()
            for frame in FRAMES
        }
    native = {kind: captures(getattr(args, kind + "_dir")) for kind in KINDS}
    crcs = {kind: getattr(args, kind + "_crc").read_bytes() for kind in KINDS}
    result = assess(original, native, crcs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("QA08_REAL_CHANNEL67_4SCENE_SOURCE " + result["status"] +
          " production_correctness=not_proven")


if __name__ == "__main__":
    main()
