#!/usr/bin/env python3
"""Recover source-executed racer primary presentation IDs from exact ROM 4bpp tiles.

Source 24 authentic Mesen PPU ticks, one 1536-entry ROM-defined 24x64 lattice.
No emulator replay, 3D pose/camera inference, palette-to-part guess or GLB fit.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import zipfile

from tools.art.audit_original_mesen_contiguous_24 import audit as audit_mesen
from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_mesen_obj_screen_pixels import decode_source_obj
from tools.art.no_replace_report import publish_text_once
from tools.extract_racer_presentation_family import (
    frame_pointer, decode_frame_record, decode_piece_mapping,
    piece_source_tile, lorom_offset, OCCUPANCY_BITS,
)
from tools.art.audit_original_mesen24_racer_vram_payload import tile_bytes

SCHEMA="UR-ART4K-AUTHENTIC-MESEN24-ORIGINAL-ROM-EXACT-POSE-GRID/1"
ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SOURCE_SHA="28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6"
TICKS=tuple(range(1601,1625))
PRIMARY_IDS=range(24*64)
ROLES={"blue":(96,136,4),"red":(97,0,3)}
ROW_TILE_INDEXES=tuple(y*8+x for y in range(5) for x in range(1,7))

# Code bytes from the *same authenticated original USA ROM*.
# Validate discrete phase update, 6-bit tilt index, frame-id synthesis,
# pointer table resolution and the DMA 32-byte producer/consumer entry seams.
# These are selected source-code witness anchors, not a proof of every branch.
ROM_CPU_ANCHORS={
    "phase_read_add_83_EE53":(0x83,0xEE53,"ad830f186500"),
    "phase_24_wrap_83_EE5E":(0x83,0xEE5E,"c91800300c38e91800"),
    "phase_mul64_83_EED9":(0x83,0xEED9,"ad830f0a0a0a0a0a0a18"),
    "phase_plus_angle_83_EEE6":(0x83,0xEEE6,"186d770f"),
    "frame_id_working_83_EF0C":(0x83,0xEF0C,"8c970f"),
    "angle_mod64_83_F086":(0x83,0xF086,"293f008d770f"),
    "source_frame_ids_83_F0D7":(0x83,0xF0D7,"ace90f8c0002"),
    "source_frame_ptr_mul3_83_F296":(0x83,0xF296,"e21085000a186500"),
    "source_frame_ptr_bank23_83_F2A4":(0x83,0xF2A4,"8ba0205aaba002"),
    "DMA_tile_source_83_F20F":(0x83,0xF20F,"852aeb0a0a0a0a0a090080"),
    "DMA_target_83_F264":(0x83,0xF264,"a526691000852699e916"),
    "NMI_VRAM_addr_82_B8F4":(0x82,0xB8F4,"ade916898000"),
}


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def original_code_contract(rom:bytes)->dict:
    if len(rom)!=2*1024*1024 or sha(rom)!=ROM_SHA:
        raise ValueError("wrong authentic original USA ROM or byte length")
    rows={}
    for name,(bank,addr,expected) in ROM_CPU_ANCHORS.items():
        n=len(expected)//2
        actual=rom[lorom_offset(bank,addr):lorom_offset(bank,addr)+n].hex()
        if actual!=expected:
            raise ValueError(f"original ROM executable witness mismatch at {bank:02X}:{addr:04X}")
        rows[name]={"cpu":f"{bank:02X}:{addr:04X}",
                    "source_code_bytes_sha256":sha(bytes.fromhex(actual)),
                    "byte_length":n}
    return rows


def source_frame_tiles(rom:bytes)->tuple[tuple[bytes,...],...]:
    """Decode all 1536 distinct table-defined original primary packed frames.

    Each returns exactly 30 32-byte tiles from the original ROM's stage source.
    The 5x6 occupancy uses the existing audited packed-word decoder.
    """
    if len(rom)!=2*1024*1024 or sha(rom)!=ROM_SHA:
        raise ValueError("wrong original USA ROM")
    blank=piece_source_tile(rom,0)[0]
    result=[]
    pointers=set()
    for frame_id in PRIMARY_IDS:
        ptr=frame_pointer(rom,frame_id)
        offset=lorom_offset(ptr.source_bank,ptr.source_addr)
        if not 0<=offset<len(rom)-3:
            raise ValueError("ROM frame pointer outside original file")
        if (ptr.source_bank,ptr.source_addr) in pointers:
            raise ValueError("duplicate original frame pointer")
        pointers.add((ptr.source_bank,ptr.source_addr))
        header=rom[offset:offset+4]
        if len(header)!=4 or header[3]&0x03:
            raise ValueError("noncanonical 30-cell source header")
        occupied=sum(bool(header[k]&(1<<bit)) for k,bit in OCCUPANCY_BITS)
        length=4+2*occupied
        record_bytes=rom[offset:offset+length]
        if len(record_bytes)!=length:
            raise ValueError("truncated original packed record")
        if frame_id < 1535:
            next_ptr=frame_pointer(rom,frame_id+1)
            nxt=lorom_offset(next_ptr.source_bank,next_ptr.source_addr)
            gap=nxt-(offset+length)
            if gap and not (frame_id==1079 and
                    next_ptr.source_bank==ptr.source_bank+1 and
                    rom[offset+length:nxt]==bytes.fromhex("ffffff00")):
                raise ValueError("original ROM packed record boundary mismatch")
        pieces=decode_piece_mapping(decode_frame_record(record_bytes))
        if len(pieces)!=occupied:
            raise ValueError("inconsistent 30-cell packed-word occupancy")
        tile_words=iter(int(p["word_hex"],16) for p in pieces)
        tiles=[]
        for k,bit in OCCUPANCY_BITS:
            active=bool(header[k]&(1<<bit))
            tiles.append(piece_source_tile(rom,next(tile_words))[0]
                         if active else blank)
        if len(tiles)!=30 or any(len(t)!=32 for t in tiles):
            raise ValueError("original 5x6 primary frame not 30 4bpp tiles")
        result.append(tuple(tiles))
    if len(result)!=1536 or len(pointers)!=1536:
        raise ValueError("not an exhaustive unique 24x64 primary ROM grid")
    return tuple(result)


def recover_unique_identity(observed:tuple[bytes,...],
                            candidates:tuple[tuple[bytes,...],...])->dict:
    if len(observed)!=30 or any(not isinstance(x,bytes) or len(x)!=32 for x in observed):
        raise ValueError("need exactly 30 raw observed 32-byte source tiles")
    if len(candidates)!=1536 or any(len(c)!=30 for c in candidates):
        raise ValueError("expected complete 1536-frame original ROM source grid")
    scores=[sum(a==b for a,b in zip(observed,row)) for row in candidates]
    winners=[n for n,score in enumerate(scores) if score==30]
    if len(winners)!=1:
        raise ValueError(f"original source tile identity unresolved: {len(winners)} perfect frame matches")
    winner=winners[0]
    alternate=max(v for n,v in enumerate(scores) if n!=winner)
    return {
        "source_primary_frame_id":winner,
        "source_primary_frame_hex":f"0x{winner:04X}",
        "source_primary_phase_index":winner//64,
        "source_primary_angle_index":winner%64,
        "source_original_ROM_matched_8x8_tile_count":30,
        "source_original_ROM_candidate_count":len(candidates),
        "next_best_nonidentical_ROM_frame_matched_tiles":alternate,
        "unique_perfect_tile_match_count":len(winners),
        "source_selected_960_4bpp_bytes_sha256":sha(b"".join(observed)),
    }


def decode_4bpp_tile8(raw:bytes)->bytes:
    """Independent SNES planar 4bpp tile decode: 8 rows x 8 index pixels."""
    if not isinstance(raw,bytes) or len(raw)!=32:
        raise ValueError("expected one original raw 32-byte 8x8 4bpp tile")
    result=bytearray(64)
    for y in range(8):
        p0,p1,p2,p3=raw[2*y],raw[2*y+1],raw[16+2*y],raw[17+2*y]
        for x in range(8):
            bit=7-x
            result[8*y+x]=(
                ((p0>>bit)&1)|(((p1>>bit)&1)<<1)|
                (((p2>>bit)&1)<<2)|(((p3>>bit)&1)<<3))
    return bytes(result)


def render_original_primary_sprite64(tiles:tuple[bytes,...])->bytes:
    """Render exact ROM 5x6 packed source into original 64x64 source indexes.

    The 30 cells occupy tile rows 0..4 and columns 1..6. All other
    34 tiles remain transparent index 0, authenticated by source comparison.
    """
    if len(tiles)!=30:
        raise ValueError("expected precisely 30 original 4bpp tiles")
    raster=bytearray(64*64)
    for n,raw in enumerate(tiles):
        cell=decode_4bpp_tile8(raw)
        y0=8*(n//6)
        x0=8*(n%6+1)
        for j in range(8):
            at=(y0+j)*64+x0
            raster[at:at+8]=cell[j*8:(j+1)*8]
    return bytes(raster)


def audit(rom:bytes,source_archive:bytes)->dict:
    if len(source_archive)>1_000_000 or sha(source_archive)!=SOURCE_SHA:
        raise ValueError("wrong canonical Mesen source archive")
    src=audit_mesen(source_archive)
    if (src["source_canonical_archive_sha256"]!=SOURCE_SHA or
            src["new_source_actual_consecutive_no_skip_Mesen_ticks"]!=list(TICKS)):
        raise ValueError("original source chronology contract changed")
    code=original_code_contract(rom)
    candidates=source_frame_tiles(rom)
    player={}
    with zipfile.ZipFile(io.BytesIO(source_archive)) as z:
        for who,(slot,expected_oam_tile,expected_palette) in ROLES.items():
            frames=[]
            first_addresses=None
            for tick in TICKS:
                desc=decode_oam(z.read(f"frame-{tick:06d}-oam.bin"))[slot]
                vram=z.read(f"frame-{tick:06d}-vram.bin")
                cgram=z.read(f"frame-{tick:06d}-cgram.bin")
                obj=decode_source_obj(desc,vram,cgram,
                       oam_mode=4,obj_base=0x6000,second_table_offset=0x1000)
                if (obj["slot"]!=slot or obj["size"]!=64 or
                        obj["source_palette_id"]!=expected_palette or
                        desc["source_oam_tile_word9"]!=expected_oam_tile or
                        desc["source_obj_hflip"] or desc["source_obj_vflip"]):
                    raise ValueError("unexpected original racer source OAM identity")
                addrs=tuple(obj["tile_word_addresses"][i] for i in ROW_TILE_INDEXES)
                if len(addrs)!=30 or len(set(addrs))!=30:
                    raise ValueError("not a distinct 5x6 source tile footprint")
                if first_addresses is None:
                    first_addresses=addrs
                elif first_addresses!=addrs:
                    raise ValueError("original source tile footprint moved in VRAM")
                observed=tuple(tile_bytes(vram,addr) for addr in addrs)
                result=recover_unique_identity(observed,candidates)
                original_64=render_original_primary_sprite64(
                    candidates[result["source_primary_frame_id"]])
                if original_64!=obj["plane"]:
                    raise ValueError("ROM primary pose fails exact 64x64 source index pixel oracle")
                result["authentic_original_bridge_tick"]=tick
                result["source_held_OAM_local_index_plane_sha256"]=sha(obj["plane"])
                result["source_ROM_reconstructed_64x64_index_plane_sha256"]=sha(original_64)
                result["source_ROM_exact_source_index_pixel_matches"]=4096
                frames.append(result)
            deltas=[(b["source_primary_phase_index"]-a["source_primary_phase_index"])%24
                    for a,b in zip(frames,frames[1:])]
            angles=[f["source_primary_angle_index"] for f in frames]
            player[who]={
                "source_original_OAM_slot":slot,
                "source_original_OAM_tile_word9":expected_oam_tile,
                "source_original_OBJ_palette_id":expected_palette,
                "original_OAM_size_and_source_flips_stable":True,
                "original_source_5x6_tile_VRAM_word_addresses":list(first_addresses),
                "source_24_unique_per_tick_ROM_primary_frame_IDs":frames,
                "actual_source_23_modulo24_phase_steps":deltas,
                "actual_phase_step_histogram":{str(k):deltas.count(k) for k in sorted(set(deltas))},
                "actual_source_angle_index_histogram":{
                    str(k):angles.count(k) for k in sorted(set(angles))},
                "all_24_source_primary_frame_IDs_exact_unique_matches":True,
            }
    return {
        "schema":SCHEMA,
        "original_usa_ROM_sha256":ROM_SHA,
        "original_Mesen24_source_archive_sha256":SOURCE_SHA,
        "original_usa_rom_EXACT_24_by_64_primary_state_grid":True,
        "original_primary_frame_pointer_table_SHA256":sha(rom[lorom_offset(0x20,0x8000):
                                          lorom_offset(0x20,0x8000)+1536*3]),
        "original_rom_1536_distinct_valid_frame_records_verified":True,
        "all_48_observed_primary_5x6_sprite_frames_unique_perfect_rom_match":True,
        "all_48_original_64x64_source_index_images_pixel_exact_from_ROM":True,
        "original_source_64x64_index_pixel_samples_matched_total":48*64*64,
        "original_source_remaining_34_tiles_per_sprite_zero_index_verified":True,
        "original_executed_24_tick_frames_are_exploratory_not_prospective_blind":True,
        "original_racer_1994_art_3D_camera_joint_angles_mesh_or_rig_recovered":False,
        "2026_candidate_3D_rig_physical_angle_scale_independently_calibrated":False,
        "complete_64tile_held_OBJ_graphics_reconstructed_from_primary_5x6_only":False,
        "original_65816_selected_executable_byte_witnesses":code,
        "per_original_source_racer":player,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom",required=True,type=Path)
    p.add_argument("--original-source-zip",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    report=audit(args.rom.read_bytes(),args.original_source_zip.read_bytes())
    publish_text_once(args.out,json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({who:{
        "unique_perfect":len(data["source_24_unique_per_tick_ROM_primary_frame_IDs"]),
        "phase_step_histogram":data["actual_phase_step_histogram"],
        "angle_histogram":data["actual_source_angle_index_histogram"]}
        for who,data in report["per_original_source_racer"].items()},sort_keys=True))


if __name__=="__main__":
    main()
