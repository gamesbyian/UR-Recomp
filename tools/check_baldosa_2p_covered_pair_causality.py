#!/usr/bin/env python3
"""QA-08 native Original PPU two-slot countdown-cover causal intervention.

One AUTHENTIC same-frame native process removes lower split OAM slots96+97
while normal Original PPU control, two separately source-isolated planes,
all four complete guest CRC streams and exact native removal log are
verified. A source-positive but final-delta-zero result is a valid
experiment, NOT an error or a license to delete shipping OBJ.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.check_baldosa_wide_slot_final_visibility import read_pam, WIDTH, HEIGHT
    from tools.check_baldosa_wide_single_slot_source import read_source
except ModuleNotFoundError:
    from check_baldosa_wide_slot_final_visibility import read_pam, WIDTH, HEIGHT
    from check_baldosa_wide_single_slot_source import read_source

FRAME = 1872
SLOTS = (96, 97)
GUEST_CRC_FRAMES = 5447
BLUE = bytes((57, 57, 255))


def verify(stock: Path, source96: Path, source97: Path, removed: Path,
           report96: Path, report97: Path, stock_crc: Path,
           source96_crc: Path, source97_crc: Path, removed_crc: Path,
           log_file: Path) -> dict:
    name = f"ur-baldosa-ws342-{FRAME:06d}.pam"
    if (stock.name != name or removed.name != name or
        stock.resolve() == removed.resolve()):
        raise ValueError("authentic independent native stock/removal frame required")
    sources = {96: source96, 97: source97}
    source_reports = {96: report96, 97: report97}
    for slot in SLOTS:
        if sources[slot].name != f"ur-baldosa-ws342-obj-slot{slot}-frame{FRAME:06d}.pam":
            raise ValueError("genuine lower OAM slot/source frame identity required")

    crcs = [p.read_bytes().splitlines() for p in
            (stock_crc, source96_crc, source97_crc, removed_crc)]
    if len(crcs[0]) != GUEST_CRC_FRAMES or any(p != crcs[0] for p in crcs[1:]):
        raise ValueError("all four authentic complete 5447-line guest CRC streams must agree")

    marker = (f"UR_RACER_HD_WIDE_REMOVE_PAIR frame={FRAME} "
              "slots=96-97 status=armed guest_unchanged=1")
    if sum(line.strip() == marker for line in log_file.read_text(
            encoding="utf-8", errors="replace").splitlines()) != 1:
        raise ValueError("native PPU pair removal not exactly once armed on real frame")

    original, final_without_both = read_pam(stock), read_pam(removed)
    original_sha = hashlib.sha256(original).hexdigest()
    source_planes = {}
    for slot in SLOTS:
        plane = read_pam(sources[slot])
        meta = read_source(sources[slot], slot)
        report = json.loads(source_reports[slot].read_text(encoding="utf-8"))
        if (report.get("schema_version") != 1 or
            report.get("status") != "passed" or
            report.get("source_log_matches_pam") is not True or
            report.get("identical_complete_original_342_rasters") != 6 or
            report.get("differing_original_rasters") != [] or
            report.get("shared_full_frame_guest_ids") !=
                [1808, 1824, 1840, 1856, 1872, 1888] or
            report.get("minimum_shared_frames") != 4 or
            report.get("source") != meta or
            report.get("source_frame_main_raster_sha256") != original_sha or
            report.get("guest_crc_comparison") !=
                "Externally enforced byte-exact in native workflow" or
            meta["guest_frame"] != FRAME or
            meta["top_opaque_source_pixels"] != 0 or
            meta["bottom_opaque_source_pixels"] <= 0):
            raise ValueError(f"independent original source slot{slot} proof incomplete")
        source_planes[slot] = (plane, meta)

    union = changed = changed_outside = lower_blue = 0
    source_sum = sum(m["bottom_opaque_source_pixels"]
                     for _, m in source_planes.values())
    changed_examples = []
    for at in range(0, len(original), 4):
        covered = any(source_planes[slot][0][at + 3] for slot in SLOTS)
        if covered:
            union += 1
            if original[at:at + 3] == BLUE:
                lower_blue += 1
        if original[at:at + 4] != final_without_both[at:at + 4]:
            if covered:
                changed += 1
                if len(changed_examples) < 12:
                    index = at // 4
                    changed_examples.append([index % WIDTH, index // WIDTH])
            else:
                changed_outside += 1
    if not union or lower_blue != union:
        raise ValueError("the source-covered blue countdown state was not reproduced")
    if changed_outside:
        raise ValueError("native counterfactual changed original outside the actual two-slot source union")
    return {
        "schema_version": 1,
        "status": ("native-covered-pair-final-unchanged"
                   if changed == 0 else "native-covered-pair-final-changed"),
        "guest_frame": FRAME,
        "source_oam_slots_removed": list(SLOTS),
        "guest_crc_equal_in_all_four_independent_native_processes": GUEST_CRC_FRAMES,
        "exact_native_pair_removal_armed": True,
        "original_final_sha256": original_sha,
        "source96_sha256": source_planes[96][1]["source_sha256"],
        "source97_sha256": source_planes[97][1]["source_sha256"],
        "original_without_pair_sha256": hashlib.sha256(final_without_both).hexdigest(),
        "two_source_emissions_total_counting_overlap_twice": source_sum,
        "source_alpha_union_coordinates": union,
        "source_coordinates_final_countdown_blue": lower_blue,
        "stock_vs_removed_full_final_rgba_changed_pixels": changed,
        "changed_outside_source_alpha_union": changed_outside,
        "bounded_final_changed_xy_examples": changed_examples,
        "pair_removal_has_zero_observable_original_final_effect": changed == 0,
        "specific_foreground_bg_obj_layer_proven": False,
        "source_slot_removal_allowed_in_product": False,
        "authored_hd_or_widescreen_remastered_allowed": False,
        "limits": (
            "Same-frame native PPU removal of lower OAM source slots96-97 "
            "under an independently verified blue countdown-colour region. "
            "A zero-delta final raster proves this pair removal made no "
            "observable Original output change in this frame, NOT what "
            "hardware layer owns those pixels, how other frames behave "
            "or permission to erase Original sprites outside this diagnostic."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    for flag in ("stock", "source96", "source97", "removed", "report96",
                 "report97", "stock-crc", "source96-crc", "source97-crc",
                 "removed-crc", "removed-log", "out"):
        ap.add_argument("--" + flag, type=Path, required=True)
    a = ap.parse_args()
    result = verify(a.stock, a.source96, a.source97, a.removed,
                    a.report96, a.report97, a.stock_crc, a.source96_crc,
                    a.source97_crc, a.removed_crc, a.removed_log)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    print("UR_QA08_2P_COVERED_PAIR_PPU " + result["status"] +
          f" emitted={result['two_source_emissions_total_counting_overlap_twice']}" +
          f" union={result['source_alpha_union_coordinates']}" +
          f" final_changed={result['stock_vs_removed_full_final_rgba_changed_pixels']}" +
          " changed_outside=0 release_hd=0")


if __name__ == "__main__":
    main()
