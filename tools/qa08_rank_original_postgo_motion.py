#!/usr/bin/env python3
"""SHA-qualified original 2P moving-frame diversity; NO native pixel claim.

Reuse the genuinely executed original Snes9x 37-callback source window.
Select additional native-comparison candidates only after quantifying how
many *actual original* source RGB pixels change in both split viewports.
This runs no game, patches no emulator and invents no unsampled native PPU.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ZIP_SHA = "6e5d488230c11d3dfcd144b6a7cbc8c25d7acfcb4f95b776a85071dd3487f5e3"
MANIFEST_SHA = "29856fa4f13bfc679b60240de80bd48b8c035801b56e0fbb3e17472a06836787"
WINDOW = tuple(range(2188, 2225))
GUEST_CANDIDATES = (2192, 2208, 2224)
CALLBACKS = tuple(f - 1 for f in GUEST_CANDIDATES)
W, H = 256, 224
SIZE = W * H * 4
SCHEMA = "qa08-original-Snes9x-2P-postGO-source-motion-diversity/1"


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def check_original_frame(blob: bytes) -> None:
    if len(blob) != SIZE:
        raise ValueError("original source callback must be complete 256x224 BGRX")
    for offset in range(0, SIZE, 4):
        blue, green, red, zero = blob[offset:offset + 4]
        if zero != 0 or green != (((green >> 2) << 2) | ((green >> 2) >> 4)):
            raise ValueError("original source lacks genuine Snes9x RGB565 BGRX expansion")
        if blue != (((blue >> 3) << 3) | ((blue >> 3) >> 2)):
            raise ValueError("original source blue is not RGB5-expanded")
        if red != (((red >> 3) << 3) | ((red >> 3) >> 2)):
            raise ValueError("original source red is not RGB5-expanded")


def compare_original_frames(a: bytes, b: bytes) -> dict:
    check_original_frame(a)
    check_original_frame(b)
    changed_top = changed_split = changed_bottom = 0
    for offset in range(0, SIZE, 4):
        if a[offset:offset + 3] == b[offset:offset + 3]:
            continue
        y = (offset // 4) // W
        if y < 111:
            changed_top += 1
        elif y < 113:
            changed_split += 1
        else:
            changed_bottom += 1
    return {
        "top_rows_0_to_110_changed_RGB_pixels": changed_top,
        "split_rows_111_to_112_changed_RGB_pixels": changed_split,
        "bottom_rows_113_to_223_changed_RGB_pixels": changed_bottom,
        "total_changed_RGB_pixels": changed_top + changed_split + changed_bottom,
        "source_pixels_compared": W * H,
    }


def assess(source: dict[int, bytes]) -> dict:
    if set(source) != set(CALLBACKS):
        raise ValueError("must provide the three exact preselected original callback frames")
    for blob in source.values():
        check_original_frame(blob)
    pairs = []
    for i, first in enumerate(CALLBACKS):
        for second in CALLBACKS[i + 1:]:
            diff = compare_original_frames(source[first], source[second])
            pairs.append({
                "original_callback_frames": [first, second],
                "original_script_frames_one_based": [first + 1, second + 1],
                **diff,
            })
    return {
        "schema": SCHEMA,
        "status": "genuine_original_source_motion_diversity_only",
        "original_Snes9x_source_ZIP_SHA256": ZIP_SHA,
        "original_source_dimensions": [W, H],
        "observed_original_callbacks": list(CALLBACKS),
        "accepted_original_full_callback_window": [WINDOW[0], WINDOW[-1]],
        "original_source_SHA256": {str(frame): digest(source[frame]) for frame in CALLBACKS},
        "real_original_full_RGB_pairwise_differences": pairs,
        "proposed_additional_native_frames": [2192, 2224],
        "native_host_has_emitted_these_additional_frames": False,
        "source_original_native_guest_phase_for_additional_frames_proven": False,
        "original_native_RGB5_pixel_parity_for_additional_frames_proven": False,
        "source_2P_rider_OAM_winner_or_4x_HD_proven": False,
        "release_or_renderer_promotion_authorized": False,
    }


def check(archive: Path) -> dict:
    raw = archive.read_bytes()
    if digest(raw) != ZIP_SHA:
        raise ValueError("original executed Snes9x source archive ZIP differs")
    with zipfile.ZipFile(archive) as zipdata:
        manifest_raw = zipdata.read("qa08-original-37frame-window.json")
        if digest(manifest_raw) != MANIFEST_SHA:
            raise ValueError("original complete source manifest SHA mismatch")
        manifest = json.loads(manifest_raw)
        records = manifest.get("source_original_frames")
        if (manifest.get("full_256x224_original_frames") != 37
            or not isinstance(records, list) or len(records) != len(WINDOW)
            or manifest.get("same_input_guest_phase_and_camera_as_native_proven") is not False):
            raise ValueError("original route/frame count or evidence boundaries not accepted")
        expected_paths = {f"qa08-original-source-window/frame_{f:06d}_{W}x{H}.raw"
                          for f in WINDOW}
        actual_paths = {p for p in zipdata.namelist()
                        if p.startswith("qa08-original-source-window/")}
        if actual_paths != expected_paths:
            raise ValueError("original 37 callback frame set missing, cropped or extra")
        wanted = {}
        for f, record in zip(WINDOW, records):
            p = f"qa08-original-source-window/frame_{f:06d}_{W}x{H}.raw"
            data = zipdata.read(p)
            if (record.get("original_Snesref_callback_frame_zero_based") != f
                or record.get("corresponding_original_retro_run_one_based") != f + 1
                or digest(data) != record.get("raw_B_G_R_X_SHA256")):
                raise ValueError("accepted original callback provenance changed")
            check_original_frame(data)
            if f in CALLBACKS:
                wanted[f] = data
    return assess(wanted)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-zip", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    report = check(args.original_zip)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("QA08_ORIGINAL_2P_MOVING_FRAMES_MEASURED "
          "callback2191_2207_2223 authenticated; no new native pixels observed")


if __name__ == "__main__":
    main()
