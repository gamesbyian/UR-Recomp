#!/usr/bin/env python3
"""One frozen source-4bpp palette-index relabel null after rigid 2D rotation.

Source indices are NOT 3D material identities or physically calibrated RGB.
Fit one shared relabelling on even original orientation indices 2..62;
score odd 1..63. All ROM frames are previously inspected, not blind data.
"""
from __future__ import annotations
import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from tools.art.no_replace_report import publish_text_once
from tools.art.audit_original_rom_fullsprite_rotation_null import (
    SCHEMA as WHOLE_SCHEMA, PHASES, ODD_ANGLES,
    ROM_SHA, SOURCE_SHA, rigid_rotation_indices, audit as whole_sprite_audit,
)
from tools.art.recover_original_mesen24_rom_pose_ids import (
    source_frame_tiles, render_original_primary_sprite64,
)

SCHEMA="UR-ART4K-ORIGINAL-ROM-ROTATED-2D-ONE-PALETTE-RELABEL-NULL/1"
EVEN_TRAIN=tuple(range(2,64,2))
MODELS=("index_identity","one_global_majority_relabel","one_global_bijective_relabel")


def validate_4bpp(plane:bytes)->None:
    if type(plane) is not bytes or len(plane)!=4096 or any(x>15 for x in plane):
        raise ValueError("one authentic 64x64 source 4bpp indexed plane required")


def overlap_counts(actual:bytes,predicted:bytes,confusion:list[list[int]])->int:
    """Count only original and rotated-reference opaque pixels; never map alpha."""
    validate_4bpp(actual)
    validate_4bpp(predicted)
    if len(confusion)!=16 or any(len(row)!=16 for row in confusion):
        raise ValueError("16x16 source-index confusion matrix required")
    n=0
    for src,old in zip(actual,predicted):
        if src and old:
            confusion[old][src]+=1
            n+=1
    return n


def majority_map(matrix:list[list[int]])->tuple[int,...]:
    if len(matrix)!=16 or any(len(row)!=16 for row in matrix):
        raise ValueError("16x16 source confusion required")
    result=[0]
    for inp in range(1,16):
        if not sum(matrix[inp][1:]):
            result.append(inp)
        else:
            # Stable source identity prior on tied training support.
            result.append(max(range(1,16),key=lambda out:
                (matrix[inp][out], out==inp, -out)))
    return tuple(result)


def bijection_map(matrix:list[list[int]])->tuple[int,...]:
    """Exact maximum-weight index permutation, preserving 0 as transparency.

    15! brute force is unnecessary: 2^15 subset dynamic programming solves
    the globally optimal one-to-one assignment, with deterministic tie order.
    """
    if len(matrix)!=16 or any(len(row)!=16 or any(type(v) is not int or v<0 for v in row)
                              for row in matrix):
        raise ValueError("finite nonnegative integer 16x16 source confusion required")
    @lru_cache(maxsize=None)
    def optimize(used:int)->tuple[int,tuple[int,...]]:
        source_idx=used.bit_count()+1
        if source_idx==16:return (0,())
        best_score=-1
        best_assignment=()
        best_identity=-1
        for index in range(1,16):
            bit=1<<(index-1)
            if used&bit:continue
            future,tail=optimize(used|bit)
            candidate=matrix[source_idx][index]+future
            assignment=(index,)+tail
            identity=int(source_idx==index)+sum(
                source==mapped for source,mapped in
                zip(range(source_idx+1,16),tail))
            if (candidate>best_score or
                    (candidate==best_score and
                     (identity>best_identity or
                      (identity==best_identity and assignment<best_assignment)))):
                best_score,best_assignment,best_identity=candidate,assignment,identity
        return best_score,best_assignment
    result=(0,)+optimize(0)[1]
    if sorted(result)!=list(range(16)):
        raise ValueError("nonbijective source index assignment")
    return result


def metric(actual:bytes,predicted:bytes,mapping:tuple[int,...])->dict:
    validate_4bpp(actual)
    validate_4bpp(predicted)
    if len(mapping)!=16 or mapping[0]!=0 or any(
            type(x) is not int or not 0<=x<16 for x in mapping):
        raise ValueError("one shared 4bpp mapping with preserved transparency required")
    n_source=sum(x!=0 for x in actual)
    n_overlap=sum(a!=0 and b!=0 for a,b in zip(actual,predicted))
    matched=sum(a!=0 and b!=0 and a==mapping[b] for a,b in zip(actual,predicted))
    return {
        "source_opaque_pixels":n_source,
        "overlap_opaque_pixels":n_overlap,
        "exact_original_index_matches":matched,
        "source_opaque_exact_index_recall":round(matched/n_source,8) if n_source else 1.0,
        "within_overlap_exact_index_fraction":round(matched/n_overlap,8) if n_overlap else 1.0,
    }


