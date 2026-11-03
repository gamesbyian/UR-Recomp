#!/usr/bin/env python3
"""Conservative, ROM-free 4bpp-index vs experimental-GLB part hypothesis scorer.

Only operates on already independently paired 64px 2D views. No real original
3D pose pairings have been admitted; labels remain provisional, never 1994 IDs.
"""
from __future__ import annotations
from collections import defaultdict
import hashlib
import itertools

SCHEMA="UR-ART4K-INDEX-VS-EXPERIMENTAL-GLB-PART/1"
PARTS=("tire","rim_and_hub","fork_and_frame","pedals","saddle")
SHIFTS=((13,7),(29,19),(37,41))

def digest(raw):return hashlib.sha256(raw).hexdigest()

def verify_pairs(pairs):
    if not isinstance(pairs,list) or len(pairs)<2:
        raise ValueError("at least two source-registered original pose families needed")
    families=set();seen=set();source_shas=set();part_names=set()
    for pair in pairs:
        if not isinstance(pair,dict):raise ValueError("malformed source/GLB 2D pairing")
        key=pair.get("id");family=pair.get("family")
        index=pair.get("source_index_plane");part=pair.get("glb_part_ids")
        names=pair.get("glb_part_id_names")
        if (not isinstance(key,str) or not key or key in seen or
                not isinstance(family,str) or not family or
                not isinstance(index,bytes) or len(index)!=4096 or
                not isinstance(part,bytes) or len(part)!=4096 or
                any(x>15 for x in index) or
                not isinstance(names,dict) or not names or
                any(type(k) is not int or not 1<=k<=255 or n not in PARTS
                    for k,n in names.items()) or
                len(set(names.values()))!=len(names) or
                any(x and x not in names for x in part) or
                pair.get("independent_pose_alignment_witness") is not True):
            raise ValueError("explicit 64px index, GLB parent mask and independent pose alignment required")
        sha=digest(index)
        if sha in source_shas:
            raise ValueError("duplicate original colourway index plane is not independent")
        source_shas.add(sha);seen.add(key);families.add(family);part_names.update(names.values())
    if len(families)<2 or len(part_names)<2:
        raise ValueError("independent family holdout and multiple parts required")
    return sorted(families),sorted(part_names)

def overlap(pairs,families,parts,shift=None):
    """4bpp-index population and index-versus-GLB-part intersections."""
    hits=defaultdict(lambda:defaultdict(int));totals=defaultdict(int)
    for row in pairs:
        if row["family"] not in families:continue
        names=row["glb_part_id_names"];mask=row["glb_part_ids"]
        for i,index in enumerate(row["source_index_plane"]):
            if index==0:continue
            totals[index]+=1
            if shift is None:q=i
            else:
                dx,dy=shift
                q=((i//64+dy)%64)*64+(i%64+dx)%64
            label=mask[q]
            if label:hits[index][names[label]]+=1
    return hits,totals

def ranked_parts(counts,total,parts):
    if total<1:return []
    scores=[]
    for n in (1,2):
        for subset in itertools.combinations(parts,n):
            matched=sum(counts[p] for p in subset)
            purity=matched/total
            score=purity-.08*(n-1)  # avoid falsely splitting each palette index
            scores.append({"parts":list(subset),"training_purity":purity,
                           "score":score,"matched_pixels":matched})
    return sorted(scores,key=lambda x:(-x["score"],len(x["parts"]),x["parts"]))

def propose_index_part_correspondence(pairs,holdout_families,
                                      min_train_pixels=8,min_heldout_pixels=4,
                                      min_train_purity=.80,min_heldout_purity=.70,
                                      min_margin=.10):
    families,parts=verify_pairs(pairs)
    if (not isinstance(holdout_families,list) or not holdout_families or
            len(set(holdout_families))!=len(holdout_families) or
            any(x not in families for x in holdout_families)):
        raise ValueError("genuine held-out original pose families required")
    held=set(holdout_families);train=set(families)-held
    if not train:raise ValueError("cannot fit on a held-out family")
    if (any(type(x) is not int or x<1 for x in (min_train_pixels,min_heldout_pixels)) or
            any(type(x) not in (int,float) or not 0<=x<=1 for x in
                (min_train_purity,min_heldout_purity,min_margin))):
        raise ValueError("invalid fixed thresholds")
    fit,fit_total=overlap(pairs,train,parts)
    hold,hold_total=overlap(pairs,held,parts)
    negatives=[overlap(pairs,train,parts,shift=shift)[0] for shift in SHIFTS]
    result=[]
    for idx in sorted(set(fit_total)|set(hold_total)):
        candidates=ranked_parts(fit[idx],fit_total[idx],parts)
        best=candidates[0] if candidates else None
        reasons=[]
        score=best["score"] if best else 0
        margin=score-(candidates[1]["score"] if len(candidates)>1 else 0)
        hypothesis=best["parts"] if best else []
        held_purity=sum(hold[idx][p] for p in hypothesis)/hold_total[idx] if hold_total[idx] else 0
        null=max((ranked_parts(counts[idx],fit_total[idx],parts)[0]["score"]
                  for counts in negatives if fit_total[idx]),default=0)
        if fit_total[idx]<min_train_pixels:reasons.append("insufficient_train_pixels")
        if hold_total[idx]<min_heldout_pixels:reasons.append("insufficient_holdout_pixels")
        if not best or best["training_purity"]<min_train_purity:
            reasons.append("weak_training_overlap")
        if held_purity<min_heldout_purity:reasons.append("heldout_pose_disagrees")
        if margin<min_margin:reasons.append("ambiguous_parts")
        if score-null<min_margin:reasons.append("cannot_beat_spatial_shift_control")
        result.append({
            "original_source_palette_index":idx,
            "candidate_experimental_3d_parts":hypothesis,
            "classification":("unresolved" if reasons else "provisional_paired_2d_hypothesis"),
            "reasons":reasons,"training_index_pixels":fit_total[idx],
            "heldout_index_pixels":hold_total[idx],
            "training_purity":best["training_purity"] if best else 0,
            "heldout_purity":held_purity,"second_candidate_margin":margin,
            "shifted_2d_control_best_score":null,
            "not_an_independent_statistical_null":True,
            "top_five_candidate_assignments":candidates[:5]})
    return {
        "schema":SCHEMA,
        "training_families":sorted(train),"heldout_families":sorted(held),
        "source_index_plane_sha_by_view":{s["id"]:digest(s["source_index_plane"]) for s in pairs},
        "experimental_glb_parent_id_sha_by_view":{s["id"]:digest(s["glb_part_ids"]) for s in pairs},
        "source_1994_part_identity_verified":False,
        "independent_original_oam_obj_part_witness_verified":False,
        "original_3d_pose_correspondence_verified":False,
        "owner_likeness_approved":False,
        "hypotheses":result}
