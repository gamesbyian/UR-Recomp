#!/usr/bin/env python3
"""Revalidate immutable 24 consecutive Mesen source OBJ observations, no ROM run.

This is genuine executed original 2D SNES OAM/VRAM/CGRAM evidence; it does NOT
identify a 1994 3D camera, skeletal rig, authored frame classes, original
per-scanline PPU ownership, physical wheel contact or approved replacement.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import zipfile

from tools.art.audit_original_mesen_oam_descriptors import decode_oam, descriptor
from tools.art.audit_original_mesen_obj_screen_pixels import decode_source_obj, p6_screen
from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-ACTUAL-24-CONTIGUOUS-MESEN-SOURCE-OBJ-CHRONOLOGY/1"
ZIP_SHA="28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6"
MANIFEST_SHA="35c04eb98be0facd1cc3bc81a3cc08db4a1ebba7f29a0962a9f7447d29c61fe3"
ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
REPLAY_SHA="28f2842fd262030e434b3aef88eb360f74de94fbf558f0eb0ba8edce645fb490"
MESEN_REV="a60e79feb4d6dcced5922d636f9211837d01e381"
MESEN_BINARY_SHA="80ff379c31eedb8d5d7b9f5b1857ade463c584166de3d5e36192242ac2ed71ee"
TICKS=tuple(range(1601,1625))
ANCHORS={
 1601:("0ac217805cbc9534001fa83834982734cc4a4d36221c49f027eeca658d39ef22",
       "0a8a82a976c61a196825b7fb6443cd842ae308db4fc729ad8e9bea2e5589ad64",
       "9a102a7214e1261d94b321a3324858ae1bc8f3ad9c6474e0e7abe04671ebb91c",
       "2d07dc1601fd604b4af33865f94538c1b5b664f8b22de9992cf775d1da103a6e"),
 1607:("ae42efdd380d2e55fcee9cef3dfa8afded3c96900a8bb30e656873b1d4d0d84b",
       "16c2bc34132b19333fd274d8e925f701e66c815b6ed208d54f3d564999ae289e",
       "30344709a2807f1fc7f838c2f7534228d0e078de9ce9cdda5786e3d0d3723544",
       "a639d1cbf1d0856fe6fbd2eace0243fe65d65ace4dde419d8d15520c86943a1d"),
 1618:("9b5052f5c65a1b848e267074192cb1b4b1bf907af2e0121f6205b9df7b3f83ac",
       "e2505928a417c479a93c4fe6e651b3adf83cecf82e28bcc2e162df7d9d5a1cfa",
       "d7d94095c68a37a0838665f7206820f07a9592973ba27922c5daba3cae1b0aad",
       "7c77f80e9affa767186bd9edab2f5fed923f854c0b9def751ee3b2cf127de929"),
}
REGIONS={"oam":544,"vram":65536,"cgram":512}
SLOTS={"blue":96,"red":97}


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def compare_masks(a:bytes,b:bytes)->int:
    if len(a)!=4096 or len(b)!=4096 or set(a)-{0,1} or set(b)-{0,1}:
        raise ValueError("exact binary 64x64 source OBJ masks required")
    return sum(x!=y for x,y in zip(a,b))


def compare_rgba(a:bytes,b:bytes)->int:
    if len(a)!=64*64*4 or len(b)!=len(a):
        raise ValueError("exact 64x64 source RGBA required")
    return sum(a[i:i+4]!=b[i:i+4] for i in range(0,len(a),4))


def summarize(rows:list[dict])->dict:
    if len(rows)!=len(TICKS) or [r["tick"] for r in rows]!=list(TICKS):
        raise ValueError("not one row for each authentic contiguous tick")
    edges=[]
    for before,after in zip(rows,rows[1:]):
        edges.append({
          "from_tick":before["tick"],"to_tick":after["tick"],
          "source_alpha_xor_pixels":compare_masks(before["_alpha"],after["_alpha"]),
          "source_rgba_changed_pixels":compare_rgba(before["_rgba"],after["_rgba"]),
          "source_index_plane_changed_pixels":sum(
              x!=y for x,y in zip(before["_plane"],after["_plane"])),
          "source_oam_descriptor_changed":before["_descriptor"]!=after["_descriptor"],
        })
    alpha_changes=[r["source_alpha_xor_pixels"] for r in edges]
    rgba_changes=[r["source_rgba_changed_pixels"] for r in edges]
    return {
      "observations":len(rows),
      "authentic_adjacent_source_edges":len(edges),
      "source_alpha_changed_edges":sum(v>0 for v in alpha_changes),
      "source_alpha_held_edges":sum(v==0 for v in alpha_changes),
      "source_rgba_changed_edges":sum(v>0 for v in rgba_changes),
      "source_rgba_held_edges":sum(v==0 for v in rgba_changes),
      "distinct_source_alpha_masks":len({r["source_alpha_sha256"] for r in rows}),
      "distinct_source_rgba":len({r["source_rgba_sha256"] for r in rows}),
      "alpha_changed_pixels_min":min(alpha_changes),
      "alpha_changed_pixels_median":statistics.median(alpha_changes),
      "alpha_changed_pixels_max":max(alpha_changes),
      "source_4bpp_observations":[{k:v for k,v in r.items() if not k.startswith("_")} for r in rows],
      "authentic_adjacent_source_2d_transitions":edges,
    }


def audit(raw:bytes)->dict:
    if len(raw)>1_000_000 or sha(raw)!=ZIP_SHA:
        raise ValueError("not the preserved actual 24-tick original Mesen source archive")
    from io import BytesIO
    expected={"manifest.json"}|{
        f"frame-{t:06d}-{p}.{ext}" for t in TICKS for p,ext in
        (("oam","bin"),("vram","bin"),("cgram","bin"),("held-display","ppm"))}
    with zipfile.ZipFile(BytesIO(raw)) as z:
        entries=z.infolist()
        if (len(entries)!=97 or {x.filename for x in entries}!=expected or
                sum(x.file_size for x in entries)>7_000_000 or
                any(x.is_dir() or x.flag_bits & 1 for x in entries)):
            raise ValueError("unrecognized or unsafe Mesen member inventory")
        manraw=z.read("manifest.json")
        if sha(manraw)!=MANIFEST_SHA:
            raise ValueError("Mesen original manifest SHA changed")
        man=json.loads(manraw)
        if (man.get("schema")!="UR-ART4K-MESENCE-LIVE-RAW-SNES-PPU-STATES/1" or
            man.get("actual_raw_SNES_sprite_RAM_VRAM_CGRAM_snapshots")!=24 or
            man.get("source_requested_capture_ticks")!=list(TICKS) or
            [r.get("emulator_bridge_frame") for r in man.get("frames",[])]!=list(TICKS) or
            man.get("original_USA_ROM_sha256")!=ROM_SHA or
            man.get("original_input_replay_sha256")!=REPLAY_SHA or
            man.get("emulator_source_revision")!=MESEN_REV or
            man.get("actual_emulator_executable_sha256")!=MESEN_BINARY_SHA or
            man.get("source_original_snes_frame_skipping_disabled_requested") is not True or
            man.get("authentic_live_emulator_bridge_step_counter_verified") is not True or
            man.get("original_held_framebuffer_P6_exported") is not True or
            man.get("original_source_to_experimental_GLb_pose_correspondence_verified") is not False):
            raise ValueError("actual Mesen source executable/replay/tick provenance invalid")
        per={"blue":[],"red":[]}
        for row in man["frames"]:
            tick=row["emulator_bridge_frame"]
            if row.get("replayed_controller_step_index")!=tick-1:
                raise ValueError("source Mesen replay step not consecutive")
            regions={}
            for key,size in REGIONS.items():
                info=row["raw_original_snes_ppu_memory"][key]
                name=f"frame-{tick:06d}-{key}.bin"
                data=z.read(name)
                if info.get("relative_file")!=name or len(data)!=size or info.get("byte_size")!=size or sha(data)!=info.get("sha256"):
                    raise ValueError("raw source PPU region missing or tampered")
                regions[key]=data
            name=f"frame-{tick:06d}-held-display.ppm"
            display=z.read(name)
            info=row["original_emulator_held_display_P6"]
            if (info.get("relative_file")!=name or
                    len(display)!=info.get("byte_size") or
                    sha(display)!=info.get("sha256")):
                raise ValueError("captured original P6 screen hash mismatch")
            p6_screen(display)
            if tick in ANCHORS and (
                tuple(sha(regions[k]) for k in REGIONS)+ (sha(display),)!=ANCHORS[tick]):
                raise ValueError("original sparse archive overlap hash mismatch")
            oam=decode_oam(regions["oam"])
            for name,slot in SLOTS.items():
                descriptor_row=oam[slot]
                if (descriptor_row["source_obj_hflip"] is not False or
                        descriptor_row["source_obj_size_select_large"] is not True):
                    raise ValueError("actual source racer OAM slot orientation/size changed")
                obj=decode_source_obj(descriptor_row,regions["vram"],regions["cgram"],
                    oam_mode=4,obj_base=0x6000,second_table_offset=0x1000)
                if obj["size"]!=64 or obj["slot"]!=slot:
                    raise ValueError("original 64px racer source shape unavailable")
                per[name].append({
                  "tick":tick,"oam_slot":slot,
                  "source_oam_x_signed9":descriptor_row["source_oam_x_signed9"],
                  "source_oam_y_raw8":descriptor_row["source_oam_y_raw8"],
                  "source_oam_tile_word9":descriptor_row["source_oam_tile_word9"],
                  "source_oam_hflip":False,
                  "source_alpha_opaque_pixels":obj["opaque_count"],
                  "source_alpha_sha256":sha(obj["alpha_mask"]),
                  "source_index_plane_sha256":sha(obj["plane"]),
                  "source_rgba_sha256":sha(obj["rgba"]),
                  "_alpha":obj["alpha_mask"],"_plane":obj["plane"],"_rgba":obj["rgba"],
                  "_descriptor":descriptor(descriptor_row),
                })
    observed={name:summarize(rows) for name,rows in per.items()}
    if (observed["blue"]["distinct_source_alpha_masks"]!=19 or
            observed["red"]["distinct_source_alpha_masks"]!=23 or
            any(observed[name]["source_alpha_changed_edges"]!=23 for name in SLOTS)):
        raise ValueError("authentic original 2D decoded source census differs")
    return {
       "schema":SCHEMA,
       "original_USA_ROM_sha256":ROM_SHA,
       "actual_source_run_id":41738370914,
       "actual_source_artifact_id":13279512372,
       "source_canonical_archive_sha256":ZIP_SHA,
       "source_mesen_manifest_sha256":MANIFEST_SHA,
       "source_original_controller_replay_sha256":REPLAY_SHA,
       "source_original_mesen_revision":MESEN_REV,
       "source_original_mesen_executable_sha256":MESEN_BINARY_SHA,
       "prior_original_source_archive_run_id":41605614082,
       "prior_sparse_frame_overlap_ticks":[1601,1607,1618],
       "prior_overlap_OAM_VRAM_CGRAM_P6_SHA256_match":True,
       "new_source_actual_consecutive_no_skip_Mesen_ticks":list(TICKS),
       "source_original_sprite_slots":{"blue":96,"red":97},
       "original_source_OBSEL_mode4_from_previous_register_witness":True,
       "original_source_OBSEL_mode4_independently_measured_at_every_new_tick":False,
       "new_original_screen_RGB_to_2D_OBJ_pixel_registration_independently_repeated":False,
       "genuine_original_2D_source_cadence_observed":True,
       "genuine_original_3D_camera_rig_pose_cadence_recovered":False,
       "owner_likeness_approved":False,
       "shipping_art_approved":False,
       "per_source_racer":observed,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive",required=True,type=Path)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    result=audit(args.archive.read_bytes())
    text=json.dumps(result,sort_keys=True,indent=2)+"\n"
    if args.out:
        publish_text_once(args.out,text)
    else:
        print(text,end="")


if __name__=="__main__":
    main()
