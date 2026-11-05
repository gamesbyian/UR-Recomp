#!/usr/bin/env python3
"""All 24 original ROM phase contours with 64 source orientations, once.

The 1994 ROM's 24 presentation indices are NOT identified as original
physical wheel/saddle degrees, and the 64 orientation indices are only a
previously tested 2D inverse screen-rotation hypothesis. This is 2D source
geometry, independent of the single unapproved 2026 GLB.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from tools.art.no_replace_report import publish_text_once
from tools.art.recover_original_rom_derotated_consensus import (
    ROM_SHA,SOURCE_SHA,N,ANGLES,BANDS,MIN_VALID_ORIENTATIONS,
    FROZEN_EVEN_ORIENTATION_PIVOT,even_source_pivot,consensus,
)
from tools.art.audit_original_rom_fullsprite_rotation_null import rigid_rotation_indices
from tools.art.recover_original_mesen24_rom_pose_ids import (
    source_frame_tiles,render_original_primary_sprite64,
)
from tools.art.analyze_original_rom_four_phase_contour_drift import _phase

SCHEMA="UR-ART4K-ORIGINAL-ROM-ALL24-2D-CONSENSUS-PHASE-DRIFT/1"
PHASES=tuple(range(24))
FROZEN_FOUR=(0,6,12,18)


def summarize(phase_records:dict[int,dict])->dict:
    if (not isinstance(phase_records,dict) or set(phase_records)!=set(PHASES)):
        raise ValueError("exactly all 24 original ROM phase consensus records required")
    decoded={n:_phase(phase_records[n]) for n in PHASES}
    # All phases must be measured on exactly the same fixed original 64-view
    # inverse-sampled source canvas; that canvas is independent of art phase.
    valid=decoded[0]["accepted"]
    if any(decoded[n]["accepted"]!=valid for n in PHASES[1:]):
        raise ValueError("original ROM phase cannot change orientation sample validity")
    common=sum(valid)
    if common<2048:
        raise ValueError("insufficient valid source orientation canvas pixels")
    all_alpha=bytes(int(valid[i] and all(decoded[n]["consensus"][i] for n in PHASES))
                    for i in range(N))
    ever_alpha=bytes(int(valid[i] and any(decoded[n]["consensus"][i] for n in PHASES))
                     for i in range(N))
    all_core=bytes(int(valid[i] and all(decoded[n]["core"][i] for n in PHASES))
                   for i in range(N))
    varying=bytes(int(ever_alpha[i] and not all_alpha[i]) for i in range(N))
    per_band={}
    for name,lo,hi in BANDS:
        idx=range(lo*64,(hi+1)*64)
        per_band[name]={
            "source_common_valid_observed_2D_positions":sum(valid[i] for i in idx),
            "source_all24_always_consensus_alpha_positions":sum(all_alpha[i] for i in idx),
            "source_all24_ever_consensus_alpha_positions":sum(ever_alpha[i] for i in idx),
            "source_all24_phase_variable_2D_alpha_positions":sum(varying[i] for i in idx),
            "source_all24_always_near_invariant_opaque_core_positions":sum(
                all_core[i] for i in idx),
        }
    if any(sum(v[f"source_all24_{key}"] for v in per_band.values())!=total
           for key,total in (
               ("always_consensus_alpha_positions",sum(all_alpha)),
               ("ever_consensus_alpha_positions",sum(ever_alpha)),
               ("phase_variable_2D_alpha_positions",sum(varying)),
               ("always_near_invariant_opaque_core_positions",sum(all_core)))):
        raise ValueError("source original all24 phase fixed y bands do not conserve alpha")
    # Preserve the already independently qualified original four phases
    # exactly, so the 24-phase extension cannot quietly contradict #3151.
    four_all=bytes(int(valid[i] and all(decoded[n]["consensus"][i] for n in FROZEN_FOUR))
                   for i in range(N))
    four_any=bytes(int(valid[i] and any(decoded[n]["consensus"][i] for n in FROZEN_FOUR))
                   for i in range(N))
    four_core=bytes(int(valid[i] and all(decoded[n]["core"][i] for n in FROZEN_FOUR))
                    for i in range(N))
    four_vary=sum(int(four_any[i] and not four_all[i]) for i in range(N))
    # Actual 1994 source numerical golden from GHA #41990764973.
    if (sum(valid),sum(four_all),sum(four_any),sum(four_core),four_vary)!=(
            3008,291,304,164,13):
        raise ValueError("source four-phase original-ROM contour golden changed")
    adjacent={}
    for phase in PHASES:
        nxt=(phase+1)%24
        before,after=decoded[phase],decoded[nxt]
        tp=sum(int(valid[i] and before["consensus"][i] and
                   after["consensus"][i]) for i in range(N))
        fp=sum(int(valid[i] and not before["consensus"][i] and
                   after["consensus"][i]) for i in range(N))
        fn=sum(int(valid[i] and before["consensus"][i] and
                   not after["consensus"][i]) for i in range(N))
        paint=sum(int(valid[i] and before["consensus"][i] and
                      after["consensus"][i] and
                      before["index"][i]==after["index"][i])
                  for i in range(N))
        per_pair_band={}
        for name,lo,hi in BANDS:
            idx=range(lo*64,(hi+1)*64)
            per_pair_band[name]={
                "phase_index_alpha_changes":sum(
                    int(valid[i] and before["consensus"][i]!=after["consensus"][i])
                    for i in idx),
                "original_phase_shared_opaque_2D_pixels":sum(
                    int(valid[i] and before["consensus"][i] and after["consensus"][i])
                    for i in idx),
            }
        if (sum(x["phase_index_alpha_changes"] for x in per_pair_band.values())!=fp+fn
                or sum(x["original_phase_shared_opaque_2D_pixels"]
                       for x in per_pair_band.values())!=tp):
            raise ValueError("original source phase-neighbor 2D alpha census not conserved")
        d=tp+fp+fn
        adjacent[f"{phase}->{nxt}"]={
            "original_ROM_index_neighbors_not_actual_Mesen_PPU_time":True,
            "source_alpha_tp_fp_fn":{"tp":tp,"fp":fp,"fn":fn},
            "source_original_2D_consensus_alpha_iou":round(tp/d,8) if d else 1.,
            "source_4bpp_exact_index_recall_on_shared_opaque":
                round(paint/tp,8) if tp else 1.,
            "fixed_image_y_bands":per_pair_band,
        }
    return {
        "source_original_common_valid_2D_positions":common,
        "source_all24_always_consensus_alpha_positions":sum(all_alpha),
        "source_all24_ever_consensus_alpha_positions":sum(ever_alpha),
        "source_all24_phase_variable_2D_alpha_positions":sum(varying),
        "source_all24_always_near_invariant_opaque_core_positions":sum(all_core),
        "source_original_four_phase_golden_preserved":[
            sum(four_all),sum(four_any),sum(four_core),four_vary],
        "per_fixed_source_image_y_band":per_band,
        "all_original_24_ROM_phase_index_neighbor_pairs":adjacent,
        "per_original_ROM_phase":{
            str(n):{
                "source_consensus_binary_sha256":
                    phase_records[n]["source_consensus_binary_sha256"],
                "source_2D_consensus_opaque_pixels":
                    phase_records[n]["source_consensus_opaque_pixels"],
                "source_2D_near_invariant_opaque_core_pixels":
                    phase_records[n]["source_near_invariant_opaque_core_pixels"],
                "original_index4_plurality_sha256":
                    phase_records[n]["source_plurality_original_4bpp_sha256"],
            }
            for n in PHASES
        },
    }


def analyze(rom:bytes,axis_raw:bytes)->dict:
    if (type(rom) is not bytes or len(rom)!=2097152 or
            hashlib.sha256(rom).hexdigest()!=ROM_SHA or
            type(axis_raw) is not bytes or
            hashlib.sha256(axis_raw).hexdigest()!=SOURCE_SHA):
        raise ValueError("actual SHA-pinned original USA ROM and 24x64 axis report required")
    axis=json.loads(axis_raw)
    if (axis.get("original_ROM_24phase_64angle_exact_source_frame_count")!=1536 or
            even_source_pivot(axis)!=FROZEN_EVEN_ORIENTATION_PIVOT or
            axis.get("original_1994_3d_angle_camera_mesh_material_or_bone_mapping_recovered") is not False):
        raise ValueError("original source 24x64 image-space evidence changed")
    grid=source_frame_tiles(rom)
    if len(grid)!=1536:
        raise ValueError("original ROM 24x64 packed tile lookup incomplete")
    pivot=FROZEN_EVEN_ORIENTATION_PIVOT
    # Same sampled source canvas for every phase, never per-image fitted.
    validity=[rigid_rotation_indices(bytes([1])*N,(-a)%64,*pivot)
              for a in ANGLES]
    records={}
    for phase in PHASES:
        images=[render_original_primary_sprite64(grid[phase*64+a])
                for a in ANGLES]
        de_rotated=[rigid_rotation_indices(p,(-a)%64,*pivot)
                    for a,p in enumerate(images)]
        records[phase]=consensus(de_rotated,validity)
    reduced=summarize(records)
    return {
        "schema":SCHEMA,
        "original_ROM_USA_sha256":ROM_SHA,
        "source_original_24x64_axis_SHA256":SOURCE_SHA,
        "source_exact_original_sprite_states_analyzed":1536,
        "source_2D_inverse_rotation_pivot_xy":list(pivot),
        "source_24_phase_indices_analyzed":list(PHASES),
        "source_all_64_orientation_indices_analyzed":True,
        "source_all_24_phase_paint_not_recovered_3D_materials":True,
        "source_24_ROM_index_neighbors_not_actual_PPU_timing":True,
        "source_previously_inspected_original_ROM_not_blind_holdout":True,
        "original_1994_3D_mesh_camera_joint_physical_angles_recovered":False,
        "owner_art_likeness_approved":False,
        **reduced,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom",type=Path,required=True)
    p.add_argument("--axis-report",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=analyze(a.rom.read_bytes(),a.axis_report.read_bytes())
    publish_text_once(a.out,json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("OK ART4K_ORIGINAL_ROM_ALL24_PHASE_2D_CONTOUR",
          json.dumps({
              "source_valid":result["source_original_common_valid_2D_positions"],
              "always":result["source_all24_always_consensus_alpha_positions"],
              "ever":result["source_all24_ever_consensus_alpha_positions"],
              "varying":result["source_all24_phase_variable_2D_alpha_positions"],
              "core":result["source_all24_always_near_invariant_opaque_core_positions"],
              "varying_by_y_band":{
                  k:v["source_all24_phase_variable_2D_alpha_positions"]
                  for k,v in result["per_fixed_source_image_y_band"].items()},
              "phase_neighbor_alpha_iou":{
                  k:v["source_original_2D_consensus_alpha_iou"]
                  for k,v in result["all_original_24_ROM_phase_index_neighbor_pairs"].items()},
          },sort_keys=True))


if __name__=="__main__":
    main()
