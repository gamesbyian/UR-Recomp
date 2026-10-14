#!/usr/bin/env python3
"""Measure each of 37 real original Snes9x vs two real native Original frames.

No guessed source pixel substitutions, presentation crops, hue tolerances,
frame-lag re-pairing or automated claim of global renderer acceptability.
The selected original one-frame pairing is retained for all 37 adjacent
frame-index matches; an apparent frame-lag counterexample is not repaired.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

try:
    from tools.qa08_accept_original_native_split_seam import rgb5_match, W, H
except ModuleNotFoundError:
    from qa08_accept_original_native_split_seam import rgb5_match, W, H

ORIGINAL_ZIP_SHA = "6e5d488230c11d3dfcd144b6a7cbc8c25d7acfcb4f95b776a85071dd3487f5e3"
ORIGINAL_MANIFEST_SHA = "29856fa4f13bfc679b60240de80bd48b8c035801b56e0fbb3e17472a06836787"
ORIGINAL_SCHEMA = "qa08-source-original-2P-37-full-PPU-raster-frames-2188-2224/1"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SCRIPT_SHA = "94eaa5ffb487d9b227e34965c1d2ee09efe3dac06ade595f7dad05315dfc5221"
WRAM_SHA = "9350bcb02f3cbf490678c5276245ec2c7fe36b9078bfab9e912d86c5cbc93bf6"
NATIVE_BASE_2208_SHA = "a946c9ebb54775639b8fd87a6861af0408cceed4896e58be05908c4a4491c67f"
NATIVE_SIZE = b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"
ORIGINAL_START = 2188
ORIGINAL_END = 2224


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("original source manifest repeated a key")
        out[key] = value
    return out


def source_frames(original_zip: Path) -> list[tuple[int, bytes, str]]:
    raw = original_zip.read_bytes()
    if digest(raw) != ORIGINAL_ZIP_SHA:
        raise ValueError("accepted original Snes9x artifact ZIP checksum changed")
    with zipfile.ZipFile(original_zip) as archive:
        manifest_raw = archive.read("qa08-original-37frame-window.json")
        manifest = json.loads(manifest_raw, object_pairs_hook=unique)
        records = manifest.get("source_original_frames")
        if (digest(manifest_raw) != ORIGINAL_MANIFEST_SHA
            or manifest.get("schema") != ORIGINAL_SCHEMA
            or manifest.get("original_ROM_SHA256") != ROM_SHA
            or manifest.get("original_script_SHA256") != SCRIPT_SHA
            or manifest.get("original_t480_WRAM_SHA256") != WRAM_SHA
            or manifest.get("same_input_guest_phase_and_camera_as_native_proven") is not False
            or manifest.get("full_256x224_original_frames") != 37
            or not isinstance(records, list) or len(records) != 37):
            raise ValueError("independent original 37-frame source/ROM/script receipt changed")
        frames = []
        for i, row in enumerate(records):
            frame = ORIGINAL_START + i
            if (row.get("original_Snesref_callback_frame_zero_based") != frame
                or row.get("corresponding_original_retro_run_one_based") != frame + 1):
                raise ValueError("original reference output frame identity/phase changed")
            data = archive.read(
                f"qa08-original-source-window/frame_{frame:06d}_256x224.raw"
            )
            sha = digest(data)
            if (len(data) != W * H * 4
                or row.get("raw_B_G_R_X_SHA256") != sha):
                raise ValueError("original source image bytes or manifest digest changed")
            frames.append((frame, data, sha))
    return frames


def native_frames(folder: Path, label: str) -> dict[int, tuple[bytes, str]]:
    pattern = "ur-baldosa-original-source-*.pam"
    found = sorted(folder.glob(pattern))
    if len(found) != 37:
        raise ValueError(f"{label} did not capture exactly 37 original-size P7 source images")
    output = {}
    for guest in range(ORIGINAL_START + 1, ORIGINAL_END + 2):
        target = folder / f"ur-baldosa-original-source-{guest:06d}.pam"
        if target not in found:
            raise ValueError(f"{label} missing exact native guest {guest}")
        raw = target.read_bytes()
        if not raw.startswith(NATIVE_SIZE) or len(raw) != len(NATIVE_SIZE) + W * H * 4:
            raise ValueError(f"{label} native guest {guest} not true 256x224 original P7")
        output[guest] = (raw[len(NATIVE_SIZE):], digest(raw))
    if label == "unchanged" and output[2208][1] != NATIVE_BASE_2208_SHA:
        raise ValueError("genuine native frame2208 baseline no longer SHA-accepted")
    return output


def compare(original: list[tuple[int, bytes, str]],
            unchanged: dict[int, tuple[bytes, str]],
            experiment: dict[int, tuple[bytes, str]],
            baseline_crc: bytes, trial_crc: bytes) -> dict:
    if (len(original) != 37 or len(unchanged) != 37 or len(experiment) != 37
        or not baseline_crc or baseline_crc != trial_crc
        or len(baseline_crc.splitlines()) != 2473):
        raise ValueError("incomplete or divergent independent native 2P inputs or original source series")
    measured = []
    fixed = moved = 0
    for original_frame, original_pixels, original_sha in original:
        guest = original_frame + 1
        base_pixels, base_sha = unchanged[guest]
        trial_pixels, trial_sha = experiment[guest]
        first = rgb5_match(original_pixels, base_pixels, with_rows=True)
        second = rgb5_match(original_pixels, trial_pixels, with_rows=True)
        diff = sum(
            base_pixels[i:i + 4] != trial_pixels[i:i + 4]
            for i in range(0, W * H * 4, 4)
        )
        fixed += first["different_pixels"] == 0
        moved += second["different_pixels"] == 0
        measured.append({
            "original_source_callback_frame": original_frame,
            "native_guest_frame": guest,
            "original_BGRX_SHA256": original_sha,
            "native_unchanged_P7_SHA256": base_sha,
            "native_experimental_P7_SHA256": trial_sha,
            "original_vs_unmodified_native_RGB5_same": first["identical_RGB5_expanded_pixels"],
            "original_vs_prime_consumed_native_RGB5_same": second["identical_RGB5_expanded_pixels"],
            "unmodified_native_mismatched_rows": first["different_pixels_by_original_output_row"],
            "prime_consumed_native_mismatched_rows": second["different_pixels_by_original_output_row"],
            "experimental_vs_unmodified_native_exact_changed_RGBA_source_pixels": diff,
        })
    all_original_exact = moved == 37
    return {
        "schema": "qa08-original-native-37-frame-2P-HDMA-prime-causal-comparison/1",
        "status": ("all-37-original-source-frames-RGB5-exact" if all_original_exact
                   else "source-37frame-original-native-counterexamples-retained"),
        "original_reference_run": 38543766102,
        "original_reference_zip_SHA256": ORIGINAL_ZIP_SHA,
        "native_original_source_size": [W, H],
        "source_frame_window_original_callback_inclusive": [ORIGINAL_START, ORIGINAL_END],
        "native_guest_frame_window_inclusive": [ORIGINAL_START+1, ORIGINAL_END+1],
        "frames_compared_exact": len(measured),
        "source_pixels_checked_per_frame": W * H,
        "original_vs_unchanged_native_RGB5_full_matching_frame_count": fixed,
        "original_vs_consumed_prime_RGB5_full_matching_frame_count": moved,
        "original_vs_consumed_prime_all_37_source_pixels_exact": all_original_exact,
        "actual_total_native_2P_guest_CRC_records_each": 2473,
        "native_guest_CRC_byte_series_identical": True,
        "comparisons": measured,
        "corrected_native_source_pixels_mutated_for_comparison": False,
        "same_frame_physical_SNES_hardware_proven": False,
        "upstream_cross_game_HDMA_first_line_compatibility_proven": False,
        "HD_racer_or_Widescreen_release_admitted": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-zip", required=True, type=Path)
    p.add_argument("--unchanged-dir", required=True, type=Path)
    p.add_argument("--experiment-dir", required=True, type=Path)
    p.add_argument("--unchanged-crc", required=True, type=Path)
    p.add_argument("--experiment-crc", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    result = compare(
        source_frames(a.original_zip),
        native_frames(a.unchanged_dir, "unchanged"),
        native_frames(a.experiment_dir, "experiment"),
        a.unchanged_crc.read_bytes(), a.experiment_crc.read_bytes(),
    )
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("QA08_ORIGINAL_NATIVE_REAL_37FRAME_SOURCE "
          f"status={result['status']} "
          f"full_exact={result['original_vs_consumed_prime_RGB5_full_matching_frame_count']}/37 "
          "production_HDMA_patch=not_admitted")


if __name__ == "__main__":
    main()
