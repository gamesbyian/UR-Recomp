#!/usr/bin/env python3
"""Authenticate a bounded genuine original-Snes9x 2P raster time series.

SNESREF_FRAME_DUMP_NATIVE=1 avoids an implicit 256x224 hi-res crop. The
callback names its *pre-increment* frame 2188..2224 (script retro_run
frame numbers are 2189..2225). Existing exact source identity, original
opcode/LUT/WRAM and source GO/t480 evidence are required independently.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

FRAMES=tuple(range(2188,2225))
WIDTH,HEIGHT=256,224
ROM="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SCRIPT="94eaa5ffb487d9b227e34965c1d2ee09efe3dac06ade595f7dad05315dfc5221"
WRAM="9350bcb02f3cbf490678c5276245ec2c7fe36b9078bfab9e912d86c5cbc93bf6"
LIVE_SCHEMA="qa08-original-Snes9x-executed-channel5-live-PPU-HDMA/1"

def read_json(path):
    def strict(pairs):
        out={}
        for k,v in pairs:
            if k in out: raise ValueError("duplicate source witness JSON key")
            out[k]=v
        return out
    return json.loads(Path(path).read_text(encoding="utf8"), object_pairs_hook=strict)

def validate(root: Path, receipt: dict, live: dict, original_go: dict) -> dict:
    if (receipt.get("USA_ROM_SHA256")!=ROM or
            receipt.get("original_script_SHA256")!=SCRIPT or
            receipt.get("original_t480_WRAM_SHA256")!=WRAM or
            receipt.get("source_65816_writer_PCs")!=18 or
            receipt.get("actual_executed_original_instruction_count")!=55 or
            receipt.get("second_camera_0DDB")!=1 or
            receipt.get("in_race_0313")!=1 or
            receipt.get("native_same_input_frame_parity_proven") is not False or
            live.get("schema")!=LIVE_SCHEMA or
            live.get("actual_original_PPU_2131_2132_writes")!=96 or
            live.get("actual_original_channel5_register_pairs")!=48 or
            live.get("actual_WRAM_PPU_byte_matches")!=96 or
            live.get("source_expected_byte_matches")!=96 or
            original_go.get("original_emulator_frame")!=1989 or
            original_go.get("original_source_fb_width")!=WIDTH or
            original_go.get("original_source_fb_height")!=HEIGHT):
        raise ValueError("genuine original source route/register/GO evidence missing")
    paths=list(root.glob("frame_*.raw"))
    expected={f"frame_{frame:06d}_{WIDTH}x{HEIGHT}.raw" for frame in FRAMES}
    if {p.name for p in paths}!=expected or len(paths)!=len(FRAMES):
        raise ValueError("missing/extra/cropped original-native-dimension source frames")
    accepted=[]
    for frame in FRAMES:
        p=root/f"frame_{frame:06d}_{WIDTH}x{HEIGHT}.raw"
        payload=p.read_bytes()
        if len(payload)!=WIDTH*HEIGHT*4:
            raise ValueError("non-256x224 original frame byte count")
        if any(payload[i]!=0 for i in range(3,len(payload),4)):
            raise ValueError("non-BGRX original Snes9x source framebuffer")
        pix=lambda x,y:list(reversed(payload[(y*WIDTH+x)*4:(y*WIDTH+x)*4+3]))
        samples=[{"x":x,"y":y,"original_RGB8":pix(x,y)} for x,y in
                 ((64,65),(96,65),(128,65),(64,177),(96,177),(128,177))]
        accepted.append({
            "original_Snesref_callback_frame_zero_based":frame,
            "corresponding_original_retro_run_one_based":frame+1,
            "raw_B_G_R_X_SHA256":hashlib.sha256(payload).hexdigest(),
            "per_original_true_256x224_screen_samples":samples})
    if len({x["raw_B_G_R_X_SHA256"] for x in accepted})<5:
        raise ValueError("stale original raster time series, insufficient changing frames")
    return {
        "schema":"qa08-source-original-2P-37-full-PPU-raster-frames-2188-2224/1",
        "status":"original-Snes9x-source-P7-BGRX-frame-data-exact-hash-attested",
        "original_ROM_SHA256":ROM,"original_script_SHA256":SCRIPT,
        "original_t480_WRAM_SHA256":WRAM,
        "source_callback_window_inclusive":[2188,2224],
        "source_run_window_inclusive":[2189,2225],
        "full_256x224_original_frames":len(accepted),
        "snesref_frame_dump_native_mode":True,
        "unmodified_original_script_route":True,
        "original_live_CGADSUB_COLDATA_proven_separately":True,
        "same_input_guest_phase_and_camera_as_native_proven":False,
        "source_256_to_native_wide_342_registration_proven":False,
        "original_vs_native_final_RGBA_parity_proven":False,
        "original_hardware_HBlank_equivalence_proven":False,
        "procedural_HD_racer_approved":False,
        "source_original_frames":accepted,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("root","receipt","live","original-go","out"):
        p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    from tools.qa08_original_snesref_raster_source import read_frame
    result=validate(a.root,read_json(a.receipt),read_json(a.live),
                    read_frame(a.original_go,"go"))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("QA08_AUTHENTIC_ORIGINAL_2P_RASTER_WINDOW frames=37 "
          "original=256x224 native_guest_alignment=unproved")

if __name__=="__main__": main()
