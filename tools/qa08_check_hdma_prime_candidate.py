#!/usr/bin/env python3
"""Adversarial exact-frame check for an EXPERIMENTAL HDMA prime candidate.

Requires original accepted Snes9x archive, genuinely produced native
256x224 P7 raster and byte-identical original/native guest CRC transcript
from the unchanged 2P route. Does not alter/mask any output rows.
A successful frame alone cannot qualify every other channel or release QA.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from tools.qa08_accept_original_native_split_seam import (
    ORIGINAL_ZIP_SHA, ORIGINAL_2207_SHA, rgb5_match, W, H,
)

ORIGINAL_FRAME_MEMBER = "qa08-original-source-window/frame_002207_256x224.raw"
P7_HEADER = b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def compare(original: bytes, native_p7: bytes,
            original_crc: bytes, candidate_crc: bytes) -> dict:
    if (not original_crc or original_crc != candidate_crc
        or len(original_crc.splitlines()) != 2473):
        raise ValueError("native 2473-frame authentic route CRC transcript differs")
    if not native_p7.startswith(P7_HEADER):
        raise ValueError("candidate is not actual source-size 256x224 RGB_ALPHA P7")
    pixels = native_p7[len(P7_HEADER):]
    if len(pixels) != W * H * 4:
        raise ValueError("candidate source raster byte count mismatch")
    result = rgb5_match(original, pixels, with_rows=True)
    if (result["identical_RGB5_expanded_pixels"] != W * H
        or result["different_pixels"] != 0
        or result["different_pixels_by_original_output_row"] != []):
        raise ValueError(
            f"candidate still differs from original at "
            f"{result['different_pixels']} exact RGB pixels: "
            f"{result['different_pixels_by_original_output_row']}"
        )
    return {
        "schema": "qa08-HDMA-prime-native-candidate-exact-2P-256x224-rgb5/1",
        "status": "one-real-frame-source-RGB5-equal-with-CRC-replay",
        "original_callback_frame": 2207,
        "native_guest_frame": 2208,
        "actual_source_pixels_equal": W * H,
        "guest_CRC_entries_equal": 2473,
        "native_P7_SHA256": sha(native_p7),
        "original_Snes9x_RGB565_green6_to_native_green5_only": True,
        "source_pixels_mutated_or_masked": False,
        "other_native_frames_channels_checked": False,
        "production_HDMA_change_authorized": False,
        "physical_SNES_or_release_certified": False,
    }


def check(original_zip: Path, candidate_p7: Path,
          original_crc: Path, candidate_crc: Path) -> dict:
    zip_bytes = original_zip.read_bytes()
    if sha(zip_bytes) != ORIGINAL_ZIP_SHA:
        raise ValueError("original archive differs from accepted source ZIP")
    with zipfile.ZipFile(original_zip) as archive:
        original = archive.read(ORIGINAL_FRAME_MEMBER)
    if sha(original) != ORIGINAL_2207_SHA:
        raise ValueError("original callback2207 raster SHA changed")
    return compare(original, candidate_p7.read_bytes(),
                   original_crc.read_bytes(), candidate_crc.read_bytes())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip", required=True, type=Path)
    parser.add_argument("--candidate-p7", required=True, type=Path)
    parser.add_argument("--original-crc", required=True, type=Path)
    parser.add_argument("--candidate-crc", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = check(args.original_zip, args.candidate_p7,
                   args.original_crc, args.candidate_crc)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print("QA08_HDMA_PRIME_CANDIDATE_FRAME_EQUAL 57344/57344 "
          "full-channel-replay=not-certified")


if __name__ == "__main__":
    main()
