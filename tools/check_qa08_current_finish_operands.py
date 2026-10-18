#!/usr/bin/env python3
"""Audit bounded current RF017 real Windows PPU source finish operand witness."""
from __future__ import annotations
import argparse,json
from pathlib import Path
SOURCE_GUEST="b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568"
SAMPLES=((1856,96,0),(1856,97,0),(3680,92,0),(3680,93,0),
         (3680,96,0),(3680,97,0),(3792,121,165),(3872,121,165))
def brightness5(colour:int,brightness:int)->int:
    if not 0<=colour<=31 or not 0<=brightness<=15:
        raise ValueError("raw 5-bit colour or brightness out of range")
    return (colour*brightness+7)//15
def predict(row:dict)->list[int]:
    main=row["pre"]
    b=row["br"]
    if len(main)!=3:raise ValueError("non-3-channel true PPU operand")
    if row["math"]==0:
        if row["sub"]!=-1 or row["subPre"] is not None or row["post"]!=main:
            raise ValueError("math-off control PPU shadow not original input")
        return [brightness5(v,b) for v in main]
    if row["math"]!=1 or row["sub"]!=4 or row["main"]!=2 or row["subPre"] is None:
        raise ValueError("missing executed BG3-plus-OBJ full-add PPU layer owner")
    sub=row["subPre"]
    if row["post"]!=[min(31,v+w) for v,w in zip(main,sub)]:
        raise ValueError("native actual postmath add contradicts operands")
    return [min(31,brightness5(v,b)+brightness5(w,b)) for v,w in zip(main,sub)]
def verify(doc:dict)->dict:
    if doc.get("schema")!="qa08-source-qualified-eight-live-current-RF017-finish-PPU-operands/1":
        raise ValueError("wrong source result schema")
    source=doc["source"]
    if (source["guest_crc_sha256"]!=SOURCE_GUEST or source["real_guest_simulations"]!=5484
        or source["artifact_id"]!=12115774634 or
        len(doc["arithmetic"]["samples"])!=8):
        raise ValueError("live real Windows RF017 source provenance absent")
    values=doc["arithmetic"]["samples"]
    keys=[(x["f"],x["x"],x["y"]) for x in values]
    if keys!=list(SAMPLES):raise ValueError("original/native source eight pixel keys changed")
    n=0
    for row in values:
        if row["br"]!=(15 if row["f"]==1856 else 7):
            raise ValueError("actual observed source brightness drift")
        observed=[int(v) for v in row["final"]]
        native5=[v>>3 for v in observed]
        expected5=[v for v in row["original"]]
        if (predict(row)!=row["predicted"] or row["predicted"]!=expected5):
            raise ValueError("brightness-before-operand-ADD source hypothesis disproved")
        if row["f"]==1856 and native5!=expected5:
            raise ValueError("source-good moving control silently changed")
        if row["f"] in (3792,3872) and native5!=expected5:
            raise ValueError("current actual BG3/OBJ RGB5 control differs")
        if row["f"]==3680:
            # Source-selected adjacent 93/97 are *intentionally exact* native
            # controls; only 92/96 are the nearby real incorrect pixels.
            expected_equal = row["x"] in (93,97)
            if (native5==expected5)!=expected_equal:
                raise ValueError("finish adjacent native exact/wrong controls changed")
        n+=1
    return {"real_source_guest_CRC":SOURCE_GUEST,"samples":n,
            "exact_snes9x_5bit_preoperand_brightness_predictions":n,
            "native_moving_controls":2,"unmodified_guest_and_PPU":True,
            "source_original_same_instruction_or_all_frame_parity_proven":False,
            "renderer_patch_QA_or_release_admitted":False}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--receipt",type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(verify(json.loads(args.receipt.read_text())),
                     sort_keys=True))
if __name__=="__main__":main()
