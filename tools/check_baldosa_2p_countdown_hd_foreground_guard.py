#!/usr/bin/env python3
"""QA-08: fail closed on HD overpaint of actual native PPU-hidden 2P racers.

This is a *candidate presentation regression*, not HD admission. At one
authenticated original two-player countdown frame the pinned native PPU
emitted slots96/97 but removing both made ZERO difference to the final
Original raster. Preserve the Original at all 411 source-alpha-covered
coordinates, for every physical output subpixel at density 1x..4x.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FRAME = 1872
WIDTH, HEIGHT = 342, 224
SOURCE_SLOTS = (96, 97)
STATUS = "recovered-authentic-native-ppu-two-slot-removal-zero-final-difference"


def read_rgba(path: Path, width: int, height: int) -> bytes:
    header = (f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\nMAXVAL 255\n"
              "TUPLTYPE RGB_ALPHA\nENDHDR\n").encode("ascii")
    raw = path.read_bytes()
    if not raw.startswith(header) or len(raw) != len(header) + width * height * 4:
        raise ValueError("P7 RGBA must have exact verified dimensions and header")
    return raw[len(header):]


def verify(stock_path: Path, source96_path: Path, source97_path: Path,
           without_pair_path: Path, candidate_path: Path,
           evidence_path: Path, density: int) -> dict:
    if density not in (1, 2, 3, 4):
        raise ValueError("only 1x..4x nearest-density Original RGBA candidates")
    expected_stock_name = f"ur-baldosa-ws342-{FRAME:06d}.pam"
    if (stock_path.name != expected_stock_name or
            without_pair_path.name != expected_stock_name or
            stock_path.resolve() == without_pair_path.resolve() or
            stock_path.resolve() == candidate_path.resolve() or
            without_pair_path.resolve() == candidate_path.resolve()):
        raise ValueError("independent exact native stock/removal and candidate output required")
    for slot, source in ((96, source96_path), (97, source97_path)):
        if source.name != f"ur-baldosa-ws342-obj-slot{slot}-frame{FRAME:06d}.pam":
            raise ValueError(f"independent authentic native original slot{slot}/frame{FRAME} required")
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if (evidence.get("schema_version") != 1 or
            evidence.get("status") != STATUS or
            evidence.get("native_guest_frame") != FRAME or
            evidence.get("stock_native_source_full_raster") != [WIDTH, HEIGHT] or
            evidence.get("actual_native_pair_removed") != [96, 97] or
            evidence.get("whole_original_rgba_byte_exact_identical") is not True or
            evidence.get("stock_vs_pair_guest_crc_cmp_in_native_workflow_passed") is not True or
            evidence.get("source96_97_native_source_report_status") != "passed" or
            evidence.get("final_original_changed_rgba_pixels_on_pair_deletion") != 0 or
            evidence.get("final_original_changed_outside_emitted_original_source") != 0 or
            evidence.get("expected_full_guest_crc_entries_per_native_route") != 2473 or
            evidence.get("authorized_hd_widescreen_or_4x_art") is not False or
            evidence.get("safe_to_erase_stock_2p_racers_in_host") is not False):
        raise ValueError("source-native causal proof is incomplete or has unsafe admission")
    stock = read_rgba(stock_path, WIDTH, HEIGHT)
    removed = read_rgba(without_pair_path, WIDTH, HEIGHT)
    sources = {
        slot: read_rgba(source, WIDTH, HEIGHT)
        for slot, source in ((96, source96_path), (97, source97_path))
    }
    def sha(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
    if (sha(stock) != evidence.get("stock_full_original_rgba_sha256") or
            sha(removed) != evidence.get("paired_deletion_full_original_rgba_sha256") or
            any(sha(sources[s]) != evidence.get(
                f"source{s}_original_rgba_sha256") for s in SOURCE_SLOTS)):
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
    if (source96 != evidence.get("source96_original_alpha_pixels") or
            source97 != evidence.get("source97_original_alpha_pixels") or
            source96 + source97 != evidence.get(
                "emitted_source_alpha_sum_counting_pair_overlap_twice") or
            count != evidence.get("distinct_original_source_coordinates") or
            blue != count or count != evidence.get(
                "distinct_original_source_coordinates_covered_by_final_blue")):
        raise ValueError("native true source alpha/covered blue counts differ from causal proof")
    return {
        "schema_version": 1,
        "status": ("preserved-causally-hidden-original-countdown-source"
                   if changed == 0 else "failed-countdown-foreground-overpaint"),
        "native_guest_frame": FRAME,
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
        "limits": ("One exact 2P guest1872 native PPU pair-removal witness, not "
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
    a = p.parse_args()
    result = verify(a.stock, a.source96, a.source97, a.without_pair,
                    a.candidate, a.causal_evidence, a.density)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    print("UR_QA08_COUNTDOWN_HD_GUARD " + result["status"] +
          f" frame={FRAME} protected={result['protected_output_subpixels_checked']}" +
          f" overpaint={result['unauthorized_candidate_subpixel_overpaints']}" +
          " remastered_admitted=0")
    return int(result["unauthorized_candidate_subpixel_overpaints"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
