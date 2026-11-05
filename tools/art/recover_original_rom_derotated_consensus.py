#!/usr/bin/env python3
"""Fixed-rotation inverse-source 2D consensus from original 24x64 ROM sprites.

Produces an uncertainty-aware canonical 64x64 image-space source silhouette
and indexed-colour plurality across existing original ROM orientation states.
Not a recovered historical 1994 3D mesh, 3D camera, joint or material.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from tools.art.no_replace_report import publish_text_once
from tools.art.audit_original_rom_fullsprite_rotation_null import (
    ROM_SHA, SOURCE_SHA, PHASES, rigid_rotation_indices,
)
from tools.art.recover_original_mesen24_rom_pose_ids import (
    source_frame_tiles, render_original_primary_sprite64,
)

SCHEMA="UR-ART4K-ORIGINAL-ROM-2D-DEROTATED-CONSENSUS-64x24/1"
N=4096
ANGLES=tuple(range(64))
BANDS=(("upper_y0_14",0,14),("middle_y15_26",15,26),
       ("lower_y27_63",27,63))
MIN_VALID_ORIENTATIONS=32
FROZEN_EVEN_ORIENTATION_PIVOT=(31.515625,19.578125)


def even_source_pivot(source:dict)->tuple[float,float]:
    box=source.get("source_phase_variation_bbox_by_ROM_angle_index")
    if not isinstance(box,dict) or set(box)!={str(a) for a in ANGLES}:
        raise ValueError("complete SHA-authenticated 64-orientation axis report required")
    centres=[]
    for a in range(0,64,2):
        b=box[str(a)]
        if (type(b) is not list or len(b)!=4 or
                any(type(v) is not int for v in b) or
                not 0<=b[0]<=b[2]<64 or not 0<=b[1]<=b[3]<64):
            raise ValueError("malformed original region support bounding box")
        centres.append(((b[0]+b[2])/2,(b[1]+b[3])/2))
    return (sum(x for x,_ in centres)/32,
            sum(y for _,y in centres)/32)


def consensus(derotated:list[bytes],validity:list[bytes])->dict:
    """Denominator excludes rotation-induced cropped source canvas positions."""
    if (type(derotated) is not list or type(validity) is not list or
            len(derotated)!=len(validity) or not 1<=len(derotated)<=64 or
            any(type(p) is not bytes or len(p)!=N or any(v>15 for v in p)
                for p in derotated) or
            any(type(p) is not bytes or len(p)!=N or set(p)-{0,1}
                for p in validity)):
        raise ValueError("matched genuine 64x64 indexed planes and 2D valid-sample masks required")
    votes=[[0]*16 for _ in range(N)]
    seen=[0]*N
    for original,valid in zip(derotated,validity):
        for k,(index,sampled) in enumerate(zip(original,valid)):
            if sampled:
                votes[k][index]+=1
                seen[k]+=1
    present=[n-votes[k][0] for k,n in enumerate(seen)]
    accepted=[seen[k]>=MIN_VALID_ORIENTATIONS for k in range(N)]
    core=bytes(int(accepted[k] and 10*present[k]>=9*seen[k]
                   and present[k]>0) for k in range(N))
    fringe=bytes(int(accepted[k] and present[k]>0 and
                 10*present[k]<9*seen[k] and
                 10*present[k]>seen[k]) for k in range(N))
    silhouette=bytes(int(accepted[k] and present[k]*2>seen[k]) for k in range(N))
    plurality=bytes(
        min((i for i in range(1,16)),
            key=lambda i:(-votes[k][i],i)) if silhouette[k] else 0
        for k in range(N))
    bands={}
    for name,y0,y1 in BANDS:
        pos=range(y0*64,(y1+1)*64)
        bands[name]={
            "source_valid_view_coverage_pixels":sum(accepted[k] for k in pos),
            "source_near_invariant_opaque_core_pixels":sum(core[k] for k in pos),
            "source_consensus_opaque_pixels":sum(silhouette[k] for k in pos),
            "source_mid_frequency_view_dependent_pixels":sum(fringe[k] for k in pos),
            "original_convention_source_index_plurality_sha256":
                hashlib.sha256(bytes(plurality[k] for k in pos)).hexdigest(),
        }
    return {
        "orientation_samples":len(derotated),
        "source_min_valid_view_count":MIN_VALID_ORIENTATIONS,
        "source_valid_coverage_pixels":sum(accepted),
        "source_near_invariant_opaque_core_pixels":sum(core),
        "source_consensus_opaque_pixels":sum(silhouette),
        "source_mid_frequency_view_dependent_pixels":sum(fringe),
        "source_consensus_binary_sha256":hashlib.sha256(silhouette).hexdigest(),
        "source_core_binary_sha256":hashlib.sha256(core).hexdigest(),
        "source_plurality_original_4bpp_sha256":hashlib.sha256(plurality).hexdigest(),
        "source_consensus_index4_64rows":[
            "".join(f"{v:x}" for v in plurality[y*64:(y+1)*64]) for y in range(64)],
        "source_valid_orientation_observation_count_64":seen,
        "source_opaque_observation_count_64":present,
        "per_fixed_source_image_y_band":bands,
    }


def analyze(rom:bytes,axis_raw:bytes)->dict:
    if (type(rom) is not bytes or hashlib.sha256(rom).hexdigest()!=ROM_SHA or
            type(axis_raw) is not bytes or
            hashlib.sha256(axis_raw).hexdigest()!=SOURCE_SHA):
        raise ValueError("wrong authenticated original ROM or original axis evidence SHA")
    axis=json.loads(axis_raw)
    if (axis.get("original_ROM_24phase_64angle_exact_source_frame_count")!=1536 or
            axis.get("original_1994_3d_angle_camera_mesh_material_or_bone_mapping_recovered") is not False):
        raise ValueError("original 24x64 ROM source identification invalid")
    pivot=even_source_pivot(axis)
    if pivot!=FROZEN_EVEN_ORIENTATION_PIVOT:
        raise ValueError("original even-only orientation pivot differs from frozen source receipt")
    grid=source_frame_tiles(rom)
    if len(grid)!=1536:
        raise ValueError("original 24 phase x 64 source orientation grid incomplete")
    valid=[rigid_rotation_indices(bytes([1])*N,(-a)%64,*pivot)
           for a in ANGLES]
    report={}
    for phase in PHASES:
        frames=[render_original_primary_sprite64(grid[phase*64+a]) for a in ANGLES]
        source_de_rotated=[
            rigid_rotation_indices(p,(-a)%64,*pivot)
            for a,p in enumerate(frames)]
        summary=consensus(source_de_rotated,valid)
        summary["original_ROM_phase_index"]=phase
        summary["original_orientation_zero_source_plane_sha256"]=hashlib.sha256(frames[0]).hexdigest()
        report[str(phase)]=summary
    return {
        "schema":SCHEMA,
        "original_ROM_USA_sha256":ROM_SHA,
        "original_24x64_source_report_sha256":SOURCE_SHA,
        "original_grid_dimensions":[24,64],
        "original_phase_indices_examined":list(PHASES),
        "original_orientation_indices_examined":list(ANGLES),
        "source_even_index_only_frozen_2D_rotation_pivot_xy":list(pivot),
        "original_SNES_pixel_display_aspect_ratio":"7:6",
        "original_index_plane_is_4bpp_not_3D_material_identity":True,
        "inverse_2D_index_rotation_unvalidated_as_1994_physical_degrees":True,
        "source_64x64_rotation_canvas_cropping_not_counted_as_background":True,
        "already_inspected_original_ROM_source_states_not_blind":True,
        "original_1994_3D_geometry_camera_joint_or_materials_recovered":False,
        "owner_art_likeness_approved":False,
        "per_original_ROM_phase":report,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom",required=True,type=Path)
    p.add_argument("--axis-report",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    record=analyze(a.rom.read_bytes(),a.axis_report.read_bytes())
    publish_text_once(a.out,json.dumps(record,indent=2,sort_keys=True)+"\n")
    print("OK ART4K_ORIGINAL_ROM_DEROTATED_CONSENSUS",
          json.dumps({k:{x:v[x] for x in (
              "source_near_invariant_opaque_core_pixels",
              "source_consensus_opaque_pixels",
              "source_mid_frequency_view_dependent_pixels")}
              for k,v in record["per_original_ROM_phase"].items()},sort_keys=True))


if __name__=="__main__":
    main()
