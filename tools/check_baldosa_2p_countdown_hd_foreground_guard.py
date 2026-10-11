#!/usr/bin/env python3
"""QA-08: fail closed on HD overpaint of actual native PPU-hidden 2P racers.

This is a *candidate presentation regression*, not HD admission. At two
authenticated original 2P countdown frames 1872 and 1888 the pinned PPU
emitted slots96/97 but their combined removal made ZERO final Original
raster difference. Preserve every source-alpha-covered pixel in the
respective frame, at every 1x..4x output subpixel.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FRAME = 1872
WIDTH, HEIGHT = 342, 224
SOURCE_SLOTS = (96, 97)
STATUS = "native-covered-pair-final-unchanged"


def read_rgba(path: Path, width: int, height: int) -> bytes:
    header = (f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\nMAXVAL 255\n"
              "TUPLTYPE RGB_ALPHA\nENDHDR\n").encode("ascii")
    raw = path.read_bytes()
    if not raw.startswith(header) or len(raw) != len(header) + width * height * 4:
        raise ValueError("P7 RGBA must have exact verified dimensions and header")
    return raw[len(header):]


def verify(stock_path: Path, source96_path: Path, source97_path: Path,
           without_pair_path: Path, candidate_path: Path,
           evidence_path: Path, density: int, frame: int = FRAME) -> dict:
    if frame not in (1872, 1888):
        raise ValueError("only independently native-proven countdown guest frames1872/1888")
    if density not in (1, 2, 3, 4):
        raise ValueError("only 1x..4x nearest-density Original RGBA candidates")
    expected_stock_name = f"ur-baldosa-ws342-{frame:06d}.pam"
    if (stock_path.name != expected_stock_name or
            without_pair_path.name != expected_stock_name or
            stock_path.resolve() == without_pair_path.resolve() or
            stock_path.resolve() == candidate_path.resolve() or
            without_pair_path.resolve() == candidate_path.resolve()):
        raise ValueError("independent exact native stock/removal and candidate output required")
    for slot, source in ((96, source96_path), (97, source97_path)):
        if source.name != f"ur-baldosa-ws342-obj-slot{slot}-frame{frame:06d}.pam":
            raise ValueError(f"independent authentic native original slot{slot}/frame{frame} required")
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if (evidence.get("schema_version") != 1 or
            evidence.get("status") != STATUS or
            evidence.get("guest_frame") != frame or
            evidence.get("source_oam_slots_removed") != [96, 97] or
            evidence.get("exact_native_pair_removal_armed") is not True or
            evidence.get("guest_crc_equal_in_all_four_independent_native_processes") != 2473 or
            evidence.get("pair_removal_has_zero_observable_original_final_effect") is not True or
            evidence.get("stock_vs_removed_full_final_rgba_changed_pixels") != 0 or
            evidence.get("changed_outside_source_alpha_union") != 0 or
            evidence.get("source_slot_removal_allowed_in_product") is not False or
            evidence.get("authored_hd_or_widescreen_remastered_allowed") is not False or
            evidence.get("specific_foreground_bg_obj_layer_proven") is not False):
        raise ValueError("source-native causal proof is incomplete or has unsafe admission")
    stock = read_rgba(stock_path, WIDTH, HEIGHT)
    removed = read_rgba(without_pair_path, WIDTH, HEIGHT)
    sources = {
        slot: read_rgba(source, WIDTH, HEIGHT)
        for slot, source in ((96, source96_path), (97, source97_path))
    }
    def sha(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
    if (sha(stock) != evidence.get("original_final_sha256") or
            sha(removed) != evidence.get("original_without_pair_sha256") or
            any(sha(sources[s]) != evidence.get(
                f"source{s}_sha256") for s in SOURCE_SLOTS)):
        raise ValueError("one or more native Original/source/counterfactual SHA mismatches")
    if stock != removed:
        raise ValueError("native Original changed when covered racer source pair was removed")
    candidate = read_rgba(candidate_path, WIDTH * density, HEIGHT * density)
    count = source96 = source97 = blue = changed = 0
    errors = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            at = 4 * (y * WIDTH + x)
            a = bool(sources[96][at + 3])
            b = bool(sources[97][at + 3])
            source96 += int(a)
            source97 += int(b)
            if not (a or b):
                continue
            count += 1
            blue += stock[at:at + 3] == bytes((57, 57, 255))
            expected = stock[at:at + 4]
            for dy in range(density):
                for dx in range(density):
                    dst = 4 * ((y * density + dy) * (WIDTH * density) +
                               x * density + dx)
                    if candidate[dst:dst + 4] != expected:
                        changed += 1
                        if len(errors) < 12:
                            errors.append([x, y, dx, dy])
    if (source96 == 0 or source97 == 0 or
            source96 + source97 != evidence.get(
                "two_source_emissions_total_counting_overlap_twice") or
            count != evidence.get("source_alpha_union_coordinates") or
            blue != count or count != evidence.get(
                "source_coordinates_final_countdown_blue")):
        raise ValueError("native true source alpha/covered blue counts differ from causal proof")
    return {
        "schema_version": 1,
        "status": ("preserved-causally-hidden-original-countdown-source"
                   if changed == 0 else "failed-countdown-foreground-overpaint"),
        "native_guest_frame": frame,
        "native_causal_source_pair": [96, 97],
        "native_original_exact_sha256": sha(stock),
        "candidate_full_rgba_sha256": sha(candidate),
        "candidate_density": density,
        "protected_logical_original_coordinates": count,
        "protected_output_subpixels_checked": count * density * density,
        "unauthorized_candidate_subpixel_overpaints": changed,
        "bounded_overpaint_xy_subpixel_examples": errors,
        "source_original_low_pair_remains_required": True,
        "candidate_original_foreground_preserved": changed == 0,
        "candidate_process_or_full_guest_event_authenticated_by_this_check": False,
        "general_2p_remastered_and_art_likeness_approved": False,
        "limits": ("One explicitly selected, independently authenticated 2P "
                   "guest1872/1888 native PPU pair-removal witness, not "
                   "a general priority mask. Pass means no source-covered "
                   "countdown pixel was overpainted, NOT graphics product "
                   "readiness, guest-process identity, or 4K authorization."),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("stock", "source96", "source97", "without-pair",
                 "candidate", "causal-evidence", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--density", type=int, required=True, choices=(1, 2, 3, 4))
    p.add_argument("--frame", type=int, choices=(1872, 1888), default=FRAME)
    a = p.parse_args()
    result = verify(a.stock, a.source96, a.source97, a.without_pair,
                    a.candidate, a.causal_evidence, a.density, frame=a.frame)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    print("UR_QA08_COUNTDOWN_HD_GUARD " + result["status"] +
          f" frame={a.frame} protected={result['protected_output_subpixels_checked']}" +
          f" overpaint={result['unauthorized_candidate_subpixel_overpaints']}" +
          " remastered_admitted=0")
    return int(result["unauthorized_candidate_subpixel_overpaints"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
