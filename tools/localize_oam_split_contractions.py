#!/usr/bin/env python3
"""Localize the two PAL-line contractions inside split-camera racer projection."""
from __future__ import annotations
import difflib, json
from analyze_racer_oam_structure_island import ROOT, ROMS, cpu_to_offset, offset_to_cpu

PAIRS=[
 ("split_p2_projection","82:AF4F","82:AFD4",
  {"pal-prototype-1994-11-29":("82:AF40","82:AFC3"),"europe-retail":("82:AF56","82:AFD9")}),
 ("split_p1_projection","82:AFD5","82:B056",
  {"pal-prototype-1994-11-29":("82:AFC4","82:B043"),"europe-retail":("82:AFDA","82:B059")}),
]

def opcodes(block: bytes, base: int):
    # We only use this to render byte coordinates around SequenceMatcher edits;
    # analyzer roles remain authoritative elsewhere.
    return block

def compare(src: bytes, dst: bytes, src_base: int, dst_base: int):
    sm=difflib.SequenceMatcher(a=list(src),b=list(dst),autojunk=False)
    edits=[]
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag=="equal": continue
        edits.append({
          "tag":tag,
          "usa_start":offset_to_cpu(src_base+i1),
          "usa_end":offset_to_cpu(src_base+i2-1) if i2>i1 else None,
          "usa_size":i2-i1,
          "usa_hex":src[i1:i2].hex(" "),
          "other_start":offset_to_cpu(dst_base+j1),
          "other_end":offset_to_cpu(dst_base+j2-1) if j2>j1 else None,
          "other_size":j2-j1,
          "other_hex":dst[j1:j2].hex(" "),
        })
    return edits

def build():
    blobs={k:p.read_bytes() for k,p in ROMS.items()}
    usa=blobs["usa-retail"]
    rows=[]
    for name,us,ue,targets in PAIRS:
        u0=cpu_to_offset(us); u1=cpu_to_offset(ue)+1
        row={"name":name,"usa_start":us,"usa_end":ue,"usa_size":u1-u0,"builds":{}}
        for build,(bs,be) in targets.items():
            b0=cpu_to_offset(bs); b1=cpu_to_offset(be)+1
            row["builds"][build]={
              "start":bs,"end":be,"size":b1-b0,
              "net_size_delta":(b1-b0)-(u1-u0),
              "edits":compare(usa[u0:u1],blobs[build][b0:b1],u0,b0),
            }
        rows.append(row)
    return {"schema_version":1,"purpose":"Localize the two 2-byte PAL-line contractions inside split-camera OAM projection.","regions":rows}

def main():
    result=build()
    print("OAM_CONTRACTION_JSON="+json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
