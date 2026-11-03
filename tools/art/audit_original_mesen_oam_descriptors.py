#!/usr/bin/env python3
"""Read-only SNES OAM descriptor census of a real, SHA-bound MesenCE capture.

A recurring descriptor and a source OAM slot are not proof of a visible racer,
1994 bone, source animation pose, or final-screen pixel ownership.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

SCHEMA = "UR-ART4K-AUTHENTIC-MESEN-OAM-DESCRIPTOR-CENSUS/1"
SOURCE_SCHEMA = "UR-ART4K-MESENCE-LIVE-RAW-SNES-PPU-STATES/1"
SOURCE_ZIP_SHA = "a1aa2d04ca936a031d6f46d821d4ece14a7bdbad03b4774f7ab705d275cef6cc"
SOURCE_MANIFEST_SHA = "f50accd67c36cc8455bcb0cc5f774f0efaa233ebc62d68fb33da2c10eb86e21a"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
EMULATOR_REV = "a60e79feb4d6dcced5922d636f9211837d01e381"
OAM_SIZE = 544


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def decode_oam(raw: bytes) -> list[dict]:
    """Decode 128 SNES OBJ entries, including correct 2-bit high table.

    Does not infer pixel dimensions: OBSEL size configuration is unavailable.
    X is 9-bit two's-complement; Y is the raw 8-bit OAM coordinate.
    """
    if not isinstance(raw, bytes) or len(raw) != OAM_SIZE:
        raise ValueError("exact 544-byte original SNES OAM required")
    out = []
    for slot in range(128):
        xlow, y, tile, attr = raw[slot*4:slot*4+4]
        high = (raw[512 + slot // 4] >> (2 * (slot % 4))) & 3
        x = xlow | ((high & 1) << 8)
        signed_x = x - 512 if x >= 256 else x
        out.append({
            "oam_slot": slot,
            "source_oam_x_signed9": signed_x,
            "source_oam_y_raw8": y,
            "source_oam_tile_word9": tile | ((attr & 1) << 8),
            "source_obj_palette_id0_to7": (attr >> 1) & 7,
            "source_obj_priority_id0_to3": (attr >> 4) & 3,
            "source_obj_hflip": bool(attr & 0x40),
            "source_obj_vflip": bool(attr & 0x80),
            "source_obj_size_select_large": bool(high & 2),
            "source_oam_raw_low4_hex": raw[slot*4:slot*4+4].hex(),
            "source_oam_high2": high,
        })
    return out


def descriptor(row: dict) -> tuple:
    return (row["source_oam_x_signed9"], row["source_oam_y_raw8"],
            row["source_oam_tile_word9"], row["source_obj_palette_id0_to7"],
            row["source_obj_priority_id0_to3"], row["source_obj_hflip"],
            row["source_obj_vflip"], row["source_obj_size_select_large"])


def summarize(raw: bytes) -> dict:
    rows = decode_oam(raw)
    freq = Counter(descriptor(x) for x in rows)
    maximum = max(freq.values())
    leaders = [key for key,n in freq.items() if n==maximum]
    if len(leaders) != 1:
        raise ValueError("no unique most-common original source OAM descriptor")
    leader = leaders[0]
    exceptions = [row for row in rows if descriptor(row)!=leader]
    return {
        "source_oam_sha256": sha(raw),
        "original_oam_slots": 128,
        "original_oam_bytes": OAM_SIZE,
        "distinct_original_oam_descriptors": len(freq),
        "modal_source_descriptor": {
            "signed_x": leader[0], "raw_y": leader[1], "tile_word9": leader[2],
            "palette": leader[3], "priority": leader[4],
            "hflip": leader[5], "vflip": leader[6], "large_size_selection": leader[7],
        },
        "modal_original_descriptor_slots": maximum,
        "different_from_modal_original_oam_slots": [x["oam_slot"] for x in exceptions],
        "nonmodal_original_oam_entries": exceptions,
        "original_displayed_sprite_pixels_verified": False,
        "source_OBSEL_sprite_pixel_sizes_verified": False,
        "source_original_3d_anatomy_verified": False,
    }


def analyze_archived_source(blob: bytes) -> dict:
    if sha(blob)!=SOURCE_ZIP_SHA:
        raise ValueError("source zip is not the frozen original executed emulator archive")
    with zipfile.ZipFile(__import__("io").BytesIO(blob)) as archive:
        names=archive.namelist()
        if (len(names)!=7 or len(set(names))!=len(names) or
                "manifest.json" not in names):
            raise ValueError("original PPU archive member inventory changed")
        manifest_raw=archive.read("manifest.json")
        if sha(manifest_raw)!=SOURCE_MANIFEST_SHA:
            raise ValueError("actual original Mesen PPU manifest SHA differs")
        receipt=json.loads(manifest_raw)
        if (receipt.get("schema")!=SOURCE_SCHEMA or
                receipt.get("original_USA_ROM_sha256")!=ROM_SHA or
                receipt.get("emulator_source_revision")!=EMULATOR_REV or
                receipt.get("source_original_live_OAM_sprite_to_racer_identity_verified") is not False):
            raise ValueError("original source emulator receipt was altered")
        frames=receipt.get("frames")
        if not isinstance(frames,list) or len(frames)!=2:
            raise ValueError("expected precisely two actual original emulator frames")
        decoded=[]
        for row in frames:
            frame=row.get("emulator_bridge_frame")
            r=row.get("raw_original_snes_ppu_memory")
            if type(frame) is not int or not isinstance(r,dict) or set(r)!={"oam","vram","cgram"}:
                raise ValueError("original source PPU frame envelope invalid")
            content={}
            for region,size in (("oam",544),("vram",65536),("cgram",512)):
                meta=r[region]
                filename=f"frame-{frame:06d}-{region}.bin"
                if (meta.get("relative_file")!=filename or
                        meta.get("byte_size")!=size or
                        filename not in names):
                    raise ValueError("original source RAM region identity invalid")
                raw=archive.read(filename)
                if len(raw)!=size or sha(raw)!=meta.get("sha256"):
                    raise ValueError("actual original emulator RAM region SHA differs")
                content[region]=raw
            decoded.append({"frame":frame,"raw":content,"summary":summarize(content["oam"])})
        if [x["frame"] for x in decoded]!=[1219,1220]:
            raise ValueError("not consecutive authenticated Mesen original frames")
        changes={
            k:sum(a!=b for a,b in zip(decoded[0]["raw"][k], decoded[1]["raw"][k]))
            for k in ("oam","vram","cgram")
        }
        changed_slots=[i for i in range(128)
                       if descriptor(decode_oam(decoded[0]["raw"]["oam"])[i]) !=
                          descriptor(decode_oam(decoded[1]["raw"]["oam"])[i])]
        return {
            "schema": SCHEMA,
            "real_original_mesen_held_frame_ticks": [1219,1220],
            "source_archive_sha256":SOURCE_ZIP_SHA,
            "source_manifest_sha256":SOURCE_MANIFEST_SHA,
            "original_USA_ROM_sha256":ROM_SHA,
            "source_PPU_bytes_changed_between_held_ticks":changes,
            "source_oam_slots_changed_between_held_ticks":changed_slots,
            "per_original_held_frame": [
                {"frame":rec["frame"],**rec["summary"]} for rec in decoded
            ],
            "same_emulator_frame_pixel_ownership_verified":False,
            "original_racer_identity_from_oam_verified":False,
            "source_OBSEL_sprite_pixel_sizes_verified":False,
            "original_source_3d_rig_or_camera_verified":False,
            "owner_likeness_approved":False,
        }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-raw-archive",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=analyze_archived_source(args.original_raw_archive.read_bytes())
    from tools.art.no_replace_report import publish_text_once
    publish_text_once(args.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="per_original_held_frame"},
                     sort_keys=True))


if __name__=="__main__":
    main()
