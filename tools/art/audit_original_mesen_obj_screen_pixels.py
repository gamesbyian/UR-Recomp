#!/usr/bin/env python3
"""Independent 4bpp SNES OBJ-to-screen evidence from actual original MesenCE.

Reconstruct ONLY original 2D OBJ rasters and match their exact opaque colours
against the original completed-screen P6. A matched 2D sprite is not recovered
1994 3D anatomy, and one held PPU state cannot describe all scanline writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_racer_tile_lineage import decode_tile
from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-ORIGINAL-MESENCE-OBJ-EXACT-COLOUR-SCREEN-MATCH/1"
SOURCE_ZIP_SHA="7106fadd8d37b134f53501a251c281e88fd0336514a123ed70b1855aedf513f7"
SOURCE_REG_JSON_SHA="b3b80d032cbfc3a6fa225c8cb524172e924e633ae27916be37dc9e2293c2cf40"
ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SNES_MODE4_SIZE={False:16,True:64}
FRAME_SIZE=(256,239)
EXPECTED_REGISTERS={"ppu.oamMode":4,"ppu.oamBaseAddress":0x6000,
                    "ppu.oamAddressOffset":0x1000,"ppu.scanline":225}


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def colour_5_to_8(value:int)->int:
    if type(value) is not int or not 0<=value<=31:
        raise ValueError("original SNES colour component must be five-bit")
    # Exact MesenCE Core/Shared/ColorUtilities.h, default SNES video filter.
    return (value<<3)|(value>>2)


def bgr555_to_rgb(word:int)->tuple[int,int,int]:
    if type(word) is not int or not 0<=word<0x8000:
        raise ValueError("invalid original CGRAM BGR555")
    return (colour_5_to_8(word&31),
            colour_5_to_8((word>>5)&31),
            colour_5_to_8((word>>10)&31))


def tile_from_vram(vram:bytes,word_address:int)->tuple[int,...]:
    if not isinstance(vram,bytes) or len(vram)!=65536:
        raise ValueError("exact original 65536-byte video RAM required")
    if type(word_address) is not int:
        raise ValueError("source PPU tile address must be integral")
    # SnesPpu uses VRAM WORD addresses masked to 0x7fff. The source
    # snapshot is a byte array. A 4bpp tile has 16 words=32 bytes.
    base=word_address&0x7fff
    source=bytes(vram[(2*((base+i)&0x7fff))+b]
                 for i in range(16) for b in (0,1))
    return decode_tile(source)


def decode_source_obj(oam_row:dict,vram:bytes,cgram:bytes,*,oam_mode:int,
                      obj_base:int,second_table_offset:int)->dict:
    if (type(oam_mode) is not int or oam_mode!=4 or
            type(obj_base) is not int or obj_base!=0x6000 or
            type(second_table_offset) is not int or second_table_offset!=0x1000):
        raise ValueError("unverified original OBSEL/OBJ tile-base configuration")
    if not isinstance(cgram,bytes) or len(cgram)!=512:
        raise ValueError("exact original 512-byte CGRAM required")
    slot=oam_row.get("oam_slot")
    tileword=oam_row.get("source_oam_tile_word9")
    palette=oam_row.get("source_obj_palette_id0_to7")
    large=oam_row.get("source_obj_size_select_large")
    if (type(slot) is not int or not 0<=slot<128 or
            type(tileword) is not int or not 0<=tileword<512 or
            type(palette) is not int or not 0<=palette<8 or
            type(large) is not bool or
            type(oam_row.get("source_obj_hflip")) is not bool or
            type(oam_row.get("source_obj_vflip")) is not bool):
        raise ValueError("original source OAM descriptor malformed")
    size=SNES_MODE4_SIZE[large]
    raster=bytearray(size*size)
    rgba=bytearray(size*size*4)
    tiles={}
    for y in range(size):
        for x in range(size):
            sx=size-1-x if oam_row["source_obj_hflip"] else x
            sy=size-1-y if oam_row["source_obj_vflip"] else y
            # SNES OBJ tile rows and columns wrap independently within the
            # 16x16 tile-number page, exactly as SnesPpu::FetchSpriteAttributes.
            tile=((((tileword&255)>>4)+(sy//8))&15)<<4
            tile|=(((tileword&15)+(sx//8))&15)
            addr=(obj_base+(tile<<4)+(second_table_offset if tileword&0x100 else 0))&0x7fff
            if addr not in tiles:
                tiles[addr]=tile_from_vram(vram,addr)
            ci=tiles[addr][(sy&7)*8+(sx&7)]
            pos=y*size+x
            raster[pos]=ci
            if ci==0:
                continue
            cgindex=128+palette*16+ci
            word=cgram[cgindex*2]|(cgram[cgindex*2+1]<<8)
            r,g,b=bgr555_to_rgb(word&0x7fff)
            rgba[pos*4:pos*4+4]=bytes([r,g,b,255])
    return {
        "slot":slot,"size":size,"plane":bytes(raster),"rgba":bytes(rgba),
        "alpha_mask":bytes(1 if index else 0 for index in raster),
        "source_palette_id":palette,
        "opaque_count":sum(ci!=0 for ci in raster),
        "tile_word_address_count":len(tiles),
        "tile_word_addresses":sorted(tiles),
    }


def p6_screen(source:bytes)->bytes:
    header=b"P6\n256 239\n255\n"
    if (not isinstance(source,bytes) or not source.startswith(header) or
            len(source)!=len(header)+FRAME_SIZE[0]*FRAME_SIZE[1]*3):
        raise ValueError("exact original 256x239 P6 screen required")
    return source[len(header):]


def best_opaque_matches(obj:dict,rgb:bytes,*,upper:bool)->dict:
    if len(rgb)!=FRAME_SIZE[0]*FRAME_SIZE[1]*3:
        raise ValueError("source original screen RGB dimensions invalid")
    size=obj["size"]
    rgba=obj["rgba"]
    points=[(x,y,rgba[4*(y*size+x):4*(y*size+x)+3])
            for y in range(size) for x in range(size)
            if rgba[4*(y*size+x)+3]]
    if not points:
        raise ValueError("no opaque source OBJ pixels to match")
    max_y=110 if upper else 175
    min_y=0 if upper else 120
    best=(-1,None,None)
    for y0 in range(min_y,max_y+1):
        if y0+size>FRAME_SIZE[1]:
            continue
        for x0 in range(76,171):
            if x0+size>FRAME_SIZE[0]:
                continue
            exact=sum(rgb[3*((y0+y)*256+x0+x):3*((y0+y)*256+x0+x)+3]==c
                      for x,y,c in points)
            if exact>best[0] or (exact==best[0] and (y0,x0)<(best[2],best[1])):
                best=(exact,x0,y0)
    return {"exact_opaque_RGB_pixel_matches":best[0],
            "total_source_OBJ_opaque_pixels":len(points),
            "source_screen_x":best[1],"source_screen_y":best[2],
            "source_screen_region":"upper" if upper else "lower",
            "complete_pixel_match":best[0]==len(points)}


def audit_source(zip_file:Path,register_summary:dict)->dict:
    archive_bytes=zip_file.read_bytes()
    if sha(archive_bytes)!=SOURCE_ZIP_SHA:
        raise ValueError("not the authenticated original no-skip Mesen source ZIP")
    if (register_summary.get("source_register_json_sha256")!=SOURCE_REG_JSON_SHA or
            register_summary.get("source_original_emulator_artifact_zip_sha256")!=
            "849abdaf241c5951e8b1627c0c9622989d421266bfcdd1c47ac2918c5c81df21" or
            register_summary.get("source_registers_at_both_ticks") is None):
        raise ValueError("original serialized source register proof differs")
    registers=register_summary["source_registers_at_both_ticks"]
    for name,value in EXPECTED_REGISTERS.items():
        if type(registers.get(name)) is not type(value) or registers[name]!=value:
            raise ValueError("original source SNES PPU register changed: "+name)
    with zipfile.ZipFile(zip_file) as z:
        first={}
        for run in ("first","second"):
            prefix="art4k-no-skip-"+run+"/"
            manifest=json.loads(z.read(prefix+"manifest.json"))
            if (manifest.get("original_USA_ROM_sha256")!=ROM_SHA or
                    manifest.get("source_original_snes_frame_skipping_disabled_requested",False) is not False):
                raise ValueError("original source emulator provenance invalid")
            frame=next((r for r in manifest["frames"] if r.get("emulator_bridge_frame")==1219),None)
            if not isinstance(frame,dict):
                raise ValueError("authentic original frame 1219 missing")
            raw={}
            for name,size in (("oam",544),("vram",65536),("cgram",512)):
                rec=frame["raw_original_snes_ppu_memory"][name]
                raw[name]=z.read(prefix+rec["relative_file"])
                if len(raw[name])!=size or sha(raw[name])!=rec["sha256"]:
                    raise ValueError("original source PPU byte SHA mismatch")
            display=frame["original_emulator_held_display_P6"]
            ppm=z.read(prefix+display["relative_file"])
            if sha(ppm)!=display["sha256"]:
                raise ValueError("original source screen SHA mismatch")
            raw["rgb"]=p6_screen(ppm)
            first[run]=raw
        if any(first["first"][key]!=first["second"][key] for key in ("oam","vram","cgram","rgb")):
            raise ValueError("original no-skip raw source or framebuffer did not repeat")
    source=first["first"]
    oam=decode_oam(source["oam"])
    results={}
    source_objects={}
    for slot,target in ((96,"lower"),(97,"upper")):
        obj=decode_source_obj(oam[slot],source["vram"],source["cgram"],
               oam_mode=4,obj_base=0x6000,second_table_offset=0x1000)
        source_objects[slot]=obj
        upper=best_opaque_matches(obj,source["rgb"],upper=True)
        lower=best_opaque_matches(obj,source["rgb"],upper=False)
        expected={"upper":(104,47),"lower":(104,160)}[target]
        chosen=upper if target=="upper" else lower
        if (not chosen["complete_pixel_match"] or
                (chosen["source_screen_x"],chosen["source_screen_y"])!=expected):
            raise ValueError("original source sprite pixels not fully matched")
        rival=lower if target=="upper" else upper
        if rival["complete_pixel_match"]:
            raise ValueError("ambiguous original split-screen sprite correspondence")
        results[str(slot)]={
            "original_OAM_slot":slot,
            "source_original_OAM_held_x":oam[slot]["source_oam_x_signed9"],
            "source_original_OAM_held_y":oam[slot]["source_oam_y_raw8"],
            "source_original_OBJ_pixel_size":[obj["size"],obj["size"]],
            "source_original_OBJ_palette_id":obj["source_palette_id"],
            "source_4bpp_indices_sha256":sha(obj["plane"]),
            "source_RGBA_sha256":sha(obj["rgba"]),
            "source_alpha_mask_sha256":sha(obj["alpha_mask"]),
            "source_opaque_pixel_count":obj["opaque_count"],
            "original_sprite_tile_count":obj["tile_word_address_count"],
            "matching_viewport":target,
            "same_screen_full_opaque_RGB_match":chosen,
            "other_viewport_best_opaque_RGB_match":rival,
        }
    a,b=source_objects[96]["alpha_mask"],source_objects[97]["alpha_mask"]
    intersection=sum(bool(x) and bool(y) for x,y in zip(a,b))
    union=sum(bool(x) or bool(y) for x,y in zip(a,b))
    return {
        "schema":SCHEMA,
        "original_two_racer_2D_alpha_shape_overlap":{
            "intersection_pixels":intersection,
            "union_pixels":union,
            "blue_only_pixels":sum(bool(x) and not bool(y) for x,y in zip(a,b)),
            "red_only_pixels":sum(bool(y) and not bool(x) for x,y in zip(a,b)),
            "shared_shape_iou":intersection/union,
            "source_alpha_planes_identical":a==b,
        },
        "original_source_PPU_archive_SHA256":SOURCE_ZIP_SHA,
        "original_PPU_register_numeric_source_sha256":SOURCE_REG_JSON_SHA,
        "original_USA_ROM_sha256":ROM_SHA,
        "original_executed_emulator_tick":1219,
        "source_screen_original_rgb_pixels":[256,239],
        "source_original_replays_are_pixel_and_PPU_identical":True,
        "verified_complete_source_2D_OBJ_to_original_screen_pixel_match":True,
        "source_OBJ_and_screen_correspondence":results,
        "source_per_scanline_OAM_register_writes_independently_captured":False,
        "original_source_1994_3D_mesh_camera_or_skeleton_recovered":False,
        "source_to_2026_GLb_pose_correspondence_verified":False,
        "original_screen_countdown_overlay_present":True,
        "owner_likeness_approved":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-no-skip-zip",type=Path,required=True)
    p.add_argument("--source-register-summary",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=audit_source(args.original_no_skip_zip,
                        json.loads(args.source_register_summary.read_text()))
    publish_text_once(args.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
        "source_2d_match_verified":result["verified_complete_source_2D_OBJ_to_original_screen_pixel_match"],
        "obj_matches":{k:v["same_screen_full_opaque_RGB_match"] for k,v in
                       result["source_OBJ_and_screen_correspondence"].items()},
        "original_3d_recovered":False},sort_keys=True))


if __name__=="__main__":
    main()
