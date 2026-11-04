#!/usr/bin/env python3
"""Original Mesen24 fixed OAM racer slots versus actual 4bpp VRAM payload edits.

Source 2D VRAM writer *identity* is unknown. No 1994 3D model or camera proven.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

from tools.art.audit_original_mesen_contiguous_24 import audit as audit_mesen
from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_mesen_obj_screen_pixels import decode_source_obj
from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-AUTHENTIC-MESEN24-FIXED-OBJ-VRAM-4BPP-TILE-PAYLOAD/1"
SOURCE_ZIP_SHA="28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6"
TICKS=tuple(range(1601,1625))
ROLES={"blue":(96,136,4),"red":(97,0,3)}


def sha(source:bytes)->str:
    return hashlib.sha256(source).hexdigest()


def tile_bytes(vram:bytes,word_address:int)->bytes:
    if (not isinstance(vram,bytes) or len(vram)!=65536 or
            type(word_address) is not int or not 0<=word_address<0x8000):
        raise ValueError("source 4bpp tile needs exact 64KiB VRAM and 15-bit word address")
    return bytes(vram[2*((word_address+i)&0x7fff)+lane]
                 for i in range(16) for lane in (0,1))


def audit(archive:bytes)->dict:
    if len(archive)>1_000_000 or sha(archive)!=SOURCE_ZIP_SHA:
        raise ValueError("source must be exact preserved Mesen 24-tick archive")
    frozen=audit_mesen(archive)
    if (frozen["source_canonical_archive_sha256"]!=SOURCE_ZIP_SHA or
            frozen["new_source_actual_consecutive_no_skip_Mesen_ticks"]!=list(TICKS)):
        raise ValueError("original execution/PPU provenance differs")
    by_player={}
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for who,(slot,expected_word,expected_palette) in ROLES.items():
            samples=[]
            for tick in TICKS:
                oam=decode_oam(z.read(f"frame-{tick:06d}-oam.bin"))[slot]
                vram=z.read(f"frame-{tick:06d}-vram.bin")
                cgram=z.read(f"frame-{tick:06d}-cgram.bin")
                obj=decode_source_obj(oam,vram,cgram,oam_mode=4,
                                      obj_base=0x6000,second_table_offset=0x1000)
                if (oam["source_oam_tile_word9"]!=expected_word or
                        obj["source_palette_id"]!=expected_palette or
                        oam["source_obj_size_select_large"] is not True or
                        oam["source_obj_hflip"] is not False or
                        oam["source_obj_vflip"] is not False or
                        obj["size"]!=64 or obj["slot"]!=slot):
                    raise ValueError("source racer OAM tileword, palette, size or flip changed")
                addresses=obj["tile_word_addresses"]
                if len(addresses)!=64:
                    raise ValueError("expected original 8x8 set of 4bpp OBJ tiles")
                payload=tuple(tile_bytes(vram,addr) for addr in addresses)
                if any(len(tile)!=32 for tile in payload):
                    raise ValueError("original 4bpp tile should be 32 bytes")
                cgram_start=128+16*expected_palette
                palette_bytes=cgram[2*cgram_start:2*(cgram_start+16)]
                if len(palette_bytes)!=32:
                    raise ValueError("source sixteen-colour OBJ palette missing")
                samples.append({"tick":tick,"x":oam["source_oam_x_signed9"],
                    "y":oam["source_oam_y_raw8"],"tile_addresses":addresses,
                    "tile_payload":payload,"palette_bytes":palette_bytes,
                    "index_sha":sha(obj["plane"])})
            first=samples[0]
            if any(s["tile_addresses"]!=first["tile_addresses"] or
                   s["palette_bytes"]!=first["palette_bytes"] for s in samples):
                raise ValueError("original sprite VRAM pointers or CGRAM palette changed")
            edges=[]
            for a,b in zip(samples,samples[1:]):
                raw_changes=sum(sum(v!=w for v,w in zip(x,y))
                        for x,y in zip(a["tile_payload"],b["tile_payload"]))
                tile_changes=sum(x!=y for x,y in zip(a["tile_payload"],b["tile_payload"]))
                edges.append({"from_original_bridge_tick":a["tick"],
                    "to_original_bridge_tick":b["tick"],
                    "source_racer_4bpp_tile_payload_changed_bytes":raw_changes,
                    "source_racer_8x8_tile_payloads_changed":tile_changes,
                    "source_index_plane_changed":a["index_sha"]!=b["index_sha"],
                    "source_palette_CGRAM_changed_bytes":sum(x!=y
                        for x,y in zip(a["palette_bytes"],b["palette_bytes"]))})
            if (len(edges)!=23 or any(e["source_racer_4bpp_tile_payload_changed_bytes"]<1 or
                  not e["source_index_plane_changed"] or
                  e["source_palette_CGRAM_changed_bytes"]!=0 for e in edges)):
                raise ValueError("actual consecutive VRAM writer witness no longer matches")
            by_player[who]={
                "actual_source_oam_slot":slot,
                "fixed_oam_source_tileword9":expected_word,
                "fixed_oam_source_palette_id":expected_palette,
                "fixed_source_OAM_large_64px_and_no_flips":True,
                "source_OAM_held_positions_by_tick":[
                    {"tick":s["tick"],"oam_x":s["x"],"oam_y":s["y"]} for s in samples],
                "unique_fixed_original_tile_word_addresses":first["tile_addresses"],
                "tile_count":64,
                "backing_4bpp_payload_bytes_per_observation":2048,
                "source_relevant_palette_CGRAM_unchanged_24_ticks":True,
                "all_23_original_adjacent_source_tile_payloads_change":True,
                "all_23_original_adjacent_source_index_planes_change":True,
                "source_23_edge_byte_changes_total":sum(e["source_racer_4bpp_tile_payload_changed_bytes"] for e in edges),
                "source_23_edge_changed_tile_instances_total":sum(e["source_racer_8x8_tile_payloads_changed"] for e in edges),
                "source_23_edges":edges,
            }
    return {
        "schema":SCHEMA,
        "original_24tick_source_ZIP_sha256":SOURCE_ZIP_SHA,
        "original_USA_rom_executed_Mesen_ticks":list(TICKS),
        "source_prior_register_mode4_base6000_offset1000_assumed_fixed":True,
        "source_OBSEL_registers_independently_read_each_new_tick":False,
        "source_OAM_positions_can_change_while_tileword_and_palette_stay_fixed":True,
        "original_2d_sprite_changes_explained_by_source_vram_payload_updates_under_stable_tile_addresses":True,
        "original_CPU_DMA_PPU_specific_writer_identified":False,
        "original_1994_3d_mesh_rig_camera_or_animation_source_recovered":False,
        "owner_likeness_approved":False,
        "per_original_source_racer":by_player,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    result=audit(args.source_zip.read_bytes())
    publish_text_once(args.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({who:{
        "total_byte_deltas":r["source_23_edge_byte_changes_total"],
        "total_changed_tile_instances":r["source_23_edge_changed_tile_instances_total"],
        "stable_tileword":r["fixed_oam_source_tileword9"]
        } for who,r in result["per_original_source_racer"].items()},sort_keys=True))


if __name__=="__main__":
    main()
