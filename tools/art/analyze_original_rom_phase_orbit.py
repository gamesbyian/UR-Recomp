#!/usr/bin/env python3
"""Measure the original ROM phase-sensitive sprite-region orbit across 64 angles.

An already authenticated 2D bitmap-bounding-box diagnostic, not a 1994 3D rig.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from tools.art.no_replace_report import publish_text_once

SOURCE_SHA = "23aa563c094471a3d7f1b5dcb12489cc1b5ca45b1240aee06fde3934a932bbd0"
SOURCE_SCHEMA = "UR-ART4K-ORIGINAL-ROM-24PHASE-64ANGLE-AXIS-COUNTERFACTUAL/1"
SCHEMA = "UR-ART4K-ORIGINAL-ROM-PHASE-REGION-64ANGLE-2D-HARMONIC/1"


def harmonic(values):
    if (not isinstance(values, (tuple, list)) or len(values) != 64 or
            any(type(v) not in (int, float) or not math.isfinite(v) for v in values)):
        raise ValueError("64 finite original orientation samples required")
    n = 64
    center = sum(values)/n
    cos_coef = 2*sum(v*math.cos(2*math.pi*k/n)
                     for k,v in enumerate(values))/n
    sin_coef = 2*sum(v*math.sin(2*math.pi*k/n)
                     for k,v in enumerate(values))/n
    residuals = [v - center - cos_coef*math.cos(2*math.pi*k/n) -
                 sin_coef*math.sin(2*math.pi*k/n)
                 for k,v in enumerate(values)]
    mse = sum(r*r for r in residuals)/n
    variance = sum((v-center)**2 for v in values)/n
    return {
        "mean_source_pixel_center": center,
        "cos_first_harmonic": cos_coef,
        "sin_first_harmonic": sin_coef,
        "first_harmonic_amplitude_source_pixels": math.hypot(cos_coef, sin_coef),
        "rmse_source_pixels": math.sqrt(mse),
        "max_abs_residual_source_pixels": max(map(abs, residuals)),
        "constant_position_null_rmse_source_pixels": math.sqrt(variance),
        "first_harmonic_R_squared": 1-mse/variance if variance else 1.0 if mse==0 else 0.0,
    }


def audit(report_raw:bytes):
    if hashlib.sha256(report_raw).hexdigest() != SOURCE_SHA:
        raise ValueError("wrong exact original-ROM axis report SHA")
    report = json.loads(report_raw)
    if (report.get("schema") != SOURCE_SCHEMA or
            report.get("original_ROM_24phase_64angle_exact_source_frame_count") != 1536 or
            report.get("original_1994_3d_angle_camera_mesh_material_or_bone_mapping_recovered") is not False):
        raise ValueError("source 2D counterfactual provenance invalid")
    boxes = report.get("source_phase_variation_bbox_by_ROM_angle_index")
    if (not isinstance(boxes, dict) or
            set(boxes) != {str(i) for i in range(64)}):
        raise ValueError("source 64-angle bounding-box census incomplete")
    x, y, widths, heights = [], [], [], []
    for k in range(64):
        box = boxes[str(k)]
        if (not isinstance(box, list) or len(box) != 4 or
                any(type(v) is not int for v in box) or
                not 0 <= box[0] <= box[2] < 64 or
                not 0 <= box[1] <= box[3] < 64):
            raise ValueError("invalid source-only phase-sensitive pixel bounding box")
        x.append((box[0]+box[2])/2)
        y.append((box[1]+box[3])/2)
        widths.append(box[2]-box[0]+1)
        heights.append(box[3]-box[1]+1)
    fx, fy = harmonic(x), harmonic(y)
    # 7:6 pixel aspect belongs to the game's display; raw 64x64 coordinate
    # circles do not automatically remain circles in display-corrected space.
    return {
        "schema":SCHEMA,"source_axis_counterfactual_json_sha256":SOURCE_SHA,
        "input_positions":"centre of each phase-sensitive alpha/index bounding box",
        "source_angle_count":64,"source_phase_count":24,
        "coordinate_units":"original source 64x64 pixels, not physical 3D",
        "original_display_pixel_aspect_horizontal_over_vertical":[7,6],
        "source_x_first_harmonic":fx,"source_y_first_harmonic":fy,
        "source_x_region_bbox_width_values":sorted(set(widths)),
        "source_y_region_bbox_height_values":sorted(set(heights)),
        "display_corrected_horizontal_orbit_amplitude":fx["first_harmonic_amplitude_source_pixels"]*7/6,
        "vertical_orbit_amplitude":fy["first_harmonic_amplitude_source_pixels"],
        "original_1994_3D_camera_mesh_or_joint_axis_recovered":False,
        "source_orientation_index_physically_calibrated_in_degrees":False,
        "source_phase_is_real_wheel_rotation_calibrated":False,
        "hypothesis":"bounded 2D first-harmonic orbit; possible composed local phase and broader orientation",
        "measurement_reuses_previously_inspected_original_sprite_grid":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-axis-report",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=audit(a.original_axis_report.read_bytes())
    publish_text_once(a.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("ART4K_ORIGINAL_PHASE_ORBIT_HARMONIC",json.dumps({
        "x":result["source_x_first_harmonic"],
        "y":result["source_y_first_harmonic"]},sort_keys=True))


if __name__=="__main__":
    main()
