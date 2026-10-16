#!/usr/bin/env python3
"""Verify exact original 2014 Snes9x matched callback end-field PPU/OAM bytes.

Input: one *unchanged* two-pad controller script and one opt-in source-only
snesref frontend capture with precisely three actual do_dump callbacks.
Reject frame substitution, source video/cgram/oam tampering or same-line
ownership inference. This does NOT prove final 2014 PPU OBJ scanline ownership.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
try:
    from tools.qa08_verify_original_medal_oam_candidates import decode
except ImportError:
    from qa08_verify_original_medal_oam_candidates import decode

CALLBACKS={
  1279:"qa08_arrow_1279",
  4031:"qa08_medal_4031",
  4175:"qa08_medal_4175",
}
POINTS={
  1279:{(55,65):(90,74,82)},
  4031:{(207,91):(115,57,74),(205,115):(115,57,74),
        (205,139):(132,132,132),(225,96):(206,189,140),
        (225,120):(206,189,140)},
  4175:{(207,91):(115,57,74),(205,115):(115,57,74),
        (205,139):(132,132,132),(225,96):(206,189,140),
        (225,120):(206,189,140)},
}
SLOTS=(96,97,98,99,112,113,114)
# Genuine original snesref end-of-field host screenshots at source 1279/4031/4175
# were produced separately from the authenticated original retro video callbacks.
# They differ in 216/778/766 pixels. Never relabel either as a video callback.
HOST_FRAME_SHA256={
  1279:"a7f5a9f2f14743c0bfb1acbc14f52c274a4f1d9b2c8d756767b3d0ac57504e85",
  4031:"d1808715289da07846ae9b24fb91520c9c8dd2969325174f5154cf2f2c972659",
  4175:"653443da0f7302caaee74887adb396b2a2e4a133669c35a70e8c760d718270fa",
}
HOST_VS_CALLBACK_NONEXACT_PIXELS={1279:216,4031:778,4175:766}
# Original OAM bytes at exact corresponding script-field labels.
SOURCE_MEDAL_TILE_ATTR={
  4031:{96:"1bcc",97:"1bcc",98:"1be6",99:"1be6",
        112:"1ba2",113:"1da4",114:"1fa6"},
  4175:{96:"1bcc",97:"1bcc",98:"1be2",99:"1be2",
        112:"1ba2",113:"1da4",114:"1fa6"},
}

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def real_RGB5_BGRX(raw:bytes,x:int,y:int)->tuple[int,int,int]:
    i=(y*256+x)*4
    b,g,r,_=raw[i:i+4]
    g5=g>>3
    return (r,(g5<<3)|(g5>>2),b)

def verify(root:Path,baseline:Path,original_log:Path,script:Path)->dict:
    baseline_meta=json.loads((baseline/"qa08-original-2p-fullroute.json").read_text())
    if baseline_meta.get("actual_callbacks_captured")!=263 or baseline_meta.get("actual_script_quit_frame")!=5484:
        raise ValueError("historical reference source fullroute not accepted")
    if sha(script.read_bytes())!=baseline_meta["exact_original_two_pad_route_LF_without_turbo_sha256"]:
        raise ValueError("current original 2P input script differs")
    expected_source={int(x["real_original_snes9x_callback_frame"]):
                     x["original_unchanged_BGRX_sha256"]
                     for x in baseline_meta["each_authentic_callback"]}
    log=original_log.read_text(encoding="utf-8",errors="replace")
    if "script f=5484 quit" not in log:
        raise ValueError("actual untouched original route did not finish")
    records=[]
    for frame,tag in CALLBACKS.items():
        if log.count(f"script f={frame} dump {tag} ")!=1:
            raise ValueError("missing/duplicated actual original source dump")
        folder=root/"registers"
        info=json.loads((folder/f"{tag}.info.json").read_text())
        reg=json.loads((folder/f"{tag}.regs.json").read_text())
        if (info.get("frame")!=frame or info.get("fb_frame")!=frame or
            info.get("tag")!=tag or info.get("fb_width")!=256 or
            info.get("fb_height")!=224 or info.get("fb_dump_format")!="BGRX8888" or
            info.get("ppuw_truncated") is not False or
            reg.get("frame_tag")!=frame or reg.get("total_emulated_frames")!=frame or
            info.get("no_colormath") is not False or info.get("no_clip") is not False):
            raise ValueError("real original PPU register/colour state source drift")
        fb=(folder/f"{tag}.fb.bgrx").read_bytes()
        raw=(root/"frames"/f"frame_{frame:06d}_256x224.raw").read_bytes()
        if len(raw)!=256*224*4 or sha(raw)!=expected_source.get(frame):
            raise ValueError("actual original video callback differs from independently verified 263-frame reference")
        if len(fb)!=256*224*4 or sha(fb)!=HOST_FRAME_SHA256[frame]:
            raise ValueError("actual original post-retro_run host screenshot source SHA differs")
        nonexact=sum(any(fb[i+j]!=raw[i+j] for j in range(3))
                     for i in range(0,256*224*4,4))
        if nonexact!=HOST_VS_CALLBACK_NONEXACT_PIXELS[frame]:
            raise ValueError("source screenshot versus video callback count differs")
        colors=[]
        for (x,y),expected in POINTS[frame].items():
            # Compare the immutable original *video callback*, not the
            # separately captured end-of-field snesref host screenshot.
            rgb=real_RGB5_BGRX(raw,x,y)
            if rgb!=expected:
                raise ValueError("original source pixel changed at qualified 2P point")
            colors.append({"x":x,"raster_y":y,"original_source_RGB5_expanded":list(rgb)})
        cgram=(folder/f"{tag}.cgram.bin").read_bytes()
        oam=(folder/f"{tag}.oam.bin").read_bytes()
        if len(cgram)!=512 or len(oam)!=544:
            raise ValueError("incomplete original 256 CGRAM slots or 128 OAM records")
        slot_states=[decode(oam,slot) for slot in SLOTS]
        if frame in SOURCE_MEDAL_TILE_ATTR:
            for entry in slot_states:
                slot=entry["slot"]
                expected=SOURCE_MEDAL_TILE_ATTR[frame][slot]
                if entry["attr"]+format(entry["tile"],"02x")!=expected or (
                    entry["large_sprite_bit"]!=0 or entry["OBJ_priority"]!=1):
                    raise ValueError("actual corresponding original OAM slot tile/priority drift")
        register_event=(folder/f"{tag}.ppuw.tsv").read_bytes()
        if not register_event.startswith(b"#frame\tvcounter\thcounter\taddr\tvalue\tsource\n"):
            raise ValueError("missing actual Snes9x PPU register port writer journal")
        records.append({"actual_original_callback":frame,"tag":tag,
                        "unaltered_video_callback_SHA256":sha(raw),
                        "separate_original_host_endfield_screenshot_SHA256":sha(fb),
                        "host_endfield_wrong_pixels_against_same_label_video_callback":nonexact,
                        "host_screenshot_not_equivalent_to_original_video_callback":True,
                        "unaltered_original_PPU_OAM_544_sha256":sha(oam),
                        "unaltered_original_PPU_CGRAM_512_sha256":sha(cgram),
                        "source_register_JSON_sha256":sha((folder/f"{tag}.regs.json").read_bytes()),
                        "source_register_write_ring_SHA256":sha(register_event),
                        "source_pixel_points":colors,
                        "original_end_field_OAM_candidates_not_active_scanline":slot_states})
    return {
        "schema":"qa08-original-Snes9x-actual-corresponding-medal-end-field-OAM/1",
        "independent_source_2P_callback_count":263,
        "source_frame_registration":"native guest f -> original callback f-1, fixed before run",
        "original_source_unmodified_controller_sha256":sha(script.read_bytes()),
        "original_unmodified_callback_endfield_count":len(records),
        "original_unmodified_source_PPU_field_samples":records,
        "no_input_video_guest_or_sprite_mutation":True,
        "original_snapshot_OAM_is_not_effective_line_OBJ_owner":True,
        "original_host_snapshot_RGB_not_relabelled_as_original_callback":True,
        "all_original_callback_SHA256_verified_separately":True,
        "original_native_identical_cpu_field_phase_accepted":False,
        "physical_windows_7to6_4x_HD_likeness_release_approved":False,
    }

def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ("root","prior-original","original-log","script","out"):
        ap.add_argument("--"+name,required=True,type=Path)
    a=ap.parse_args()
    report=verify(a.root,a.prior_original,a.original_log,a.script)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("QA08_ORIGINAL_SNES9X_MEDAL_END_FIELDS exact_frames=3 "
          "same_source_raster=1 scanline_owner=UNKNOWN release=0")

if __name__=="__main__":
    main()
