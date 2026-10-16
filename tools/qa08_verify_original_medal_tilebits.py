#!/usr/bin/env python3
"""Verify real 2014 Snes9x medal 4bpp indexed-OBJ summaries without image edits.

Reject any changed source image among 263 full callback BGRX frames. Check
both 2014 callback labels and exact OAM seven-slot positions/tile names, all
14 16x16 tile histogram/mask witnesses, and exactly ten predetermined pixel
samples with per-slot transparent/opaque index and original CGRAM word.
No sprite artwork, ROM, VRAM file, synthetic reference or Windows release
claim is serialized.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ORIGINAL_SHA="72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
CALLBACKS=(4031,4175)
SLOTS=(96,97,98,99,112,113,114)
COORDS=((207,91),(205,115),(205,139),(225,96),(225,120))
XY={96:(219,112),97:(219,88),98:(219,112),99:(219,88),
    112:(200,91),113:(200,115),114:(200,139)}
NAME={4031:{96:0xcc,97:0xcc,98:0xe6,99:0xe6,112:0xa2,113:0xa4,114:0xa6},
      4175:{96:0xcc,97:0xcc,98:0xe2,99:0xe2,112:0xa2,113:0xa4,114:0xa6}}
FIELD=re.compile(r"([A-Za-z0-9_]+)=([A-Za-z0-9_.-]+)")
PIXELS=256*224*4

def sha(blob:bytes)->str:
    return hashlib.sha256(blob).hexdigest()


def fields(line:str,prefix:str)->dict[str,str]:
    if not line.startswith(prefix+" "):
        raise ValueError("unexpected original tilebit source record")
    tokens=line[len(prefix)+1:].split()
    if any(FIELD.fullmatch(x) is None for x in tokens):
        raise ValueError("unexpected original tilebit log contents")
    pairs=[v.split("=",1) for v in tokens]
    result=dict(pairs)
    if len(result)!=len(pairs):
        raise ValueError("duplicate original source field")
    return result


def parse_records(log:str)->dict:
    want=("QA08_ORIGINAL_TILE_SOURCE","QA08_ORIGINAL_TILE_ROW",
          "QA08_ORIGINAL_TILE_COUNTS","QA08_ORIGINAL_TILE_SAMPLE")
    found={k:[] for k in want}
    if "QA08_ORIGINAL_4BPP_REJECT" in log:
        raise ValueError("original-only sprite tile source explicitly rejected")
    for line in log.splitlines():
        for k in want:
            if line.startswith(k+" "):
                found[k].append(fields(line,k))
    if [len(found[k]) for k in want]!=[14,224,14,10]:
        raise ValueError("truncated, duplicated or altered 2-frame seven-sprite 4bpp records")
    sprites={};all_samples={}
    for k in CALLBACKS:
        for slot in SLOTS:
            label=(k,slot)
            records=[p for p in found[want[0]]
                     if int(p["cb"])==k and int(p["slot"])==slot]
            hist=[p for p in found[want[2]]
                  if int(p["cb"])==k and int(p["slot"])==slot]
            rows=[p for p in found[want[1]]
                  if int(p["cb"])==k and int(p["slot"])==slot]
            if len(records)!=1 or len(hist)!=1 or len(rows)!=16:
                raise ValueError("each source slot needs exactly one 16x16 masked decode")
            s,h=records[0],hist[0]
            if ((int(s["x"]),int(s["y"]))!=XY[slot] or
                (int(s["name"],16)&255)!=NAME[k][slot] or
                int(s["size"])!=16 or int(s["priority"])!=1 or
                int(s["hflip"]) not in (0,1) or int(s["vflip"]) not in (0,1) or
                len(s["indexed16_FNV64"])!=16 or
                re.fullmatch(r"[0-9a-f]{16}",s["indexed16_FNV64"]) is None):
                raise ValueError("foreign Snes9x OAM or sprite-index decode metadata")
            counts=[]
            for index in range(16):
                counts.append(int(h[f"c{index}"]))
            if any(not 0<=v<=256 for v in counts) or sum(counts)!=256:
                raise ValueError("impossible source 4-bit palette-index histogram")
            if sum(counts[1:])!=int(s["nonzero"]):
                raise ValueError("tile source opacity count contradicts histogram")
            masks={int(x["row"]):int(x["opaque_mask"],16) for x in rows}
            if len(masks)!=16 or set(masks)!=set(range(16)) or any(not 0<=v<=65535 for v in masks.values()):
                raise ValueError("invalid/duplicated original sprite source occupancy rows")
            if sum(v.bit_count() for v in masks.values())!=int(s["nonzero"]):
                raise ValueError("source 4bpp row opacity does not match histogram")
            sprites[label]={"original_video_callback":k,"source_slot":slot,
                            "sprite_xy":[*XY[slot]],"name_low_byte":f"{NAME[k][slot]:02x}",
                            "actual_original_name9":s["name"].lower(),
                            "palette_class":int(s["pal"]),
                            "priority":int(s["priority"]),
                            "source_16x16_opaque_pixels":int(s["nonzero"]),
                            "tile_index_FNV64":s["indexed16_FNV64"],
                            "source_16_rows_opacity_hex":[f"{masks[i]:04x}" for i in range(16)],
                            "source_16_palette_index_counts":counts}
        for i,(x,y) in enumerate(COORDS):
            matches=[r for r in found[want[3]] if
                     int(r["cb"])==k and int(r["x"])==x and int(r["y"])==y]
            if len(matches)!=1:
                raise ValueError("original source medal pixel samples wrong/missing")
            sample=matches[0];details={}
            for slot in SLOTS:
                word=sample[f"s{slot}"]
                xx=x-XY[slot][0]
                yy=(y-XY[slot][1]+256)&255
                if 0<=xx<16 and yy<16:
                    match=re.fullmatch(r"(\d{1,2})\.([0-9a-f]{4})",word)
                    if match is None:
                        raise ValueError("original sprite source pixel missing indexed VRAM value")
                    value=int(match.group(1))
                    if not 0<=value<=15:
                        raise ValueError("original source OBJ index outside 4-bit depth")
                    expected=bool(int(sprites[k,slot]["source_16_rows_opacity_hex"][yy],16)&(1<<xx))
                    if bool(value)!=expected:
                        raise ValueError("original source sprite transparency sample not in row mask")
                    details[str(slot)]={"indexed4bpp":value,"CGRAM_RGB15_word":match.group(2)}
                elif word!="outside":
                    raise ValueError("out-of-bounds sprite source fabricated as opaque")
            all_samples[k,i]={"original_video_callback":k,"source_xy":[x,y],
                              "original_OAM_slots_with_source_sample":details}
    return {
        "schema":"qa08-original-2014-medal-sprite-4bpp-indexed-source/1",
        "actual_original_video_callbacks":[*CALLBACKS],
        "correctly_registered_native_guests":[k+1 for k in CALLBACKS],
        "actual_sampled_original_sprite_slots":len(sprites),
        "actual_sampled_original_pixel_slots":len(all_samples),
        "authenticated_16x16_sprites":[sprites[k,s] for k in CALLBACKS for s in SLOTS],
        "actual_indexed_pixel_candidates":[all_samples[k,i] for k in CALLBACKS for i in range(5)],
        "original_4bit_index_source_reproduced_for_selected_slots":True,
        "actual_Windows_corresponding_sprite_4bpp_source_proven":False,
        "underlying_original_tile_VRAM_writers_proven":False,
        "original_2014_effective_pixel_OBJ_priority_or_palmath_added_by_this_observer":False,
        "full_296_medal_pixels_causally_explained":False,
        "no_full_VRAM_or_game_art_exported":True,
        "renderer_or_CPU_patch_approved":False,
        "release_QA08_QA10_or_HD_likeness_accepted":False,
    }


def verify(root:Path,original:Path)->dict:
    if sha(original.read_bytes())!=ORIGINAL_SHA:
        raise ValueError("foreign original 2014 sprite reference ZIP")
    with zipfile.ZipFile(original) as old:
        orig=json.loads(old.read("qa08-original-2p-fullroute.json"))
        fresh=json.loads((root/"manifest.json").read_text())
        if (orig.get("actual_callbacks_captured")!=263 or
            fresh.get("actual_callbacks_captured")!=263 or
            orig.get("capture_selection")!=[1279,5471,16] or
            fresh.get("capture_selection")!=orig["capture_selection"]):
            raise ValueError("source original 2014 callback registration changed")
        entries={v["real_original_snes9x_callback_frame"]:v for v in
                 orig["each_authentic_callback"]}
        if len(entries)!=263:
            raise ValueError("truncated original frame baseline")
        for cb in range(1279,5472,16):
            name=f"frames/frame_{cb:06d}_256x224.raw"
            a=old.read(name)
            b=(root/name).read_bytes()
            if a!=b or len(a)!=PIXELS or sha(a)!=entries[cb]["original_unchanged_BGRX_sha256"]:
                raise ValueError(f"read-only sprite probe modified original source callback {cb}")
    decoded=parse_records((root/"original.log").read_text(errors="replace"))
    decoded.update({
        "original_263_full_source_frame_bytes_identical":True,
        "original_263_video_frame_archive_sha256":ORIGINAL_SHA,
        "unchanged_2014_original_2P_USA_ROM_sha256":"859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
    })
    return decoded


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=verify(a.root,a.original)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("QA08_ORIGINAL_4BPP_SOURCE_PASS images=263 slots=14 pixel_samples=10 actual_SNES_hardware=UNPROVEN")


if __name__=="__main__":
    main()
