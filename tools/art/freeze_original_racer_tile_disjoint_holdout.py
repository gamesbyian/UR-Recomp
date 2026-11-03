#!/usr/bin/env python3
"""Freeze a source-tile-disjoint original 2D holdout without seeing GLB scores.

Consumes two SHA-verified historical evidence artifacts only. This never
claims independent original 3D viewpoints, source animation chronology, or
recovery of a 1994 camera/rig. Identical index planes join windows transitively.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

SCHEMA="UR-ART4K-FROZEN-ORIGINAL-TILE-DISJOINT-HOLDOUT/1"
MANIFEST_SHA="e26193f767d22280ab65b0549e707fa05ef246a903a4cebd47411f75726dc66e"
TILE_REPORT_SHA="cccb78328307003b3f8148aa20ef7cca27c905e77610be2b3ffd1aa7e7d5f33f"
ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
REGISTRY_SHA="05372395d04d5403c7b80859c171f06d754f1322a676d66f4ce5d7b3aec948ad"
FIRST="first-1205-1220"


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def valid_sha(s):
    return type(s) is str and len(s)==64 and all(c in "0123456789abcdef" for c in s)


def freeze(per_window:dict[str,set[str]],edges:list[dict],first:str=FIRST)->dict:
    """Connected-window fitting cohort, then independent tile-overlap diagnostic.

    Holdouts sharing index planes with the fitting cohort are never withheld.
    Sharing a tile is *measured* independently of identical index-plane identity;
    it is neither silently discarded nor automatically called pose leakage.
    """
    if (not isinstance(per_window,dict) or first not in per_window or
            len(per_window)<2 or any(type(w) is not str or not w or
                not isinstance(poses,set) or not poses or
                any(not valid_sha(h) for h in poses)
                for w,poses in per_window.items())):
        raise ValueError("invalid source pose windows or first family")
    names=sorted(per_window)
    planes=set().union(*per_window.values())
    parent={n:n for n in names}
    def root(n):
        while parent[n]!=n:
            parent[n]=parent[parent[n]];n=parent[n]
        return n
    windows_by_plane=defaultdict(list)
    for name in names:
        for h in per_window[name]:windows_by_plane[h].append(name)
    for windows in windows_by_plane.values():
        leader=windows[0]
        for name in windows[1:]:
            parent[root(name)]=root(leader)
    fitting_windows={n for n in names if root(n)==root(first)}
    fitted=set().union(*(per_window[n] for n in fitting_windows))
    withheld=planes-fitted
    if not withheld:
        raise ValueError("no genuinely withheld original source planes")
    if not isinstance(edges,list):
        raise ValueError("tile-reuse evidence must be an exact list")
    by_pair={}
    for edge in edges:
        if not isinstance(edge,dict):
            raise ValueError("invalid source tile reuse pair")
        a=edge.get("left_source_index_sha256")
        b=edge.get("right_source_index_sha256")
        count=edge.get("shared_nonblank_exact_tile_contents")
        if (not valid_sha(a) or not valid_sha(b) or a==b or
                a not in planes or b not in planes or
                type(count) is not int or not 1<=count<=30):
            raise ValueError("unknown or invalid source tile overlap witness")
        pair=tuple(sorted((a,b)))
        if pair in by_pair:
            raise ValueError("duplicate cross-source tile reuse edge")
        by_pair[pair]=count
    def overlap(a,b):
        return by_pair.get(tuple(sorted((a,b))),0)
    heldout=[]
    cross=Counter()
    for h in sorted(withheld):
        values=[overlap(h,f) for f in sorted(fitted)]
        cross.update(values)
        heldout.append({
            "original_source_index_plane_sha256":h,
            "fitting_planes_with_at_least_one_exact_nonblank_tile":sum(x>0 for x in values),
            "maximum_shared_exact_nonblank_tiles_in_one_pair":max(values),
            "total_pairwise_shared_exact_nonblank_tile_counts":sum(values),
            "tile_disjoint_from_every_fitted_original_plane":not any(values),
        })
    return {
        "schema":SCHEMA,
        "fit_connected_original_registry_windows":sorted(fitting_windows),
        "all_original_registry_windows":len(names),
        "original_fitting_index_plane_shas":sorted(fitted),
        "original_withheld_index_plane_shas":sorted(withheld),
        "original_fitting_planes":len(fitted),
        "original_withheld_planes":len(withheld),
        "potential_fitting_to_withheld_pairs":len(fitted)*len(withheld),
        "fitting_to_withheld_pairs_with_any_shared_exact_nonblank_tile":
            sum(count for n,count in cross.items() if n>0),
        "fitting_to_withheld_tile_overlap_histogram":
            {str(n):cross[n] for n in sorted(cross)},
        "fully_tile_disjoint_original_withheld_index_plane_shas":
            [x["original_source_index_plane_sha256"] for x in heldout
             if x["tile_disjoint_from_every_fitted_original_plane"]],
        "per_original_withheld_plane":heldout,
        "selection_uses_no_GLb_model_results":True,
        "source_original_3d_camera_verified":False,
        "source_live_ppu_sequence_verified":False,
        "source_original_3d_viewpoint_independence_verified":False,
        "original_source_to_model_pose_correspondence_verified":False,
        "owner_likeness_approved":False,
    }


def produce(source_zip:Path,tile_report_path:Path)->dict:
    """Read archived ROM-authenticated source manifest and exact numeric lineage."""
    raw=tile_report_path.read_bytes()
    if sha(raw)!=TILE_REPORT_SHA:
        raise ValueError("not the frozen original authenticated tile-lineage report")
    lineage=json.loads(raw)
    if (lineage.get("schema")!="UR-ART4K-ORIGINAL-RACER-SOURCE-TILE-LINEAGE/1" or
            lineage.get("source_rom_sha256")!=ROM_SHA or
            lineage.get("source_registry_sha256")!=REGISTRY_SHA or
            lineage.get("source_manifest_sha256")!=MANIFEST_SHA or
            lineage.get("original_source_representations")!=59 or
            lineage.get("unique_original_index_planes")!=35 or
            lineage.get("original_1994_anatomical_part_correspondence_verified") is not False):
        raise ValueError("tile evidence provenance or limitations invalid")
    with zipfile.ZipFile(source_zip) as archive:
        manifest_bytes=archive.read("source-corpus.json")
        if sha(manifest_bytes)!=MANIFEST_SHA:
            raise ValueError("original source composition manifest SHA differs")
    manifest=json.loads(manifest_bytes)
    if (manifest.get("source_rom_sha256")!=ROM_SHA or
            manifest.get("source_registry_sha256")!=REGISTRY_SHA or
            manifest.get("native_live_original_PPU_or_1994_3d_camera_independently_verified") is not False):
        raise ValueError("invalid historical source-original provenance")
    per= lineage["per_original_index_plane"]
    if len(per)!=35 or set(per)!={k for k in per if valid_sha(k)}:
        raise ValueError("not 35 canonical original 4bpp source planes")
    representation_to_plane={}
    for plane,row in per.items():
        ids=row.get("original_representation_ids")
        if (not isinstance(ids,list) or not ids or
                row.get("representation_count")!=len(ids)):
            raise ValueError("source colourway group has incomplete membership")
        for identity in ids:
            if identity in representation_to_plane:
                raise ValueError("original representation assigned to two planes")
            representation_to_plane[identity]=plane
    if set(representation_to_plane)!=set(manifest["source_representations"]) or len(representation_to_plane)!=59:
        raise ValueError("original registry identities do not match tile evidence")
    windows=defaultdict(set)
    for row in manifest["source_temporal_frame_observations"]:
        win=row["window"]
        if win not in manifest["registered_source_windows"]:
            raise ValueError("unknown source authored registry window")
        for identity in row["representations"].values():
            windows[win].add(representation_to_plane[identity])
    if set(windows)!=set(manifest["registered_source_windows"]) or len(windows)!=27:
        raise ValueError("original registry window set is incomplete")
    result=freeze(dict(windows),lineage["shared_exact_opaque_tile_pairs"])
    if (result["original_fitting_planes"]!=16 or
            result["original_withheld_planes"]!=19 or
            len(result["fully_tile_disjoint_original_withheld_index_plane_shas"])!=6 or
            result["fitting_to_withheld_pairs_with_any_shared_exact_nonblank_tile"]!=13):
        raise ValueError("historical original 16/19/6 tile-disjoint split changed")
    for plane in result["fully_tile_disjoint_original_withheld_index_plane_shas"]:
        result.setdefault("fully_tile_disjoint_source_representation_ids",{})[plane]=sorted(
            identity for identity,h in representation_to_plane.items() if h==plane)
    result["source_corpus_manifest_sha256"]=MANIFEST_SHA
    result["source_original_tile_lineage_report_sha256"]=TILE_REPORT_SHA
    result["original_source_rom_sha256"]=ROM_SHA
    result["original_source_registry_sha256"]=REGISTRY_SHA
    result["selection_frozen_before_consulting_any_experimental_GLb_score"]=True
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--tile-lineage-json",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    from tools.art.no_replace_report import publish_text_once
    report=produce(x.source_zip,x.tile_lineage_json)
    publish_text_once(x.out,json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in
                      ("per_original_withheld_plane","original_fitting_index_plane_shas",
                       "original_withheld_index_plane_shas")},sort_keys=True,indent=2))


if __name__=="__main__":
    main()
