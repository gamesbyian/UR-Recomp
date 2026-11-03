#!/usr/bin/env python3
"""Quantify two PREDECLARED 2D projection-orientation arms using real original RGB.

One arm keeps the same 2026 experimental GLB screen projection for both
players. The other mirrors that GLB projection for authentic original
upper-viewport red. Neither is a recovered 1994 camera/3D animation pose.
All source raster and original P6 identity checks reuse the merged evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import zipfile

from tools.art.audit_original_mesen_sparse_pose_correspondence import (
    SOURCE_ZIP_SHA, TICKS, validate_receipt, audit_source,
)
from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_mesen_obj_screen_pixels import decode_source_obj
from tools.art.audit_original_racer_chroma_axes import painted_axis
from tools.art.select_original_mesen_live_pose_exemplars import visible_rgba
from tools.art.no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-ORIGINAL-LIVE40-SOURCE-VS-2026-GLB-PAINT-AXIS-MIRROR-SENSITIVITY/1"
AXIS_SCHEMA = "UR-ART4K-AUTHENTIC-SOURCE-VS-REAL-GLB-PAINTED-AXIS-SUMMARY/1"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
MODEL_COMMIT = "d061cddcdbac9b2b5ac137d0d721b63f92dc3ec1"
CAMERA_SHA = "1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028"
POSES = ("upright", "pedal", "wheelie", "stunt", "bank")
EXPECTED_AXES = {
    "upright": 6.944131,
    "pedal": 6.944131,
    "wheelie": 33.869252,
    "stunt": -43.167160,
    "bank": 9.272860,
}
ARMS = ("shared_model_projection", "red_model_projection_reflected")
THRESHOLDS = (10.0, 20.0)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def frozen_glb_axes(packet: dict) -> dict[str, float]:
    """Require the exact already inspected five-GLB real-source axis experiment."""
    if (type(packet) is not dict or packet.get("schema") != AXIS_SCHEMA or
            packet.get("run_id") != 41290041584 or
            packet.get("source_rom_sha256") != ROM_SHA or
            packet.get("model_2026_source_commit") != MODEL_COMMIT or
            packet.get("provisional_camera_sha256") != CAMERA_SHA or
            packet.get("original_1994_pixel_aspect") != "7:6" or
            packet.get("source_independent_binary_silhouettes") != 35 or
            packet.get("experimental_pose_paint_axes_deg") != EXPECTED_AXES or
            any(packet.get("caveats", {}).get(key) is not False for key in (
                "original_1994_3d_camera_identified",
                "original_1994_mesh_or_joints_recovered",
                "original_sprite_2026_glb_pose_correspondence_verified",
                "owner_character_likeness_approved", "shipping_art_approved"))):
        raise ValueError("not the frozen authenticated five-GLB projected-axis evidence")
    return dict(EXPECTED_AXES)


def axis_gap(source_angle: float, glb_axes: dict[str, float], *,
             red: bool, arm: str) -> float:
    """One globally predeclared reflection per racer and arm, never per-frame."""
    if (type(source_angle) not in (int, float) or
            not math.isfinite(source_angle) or not -90 < source_angle < 90 or
            type(red) is not bool or arm not in ARMS or
            not isinstance(glb_axes, dict) or
            glb_axes != EXPECTED_AXES):
        raise ValueError("invalid immutable screen/camera axis comparison")
    sign = -1 if (red and arm == "red_model_projection_reflected") else 1
    return round(min(abs(source_angle - sign * value)
                     for value in glb_axes.values()), 6)


def summarize(rows: list[dict]) -> dict:
    """One vote per authenticated original frame/racer, no best-GLB pose label."""
    expected = [(tick, racer) for tick in TICKS for racer in ("blue", "red")]
    if (type(rows) is not list or
            [(r.get("tick"), r.get("racer")) for r in rows] != expected):
        raise ValueError("original 20-tick x two-racer census incomplete")
    out = {}
    for arm in ARMS:
        samples = {}
        for racer in ("blue", "red"):
            group = [r["nearest_projected_angle_gap_deg"][arm] for r in rows
                     if r["racer"] == racer]
            if (len(group) != 20 or
                    any(type(x) not in (float,int) or
                        not math.isfinite(x) or not 0 <= x < 180 for x in group)):
                raise ValueError("invalid real source versus model projected gap")
            samples[racer] = {
                "source_observations": 20,
                "mean_nearest_glb_axis_gap_deg": round(sum(group)/20,6),
                "max_nearest_glb_axis_gap_deg": max(group),
                "source_observations_gap_over_10_deg": sum(x > 10 for x in group),
                "source_observations_gap_over_20_deg": sum(x > 20 for x in group),
            }
        all_gaps = [r["nearest_projected_angle_gap_deg"][arm] for r in rows]
        out[arm] = {
            "original_2D_source_observations": 40,
            "source_observations_gap_over_10_deg": sum(x>10 for x in all_gaps),
            "source_observations_gap_over_20_deg": sum(x>20 for x in all_gaps),
            "mean_nearest_glb_axis_gap_deg": round(sum(all_gaps)/40,6),
            "maximum_nearest_glb_axis_gap_deg": max(all_gaps),
            "by_original_racer": samples,
        }
    return out


def compare(original_zip: Path, receipt_path: Path, glb_axis_path: Path) -> dict:
    registration = json.loads(receipt_path.read_text())
    validate_receipt(registration)
    orig = audit_source(original_zip, registration)
    if (orig.get("actual_source_zip_sha256") != SOURCE_ZIP_SHA or
            orig.get("source_pixel_accounting") !=
            {"opaque": 12937, "exact": 12416, "red_plus_13": 521} or
            orig.get("unexplained_original_source_pixels") != 0):
        raise ValueError("original source screen pixels not independently verified")
    axis_bytes = glb_axis_path.read_bytes()
    frozen = frozen_glb_axes(json.loads(axis_bytes))
    rows = []
    with zipfile.ZipFile(original_zip) as archive:
        for example in registration["samples"]:
            tick = example["tick"]
            oam = decode_oam(archive.read(f"frame-{tick:06d}-oam.bin"))
            vram = archive.read(f"frame-{tick:06d}-vram.bin")
            cgram = archive.read(f"frame-{tick:06d}-cgram.bin")
            for racer, slot, player in (
                    ("blue", 96, "p2"), ("red", 97, "p1")):
                obj = decode_source_obj(
                    oam[slot], vram, cgram, oam_mode=4,
                    obj_base=0x6000, second_table_offset=0x1000)
                source_axis = painted_axis(obj["rgba"], player)
                screen_rgba = visible_rgba(obj["rgba"], racer)
                screen_axis = painted_axis(screen_rgba, player)
                held = source_axis["signed_axis_angle_from_image_vertical_deg"]
                screen = screen_axis["signed_axis_angle_from_image_vertical_deg"]
                if (obj["opaque_count"] != example[racer]["opaque"] or
                        screen_axis["pixel_count"] != source_axis["pixel_count"] or
                        (racer == "blue" and held != screen) or
                        (racer == "red" and abs(held+screen) > .000002)):
                    raise ValueError("authentic original held/screen 2D colour axes differ")
                rows.append({
                    "tick":tick, "racer":racer,
                    "held_source_4bpp_index_plane_sha256": sha(obj["plane"]),
                    "original_held_RGBA_sha256": sha(obj["rgba"]),
                    "actual_original_completed_screen_xy": example[racer]["screen_xy"],
                    "original_coloured_source_pixel_count":screen_axis["pixel_count"],
                    "original_held_chroma_axis_deg":held,
                    "original_completed_screen_chroma_axis_deg":screen,
                    "completed_screen_horizontal_mirror_from_held": racer=="red",
                    "nearest_projected_angle_gap_deg": {
                        arm: axis_gap(screen,frozen,red=racer=="red",arm=arm)
                        for arm in ARMS},
                })
    summary = summarize(rows)
    if (summary["shared_model_projection"]["source_observations_gap_over_10_deg"] <
            summary["red_model_projection_reflected"]["source_observations_gap_over_10_deg"]):
        raise ValueError("expected original camera-orientation sensitivity absent")
    return {
        "schema": SCHEMA,
        "original_USA_ROM_SHA256": ROM_SHA,
        "original_source_zip_sha256": SOURCE_ZIP_SHA,
        "original_Mesen_source_run_id": 41605614082,
        "original_source_artifact_id": 13217381754,
        "frozen_experimental_2026_GLb_axis_report_sha256": sha(axis_bytes),
        "frozen_2026_GLb_commit": MODEL_COMMIT,
        "provisional_camera_sha256": CAMERA_SHA,
        "source_pixel_aspect": "7:6",
        "source_all_40_screen_correspondences_verified": True,
        "fixed_racer_wide_screen_orientation": "red source alpha and RGB reflected to original completed upper viewport; blue unchanged",
        "model_projection_orientation_arms": list(ARMS),
        "model_mirror_choice_optimized_per_source": False,
        "experimental_glb_geometry_or_camera_fitted": False,
        "genuine_original_1994_3D_camera_or_joint_pose_recovered": False,
        "source_to_2026_GLb_pose_labels_verified": False,
        "model_painted_frame_equals_original_3D_anatomical_part": False,
        "owner_likeness_approved": False,
        "summary": summary,
        "per_source": rows,
    }


def compact_receipt(result: dict) -> dict:
    """Keep only the fixed comparisons + actual source coordinates in git."""
    return {
        key: result[key] for key in (
            "schema", "original_USA_ROM_SHA256", "original_source_zip_sha256",
            "original_Mesen_source_run_id", "original_source_artifact_id",
            "frozen_experimental_2026_GLb_axis_report_sha256",
            "frozen_2026_GLb_commit", "provisional_camera_sha256",
            "source_pixel_aspect", "source_all_40_screen_correspondences_verified",
            "fixed_racer_wide_screen_orientation",
            "model_projection_orientation_arms",
            "model_mirror_choice_optimized_per_source",
            "experimental_glb_geometry_or_camera_fitted",
            "genuine_original_1994_3D_camera_or_joint_pose_recovered",
            "source_to_2026_GLb_pose_labels_verified",
            "model_painted_frame_equals_original_3D_anatomical_part",
            "owner_likeness_approved", "summary")}
    

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip",type=Path,required=True)
    parser.add_argument("--registration",type=Path,default=Path(
        "analysis/data/racer-original-mesen-twenty-live-2d-screen-registrations-20261103.json"))
    parser.add_argument("--real-glb-axis-report",type=Path,default=Path(
        "analysis/data/racer-original-vs-glb-painted-axis-coverage-20261101.json"))
    parser.add_argument("--verify-committed",type=Path)
    parser.add_argument("--out",type=Path,required=True)
    args = parser.parse_args()
    result = compare(args.source_zip,args.registration,args.real_glb_axis_report)
    if args.verify_committed and compact_receipt(result) != json.loads(
            args.verify_committed.read_text()):
        raise ValueError("recomputed original 40-source camera-orientation sensitivity changed")
    publish_text_once(args.out, json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "source_original_2d_observations":len(result["per_source"]),
        "projected_axis_orientation_sensitivity":result["summary"],
        "original_3d_camera_or_pose_recovered":False,
    },sort_keys=True))


if __name__ == "__main__":
    main()
