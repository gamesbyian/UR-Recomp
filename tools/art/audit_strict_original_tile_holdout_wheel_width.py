#!/usr/bin/env python3
"""Read-only retrospective wheel-width audit on pre-frozen source-tile holdouts.

Rejoins earlier published *2D* experimental-GLB IoU scores to original 4bpp
index-plane SHA identities. No new model fits, 1994 pose registration, original
camera evidence, PPU frame history or source anatomical labels are inferred.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path

SCHEMA="UR-ART4K-RETROSPECTIVE-STRICT-SOURCE-TILE-WHEEL-WIDTH/1"
ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SOURCE_SHA="e26193f767d22280ab65b0549e707fa05ef246a903a4cebd47411f75726dc66e"
GLB_SHA="efdc8425f252b4a0218d140d087c6cc923689589e0cf74cc6333d722182595f5"
CAMERA_SHA="1261016b22524795ce434b0524df3b09c61dff9c71c11180d44acb45355c6028"
WHEEL_BLOB="49db7090f3455b2a9cc7ae946888fb4413877fd8"
LOOKUP_BLOB="525c3d52f96594d332394ba60dc2096b391caec4"
FROZEN_BLOB="828d8e0c53f314a9e2164d8fd0158c7f01e90049"


def valid_sha(s):
    return type(s) is str and len(s)==64 and all(c in "0123456789abcdef" for c in s)


def git_blob_sha(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def read_frozen_file(path:Path,blob:str)->dict:
    raw=path.read_bytes()
    if git_blob_sha(raw)!=blob:
        raise ValueError("source JSON changed from precommitted evidence blob")
    return json.loads(raw)


def decimal_score(x):
    if isinstance(x,bool) or not isinstance(x,(int,float,str)):
        raise ValueError("original 2D source score is not a number")
    try:
        value=Decimal(str(x))
    except Exception as exc:
        raise ValueError("original 2D source score is malformed") from exc
    if not value.is_finite() or not Decimal(0)<=value<=Decimal(1):
        raise ValueError("original 2D source IoU must be finite between zero and one")
    return value


def rounded(value:Decimal)->str:
    return str(value.quantize(Decimal("0.00000001"),rounding=ROUND_HALF_UP))


def compare_fixed_2d_masks(index_to_mask:dict, all_held:list, strict:list,
                           scores:dict)->dict:
    """Require an exact bijection of original source 4bpp and binary masks.

    Neither selecting a new camera nor choosing a best GLB pose per source is
    part of this operation. Both models' earlier per-source scores are frozen.
    """
    if (not isinstance(index_to_mask,dict) or not index_to_mask or
            any(not valid_sha(k) or not valid_sha(v)
                for k,v in index_to_mask.items()) or
            len(set(index_to_mask.values()))!=len(index_to_mask) or
            not isinstance(all_held,list) or not all_held or
            any(not valid_sha(x) for x in all_held) or
            len(all_held)!=len(set(all_held)) or
            not isinstance(strict,list) or not strict or
            any(not valid_sha(x) for x in strict) or
            len(strict)!=len(set(strict)) or
            not set(strict).issubset(all_held)):
        raise ValueError("original source pose membership or 4bpp/binary identity invalid")
    if (set(all_held)-set(index_to_mask) or
            not isinstance(scores,dict) or
            set(scores)!={index_to_mask[x] for x in all_held}):
        raise ValueError("previously scored original heldout masks differ from frozen set")
    rows=[]
    for original in sorted(all_held):
        binary=index_to_mask[original]
        values=scores[binary]
        if not isinstance(values,dict) or set(values)!={"one_x_mask_iou","one_point_one_x_mask_iou"}:
            raise ValueError("historical width comparison missing exactly two source scores")
        before=decimal_score(values["one_x_mask_iou"])
        after=decimal_score(values["one_point_one_x_mask_iou"])
        rows.append({"original_index_plane_sha256":original,
                     "original_binary_mask_sha256":binary,
                     "wheel_width_1_00_iou":rounded(before),
                     "wheel_width_1_10_iou":rounded(after),
                     "delta_iou":rounded(after-before),
                     "strictly_tile_disjoint_from_fit":original in strict})
    def aggregate(ordered):
        vals=[r for r in rows if r["original_index_plane_sha256"] in ordered]
        return {
            "independent_original_2d_source_planes":len(vals),
            "width_1_00_mean_iou":rounded(sum((Decimal(x["wheel_width_1_00_iou"]) for x in vals),Decimal(0))/len(vals)),
            "width_1_10_mean_iou":rounded(sum((Decimal(x["wheel_width_1_10_iou"]) for x in vals),Decimal(0))/len(vals)),
            "width_1_10_minus_1_00_mean_delta_iou":
                rounded(sum((Decimal(x["delta_iou"]) for x in vals),Decimal(0))/len(vals)),
            "width_1_10_wins":sum(Decimal(x["delta_iou"])>0 for x in vals),
            "width_1_10_losses":sum(Decimal(x["delta_iou"])<0 for x in vals),
            "width_1_10_ties":sum(Decimal(x["delta_iou"])==0 for x in vals),
        }
    return {
        "all_19_original_source_shapes":aggregate(set(all_held)),
        "strict_six_source_tile_disjoint_shapes":aggregate(set(strict)),
        "per_original_2d_source_index_plane":rows,
    }


def audited_retrospective(wheel:dict,lookup:dict,frozen:dict)->dict:
    if (wheel.get("schema")!="UR-RACER-WHEEL-HOLDOUT-RETAINED-RESEARCH-SUMMARY/1" or
            wheel.get("source_rom_sha256")!=ROM_SHA or
            wheel.get("source_corpus_sha256")!=SOURCE_SHA or
            wheel.get("model_glb_sha256")!=GLB_SHA or
            wheel.get("provisional_camera_sha256")!=CAMERA_SHA or
            wheel.get("heldout_independent_binary_mask_count")!=19 or
            wheel.get("original_sprite_to_2026_experimental_rig_pose_registered") is not False):
        raise ValueError("historical unpaired 2026 GLB candidate evidence changed")
    if (lookup.get("schema")!="UR-ART4K-SOURCE-RGBA-TO-4BPP-INDEX-LOOKUP/1" or
            lookup.get("original_usa_rom_sha256")!=ROM_SHA or
            lookup.get("original_source_manifest_sha256")!=SOURCE_SHA or
            lookup.get("source_images_verified")!=41 or
            lookup.get("unique_index_planes_verified")!=35 or
            lookup.get("original_3d_part_identity_verified") is not False):
        raise ValueError("source ROM index lookup provenance is not valid")
    if (frozen.get("schema")!="UR-ART4K-FROZEN-ORIGINAL-TILE-DISJOINT-HOLDOUT-SUMMARY/1" or
            frozen.get("original_USA_ROM_sha256")!=ROM_SHA or
            frozen.get("original_source_manifest_sha256")!=SOURCE_SHA or
            frozen.get("fit_to_withheld_pairs_total")!=304 or
            frozen.get("fit_to_withheld_pairs_with_any_nonblank_tile_overlap")!=13 or
            frozen.get("source_4bpp_planes_in_fit")!=16 or
            frozen.get("source_4bpp_planes_in_withheld")!=19 or
            frozen.get("fit_to_withheld_planes_with_zero_nonblank_tile_overlap")!=6 or
            frozen.get("experimental_GLb_pose_correspondence_verified") is not False):
        raise ValueError("strict 2D source tile-disjoint split changed")
    map_index={}
    for record in lookup["rgba_to_index"].values():
        src=record["original_4bpp_index_plane_sha256"]
        mask=record["source_binary_mask_sha256"]
        if not valid_sha(src) or not valid_sha(mask):
            raise ValueError("original 4bpp index/alpha SHA malformed")
        if src in map_index and map_index[src]!=mask:
            raise ValueError("colourway changed original source binary mask")
        map_index[src]=mask
    fit=frozen["fit_original_index_plane_sha256"]
    held=frozen["withheld_original_index_plane_sha256"]
    strict=frozen["strictly_tile_disjoint_withheld_index_plane_sha256"]
    if (len(map_index)!=35 or len(fit)!=16 or len(held)!=19 or len(strict)!=6 or
            set(fit)&set(held) or set(fit+held)!=set(map_index)):
        raise ValueError("source 35/16/19/6 original membership mismatch")
    report=compare_fixed_2d_masks(map_index,held,strict,wheel["withheld_binary_mask_scores"])
    prior=wheel["previously_untested_source_2D_masks"]
    broad=report["all_19_original_source_shapes"]
    for label,field in (("width_1_00_mean_iou","one_x_mean_iou"),
                        ("width_1_10_mean_iou","one_point_one_x_mean_iou")):
        if abs(Decimal(broad[label])-decimal_score(prior[field]))>Decimal("0.00000001"):
            raise ValueError("retained historical original source averages do not reproduce")
    if (broad["width_1_10_wins"]!=19 or
            report["strict_six_source_tile_disjoint_shapes"]["width_1_10_wins"]!=6):
        raise ValueError("frozen 19/6 source counts contradicted by exact wheel report")
    return {
        "schema":SCHEMA,
        "source_original_ROM_SHA256":ROM_SHA,
        "source_original_2d_manifest_SHA256":SOURCE_SHA,
        "experimental_GLb_SHA256":GLB_SHA,
        "provisional_camera_SHA256":CAMERA_SHA,
        "original_index_lookup_git_blob_SHA1":LOOKUP_BLOB,
        "precommitted_source_tile_disjoint_holdout_git_blob_SHA1":FROZEN_BLOB,
        "historical_original_wheel_width_score_git_blob_SHA1":WHEEL_BLOB,
        "historical_source_geometry_scores_reused_without_recomputation":True,
        "strict_six_selection_is_retrospective_and_not_new_blind_3d_poses":True,
        "source_1994_original_camera_or_3d_rig_verified":False,
        "original_sprite_to_experimental_GLb_pose_mapping_verified":False,
        "owner_likeness_approved":False,
        "shipping_art_approved":False,
        **report,
    }


def main():
    root=Path(__file__).resolve().parents[2]
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=root)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    root=args.root.resolve()
    wheel=read_frozen_file(root/"analysis/data/racer-wheel-x-genuine-rom-holdout-20261101.json",WHEEL_BLOB)
    lookup=read_frozen_file(root/"analysis/data/racer-original-index-lookup-20261102.json",LOOKUP_BLOB)
    frozen=read_frozen_file(root/"analysis/data/racer-original-strict-tile-disjoint-holdout-20261103.json",FROZEN_BLOB)
    raw=json.dumps(audited_retrospective(wheel,lookup,frozen),indent=2,sort_keys=True)+"\n"
    if args.out:
        if args.out.resolve().is_relative_to(root):
            raise ValueError("do not overwrite frozen original input repository")
        from tools.art.no_replace_report import publish_text_once
        publish_text_once(args.out,raw)
    else:
        print(raw,end="")


if __name__=="__main__":
    main()
