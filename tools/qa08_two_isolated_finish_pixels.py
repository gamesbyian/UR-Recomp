#!/usr/bin/env python3
"""QA-08: identify the TWO isolated finish pixels in real original/Win32 2P.

Read only the immutable original and freshly source-qualified Windows archives;
run the established full strict 263-frame original/native comparator first.
All image bytes, script provenance, guest CRC and same-frame labels are checked
by that comparator. Do not search for a temporal/spatial alignment, recolour,
mask, crop, fabricate pixels, or infer an emulator error is a SNES hardware bug.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from qa08_compare_windows_original_twoplayer_sparse import (
    HEADER, H, W, compare, inspect as inspect_full,
)

GUESTS = (3792, 3872)
NEIGHBOURS = (3776, 3808, 3856, 3888)
EXPECTED_FULL_EXACT = 203
EXPECTED_FULL_WRONG = 385373
EXPECTED_NATIVE_EXE = (
    "29431b073fd550e29b908f4e1d20fe9ee46b357b7a3e73b4fa21a224fa0dbf08"
)
EXPECTED_CRC = (
    "c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876"
)


def original_rgb5(raw: bytes, x: int, y: int) -> tuple[int, int, int]:
    b, g, r, _ = raw[(y * W + x) * 4:(y * W + x + 1) * 4]
    g5 = g >> 3
    return (r, (g5 << 3) | (g5 >> 2), b)


def native_rgb(raw: bytes, x: int, y: int) -> tuple[int, int, int]:
    return tuple(raw[(y * W + x) * 4:(y * W + x) * 4 + 3])


def neighbourhood(source: bytes, native: bytes, x: int, y: int,
                  radius: int = 2) -> list[dict]:
    if len(source) != W * H * 4 or len(native) != W * H * 4:
        raise ValueError("neighbourhood requires full 256x224 authentic frames")
    if not (0 <= x < W and 0 <= y < H and 0 <= radius <= 4):
        raise ValueError("invalid source pixel radius/coordinate")
    pixels = []
    for yy in range(max(0, y-radius), min(H, y+radius+1)):
        for xx in range(max(0, x-radius), min(W, x+radius+1)):
            src = original_rgb5(source, xx, yy)
            dst = native_rgb(native, xx, yy)
            pixels.append({"x": xx, "y": yy,
                "original_RGB5_expanded": list(src),
                "real_windows_RGB8": list(dst),
                "wrong_RGB5": src != dst})
    return pixels


def extract_source_frames(original_dir: Path, windows_dir: Path,
                          guest: int) -> tuple[bytes, bytes]:
    original = (original_dir/"frames"/f"frame_{guest-1:06d}_256x224.raw").read_bytes()
    native_p7 = (windows_dir/"source"/f"ur-baldosa-original-source-{guest:06d}.pam").read_bytes()
    if len(original) != W * H * 4 or not native_p7.startswith(HEADER) or (
        len(native_p7) != len(HEADER)+W*H*4
    ):
        raise ValueError("missing complete unaltered source or Win32 post-PPU field")
    return original, native_p7[len(HEADER):]


def analyze(original_dir: Path, windows_dir: Path, route: Path) -> dict:
    full = inspect_full(original_dir, windows_dir, route)
    if (
        full["strict_exact_2P_sampled_frames"] != EXPECTED_FULL_EXACT
        or full["total_original_vs_windows_incorrect_RGB5_pixels"] != EXPECTED_FULL_WRONG
        or full["native_guest_CRC_sha256"] != EXPECTED_CRC
        or full["actual_native_Windows_executable_sha256"] != EXPECTED_NATIVE_EXE
        or full["all_2P_source_pixels_compared"] != 263*W*H
        or full["full_logical_pixel_geometry"] != [W, H]
    ):
        raise ValueError("not the authentic qualified latest graphics candidate")
    rows = {r["real_windows_guest"]:r for r in full["full_original_to_native_source_comparisons"]}
    if set(GUESTS + NEIGHBOURS) - set(rows):
        raise ValueError("missing exact source-registered finish fields")
    if any(rows[guest]["wrong_RGB5_pixels"] != 0 for guest in NEIGHBOURS):
        raise ValueError("the four original/native neighbouring frames are no longer exact")
    per_pixel = []
    for guest in GUESTS:
        row = rows[guest]
        if row["wrong_RGB5_pixels"] != 1 or len(row["first_eight_wrong"]) != 1:
            raise ValueError("the supposed isolated finish pixel is not unique")
        first = row["first_eight_wrong"][0]
        x, y = first["x"], first["y"]
        original, windows = extract_source_frames(original_dir, windows_dir, guest)
        if hashlib.sha256(original).hexdigest() != row["original_unchanged_BGRX_sha256"]:
            raise ValueError("finish original source SHA drift")
        p7 = (windows_dir/"source"/f"ur-baldosa-original-source-{guest:06d}.pam").read_bytes()
        if hashlib.sha256(p7).hexdigest() != row["native_unchanged_P7_sha256"]:
            raise ValueError("finish Windows source SHA drift")
        allwrong = compare(original, windows)
        if allwrong["wrong_RGB5_pixels"] != 1 or allwrong["first_eight_wrong"] != [first]:
            raise ValueError("wrong RGB5 source pixel or source-byte registration")
        px = neighbourhood(original, windows, x, y, 2)
        if sum(p["wrong_RGB5"] for p in px) != 1:
            raise ValueError("non-isolated finish mismatch inside full 5x5 scanline region")
        contextual = []
        for neighbour in (guest-16, guest+16):
            src, native = extract_source_frames(original_dir, windows_dir, neighbour)
            if compare(src,native)["wrong_RGB5_pixels"] != 0:
                raise ValueError("neighbour source/window not strictly identical")
            contextual.append({
                "guest":neighbour,
                "same_coordinate_original_RGB5_expanded":list(original_rgb5(src,x,y)),
                "same_coordinate_Windows_RGB8":list(native_rgb(native,x,y)),
                "frame_has_zero_wrong_RGB5_pixels":True,
            })
        per_pixel.append({
            "native_guest":guest,
            "original_video_callback":guest-1,
            "x":x,"y":y,
            "original_RGB5_expanded":list(original_rgb5(original,x,y)),
            "windows_RGB8":list(native_rgb(windows,x,y)),
            "five_by_five_actual_source_pixel_pairs":px,
            "previous_and_next_full_frame_source_exact_at_pixel":contextual,
            "full_frame_wrong_RGB5_pixels":1,
            "pixel_PPU_main_sub_OBJ_window_ownership_verified":False,
        })
    return {
        "schema":"qa08-two-isolated-authentic-original-native-finish-pixels/1",
        "status":"two_finish_source_pixel_positions_identified_no_renderer_fix",
        "original_authentic_source_callbacks":263,
        "native_full_5484_guest_CRC_sha256":EXPECTED_CRC,
        "exact_built_Windows_executable_sha256":EXPECTED_NATIVE_EXE,
        "all_other_2p_original_snes9x_reference_wrong_RGB5_pixels":EXPECTED_FULL_WRONG-2,
        "all_compared_reference_RGB5_pixels":263*W*H,
        "source_pairing":"original callback=f-1/native guest=f; no search",
        "source_geometry":[W,H],
        "source_green_normalization":"2014 Snes9x 6-bit green to 5-bit only",
        "isolated_source_pixels":per_pixel,
        "four_surrounding_guest_frames_full_exact":[*NEIGHBOURS],
        "source_original_effective_PPU_OBJ_window_math_proven":False,
        "actual_SNES_DAC_equivalence_proven":False,
        "guest_CPU_APU_clock_or_port_phase_proven":False,
        "release_QA08_QA10_4x_PAR_HD_acceptance":False,
        "next_discriminator":"original effective single-pixel main/sub OBJ, window, math, and native PPU owner at those exact two coordinates; do not patch a neighbouring pixel",
    }


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("original-dir","windows-dir","route","out"):
        parser.add_argument("--"+key,required=True,type=Path)
    args=parser.parse_args()
    result=analyze(args.original_dir,args.windows_dir,args.route)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    for p in result["isolated_source_pixels"]:
        print("QA08_ISOLATED_FINISH",f"guest={p['native_guest']}",
              f"x={p['x']} y={p['y']}",
              f"original={p['original_RGB5_expanded']}",
              f"windows={p['windows_RGB8']}", "same_neighbor_frames=2",
              "release=0")


if __name__=="__main__":
    main()
