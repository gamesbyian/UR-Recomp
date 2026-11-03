#!/usr/bin/env python3
"""Offline re-verification of 20 original Mesen USA-ROM 2D racer/screen matches.

Requires the independent original Mesen source ZIP. No ROM execution or 3D
fitting. A matching RGB pixel is an observed correspondence, not established
PPU scanline ownership or an original 1994 mesh/rig/camera.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_mesen_obj_screen_pixels import (
    decode_source_obj, p6_screen,
)
from tools.art.audit_original_postcountdown_obj_compositing import compare_opaque_pixels
from tools.art.capture_original_mesen_ppu_raw import (
    validate_snapshot_files, REGIONS, ROM_SHA, MESEN_REVISION,
)

SCHEMA="UR-ART4K-20-ORIGINAL-MESEN-2D-SPRITES-REGISTERED-TO-COMPLETED-P6/1"
TICKS=(1601,1607,1618,1631,1648,1671,1700,1731,1768,1809,
       1852,1899,1952,2011,2072,2139,2210,2283,2362,2445)
SOURCE_ZIP_SHA="709fbc2a1cd94b888d8ae0d43894c42c5d455bd968f6bc11f26e710f44e2788f"
MAX_ZIP=1_000_000
MAX_UNCOMPRESSED=6_000_000
MANIFEST="manifest.json"


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def validate_receipt(receipt:dict)->None:
    if (not isinstance(receipt,dict) or receipt.get("schema")!=SCHEMA or
            receipt.get("source_zip_sha256")!=SOURCE_ZIP_SHA or
            receipt.get("source_run")!=41605614082 or
            receipt.get("source_artifact")!=13217381754 or
            receipt.get("original_rom_sha256")!=ROM_SHA or
            receipt.get("mesen_revision")!=MESEN_REVISION or
            receipt.get("source_no_frame_skip") is not True):
        raise ValueError("unverified original sparse Mesen source receipt")
    fields=("source_original_per_scanline_oam_mutations_proved",
            "original_ppu_colour_math_or_pixel_layer_ownership_proved",
            "original_1994_source_3d_model_rig_camera_recovered",
            "experimental_2026_glb_pose_registration_verified",
            "owner_likeness_approved")
    if any(receipt.get(field) is not False for field in fields):
        raise ValueError("overclaimed original 3D/PPU or owner likeness")
    samples=receipt.get("samples")
    if (not isinstance(samples,list) or
            [r.get("tick") for r in samples]!=list(TICKS)):
        raise ValueError("changed original source tick census")
    totals={"opaque":0,"exact":0,"red_plus_13":0}
    for row in samples:
        if not isinstance(row,dict) or set(row)!={"tick","blue","red"}:
            raise ValueError("wrong original racer sample envelope")
        for name in ("blue","red"):
            val=row[name]
            if (not isinstance(val,dict) or
                    set(val)!={"screen_xy","opaque","exact","red_plus_13","classification_sha256"} or
                    type(val["screen_xy"]) is not list or len(val["screen_xy"])!=2 or
                    any(type(a) is not int or a<0 or a>192 for a in val["screen_xy"]) or
                    type(val["opaque"]) is not int or not 0<val["opaque"]<=4096 or
                    any(type(val[k]) is not int or val[k]<0 for k in ("exact","red_plus_13")) or
                    val["exact"]+val["red_plus_13"]!=val["opaque"] or
                    not isinstance(val["classification_sha256"],str) or
                    len(val["classification_sha256"])!=64 or
                    any(c not in "0123456789abcdef" for c in val["classification_sha256"])):
                raise ValueError("incorrect original pixel classification receipt")
            for k in totals:totals[k]+=val[k]
    summary=receipt.get("summary")
    if (not isinstance(summary,dict) or summary.get("real_emulator_frame_ticks")!=20 or
            summary.get("original_racer_frames")!=40 or
            summary.get("source_opaque_pixels")!=12937 or
            summary.get("direct_source_RGB")!=12416 or
            summary.get("red_plus_13_RGB")!=521 or
            summary.get("unexplained_RGB")!=0 or
            totals!={"opaque":12937,"exact":12416,"red_plus_13":521}):
        raise ValueError("original 12937-pixel source receipt accounting changed")
    if (receipt.get("held_red_oam_xy")!=[48,48] or
            receipt.get("held_red_hflip") is not False or
            receipt.get("red_screen_mirror") is not True or
            receipt.get("blue_screen_mirror") is not False):
        raise ValueError("source held OAM vs observed flip identity changed")


def audit_source(source_zip:Path,receipt:dict)->dict:
    validate_receipt(receipt)
    raw=source_zip.read_bytes()
    if len(raw)>MAX_ZIP or sha(raw)!=SOURCE_ZIP_SHA:
        raise ValueError("not the authentic original 20-tick source ZIP")
    expected={MANIFEST}
    for tick in TICKS:
        for region in REGIONS:
            expected.add(f"frame-{tick:06d}-{region}.bin")
        expected.add(f"frame-{tick:06d}-held-display.ppm")
    with zipfile.ZipFile(source_zip) as archive:
        entries=archive.infolist()
        names=[entry.filename for entry in entries]
        if (len(names)!=len(expected) or set(names)!=expected or
                sum(entry.file_size for entry in entries)>MAX_UNCOMPRESSED or
                any(entry.is_dir() or entry.flag_bits&1 for entry in entries)):
            raise ValueError("unexpected source ZIP member inventory, encryption or sizes")
        manifest=json.loads(archive.read(MANIFEST))
        if (manifest.get("source_requested_capture_ticks")!=list(TICKS) or
                manifest.get("original_input_replay_sha256")!=receipt["original_controller_sha256"] or
                manifest.get("actual_emulator_executable_sha256")!=receipt["mesen_executable_sha256"] or
                manifest.get("source_original_snes_frame_skipping_disabled_requested") is not True):
            raise ValueError("source replay, executable or sparse ticks differ")
        with tempfile.TemporaryDirectory(prefix="art4k-live-20-") as folder:
            root=Path(folder)
            for entry in entries:
                (root/entry.filename).write_bytes(archive.read(entry))
            validate_snapshot_files(root,manifest)
            counts={"opaque":0,"exact":0,"red_plus_13":0}
            source_shapes={"blue":set(),"red":set()}
            for frame in receipt["samples"]:
                tick=frame["tick"]
                read=lambda region:(root/f"frame-{tick:06d}-{region}.bin").read_bytes()
                raw_oam,raw_vram,raw_cgram=(read(x) for x in ("oam","vram","cgram"))
                rgb=p6_screen((root/f"frame-{tick:06d}-held-display.ppm").read_bytes())
                slots=decode_oam(raw_oam)
                for name,slot,mirror in (("blue",96,False),("red",97,True)):
                    held=slots[slot]
                    if held["source_obj_hflip"] is not False:
                        raise ValueError("original held OAM horizontal flip is not the archived witness")
                    if name=="red" and (held["source_oam_x_signed9"],held["source_oam_y_raw8"])!=(48,48):
                        raise ValueError("held original red OAM differs")
                    obj=decode_source_obj(held,raw_vram,raw_cgram,
                        oam_mode=4,obj_base=0x6000,second_table_offset=0x1000)
                    xy=frame[name]["screen_xy"]
                    measured=compare_opaque_pixels(obj,rgb,x=xy[0],y=xy[1],
                        horizontal_mirror=mirror)
                    expected_row=frame[name]
                    for source_key,expected_key in (
                            ("source_opaque_pixels","opaque"),
                            ("direct_exact_RGB","exact"),
                            ("red_5bit_plus_13_RGB","red_plus_13"),
                            ("source_screen_pixel_classification_sha256","classification_sha256")):
                        if measured[source_key]!=expected_row[expected_key]:
                            raise ValueError(f"original source pixel mismatch {tick} {name} {source_key}")
                    if (measured["unaccounted_RGB"] or
                            measured["source_chromatic_pixels"] !=
                            measured["source_chromatic_pixels_accounted"]):
                        raise ValueError("incomplete original source RGB correspondence")
                    wrong=compare_opaque_pixels(obj,rgb,x=xy[0],y=xy[1],
                        horizontal_mirror=not mirror)
                    shift=compare_opaque_pixels(obj,rgb,x=xy[0]+1,y=xy[1],
                        horizontal_mirror=mirror)
                    if not wrong["unaccounted_RGB"] or not shift["unaccounted_RGB"]:
                        raise ValueError("orientation/position negative control failed")
                    source_shapes[name].add(sha(obj["alpha_mask"]))
                    for field in counts:counts[field]+=expected_row[field]
            if counts!={"opaque":12937,"exact":12416,"red_plus_13":521}:
                raise ValueError("original live source totals changed")
            if any(len(x)!=20 for x in source_shapes.values()):
                raise ValueError("original sampled 2D silhouette diversity changed")
            return {
                "schema":SCHEMA,
                "actual_source_zip_sha256":SOURCE_ZIP_SHA,
                "original_source_frame_ticks":list(TICKS),
                "original_source_sprite_observations":40,
                "source_alpha_unique_per_racer":{k:len(v) for k,v in source_shapes.items()},
                "source_pixel_accounting":counts,
                "unexplained_original_source_pixels":0,
                "original_1994_3D_mesh_camera_or_skeleton_verified":False,
                "original_live_PPU_layer_winner_or_flip_writer_verified":False,
                "source_to_experimental_GLB_pose_mapping_verified":False,
                "owner_likeness_approved":False,
            }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-zip",required=True,type=Path)
    p.add_argument("--receipt",type=Path,default=Path(
        "analysis/data/racer-original-mesen-twenty-live-2d-screen-registrations-20261103.json"))
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    from tools.art.no_replace_report import publish_text_once
    result=audit_source(args.original_zip,json.loads(args.receipt.read_text()))
    publish_text_once(args.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
