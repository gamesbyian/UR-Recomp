#!/usr/bin/env python3
"""Retrospective translation-orbit control for authenticated ROM-composed masks.

No original-emulator timing, source motion, or 3D articulation is inferred.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

try:
    from tools.art.audit_original_racer_translation_only_control import binary, source_edges
    from tools.art.evaluate_original_racer_wheel_holdout import originals_from_corpus
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from audit_original_racer_translation_only_control import binary, source_edges
    from evaluate_original_racer_wheel_holdout import originals_from_corpus
    from freeze_racer_source_family_splits import validate_corpus
    from no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-ORIGINAL-ROM-TRANSLATION-ORBIT-RESIDUAL/1"


def translate(mask: bytes, dx: int, dy: int) -> bytes | None:
    """Never clip a visible original pixel, even if clipping improves fit."""
    if not binary(mask) or type(dx) is not int or type(dy) is not int:
        raise ValueError("expected nonempty binary 64x64 source and integer shift")
    result = bytearray(4096)
    for i, v in enumerate(mask):
        if v:
            x, y = i % 64 + dx, i // 64 + dy
            if x < 0 or x >= 64 or y < 0 or y >= 64:
                return None
            result[64*y+x] = 1
    return bytes(result)


def analyze_pair(before: bytes, after: bytes, radius: int = 2) -> dict:
    """Optimize bounded integer displacement against the *next* source raster.

    All equal-optimum shifts are reported. Least motion, y, then x is a
    deterministic tie-break, with no physical-motion interpretation.
    """
    if (not binary(before) or not binary(after) or type(radius) is not int
            or not 0 <= radius <= 8):
        raise ValueError("two nonempty binary 64x64 masks and radius 0..8 required")
    changed = {i for i in range(4096) if before[i] != after[i]}
    candidates = []
    for dy in range(-radius, radius+1):
        for dx in range(-radius, radius+1):
            shifted = translate(before, dx, dy)
            if shifted is not None:
                candidates.append((sum(a != b for a, b in zip(shifted, after)),
                                   dx, dy, shifted))
    if not candidates:
        raise ValueError("even zero translation was unexpectedly invalid")
    optimum = min(c[0] for c in candidates)
    tied = [c for c in candidates if c[0] == optimum]
    chosen = min(tied, key=lambda c: (abs(c[1])+abs(c[2]), c[2], c[1]))
    _, dx, dy, shifted = chosen
    predicted = {i for i in range(4096) if before[i] != shifted[i]}
    common = len(changed & predicted)
    if optimum != len(changed)+len(predicted)-2*common:
        raise ValueError("source/alignment XOR identity violated")
    higher = [c[0] for c in candidates if c[0] != optimum]
    # Source raster crop coordinates, NOT an original anatomical segmentation.
    # Union-normalized mismatch prevents dense silhouette bands receiving
    # more weight merely because they contain more source pixels.
    regions = []
    for y0, y1 in ((0, 16), (16, 32), (32, 40), (40, 64)):
        lo, hi = y0*64, y1*64
        occupancy = sum(bool(a or b) for a, b in
                        zip(shifted[lo:hi], after[lo:hi]))
        mismatch = sum(a != b for a, b in
                       zip(shifted[lo:hi], after[lo:hi]))
        regions.append({
            "raster_y_start_inclusive": y0,
            "raster_y_end_exclusive": y1,
            "source_target_union_pixels": occupancy,
            "aligned_shape_residual_pixels": mismatch,
            "fraction_union_pixels_mismatched":
                round(mismatch/occupancy, 8) if occupancy else None,
        })
    if sum(b["aligned_shape_residual_pixels"] for b in regions) != optimum:
        raise ValueError("regional original-mask XOR does not conserve residual")
    return {
        "original_changed_pixels": len(changed),
        "optimal_integer_shift_dx_dy": [dx, dy],
        "optimal_residual_shape_pixels": optimum,
        "residual_reduction_from_unshifted_pixels": len(changed)-optimum,
        "candidate_nonclipping_shifts": len(candidates),
        "equally_optimal_shift_count": len(tied),
        "next_distinct_residual_margin_pixels": min(higher)-optimum if higher else None,
        "shifted_previous_changed_pixels": len(predicted),
        "original_change_pixels_overlapping_shift": common,
        "posthoc_translation_change_recall":
            round(common/len(changed), 8) if changed else None,
        "posthoc_translation_change_precision":
            round(common/len(predicted), 8) if predicted else None,
        "source_mask_raster_regions": regions,
        "target_silhouette_used_for_search": True,
        "real_original_emulator_frame_timing_observed": False,
        "physical_source_translation_or_3d_articulation_inferred": False,
    }


def evaluate(corpus_path: Path, radius: int = 2) -> dict:
    corpus, verified = validate_corpus(corpus_path)
    groups = originals_from_corpus(corpus_path, corpus)
    if len(groups) != 35 or set(groups) != verified["all_masks"]:
        raise ValueError("wrong original ROM-composed 35-mask corpus")
    # Existing authenticated raster, but temporal *order* is an authored registry.
    edges = source_edges(corpus, groups)
    rows = []
    for edge in edges:
        before = groups[edge["original_binary_mask_sha256_before"]]["mask"]
        after = groups[edge["original_binary_mask_sha256_after"]]["mask"]
        stats = analyze_pair(before, after, radius)
        anchor_shift = edge["pixels"]["source_visible_anchor_delta_x2_y2"]
        stats["best_shift_matches_target_visible_alpha_anchor_delta"] = (
            [2*v for v in stats["optimal_integer_shift_dx_dy"]] == anchor_shift)
        rows.append({
            "window": edge["window"], "player": edge["player"],
            "from_authored_guest_frame": edge["from_guest_frame"],
            "to_authored_guest_frame": edge["to_guest_frame"],
            "original_binary_mask_sha256_before": edge["original_binary_mask_sha256_before"],
            "original_binary_mask_sha256_after": edge["original_binary_mask_sha256_after"],
            "source_visible_anchor_delta_x2_y2": anchor_shift,
            "diagnostic": stats,
        })
    stats = [r["diagnostic"] for r in rows]
    changing = [s for s in stats if s["original_changed_pixels"]]
    # Same binary masks recur in multiple authored windows. Count a directed
    # pair only once before presenting residuals as independent shape cases.
    distinct_pairs = {}
    for row in rows:
        d = row["diagnostic"]
        if not d["original_changed_pixels"]:
            continue
        key = (row["original_binary_mask_sha256_before"],
               row["original_binary_mask_sha256_after"])
        earlier = distinct_pairs.setdefault(key, d)
        if earlier != d:
            raise ValueError("same authenticated directed masks yielded different residuals")
    distinct = list(distinct_pairs.values())
    aggregate_regions = []
    for i, (y0, y1) in enumerate(((0, 16), (16, 32), (32, 40), (40, 64))):
        occupancy = sum(x["source_mask_raster_regions"][i]["source_target_union_pixels"]
                        for x in distinct)
        residual = sum(x["source_mask_raster_regions"][i]["aligned_shape_residual_pixels"]
                       for x in distinct)
        aggregate_regions.append({
            "raster_y_start_inclusive": y0, "raster_y_end_exclusive": y1,
            "source_target_union_pixels": occupancy,
            "aligned_shape_residual_pixels": residual,
            "fraction_union_pixels_mismatched":
                round(residual/occupancy, 8) if occupancy else None,
        })
    if (sum(r["aligned_shape_residual_pixels"] for r in aggregate_regions)
            != sum(d["optimal_residual_shape_pixels"] for d in distinct)):
        raise ValueError("deduplicated regional residual does not conserve XOR")
    if len(rows) != 109 or len(changing) != 19:
        raise ValueError("ROM-composed *authored registry* census changed")
    return {
        "schema": SCHEMA,
        "canonical_original_rom_sha256": corpus["source_rom_sha256"],
        "verified_original_source_corpus_manifest_sha256": verified["corpus_sha256"],
        "registered_sequence_origin": "authored-reference-registry-not-live-PPU",
        "max_abs_integer_shift_pixels": radius,
        "source_original_64x64_mask_bytes_revalidated": True,
        "summary": {
            "authored_registry_consecutive_edges": len(rows),
            "authored_registry_changed_edges": len(changing),
            "authored_registry_unchanged_edges": len(rows)-len(changing),
            "changed_source_pixels": sum(s["original_changed_pixels"] for s in stats),
            "unique_directed_changed_binary_mask_pairs": len(distinct),
            "unique_directed_optimal_residual_pixels":
                sum(d["optimal_residual_shape_pixels"] for d in distinct),
            "unique_directed_regional_shape_residual": aggregate_regions,
            "best_shift_residual_pixels": sum(s["optimal_residual_shape_pixels"] for s in stats),
            "positive_shape_residual_edges":
                sum(s["optimal_residual_shape_pixels"] > 0 for s in changing),
            "shift_oracle_tie_edges": sum(s["equally_optimal_shift_count"] > 1 for s in stats),
            "changed_edges_best_shift_disagrees_with_visible_alpha_anchor":
                sum(not s["best_shift_matches_target_visible_alpha_anchor_delta"]
                    for s in changing),
        },
        "authored_registry_edges": rows,
        "input_next_original_mask_used_in_search": True,
        "no_cross_window_or_player_edge_bridging": True,
        "source_articulation_or_live_cadence_recovered": False,
        "real_1994_3d_model_or_camera_recovered": False,
        "owner_likeness_approved": False, "shipping_art_approved": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--radius", type=int, default=2)
    parser.add_argument("--out", type=Path)
    a = parser.parse_args()
    result = json.dumps(evaluate(a.corpus, a.radius), sort_keys=True, indent=2) + "\n"
    if a.out:
        publish_text_once(a.out, result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
