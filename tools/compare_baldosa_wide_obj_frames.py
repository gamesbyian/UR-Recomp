#!/usr/bin/env python3
"""Compare independently captured wide PPU OBJ reports across moving frames.

Frame 1856's overlap witness is a single-frame observation, not a universal
racer visibility rule. Compare source emission, slot overlap, and Original
raster RGB disagreements independently across frames. No drawing admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SLOTS = ("96", "97", "98", "99")
PAIRS = ("96-97", "96-98", "96-99", "97-98", "97-99", "98-99")
PIXELS = 342 * 224


def _validate(report: dict) -> None:
    if report.get("schema_version") != 1:
        raise ValueError("unsupported per-frame source evidence schema")
    if report.get("status") not in ("passed", "unproven"):
        raise ValueError("missing or unsupported source evidence status")
    if set(report.get("per_slot", {})) != set(SLOTS):
        raise ValueError("expected exactly four independent OAM slots")
    if set(report.get("source_obj_sha256", {})) != set(SLOTS):
        raise ValueError("missing per-slot source digests")
    if set(report.get("source_overlap_pairs", {})) != set(PAIRS):
        raise ValueError("incomplete source overlap pair census")
    for digest in [report.get("stock_ppu_sha256"),
                   *report["source_obj_sha256"].values()]:
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("invalid source/main raster digest")
        try:
            bytes.fromhex(digest)
        except ValueError as exc:
            raise ValueError("nonhex source/main raster digest") from exc

    observed_total = 0
    for slot in SLOTS:
        row = report["per_slot"][slot]
        needed = ("source_opaque", "source_opaque_top", "source_opaque_bottom",
                  "unique_source_pixels", "overlap_source_pixels",
                  "main_rgb_matches_source", "main_rgb_differs_source",
                  "unique_main_rgb_differs", "overlap_main_rgb_differs")
        if not all(isinstance(row.get(key), int) and
                   not isinstance(row[key], bool) and row[key] >= 0
                   for key in needed):
            raise ValueError(f"incomplete/nonnegative per-slot census {slot}")
        total = row["source_opaque"]
        if (total > PIXELS or
            total != row["source_opaque_top"] + row["source_opaque_bottom"] or
            total != row["unique_source_pixels"] + row["overlap_source_pixels"] or
            total != row["main_rgb_matches_source"] + row["main_rgb_differs_source"] or
            row["main_rgb_differs_source"] !=
              row["unique_main_rgb_differs"] + row["overlap_main_rgb_differs"]):
            raise ValueError(f"inconsistent per-slot PPU census {slot}")
        observed_total += total

    if observed_total != report.get("source_alpha_total_across_slots"):
        raise ValueError("source-alpha sum does not match four slot reports")
    union = report.get("source_alpha_union_pixels")
    multiple = report.get("source_alpha_multi_slot_pixels")
    if (not isinstance(union, int) or not isinstance(multiple, int) or
        union < 0 or multiple < 0 or multiple > union or union > PIXELS or
        observed_total < union):
        raise ValueError("invalid union/multi-slot PPU census")
    for pair in PAIRS:
        count = report["source_overlap_pairs"][pair]
        if not isinstance(count, int) or count < 0 or count > multiple:
            raise ValueError(f"invalid source pair overlap {pair}")


def compare(before: dict, after: dict) -> dict:
    _validate(before)
    _validate(after)
    f0, f1 = before.get("guest_frame"), after.get("guest_frame")
    if (not isinstance(f0, int) or not isinstance(f1, int)
        or isinstance(f0, bool) or isinstance(f1, bool) or f0 < 0 or f1 <= f0):
        raise ValueError("source frames must be two ordered distinct guest frames")
    if before["stock_ppu_sha256"] == after["stock_ppu_sha256"]:
        raise ValueError("source frames have identical Original main raster")
    slot_deltas = {}
    for slot in SLOTS:
        a, b = before["per_slot"][slot], after["per_slot"][slot]
        keys = ("source_opaque", "source_opaque_top", "source_opaque_bottom",
                "overlap_source_pixels", "unique_main_rgb_differs",
                "overlap_main_rgb_differs")
        slot_deltas[slot] = {
            "before_source": a["source_opaque"],
            "after_source": b["source_opaque"],
            "source_delta": b["source_opaque"] - a["source_opaque"],
            "source_absent_before": a["source_opaque"] == 0,
            "source_absent_after": b["source_opaque"] == 0,
            "source_digest_changed":
                before["source_obj_sha256"][slot] != after["source_obj_sha256"][slot],
            "deltas": {k: b[k] - a[k] for k in keys},
            "nonmatching_original_rgb_before": a["main_rgb_differs_source"],
            "nonmatching_original_rgb_after": b["main_rgb_differs_source"],
        }
    overlap = {
        pair: {
            "before": before["source_overlap_pairs"][pair],
            "after": after["source_overlap_pairs"][pair],
            "delta": after["source_overlap_pairs"][pair] -
                     before["source_overlap_pairs"][pair],
        }
        for pair in PAIRS
    }
    return {
        "schema_version": 1,
        "status": "observed-not-admitted",
        "frames": [f0, f1],
        "guest_frame_delta": f1 - f0,
        "stock_frame_digests_differ": True,
        "slot_source_deltas": slot_deltas,
        "source_pair_overlap_deltas": overlap,
        "source_union_delta":
            after["source_alpha_union_pixels"] -
            before["source_alpha_union_pixels"],
        "source_multi_slot_delta":
            after["source_alpha_multi_slot_pixels"] -
            before["source_alpha_multi_slot_pixels"],
        "unresolved_per_slot_bg_window_or_priority_candidates": {
            slot: [before["per_slot"][slot]["unique_main_rgb_differs"],
                   after["per_slot"][slot]["unique_main_rgb_differs"]]
            for slot in SLOTS
        },
        "safe_to_destructively_replace_original_obj": False,
        "limits": (
            "Source-alpha and color-comparison changes across two distinct "
            "guest frames do not establish stable per-player visibility, "
            "raster owner, BG/window depth, final compositing priority or "
            "safe 342-wide HD replacement. Counts are not spatially registered "
            "across moving frames; independently validated per-frame input "
            "provenance is mandatory."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", type=Path, required=True)
    ap.add_argument("--after", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    reports = [json.loads(p.read_text(encoding="utf-8"))
               for p in (args.before, args.after)]
    result = compare(*reports)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    top = result["source_pair_overlap_deltas"]["98-99"]
    bottom = result["source_pair_overlap_deltas"]["96-97"]
    print(
        "UR_BALDOSA_WIDE_TEMPORAL_SOURCE OBSERVED "
        f"frames={result['frames'][0]}:{result['frames'][1]} "
        f"top_overlap={top['before']}->{top['after']} "
        f"bottom_overlap={bottom['before']}->{bottom['after']} "
        "safe_hd_admission=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
