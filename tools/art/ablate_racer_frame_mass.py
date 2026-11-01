#!/usr/bin/env python3
"""Bounded offline source-verified frame-mass ablation for EXISTING #2832 SCAD.

No new unicycle rig, original 1994 3D pose pairing, source image redistribution,
GLB approval or runtime change. This compares one shared upright source-model
shape against 10 unique original 2D silhouettes, using original source anchors.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

try:
    from tools.art.build_racer_source_pixel_corpus import build, ROOT, REGISTRY
    from tools.art.build_real_viewer_pose_matrix import (
        original_registered_contacts, original_lowest_alpha_anchor,
        translated_binary_mask,
    )
    from tools.art.racer_source_pixels import alpha_metrics, decode_rgba_png
    from tools.art.render_racer_glb_projection import render_mask, camera_config, np, trimesh
    from tools.art.score_racer_candidate import score
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from build_racer_source_pixel_corpus import build, ROOT, REGISTRY
    from build_real_viewer_pose_matrix import (
        original_registered_contacts, original_lowest_alpha_anchor,
        translated_binary_mask,
    )
    from racer_source_pixels import alpha_metrics, decode_rgba_png
    from render_racer_glb_projection import render_mask, camera_config, np, trimesh
    from score_racer_candidate import score
    from no_replace_report import publish_text_once

SCHEMA = "UR-RACER-SOURCE-FRAME-MASS-ABLATION/1"
CAMERA = ROOT / "analysis/data/racer-inverse-side-provisional-1205.json"
CANONICAL_SOURCE_SHA = "e99ef45bfe72f09ee97f51b7d7449c501aee2ca2d93596106ede4b56caddc984"
PART_CALLS = {
    "tire": "tire();",
    "rim_and_hub": "rim_and_hub();",
    "pedals": "pedals(18);",
    "saddle": "saddle(0);",
    "fork_and_frame": "fork_and_frame();",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_masses(values: list[float]) -> list[float]:
    if not values or len(values) > 16:
        raise ValueError("a bounded set of 1..16 frame masses is required")
    answer = []
    for value in values:
        if type(value) not in (float,int) or not math.isfinite(value) or not 1 <= value <= 2:
            raise ValueError("existing source frame_mass must lie in [1,2]")
        if value in answer:
            raise ValueError("duplicate frame mass would multiply the study")
        answer.append(float(value))
    if 1.0 not in answer:
        raise ValueError("include original unmodified 1.0 blockout as a control")
    return answer


def validate_scores(rows: list[dict], source_count: int) -> dict:
    if len(rows) != source_count or len({x.get("source_binary_mask_sha256") for x in rows}) != source_count:
        raise ValueError("every original binary source shape gets exactly one vote")
    ious, contours = [], []
    by_player = defaultdict(list)
    for row in rows:
        iou, contour = row.get("mask_iou"), row.get("boundary_chamfer_mean_physical_px")
        if (type(iou) not in (int,float) or not math.isfinite(iou) or not 0 <= iou <= 1 or
                type(contour) not in (int,float) or not math.isfinite(contour) or not 0 <= contour <= 100):
            raise ValueError("invalid original source IoU or Chamfer score")
        players = row.get("player_set")
        if not isinstance(players, list) or not players or not set(players).issubset({"p1","p2"}):
            raise ValueError("source shape lacks player provenance")
        ious.append(iou)
        contours.append(contour)
        for player in set(players):
            by_player[player].append({"iou":iou,"contour":contour})
    return {
        "equal_original_binary_mask_weight_mean_iou": round(sum(ious)/len(ious),8),
        "equal_original_binary_mask_weight_mean_chamfer_physical_px": round(
            sum(contours)/len(contours),8),
        "mean_by_original_player_group": {
            p:{
                "unique_source_shape_count":len(v),
                "mean_mask_iou":round(sum(x["iou"] for x in v)/len(v),8),
                "mean_chamfer_physical_px":round(sum(x["contour"] for x in v)/len(v),8),
            }
            for p,v in sorted(by_player.items())
        },
    }


def source_masks() -> tuple[dict, dict]:
    corpus=build()
    contacts=original_registered_contacts(REGISTRY,corpus["source_registry_current_sha256"])
    shapes={}
    for row in corpus["observations"]:
        path=ROOT/row["source_image"]
        w,h,pixels,png_sha=decode_rgba_png(path)
        if (w,h)!=(64,64) or png_sha != row["png_file_sha256"]:
            raise ValueError("original retained PNG changed")
        metrics=alpha_metrics(pixels,w,h)
        if metrics["source_rgba_sha256"]!=row["source_rgba_sha256"]:
            raise ValueError("original ROM-composition image hash mismatch")
        mask=bytes(int(x>0) for x in pixels[3::4])
        binary_sha=sha(mask)
        registered=contacts.get(row["representation_id"])
        if (registered is None or registered[0] != row["player"] or
                original_lowest_alpha_anchor(mask) != registered[1]):
            raise ValueError("original registered contact disagrees with source pixels")
        if binary_sha not in shapes:
            shapes[binary_sha]={
                "source_binary_mask_sha256":binary_sha,
                "mask":mask,
                "contact_x2_y2":list(registered[1]),
                "player_set":set(),
            }
        group=shapes[binary_sha]
        if group["mask"]!=mask or group["contact_x2_y2"]!=list(registered[1]):
            raise ValueError("same original binary mask has conflicting source geometry")
        group["player_set"].add(row["player"])
    if len(shapes)!=10:
        raise ValueError("first original family must contain 10 source masks")
    for value in shapes.values():
        value["player_set"]=sorted(value["player_set"])
    return shapes, corpus


def source_prefix(scad: bytes, required_sha: str) -> str:
    if sha(scad)!=required_sha:
        raise ValueError("SCAD file differs from the declared original model SHA")
    decoded=scad.decode("utf-8")
    terminal="rig(rig_pose);\n"
    if not decoded.endswith(terminal) or "rig_frame_mass=" not in decoded:
        raise ValueError("unknown SCAD rig entrypoint/parameter; refuse guessed model export")
    return decoded[:-len(terminal)]


def export_part(prefix: str, part: str, mass: float,
                folder: Path, openscad: str):
    if part not in PART_CALLS:
        raise ValueError("unknown original source rig part")
    target=folder/(part+"-"+str(mass).replace(".","_"))
    scad=target.with_suffix(".scad")
    stl=target.with_suffix(".stl")
    scad.write_text(prefix+"\ntranslate([0,0,1]) "+PART_CALLS[part]+"\n",encoding="utf-8")
    cmd=[openscad,"-D",f"rig_frame_mass={mass:g}","-o",str(stl),str(scad)]
    result=subprocess.run(cmd,text=True,capture_output=True,timeout=120,check=False)
    if result.returncode or not stl.is_file():
        raise RuntimeError("OpenSCAD failed for "+part+":"+str(mass)+" "+result.stderr[-200:])
    mesh=trimesh.load_mesh(stl,process=False)
    if (len(mesh.faces)<1 or not np.isfinite(mesh.vertices).all()):
        raise ValueError("invalid source-authored STL output")
    return mesh,sha(stl.read_bytes()),len(mesh.faces)


def validate_frame_tire_overlap(volume: float, faces: int, components: int,
                                watertight: bool, winding: bool,
                                stl_sha256: str) -> dict:
    """Require an actual closed CSG solid before reporting 3D interference.

    This is OpenSCAD's exact fork_AND_tire Boolean solid, not a 2D silhouette
    overlap. It can contain multiple disconnected solids. It is not a
    statement that the 1994 model had the same mechanical constraints.
    """
    if (type(volume) not in (float, int) or not math.isfinite(volume) or volume <= 0 or
            type(faces) is not int or faces < 4 or
            type(components) is not int or components < 1 or
            watertight is not True or winding is not True or
            not isinstance(stl_sha256, str) or len(stl_sha256) != 64 or
            any(c not in "0123456789abcdef" for c in stl_sha256)):
        raise ValueError("invalid/non-watertight source-authored fork-tire CSG intersection")
    return {
        "fork_tire_intersection_csg_volume_model_units_cubed": round(volume, 12),
        "fork_tire_intersection_csg_watertight": True,
        "fork_tire_intersection_csg_winding_consistent": True,
        "fork_tire_intersection_connected_components": components,
        "fork_tire_intersection_triangle_count": faces,
        "fork_tire_intersection_stl_sha256": stl_sha256,
        "fork_tire_intersection_is_mechanical_art_approval": False,
    }


def export_fork_tire_csg(prefix: str, mass: float,
                         folder: Path, openscad: str) -> dict:
    """Optional exact CSG test of source fork volume intersecting source tire.

    Uses the *same* original SCAD modules and mass parameter as silhouette
    ablation. A mesh-processing boolean approximation is NOT substituted.
    """
    target = folder / ("fork-tire-CSG-" + str(mass).replace(".", "_"))
    script = target.with_suffix(".scad")
    stl = target.with_suffix(".stl")
    script.write_text(prefix + "\n" +
                      "intersection(){ translate([0,0,1]) fork_and_frame(); "
                      "translate([0,0,1]) tire(); }\n", encoding="utf-8")
    done = subprocess.run(
        [openscad, "-D", f"rig_frame_mass={mass:g}",
         "-o", str(stl), str(script)],
        text=True, capture_output=True, timeout=120, check=False
    )
    if done.returncode:
        raise RuntimeError("source fork/tire OpenSCAD CSG failed: " + done.stderr[-200:])
    if not stl.is_file():
        # A genuinely collision-free future model has ZERO intersection.
        # OpenSCAD 2021.01 reports this explicitly without writing an STL.
        # Distinguish that result from an absent/failed/corrupted export.
        if "Current top level object is empty." not in done.stderr:
            raise RuntimeError("source fork/tire CSG output absent without explicit empty proof")
        return {
            "fork_tire_intersection_csg_volume_model_units_cubed": 0.0,
            "fork_tire_intersection_csg_watertight": None,
            "fork_tire_intersection_csg_winding_consistent": None,
            "fork_tire_intersection_connected_components": 0,
            "fork_tire_intersection_triangle_count": 0,
            "fork_tire_intersection_stl_sha256": None,
            "fork_tire_csg_empty_proven_by_openscad": True,
            "fork_tire_intersection_is_mechanical_art_approval": False,
        }
    raw = stl.read_bytes()
    mesh = trimesh.load_mesh(stl, process=True)
    return validate_frame_tire_overlap(
        float(mesh.volume), int(len(mesh.faces)),
        len(mesh.split(only_watertight=False)),
        bool(mesh.is_watertight), bool(mesh.is_winding_consistent),
        sha(raw),
    )


def study(scad_path: Path, source_sha: str, camera_path: Path,
          mass_values: list[float], *, measure_frame_tire_csg: bool = False) -> dict:
    if np is None or trimesh is None:
        raise RuntimeError("offline source model ablation requires NumPy and Trimesh")
    masses=checked_masses(mass_values)
    source_bytes=scad_path.read_bytes()
    prefix=source_prefix(source_bytes, source_sha)
    camera_bytes=camera_path.read_bytes()
    camera=json.loads(camera_bytes)
    camera_config(camera)
    witness=camera.get("source_witness",{})
    if (camera.get("camera_calibration_status") != "provisional" or
            (witness.get("player"),witness.get("guest_frame")) != ("p1",1205) or
            camera.get("source_anchor_x2_y2") != [67,76]):
        raise ValueError("only explicit provisional P1 source witness camera is supported")
    openscad=shutil.which("openscad")
    if not openscad:
        raise RuntimeError("OpenSCAD executable is required for exact source geometry")
    shapes,corpus=source_masks()
    rows=[]
    with tempfile.TemporaryDirectory(prefix="ur-frame-mass-ablation-") as temporary:
        folder=Path(temporary)
        fixed_parts={}
        for part in ("tire","rim_and_hub","pedals","saddle"):
            fixed_parts[part]=export_part(prefix,part,1.0,folder,openscad)
        for mass in masses:
            fork=export_part(prefix,"fork_and_frame",mass,folder,openscad)
            geometry=trimesh.util.concatenate([fixed_parts[p][0] for p in
                 ("tire","rim_and_hub","pedals","saddle")]+[fork[0]])
            projected=render_mask(geometry.vertices,geometry.faces,camera)
            mask=bytes(int(v) for v in projected[2::4,2::4].reshape(-1))
            if len(mask)!=4096 or not any(mask):
                raise ValueError("source candidate projected alpha mask invalid")
            scored=[]
            for group in shapes.values():
                registered=group["contact_x2_y2"]
                delta=(registered[0]-67,registered[1]-76)
                if any(x%2 for x in delta):
                    raise ValueError("half-pixel contact requires direct 4x rerender")
                placed=translated_binary_mask(mask,delta[0]//2,delta[1]//2)
                metric=score(group["mask"],placed)
                scored.append({
                    "source_binary_mask_sha256":group["source_binary_mask_sha256"],
                    "player_set":group["player_set"],
                    "source_registered_contact_x2_y2":registered,
                    "mask_iou":metric["mask_iou"],
                    "boundary_chamfer_mean_physical_px":metric[
                        "boundary_chamfer_mean_physical_px"],
                })
            overlap = (export_fork_tire_csg(prefix, mass, folder, openscad)
                       if measure_frame_tire_csg else None)
            rows.append({
                "rig_frame_mass":mass,
                **({"fork_tire_csg": overlap} if overlap is not None else {}),
                "candidate_fork_source_stl_sha256":fork[1],
                "candidate_fork_triangle_count":fork[2],
                "whole_model_triangle_count":len(geometry.faces),
                "source_registered_candidate_logical_mask_sha256":sha(mask),
                "source_shape_scores":scored,
                **validate_scores(scored,10),
            })
    control=next(row for row in rows if row["rig_frame_mass"]==1.0)
    if measure_frame_tire_csg:
        baseline=control["fork_tire_csg"]["fork_tire_intersection_csg_volume_model_units_cubed"]
        for row in rows:
            volume=row["fork_tire_csg"]["fork_tire_intersection_csg_volume_model_units_cubed"]
            # Ratios to a zero-overlap baseline have no finite interpretation.
            # Preserve absolute CSG volume and explicitly mark undefined ratios.
            row["fork_tire_csg"]["volume_ratio_to_unmodified_1_0_rig"] = (
                round(volume/baseline,6) if baseline > 0 else None)
            row["fork_tire_csg"]["unmodified_baseline_csg_intersection_is_zero"] = baseline == 0
    if (source_sha==CANONICAL_SOURCE_SHA and
            abs(control["equal_original_binary_mask_weight_mean_iou"]-0.57255469)>1e-7):
        raise ValueError("canonical 2026 model baseline failed independent 10-source verification")
    return {
        "schema":SCHEMA,
        "source_scad_sha256":source_sha,
        "source_registry_sha256":corpus["source_registry_current_sha256"],
        "source_rom_sha256":corpus["historical_manifest_declared_rom_sha256"],
        "source_camera_sha256":sha(camera_bytes),
        "camera_status":"provisional",
        "original_source_observations":32,
        "distinct_source_binary_masks":10,
        "study_pose":"original_source_2026_upright_blockout_only",
        "unpaired_shape_metric_without_original_pose_mapping":True,
        "one_shared_3d_source_geometry_parameter_per_trial":True,
        "tire_rim_pedals_saddle_source_modules_unchanged_across_trials":True,
        "all_original_2d_contact_offsets_from_registered_source":True,
        "distinct_animation_family_holdout_tested":False,
        "1994_source_3d_camera_recovered":False,
        "owner_likeness_approved":False,
        "shipping_art_approved":False,
        "model_files_modified":False,
        "optional_exact_frame_tire_csg_measured":measure_frame_tire_csg,
        "csg_overlap_is_original_1994_mechanical_contact_proof":False,
        "parameter_trials":rows,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-scad",required=True,type=Path)
    ap.add_argument("--source-scad-sha256",required=True)
    ap.add_argument("--camera",type=Path,default=CAMERA)
    ap.add_argument("--mass",type=float,action="append",help="repeat 1.0..2.0, include 1.0")
    ap.add_argument("--measure-frame-tire-csg", action="store_true",
                    help="opt-in exact OpenSCAD fork/tire 3D intersection (costly)")
    ap.add_argument("--out",required=True,type=Path,help="new immutable JSON, outside repository")
    args=ap.parse_args()
    if args.out.resolve().is_relative_to(ROOT.resolve()):
        ap.error("source research receipts must be outside public repository")
    report=study(args.source_scad,args.source_scad_sha256,args.camera,
                 args.mass or [1.0,1.2,1.4,1.6,2.0],
                 measure_frame_tire_csg=args.measure_frame_tire_csg)
    output=json.dumps(report,sort_keys=True,indent=2)+"\n"
    publish_text_once(args.out,output)
    print(json.dumps({
        "schema":report["schema"],"source_scad_sha256":report["source_scad_sha256"],
        "trial_count":len(report["parameter_trials"]),
        "output_sha256":sha(output.encode("utf-8")),
        "owner_likeness_approved":False,"shipping_art_approved":False
    },indent=2,sort_keys=True))


if __name__=="__main__":
    main()
