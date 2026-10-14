#!/usr/bin/env python3
"""Hash authentic original Snes9x PPU-write journals and final RGB framebuffers.

Consumes one already executed original-USA snesref route's GO/t480 dumps.
No original/native frame alignment, 342-to-256 crop, source OBJ owner or
physical SNES register/pixel fidelity is inferred.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

WIDTH, HEIGHT, BPP = 256, 224, 4
TAG_FRAMES = {"go": 1989, "t480": 2473}
SOURCE = ("cpu", "dma", "hdma")
RECORD_COLS = 6
COLOUR_REGS = {"2130":"CGWSEL", "2131":"CGADSUB", "2132":"COLDATA"}

def load_json(p: Path) -> dict:
    def distinct(pairs):
        out = {}
        for k,v in pairs:
            if k in out:
                raise ValueError("duplicate original screenshot/PPU metadata key: "+k)
            out[k] = v
        return out
    out=json.loads(p.read_text(encoding="utf8"),object_pairs_hook=distinct)
    if not isinstance(out,dict):
        raise ValueError("original snesref metadata must be JSON object")
    return out

def beam_key(v: int) -> int:
    # snesref original retro_run spans V225..261, then V0..224.
    if not isinstance(v,int) or not 0<=v<=261:
        raise ValueError("invalid original Snes9x PPU beam V")
    return (v-225) % 262

def parse_ppuw(path: Path, frame: int, expected: int) -> dict:
    raw=path.read_bytes()
    if not raw.startswith(b"#frame\tvcounter\thcounter\taddr\tvalue\tsource\n"):
        raise ValueError("invalid original snesref PPU write table header")
    lines=raw.decode("ascii").splitlines()
    if any(s.startswith("#truncated") for s in lines):
        raise ValueError("original Snes9x PPU write ring truncated")
    events=[]
    for line in lines[1:]:
        if line.startswith("#"):
            raise ValueError("unexpected PPU witness comment")
        fields=line.split("\t")
        if len(fields)!=RECORD_COLS:
            raise ValueError("malformed original snesref PPU event")
        f,v,h=map(int,fields[:3])
        addr,value,source=fields[3:]
        if (f!=frame or source not in SOURCE or
                len(addr)!=4 or len(value)!=2 or
                addr!=addr.upper() or value!=value.upper() or
                not 0<=h<=511 or not 0<=int(value,16)<=255 or
                not (0x2100<=int(addr,16)<=0x2133 or addr=="420C")):
            raise ValueError("forged original source frame/beam/register/write")
        event={"frame":f,"v":v,"h":h,"addr":addr,"value":value,
               "source":source,"key":beam_key(v)}
        if events and (event["key"],h)<(events[-1]["key"],events[-1]["h"]):
            raise ValueError("original source PPU journal not in real beam chronology")
        events.append(event)
    if len(events)!=expected or not 1<=expected<=100000:
        raise ValueError("original PPU register count differs from snesref metadata")
    by_src=Counter(e["source"] for e in events)
    colors=[{"ordinal":i,"native_scanline_comparison_permitted":False,
             "original_beam_v":e["v"],"original_beam_h":e["h"],
             "source":e["source"],"register":COLOUR_REGS[e["addr"]],
             "byte":"0x"+e["value"]}
            for i,e in enumerate(events) if e["addr"] in COLOUR_REGS]
    return {"raw_PPU_journal_sha256":hashlib.sha256(raw).hexdigest(),
            "actual_source_write_count":len(events),
            "per_provenance_class":dict(sorted(by_src.items())),
            "ppu_colour_register_writes":len(colors),
            "colour_events":colors[:160],
            "colour_event_count_truncated_in_report":len(colors)>160,
            "hdma_CGADSUB_writes":sum(x["source"]=="hdma" and x["register"]=="CGADSUB" for x in colors),
            "hdma_COLDATA_writes":sum(x["source"]=="hdma" and x["register"]=="COLDATA" for x in colors)}

def read_frame(root: Path, tag: str) -> dict:
    if tag not in TAG_FRAMES:
        raise ValueError("unsupported original 2P replay checkpoint")
    expected_frame=TAG_FRAMES[tag]
    info=load_json(root/(tag+".info.json"))
    if (info.get("tag")!=tag or info.get("frame")!=expected_frame or
            info.get("fb_frame")!=expected_frame or
            info.get("fb_width")!=WIDTH or info.get("fb_height")!=HEIGHT or
            info.get("fb_dump_format")!="BGRX8888" or
            info.get("ppuw_truncated") is not False or
            type(info.get("ppuw_entries")) is not int or
            info["ppuw_entries"]<=0 or
            info.get("no_colormath") is not False or
            info.get("no_clip") is not False or
            info.get("layer_mask")!="1F" or
            type(info.get("snesref_dbg_version")) is not int or
            info["snesref_dbg_version"]<1):
        raise ValueError("authentic original Snes9x full-colour RGB or PPU witness metadata missing")
    raw=(root/(tag+".fb.bgrx")).read_bytes()
    if len(raw)!=WIDTH*HEIGHT*BPP:
        raise ValueError("original 256x224 BGRX image size mismatch")
    # No +43 widening transform is assumed. These are literal original
    # 256x224 source coordinates, not purported Baldosa x133 equivalents.
    sampled=[]
    for x,y in ((90,50),(90,162),(128,50),(128,162)):
        off=(y*WIDTH+x)*BPP
        b,g,r,_=raw[off:off+BPP]
        sampled.append({"original_source_xy":[x,y],"original_RGB8":[r,g,b]})
    journal=parse_ppuw(root/(tag+".ppuw.tsv"),expected_frame,info["ppuw_entries"])
    return {"script_tag":tag,"original_emulator_frame":expected_frame,
            "original_source_fb_width":WIDTH,"original_source_fb_height":HEIGHT,
            "original_RGB_raw_B_G_R_X_SHA256":hashlib.sha256(raw).hexdigest(),
            "source_frame_info_sha256":hashlib.sha256((root/(tag+".info.json")).read_bytes()).hexdigest(),
            "source_image_samples_not_native_aligned":sampled,
            "source_register_writes":journal}

def check(root: Path) -> dict:
    output=[read_frame(root,tag) for tag in ("go","t480")]
    return {
        "schema":"qa08-true-original-Snes9x-2P-source-RGB-and-PPU-register-frames/1",
        "status":"original-Snes9x-raw-screen-and-real-register-writes-hash-observed",
        "original_two_player_script_checkpoint_frames":[1989,2473],
        "full_source_FB_and_original_PPU_journal_complete":True,
        "original_screen_size":[WIDTH,HEIGHT],
        "observed_original_Snes9x_source_samples":output,
        "source_does_not_prove_guest_simulation_same_phase_as_Baldosa":True,
        "source_does_not_prove_widened_342_original_crop_offset":True,
        "source_PPU_write_journal_cannot_replace_live_PPUs_register_or_pixel":True,
        "original_native_pixel_parity_proven":False,
        "physical_SNES_hardware_timing_proven":False,
        "authored_HD_racer_approved":False,
    }

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=check(a.root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("QA08_ORIGINAL_SNESREF_PIXEL_SOURCE_ACCEPTED "
          "original_frames=1989,2473 raster=256x224 no_native_parity=1")

if __name__=="__main__":
    main()
