#!/usr/bin/env python3
"""Recheck original 1994 PPU phase-change coverage against an exact old real-GLB witness.

The historical no-frame-skip two-player original-Mesen24 source ran in
https://github.com/gamesbyian/UR-Recomp/actions/runs/41892738666
and is retained as Actions artifact 13354178658. This read-only audit uses
its real original-source/per-edge signed TP/FP/FN counts, never synthetic
original sprites, and does not export a new 2026 rig or claim 1994 geometry.
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
        ARMS, HISTORICAL_SOURCE, HISTORICAL_RUN, ROLES,
    )
except ModuleNotFoundError:
    from audit_mesen24_reconstruction_tradeoffs import (
        ARMS, HISTORICAL_SOURCE, HISTORICAL_RUN, ROLES,
    )

WITNESS_MEMBER = "real-model-evidence/original-all24-saddle-only-generalization.json"
WITNESS_SHA256 = "fbc5534aacaac13d3ab9eae3463853abe0009bf9c7ab56a87bf8968d4039e137"
WITNESS_GLB_SHA256 = "c8c4930825bb2d55bbbe0988862d826a3a46199f51e7741fd6e16b8e594cd65a"
TICKS = tuple(range(1601, 1625))
SHAPES = {"blue": 19, "red": 23}
IDENTITIES = {
    "source_exact_original_USA_ROM_sha256": "original_source_USA_ROM_sha256",
    "source_exact_original_Mesen24_archive_sha256": "original_Mesen24_archive_sha256",
    "source_exact_ROM_phase_orientation_report_sha256": "original_pose_report_sha256",
    "source_exact_64_angle_report_sha256": "original_axis_sha256",
    "source_unchanged_7_6_camera_sha256": "provisional_camera_sha256",
    "current_source_authored_2026_SCAD_sha256": "current_2026_authored_SCAD_sha256",
}


def counts(record):
    if (not isinstance(record, dict) or set(record) != {"tp", "fp", "fn"}
            or any(type(record[k]) is not int or not 0 <= record[k] <= 4096
                   for k in ("tp", "fp", "fn"))):
        raise ValueError("unbounded or malformed TP/FP/FN evidence")
    return (record["tp"], record["fp"], record["fn"])


def iou(tp, fp, fn):
    return round(tp / (tp + fp + fn), 8) if tp + fp + fn else 1.0


def analyze_witness(witness):
    """Prove source and predicted edge counts from exact original per-tick data."""
    if (not isinstance(witness, dict) or
            witness.get("schema") != "UR-ART4K-ORIGINAL-24TICK-REAL-2026-SADDLE-LEAN-GENERALIZATION/1"
            or witness.get("source_original_timeline_ticks") != [1601, 1624]
            or witness.get("source_each_player_has_all_24_consecutive_original_PPU_images") is not True
            or witness.get("original_1994_3D_mesh_camera_joint_or_source_materials_recovered") is not False
            or witness.get("owner_2026_character_art_likeness_approved") is not False
            or witness.get("current_successful_2026_16_material_GLB_sha256") != WITNESS_GLB_SHA256):
        raise ValueError("incorrect or unapproved original sprite/2026 real-GLB witness")
    for field, source in IDENTITIES.items():
        if witness.get(field) != HISTORICAL_SOURCE[source]:
            raise ValueError("historical source identity or provisional camera drift: " + field)
    original = witness.get("original_source_per_role")
    if not isinstance(original, dict) or set(original) != set(ROLES):
        raise ValueError("must include exactly blue and red original racers")
    result = {}
    for role in ROLES:
        record = original[role]
        if not isinstance(record, dict):
            raise ValueError("missing source original role")
        frames = record.get("original_24_tick_samples")
        groups = record.get("original_unique_binary_source_alpha_shape_sha256_to_ticks")
        if (not isinstance(frames, dict) or set(frames) != set(map(str, TICKS))
                or not isinstance(groups, dict) or len(groups) != SHAPES[role]):
            raise ValueError("missing complete 24-tick original source timeline")
        reconstructed = {}
        for tick in TICKS:
            frame = frames[str(tick)]
            if not isinstance(frame, dict):
                raise ValueError("missing original source alpha SHA")
            digest = frame.get("source_2D_alpha_sha256")
            if (not isinstance(digest, str) or len(digest) != 64
                    or any(c not in "0123456789abcdef" for c in digest)):
                raise ValueError("malformed genuine source alpha SHA")
            reconstructed.setdefault(digest, []).append(tick)
        if groups != reconstructed:
            raise ValueError("original unique-source shape groups do not match actual source frames")
        arms = record.get("arms")
        if not isinstance(arms, dict) or set(arms) != set(ARMS):
            raise ValueError("one predeclared fixed pose missing or fitted arm inserted")
        role_stats = {}
        source_edge_counts = None
        for arm in ARMS:
            item = arms[arm]
            if (not isinstance(item, dict) or
                    item.get("original_chronological_source_frame_count") != 24 or
                    item.get("original_unique_64px_binary_shape_count") != SHAPES[role] or
                    item.get("source_actual_timeline_edge_count") != 23):
                raise ValueError("invalid original source sample/edge counts")
            edges = item.get("per_original_chronological_edge")
            if not isinstance(edges, list) or len(edges) != 23:
                raise ValueError("not all original 23 chronological edges recorded")
            totals = [0, 0, 0]
            source_changes = []
            candidate_edge_ticks = []
            for i, edge in enumerate(edges):
                if (not isinstance(edge, dict)
                        or edge.get("source_ticks") != [TICKS[i], TICKS[i + 1]]):
                    raise ValueError("original consecutive source edge omitted or reordered")
                tp, fp, fn = counts({k: edge.get(k) for k in ("tp", "fp", "fn")})
                if tp + fp + fn > 4096:
                    raise ValueError("one original 64px binary edge exceeds image bounds")
                observed = edge.get("iou")
                if (type(observed) not in (int, float) or not math.isfinite(observed)
                        or abs(observed - iou(tp, fp, fn)) > 5e-8):
                    raise ValueError("original per-edge IoU inconsistent with pixels")
                source_changes.append(tp + fn)
                if tp + fp:
                    candidate_edge_ticks.append([TICKS[i], TICKS[i + 1]])
                for j, number in enumerate((tp, fp, fn)):
                    totals[j] += number
            if source_edge_counts is None:
                source_edge_counts = source_changes
            elif source_edge_counts != source_changes:
                raise ValueError("same historical source changed masks cannot depend on candidate arm")
            if not all(source_changes):
                raise ValueError("every authentic original consecutive source edge must change")
            if tuple(totals) != counts(item.get("source_actual_23_consecutive_edge_change_tp_fp_fn")):
                raise ValueError("per-edge totals disagree with original source aggregate")
            stated = item.get("source_actual_23_consecutive_edge_change_pooled_iou")
            if (type(stated) not in (int, float)
                    or abs(stated - iou(*totals)) > 5e-8):
                raise ValueError("original motion score disagrees with raw edge counts")
            role_stats[arm] = {
                "original_nonempty_edges": sum(bool(n) for n in source_changes),
                "predicted_nonempty_edges": len(candidate_edge_ticks),
                "predicted_change_edge_ticks": candidate_edge_ticks,
                "original_changed_alpha_pixels": sum(source_changes),
                "predicted_changed_alpha_pixels": totals[0] + totals[1],
                "matched_changed_alpha_pixels": totals[0],
                "false_positive_changed_alpha_pixels": totals[1],
                "unexplained_original_changed_alpha_pixels": totals[2],
                "pooled_changed_alpha_iou": iou(*totals),
            }
        result[role] = role_stats
    return {
        "schema": "UR-ART4K-AUTHENTIC-MESEN24-EDGE-COVERAGE/1",
        "historical_original_and_real_glb_run": HISTORICAL_RUN,
        "historical_witness_artifact_id": 13354178658,
        "original_witness_json_sha256": WITNESS_SHA256,
        "historical_2026_glb_sha256": WITNESS_GLB_SHA256,
        "original_frames_per_player": 24,
        "original_edges_per_player": 23,
        "original_distinct_shapes": SHAPES,
        "roles_and_fixed_control_arms": result,
        "orientation_only_controls_cover_all_source_edges": all(
            result[role][arm]["predicted_nonempty_edges"] == 23
            for role in ROLES for arm in ARMS),
        "previous_owner_selected_wider_pedal_model_tested": False,
        "original_1994_mechanics_recovered": False,
        "shipping_art_approved": False,
    }


def analyze_historical_artifact(archive: Path):
    """Use exactly the historical Actions ZIP member; no live ROM or exporter."""
    with zipfile.ZipFile(archive) as zipped:
        if WITNESS_MEMBER not in zipped.namelist():
            raise ValueError("missing original Mesen24 real-GLB source witness")
        info = zipped.getinfo(WITNESS_MEMBER)
        if info.file_size > 2_000_000:
            raise ValueError("historical witness exceeds agreed evidence bounds")
        raw = zipped.read(info)
    if hashlib.sha256(raw).hexdigest() != WITNESS_SHA256:
        raise ValueError("historical original Mesen24 real-GLB witness SHA differs")
    return analyze_witness(json.loads(raw))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("historical_artifact_zip", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    text = json.dumps(analyze_historical_artifact(args.historical_artifact_zip),
                      indent=2, sort_keys=True) + "\n"
    if args.out:
        if args.out.exists():
            parser.error("refusing to overwrite retained independent evidence")
        with args.out.open("x", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
