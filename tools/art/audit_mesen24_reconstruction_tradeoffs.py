#!/usr/bin/env python3
"""Audit shape-versus-motion trade-offs in authentic Mesen24 ART-4K reports.

Research-only: never convert image-space scores into original 1994 model,
owner-likeness, or Windows release acceptance.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

SCHEMA = "UR-ART4K-EXACT-ORIGINAL-MESEN24-SADDLE-TEMPORAL-EVIDENCE/1"
ROLES = ("blue", "red")
METRICS = ("chronological_pooled_iou",
           "unique_shape_equal_vote_mean_iou",
           "real_23_tick_edge_change_pooled_iou")


def audit(report, baseline="axle_root_saddle_neutral"):
    """Require a same-source, same-arm cross-role comparison, no role cherry-pick."""
    if not isinstance(report, dict) or report.get("schema") != SCHEMA:
        raise ValueError("unrecognized authentic source report")
    producer = report.get("producer")
    if not isinstance(producer, dict):
        raise ValueError("missing source-provenance record")
    for k in ("original_source_USA_ROM_sha256", "original_Mesen24_archive_sha256",
              "original_pose_report_sha256", "original_axis_sha256",
              "provisional_camera_sha256", "current_2026_authored_SCAD_sha256"):
        s = producer.get(k)
        if not isinstance(s, str) or len(s) != 64 or any(c not in "0123456789abcdef" for c in s):
            raise ValueError("missing exact source identity: " + k)
    if (producer.get("original_1994_physical_3d_model_or_camera_recovered") is not False
            or producer.get("original_art_likeness_approved") is not False):
        raise ValueError("scientific and artistic veto flags must remain false")
    roles = report.get("reported_per_role")
    if not isinstance(roles, dict) or set(roles) != set(ROLES):
        raise ValueError("both original source roles are mandatory")
    if not all(isinstance(roles[r], dict) for r in ROLES):
        raise ValueError("invalid role evidence")
    arms = set(roles["blue"])
    if baseline not in arms or arms != set(roles["red"]):
        raise ValueError("candidate/control arms differ between source roles")
    if "original_source_2d_rotation" not in arms:
        raise ValueError("missing original-art rigid-rotation null")
    values = {}
    for arm in sorted(arms):
        values[arm] = {}
        for role in ROLES:
            item = roles[role][arm]
            if not isinstance(item, dict) or type(item.get("unique_shapes")) is not int:
                raise ValueError("missing SHA-distinct source counts")
            expected_shapes = 19 if role == "blue" else 23
            if item["unique_shapes"] != expected_shapes:
                raise ValueError("unexpected exact Mesen24 distinct-shape count")
            vals = []
            for name in METRICS:
                value = item.get(name)
                if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError("invalid bounded source metric: " + name)
                vals.append(float(value))
            values[arm][role] = vals
    comparisons = {}
    for arm in sorted(arms - {baseline, "original_source_2d_rotation"}):
        differences = {
            role: [round(v - b, 8) for v, b in zip(values[arm][role], values[baseline][role])]
            for role in ROLES
        }
        flat = [x for row in differences.values() for x in row]
        comparisons[arm] = {
            "delta_against_neutral_by_role": dict(zip(ROLES, (
                dict(zip(METRICS, differences[role])) for role in ROLES))),
            "dominates_neutral_all_roles_and_metrics": all(x >= 0 for x in flat) and any(x > 0 for x in flat),
            "shape_gain_both_roles": all(differences[r][1] > 0 for r in ROLES),
            "chronological_motion_gain_both_roles": all(differences[r][2] > 0 for r in ROLES),
        }
    return {
        "schema": "UR-ART4K-MESEN24-MULTIOBJECTIVE-REVIEW/1",
        "baseline": baseline,
        "source_identity": {k: producer[k] for k in (
            "original_source_USA_ROM_sha256", "original_Mesen24_archive_sha256",
            "original_pose_report_sha256", "original_axis_sha256",
            "provisional_camera_sha256", "current_2026_authored_SCAD_sha256")},
        "metrics": METRICS,
        "comparisons": comparisons,
        "historical_3d_recovered": False,
        "likeness_approved": False,
        "shipping_art_approved": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    reviewed = audit(json.loads(args.report.read_text(encoding="utf-8")))
    encoded = json.dumps(reviewed, indent=2, sort_keys=True) + "\n"
    if args.out:
        if args.out.exists():
            parser.error("refusing to overwrite review evidence")
        args.out.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
