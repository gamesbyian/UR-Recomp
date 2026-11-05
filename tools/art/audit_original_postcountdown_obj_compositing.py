#!/usr/bin/env python3
"""Verify bounded original 2D OBJ orientation/colour effects in existing Mesen frames.

This verifies source raster-to-completed-RGB correspondences, NOT the original
PPU register writes, scanline ownership, original 3D rig or art acceptance.
It never emulates the ROM or modifies the original captured PPU memory.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_mesen_obj_screen_pixels import (
    colour_5_to_8, decode_source_obj, sha,
)
from tools.art.audit_original_postcountdown_obj_screen import (
    SOURCE_ZIP_SHA, TICKS, source_archive_frames,
)
from tools.art.capture_original_mesen_ppu_raw import ROM_SHA, MESEN_REVISION
from tools.art.no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-AUTHENTIC-ORIGINAL-OBJ-ORIENTATION-AND-RED-COMPOSITING/1"
FRAME_WIDTH = 256
FRAME_HEIGHT = 239
BONUS_RED_5BIT = 13
# Screen registrations were established by the earlier bounded 2D source
# comparisons; do not silently infer these from one held OAM snapshot.
BLUE_SCREEN_Y_OFFSET_FROM_HELD = 7
RED_SCREEN_Y_OFFSET_FROM_HELD = 0


def compare_opaque_pixels(obj: dict, screen_rgb: bytes, *, x: int, y: int,
                          horizontal_mirror: bool, red_addend: int = BONUS_RED_5BIT) -> dict:
    """Classify every original opaque pixel at a fixed registered screen origin.

    The two explicitly tested pixel states are (1) exact source RGB and
    (2) source BGR555 red component +13 (clamped to 31), green/blue unchanged,
    expanded using the *exact* MesenCE 5-to-8 channel rule.
    A matching colour is a correspondence, not proof of its PPU producer.
    """
    size = obj.get("size")
    plane, rgba, alpha = obj.get("plane"), obj.get("rgba"), obj.get("alpha_mask")
    if (type(size) is not int or size != 64 or
            not isinstance(plane, bytes) or len(plane) != size*size or
            not isinstance(rgba, bytes) or len(rgba) != size*size*4 or
            not isinstance(alpha, bytes) or len(alpha) != size*size or
            sum(bool(p) for p in plane) != obj.get("opaque_count") or
            any((bool(p) != bool(a)) for p,a in zip(plane,alpha))):
        raise ValueError("original 2D OBJ source alpha/index data inconsistent")
    if (not isinstance(screen_rgb, bytes) or
            len(screen_rgb) != FRAME_WIDTH*FRAME_HEIGHT*3 or
            type(x) is not int or type(y) is not int or
            not 0 <= x <= FRAME_WIDTH-size or
            not 0 <= y <= FRAME_HEIGHT-size or
            type(horizontal_mirror) is not bool or
            type(red_addend) is not int or not 0 <= red_addend <= 31):
        raise ValueError("invalid bounded source screen registration or colour rule")
    direct = red_added = unaccounted = chroma = chroma_accounted = 0
    # 0 transparent, 1 direct, 2 altered red, 3 residual.
    classification = bytearray(size*size)
    examples = []
    for local_y in range(size):
        for local_x in range(size):
            source_x = size-1-local_x if horizontal_mirror else local_x
            src_pos = local_y*size+source_x
            if not alpha[src_pos]:
                continue
            rgba_at = src_pos*4
            source = tuple(rgba[rgba_at:rgba_at+3])
            if rgba[rgba_at+3] != 255:
                raise ValueError("original opaque OBJ RGBA lost alpha")
            r5 = source[0] >> 3
            if colour_5_to_8(r5) != source[0]:
                raise ValueError("original source red not produced by Mesen 5-bit expansion")
            is_chroma = max(source)-min(source) >= 35
            chroma += int(is_chroma)
            screen_pos = 3*((y+local_y)*FRAME_WIDTH+x+local_x)
            actual = tuple(screen_rgb[screen_pos:screen_pos+3])
            pos = local_y*size+local_x
            if actual == source:
                direct += 1
                classification[pos] = 1
                chroma_accounted += int(is_chroma)
            else:
                altered = (colour_5_to_8(min(31,r5+red_addend)),
                           source[1],source[2])
                if actual == altered and actual != source:
                    red_added += 1
                    classification[pos] = 2
                    chroma_accounted += int(is_chroma)
                else:
                    unaccounted += 1
                    classification[pos] = 3
                    if len(examples) < 5:
                        examples.append({
                            "source_pixel_local_xy": [local_x,local_y],
                            "source_RGB": list(source),
                            "completed_screen_RGB": list(actual),
                        })
    total = direct+red_added+unaccounted
    if not total or total != obj["opaque_count"]:
        raise ValueError("source opaque pixel accounting incomplete")
    return {
        "source_opaque_pixels": total,
        "direct_exact_RGB": direct,
        "red_5bit_plus_13_RGB": red_added,
        "unaccounted_RGB": unaccounted,
        "source_chromatic_pixels": chroma,
        "source_chromatic_pixels_accounted": chroma_accounted,
        "source_screen_pixel_classification_sha256": sha(bytes(classification)),
        "unaccounted_examples": examples,
    }


def analyse(frames: list[dict]) -> dict:
    if not isinstance(frames,list) or [row.get("tick") for row in frames] != list(TICKS):
        raise ValueError("authentic five consecutive source frames required")
    rows=[]
    for frame in frames:
        descriptors=decode_oam(frame["oam"])
        for slot, colour in ((96,"blue"),(97,"red")):
            descriptor=descriptors[slot]
            # This is the *held* end-frame OAM H flip bit. Its value alone
            # does not describe the upper viewport during earlier scanout.
            if descriptor["source_obj_hflip"] is not False:
                raise ValueError("held original OBJ H-flip identity differs")
            candidate=decode_source_obj(
                descriptor,frame["vram"],frame["cgram"],
                oam_mode=4,obj_base=0x6000,second_table_offset=0x1000,
            )
            x=descriptor["source_oam_x_signed9"]
            y=descriptor["source_oam_y_raw8"]+(
                BLUE_SCREEN_Y_OFFSET_FROM_HELD if slot==96
                else RED_SCREEN_Y_OFFSET_FROM_HELD)
            mirror=(slot==97)
            evidence=compare_opaque_pixels(
                candidate,frame["rgb"],x=x,y=y,horizontal_mirror=mirror,
            )
            inverted=compare_opaque_pixels(
                candidate,frame["rgb"],x=x,y=y,horizontal_mirror=not mirror,
            )
            displaced=compare_opaque_pixels(
                candidate,frame["rgb"],x=x+1,y=y,horizontal_mirror=mirror,
            )
            wrong_colour=compare_opaque_pixels(
                candidate,frame["rgb"],x=x,y=y,horizontal_mirror=mirror,
                red_addend=12,
            )
            rows.append({
                "original_emulator_tick":frame["tick"],
                "original_OAM_slot":slot,
                "source_colourway":colour,
                "source_held_OAM_xy":[descriptor["source_oam_x_signed9"],
                                      descriptor["source_oam_y_raw8"]],
                "source_held_OAM_horizontal_flip_bit":False,
                "tested_screen_origin_xy":[x,y],
                "independently_preobserved_screen_y_offset":y-descriptor["source_oam_y_raw8"],
                "postcapture_2D_diagnostic_mirror_applied":mirror,
                "source_pixel_correspondence":evidence,
                "opposite_orientation_unaccounted":inverted["unaccounted_RGB"],
                "one_pixel_x_shift_unaccounted":displaced["unaccounted_RGB"],
                "red_bonus_12_instead_of_13_unaccounted":wrong_colour["unaccounted_RGB"],
            })
    return {
        "schema":SCHEMA,
        "source_original_ROM_sha256":ROM_SHA,
        "source_Mesen_revision":MESEN_REVISION,
        "source_artifact_zip_sha256":SOURCE_ZIP_SHA,
        "original_emulator_ticks":list(TICKS),
        "observed_RGB_red_component_5bit_addend":BONUS_RED_5BIT,
        "original_2D_source_correspondence_per_frame":rows,
        "source_completed_P6_and_held_PPU_arrays_SHA_verified":True,
        "source_pixel_rgb_correspondence_with_two_observed_transform_states_verified":
            all(r["source_pixel_correspondence"]["unaccounted_RGB"]==0 for r in rows),
        "source_original_effective_per_scanline_OAM_flip_write_verified":False,
        "source_original_pixel_layer_winner_or_colour_math_register_verified":False,
        "source_1994_original_3D_geometry_rig_camera_verified":False,
        "source_to_2026_GLB_pose_mapping_verified":False,
        "owner_likeness_approved":False,
        "interpretation":
            "From authentic original held 2D OBJ tile/colour bytes, all opaque pixels"
            " coincide with completed-screen RGB after an observational horizontal"
            " reversal of red and/or source 5-bit red+13 (clamped) at affected pixels."
            " Blue is registered at held Y+7, red at held XY. The actual PPU"
            " split-screen OAM flag writes and final colour-math layer ownership"
            " remain unobserved; this is not proof of original 3D geometry.",
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-postcountdown-zip",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    opts=parser.parse_args()
    frames=source_archive_frames(opts.original_postcountdown_zip.read_bytes())
    result=analyse(frames)
    publish_text_once(opts.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
        "source_2D_correspondence_verified":
            result["source_pixel_rgb_correspondence_with_two_observed_transform_states_verified"],
        "per_source_racer_frame": [
            {"tick":r["original_emulator_tick"],"slot":r["original_OAM_slot"],
             "mirror":r["postcapture_2D_diagnostic_mirror_applied"],
             **{k:v for k,v in r["source_pixel_correspondence"].items()
                if k in ("source_opaque_pixels","direct_exact_RGB",
                         "red_5bit_plus_13_RGB","unaccounted_RGB")}}
            for r in result["original_2D_source_correspondence_per_frame"]
        ],
        "original_3D_geometry_verified":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
