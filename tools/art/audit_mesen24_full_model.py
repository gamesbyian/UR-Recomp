#!/usr/bin/env python3
"""Score all same-source 2026 model variants without conflating shape and motion.

Requires a real, complete, source-verified Mesen24/GLB experiment report.
This is an observational research review, never an original-1994 3D approval.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from tools.art.score_original_mesen24_full_saddle import (
    SCHEMA, ARMS, TICKS, DRIVE_TRIALS, LEVEL_TRIALS, SLIDE_TRIALS,
    STRETCH_TRIALS, SPAN_TRIALS,
)

METRICS = (
    ("source_frame_pooled_alpha_iou", "chronological_shape"),
    ("source_unique_shape_equal_vote_mean_alpha_iou", "equal_vote_source_shape"),
    ("source_actual_23_consecutive_edge_change_pooled_iou", "chronological_motion"),
)
ROLES = ("blue", "red")
HASH_KEYS = (
    "source_exact_original_USA_ROM_sha256",
    "source_exact_original_Mesen24_archive_sha256",
    "source_exact_ROM_phase_orientation_report_sha256",
    "source_exact_64_angle_report_sha256",
    "source_unchanged_7_6_camera_sha256",
    "current_source_authored_2026_SCAD_sha256",
    "current_successful_2026_16_material_GLB_sha256",
)


def strict_scores(report):
    if not isinstance(report, dict) or report.get("schema") != SCHEMA:
        raise ValueError("wrong source-owned full-model report")
    for key in HASH_KEYS:
        value = report.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(
            c not in "0123456789abcdef" for c in value
        ):
            raise ValueError("invalid exact source or GLB digest: " + key)
    if (report.get("original_1994_3D_mesh_camera_joint_or_source_materials_recovered") is not False
            or report.get("owner_2026_character_art_likeness_approved") is not False
            or report.get("source_each_player_has_all_24_consecutive_original_PPU_images") is not True
            or report.get("source_unique_binary_silhouettes_grouped_without_duplicate_vote_weight") is not True
            or report.get("original_source_fixed_y_band_temporal_edges_partition_exactly") is not True
            or report.get("source_viewpoint_families_are_known_NOT_prospective_blind") is not True
            or report.get("source_original_timeline_ticks") != [1601, 1624]):
        raise ValueError("the authenticated 48-frame source contract is incomplete")
    roles = report.get("original_source_per_role")
    if not isinstance(roles, dict) or set(roles) != set(ROLES):
        raise ValueError("both authenticated source racers required")
    output = {}
    for role in ROLES:
        evidence = roles[role]
        if not isinstance(evidence, dict) or set(evidence.get("original_24_tick_samples", {})) != {
            str(t) for t in TICKS
        }:
            raise ValueError("all 24 original ticks are required per racer")
        items = evidence.get("arms")
        if not isinstance(items, dict) or set(items) != set(ARMS):
            raise ValueError("all frozen control and shape arms must be present")
        output[role] = {}
        for arm in ARMS:
            value = items[arm]
            if (not isinstance(value, dict)
                    or value.get("original_chronological_source_frame_count") != 24
                    or value.get("source_actual_timeline_edge_count") != 23
                    or value.get("original_unique_64px_binary_shape_count") != (
                        19 if role == "blue" else 23
                    )
                    or len(value.get("per_original_chronological_edge", [])) != 23):
                raise ValueError("incomplete exact Mesen24 chronology for " + role + ":" + arm)
            metrics = []
            for key, _ in METRICS:
                number = value.get(key)
                if type(number) not in (int, float) or not math.isfinite(number) or not 0 <= number <= 1:
                    raise ValueError("invalid genuine-source score " + key)
                metrics.append(float(number))
            output[role][arm] = metrics
    return output


def compare(report):
    scores = strict_scores(report)
    # Only compare differently sculpted geometry under an identical wheel
    # drive and identical parent-attitude control. Static nulls are displayed
    # independently and never treated as dynamic-geometry baselines.
    variants = (
        ("saddle_slide", SLIDE_TRIALS),
        ("upper_frame_stretch", STRETCH_TRIALS),
        ("saddle_span", SPAN_TRIALS),
    )
    pairs = []
    for family, trials in variants:
        for arm, mode, magnitude in trials:
            baseline = "axle_root_saddle_world_level_" + (
                "rom_phase_15deg" if mode == "rom_phase" else "fixed_tick_24deg"
            )
            offsets = {}
            for role in ROLES:
                offsets[role] = {
                    label: round(candidate - control, 8)
                    for (key, label), candidate, control in zip(
                        METRICS, scores[role][arm], scores[role][baseline]
                    )
                }
            deltas = [offsets[role][label] for role in ROLES for _, label in METRICS]
            pairs.append({
                "family": family,
                "arm": arm,
                "baseline_same_wheel_drive_and_saddle_attitude": baseline,
                "authoring_parameter": magnitude,
                "both_racers": offsets,
                "strictly_dominates_all_six": all(d >= 0 for d in deltas) and any(d > 0 for d in deltas),
                "shape_better_both": all(offsets[r]["equal_vote_source_shape"] > 0 for r in ROLES),
                "motion_better_both": all(offsets[r]["chronological_motion"] > 0 for r in ROLES),
                "mixed_tradeoff": any(d > 0 for d in deltas) and any(d < 0 for d in deltas),
            })
    return {
        "schema": "UR-ART4K-MESEN24-FULL-MODEL-PARETO-REVIEW/1",
        "source_identity": {key: report[key] for key in HASH_KEYS},
        "original_1994_3d_model_recovered": False,
        "owner_art_approved": False,
        "shipping_art_approved": False,
        "metrics_by_role_and_arm": {
            role: {arm: dict(zip((label for _, label in METRICS), values))
                   for arm, values in scores[role].items()} for role in ROLES
        },
        "same_control_variant_comparisons": pairs,
        "comparison_count": len(pairs),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Complete verified original-source+GLB JSON report")
    parser.add_argument("--out", type=Path, help="Write only to a nonexistent immutable report path")
    args = parser.parse_args()
    result = compare(json.loads(args.report.read_text(encoding="utf-8")))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        if args.out.exists():
            parser.error("cannot overwrite prior reconstruction evidence")
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
