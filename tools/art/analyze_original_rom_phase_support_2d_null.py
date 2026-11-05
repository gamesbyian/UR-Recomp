#!/usr/bin/env python3
"""Original 24x64 racer phase-sensitive pixels versus fixed 2D motion controls.

The source is a recovered 2D ROM sprite manifold. This experiment cannot
identify the original 1994 3D mesh, rotation axis, camera or physical degrees.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from tools.art.no_replace_report import publish_text_once
from tools.art.analyze_original_rom_phase_orbit import (
    SOURCE_SHA as AXIS_REPORT_SHA, SOURCE_SCHEMA as AXIS_SCHEMA,
)
from tools.art.recover_original_mesen24_rom_pose_ids import (
    ROM_SHA, source_frame_tiles, render_original_primary_sprite64,
)

SCHEMA = "UR-ART4K-SOURCE-ORIGINAL-64-ANGLE-PHASE-SUPPORT-2D-NULL/1"
WIDTH = 64
PIXELS = WIDTH * WIDTH
ANGLES = range(64)
PHASES = range(24)
CONTROLS = ("static_support", "orbit_translation", "rigid_screen_rotation")


def source_supports(rom: bytes) -> tuple[bytes, ...]:
    """Pixel positions whose original 4bpp index varies with phase at fixed angle."""
    if len(rom) != 2_097_152 or hashlib.sha256(rom).hexdigest() != ROM_SHA:
        raise ValueError("wrong authentic original USA ROM")
    frames = source_frame_tiles(rom)
    if len(frames) != len(ANGLES) * len(PHASES):
        raise ValueError("incomplete original 24x64 frame table")
    supports = []
    for angle in ANGLES:
        initial = render_original_primary_sprite64(frames[angle])
        mask = bytearray(PIXELS)
        for phase in range(1, 24):
            other = render_original_primary_sprite64(frames[phase * 64 + angle])
            for i, (a, b) in enumerate(zip(initial, other)):
                if a != b:
                    mask[i] = 1
        if not any(mask):
            raise ValueError("empty phase-sensitive original source support")
        supports.append(bytes(mask))
    return tuple(supports)


def bbox(mask: bytes) -> list[int]:
    if not isinstance(mask, bytes) or len(mask) != PIXELS:
        raise ValueError("expected original 64x64 binary support")
    xs = [i % WIDTH for i, x in enumerate(mask) if x]
    ys = [i // WIDTH for i, x in enumerate(mask) if x]
    if not xs:
        raise ValueError("cannot register empty source support")
    return [min(xs), min(ys), max(xs), max(ys)]


def even_index_harmonic(values: list[float]) -> dict:
    """Fit harmonic only on even source orientations; assess odd angles separately."""
    if len(values) != 64 or any(not math.isfinite(v) for v in values):
        raise ValueError("64 finite original region centres required")
    samples = range(0, 64, 2)
    mean = sum(values[k] for k in samples) / len(samples)
    cos = 2 * sum(values[k] * math.cos(2 * math.pi * k / 64)
                  for k in samples) / len(samples)
    sin = 2 * sum(values[k] * math.sin(2 * math.pi * k / 64)
                  for k in samples) / len(samples)
    return {"mean": mean, "cos": cos, "sin": sin}


def harmonic_at(fit: dict, angle: int) -> float:
    t = 2 * math.pi * angle / 64
    return fit["mean"] + fit["cos"] * math.cos(t) + fit["sin"] * math.sin(t)


def predict_2d(mask: bytes, control: str, angle: int,
               x_fit: dict, y_fit: dict) -> bytes:
    """Map one fixed angle-0 support. No per-orientation registration or retuning.

    Source-screen coordinates are *raw SNES source pixels*: its 7:6 display
    correction is deliberately not applied to integer source mask sampling.
    """
    if not isinstance(mask, bytes) or len(mask) != PIXELS or set(mask) - {0, 1}:
        raise ValueError("invalid source binary support mask")
    if control not in CONTROLS or type(angle) is not int or not 0 <= angle < 64:
        raise ValueError("invalid frozen 2D motion control or angle")
    if control == "static_support":
        return mask
    theta = 2 * math.pi * angle / 64
    out = bytearray(PIXELS)
    if control == "orbit_translation":
        dx = harmonic_at(x_fit, angle) - harmonic_at(x_fit, 0)
        dy = harmonic_at(y_fit, angle) - harmonic_at(y_fit, 0)
        for y in range(64):
            for x in range(64):
                sx = math.floor(x - dx + 0.5)
                sy = math.floor(y - dy + 0.5)
                if 0 <= sx < 64 and 0 <= sy < 64:
                    out[y * 64 + x] = mask[sy * 64 + sx]
    else:
        # One fixed screen-space pivot from 32 even original box centres.
        # The index-angle's 2pi/64 step is a 2D hypothesis, not physical degrees.
        cx, cy = x_fit["mean"], y_fit["mean"]
        co, si = math.cos(theta), math.sin(theta)
        for y in range(64):
            for x in range(64):
                dx, dy = x - cx, y - cy
                sx = math.floor(cx + co * dx + si * dy + 0.5)
                sy = math.floor(cy - si * dx + co * dy + 0.5)
                if 0 <= sx < 64 and 0 <= sy < 64:
                    out[y * 64 + x] = mask[sy * 64 + sx]
    return bytes(out)


def compare(expected: bytes, predicted: bytes) -> dict:
    if (not isinstance(expected, bytes) or not isinstance(predicted, bytes)
            or len(expected) != PIXELS or len(predicted) != PIXELS
            or set(expected) - {0, 1} or set(predicted) - {0, 1}):
        raise ValueError("source support comparison requires binary 64x64 planes")
    tp = sum(a == 1 and b == 1 for a, b in zip(expected, predicted))
    fp = sum(a == 0 and b == 1 for a, b in zip(expected, predicted))
    fn = sum(a == 1 and b == 0 for a, b in zip(expected, predicted))
    union = tp + fp + fn
    return {"intersection": tp, "predicted_only": fp, "source_only": fn,
            "source_support_pixels": tp + fn, "predicted_support_pixels": tp + fp,
            "iou": round(tp / union, 8) if union else 1.0,
            "recall": round(tp / (tp + fn), 8) if tp + fn else 1.0,
            "precision": round(tp / (tp + fp), 8) if tp + fp else 1.0}


def audit(rom: bytes, axis_raw: bytes) -> dict:
    if hashlib.sha256(axis_raw).hexdigest() != AXIS_REPORT_SHA:
        raise ValueError("wrong authenticated 24x64 source axis report SHA")
    source = json.loads(axis_raw)
    if (source.get("schema") != AXIS_SCHEMA
            or source.get("original_ROM_24phase_64angle_exact_source_frame_count") != 1536
            or source.get("original_1994_3d_angle_camera_mesh_material_or_bone_mapping_recovered") is not False):
        raise ValueError("original source axis provenance invalid")
    supports = source_supports(rom)
    reported_boxes = source.get("source_phase_variation_bbox_by_ROM_angle_index")
    if (not isinstance(reported_boxes, dict)
            or set(reported_boxes) != {str(k) for k in ANGLES}):
        raise ValueError("original source angle census missing")
    boxes = [bbox(supports[k]) for k in ANGLES]
    if any(boxes[k] != reported_boxes[str(k)] for k in ANGLES):
        raise ValueError("reconstructed original source pixel support bbox mismatch")
    x_centres = [(b[0] + b[2]) / 2 for b in boxes]
    y_centres = [(b[1] + b[3]) / 2 for b in boxes]
    x_fit = even_index_harmonic(x_centres)
    y_fit = even_index_harmonic(y_centres)
    fixed = supports[0]
    score_rows = []
    for angle in range(1, 64, 2):
        actual = supports[angle]
        controls = {control: compare(actual, predict_2d(
            fixed, control, angle, x_fit, y_fit)) for control in CONTROLS}
        score_rows.append({"original_ROM_orientation_index": angle,
                           "source_support_pixels": sum(actual),
                           "controls": controls})
    aggregate = {}
    for name in CONTROLS:
        rows = [row["controls"][name] for row in score_rows]
        tp = sum(row["intersection"] for row in rows)
        fp = sum(row["predicted_only"] for row in rows)
        fn = sum(row["source_only"] for row in rows)
        aggregate[name] = {
            "tested_odd_orientation_count": len(rows),
            "mean_per_orientation_iou": round(sum(row["iou"] for row in rows) / len(rows), 8),
            "pooled_iou": round(tp / (tp + fp + fn), 8),
            "pooled_intersection": tp, "pooled_false_positive": fp,
            "pooled_false_negative": fn}
    observed_support = [sum(mask) for mask in supports]
    return {
        "schema": SCHEMA,
        "source_USA_ROM_sha256": ROM_SHA,
        "source_original_24phase_64angle_axis_report_sha256": AXIS_REPORT_SHA,
        "original_frame_grid_size": [24, 64],
        "original_pixel_coordinate_space": "64x64 raw SNES source, aspect 7:6 at display",
        "predeclared_fixed_support_reference_angle": 0,
        "harmonic_fit_source_orientation_parity": "even-only 0,2,...,62",
        "scored_orientation_parity": "odd-only 1,3,...,63 retrospective diagnostics",
        "source_support_pixels_min": min(observed_support),
        "source_support_pixels_max": max(observed_support),
        "source_support_pixels_reference_zero": observed_support[0],
        "source_even_index_x_fit": x_fit, "source_even_index_y_fit": y_fit,
        "controls_are_source_space_2D_nulls_not_3D": True,
        "rigid_screen_rotation_step_is_uncalibrated_2pi_over_64": True,
        "original_1994_3D_mesh_camera_joint_axis_recovered": False,
        "source_racer_art_owner_approved": False,
        "summary": aggregate, "scored_odd_orientation_rows": score_rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", required=True, type=Path)
    parser.add_argument("--original-axis-report", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.rom.read_bytes(), args.original_axis_report.read_bytes())
    publish_text_once(args.out, json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("ART4K_ORIGINAL_PHASE_SUPPORT_2D_NULL", json.dumps({
        "summary": result["summary"],
        "support_range": [result["source_support_pixels_min"],
                          result["source_support_pixels_max"]]
    }, sort_keys=True))


if __name__ == "__main__":
    main()