def audit(rom:bytes,axis_raw:bytes)->dict:
    if hashlib.sha256(rom).hexdigest()!=ROM_SHA or hashlib.sha256(axis_raw).hexdigest()!=SOURCE_SHA:
        raise ValueError("wrong authenticated original USA ROM or source-axis SHA")
    base=whole_sprite_audit(rom,axis_raw)
    if base["schema"]!=WHOLE_SCHEMA or len(base["per_original_source_sprite"])!=128:
        raise ValueError("original 2D whole-sprite rotation null provenance invalid")
    cx,cy=base["source_fixed_pivot_source_pixels"]
    frames=source_frame_tiles(rom)
    confusion=[[0]*16 for _ in range(16)]
    training_pairs=0
    for phase in PHASES:
        reference=render_original_primary_sprite64(frames[phase*64])
        validate_4bpp(reference)
        for angle in EVEN_TRAIN:
            target=render_original_primary_sprite64(frames[phase*64+angle])
            rotated=rigid_rotation_indices(reference,angle,cx,cy)
            training_pairs+=overlap_counts(target,rotated,confusion)
    fitted={
        "index_identity":tuple(range(16)),
        "one_global_majority_relabel":majority_map(confusion),
        "one_global_bijective_relabel":bijection_map(confusion),
    }
    if set(fitted)!=set(MODELS):
        raise ValueError("missing frozen 2D palette null")
    sums={m:{"source_opaque_pixels":0,"overlap_opaque_pixels":0,
             "exact_original_index_matches":0} for m in MODELS}
    by_phase={}
    for phase in PHASES:
        reference=render_original_primary_sprite64(frames[phase*64])
        rows=[]
        for angle in ODD_ANGLES:
            target=render_original_primary_sprite64(frames[phase*64+angle])
            rotated=rigid_rotation_indices(reference,angle,cx,cy)
            per={key:metric(target,rotated,mapping) for key,mapping in fitted.items()}
            assert len({record["source_opaque_pixels"] for record in per.values()})==1
            rows.append({"original_phase_index":phase,
                         "original_orientation_index":angle,
                         "metrics":per})
            for name,record in per.items():
                for k in sums[name]:sums[name][k]+=record[k]
        by_phase[str(phase)]={
            name:round(sum(r["metrics"][name]["source_opaque_exact_index_recall"]
                           for r in rows)/len(rows),8)
            for name in MODELS}
    outcomes={}
    for name,counts in sums.items():
        source=counts["source_opaque_pixels"]
        overlap=counts["overlap_opaque_pixels"]
        outcome=dict(counts)
        outcome.update({
            "pooled_source_exact_index_recall":
                round(counts["exact_original_index_matches"]/source,8),
            "pooled_within_overlap_exact_fraction":
                round(counts["exact_original_index_matches"]/overlap,8),
        })
        outcomes[name]=outcome
    original=base["aggregate"]["one_pivot_2D_rigid_rotation"]
    if (outcomes["index_identity"]["exact_original_index_matches"]!=
            original["original_4bpp_exact_matching_opaque_pixels"] or
            outcomes["index_identity"]["source_opaque_pixels"]!=
            original["source_opaque_alpha_intersection"]+
            original["source_opaque_alpha_false_negative"]):
        raise ValueError("this null changed the earlier 128-original-sprite 2D baseline")
    return {
        "schema":SCHEMA,
        "source_USA_ROM_sha256":ROM_SHA,
        "original_axis_report_sha256":SOURCE_SHA,
        "original_source_fixed_2D_rotation_pivot_xy":[cx,cy],
        "source_pixel_aspect_display":[7,6],
        "training_original_orientation_indices":list(EVEN_TRAIN),
        "scored_original_orientation_indices":list(ODD_ANGLES),
        "original_source_phase_indices":list(PHASES),
        "training_pixel_pairs_in_opaque_overlap":training_pairs,
        "source_palette_index_0_reserved_for_transparency":True,
        "global_mapping_shared_across_all_phases_and_angles":True,
        "already_inspected_ROM_states_not_prospective_holdout":True,
        "physical_source_3D_mesh_camera_lights_or_materials_recovered":False,
        "source_owner_art_approval":False,
        "candidate_index_mappings":{name:list(v) for name,v in fitted.items()},
        "source_train_index_confusion":confusion,
        "pooled_original_odd_orientation_results":outcomes,
        "mean_original_odd_index_recall_by_phase":by_phase,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom",type=Path,required=True)
    p.add_argument("--original-axis-report",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=audit(a.rom.read_bytes(),a.original_axis_report.read_bytes())
    publish_text_once(a.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("ART4K_SOURCE_ROTATED_2D_INDEX_RELABEL_NULL",
          json.dumps(result["pooled_original_odd_orientation_results"],sort_keys=True))


if __name__=="__main__":
    main()
