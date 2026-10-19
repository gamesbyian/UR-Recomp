#!/usr/bin/env python3
"""QA08: immutable 2014 medal-painter versus correctly registered Win32 source.

Read-only three-real-execution discriminator. A same-numbered internal original
painter stage is NOT a valid replacement for original callback f-1. In
particular do not alter guest input, frame numbering, PPU pixels, or renderer.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
try:
    from tools.qa08_verify_original_medal_callback_registration import (
        consumed_input, INPUT_SHA, rgb565_to_rgb8,
    )
except ImportError:
    from qa08_verify_original_medal_callback_registration import (
        consumed_input, INPUT_SHA, rgb565_to_rgb8,
    )

ORIGINAL_OUTER = "3475ee87b5b20768f9377d8d1c787927955c33ee6d4388dae008f5486a81370e"
ORIGINAL_NESTED = "72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
PAINTER_ZIP = "8387c413d42cf8d2da2a61ba3ec67e8375394f938171dc4d73a3e4ba567920e4"
NATIVE_OUTER = "832c08263e2d3013d5b15df82b2b0574fabfd3114194b7cbef9f6bb1b2959727"
NATIVE_INNER = "c36fdd0238735e739219b013d25665e42a008a7827ee97631a322217c9f4f0cd"
REPORT_SHA = "71afe4439a361706d159afe203b67a63845a93866eaeb48bd018adcc3636881d"
GUEST_SHA = "b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568"
HEADER = (b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
          b"TUPLTYPE RGB_ALPHA\nENDHDR\n")
POINTS = ((207,91),(205,115),(205,139),(225,96),(225,120))
FRAMES = (4032,4176)
RECURRING_GUEST_FRAMES = tuple(range(4032, 5185, 48))  # authentic 25 medal source samples
LAYER = re.compile(
    r"UR_QA08_ORIGINAL_MEDAL_LAYER frame=(\d+) range=(\d+),(\d+) "
    r"x=(\d+) y=(\d+) stage=(\w+) bg=(-?\d+) bgmode=(\d+) "
    r"depth=([0-9a-f]{2}) rgb565=([0-9a-f]{4}) "
    r"source_callback_proven=0 native_frame_proven=0"
)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def checked(path: Path, expected: str) -> bytes:
    raw = path.read_bytes()
    if sha(raw) != expected:
        raise ValueError(f"exact original artifact SHA mismatch: {path.name}")
    return raw

def rgb5(rgb: tuple[int,int,int]) -> tuple[int,int,int]:
    return tuple(v >> 3 for v in rgb)

def rgb565_rgb5(value: int) -> tuple[int,int,int]:
    # Real original paint buffer stores 5/6/5, whereas the comparison uses
    # final output RGB5. In particular green is SIX bits before truncation.
    return ((value >> 11) & 31, ((value >> 6) & 31), value & 31)

def original_rgb(raw: bytes, x: int, y: int) -> tuple[int,int,int]:
    if len(raw) != 256*224*4:
        raise ValueError("original BGRX callback cropped")
    pos = 4*(y*256+x)
    b,g,r,unused = raw[pos:pos+4]
    if unused != 0:
        raise ValueError("2014 BGRX callback fourth channel changed")
    return r,g,b

def native_rgb(raw: bytes, x: int, y: int) -> tuple[int,int,int]:
    if len(raw) != len(HEADER)+256*224*4 or not raw.startswith(HEADER):
        raise ValueError("actual original-native PPU P7 format cropped/altered")
    pos = len(HEADER)+4*(y*256+x)
    r,g,b,a = raw[pos:pos+4]
    # Exact Baldosa P7 writer reserves its fourth channel as zero. The
    # P7 TUPLTYPE header alone does not imply opaque host compositing alpha.
    if a != 0:
        raise ValueError("native source P7 alpha/reserved fourth channel changed")
    return r,g,b

def classify(original: tuple[int,int,int], painter_prev: tuple[int,int,int],
             painter_next: tuple[int,int,int], native: tuple[int,int,int]) -> dict:
    """Explicit stage-to-final distinctions; never infer a valid global shift."""
    if original != painter_prev:
        raise ValueError("source-original painter disagrees with SAME original callback")
    a,b,c = rgb5(original),rgb5(native),rgb5(painter_next)
    return {
        "original_callback_RGB5":list(a), "native_final_RGB5":list(b),
        "original_next_internal_painter_stage_RGB5":list(c),
        "correctly_registered_exact": a==b,
        "counterfactual_next_internal_stage_equal": b==c,
        "absolute_next_stage_difference":[abs(v-w) for v,w in zip(b,c)],
    }

def verify(original_outer: Path, painter: Path, native_outer: Path) -> dict:
    outer=zipfile.ZipFile(io.BytesIO(checked(original_outer, ORIGINAL_OUTER)))
    original=outer.read("original.zip")
    if sha(original) != ORIGINAL_NESTED: raise ValueError("nested 2014 Snes9x source changed")
    o=zipfile.ZipFile(io.BytesIO(original))
    p=zipfile.ZipFile(io.BytesIO(checked(painter, PAINTER_ZIP)))
    n=zipfile.ZipFile(io.BytesIO(checked(native_outer, NATIVE_OUTER)))
    payload=n.read("qa08-premath-source-images.zip")
    if sha(payload) != NATIVE_INNER: raise ValueError("nested genuine Win32 source image archive changed")
    source=zipfile.ZipFile(io.BytesIO(payload))
    report=n.read("qa08-premath-full263-ab.json")
    if sha(report) != REPORT_SHA: raise ValueError("genuine 263-frame PPU report changed")
    meta=json.loads(report)
    manifest=json.loads(o.read("qa08-original-2p-fullroute.json"))
    if (meta["native_actual_5484_guest_CRC_SHA256"]!=GUEST_SHA or
        meta["all_263_full_logical_256x224_source_frames"]!=263 or
        meta["baseline_wrong_RGB5"]!=890205 or
        meta["experimental_wrong_RGB5"]!=890205 or
        meta["corrected_real_pixels"]!=0 or meta["newly_wrong_real_pixels"]!=0 or
        manifest["actual_callbacks_captured"]!=263):
        raise ValueError("native CRC or independently authenticated full-route census changed")
    if (consumed_input(o.read("original.log")) != (INPUT_SHA,26) or
        consumed_input(p.read("qa08-original-medal/original.log")) != (INPUT_SHA,26)):
        raise ValueError("painter-to-original actual consumed mask route not authenticated")
    calls=p.read("qa08-original-medal/active-tile-candidates.log").decode("ascii").splitlines()
    observations=p.read("qa08-original-medal/original-layer-stages.log").decode("ascii").splitlines()
    if len(calls)!=252 or len(observations)!=360:
        raise ValueError("original source painter-stage witness population changed")
    finals={}
    for line in observations:
        m=LAYER.fullmatch(line)
        if m is None: raise ValueError("malformed original stage ownership record")
        f,y0,y1,x,y,stage,bg,mode,depth,color=m.groups()
        f,y0,y1,x,y,bg,mode=map(int,(f,y0,y1,x,y,bg,mode))
        if (y0,y1)!=(0,223) or mode!=3 or (x,y) not in POINTS:
            raise ValueError("source painter geometry or mode shifted")
        if stage=="FINAL":
            key=f,x,y
            if key in finals: raise ValueError("duplicate last Snes9x pixel writer")
            finals[key]=(int(depth,16),int(color,16))
    original_callbacks={a["real_original_snes9x_callback_frame"]:a
                        for a in manifest["each_authentic_callback"]}
    native_frames={a["guest"]:a for a in meta["per_frame"]}
    if len(original_callbacks)!=263 or len(native_frames)!=263 or len(finals)!=90:
        raise ValueError("source frames/stages missing or duplicated")
    rows=[]
    for guest in FRAMES:
        ocb=guest-1
        original_meta=original_callbacks[ocb]
        native_meta=native_frames[guest]
        if (original_meta["original_1based_frame"]!=guest or
            native_meta["original_callback"]!=ocb):
            raise ValueError("source callback alignment not exact")
        odata=o.read(f"frames/frame_{ocb:06}_256x224.raw")
        ndata=source.read(f"source/ur-baldosa-original-source-{guest:06}.pam")
        if (sha(odata)!=original_meta["original_unchanged_BGRX_sha256"] or
            sha(ndata)!=native_meta["experimental_P7_sha256"]):
            raise ValueError("actual 2014 callback/native P7 source SHA altered")
        for x,y in POINTS:
            pprevious=finals[(ocb,x,y)][1]
            pnext=finals[(guest,x,y)][1]
            cb=original_rgb(odata,x,y)
            native=native_rgb(ndata,x,y)
            result=classify(cb,rgb565_to_rgb8(pprevious),
                            rgb565_to_rgb8(pnext),native)
            # Independently verify the original 6-bit green -> RGB5
            # truncation against its actual same-source RGB565 stage.
            # Never infer a native winning OAM slot from this pixel.
            if result["original_next_internal_painter_stage_RGB5"] != list(rgb565_rgb5(pnext)):
                raise ValueError("original painter RGB565-to-RGB5 channel conversion drift")
            rows.append({"native_guest_frame":guest,
                "registered_original_callback":ocb,
                "counterfactual_original_internal_stage_frame":guest,
                "x":x,"y":y,"original_next_stage_depth":f"{finals[(guest,x,y)][0]:02x}",
                **result})
    real_equal=sum(r["correctly_registered_exact"] for r in rows)
    next_equal=sum(r["counterfactual_next_internal_stage_equal"] for r in rows)
    if (len(rows),real_equal,next_equal)!=(10,0,8):
        raise ValueError("authentic 2014/native medal phase discriminator changed")
    expected={(4032,205,115),(4176,205,115)}
    different={(r["native_guest_frame"],r["x"],r["y"]) for r in rows
               if not r["counterfactual_next_internal_stage_equal"]}
    if different!=expected or any(
        r["absolute_next_stage_difference"]!=[0,1,1] for r in rows
        if (r["native_guest_frame"],r["x"],r["y"]) in expected):
        raise ValueError("counterfactual two minimal shade differences changed")
    # Stronger SAME-FRAME independent original/native source checks: the
    # immutable 263-image archives include all 25 repeated medal appearances.
    # Only the two FRAMES above have original painter-stage instrumentation;
    # do not invent that absent producer evidence on the other 23 samples.
    recurrent=[]
    for guest in RECURRING_GUEST_FRAMES:
        cb=guest-1
        original_meta=original_callbacks.get(cb)
        native_meta=native_frames.get(guest)
        if (not original_meta or not native_meta or
            original_meta["original_1based_frame"]!=guest or
            native_meta["original_callback"]!=cb):
            raise ValueError("medal 48-field source frame registration missing")
        odata=o.read(f"frames/frame_{cb:06}_256x224.raw")
        ndata=source.read(f"source/ur-baldosa-original-source-{guest:06}.pam")
        if (sha(odata)!=original_meta["original_unchanged_BGRX_sha256"] or
            sha(ndata)!=native_meta["experimental_P7_sha256"]):
            raise ValueError("medal recurrence source frame SHA altered")
        for x,y in POINTS:
            ref_rgb5=rgb5(original_rgb(odata,x,y))
            native_rgb5=rgb5(native_rgb(ndata,x,y))
            recurrent.append((guest,x,y,ref_rgb5,native_rgb5))
    if len(recurrent)!=125 or any(ref==native for _,_,_,ref,native in recurrent):
        raise ValueError("authentic repeated medal RGB5 discrepancy no longer 125/125")
    original_gray=set(ref for _,x,y,ref,_ in recurrent if (x,y)==(205,139))
    native_gray=set(native for _,x,y,_,native in recurrent if (x,y)==(205,139))
    if (original_gray!={(15,15,15),(16,16,16),(17,17,17),(20,20,20)} or
        native_gray!={(14,7,9)}):
        raise ValueError("original gray-cycle overlap with medal mask changed")
    for x,y in POINTS:
        if (x,y)==(205,139): continue
        group={(ref,native) for _,px,py,ref,native in recurrent if (px,py)==(x,y)}
        if len(group)!=1:
            raise ValueError("recurrent colored medal sample changed across 25 source frames")
    return {
        "schema":"qa08-source-original-medal-internal-stage-vs-visible-callback/1",
        "real_source_original_artifact":ORIGINAL_NESTED,
        "real_source_painter_artifact":PAINTER_ZIP,
        "real_integrated_native_source_artifact":NATIVE_OUTER,
        "actual_native_guest_CRC_SHA256":GUEST_SHA,
        "real_observations":len(rows),
        "recurring_source_medal_frames":len(RECURRING_GUEST_FRAMES),
        "recurring_registered_pixel_disagreements":len(recurrent),
        "recurring_original_gray_205_139_four_phase_RGB5":[list(c) for c in sorted(original_gray)],
        "recurring_native_205_139_RGB5":list(next(iter(native_gray))),
        "authentic_original_callback_vs_native_RGB5_exact":real_equal,
        "counterfactual_next_original_internal_stage_vs_native_RGB5_exact":next_equal,
        "counterfactual_minor_shade_differences":len(rows)-next_equal,
        "native_guest_to_original_consumed_controller_identity_proven":False,
        "global_video_frame_shift_authorized":False,
        "source_2014_painter_winner_established":True,
        "native_2014_cpu_NMI_raster_phase_root_cause_proven":False,
        "shipping_original_result_parity_proven":False,
        "QA08_or_release_accepted":False,
        "samples":rows,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-outer",type=Path,required=True)
    p.add_argument("--painter",type=Path,required=True)
    p.add_argument("--native-outer",type=Path,required=True)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    try: result=verify(args.original_outer,args.painter,args.native_outer)
    except (OSError,ValueError,KeyError,UnicodeError,zipfile.BadZipFile) as e:
        p.exit(2,f"QA08_MEDAL_STAGE_REFUSED: {e}\n")
    data=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if args.out: args.out.write_text(data,encoding="utf-8")
    else: print(data)
    print("QA08_MEDAL_STAGE_OK original_match=0/10 next_stage_match=8/10 no_global_shift=1")

if __name__=="__main__":
    main()
