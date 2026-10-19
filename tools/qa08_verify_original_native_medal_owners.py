#!/usr/bin/env python3
"""QA08 archived original/native sprite winner crosswalk, diagnostic only.

Compare actual last surviving 2014 Snes9x source painter tile calls against
actual native Win32 4bpp fetches at TWO named internal fields. These are
different compiled executions; apparent stage agreement DOES NOT establish
same consumed guest-input/beam time or the correct original VIDEO callback.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import zipfile

ORIGINAL_SHA = "8387c413d42cf8d2da2a61ba3ec67e8375394f938171dc4d73a3e4ba567920e4"
NATIVE_SHA = "725ef03df3d43ff5d30b4bea944e32555974fb0b0e01af025da76ef88959b408"
ORIGINAL_CALLS = "qa08-original-medal/active-tile-candidates.log"
ORIGINAL_LAYERS = "qa08-original-medal/original-layer-stages.log"
NATIVE_LOG = "baseline/log.txt"
FRAMES = (4032, 4176)
POINTS = ((207,91),(205,115),(205,139),(225,96),(225,120))
OWNERS = {(207,91): None,(205,115):113,(205,139):114,(225,96):97,(225,120):96}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def member(path: Path, expected: str, name: str) -> bytes:
    blob=path.read_bytes()
    if sha(blob)!=expected: raise ValueError("immutable archived source ZIP SHA mismatch")
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None: raise ValueError("source archive CRC invalid")
        return archive.read(name)

def decode(record: str, prefix: str) -> dict[str,str]:
    if not record.startswith(prefix+" "): raise ValueError("wrong source event kind")
    result={}
    for item in record[len(prefix)+1:].split():
        if "=" not in item: raise ValueError("malformed source event")
        key,value=item.split("=",1)
        if key in result: raise ValueError("duplicate source field")
        result[key]=value
    return result

def inthex(value: str) -> int:
    return int(value,16)

def verify(original_zip: Path, native_zip: Path) -> dict:
    raw_calls=member(original_zip,ORIGINAL_SHA,ORIGINAL_CALLS).decode("ascii").splitlines()
    raw_stages=member(original_zip,ORIGINAL_SHA,ORIGINAL_LAYERS).decode("ascii").splitlines()
    log=member(native_zip,NATIVE_SHA,NATIVE_LOG).decode("utf-8").splitlines()
    if len(raw_calls)!=252 or len(raw_stages)!=360:
        raise ValueError("original 2014 sprite/stage population changed")
    originals=defaultdict(list)
    for line in raw_calls:
        data=decode(line,"UR_QA08_ORIGINAL_ACTIVE_MEDAL_TILE")
        key=(int(data["frame"]),int(data["x"]),int(data["y"]))
        originals[key].append(data)
    final_depth={}
    for line in raw_stages:
        data=decode(line,"UR_QA08_ORIGINAL_MEDAL_LAYER")
        if data["stage"]!="FINAL": continue
        if data["range"]!="0,223" or data["bgmode"]!="3":
            raise ValueError("original Snes9x source display geometry/mode changed")
        key=(int(data["frame"]),int(data["x"]),int(data["y"]))
        if key in final_depth: raise ValueError("duplicate original final layer")
        final_depth[key]=inthex(data["depth"])
    if len(final_depth)!=90: raise ValueError("missing authentic original painter fields")
    fetched=defaultdict(list)
    natives={}
    native_oam=0
    for line in log:
        if line.startswith("UR_QA08_WIN_OBJ_FETCH "):
            data=decode(line,"UR_QA08_WIN_OBJ_FETCH")
            key=(int(data["frame"]),int(data["x"]),int(data["raster_y"]))
            fetched[key].append(data)
        elif line.startswith("UR_QA08_WIN_PIXEL_OWNER "):
            data=decode(line,"UR_QA08_WIN_PIXEL_OWNER")
            key=(int(data["frame"]),int(data["x"]),int(data["raster_y"]))
            if key in natives:raise ValueError("duplicate native source final pixel")
            natives[key]=data
        elif line.startswith("UR_QA08_WIN_OAM_LINE "):
            native_oam+=1
    if len(natives)!=25 or sum(map(len,fetched.values()))!=25 or native_oam!=175:
        raise ValueError("actual native PPU fetch, owner or OAM observations changed")
    out=[]
    for frame in FRAMES:
        for x,y in POINTS:
            key=frame,x,y
            src=originals.get(key,[])
            nfetch=fetched.get(key,[])
            n=natives.get(key)
            if not n or len(src) not in (2,4):raise ValueError("missing source-original pixel witness")
            # Original 2014 renders each field twice: each paint pass must
            # independently choose the SAME visible slot or BG negative.
            half=len(src)//2
            first,second=src[:half],src[half:]
            if first != second:
                # RGB-before history may differ; only compare immutable
                # paint ownership/tile/alpha/priority fields.
                fields=("slot","objname","src_tile","changed_z","zafter")
                if [tuple(d[k] for k in fields) for d in first] != [
                    tuple(d[k] for k in fields) for d in second]:
                    raise ValueError("original per-pass writer identity shifted")
            winner=OWNERS[(x,y)]
            real=[d for d in first if d["changed_z"]=="1"]
            if winner is None:
                if real or nfetch or final_depth[key]!=0x27 or n["main"]!="0":
                    raise ValueError("BG negative control was promoted into sprite")
                out.append({"guest_internal_field":frame,"pixel":[x,y],
                            "original_owner":"BG0","native_owner":"background (main enum 0)",
                            "visible_OBJ_winner_equivalent":True})
                continue
            if (len(real)!=1 or int(real[0]["slot"])!=winner or
                final_depth[key]!=0x28 or n["main"]!="4" or
                len(nfetch) not in (1,2)):
                raise ValueError("source-original/native last visible OBJ winner changed")
            source_winner=real[0]
            actual_winner=nfetch[-1]
            if (int(actual_winner["slot"])!=winner or
                (inthex(source_winner["src_tile"]) & 255) !=
                   (inthex(actual_winner["used_tile"]) & 255) or
                (inthex(source_winner["objname"]) & 255) !=
                   (inthex(actual_winner["oam_tile"]) & 255) or
                inthex(actual_winner["writer_obj"])!=inthex(n["obj"])):
                raise ValueError("cross-emulator source winner/4bpp/OAM suffix mismatch")
            expected_contenders=2 if x==225 else 1
            if len(nfetch)!=expected_contenders or len(first)!=expected_contenders:
                raise ValueError("sprite overlap contender population changed")
            if len(nfetch)==2 and (int(nfetch[0]["slot"])!=winner+2 or
                                    first[-1]["changed_z"]!="0"):
                raise ValueError("occluded overlapping source sprite incorrectly became winner")
            out.append({"guest_internal_field":frame,"pixel":[x,y],
                        "original_owner":"OBJ"+str(winner),
                        "native_owner":"OBJ"+str(winner),
                        "original_source_tile":source_winner["src_tile"],
                        "native_used_tile":actual_winner["used_tile"],
                        "original_OAM_name":source_winner["objname"],
                        "native_OAM_tile":actual_winner["oam_tile"],
                        "native_effective_encoded_obj":n["obj"],
                        "native_actual_last_fetch":True,
                        "visible_OBJ_winner_equivalent":True})
    if len(out)!=10 or sum(row["original_owner"].startswith("OBJ") for row in out)!=8:
        raise ValueError("crosswalk sample population invalid")
    return {
      "schema":"qa08-original-2014-and-native-4bpp-visible-winner-crosswalk/1",
      "original_Snes9x_source_archive_sha256":ORIGINAL_SHA,
      "native_actual_4bpp_source_archive_sha256":NATIVE_SHA,
      "original_sprite_pixels_matching_native_slot_and_tile_suffix":8,
      "original_native_background_negative_controls":2,
      "overlapping_sprite_pixels_with_same_winning_low_OAM_slot":4,
      "correct_original_to_native_video_frame_registration_proven":False,
      "same_original_native_guest_consumed_input_and_beam_proven":False,
      "original_native_color_math_or_CGRAM_parity_proven":False,
      "native_misaligned_2014_callback_pixels_corrected":0,
      "release_or_QA08_gate_accepted":False,
      "samples":out
    }

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-painter",type=Path,required=True)
    p.add_argument("--native-4bpp",type=Path,required=True)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    try: report=verify(args.original_painter,args.native_4bpp)
    except (OSError,ValueError,KeyError,UnicodeError,zipfile.BadZipFile) as e:
        p.exit(2,"QA08_MEDAL_OWNERS_REFUSED: "+str(e)+"\n")
    data=json.dumps(report,indent=2,sort_keys=True)+"\n"
    if args.out: args.out.write_text(data,encoding="utf-8")
    else: print(data)
    print("QA08_ORIGINAL_NATIVE_OBSERVED_WINNERS_OK OBJ=8/8 BG=2/2 release=0")

if __name__=="__main__":
    main()
