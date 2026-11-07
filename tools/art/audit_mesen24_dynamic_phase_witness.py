#!/usr/bin/env python3
"""Compare two independently qualified original-ROM/real-2026-GLB Mesen24 witnesses.

Retrospective source research, never recovered original 1994 3D physics or
approved 2026 art. Source cameras and ROM are identical, whereas the two
historical actual GLB byte SHA values differ: cross-verify every static
control before interpreting independent phase-driven wheel motion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import zipfile

try:
    from tools.art.audit_mesen24_reconstruction_tradeoffs import (
        HISTORICAL_SOURCE, HISTORICAL_RUN, ARMS, ROLES, METRICS,
    )
    from tools.art.audit_mesen24_edge_coverage import (
        WITNESS_MEMBER, WITNESS_SHA256, WITNESS_GLB_SHA256,
        TICKS, SHAPES, IDENTITIES, analyze_witness, counts, iou,
    )
except ModuleNotFoundError:
    from audit_mesen24_reconstruction_tradeoffs import (
        HISTORICAL_SOURCE, HISTORICAL_RUN, ARMS, ROLES, METRICS,
    )
    from audit_mesen24_edge_coverage import (
        WITNESS_MEMBER, WITNESS_SHA256, WITNESS_GLB_SHA256,
        TICKS, SHAPES, IDENTITIES, analyze_witness, counts, iou,
    )

DYNAMIC_RUN = "https://github.com/gamesbyian/UR-Recomp/actions/runs/42172010215"
DYNAMIC_ARTIFACT_ID = 13483150035
DYNAMIC_WITNESS_SHA256 = "ae90fc1639789633832d63861c9d9c89bda9d71aa2293c2fc392696b504a80c9"
DYNAMIC_GLB_SHA256 = "2cbebdd2c274299d2711d17abb031414a0bf6cddf64b075e64af18ea8327f42f"
ROM = "axle_root_saddle_world_level_rom_phase_15deg"
TICK = "axle_root_saddle_world_level_fixed_tick_24deg"
DYNAMIC_ARMS = (
    ROM, TICK,
    "axle_root_hub_cover_rom_phase_15deg",
    "axle_root_hub_cover_fixed_tick_24deg",
    "axle_root_hub_cover_axle_locked_rom_phase_15deg",
    "axle_root_hub_cover_axle_locked_fixed_tick_24deg",
)
ALL_ARMS = tuple(ARMS) + DYNAMIC_ARMS
SCORES = (
    "source_frame_pooled_alpha_iou",
    "source_unique_shape_equal_vote_mean_alpha_iou",
    "source_actual_23_consecutive_edge_change_pooled_iou",
)
STATIC_FROZEN = SCORES + (
    "per_original_chronological_edge",
    "source_actual_23_consecutive_edge_change_tp_fp_fn",
    "original_chronological_source_frame_count",
    "original_unique_64px_binary_shape_count",
    "source_actual_timeline_edge_count",
)
HUB_MATCHES = (
    ("axle_root_hub_cover_rom_phase_15deg", ROM),
    ("axle_root_hub_cover_fixed_tick_24deg", TICK),
)


def check_scores(item):
    """Independently reconstruct exact eight-decimal temporal IoU from edges."""
    if (not isinstance(item, dict) or
            item.get("original_chronological_source_frame_count") != 24 or
            item.get("source_actual_timeline_edge_count") != 23):
        raise ValueError("incorrect source frame or edge count")
    for key in SCORES:
        v = item.get(key)
        if type(v) not in (float, int) or not math.isfinite(v) or not 0 <= v <= 1:
            raise ValueError("missing or invalid original-real-model measure: " + key)
    edges = item.get("per_original_chronological_edge")
    if not isinstance(edges, list) or len(edges) != 23:
        raise ValueError("original 23 source edges missing")
    totals = [0, 0, 0]
    original_changed_by_edge = []
    predicted = 0
    for idx, record in enumerate(edges):
        if (not isinstance(record, dict) or
                record.get("source_ticks") != [TICKS[idx], TICKS[idx + 1]]):
            raise ValueError("source chronological edge order altered")
        tp, fp, fn = counts({k: record.get(k) for k in ("tp", "fp", "fn")})
        if tp + fp + fn > 4096:
            raise ValueError("source edge exceeds original 64px mask")
        actual_iou = record.get("iou")
        if (type(actual_iou) not in (int, float)
                or not math.isfinite(actual_iou)
                or abs(actual_iou - iou(tp, fp, fn)) > 5e-8):
            raise ValueError("source edge IoU does not match actual pixels")
        original_changed_by_edge.append(tp + fn)
        predicted += int(tp + fp > 0)
        for j, v in enumerate((tp, fp, fn)):
            totals[j] += v
    if (tuple(totals) != counts(item.get(
            "source_actual_23_consecutive_edge_change_tp_fp_fn"))
            or abs(item["source_actual_23_consecutive_edge_change_pooled_iou"]
                   - iou(*totals)) > 5e-8):
        raise ValueError("source aggregate does not match 23 actual source edges")
    return {
        "chronological_shape_iou": item[SCORES[0]],
        "unique_source_shape_equal_vote_iou": item[SCORES[1]],
        "original_edge_change_iou": item[SCORES[2]],
        "original_source_nonempty_change_edges": sum(bool(v) for v in original_changed_by_edge),
        "model_predicted_nonempty_change_edges": predicted,
        "source_changed_alpha_pixel_instances": sum(original_changed_by_edge),
        "model_predicted_changed_alpha_pixel_instances": totals[0] + totals[1],
        "matched_changed_alpha_pixel_instances": totals[0],
        "false_positive_changed_alpha_pixel_instances": totals[1],
        "missed_original_changed_alpha_pixel_instances": totals[2],
        "edge_source_counts": original_changed_by_edge,
    }


def compare_historical_witnesses(original, dynamic):
    """Reject source drift, baseline revisions and per-player best-arm selection."""
    baseline = analyze_witness(original)
    if (not isinstance(dynamic, dict) or
            dynamic.get("schema") !=
                "UR-ART4K-ORIGINAL-24TICK-REAL-2026-SADDLE-LEAN-GENERALIZATION/3"
            or dynamic.get("source_original_timeline_ticks") != [1601, 1624]
            or dynamic.get("source_each_player_has_all_24_consecutive_original_PPU_images") is not True
            or dynamic.get("original_1994_3D_mesh_camera_joint_or_source_materials_recovered") is not False
            or dynamic.get("owner_2026_character_art_likeness_approved") is not False
            or dynamic.get("current_successful_2026_16_material_GLB_sha256") != DYNAMIC_GLB_SHA256):
        raise ValueError("wrong qualified source/2026-GLB dynamic witness")
    for field, pin in IDENTITIES.items():
        if dynamic.get(field) != HISTORICAL_SOURCE[pin]:
            raise ValueError("different original source ROM, provisional camera or 2026 model")
    roles = dynamic.get("original_source_per_role")
    if not isinstance(roles, dict) or set(roles) != set(ROLES):
        raise ValueError("must preserve original two racers")
    selected = {}
    for role in ROLES:
        old = original["original_source_per_role"][role]
        new = roles[role]
        if (not isinstance(new, dict)
                or new.get("original_unique_binary_source_alpha_shape_sha256_to_ticks")
                    != old["original_unique_binary_source_alpha_shape_sha256_to_ticks"]):
            raise ValueError("authentic original source silhouettes changed")
        original_frames = old["original_24_tick_samples"]
        new_frames = new.get("original_24_tick_samples")
        if not isinstance(new_frames, dict) or set(new_frames) != set(map(str, TICKS)):
            raise ValueError("original 24 source ticks missing in dynamic report")
        for tick in TICKS:
            if (not isinstance(new_frames[str(tick)], dict)
                    or new_frames[str(tick)].get("source_2D_alpha_sha256")
                        != original_frames[str(tick)]["source_2D_alpha_sha256"]):
                raise ValueError("source original alpha frame changed: " + str(tick))
        arms = new.get("arms")
        if not isinstance(arms, dict) or set(arms) != set(ALL_ARMS):
            raise ValueError("must retain all exact fixed and matched dynamic controls")
        # The two historical source-owned GLB byte hashes differ; therefore
        # establish pixel-identical original controls instead of inferring
        # asset-byte identity from a shared authored SCAD hash.
        for arm in ARMS:
            for key in STATIC_FROZEN:
                if arms[arm].get(key) != old["arms"][arm].get(key):
                    raise ValueError("original 48-frame baseline changed: " + role + "/" + arm + "/" + key)
        baseline_edges = baseline["roles_and_fixed_control_arms"][role][ARMS[0]]
        observations = {}
        original_change_counts = None
        for arm in ALL_ARMS:
            if arms[arm].get("original_unique_64px_binary_shape_count") != SHAPES[role]:
                raise ValueError("original unique shape count drifted")
            score = check_scores(arms[arm])
            if score["original_source_nonempty_change_edges"] != 23:
                raise ValueError("authentic original source timeline is incomplete")
            if score["source_changed_alpha_pixel_instances"] != baseline_edges["original_changed_alpha_pixels"]:
                raise ValueError("source observed alpha motion differs from historical baseline")
            if original_change_counts is None:
                original_change_counts = score["edge_source_counts"]
            elif original_change_counts != score["edge_source_counts"]:
                raise ValueError("candidate-dependent original source edge counts")
            score.pop("edge_source_counts")
            if arm in DYNAMIC_ARMS and score["model_predicted_nonempty_change_edges"] != 23:
                raise ValueError("source phase-driven model missed an original chronological step")
            observations[arm] = score
        selected[role] = observations

    def both(predicate):
        return all(predicate(selected[role]) for role in ROLES)

    phase_beat = {
        arm: both(lambda x: x[arm]["original_edge_change_iou"] >
            x["original_source_2d_rotation"]["original_edge_change_iou"])
        for arm in (ROM, TICK)
    }
    phase_shape = {
        arm: both(lambda x: x[arm]["unique_source_shape_equal_vote_iou"] >
            x["axle_root_saddle_plus15"]["unique_source_shape_equal_vote_iou"])
        for arm in (ROM, TICK)
    }
    hub_dominates = {
        cover: all(
            selected[role][cover][metric] >= selected[role][control][metric]
            for role in ROLES
            for metric in ("chronological_shape_iou",
                           "unique_source_shape_equal_vote_iou",
                           "original_edge_change_iou")
        )
        for cover, control in HUB_MATCHES
    }
    return {
        "schema": "UR-ART4K-MESEN24-SOURCE-LOCKED-PHASE-DRIVE-COMPARISON/1",
        "historical_static_original_rom_run": HISTORICAL_RUN,
        "qualified_dynamic_original_rom_run": DYNAMIC_RUN,
        "static_witness_sha256": WITNESS_SHA256,
        "dynamic_witness_sha256": DYNAMIC_WITNESS_SHA256,
        "original_source_sha256": HISTORICAL_SOURCE,
        "old_2026_static_glb_sha256": WITNESS_GLB_SHA256,
        "old_2026_dynamic_glb_sha256": DYNAMIC_GLB_SHA256,
        "historical_glb_byte_equality_asserted": False,
        "true_original_24_frames_and_23_edges_each": True,
        "authentic_1994_original_masks_identical_between_runs": True,
        "static_four_arm_baselines_preserved_pixel_exactly": True,
        "fixed_phase_controls_exceed_source_2d_null_edge_iou_both_roles": phase_beat,
        "fixed_phase_controls_keep_saddle_plus15_unique_shape_gain_both_roles": phase_shape,
        "experimental_hub_cover_dominates_matched_no_hub_all_metrics_both_roles":
            hub_dominates,
        "role_metrics": selected,
        "owner_selected_later_outboard_mirrored_model_tested": False,
        "proven_1994_physical_animation": False,
        "owner_likeness_approved": False,
        "shipping_art_approved": False,
    }


def load_exact_witness(archive: Path, expected: str):
    with zipfile.ZipFile(archive) as zipped:
        info = zipped.getinfo(WITNESS_MEMBER)
        if info.file_size > 2_000_000:
            raise ValueError("unbounded historical original-source witness")
        raw = zipped.read(info)
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("historical original-ROM/GLB witness SHA differs")
    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_static_artifact_zip", type=Path)
    parser.add_argument("original_dynamic_artifact_zip", type=Path)
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = compare_historical_witnesses(
        load_exact_witness(args.original_static_artifact_zip, WITNESS_SHA256),
        load_exact_witness(args.original_dynamic_artifact_zip, DYNAMIC_WITNESS_SHA256),
    )
    if args.expected and report != json.loads(args.expected.read_text(encoding="utf-8")):
        parser.error("original source-locked real model comparison changed")
    text = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.out:
        with args.out.open("x", encoding="utf-8") as file:
            file.write(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
