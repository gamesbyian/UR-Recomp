#!/usr/bin/env python3
"""Audit measured projected racer poses across a source-hash-bound time sequence.

No image reconstruction, Blender rig inference, automatic style approval or
authenticity claim. Reuses the existing PNG identity + landmark validator.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from tools.art.measure_unicycle_reference import (
        measure, SCHEMA, text_field,
    )
    from tools.art.validate_upscale_trials import ensure, TrialError
except ModuleNotFoundError:
    from measure_unicycle_reference import measure, SCHEMA, text_field
    from validate_upscale_trials import ensure, TrialError


SEQUENCE_SCHEMA = "UR-RACER-LIKENESS-MOTION-AUDIT/1"
METRICS = (
    "wheel_width_over_wheel_height",
    "saddle_width_over_wheel_diameter",
    "saddle_height_over_wheel_diameter",
    "saddle_top_minus_wheel_top_over_wheel_diameter",
    "saddle_center_x_from_wheel_center_over_diameter",
    "saddle_center_y_from_wheel_center_over_diameter",
)
ASPECT_FACTOR = {"square": 1.0, "snes_7_6": 7.0 / 6.0}


def projected_pose_metrics(view: dict) -> dict:
    """Source-image projection in one pose, never a recovered 3D rig."""
    p = view["landmark_pixel_coordinates"]
    aspect = ASPECT_FACTOR[view["pixel_aspect"]]
    wheel_height = p["wheel_bottom"][1] - p["wheel_top"][1]
    wheel_cx = (p["wheel_left"][0] + p["wheel_right"][0]) / 2
    wheel_cy = (p["wheel_top"][1] + p["wheel_bottom"][1]) / 2
    saddle_cx = (p["saddle_left"][0] + p["saddle_right"][0]) / 2
    saddle_cy = (p["saddle_top"][1] + p["saddle_bottom"][1]) / 2
    return {
        **{key: view["projected_ratios"][key] for key in METRICS[:4]},
        "saddle_center_x_from_wheel_center_over_diameter":
            round((saddle_cx - wheel_cx) * aspect / wheel_height, 6),
        "saddle_center_y_from_wheel_center_over_diameter":
            round((saddle_cy - wheel_cy) / wheel_height, 6),
    }


def audit(manifest: Path) -> dict:
    # measure() hashes and validates every unmodified local reference PNG,
    # including coordinates, view angle, pixel aspect and provenance.
    measured = measure(manifest)
    raw = json.loads(manifest.read_text(encoding="utf-8"))
    ensure(raw.get("schema") == SCHEMA, "landmark schema must be validated")
    sequences = raw.get("sequences")
    ensure(isinstance(sequences, list) and bool(sequences),
           "at least one explicit temporal sequence is required")
    by_id = {x["reference_id"]: x for x in measured["views"]}
    output = []
    sequence_ids = set()
    for sequence in sequences:
        ensure(isinstance(sequence, dict), "sequence must be an object")
        ident = text_field(sequence.get("id"), "sequence id")
        ensure(ident not in sequence_ids, "duplicate sequence ID")
        sequence_ids.add(ident)
        mode = sequence.get("camera_mode")
        ensure(mode in ("declared-fixed", "unverified-or-moving"),
               "camera mode must be explicit")
        camera_notes = text_field(sequence.get("camera_notes"),
                                  f"{ident}: camera evidence/uncertainty")
        frames = sequence.get("frames")
        ensure(isinstance(frames, list) and len(frames) >= 2,
               f"{ident}: at least two time-tagged frames required")
        selected = []
        visited = set()
        last_ms = -1
        for frame in frames:
            ensure(isinstance(frame, dict), f"{ident}: invalid frame record")
            rid = text_field(frame.get("reference_id"), f"{ident}: frame reference")
            millis = frame.get("time_ms")
            ensure(rid in by_id, f"{ident}: reference absent from validated manifest")
            ensure(rid not in visited, f"{ident}: duplicate frame reference")
            ensure(type(millis) is int and millis >= 0 and millis > last_ms,
                   f"{ident}: time_ms must be strictly increasing integers")
            visited.add(rid)
            last_ms = millis
            view = by_id[rid]
            selected.append({
                "reference_id": rid, "time_ms": millis,
                "image_sha256": view["image_sha256"],
                "source_kind": view["source_kind"],
                "source_credit": view["source_credit"],
                "region_or_version": view["region_or_version"],
                "view_angle": view["view_angle"],
                "pixel_aspect": view["pixel_aspect"],
                "image_dimensions": view["image_dimensions"],
                "crop_and_rescale_history": view["crop_and_rescale_history"],
                "projected_pose_metrics": projected_pose_metrics(view),
            })
        baseline = selected[0]
        common = ("source_kind", "source_credit", "region_or_version",
                  "pixel_aspect")
        ensure(all(all(row[key] == baseline[key] for key in common)
                   for row in selected[1:]),
               f"{ident}: mixed source identity/pixel-aspect invalidates motion series")
        fixed_keys = ("view_angle", "image_dimensions",
                      "crop_and_rescale_history")
        consistent_projection = all(
            all(row[key] == baseline[key] for key in fixed_keys)
            for row in selected[1:]
        ) and baseline["view_angle"] != "unknown"
        if mode == "declared-fixed":
            ensure(consistent_projection,
                   f"{ident}: fixed projection declaration contradicts source tags")
        transitions = []
        for prior, current in zip(selected, selected[1:]):
            a, b = prior["projected_pose_metrics"], current["projected_pose_metrics"]
            transitions.append({
                "from_reference_id": prior["reference_id"],
                "to_reference_id": current["reference_id"],
                "elapsed_ms": current["time_ms"] - prior["time_ms"],
                "projected_metric_deltas": {
                    key: round(b[key] - a[key], 6) for key in METRICS
                },
            })
        spans = {
            key: round(max(row["projected_pose_metrics"][key] for row in selected) -
                       min(row["projected_pose_metrics"][key] for row in selected), 6)
            for key in METRICS
        }
        output.append({
            "sequence_id": ident,
            "camera_mode_declared": mode,
            "camera_notes": camera_notes,
            "source_tags_consistent_for_fixed_projection": consistent_projection,
            "fixed_physical_3d_camera_independently_proven": False,
            "frame_count": len(selected),
            "frames": selected,
            "adjacent_projected_changes": transitions,
            "metric_spans_over_sequence": spans,
            "motion_continuity_or_likeness_automatically_approved": False,
        })
    return {
        "schema": SEQUENCE_SCHEMA,
        "validated_source_view_count": measured["view_count"],
        "sequence_count": len(output),
        "sequences": output,
        "original_artist_3d_rig_recovered": False,
        "original_character_likeness_approved": False,
        "shipping_art_approved": False,
        "limits": (
            "All PNGs are hash-validated source views. Projected landmarks "
            "measure 2D motion only; tags and times are declared, not an "
            "independent temporal video oracle. Distinct pose, camera, art "
            "style, occlusion and physical scale can alter every ratio. "
            "Reviewers must evaluate real gameplay-scale animation and "
            "official character references before any artistic approval."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        result = audit(args.manifest)
    except (TrialError, ValueError, TypeError, KeyError, OSError) as exc:
        parser.exit(2, f"invalid racer animation reference: {exc}\n")
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
