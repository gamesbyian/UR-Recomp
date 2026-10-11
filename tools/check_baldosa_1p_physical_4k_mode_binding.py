#!/usr/bin/env python3
"""QA-10: bind actual SDL 4K Original parity to its original 1P guest mode.

This *follows*, never replaces, the exact 8.29-million-pixel physical
oracle. It accepts that oracle's report only when the tested 342x224
Original and 1368x896 4x contents are the separately accepted genuine
live-1P guest2208 images, not the coincident-frame live 2P raster.
Guest route CRC parity remains the independent native workflow gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

FRAME = 2208
ORIGINAL_1P_SOURCE_SHA = (
    "8e81014ae6b7285b8d4a79985cc6ba146b309e913fc0e7e3cb8800730f3f0f05"
)
ORIGINAL_1P_4X_SHA = (
    "b8257c7f94a4b97b343626f773be912b8967a9a1849ef3574fd8d755ef3bab7a"
)
# Independently accepted two-player Original at the very same guest index.
ORIGINAL_2P_SOURCE_SHA = (
    "f9ca59c19dc3e8d51c7ca1dbce25d5dc14e56ba36011128abbadee8cec0e7b4a"
)
ORIGINAL_2P_PHYSICAL_SHA = (
    "29f6ef1f9b5965d32818228182922e337a0570433b5929c89e285af2969a0fac"
)
PHYSICAL_LINE = (
    "UR_BALDOSA_PHYSICAL_4K_CAPTURE frame=2208 output=3840x2160 "
    "source=SDL_RenderReadPixels status=saved"
)
LIVE_MODE = re.compile(
    r"^UR_BALDOSA_WS342_LIVE_MODE frame=(\d+) mode=1 "
    r"guest_race=[0-9A-Fa-f]+ frontend=[0-9A-Fa-f]+$", re.M
)
PRESENT = (
    "UR_BALDOSA_WS342_PRESENT frame=2208 width=342 height=224 "
    "pitch=5472 calibrated=1 saved=1 density=4 raster=1368x896"
)
SHA = re.compile(r"^[0-9a-f]{64}$")


def verify(physical_report: Path, native_log: Path) -> dict:
    report = json.loads(physical_report.read_text(encoding="utf-8"))
    if (report.get("schema_version") != 1 or
        report.get("status") != "exact-native-capture-pixel-parity" or
        report.get("frame") != FRAME or
        report.get("source_ppu_size") != [342, 224] or
        report.get("native_density_size") != [1368, 896] or
        report.get("physical_capture_size") != [3840, 2160] or
        report.get("output_viewport") != [0, 0, 3840, 2160] or
        report.get("original_pixel_aspect") != [7, 6] or
        report.get("wide_horizontal_fit") != [512, 513] or
        report.get("sdl2_software_nearest_fixed_point_bits") != 16 or
        report.get("native_density_and_output_distinct") is not True or
        report.get("full_height_224_rows_preserved") is not True or
        report.get("opaque_sdl_drawable_alpha_expected") != 255 or
        report.get("original_ppu_alpha_is_not_output_opacity") is not True):
        raise ValueError("missing genuine Original 1P 342-wide physical-4K geometry/parity report")
    if (report.get("rgba_source_sha256") != ORIGINAL_1P_SOURCE_SHA or
        report.get("rgba_density_sha256") != ORIGINAL_1P_4X_SHA or
        report.get("rgba_source_sha256") == ORIGINAL_2P_SOURCE_SHA):
        raise ValueError("physical 4K report does not bind independently accepted original live 1P pixels")
    screen = report.get("rgba_capture_sha256")
    if (not isinstance(screen, str) or not SHA.fullmatch(screen) or
        screen in (ORIGINAL_1P_SOURCE_SHA, ORIGINAL_1P_4X_SHA,
                   ORIGINAL_2P_PHYSICAL_SHA)):
        raise ValueError("physical 4K reported output is missing, malformed, or copied from wrong mode")
    log = native_log.read_text(encoding="utf-8", errors="replace")
    lines = [row.strip() for row in log.splitlines()]
    if lines.count(PHYSICAL_LINE) != 1 or lines.count(PRESENT) != 1:
        raise ValueError("actual full drawable SDL capture and genuine live 1P post-GO presentation both required")
    mode = [int(m.group(1)) for m in LIVE_MODE.finditer(log)]
    if len(mode) != 1 or not 0 <= mode[0] < FRAME:
        raise ValueError("native source log does not prove one live 1P mode was activated before post-GO")
    if "UR_BALDOSA_PHYSICAL_4K_CAPTURE_REJECT" in log:
        raise ValueError("physical SDL capture was rejected in native host log")
    return {
        "schema_version": 1,
        "status": "accepted-live-1p-same-guest-original-physical-4k-provenance",
        "guest_frame": FRAME,
        "live_oneplayer_mode_activated_at_guest_frame": mode[0],
        "exact_physical_SDL_capture_log_lines_verified": 1,
        "exact_live_1p_source_presentation_log_lines_verified": 1,
        "independently_accepted_original_oneplayer_source_sha256":
            ORIGINAL_1P_SOURCE_SHA,
        "independently_accepted_original_oneplayer_density4_sha256":
            ORIGINAL_1P_4X_SHA,
        "accepted_original_oneplayer_physical3840x2160_sha256": screen,
        "same_guest_original_twoplayer_source_sha256_excluded":
            ORIGINAL_2P_SOURCE_SHA,
        "full_guest_CRC_parity_and_physical_all_pixel_oracle_run_by_parent":
            True,
        "full_guest_CRC_rechecked_by_this_report": False,
        "physical_pixels_rechecked_by_this_report": False,
        "hd_art_or_modern_display_mode_admitted": False,
        "limitations": (
            "A provenance binding on the accepted same-frame physical "
            "pixel oracle plus native SDL/live-mode log. It does not "
            "independently re-render an 8.29M-pixel frame, certify GPU "
            "behavior, legal image redistribution, 3D art or release."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--physical-report", required=True, type=Path)
    ap.add_argument("--native-log", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    result = verify(a.physical_report, a.native_log)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    print("UR_QA10_1P_PHYSICAL_4K_MODE_BINDING " + result["status"] +
          f" guest={FRAME} source={ORIGINAL_1P_SOURCE_SHA[:12]}" +
          f" drawable={result['accepted_original_oneplayer_physical3840x2160_sha256'][:12]}" +
          " art_admitted=0")


if __name__ == "__main__":
    main()
