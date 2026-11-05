#!/usr/bin/env python3
"""Post-hoc perceptual redundancy audit for the genuine original wheel holdout.

Exact SHA-distinct original binary source silhouettes can be visually almost
identical. Report both exact-mask and source-mask-IoU-connected cluster scores
at several DECLARED thresholds; threshold selection happened AFTER seeing
the geometry result, so do not claim prospective independent 3D poses.
"""
from __future__ import annotations

import argparse
import hashlib
from itertools import combinations
import json
from pathlib import Path
from statistics import median

try:
    from tools.art.freeze_racer_source_family_splits import validate_corpus
    from tools.art.evaluate_original_racer_wheel_holdout import (
        SCHEMA as HOLDOUT_SCHEMA, originals_from_corpus, digest,
    )
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from freeze_racer_source_family_splits import validate_corpus
    from evaluate_original_racer_wheel_holdout import (
        SCHEMA as HOLDOUT_SCHEMA, originals_from_corpus, digest,
    )
    from no_replace_report import publish_text_once

SCHEMA = "UR-RACER-ORIGINAL-HOLDOUT-NEAR-DUPLICATE-AUDIT/1"
THRESHOLDS = (0.80, 0.85, 0.90, 0.95)


def mask_iou(a: bytes, b: bytes) -> float:
    if (not isinstance(a, bytes) or not isinstance(b, bytes)
            or len(a) != 4096 or len(b) != 4096
            or any(x not in (0,1) for x in a)
            or any(x not in (0,1) for x in b)):
        raise ValueError("near-duplicate metric requires binary source 64x64 masks")
    intersection = sum(x == 1 and y == 1 for x, y in zip(a,b))
    union = sum(x == 1 or y == 1 for x, y in zip(a,b))
    if union == 0:
        raise ValueError("original source masks are empty")
    return intersection/union


def cluster_masks(masks: dict[str, bytes], threshold: float):
    """Union-find connected components; threshold is descriptive, not learned."""
    if (type(threshold) is not float or not 0 < threshold <= 1
            or not isinstance(masks, dict) or len(masks) < 2
            or any(not isinstance(k,str) or len(k)!=64 or
                   hashlib.sha256(v).hexdigest()!=k for k,v in masks.items())):
        raise ValueError("invalid original silhouette set or threshold")
    keys=sorted(masks)
    parent={k:k for k in keys}

    def root(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]
            x=parent[x]
        return x

    pairwise=[]
    for a,b in combinations(keys,2):
        s=mask_iou(masks[a],masks[b])
        pairwise.append(s)
        if s>=threshold:
            parent[root(a)]=root(b)
    groups={}
    for k in keys:
        groups.setdefault(root(k),[]).append(k)
    return sorted((sorted(g) for g in groups.values()),
                  key=lambda g:(-len(g),g[0])), pairwise


def score_clusters(groups, rows: dict):
    """Equal vote to each near-duplicate group; each source mask once within."""
    results=[]
    seen=set()
    for group in groups:
        if not group or any(h in seen or h not in rows for h in group):
            raise ValueError("cluster overlaps or lacks original source metrics")
        seen.update(group)
        baseline=[rows[h]["unpaired_candidate_scores"]["1.0"]["mask_iou"]
                  for h in group]
        wider=[rows[h]["unpaired_candidate_scores"]["1.1"]["mask_iou"]
               for h in group]
        a=sum(baseline)/len(baseline)
        b=sum(wider)/len(wider)
        results.append({"binary_mask_shas":group,
                        "source_binary_mask_count":len(group),
                        "baseline_mean_iou":round(a,8),
                        "wider_1_10_mean_iou":round(b,8),
                        "delta_iou":round(b-a,8)})
    return {"cluster_count":len(results),
            "cluster_sizes":sorted([len(g) for g in groups], reverse=True),
            "equal_cluster_mean_baseline_iou":
                round(sum(x["baseline_mean_iou"] for x in results)/len(results),8),
            "equal_cluster_mean_wider_iou":
                round(sum(x["wider_1_10_mean_iou"] for x in results)/len(results),8),
            "equal_cluster_wider_wins":sum(x["delta_iou"]>0 for x in results),
            "equal_cluster_wider_losses":sum(x["delta_iou"]<0 for x in results),
            "clusters":results}


def audit(corpus_file: Path, holdout_file: Path):
    receipt, validated = validate_corpus(corpus_file)
    raw = holdout_file.read_bytes()
    source = json.loads(raw)
    if (source.get("schema") != HOLDOUT_SCHEMA or
            source.get("source_corpus_sha256") != digest(corpus_file.read_bytes())
            or source.get("original_independent_binary_silhouettes") != len(validated["all_masks"])
            or source.get("original_source_frame_observations") !=
                len(receipt["source_temporal_frame_observations"])
            or source.get("old_original_3d_camera_recovered") is not False
            or source.get("owner_character_likeness_approved") is not False):
        raise ValueError("stale or falsely claimed original source holdout")
    split=source["leakage_free_window_split"]
    holdout=split["withheld_binary_shas"]
    fit=split["fit_binary_shas"]
    if (not isinstance(holdout,list) or len(holdout)<2 or len(set(holdout))!=len(holdout)
            or set(holdout) & set(fit)
            or set(holdout)|set(fit) != validated["all_masks"]):
        raise ValueError("original binary source holdout leakage or missing shape")
    originals=originals_from_corpus(corpus_file,receipt)
    if set(originals)!=validated["all_masks"]:
        raise ValueError("original source pixel identity changed")
    masks={h:originals[h]["mask"] for h in holdout}
    scores=source["per_original_binary_mask"]
    if set(scores)!=set(originals):
        raise ValueError("unpaired source silhouette scores incomplete")
    result={}
    for threshold in THRESHOLDS:
        groups,pairwise=cluster_masks(masks,float(threshold))
        row=score_clusters(groups,scores)
        row["min_pair_iou"]=round(min(pairwise),8)
        row["median_pair_iou"]=round(median(pairwise),8)
        row["max_pair_iou"]=round(max(pairwise),8)
        result[str(threshold)]=row
    return {
        "schema":SCHEMA,
        "original_corpus_sha256":digest(corpus_file.read_bytes()),
        "frozen_wheel_holdout_report_sha256":digest(raw),
        "original_source_binary_mask_count":len(originals),
        "exact_sha_distinct_heldout_masks":len(holdout),
        "same_1994_3d_camera_proven":False,
        "near_duplicate_thresholds_selected_after_original_result":True,
        "clusters_are_verified_independent_original_3d_poses":False,
        "original_sprite_to_2026_glb_pose_mapping_verified":False,
        "owner_character_likeness_approved":False,
        "shipping_art_approved":False,
        "thresholds":result,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus",required=True,type=Path)
    parser.add_argument("--holdout",required=True,type=Path)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    result=json.dumps(audit(args.corpus,args.holdout),indent=2,sort_keys=True)+"\n"
    if args.out:
        publish_text_once(args.out,result)
    else:
        print(result,end="")


if __name__=="__main__":
    main()
