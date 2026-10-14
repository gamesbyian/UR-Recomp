#!/usr/bin/env python3
"""Strict 26-pixel real native BG3/OBJ PPU source and causal RGB witness.

The source records must agree with existing independently accepted full Original
PPU pixels, both isolated front-source causal reports and full guest CRC
counts. No synthetic observer, physical-console pass or new HD art is inferred.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

try:
    from tools import check_qa08_native_main_sub_pixel_probe as qa
except ModuleNotFoundError:
    import check_qa08_native_main_sub_pixel_probe as qa

PATTERN = re.compile(
    qa.PATTERN.pattern.replace(
        "UR_QA08_NATIVE_PPU_PIXEL", "UR_QA08_NATIVE_PPU_TEXT26"
    )
)
KIND_SLOTS = {"stock": None, "removed98": 98, "removed96": 96}


def rgb5_from_rgb8(rgb: list[int]) -> list[int]:
    if len(rgb) != 3:
        raise ValueError("source RGB triplet expected")
    values = []
    for value in rgb:
        if type(value) is not int:
            raise ValueError("not native expanded 5-bit RGB")
        matches = [b for b in range(32) if (b << 3) | (b >> 2) == value]
        if len(matches) != 1:
            raise ValueError("source pixel does not use 5-bit SNES expansion")
        values.append(matches[0])
    return values


def rgb5_from_rgb15(value: int) -> list[int]:
    return [(value >> shift) & 31 for shift in (0, 5, 10)]


def expected_points(causal: dict) -> dict[tuple[int, int], dict]:
    if (causal.get("guest_frame") != 2208 or
            causal.get("native_each_front_removed_in_independent_full_guest_process")
            is not True):
        raise ValueError("authentic source-removal acceptance missing")
    out = {}
    paired = {}
    for slot, lower in ((98, False), (96, True)):
        evidence = causal["per_original_front_slot"][str(slot)]
        if (evidence["all_four_guest_crc_streams_equal_at_exact_frame_count"] != 2473 or
                evidence["authentic_native_arm_marker_one"] is not True):
            raise ValueError("source front removal guest/arm witness invalid")
        samples = evidence["bounded_original_red_text_over_front_samples"]
        if len(samples) != 13:
            raise ValueError("not all 13 independent front/text pixels selected")
        for sample in samples:
            x, y = sample["xy"]
            if ((x, y) in out or x not in (132, 133, 135, 136) or
                    not (159 <= y <= 164 if lower else 47 <= y <= 52)):
                raise ValueError("bad/duplicate native 26 pixel registration")
            if sample["native_final_changed"] is not True:
                raise ValueError("non-causal normal/racer overlap position")
            out[(x, y)] = {"source_front": slot, "normal": sample["stock_original_rgb"],
                            "source": sample["source_rgb"],
                            "removed": sample["native_original_after_front_removal_rgb"]}
            paired[(x, y - 112 if lower else y)] = paired.get(
                (x, y - 112 if lower else y), []
            ) + [(slot, sample["stock_original_rgb"], sample["source_rgb"])]
    if len(out) != 26 or len(paired) != 13:
        raise ValueError("missing exact source-positive paired text witnesses")
    if any(sorted(t[0] for t in rows) != [96, 98] or
           rows[0][1:] != rows[1][1:] for rows in paired.values()):
        raise ValueError("upper/lower source/stock pairing differs")
    return out


def read_records(path: Path, rgba: bytes, points: dict, kind: str) -> dict:
    lines = [line for line in path.read_text(encoding="utf8", errors="replace").splitlines()
             if "UR_QA08_NATIVE_PPU_TEXT26" in line]
    if len(lines) != 26:
        raise ValueError("not all 26 genuinely recorded native PPU pixel records")
    out = {}
    for line in lines:
        match = PATTERN.fullmatch(line)
        if not match:
            raise ValueError("malformed original PPU source-text record")
        frame, x, y = map(int, match.group(1, 2, 3))
        coord = (x, y)
        if frame != 2208 or coord not in points or coord in out:
            raise ValueError("wrong frame, out-of-mask or duplicated PPU sample")
        main, sub, main15, sub15, final, cgadsub, cgwsel, fixed15 = [
            int(v, 16) for v in match.group(4, 5, 6, 7, 8, 9, 10, 11)
        ]
        math, rendered, present, clip = map(int, match.group(12, 13, 14, 15))
        is_lower = y >= 112
        source = points[coord]
        removed_here = KIND_SLOTS[kind] == source["source_front"]
        should_equal_stock = not removed_here
        target = source["normal"] if should_equal_stock else source["removed"]
        actual_rgba = rgba[4 * (342 * y + x):4 * (342 * y + x) + 4]
        if (len(actual_rgba) != 4 or list(actual_rgba[:3]) != target or
                final != (target[0] << 16 | target[1] << 8 | target[2])):
            raise ValueError("real Original stock/deletion frame RGB witness changed")
        if (not (0 <= main15 <= 0x7fff and 0 <= sub15 <= 0x7fff) or
                cgadsub != 0x04 or cgwsel != 0x02 or
                math != 1 or rendered != 1 or clip != 1 or
                (main >> 8) & 15 != 2 or main15 != 0x000D or
                fixed15 != (0x0260 if is_lower else 0x000F) or
                present != int((sub & 255) != 0)):
            raise ValueError("recorded native BG3/window/HDMA field state disagrees")
        actual_sub = rgb5_from_rgb15(sub15)
        source_rgb5 = rgb5_from_rgb8(source["source"])
        if should_equal_stock:
            if (not present or ((sub >> 8) & 15) not in (4, 6) or
                    actual_sub != source_rgb5):
                raise ValueError("actual native OBJ subscreen does not own rider pixel")
        else:
            if present or sub15 != 0:
                raise ValueError("removed native front OBJ still occupies subscreen")
        fixed_operand = fixed15 if not present else sub15
        result_rgb5 = [
            min(31, a + b) for a, b in zip(
                rgb5_from_rgb15(main15), rgb5_from_rgb15(fixed_operand)
            )
        ]
        expected_rgb5 = rgb5_from_rgb8(target)
        if result_rgb5 != expected_rgb5:
            raise ValueError("original native PPU colour-math source equation disagrees")
        out[coord] = {
            "main_zbuf": f"0x{main:04X}", "main_RGB15": f"0x{main15:04X}",
            "sub_zbuf": f"0x{sub:04X}", "sub_RGB15": f"0x{sub15:04X}",
            "live_fixed_RGB15": f"0x{fixed15:04X}",
            "subscreen_is_OBJ": should_equal_stock,
            "subscreen_present": bool(present),
            "original_RGB5": expected_rgb5,
            "stock_or_removed": "stock" if should_equal_stock else "front-removed",
        }
    if set(out) != set(points):
        raise ValueError("missing original-native source point")
    return out


def check(stock: Path, stock_log: Path, removed98: Path, removed98_log: Path,
          removed96: Path, removed96_log: Path, causal: Path, journal: Path) -> dict:
    ev = json.loads(causal.read_text(encoding="utf8"))
    j = json.loads(journal.read_text(encoding="utf8"))
    if (j.get("guest_frame") != 2208 or
            j.get("full_original_342x224_RGBA_SHA256") != qa.STOCK_SHA or
            j.get("full_native_guest_CRC_entries_equal") != 2473):
        raise ValueError("genuine full native guest/frame acceptance missing")
    # Baseline is the CPU journal, not live render-time fixed15.
    for name in ("completed", "recording"):
        state = j["field_register_journals"][name]["beam_order_colour_knowledge"]
        if state["visible_line_tag_intervals_after_same_line_final_write"] != [{
            "first_visible_line_tag": 0, "last_visible_line_tag": 223,
            "cgadsub": "0x04", "cgwsel": "0x02",
            "fixed_R5_G5_B5": [0, 19, 0], "fixed_rgb15": "0x0260",
        }]:
            raise ValueError("native CPU journal colour field evidence invalid")
    points = expected_points(ev)
    stock_rgba = qa.load_pam(stock, qa.STOCK_SHA)
    upper = ev["per_original_front_slot"]["98"]
    lower = ev["per_original_front_slot"]["96"]
    r98 = qa.load_pam(removed98, upper["native_front_removed_original_sha256"])
    r96 = qa.load_pam(removed96, lower["native_front_removed_original_sha256"])
    reports = {
        "stock": read_records(stock_log, stock_rgba, points, "stock"),
        "removed98": read_records(removed98_log, r98, points, "removed98"),
        "removed96": read_records(removed96_log, r96, points, "removed96"),
    }
    mask = {str(k):[x,y] for k, (x,y) in enumerate(sorted(points))}
    return {
        "schema": "qa08-original-2p-26-pixel-ppu-main-sub-causal/1",
        "status": "strict-source-observed-native-26-pixel-BG3-OBJ-foreground",
        "guest_frame": 2208,
        "guest_CRC_entries_equal": 2473,
        "original_full_RGBA_sha256": qa.STOCK_SHA,
        "original_source_front_pixels_per_viewport": 13,
        "native_compositor_pixel_records": 78,
        "stock_native_BG3_main_OBJ_subscreen": 26,
        "front_removed_native_empty_subscreen": 26,
        "opposite_front_removed_original_OBJ_intact": 26,
        "upper_live_fixed_RGB15": "0x000F",
        "lower_live_fixed_RGB15": "0x0260",
        "source_coordinates": mask,
        "physical_SNES_hardware_acceptance": False,
        "HD_art_character_approved": False,
        "samples": {
            name:{f"{x},{y}": item for (x,y), item in sorted(rows.items())}
            for name, rows in reports.items()
        },
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("stock", "stock-log", "removed98", "removed98-log", "removed96",
                "removed96-log", "causal", "journal", "out"):
        p.add_argument("--"+key, type=Path, required=True)
    a=p.parse_args()
    result=check(a.stock,a.stock_log,a.removed98,a.removed98_log,
                 a.removed96,a.removed96_log,a.causal,a.journal)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("UR_QA08_NATIVE_TEXT26_ACCEPTED guest=2208 native=78 "
          "mainBG3=78 stockOBJ=26 removals_empty=26 oppositeOBJ=26 "
          "guestCRC=2473 HD_admitted=0 hardware=0")


if __name__=="__main__":
    main()
