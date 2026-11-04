#!/usr/bin/env python3
"""Original Mesen 2P upper-event pixels versus authentic 2026 GLB parent coverage.

No original 1994 mesh part/material inference. Reuses original and GLB hashes,
single camera, tick1601 anchors, and exact 2026 root controllers.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import runpy

from tools.art.glb_parent_part_id_raster import PARTS,validated_camera
from tools.art.count_real_glb_parent_source_y_bands import (
    SOURCE_SCAD_SHA,SOURCE_Y_BANDS,project_real_parent_masks256,
)
from tools.art.score_original_mesen24_fixed_pivot_glb import (
    check_receipts,read_original_roles,anchor,registered_mask4,metric,
)
from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-AUTHENTIC-PPU-TO-REAL-2026-GLB-PARENT-OVERLAP/1"
# Real chronological upper-band event destinations; retrospectively examined.
TICKS={"blue":1603,"red":1606}
ARMS=("static_2026_3d","wheel_axle_root_only","historical_midbody_root_only")


def parent_overlap(source:bytes,parents:dict[str,bytes])->dict:
    if (type(source) is not bytes or len(source)!=4096 or set(source)-{0,1} or
            not isinstance(parents,dict) or set(parents)!=set(PARTS) or
            any(type(m) is not bytes or len(m)!=4096 or set(m)-{0,1}
                for m in parents.values())):
        raise ValueError("one exact original source and five real parent 64px masks required")
    union=bytes(int(any(m[k] for m in parents.values())) for k in range(4096))
    full=metric(source,union)
    bands={}
    for name,lo,hi in SOURCE_Y_BANDS:
        xy=range(lo*64,(hi+1)*64)
        multiplicity={k:sum(bool(m[k]) for m in parents.values()) for k in xy}
        counts={
            "original_opaque":sum(source[k] for k in xy),
            "candidate_union_opaque":sum(union[k] for k in xy),
            "tp":sum(bool(source[k] and union[k]) for k in xy),
            "fp":sum(bool(not source[k] and union[k]) for k in xy),
            "fn":sum(bool(source[k] and not union[k]) for k in xy),
            "nonexclusive_2026_projection_pixels":sum(n>1 for n in multiplicity.values()),
        }
        parts={}
        for part,mask in parents.items():
            parts[part]={
                "projected_model_opaque":sum(mask[k] for k in xy),
                "overlap_with_original_opaque":
                    sum(bool(mask[k] and source[k]) for k in xy),
                "model_only_opaque":sum(bool(mask[k] and not source[k]) for k in xy),
                "exclusive_model_opaque":
                    sum(bool(mask[k] and multiplicity[k]==1) for k in xy),
                "exclusive_model_original_overlap":
                    sum(bool(mask[k] and source[k] and multiplicity[k]==1) for k in xy),
            }
        if counts["original_opaque"]!=counts["tp"]+counts["fn"] or (
                counts["candidate_union_opaque"]!=counts["tp"]+counts["fp"]):
            raise ValueError("original/2026 alpha support not conserved")
        den=counts["tp"]+counts["fp"]+counts["fn"]
        bands[name]={**counts,"iou":round(counts["tp"]/den,8) if den else 1.,
                     "authored_2026_parent_projection":parts}
    for key in ("tp","fp","fn"):
        if sum(v[key] for v in bands.values())!=full[key]:
            raise ValueError("authored 2026 parent regions disagree with original source alpha")
    return {"whole_original_vs_2026_alpha":full,"source_y_regions":bands}


def audit(source_zip:bytes,pose_raw:bytes,axis_raw:bytes,
          camera_raw:bytes,exports:Path)->dict:
    import numpy as np
    import trimesh
    from tools.art.experimental_fixed_root_orbit import apply_root_scene
    from tools.art.render_racer_glb_projection import render_mask
    pose,_,camera=check_receipts(source_zip,pose_raw,axis_raw,camera_raw)
    validated_camera(camera)
    originals=read_original_roles(source_zip,pose)
    validate=runpy.run_path(str(Path(__file__).resolve().parent/
                                  "model-review/stage_pages.py"))["validate"]
    pointer,outputs=validate(exports,"upright")
    raw=outputs["glb"].read_bytes()
    if (pointer["source_sha256"]!=SOURCE_SCAD_SHA or
            pointer["glb_sha256"]!=hashlib.sha256(raw).hexdigest() or
            raw[:4]!=b"glTF"):
        raise ValueError("real 2026 GLB current-success source receipt changed")
    scene=trimesh.load(outputs["glb"],file_type="glb",force="scene",process=False)

    def project(angle:int,pivot:str):
        apply_root_scene(scene,angle,pivot,0.,0.)
        masks=project_real_parent_masks256(scene,camera)
        union=np.logical_or.reduce([masks[p] for p in PARTS])
        world=(scene.to_geometry() if callable(getattr(scene,"to_geometry",None))
               else scene.dump(concatenate=True))
        expected=render_mask(np.asarray(world.vertices),
                             np.asarray(world.faces),camera).astype(bool)
        if not np.array_equal(union,expected):
            raise ValueError("2026 GLB parent union disagrees with established whole renderer")
        return masks,union

    static,neutral=project(0,"wheel_axle")
    neutral_anchor=anchor(bytes(neutral[2::4,2::4].astype(np.uint8).ravel()))
    scores={}
    for role,tick in TICKS.items():
        original=originals[role][tick]
        a=original["angle"]
        placement=anchor(originals[role][1601]["alpha"])
        results={}
        for arm in ARMS:
            if arm=="static_2026_3d":masks,whole=static,neutral
            else:masks,whole=project(a,"wheel_axle" if
                arm=="wheel_axle_root_only" else "historical_midbody")
            registered={part:registered_mask4(mask,placement,neutral_anchor)
                        for part,mask in masks.items()}
            combined=bytes(int(any(m[k] for m in registered.values()))
                           for k in range(4096))
            if combined!=registered_mask4(whole,placement,neutral_anchor):
                raise ValueError("source-registered 2026 parts do not reconstruct whole alpha")
            results[arm]=parent_overlap(original["alpha"],registered)
        scores[role]={
            "original_Mesen_tick":tick,"source_ROM_orientation_index":a,
            "source_ROM_phase_index":original["phase"],
            "one_original_tick1601_anchor_x2y2":list(placement),
            "models":results}
    return {"schema":SCHEMA,
            "original_ROM_sha256":pose["original_usa_ROM_sha256"],
            "authentic_source_Mesen24_zip_sha256":
                pose["original_Mesen24_source_archive_sha256"],
            "original_pose_report_sha256":hashlib.sha256(pose_raw).hexdigest(),
            "original_source_axis_sha256":hashlib.sha256(axis_raw).hexdigest(),
            "original_camera_sha256":hashlib.sha256(camera_raw).hexdigest(),
            "actual_attempt_specific_2026_GLb_sha256":pointer["glb_sha256"],
            "model_2026_SCAD_source_sha256":SOURCE_SCAD_SHA,
            "source_image_frame_selection":TICKS,"preselected_model_arms":ARMS,
            "original_1994_3D_camera_geometry_or_parts_recovered":False,
            "original_sprites_are_held_OAM_local_not_screen_reflected":True,
            "source_2026_likeness_owner_approved":False,
            "previously_inspected_retrospective_source_not_blind":True,
            "2026_parent_pixels_overlap_so_part_counts_are_not_additive":True,
            "source_vs_model":scores}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--pose-report",type=Path,required=True)
    p.add_argument("--axis-report",type=Path,required=True)
    p.add_argument("--camera",type=Path,required=True)
    p.add_argument("--verified-exports",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    record=audit(a.source_zip.read_bytes(),a.pose_report.read_bytes(),
                 a.axis_report.read_bytes(),a.camera.read_bytes(),
                 a.verified_exports)
    publish_text_once(a.out,json.dumps(record,sort_keys=True,indent=2)+"\n")
    print("ART4K_REAL_ORIGINAL_PPU_GLB_PARENT_UPPER_RESIDUAL",
          json.dumps({role:{arm:{"full":row["whole_original_vs_2026_alpha"],
              "upper":row["source_y_regions"]["upper_y0_14"]}
              for arm,row in receipt["models"].items()}
              for role,receipt in record["source_vs_model"].items()},sort_keys=True))


if __name__=="__main__":main()
