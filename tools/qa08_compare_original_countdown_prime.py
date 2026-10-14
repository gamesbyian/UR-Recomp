#!/usr/bin/env python3
"""Adversarial real original-Snes9x countdown versus native HDMA-prime sources.

Compare *every* RGB5 pixel, including seam/window rows, over a bounded
real-original callback phase window. Do not promote highest-scoring temporal
candidate to accepted source alignment without independent guest evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

try:
    from tools.qa08_accept_original_native_split_seam import (
        rgb5_match, W, H, INPUT_SHA, ROM_SHA, WRAM_SHA,
    )
except ModuleNotFoundError:
    from qa08_accept_original_native_split_seam import (
        rgb5_match, W, H, INPUT_SHA, ROM_SHA, WRAM_SHA,
    )

WINDOW = tuple(range(1848, 1865))
PRESELECTED_CALLBACK = 1855
NATIVE_GUEST = 1856
NATIVE_ZIP_SHA = "298c73f095c2ecdebc99c0e7392dbc4112fecd61eb8feb5106fb2921e1cdd0ec"
P7_HEADER = b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"
BASELINE_SHA = "6aea6cebaf1292d962ad5ce01a73966bb0ad8948095d1e73b155712cac41039a"
TRIAL_SHA = "ed35731cde55e927165f173c1db29c27b3b7eeff19862fbca27db3467cb8bc87"
BASE_PREFIX = "qa08-native-baseline"
TRIAL_PREFIX = "qa08-native-experiment"


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def native(zip_bytes: bytes, strict_archive: bool = True) -> dict:
    if strict_archive and sha(zip_bytes) != NATIVE_ZIP_SHA:
        raise ValueError("source-accepted native two-process ZIP SHA changed")
    with zipfile.ZipFile(__import__("io").BytesIO(zip_bytes)) as z:
        bpath = f"{BASE_PREFIX}/ur-baldosa-original-source-{NATIVE_GUEST:06d}.pam"
        tpath = f"{TRIAL_PREFIX}/ur-baldosa-original-source-{NATIVE_GUEST:06d}.pam"
        b, t = z.read(bpath), z.read(tpath)
        if not b.startswith(P7_HEADER) or not t.startswith(P7_HEADER):
            raise ValueError("native sample is not native 256x224 original source P7")
        if len(b) != len(P7_HEADER) + W * H * 4 or len(t) != len(b):
            raise ValueError("native sample source length changed")
        if (sha(b) != BASELINE_SHA or sha(t) != TRIAL_SHA):
            raise ValueError("accepted before/after native countdown P7 digests changed")
        one = z.read("qa08-counterfactual/baseline/fd/crc.txt")
        two = z.read("qa08-counterfactual/experiment/fd/crc.txt")
        if not one or one != two or len(one.splitlines()) != 2473:
            raise ValueError("two accepted native processes lose full 2473 guest CRC parity")
        return {"stock": b[len(P7_HEADER):], "global_prime": t[len(P7_HEADER):],
                "stock_p7_sha256": sha(b), "global_prime_p7_sha256": sha(t)}


def compare(original: dict[int, bytes], captures: dict) -> dict:
    if set(original) != set(WINDOW):
        raise ValueError("requires exactly 17 consecutive original Snes9x callbacks")
    rows = []
    for frame in WINDOW:
        pixels = original[frame]
        if len(pixels) != W * H * 4:
            raise ValueError("original countdown BGRX source-size frame truncated")
        row = {
            "original_Snes9x_callback_frame": frame,
            "original_one_based_script_frame": frame + 1,
            "actual_original_source_BGRX_SHA256": sha(pixels),
        }
        for title in ("stock", "global_prime"):
            score = rgb5_match(pixels, captures[title], with_rows=frame==PRESELECTED_CALLBACK)
            row[title + "_normalized_matching_pixels"] = score["identical_RGB5_expanded_pixels"]
            row[title + "_different_pixels"] = score["different_pixels"]
            if frame == PRESELECTED_CALLBACK:
                row[title + "_prespecified_frame_changed_rows"] = score[
                    "different_pixels_by_original_output_row"]
        rows.append(row)
    ranks = {}
    for title in ("stock", "global_prime"):
        ordered = sorted(rows, key=lambda v: (
            -v[title + "_normalized_matching_pixels"],
            v["original_Snes9x_callback_frame"]))
        ranks[title] = {
            "best_original_callback": ordered[0]["original_Snes9x_callback_frame"],
            "best_matching_pixels": ordered[0][title + "_normalized_matching_pixels"],
            "second_best_matching_pixels": ordered[1][title + "_normalized_matching_pixels"],
            "best_matching_fraction": ordered[0][title + "_normalized_matching_pixels"] / (W * H),
            "prespecified_callback1855_matches": rows[PRESELECTED_CALLBACK - WINDOW[0]][
                title + "_normalized_matching_pixels"],
        }
    before = ranks["stock"]["prespecified_callback1855_matches"]
    after = ranks["global_prime"]["prespecified_callback1855_matches"]
    return {
        "schema": "qa08-original-countdown-17-Snes9x-PPU-vs-native-2P-prime/1",
        "status": "independent-real-original-and-native-source-countdown-ranked",
        "original_source_callback_window": [WINDOW[0], WINDOW[-1]],
        "native_frame": NATIVE_GUEST,
        "prespecified_original_callback_for_native_guest1856": PRESELECTED_CALLBACK,
        "original_rom_sha256": ROM_SHA,
        "original_script_sha256": INPUT_SHA,
        "original_t480_wram_sha256": WRAM_SHA,
        "native_real_two_run_artifact_sha256": NATIVE_ZIP_SHA,
        "native_frame_source_sha256": {
            "stock": captures["stock_p7_sha256"],
            "global_prime": captures["global_prime_p7_sha256"],
        },
        "real_source_size": [W, H],
        "normalized_RGB5_comparison_pixels_each_original_frame": W * H,
        "prespecified_phase_global_prime_minus_stock_matching_pixels": after - before,
        "does_prespecified_global_prime_match_more_original_pixels": after > before,
        "source_normalization": "Snes9x RGB565 green6 to native RGB5 only",
        "original_callback_phase_search_is_discovery_not_independent_frame_alignment": True,
        "original_guest_state_and_source_PPU_event_phase_equivalence_proven": False,
        "original_hardware_raster_or_global_prime_correctness_proven": False,
        "window_OAM_HDMA_register_effects_independently_caused": False,
        "results": rows,
        "ranked_native_source_comparisons": ranks,
    }


def check(original_dir: Path, native_zip: Path, script: Path,
          original_t480_wram: Path, original_log: Path) -> dict:
    if (sha(script.read_bytes()) != INPUT_SHA or
        sha(original_t480_wram.read_bytes()) != WRAM_SHA or
        "script f=2473 quit" not in original_log.read_text(errors="replace")):
        raise ValueError("original source USA 2P route, t480 or full-run receipt changed")
    paths = sorted(original_dir.glob("frame_*.raw"))
    wanted = {f"frame_{f:06d}_{W}x{H}.raw" for f in WINDOW}
    if {p.name for p in paths} != wanted or len(paths) != len(WINDOW):
        raise ValueError("original callback frame archive missing/extra/cropped")
    source = {frame: (original_dir / f"frame_{frame:06d}_{W}x{H}.raw").read_bytes()
              for frame in WINDOW}
    return compare(source, native(native_zip.read_bytes()))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-dir", type=Path, required=True)
    p.add_argument("--native-zip", type=Path, required=True)
    p.add_argument("--original-script", type=Path, required=True)
    p.add_argument("--original-t480-wram", type=Path, required=True)
    p.add_argument("--original-log", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    result = check(a.original_dir, a.native_zip, a.original_script,
                   a.original_t480_wram, a.original_log)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    ranks = result["ranked_native_source_comparisons"]
    print("QA08_ORIGINAL_NATIVE_2P_COUNTDOWN_SOURCE "
          f"stock_best_callback={ranks['stock']['best_original_callback']} "
          f"prime_best_callback={ranks['global_prime']['best_original_callback']} "
          f"prespecified_delta={result['prespecified_phase_global_prime_minus_stock_matching_pixels']} "
          "gameplay_state_alignment=unverified")


if __name__ == "__main__":
    main()
