#!/usr/bin/env python3
"""Compare REAL stock, global-prime and channel-7-only native 2P PPUs.

Experimental, original-reference-grounded and intentionally NOT a shipping
renderer gate. Fail closed on wrong source archives, controls or guest route;
report actual channel-7 image failure as a scientific negative, not a
tolerance, crop or invented sprite/scanline explanation.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

try:
    from tools.qa08_accept_original_native_split_seam import (
        ORIGINAL_ZIP_SHA, ORIGINAL_2207_SHA, rgb5_match, W, H,
    )
    from tools.qa08_compare_original_countdown_prime import (
        BASELINE_SHA as COUNTDOWN_STOCK_SHA,
        TRIAL_SHA as COUNTDOWN_GLOBAL_SHA,
    )
    from tools.qa08_compare_native_hdma_prime_trial import (
        BASELINE_REAL_SHA256, HEADER,
    )
except ModuleNotFoundError:
    from qa08_accept_original_native_split_seam import (
        ORIGINAL_ZIP_SHA, ORIGINAL_2207_SHA, rgb5_match, W, H,
    )
    from qa08_compare_original_countdown_prime import (
        BASELINE_SHA as COUNTDOWN_STOCK_SHA,
        TRIAL_SHA as COUNTDOWN_GLOBAL_SHA,
    )
    from qa08_compare_native_hdma_prime_trial import (
        BASELINE_REAL_SHA256, HEADER,
    )

SCHEMA = "qa08-original-native-channel7-selective-prime-3scene/1"
FRAMES = (400, 1856, 2208)
COUNTDOWN_ZIP_SHA = "56ec0011a3559f5953578c495d080d0150f2a06fb7a76c2e437fab781e2b2ce6"
ORIGINAL_FILES = {
    1856: "qa08-original-countdown-17/frame_001855_256x224.raw",
    2208: "qa08-original-source-window/frame_002207_256x224.raw",
}


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def decode_p7(data: bytes) -> bytes:
    if not data.startswith(HEADER) or len(data) != len(HEADER) + W * H * 4:
        raise ValueError("not genuine complete 256x224 native original-source RGB_ALPHA P7")
    return data[len(HEADER):]


def pixels_changed(left: bytes, right: bytes) -> dict:
    if len(left) != W * H * 4 or len(right) != len(left):
        raise ValueError("not two complete source RGBA rasters")
    rows = Counter()
    alpha = 0
    examples = []
    for i in range(W * H):
        p = i * 4
        if left[p:p + 4] == right[p:p + 4]:
            continue
        y, x = divmod(i, W)
        rows[y] += 1
        alpha += left[p + 3] != right[p + 3]
        if len(examples) < 6:
            examples.append({"xy": [x, y],
                             "before": left[p:p + 4].hex(),
                             "after": right[p:p + 4].hex()})
    return {"changed_RGBA_pixels": sum(rows.values()),
            "changed_alpha_pixels": alpha,
            "changed_rows": [{"y": y, "count": rows[y]} for y in sorted(rows)],
            "examples": examples}


def check_crcs(crcs: dict[str, bytes]) -> None:
    if set(crcs) != {"stock", "global", "channel7"}:
        raise ValueError("three native process CRC transcripts required")
    first = crcs["stock"]
    if (not first or any(value != first for value in crcs.values())
        or len(first.splitlines()) != 2473
        or any(len(line) != 10 or not line.startswith(b"0x")
               or any(c not in b"0123456789ABCDEF" for c in line[2:])
               for line in first.splitlines())):
        raise ValueError("three genuine 2473-frame source guest CRC streams differ")


def compare(native: dict[str, dict[int, bytes]],
            originals: dict[int, bytes], crcs: dict[str, bytes],
            *, strict_reference: bool = True) -> dict:
    if set(native) != {"stock", "global", "channel7"}:
        raise ValueError("requires three independently executed native versions")
    if any(set(run) != set(FRAMES) for run in native.values()):
        raise ValueError("every native version must supply exactly three actual frames")
    if set(originals) != {1856, 2208}:
        raise ValueError("requires two genuine original-emulator source frames")
    check_crcs(crcs)
    decoded = {kind: {frame: decode_p7(data) for frame, data in captures.items()}
               for kind, captures in native.items()}
    if strict_reference and (
        digest(native["stock"][2208]) != BASELINE_REAL_SHA256
        or digest(native["stock"][1856]) != COUNTDOWN_STOCK_SHA
        or digest(native["global"][1856]) != COUNTDOWN_GLOBAL_SHA
        or digest(originals[2208]) != ORIGINAL_2207_SHA
    ):
        raise ValueError("previously accepted native/original controls have changed")

    scenes = []
    for frame in FRAMES:
        n = {kind: decoded[kind][frame] for kind in decoded}
        stock_to_global = pixels_changed(n["stock"], n["global"])
        stock_to_channel7 = pixels_changed(n["stock"], n["channel7"])
        global_to_channel7 = pixels_changed(n["global"], n["channel7"])
        record = {
            "native_guest_frame": frame,
            "scene": {400: "2P-frontend", 1856: "2P-countdown",
                      2208: "2P-postGO"}[frame],
            "native_P7_SHA256": {kind: digest(native[kind][frame])
                                  for kind in native},
            "stock_to_global": stock_to_global,
            "stock_to_channel7": stock_to_channel7,
            "global_to_channel7": global_to_channel7,
        }
        if frame in originals:
            scores = {kind: rgb5_match(originals[frame], n[kind],
                                      with_rows=True) for kind in n}
            # Global experiment is the positive source control, not a
            # source-accuracy assertion invented by this new study.
            if scores["global"]["identical_RGB5_expanded_pixels"] != W * H:
                raise ValueError("accepted all-channel source-pixel control regressed")
            record["original_Snes9x_callback_frame"] = frame - 1
            record["original_BGRX_SHA256"] = digest(originals[frame])
            record["all_57344_RGB5_pixel_original_comparisons"] = scores
            record["channel7_exact_original_RGB5"] = (
                scores["channel7"]["identical_RGB5_expanded_pixels"] == W * H)
        scenes.append(record)

    preserved_alpha = all(
        not scene["stock_to_channel7"]["changed_alpha_pixels"]
        for scene in scenes)
    frontend_unchanged = scenes[0]["stock_to_channel7"]["changed_RGBA_pixels"] == 0
    original_exact_both = all(
        scene["channel7_exact_original_RGB5"] for scene in scenes[1:])
    result = {
        "schema": SCHEMA,
        "status": ("experimental_channel7_three_scene_source_consistent"
                   if original_exact_both and preserved_alpha and frontend_unchanged
                   else "experimental_channel7_source_divergence_observed"),
        "source_size": [W, H],
        "real_guest_frames": list(FRAMES),
        "native_process_count": 3,
        "identical_guest_CRC_entries": 2473,
        "original_reference_zip_sha256": {
            "countdown": COUNTDOWN_ZIP_SHA, "postGO": ORIGINAL_ZIP_SHA,
        },
        "three_scene_native_source_pixels_compared_per_process": len(FRAMES) * W * H,
        "original_2P_scenes_exact_in_channel7_experiment": original_exact_both,
        "frontend_unchanged_from_stock": frontend_unchanged,
        "source_alpha_preserved_vs_stock": preserved_alpha,
        "actual_source_dispositions": scenes,
        "source_frame_phase_and_guest_camera_alignment_proven": False,
        "effective_per_scanline_channel5_colour_math_proven": False,
        "line112_OAM_priority_and_final_sprite_ownership_proven": False,
        "other_1P_2P_transitions_results_and_moving_frames_proven": False,
        "upstream_Gundam_Wing_or_hardware_compatibility_proven": False,
        "true_342_world_and_4x_original_reverified": False,
        "shipping_renderer_change_authorized": False,
    }
    return result


def original_image(archive: Path, expected_zip_sha: str, member: str) -> bytes:
    if digest(archive.read_bytes()) != expected_zip_sha:
        raise ValueError("original Snes9x source ZIP SHA changed")
    with zipfile.ZipFile(archive) as z:
        return z.read(member)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("stock", "global", "channel7"):
        parser.add_argument("--" + name + "-dir", required=True, type=Path)
        parser.add_argument("--" + name + "-crc", required=True, type=Path)
    parser.add_argument("--original-countdown-zip", required=True, type=Path)
    parser.add_argument("--original-postgo-zip", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    def images(directory: Path) -> dict[int, bytes]:
        return {f: (directory / f"ur-baldosa-original-source-{f:06d}.pam").read_bytes()
                for f in FRAMES}
    native = {k: images(getattr(args, k + "_dir"))
              for k in ("stock", "global", "channel7")}
    originals = {
        1856: original_image(args.original_countdown_zip, COUNTDOWN_ZIP_SHA,
                             ORIGINAL_FILES[1856]),
        2208: original_image(args.original_postgo_zip, ORIGINAL_ZIP_SHA,
                             ORIGINAL_FILES[2208]),
    }
    crcs = {k: getattr(args, k + "_crc").read_bytes()
            for k in ("stock", "global", "channel7")}
    result = compare(native, originals, crcs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("QA08_REAL_CHANNEL7_PRIME "
          f"status={result['status']} "
          "production_correctness=unproven")


if __name__ == "__main__":
    main()
