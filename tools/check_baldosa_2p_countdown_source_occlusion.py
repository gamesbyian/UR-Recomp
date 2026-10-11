#!/usr/bin/env python3
"""Original PPU 2P racer-source countdown-foreground observation (QA-08).

Consumes only existing original PPU same-frame stock rasters and 12 native
source planes with independently validated per-slot provenance. This observes
colour differences; it does NOT identify the winning BG/OBJ/window layer,
give a replaceable racer mask or enable any HD sprite.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

try:
    from tools.check_baldosa_wide_single_slot_source import read_source
    from tools.check_baldosa_wide_slot_final_visibility import read_pam, WIDTH, HEIGHT
except ModuleNotFoundError:
    from check_baldosa_wide_single_slot_source import read_source
    from check_baldosa_wide_slot_final_visibility import read_pam, WIDTH, HEIGHT

FRAMES = (1856, 1872, 1888)
SLOTS = (96, 97, 98, 99)
EXISTING_CAPTURED_FRAMES = [1808, 1824, 1840, 1856, 1872, 1888]
COUNTDOWN_RGB = (57, 57, 255)


def verified_frame(root: Path, frame: int) -> dict:
    if frame not in FRAMES:
        raise ValueError("only bounded authentic moving two-player frames")
    original = read_pam(root / "baldosa-ws342-captures" /
                        f"ur-baldosa-ws342-{frame:06d}.pam")
    stock_digest = hashlib.sha256(original).hexdigest()
    per_slot = {}
    masks = {"upper": set(), "lower": set()}
    for slot in SLOTS:
        source_file = (root / "baldosa-ws342-obj-slots" /
                       f"ur-baldosa-ws342-obj-slot{slot}-frame{frame:06d}.pam")
        report_path = (root / "baldosa-evidence" /
                       (f"ws342_obj_slot_{slot}" +
                        (f"_frame{frame}" if frame != 1856 else "") + ".json"))
        source = read_pam(source_file)
        meta = read_source(source_file, slot)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if (meta["guest_frame"] != frame or
            report.get("schema_version") != 1 or
            report.get("status") != "passed" or
            report.get("source_log_matches_pam") is not True or
            report.get("identical_complete_original_342_rasters") != 6 or
            report.get("differing_original_rasters") != [] or
            report.get("shared_full_frame_guest_ids") != EXISTING_CAPTURED_FRAMES or
            report.get("minimum_shared_frames") != 4 or
            report.get("source") != meta or
            report.get("source_frame_main_raster_sha256") != stock_digest or
            report.get("guest_crc_comparison") !=
                "Externally enforced byte-exact in native workflow"):
            raise ValueError(f"source or complete Original PPU provenance invalid: {slot}/{frame}")
        emitted = meta["top_opaque_source_pixels"] + meta["bottom_opaque_source_pixels"]
        if not emitted:
            raise ValueError("unexpected missing real 2P source")
        if slot >= 98 and meta["bottom_opaque_source_pixels"]:
            raise ValueError("upper split source alpha leaked below analytic half")
        if slot <= 97 and meta["top_opaque_source_pixels"]:
            raise ValueError("lower split source alpha leaked above analytic half")
        equal = blue = 0
        for pixel in range(WIDTH * HEIGHT):
            i = 4 * pixel
            if not source[i + 3]:
                continue
            masks["upper" if slot >= 98 else "lower"].add(pixel)
            equal += original[i:i + 3] == source[i:i + 3]
            blue += original[i:i + 3] == bytes(COUNTDOWN_RGB)
        per_slot[str(slot)] = {
            "source_rgba_sha256": meta["source_sha256"],
            "source_opaque_alpha_mask_sha256": hashlib.sha256(bytes(
                int(source[at + 3] != 0)
                for at in range(0, len(source), 4))).hexdigest(),
            "source_emitted_pixels": emitted,
            "source_rgb_matches_final_original": equal,
            "source_rgb_differs_final_original": emitted - equal,
            "final_original_is_blue_over_source": blue,
        }
    if masks["upper"] & masks["lower"]:
        raise ValueError("original OBJ bands overlap unexpectedly")
    # Count every stock Original RGB match to the visually observed
    # countdown-blue colour, not only those inside racer source alpha.
    # This is a temporal colour mask, emphatically not an OBJ/BG owner mask.
    full_blue = bytes(
        int(original[at:at + 3] == bytes(COUNTDOWN_RGB))
        for at in range(0, len(original), 4))
    blue_points = [pos for pos, flag in enumerate(full_blue) if flag]
    blue_x = [pos % WIDTH for pos in blue_points]
    blue_y = [pos // WIDTH for pos in blue_points]
    blue_bbox = ([min(blue_x), min(blue_y), max(blue_x), max(blue_y)]
                 if blue_points else None)
    by_band = {}
    for band, mask in masks.items():
        if not mask:
            raise ValueError("missing independent source for split band")
        colours = Counter(
            tuple(original[4 * pos:4 * pos + 3]) for pos in mask)
        blue = colours[COUNTDOWN_RGB]
        by_band[band] = {
            "distinct_original_emitted_coordinates": len(mask),
            "source_alpha_union_mask_sha256": hashlib.sha256(bytes(
                int(pos in mask) for pos in range(WIDTH * HEIGHT))).hexdigest(),
            "blue_final_original_coordinates": blue,
            "all_source_coordinates_final_blue": blue == len(mask),
            "bounded_most_common_original_rgb": [
                {"rgb": list(rgb), "pixels": count}
                for rgb, count in colours.most_common(5)
            ],
        }
    return {
        "guest_frame": frame,
        "original_unmodified_342x224_sha256": stock_digest,
        "verified_independent_slot_sources": 4,
        "full_original_blue_rgb_mask_sha256": hashlib.sha256(full_blue).hexdigest(),
        "full_original_blue_rgb_pixel_count": len(blue_points),
        "full_original_blue_rgb_bbox": blue_bbox,
        "per_slot": per_slot,
        "source_union_by_raster_band": by_band,
    }


def assess(root: Path) -> dict:
    frames = {str(frame): verified_frame(root, frame) for frame in FRAMES}
    if len({r["original_unmodified_342x224_sha256"] for r in frames.values()}) != 3:
        raise ValueError("not three distinct complete Original moving frames")
    # The blue "2" spans an identical set of native Original raster pixels
    # while real moving racer source planes change underneath it.
    if (frames["1872"]["full_original_blue_rgb_mask_sha256"] !=
            frames["1888"]["full_original_blue_rgb_mask_sha256"] or
            frames["1872"]["full_original_blue_rgb_pixel_count"] !=
                frames["1888"]["full_original_blue_rgb_pixel_count"]):
        raise ValueError("native full-frame countdown blue overlay mask changed across moving 2P frames")
    if (frames["1856"]["full_original_blue_rgb_mask_sha256"] ==
            frames["1872"]["full_original_blue_rgb_mask_sha256"]):
        raise ValueError("pre-countdown and covered original blue masks incorrectly identical")
    if any(frames["1872"]["per_slot"][str(slot)]["source_opaque_alpha_mask_sha256"] ==
           frames["1888"]["per_slot"][str(slot)]["source_opaque_alpha_mask_sha256"]
           for slot in (96, 97)):
        raise ValueError("lower source OAM alpha is static, not independently changing behind the overlay")
    if (frames["1872"]["source_union_by_raster_band"]["lower"]["source_alpha_union_mask_sha256"] ==
            frames["1888"]["source_union_by_raster_band"]["lower"]["source_alpha_union_mask_sha256"]):
        raise ValueError("lower source union is frozen despite independently moving per-slot OAM")
    for frame in FRAMES:
        row = frames[str(frame)]
        lower = row["source_union_by_raster_band"]["lower"]
        if row["per_slot"]["98"]["source_rgb_matches_final_original"] == 0:
            raise ValueError("authentic upper player positive Original witness absent")
        if frame == 1856:
            if (lower["all_source_coordinates_final_blue"] or
                row["per_slot"]["96"]["source_rgb_matches_final_original"] == 0):
                raise ValueError("authentic visible pre-overlay lower racer missing")
        elif (not lower["all_source_coordinates_final_blue"] or
              any(row["per_slot"][str(slot)]["source_rgb_matches_final_original"]
                  for slot in (96, 97))):
            raise ValueError("original 2P lower countdown-covering witness changed")
    return {
        "schema_version": 1,
        "status": "observed-original-2p-lower-source-covered-by-countdown-color",
        "exact_original_guest_frames": list(FRAMES),
        "independently_verified_source_exports": 12,
        "source_slot_per_view": {"upper": [98, 99], "lower": [96, 97]},
        "original_logical_raster": [WIDTH, HEIGHT],
        "countdown_2_uniform_rgb": list(COUNTDOWN_RGB),
        "countdown_2_blue_final_mask_temporally_equal_1872_1888": True,
        "source_slot_rgb_and_alpha_changed_while_blue_mask_constant": True,
        "source_union_changed_while_full_blue_mask_constant": True,
        "per_original_frame": frames,
        "foreground_numeral_source_layer_proven": False,
        "per_source_final_ppu_causality_proven": False,
        "safe_to_promote_hd_racer_rendering": False,
        "limits": ("At native frames1872/1888 all lower-racer source-alpha "
                   "coordinates in unmodified Original are uniformly blue, "
                   "matching the visually observed large countdown '2'. "
                   "Pixel-colour agreement alone does NOT reveal final BG/OBJ "
                   "priority, justify a generalized foreground mask, or "
                   "authorize original sprite removal or new Remastered art."),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-artifact-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = assess(args.native_artifact_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    for frame in (1872, 1888):
        band = result["per_original_frame"][str(frame)]["source_union_by_raster_band"]["lower"]
        print(f"UR_QA08_ORIGINAL_2P_COUNTDOWN_COVER frame={frame} "
              f"blue={band['blue_final_original_coordinates']}/"
              f"{band['distinct_original_emitted_coordinates']} HD_admitted=0")


if __name__ == "__main__":
    main()
