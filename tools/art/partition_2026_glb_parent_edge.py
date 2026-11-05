"""Disjoint attribution of *visible* 2026 GLB union motion to authored parents.

Original 1994 source has no known matching parent labels. For candidate 2026
union XOR changes, attribute only uniquely visible parent pixels. Multiple
model parents at the changed pixel remain explicitly ambiguous (non-additive).
Opaque parent motion hidden by another opaque parent is not visible motion.
"""
from __future__ import annotations

from tools.art.glb_parent_part_id_raster import PARTS

SOURCE_Y_BANDS=(("upper_y0_14",0,14),("middle_y15_26",15,26),
                ("lower_y27_63",27,63))


def partition_2026_visible_motion(before:dict[str,bytes],after:dict[str,bytes])->dict:
    if (not isinstance(before,dict) or not isinstance(after,dict) or
            set(before)!=set(PARTS) or set(after)!=set(PARTS) or
            any(type(mask) is not bytes or len(mask)!=4096 or set(mask)-{0,1}
                for group in (before,after) for mask in group.values())):
        raise ValueError("exactly five authentic 2026 part masks on 64x64 required")
    classified={part:bytearray(4096) for part in PARTS}
    ambiguous=bytearray(4096)
    union_change=bytearray(4096)
    for k in range(4096):
        old=[part for part in PARTS if before[part][k]]
        new=[part for part in PARTS if after[part][k]]
        if bool(old)==bool(new):
            continue  # interior change or fully hidden upper/lower model change
        union_change[k]=1
        visible=new if new else old
        if len(visible)==1:
            classified[visible[0]][k]=1
        else:
            ambiguous[k]=1
    result={part:bytes(mask) for part,mask in classified.items()}
    result["overlapping_2026_parts_unattributed"]=bytes(ambiguous)
    if any(sum(int(mask[k]) for mask in result.values())!=union_change[k]
           for k in range(4096)):
        raise ValueError("2026 visible parent motion does not partition union XOR")
    return {"whole_visible_2026_union_xor":bytes(union_change),
            "disjoint_candidate_motion_masks":result}


def source_vs_model_motion_regions(original_before:bytes,original_after:bytes,
                                   before:dict[str,bytes],after:dict[str,bytes])->dict:
    if any(type(x) is not bytes or len(x)!=4096 or set(x)-{0,1}
           for x in (original_before,original_after)):
        raise ValueError("two exact binary 64px original source frames required")
    original_edge=bytes(int(x!=y) for x,y in zip(original_before,original_after))
    partition=partition_2026_visible_motion(before,after)
    candidate_edge=partition["whole_visible_2026_union_xor"]
    by=partition["disjoint_candidate_motion_masks"]
    bands={}
    totals={"tp":0,"fp":0,"fn":0}
    for name,lo,hi in SOURCE_Y_BANDS:
        indices=range(lo*64,(hi+1)*64)
        tp=sum(int(original_edge[k] and candidate_edge[k]) for k in indices)
        fp=sum(int(not original_edge[k] and candidate_edge[k]) for k in indices)
        fn=sum(int(original_edge[k] and not candidate_edge[k]) for k in indices)
        per={}
        for part,mask in by.items():
            per[part]={
                "source_changed_pixel_instances_explained":sum(
                    int(original_edge[k] and mask[k]) for k in indices),
                "candidate_change_absent_from_source":sum(
                    int(not original_edge[k] and mask[k]) for k in indices),
                "candidate_visible_motion_pixels":sum(mask[k] for k in indices),
            }
        if (sum(v["source_changed_pixel_instances_explained"] for v in per.values())!=tp
                or sum(v["candidate_change_absent_from_source"] for v in per.values())!=fp
                or sum(v["candidate_visible_motion_pixels"] for v in per.values())!=tp+fp):
            raise ValueError("visible model parent motion counts do not partition union change")
        for key,val in (("tp",tp),("fp",fp),("fn",fn)):
            totals[key]+=val
        bands[name]={
            "source_image_y_inclusive":[lo,hi],
            "original_changed_pixel_instances":tp+fn,
            "2026_union_changed_pixel_instances":tp+fp,
            "original_vs_2026_union_xor_tp_fp_fn":{"tp":tp,"fp":fp,"fn":fn},
            "2026_disjoint_visible_parent_motion":per,
            "source_image_band_is_not_a_1994_part_identity":True,
        }
    true_tp=sum(int(a and b) for a,b in zip(original_edge,candidate_edge))
    true_fp=sum(int(not a and b) for a,b in zip(original_edge,candidate_edge))
    true_fn=sum(int(a and not b) for a,b in zip(original_edge,candidate_edge))
    if totals!={"tp":true_tp,"fp":true_fp,"fn":true_fn}:
        raise ValueError("2026 authored-part regions disagree with full original source")
    d=true_tp+true_fp+true_fn
    return {
        "original_source_changed_pixel_instances":sum(original_edge),
        "candidate_2026_visible_union_changed_pixel_instances":sum(candidate_edge),
        "source_vs_2026_motion_tp_fp_fn":totals,
        "source_vs_2026_motion_iou":round(true_tp/d,8) if d else 1.,
        "source_image_bands":bands,
        "overlapping_model_parts_are_explicitly_unattributed":True,
        "2026_synthetic_part_names_are_not_original_1994_anatomy":True,
    }
