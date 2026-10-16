#!/usr/bin/env python3
"""Cross-check real Snes9x source OAM vs real native Windows line OAM.

Read-only, four pinned evidence streams in three immutable ZIP archives:
original 263-source callbacks, extra original end-field OAM+video host dumps,
and the actual Windows 11-pixel/70-live-OAM record. The original callback
and end-field screenshot with the same numeric frame are *not* equal pixels.
Neither observation proves instruction/beam-phase equivalence or same-line
original OBJ priority. This tool never edits renderer, emulators or input.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

SHA={
 "original_263":"72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e",
 "original_extra":"7a506cfc5f44bd8cc6aaba8482f42140b51618ba14aedec8f9bc7558417ad4b2",
 "native_11pixel":"002c95a44f3539652760609c6f6d7376c82e6014f2481cc60bbb1f8990b3b970",
}
FIELDS={
 1279:{"tag":"qa08_arrow_1279","host":"a7f5a9f2f14743c0bfb1acbc14f52c274a4f1d9b2c8d756767b3d0ac57504e85",
       "oam":"a072b66061b6701550cb6a8ed71173572112c7db1f278cb8157412aea8fe96f2",
       "cgram":"22437d32a69725f89f1d584e17056f30fe91a07376543f304003f3770e85c99a",
       "wrong":216},
 4031:{"tag":"qa08_medal_4031","host":"d1808715289da07846ae9b24fb91520c9c8dd2969325174f5154cf2f2c972659",
       "oam":"50cb34e03ed33faed97730792ba12a8aeab5fdff3d3cec15e4bb411d5640501e",
       "cgram":"431224685084e4a1ec62da7d7aaab96a7c36beb78aa8d257b0569be416737c12",
       "wrong":778},
 4175:{"tag":"qa08_medal_4175","host":"653443da0f7302caaee74887adb396b2a2e4a133669c35a70e8c760d718270fa",
       "oam":"3e5a91d8612d562aaac1a2787c7a58bd55d26ca40006ce57e7d40cda2ef950e0",
       "cgram":"431224685084e4a1ec62da7d7aaab96a7c36beb78aa8d257b0569be416737c12",
       "wrong":766},
}
SLOTS=(96,97,98,99,112,113,114)
ORIGINAL_TILE={
4031:{96:0xcc,97:0xcc,98:0xe6,99:0xe6,112:0xa2,113:0xa4,114:0xa6},
4175:{96:0xcc,97:0xcc,98:0xe2,99:0xe2,112:0xa2,113:0xa4,114:0xa6},
}
NATIVE_TILE={
4032:{96:0xce,97:0xce,98:0xe6,99:0xe6,112:0xa0,113:0xa2,114:0xa4},
4176:{96:0xce,97:0xce,98:0xe2,99:0xe2,112:0xa0,113:0xa2,114:0xa4},
}

def sha(buf:bytes)->str:
    return hashlib.sha256(buf).hexdigest()

def check(actual,expected,label:str)->None:
    if actual!=expected:raise ValueError(f"unqualified source {label}: {actual!r} != {expected!r}")

def open_zip(path:Path,label:str)->zipfile.ZipFile:
    check(sha(path.read_bytes()),SHA[label],label+" outer source ZIP SHA256")
    z=zipfile.ZipFile(path)
    names=z.namelist()
    if len(names)!=len(set(names)):
        raise ValueError("duplicate original/native ZIP source members")
    return z

def source_slot(oam:bytes,n:int)->dict:
    if len(oam)!=544 or n not in SLOTS:raise ValueError("source OAM 544-byte image/slot missing")
    x,y,tile,attr=oam[4*n:4*n+4]
    hi=(oam[512+n//4]>>((n%4)*2))&3
    signed=x+(256 if hi&1 else 0)
    if signed>=256:signed-=512
    return {"slot":n,"x":signed,"y":y,"tile":tile,"attr":attr,
            "OBJ_palette":(attr>>1)&7,"OBJ_priority":(attr>>4)&3,
            "large_sprite_bit":hi>>1,"highOAM":hi}

def pixel_difference_count(raw:bytes,host:bytes)->int:
    if len(raw)!=256*224*4 or len(host)!=len(raw):
        raise ValueError("actual unmasked 256x224 original video/screenshot missing")
    return sum(raw[i:i+3]!=host[i:i+3] for i in range(0,len(raw),4))

def slot_delta(original:dict,native:str,hi:int,slot:int)->dict:
    if hi!=original["highOAM"] or original["large_sprite_bit"]!=0:
        raise ValueError("source/high OAM discrepancy or unsupported large sprite")
    if len(native)!=4:
        raise ValueError("invalid native tile-attribute source bytes")
    attr=int(native[:2],16)
    tile=int(native[2:],16)
    if attr!=original["attr"]:
        raise ValueError("matching original/native sprite priority/palette/flip attributes differ")
    if not 0<=tile<=255:
        raise ValueError("invalid native tile index")
    return {"slot":slot,"original_tile":f"{original['tile']:02x}",
            "native_tile":f"{tile:02x}","native_minus_original_tile":tile-original["tile"],
            "source_palette":original["OBJ_palette"],"source_priority":original["OBJ_priority"]}

def verify(original:Path, extra:Path, native:Path)->dict:
    with open_zip(original,"original_263") as src,open_zip(extra,"original_extra") as e,open_zip(native,"native_11pixel") as w:
        original_manifest=json.loads(src.read("qa08-original-2p-fullroute.json"))
        hist=json.loads(e.read("original-263-verified.json"))
        data=json.loads(w.read("qa08-native-effective-pixel-owner.json"))
        if (original_manifest["actual_callbacks_captured"]!=263 or
            original_manifest["actual_script_quit_frame"]!=5484 or
            hist["263_original_unmasked_BGRX_frames_identical_to_prior_original"] is not True or
            hist["script_still_quits_at_5484"] is not True or
            hist["native_guest_phase_certified"] is not False):
            raise ValueError("old original full 263 callback corpus not independently preserved")
        if (data["real_native_2p_guest_frames"]!=5484 or
            data["real_native_2p_guest_crc_sha256"]!="c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876" or
            data["independently_source_qualified_native_scanline_OAM_snapshots"]!=70 or
            data["original_snes9x_2014_same_field_pixel_priority_proven"] is not False):
            raise ValueError("native effective OAM source or guest CRC unqualified")
        source_sha={int(row["real_original_snes9x_callback_frame"]):
                    row["original_unchanged_BGRX_sha256"]
                    for row in original_manifest["each_authentic_callback"]}
        original_fields={}
        for frame,expected in FIELDS.items():
            tag=expected["tag"]
            raw=src.read(f"frames/frame_{frame:06d}_256x224.raw")
            callback_sha=sha(raw)
            check(callback_sha,source_sha.get(frame),f"source callback {frame} SHA")
            info=json.loads(e.read(f"registers/{tag}.info.json"))
            reg=json.loads(e.read(f"registers/{tag}.regs.json"))
            if (info["frame"]!=frame or info["fb_frame"]!=frame or
                reg["frame_tag"]!=frame or reg["total_emulated_frames"]!=frame or
                info["ppuw_truncated"] is not False):
                raise ValueError("original capture field or PPU source metadata mislabeled")
            host=e.read(f"registers/{tag}.fb.bgrx")
            oam=e.read(f"registers/{tag}.oam.bin")
            cgram=e.read(f"registers/{tag}.cgram.bin")
            check(sha(host),expected["host"],f"host snapshot {frame}")
            check(sha(oam),expected["oam"],f"OAM {frame}")
            check(sha(cgram),expected["cgram"],f"CGRAM {frame}")
            check(pixel_difference_count(raw,host),expected["wrong"],
                  f"separate video/host screenshot pixels {frame}")
            original_fields[frame]={
                "original_video_callback_sha256":callback_sha,
                "separate_original_host_screenshot_sha256":sha(host),
                "wrong_pixels_between_separate_original_producers":expected["wrong"],
                "original_endfield_OAM_sha256":sha(oam),
                "original_endfield_CGRAM_sha256":sha(cgram),
                "slots":{n:source_slot(oam,n) for n in SLOTS},
            }
        native_rows=data["native_OAM_in_effect_on_selected_lines"]
        comparisons=[]
        for frame in (4031,4175):
            guest=frame+1
            for slot in SLOTS:
                origin=original_fields[frame]["slots"][slot]
                check(origin["tile"],ORIGINAL_TILE[frame][slot],
                      f"original {frame} slot {slot} tile")
                actual=[row for row in native_rows if row["native_guest"]==guest
                        and row["OAM_slot"]==slot]
                check(len(actual),5,f"native guest {guest} slot {slot} actual scanlines")
                tileattrs={row["native_scanline_oam_tile_attr"] for row in actual}
                xy={row["native_scanline_oam_xy"] for row in actual}
                high={row["native_scanline_high_oam_pair"] for row in actual}
                if len(tileattrs)!=1 or len(xy)!=1 or len(high)!=1:
                    raise ValueError("native OAM slot changed across five original PPU lines")
                check(tileattrs.pop()[2:],f"{NATIVE_TILE[guest][slot]:02x}",
                      f"native {guest} slot {slot} source tile")
                xynext=xy.pop()
                check(xynext,f"{origin['y']:02x}{origin['x']&255:02x}",
                      f"native {guest} slot {slot} source OAM XY")
                val=f"{origin['attr']:02x}{NATIVE_TILE[guest][slot]:02x}"
                row=slot_delta(origin,val,high.pop(),slot)
                row.update({"original_source_field":frame,"native_guest":guest,
                            "live_native_scanline_samples":5})
                expected_delta=(-2 if slot in (112,113,114)
                                else 2 if slot in (96,97) else 0)
                check(row["native_minus_original_tile"],expected_delta,
                      f"source OAM slot {slot} exact matching-field delta")
                comparisons.append(row)
        return {
          "schema":"qa08-real-original-to-native-same-numbered-field-OAM-discriminator/1",
          "archive_SHA256":SHA,
          "source_video_callbacks_verified_against_independent_original_263":3,
          "original_snesref_host_snapshots_distinct_from_video_callbacks":True,
          "original_host_vs_video_source_checks":original_fields_to_report(original_fields),
          "native_guest_CRC_entries_verified":5484,
          "native_real_per_line_OAM_samples_verified":70,
          "original_native_matching_field_slot_comparisons":comparisons,
          "slots_112_114_original_vs_native_tile_delta":-2,
          "slots_96_97_original_vs_native_tile_delta":2,
          "slots_98_99_matched_tile_delta":0,
          "original_end_of_field_OAM_is_effective_scanline_source":False,
          "original_native_instruction_and_beam_phase_accepted":False,
          "graphics_color_or_sprite_correction_applied":False,
          "physical_or_release_quality_accepted":False,
        }

def original_fields_to_report(fields):
    return [{k:v for k,v in fields[f].items() if k!="slots"} | {"source_field":f}
            for f in (1279,4031,4175)]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("original","original-extra","native","out"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    value=verify(a.original,a.original_extra,a.native)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")
    print("QA08_MATCHED_SOURCE_OAM exact_slot_comparisons=14 original_263=1 "
          "original_scanline_ownership=UNACCEPTED fixed_raster=0")

if __name__=="__main__":
    main()
