#!/usr/bin/env python3
"""Project the original ROM phase-region orbit onto the provisional 2026 rig plane.

A camera-conditioned, two-pivot diagnostic. Source y/depth is unconstrained;
the original artist's 1994 mesh, camera, joints and physical degrees remain unknown.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from tools.art.no_replace_report import publish_text_once
from tools.art.glb_parent_part_id_raster import validated_camera
from tools.art.analyze_original_rom_phase_orbit import (
    SOURCE_SHA, SOURCE_SCHEMA, audit as phase_orbit_audit,
)

CAMERA_SHA = "1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028"
SCHEMA = "UR-ART4K-SOURCE-PHASE-ORBIT-TO-2026-PROVISIONAL-PIVOT/1"
# Existing historical (not reconstructed) source blockout at
# tools/art/candidates/unicycle_shared_rig.scad, SHA e99ef45..., #2832:
# shared_rig translate z=1.0; continuous_rig local stunt pivot z=1.80.
# These are choices authored in 2026, not evidence of 1994 geometry.
CANDIDATE_PIVOTS = {
    "historical_2026_wheel_axle": (0.0, 0.0, 1.0),
    "historical_2026_continuous_stunt_midbody": (0.0, 0.0, 1.8),
}
CANDIDATE_SCAD_SHA = "e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984"


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def projection(camera: dict, point: tuple[float, float, float]) -> tuple[float, float]:
    right, up, origin, scale, anchor, _ = validated_camera(camera)
    if len(point) != 3 or any(not math.isfinite(v) for v in point):
        raise ValueError("finite 3D hypothetical point required")
    offset = [point[i] - origin[i] for i in range(3)]
    return (anchor[0] / 2 + dot(offset, right) * scale * 6 / 7,
            anchor[1] / 2 - dot(offset, up) * scale)


def source_backprojection(camera: dict, pixel: tuple[float, float]) -> dict:
    right, up, origin, scale, anchor, front = validated_camera(camera)
    if len(pixel) != 2 or any(not math.isfinite(v) for v in pixel):
        raise ValueError("finite original 2D source position required")
    r = (pixel[0] - anchor[0] / 2) / (scale * 6 / 7)
    u = (anchor[1] / 2 - pixel[1]) / scale
    # One *line* in world space, not one recovered 3D point.
    point = [origin[i] + r * right[i] + u * up[i] for i in range(3)]
    return {
        "world_point_at_zero_declaration_depth": point,
        "unconstrained_camera_depth_direction_world": list(front),
        "world_depth_coordinate_identified": False,
        "world_lateral_component": r,
        "world_up_component": u,
    }


def projected_2026_wheel_axle_root_orbit(camera:dict,
                                           pivot:tuple[float,float,float],
                                           source_orientation_index:int)->tuple[float,float]:
    """One frozen provisional 3D root-angle hypothesis, one 2026 axle.

    The whole 2026 GLB source is a lost-historical-rig **candidate only**.
    The original 64 ROM orientation IDs are an uncalibrated 2D index system,
    not measured physical 1994 degrees.
    """
    if (type(source_orientation_index) is not int or
            not 0<=source_orientation_index<64 or
            pivot not in CANDIDATE_PIVOTS.values()):
        raise ValueError("one original 64-index state and a historical 2026 pivot required")
    axle=CANDIDATE_PIVOTS["historical_2026_wheel_axle"]
    theta=math.tau*source_orientation_index/64
    c,s=math.cos(theta),math.sin(theta)
    x=pivot[0]+c*(axle[0]-pivot[0])+s*(axle[2]-pivot[2])
    y=pivot[1]+(axle[1]-pivot[1])
    z=pivot[2]-s*(axle[0]-pivot[0])+c*(axle[2]-pivot[2])
    return projection(camera,(x,y,z))


def compare_full_64_source_orbit(camera:dict,source_boxes:dict)->dict:
    if (not isinstance(source_boxes,dict) or
            set(source_boxes)!={str(i) for i in range(64)}):
        raise ValueError("original 64-state ROM phase-region box table required")
    observed=[]
    for k in range(64):
        b=source_boxes[str(k)]
        if (type(b) is not list or len(b)!=4 or
                any(type(v) is not int for v in b) or
                not 0<=b[0]<=b[2]<64 or not 0<=b[1]<=b[3]<64):
            raise ValueError("invalid original 1994 source-region bounding box")
        observed.append(((b[0]+b[2])/2,(b[1]+b[3])/2))
    report={}
    for name,pivot in CANDIDATE_PIVOTS.items():
        predicted=[projected_2026_wheel_axle_root_orbit(camera,pivot,k)
                   for k in range(64)]
        total_raw=[0.,0.];total_displacement=[0.,0.]
        for k,(sx,sy) in enumerate(observed):
            for j,source_coord in enumerate((sx,sy)):
                total_raw[j]+=(source_coord-predicted[k][j])**2
                total_displacement[j]+=(
                    (source_coord-observed[0][j])-
                    (predicted[k][j]-predicted[0][j]))**2
        raw_rmse=[math.sqrt(x/64) for x in total_raw]
        relative_rmse=[math.sqrt(x/64) for x in total_displacement]
        report[name]={
            "historical_2026_fixed_source_world_pivot":list(pivot),
            "model_wheel_axle_at_source_orientation_zero_xy":list(predicted[0]),
            "model_wheel_axle_at_source_orientation_32_xy":list(predicted[32]),
            "source_absolute_unfitted_pixel_xy_rmse":raw_rmse,
            "source_angle_zero_reference_subtracted_pixel_xy_rmse":relative_rmse,
            "source_angle_zero_reference_subtracted_7_6_display_xy_rmse":
                [relative_rmse[0]*7/6,relative_rmse[1]],
            "whole_2d_orbit_displacement_rmse_7_6_display_pixels":
                math.hypot(relative_rmse[0]*7/6,relative_rmse[1]),
            "original_1994_wheel_axle_location_measured":False,
        }
    return {
        "original_ROM_source_orientation_count":64,
        "source_angle_zero_region_center_source_xy":list(observed[0]),
        "source_angle_32_region_center_source_xy":list(observed[32]),
        "rig_candidate_root_index_angle_assumption":"2pi * original index / 64, UNCALIBRATED",
        "source_phase_sensitive_region_not_a_verified_original_3D_wheel_hub":True,
        "source_2D_orbit_hypothesis_two_historical_2026_pivots":report,
    }


def audit(axis_raw: bytes, camera_raw: bytes) -> dict:
    if hashlib.sha256(axis_raw).hexdigest() != SOURCE_SHA:
        raise ValueError("wrong original ROM phase-orbit axis report")
    if hashlib.sha256(camera_raw).hexdigest() != CAMERA_SHA:
        raise ValueError("wrong provisional original-SNES camera hypothesis")
    src = json.loads(axis_raw)
    if src.get("schema") != SOURCE_SCHEMA:
        raise ValueError("wrong original ROM 24x64 source axis schema")
    orbit = phase_orbit_audit(axis_raw)
    camera = json.loads(camera_raw)
    validated_camera(camera)
    centre = (
        orbit["source_x_first_harmonic"]["mean_source_pixel_center"],
        orbit["source_y_first_harmonic"]["mean_source_pixel_center"],
    )
    recovered_line = source_backprojection(camera, centre)
    full_orbits=compare_full_64_source_orbit(
        camera,src["source_phase_variation_bbox_by_ROM_angle_index"])
    row = {}
    for name, world in CANDIDATE_PIVOTS.items():
        px = projection(camera, world)
        residual = (px[0] - centre[0], px[1] - centre[1])
        row[name] = {
            "historical_2026_hypothetical_world_xyz": list(world),
            "hypothetical_projected_source_pixel_xy": list(px),
            "raw_source_pixel_residual_xy": list(residual),
            "distance_in_7_6_corrected_source_display_pixel_units": math.hypot(
                residual[0] * 7 / 6, residual[1]),
        }
    return {
        "schema": SCHEMA,
        "source_ROM_phase_axis_report_sha256": SOURCE_SHA,
        "source_original_24x64_2D_orbit_mean_source_pixel_xy": list(centre),
        "source_original_7_6_SNes_horizontal_pixel_ratio": [7, 6],
        "provisional_2026_fixed_side_camera_sha256": CAMERA_SHA,
        "historical_2026_unapproved_SCAD_source_sha256": CANDIDATE_SCAD_SHA,
        "source_orbit_pivot_backprojection_is_camera_conditional": True,
        "source_orbit_centre_backprojected_world_line": recovered_line,
        "hypothetical_existing_2026_part_pivots": row,
        "all_original_64_source_angle_region_vs_existing_2026_axle_orbits": full_orbits,
        "original_source_1994_camera_or_mesh_recovered": False,
        "original_1994_3D_joint_pivot_recovered": False,
        "owner_likeness_approved": False,
        "strictly_two_preexisting_2026_candidate_pivots_no_optimization": True,
        "shared_camera_7_6_and_glb_model_same_scale_not_independently_verified": True,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-axis-report", type=Path, required=True)
    p.add_argument("--camera", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    record = audit(a.original_axis_report.read_bytes(), a.camera.read_bytes())
    publish_text_once(a.out, json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("ART4K_SOURCE_ORBIT_TWO_HISTORICAL_2026_PIVOTS",
          json.dumps(record["hypothetical_existing_2026_part_pivots"], sort_keys=True))
    print("OK ART4K_SOURCE_ORBIT_ALL64_2026_AXLE_ROOT_CONTROLS",
          json.dumps(
              record["all_original_64_source_angle_region_vs_existing_2026_axle_orbits"]
              ["source_2D_orbit_hypothesis_two_historical_2026_pivots"],
              sort_keys=True))


if __name__ == "__main__":
    main()
