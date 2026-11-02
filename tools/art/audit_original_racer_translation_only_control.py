#!/usr/bin/env python3
"""Original-ROM source translation-only changed-pixel and aligned-shape control.

The original next raster supplies its own visible-bottom-alpha anchor. Therefore
this is a POST-HOC descriptive translation baseline, never predictive motion or
an estimate of the original character's physical movement/3D articulation.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path

try:
    from tools.art.evaluate_original_racer_wheel_holdout import originals_from_corpus
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from evaluate_original_racer_wheel_holdout import originals_from_corpus
    from freeze_racer_source_family_splits import validate_corpus
    from no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-ORIGINAL-SOURCE-TRANSLATION-ONLY-CONTROL/1"


def binary(mask):
    return (isinstance(mask, (bytes, bytearray)) and len(mask) == 4096
            and any(mask) and all(bit in (0, 1) for bit in mask))


def shift_original_mask(source, original_anchor, next_anchor):
    """Exact integer-pixel shift, avoiding invented half-pixel interpolation."""
    if not binary(source):
        raise ValueError("invalid authentic 64x64 original silhouette")
    if any(not isinstance(a, (list, tuple)) or len(a) != 2 or
           any(type(v) is not int for v in a) for a in (original_anchor, next_anchor)):
        raise ValueError("invalid original visible-alpha anchor")
    dx2, dy2 = (next_anchor[0] - original_anchor[0],
                next_anchor[1] - original_anchor[1])
    if dx2 % 2 or dy2 % 2:
        raise ValueError("half-pixel original shift needs explicit resampling study")
    dx, dy = dx2 // 2, dy2 // 2
    shifted = bytearray(4096)
    for index, pixel in enumerate(source):
        if not pixel:
            continue
        x, y = index % 64 + dx, index // 64 + dy
        if not 0 <= x < 64 or not 0 <= y < 64:
            raise ValueError("original source translation would clip visible alpha")
        shifted[64*y+x] = 1
    return bytes(shifted)


def measure(before, after, anchor_before, anchor_after):
    if not binary(before) or not binary(after):
        raise ValueError("original frame requires two nonempty binary silhouettes")
    shifted = shift_original_mask(before, anchor_before, anchor_after)
    source = {i for i in range(4096) if before[i] != after[i]}
    predicted = {i for i in range(4096) if before[i] != shifted[i]}
    overlap = len(source & predicted)
    residual = sum(a != b for a, b in zip(shifted, after))
    if residual != len(source) + len(predicted) - 2*overlap:
        raise ValueError("original-image translation XOR identity failed")
    return {
        "source_changed_pixels": len(source),
        "translated_original_changed_pixels": len(predicted),
        "matched_changed_pixels": overlap,
        "actual_next_minus_shifted_previous_shape_pixels": residual,
        "source_raster_changed": bool(source),
        "source_visible_bottom_alpha_anchor_changed":
            anchor_before != anchor_after,
        "source_visible_anchor_delta_x2_y2":
            [anchor_after[0]-anchor_before[0], anchor_after[1]-anchor_before[1]],
        "change_pixel_recall": round(overlap/len(source), 8) if source else None,
        "change_pixel_precision": (round(overlap/len(predicted), 8)
                                   if predicted else None),
        "original_next_raster_used_to_measure_translation": True,
        "physical_ground_contact_or_3d_motion_inferred": False,
    }


def source_edges(corpus, groups):
    paths, seen = {}, set()
    for observation in corpus["source_temporal_frame_observations"]:
        window, number = observation["window"], observation["guest_frame"]
        if type(window) is not str or type(number) is not int:
            raise ValueError("invalid authentic source frame identity")
        for player, representation in observation["representations"].items():
            if player not in ("p1", "p2"):
                raise ValueError("unexpected player")
            row = corpus["source_representations"].get(representation)
            if not isinstance(row, dict) or row.get("player") != player:
                raise ValueError("source representation/player mismatch")
            sha = row["source_binary_mask_sha256"]
            if sha not in groups or (window, player, number) in seen:
                raise ValueError("wrong or repeated verified original frame")
            seen.add((window, player, number))
            paths.setdefault((window, player), []).append((number, sha))
    if len(paths) != 35 or len(seen) != 144:
        raise ValueError("wrong player-track or source observation census")
    result = []
    for (window, player), rows in sorted(paths.items()):
        rows.sort()
        for (a, sha_a), (b, sha_b) in zip(rows, rows[1:]):
            if b <= a:
                raise ValueError("nonmonotonic original guest frame")
            if b != a + 1:
                continue  # no invented source time across missing frames
            source_a, source_b = groups[sha_a], groups[sha_b]
            movement = measure(
                source_a["mask"], source_b["mask"],
                source_a["source_alpha_anchor_x2_y2"],
                source_b["source_alpha_anchor_x2_y2"],
            )
            result.append({
                "window": window, "player": player,
                "from_guest_frame": a, "to_guest_frame": b,
                "original_binary_mask_sha256_before": sha_a,
                "original_binary_mask_sha256_after": sha_b,
                "pixels": movement,
            })
    if len(result) != 109:
        raise ValueError("genuine consecutive source edge count changed")
    return result


def summarize(rows):
    if len(rows) != 109:
        raise ValueError("actual original P1/P2 census not established")
    x = [r["pixels"] for r in rows]
    source = sum(r["source_changed_pixels"] for r in x)
    predicted = sum(r["translated_original_changed_pixels"] for r in x)
    matched = sum(r["matched_changed_pixels"] for r in x)
    residual = sum(r["actual_next_minus_shifted_previous_shape_pixels"] for r in x)
    moving = [r for r in x if r["source_raster_changed"]]
    held = len(x)-len(moving)
    deltas = Counter(tuple(r["source_visible_anchor_delta_x2_y2"]) for r in moving)
    if (source != 1631 or len(moving) != 19 or held != 90
            or predicted != 1776 or matched != 1057 or residual != 1293
            or deltas != Counter({(2, 0): 10, (-2, 0): 7, (0, 0): 2})
            or any(r["translated_original_changed_pixels"] for r in x
                   if not r["source_raster_changed"])):
        raise ValueError("source-verified original translation controls diverged")
    return {
        "genuine_source_frame_edges": len(rows),
        "source_changed_silhouette_edges": len(moving),
        "source_held_edges": held,
        "source_anchor_right_one_logical_pixel_edges": deltas[(2, 0)],
        "source_anchor_left_one_logical_pixel_edges": deltas[(-2, 0)],
        "source_shape_change_with_fixed_anchor_edges": deltas[(0, 0)],
        "original_changed_pixel_positions": source,
        "predicted_source_translation_changed_pixel_positions": predicted,
        "matching_original_changed_pixel_positions": matched,
        "source_translation_changed_pixel_recall": round(matched / source, 8),
        "source_translation_changed_pixel_precision": round(matched / predicted, 8),
        "next_original_shape_residual_after_shift_pixels": residual,
        "source_anchor_used_for_translation_from_target_frame": True,
        "translation_only_is_posthoc_not_predictive": True,
    }


def evaluate(corpus_path: Path):
    corpus, verified = validate_corpus(corpus_path)
    groups = originals_from_corpus(corpus_path, corpus)
    if len(groups) != 35 or set(groups) != verified["all_masks"]:
        raise ValueError("original source silhouette corpus no longer 35 masks")
    edges = source_edges(corpus, groups)
    return {
        "schema": SCHEMA,
        "canonical_original_rom_sha256": corpus["source_rom_sha256"],
        "source_original_corpus_manifest_sha256": verified["corpus_sha256"],
        "authentic_original_64x64_pngs_independently_revalidated": True,
        "registered_camera_or_3d_motion_recovered": False,
        "original_next_frame_lookahead_used": True,
        "artistic_likeness_approved": False,
        "shipping_art_approved": False,
        "summary": summarize(edges),
        "source_edges": edges,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    output = json.dumps(evaluate(args.corpus), indent=2, sort_keys=True) + "\n"
    if args.out:
        publish_text_once(args.out, output)
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
