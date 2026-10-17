#!/usr/bin/env python3
"""Recompute original Snes9x vs native Windows 1P/2P complete RGB5 samples.

Input is four independent archived source-producer ZIPs. Validate complete
archive hashes, the per-frame raw pixel digests and predeclared callbacks.
No crop, pixel mask, temporal search, colour substitution or release pass.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import zipfile

W,H,FIRST,STEP=256,224,1280,16
PX=W*H
HEADER=b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n"
USA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
PINS={
 "oneplayer":{
  "original":"1b2fb01338380dc7e4d093ccbb0a5778bd04388945ee0bc7eb5b910d4de3ca59",
  "windows":"db0dc0aacde50503aee0cdbe8047dc22ef1550233afd83c4c69fa27099f1d005",
  "orig_json":"qa08-original-1p-sparse.json",
  "win_json":"qa08-windows-original-oneplayer-coverage.json","last":5440},
 "twoplayer":{
  "original":"72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e",
  "windows":"f01ab5a4888c227f306a0b9cd89e67710a4b41cad4c22867072280a17811fa82",
  "orig_json":"qa08-original-2p-fullroute.json",
  "win_json":"qa08-windows-2p-fullroute.json","last":5472}
}
GREYS=frozenset((123,132,140,165))
GREY_FRAMES=(4064,4176,4288,4400,4512,4624,4736,4848,4960,5072,5184,5296,5408)
ONE_OPEN=tuple(range(1280,1361,16))
TWO_OPEN=tuple(range(1280,1633,16))
ONE_FINISH=(3968,3984,4000)
TWO_FINISH=(3792,3872)
ONE_RETURN=tuple(range(4016,5441,16))
MEDALS=(4032,4080,4128,4224,4272,4320,4368,4416,4464,4560,4608,
        4656,4704,4752,4800,4896,4944,4992,5040,5088,5136)

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def check(actual,expected,label):
    if actual!=expected:
        raise ValueError(f"source or pixel identity drift {label}: {actual!r} != {expected!r}")

def compare(original:bytes,native:bytes,width:int=W,height:int=H)->dict:
    """Original BGRX 6-bit green -> RGB5; native actual post-PPU RGBA."""
    n=width*height
    if len(original)!=n*4 or len(native)!=n*4:
        raise ValueError("truncated/unmasked original 4-byte logical pixels")
    mask=bytearray(n)
    nongray=bytearray(n)
    left,top,right,bottom=width,height,-1,-1
    wrong=gray=0
    colors=Counter()
    wrong_destinations=defaultdict(set)
    wrong_src_counts=Counter()
    unchanged_src_colors=set()
    for p in range(n):
        i=p*4
        green5=original[i+1]>>3
        src=(original[i+2],(green5<<3)|(green5>>2),original[i])
        dst=tuple(native[i:i+3])
        if src==dst:
            unchanged_src_colors.add(src)
            continue
        wrong_destinations[src].add(dst)
        wrong_src_counts[src]+=1
        mask[p]=1
        wrong+=1
        if (src[0] in GREYS and dst[0] in GREYS
            and src[0]==src[1]==src[2] and dst[0]==dst[1]==dst[2]):
            gray+=1
        else:
            nongray[p]=1
        x,y=p%width,p//width
        left,top=min(left,x),min(top,y)
        right,bottom=max(right,x),max(bottom,y)
        colors[(src,dst)]+=1
    nonsingleton={src for src,dests in wrong_destinations.items() if len(dests)>1}
    return {"wrong":wrong,"gray":gray,"nongray":wrong-gray,
            "wrong_reference_RGB5_with_multiple_destinations":len(nonsingleton),
            "wrong_pixels_requiring_nonfunctional_RGB5_mapping":sum(wrong_src_counts[src] for src in nonsingleton),
            "wrong_pixels_reference_RGB5_unchanged_elsewhere":sum(wrong_src_counts[src] for src in wrong_src_counts if src in unchanged_src_colors),
            "distinct_wrong_reference_RGB5":len(wrong_destinations),
            "max_distinct_wrong_destinations_per_source_RGB5":max((len(v) for v in wrong_destinations.values()),default=0),
            "bounds":[left,top,right,bottom] if wrong else None,
            "mask":bytes(mask),"nongray_mask":bytes(nongray),
            "swatches":[(list(a),list(b),n) for (a,b),n in colors.most_common(6)]}

def load(mode:str,original_zip:Path,windows_zip:Path)->dict:
    pins=PINS[mode]
    check(sha(original_zip.read_bytes()),pins["original"],mode+" original ZIP")
    check(sha(windows_zip.read_bytes()),pins["windows"],mode+" Windows ZIP")
    images={}
    with zipfile.ZipFile(original_zip) as o,zipfile.ZipFile(windows_zip) as w:
        for a in (o,w):
            members=a.namelist()
            if len(members)!=len(set(members)):
                raise ValueError("duplicate ZIP source members")
        om=json.loads(o.read(pins["orig_json"]))
        wm=json.loads(w.read(pins["win_json"]))
        if mode=="oneplayer":
            check(om["USA_ROM_sha256"],USA,"original 1P USA ROM")
            original_hash={int(f["original_callback"]):f["actual_unmodified_BGRX_sha256"]
                           for f in om["all_original_source_frame_hashes"]}
            win_hash=wm["complete_source_RGBA_P7_sha256_by_frame"]
        else:
            check(om["unaltered_USA_ROM_sha256"],USA,"original 2P USA ROM")
            check(wm["original_USA_ROM_sha256"],USA,"native 2P USA ROM")
            original_hash={int(f["real_original_snes9x_callback_frame"]):
                           f["original_unchanged_BGRX_sha256"]
                           for f in om["each_authentic_callback"]}
            win_hash=wm["source_frame_P7_SHA256_by_guest"]
        frames=tuple(range(FIRST,pins["last"]+1,STEP))
        check(len(original_hash),len(frames),mode+" original manifest")
        check(len(win_hash),len(frames),mode+" native manifest")
        for guest in frames:
            callback=guest-1
            raw=o.read(f"frames/frame_{callback:06d}_256x224.raw")
            p7=w.read(f"source/ur-baldosa-original-source-{guest:06d}.pam")
            check(sha(raw),original_hash.get(callback),f"{mode} original {callback}")
            check(sha(p7),win_hash.get(str(guest)),f"{mode} native {guest}")
            if len(p7)!=len(HEADER)+PX*4 or not p7.startswith(HEADER):
                raise ValueError("native logical 256x224 PAM corrupt or cropped")
            images[guest]=compare(raw,p7[len(HEADER):])
    check(len(images),261 if mode=="oneplayer" else 263,mode+" source count")
    return images

def partition(one:dict,two:dict)->dict:
    def total(d,frames,key="wrong"):
        return sum(d[f][key] for f in frames)
    exact1=sum(x["wrong"]==0 for x in one.values())
    exact2=sum(x["wrong"]==0 for x in two.values())
    check((exact1,total(one,one)),(162,19153),"1P all source pixels")
    check((exact2,total(two,two)),(203,385373),"2P all source pixels")
    check(total(one,ONE_OPEN),1050,"1P menu")
    check(total(one,ONE_FINISH),520,"1P finish")
    check(total(one,ONE_RETURN),17583,"1P cursor return")
    assigned1=set(ONE_OPEN+ONE_FINISH+ONE_RETURN)
    check(total(one,(f for f in one if f not in assigned1)),0,"1P other")
    for frame,row in one.items():
        b=row["bounds"]
        if b and (b[2]-b[0]+1>32 or b[3]-b[1]+1>18):
            raise ValueError(f"1P cursor escaped 32x18 box guest={frame}")
    check(total(two,TWO_OPEN),4487,"2P opening")
    check([two[f]["wrong"] for f in TWO_FINISH],[1,1],"2P finish")
    check(two[4016]["wrong"],54709,"2P blackout")
    check(total(two,GREY_FRAMES,"gray"),318775,"2P gray cycle")
    four=[f for f in GREY_FRAMES if two[f]["nongray"]]
    check(four,[4176,4512,4848,5184],"overlaid medal gray frames")
    check([two[f]["nongray"] for f in four],[296]*4,"medals in gray frames")
    mask=two[MEDALS[0]]["mask"]
    for f in MEDALS:
        check(two[f]["wrong"],296,f"medal pixels {f}")
        check(two[f]["mask"],mask,f"medal shape {f}")
    for f in four:
        check(two[f]["nongray_mask"],mask,f"gray medal shape {f}")
    # A single-valued frame-wide RGB5->RGB5 LUT cannot map one RGB5 input
    # to multiple wrong outputs. This does not determine whether genuine
    # per-sprite palette indices, object priority or colour math differ.
    for case,frame,expected in ((one,1280,233),(two,1280,196)):
        check(case[frame]["wrong_reference_RGB5_with_multiple_destinations"],0,
              f"early cursor single-valued swatches {frame}")
        check(case[frame]["wrong_pixels_reference_RGB5_unchanged_elsewhere"],
              expected,f"global RGB5 remap counterexample {frame}")
    ambiguity=Counter(two[f]["wrong_pixels_requiring_nonfunctional_RGB5_mapping"]
                      for f in MEDALS)
    check(dict(ambiguity),{290:5,294:16},"medal single RGB5 LUT falsification")
    for f in MEDALS:
        check(two[f]["wrong_reference_RGB5_with_multiple_destinations"],28,
              f"medal RGB5 input/output ambiguity {f}")
        check(two[f]["wrong_pixels_reference_RGB5_unchanged_elsewhere"],267,
              f"medal source-colour unchanged elsewhere {f}")
        check(two[f]["max_distinct_wrong_destinations_per_source_RGB5"],8,
              f"medal maximum destinations {f}")
    check(two[MEDALS[0]]["bounds"],[202,91,227,153],"2P medal box")
    assigned2=set(TWO_OPEN+TWO_FINISH+GREY_FRAMES+MEDALS+(4016,))
    check(total(two,(f for f in two if f not in assigned2)),0,"unexplained 2P frames")
    return {
      "schema":"qa08-recomputed-source-pinned-full-raster-sparse-residual-partition/1",
      "source_pixel_geometry":[W,H],"source_pixels_per_frame":PX,
      "source_original_native_frame_hashes_verified":len(one)+len(two),
      "original_snes9x_callback_for_native_guest":"f-1 precommitted; no frame search",
      "original_colour_normalization":"green6_to_green5 only; no mask, crop, shift, recolour",
      "oneplayer":{"frames":261,"exact":exact1,"incorrect_RGB5_pixels":19153,
                   "opening_cursor_pixels":1050,"finish_cursor_pixels":520,
                   "results_cursor_pixels":17583,"moving_race_pixel_errors":0},
      "twoplayer":{"frames":263,"exact":exact2,"incorrect_RGB5_pixels":385373,
                   "opening_cursor_pixels":4487,"finish_pixels":2,"blackout_pixels":54709,
                   "four_gray_CGRAM_signature_pixels":318775,"result_medal_pixel_errors":7400,
                   "non_gray_medal_mask_SHA256":sha(mask),
                   "gray_frames_with_same_296_pixel_medal_mask":four,
                   "21_distinct_results_frames_with_same_mask":list(MEDALS)},
      "palette_only_hypothesis":{
          "opening_oneplayer_guest1280":{"single_valued_wrong_RGB5_map":True,
                                      "wrong_pixels_original_colour_unchanged_elsewhere":233},
          "opening_twoplayer_guest1280":{"single_valued_wrong_RGB5_map":True,
                                      "wrong_pixels_original_colour_unchanged_elsewhere":196},
          "result_medal_21_frames_single_RGB5_LUT_impossible":True,
          "inconsistent_wrong_pixels_per_medal_frame_distribution":{"290":5,"294":16},
          "each_medal_frame_wrong_pixels":296,
          "each_medal_frame_distinct_original_RGB5_with_multiple_wrong_outputs":28,
          "each_medal_frame_wrong_pixels_same_colour_unchanged_elsewhere":267,
          "max_different_native_RGB5_for_same_original_RGB5":8,
          "per_sprite_index_or_priority_or_math_cause_adjudicated":False,
          "global_palette_recolouring_admitted":False},
      "source_archives":{k:{"original":v["original"],"windows":v["windows"]}
                         for k,v in PINS.items()},
      "source_accepted_as_full_CPU_APU_camera_frame_phase":False,
      "effective_final_pixel_OBJ_window_and_colour_math_ownership_proven":False,
      "released_or_HDriver_art_likeness_approved":False,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("original-1p","windows-1p","original-2p","windows-2p","out"):
        p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    one=load("oneplayer",a.original_1p,a.windows_1p)
    two=load("twoplayer",a.original_2p,a.windows_2p)
    result=partition(one,two)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("QA08_ARCHIVED_RGB5_PARTITION exact_1p=162/261 exact_2p=203/263 "
          "wrong_1p=19153 wrong_2p=385373 release=0")

if __name__=="__main__":
    main()
