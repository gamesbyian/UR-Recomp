#!/usr/bin/env python3
"""Strict original 2P 37-callback RGB5 window vs REAL additional native PPUs.

A rank is a temporal discovery, not certification of guest phase or a
production-renderer correction. Only authentic on-disk source-size rasters,
complete full-route native CRCs and pinned original Snes9x captures qualify.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

try:
    from tools.qa08_accept_original_native_split_seam import (
        rgb5_match, W, H, ORIGINAL_2207_SHA,
    )
    from tools.qa08_compare_channel7_native_prime import decode_p7
    from tools.qa08_rank_original_postgo_motion import (
        ZIP_SHA, MANIFEST_SHA, WINDOW, check_original_frame,
    )
except ModuleNotFoundError:
    from qa08_accept_original_native_split_seam import (
        rgb5_match, W, H, ORIGINAL_2207_SHA,
    )
    from qa08_compare_channel7_native_prime import decode_p7
    from qa08_rank_original_postgo_motion import (
        ZIP_SHA, MANIFEST_SHA, WINDOW, check_original_frame,
    )

SCHEMA = "qa08-original-native-2P-moving-37window-actual-source-rgb5/1"
KINDS = ("stock", "global", "channel7", "channel57")
NATIVE_FRAMES = (2192, 2208, 2224)
CANDIDATE_PAIRS = {2192: 2191, 2224: 2223}
HEADER_FRAME = "qa08-original-source-window/frame_{:06d}_256x224.raw"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def original_window(archive: Path) -> dict[int, bytes]:
    raw = archive.read_bytes()
    if sha(raw) != ZIP_SHA:
        raise ValueError("original Snes9x 37-frame source archive SHA changed")
    with zipfile.ZipFile(archive) as z:
        manifest_raw = z.read("qa08-original-37frame-window.json")
        if sha(manifest_raw) != MANIFEST_SHA:
            raise ValueError("original 37-frame source manifest SHA changed")
        manifest = json.loads(manifest_raw)
        records = manifest.get("source_original_frames")
        if (not isinstance(records, list) or len(records) != len(WINDOW)
            or manifest.get("full_256x224_original_frames") != len(WINDOW)
            or manifest.get("same_input_guest_phase_and_camera_as_native_proven") is not False):
            raise ValueError("source original route/manifest not accepted")
        available = {
            name for name in z.namelist()
            if name.startswith("qa08-original-source-window/")
        }
        expected = {HEADER_FRAME.format(f) for f in WINDOW}
        if available != expected:
            raise ValueError("original callback archive missing/extra source frames")
        original = {}
        for f, row in zip(WINDOW, records):
            b = z.read(HEADER_FRAME.format(f))
            check_original_frame(b)
            if (row.get("original_Snesref_callback_frame_zero_based") != f
                or row.get("corresponding_original_retro_run_one_based") != f + 1
                or row.get("raw_B_G_R_X_SHA256") != sha(b)):
                raise ValueError("original executed callback source digest differs")
            original[f] = b
    if sha(original[2207]) != ORIGINAL_2207_SHA:
        raise ValueError("previous accepted original postGO exact source changed")
    return original


def check_crc(crcs: dict[str, bytes]) -> None:
    if set(crcs) != set(KINDS):
        raise ValueError("requires four complete independent guest CRC logs")
    for kind in KINDS:
        lines = crcs[kind].splitlines()
        if (len(lines) != 2473 or
            any(not row.startswith(b"0x") or len(row) != 10
                or any(v not in b"0123456789ABCDEF" for v in row[2:])
                for row in lines)):
            raise ValueError("native guest 2473-frame CRC transcript malformed")
    if len(set(crcs.values())) != 1:
        raise ValueError("native original-source guest CRC transcripts disagree")


def compare(original: dict[int, bytes], native: dict[str, dict[int, bytes]],
            crcs: dict[str, bytes], *, strict_original: bool = True) -> dict:
    if set(original) != set(WINDOW):
        raise ValueError("requires every original Snes9x callback in accepted window")
    if set(native) != set(KINDS):
        raise ValueError("requires four native original PPU source variants")
    if any(set(v) != set(NATIVE_FRAMES) for v in native.values()):
        raise ValueError("requires three actual native PPU scenes per guest process")
    check_crc(crcs)
    if strict_original and sha(original[2207]) != ORIGINAL_2207_SHA:
        raise ValueError("original accepted postGO source changed")
    for b in original.values():
        check_original_frame(b)

    decoded = {k: {f: decode_p7(raw) for f, raw in frames.items()}
               for k, frames in native.items()}
    # The already accepted post-GO global first-line-prime control must
    # still be exact, or the source correlation in this window is invalid.
    control = rgb5_match(original[2207], decoded["global"][2208])
    if control["different_pixels"]:
        raise ValueError("original/native accepted global-prime postGO source control changed")

    frames = []
    for guest in CANDIDATE_PAIRS:
        prespecified_original = CANDIDATE_PAIRS[guest]
        per_kind = {}
        for kind in KINDS:
            source = decoded[kind][guest]
            samples = []
            for callback in WINDOW:
                score = rgb5_match(original[callback], source)
                samples.append({
                    "original_callback": callback,
                    "same_RGB5_pixels": score["identical_RGB5_expanded_pixels"],
                    "different_RGB5_pixels": score["different_pixels"],
                })
            ranked = sorted(samples, key=lambda s: (
                -s["same_RGB5_pixels"], s["original_callback"]))
            prespecified = samples[prespecified_original - WINDOW[0]]
            per_kind[kind] = {
                "actual_native_P7_sha256": sha(native[kind][guest]),
                "prespecified_original_callback": prespecified_original,
                "prespecified_matching_RGB5_pixels": prespecified["same_RGB5_pixels"],
                "prespecified_wrong_RGB5_pixels": prespecified["different_RGB5_pixels"],
                "ranked_original_callback": ranked[0]["original_callback"],
                "ranked_matching_RGB5_pixels": ranked[0]["same_RGB5_pixels"],
                "runner_up_matching_RGB5_pixels": ranked[1]["same_RGB5_pixels"],
                "all_37_original_callback_scores": samples,
                "prespecified_pair_has_pixel_parity": (
                    prespecified["different_RGB5_pixels"] == 0),
                "ranked_pair_has_pixel_parity": (
                    ranked[0]["different_RGB5_pixels"] == 0),
            }
        frames.append({
            "native_guest_frame": guest,
            "original_phase_prespecified_by_prior_2207_to_2208_alignment": prespecified_original,
            "actual_original_source_sha256": sha(original[prespecified_original]),
            "four_real_source_dispositions": per_kind,
        })

    return {
        "schema": SCHEMA,
        "status": "real_native_2P_motion_compared_to_genuine_original_callback_window",
        "original_source_archive_sha256": ZIP_SHA,
        "source_geometry": [W, H],
        "actual_original_callback_window": [WINDOW[0], WINDOW[-1]],
        "native_source_guest_frames": list(NATIVE_FRAMES),
        "independent_actual_native_guest_processes": len(KINDS),
        "identical_guest_CRC_records": 2473,
        "previous_postGO_global_prime_control_exact_RGB5": True,
        "new_actual_native_original_results": frames,
        "ranked_callback_is_phase_discovery_not_guest_state_proof": True,
        "source_CPU_OAM_camera_phase_equivalence_for_extra_frames_proven": False,
        "other_2P_results_transition_and_1P_scenes_proven": False,
        "native_production_renderer_fix_authorized": False,
        "physical_SNES_or_release_approved": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip", type=Path, required=True)
    for kind in KINDS:
        parser.add_argument("--" + kind + "-dir", type=Path, required=True)
        parser.add_argument("--" + kind + "-crc", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    originals = original_window(args.original_zip)
    native = {
        kind: {
            frame: (getattr(args, kind + "_dir") /
                    f"ur-baldosa-original-source-{frame:06d}.pam").read_bytes()
            for frame in NATIVE_FRAMES}
        for kind in KINDS
    }
    crc = {k: getattr(args, k + "_crc").read_bytes() for k in KINDS}
    result = compare(originals, native, crc)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("QA08_ORIGINAL_NATIVE_2P_MOVING_SOURCE_WINDOW "
          "native_observed=2 original_callbacks=37 phase_equivalence=not_proven")


if __name__ == "__main__":
    main()
