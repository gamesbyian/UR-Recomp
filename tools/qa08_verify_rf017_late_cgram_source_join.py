#!/usr/bin/env python3
"""Independently verify real current RF017 Windows late CGRAM against 2014 Snes9x.

Archive-only: six actual native CPU $2121/$2122 writer packets from a compiled
Windows PE and the SHA-bound original 2014 Snes9x 112-field source journal.
No second emulator, renderer, temporal shift, RGB mapping or guest mutation.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import zipfile

ORIGINAL_SHA = "d725ee45db1b66d098e79499263dd089dba80a26de517c30db674f91e20f80a8"
CURRENT_SHA = "a62f0c228e85c741a8f1da0b92a4444f9091681c065c93c8a678b4ee2bb6f2ef"
ORIGINAL_TSV_SHA = "7e1f36a58fe52205011c9f34d4704c6311d929ac75caf11ea7e6958a6cc386c4"
CURRENT_JSON_SHA = "33e27bc151c020e38beb40672fe67e2cc74bc43b8456bdbfd72af6f9c04dedda"
GUEST_SHA = "b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568"
PE_SHA = "41433d4e7bf678c191799d94d01b2ad3984cbc9fd5aa168cb5b5160b15c6d5b4"
SCRIPT_SHA = "ef74ec51fa585aa76652f4a14d2727f0074434b3925522ab2607e3bd29aa0194"
SLOTS = {0x6c,0x6d,0x6e,0x6f}
PAIRS = ((5155,5157,"direct"),(5162,5164,"direct"),
         (5169,5171,"direct"),(5176,5178,"direct"),
         (5183,5157,"28-field prior-cycle"),(5190,5164,"28-field prior-cycle"))
COLORS = {0x4210,0x4631,0x4a52,0x56b5}

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def rgb15_group(rows:list[tuple[int,int,int,int,str]])->dict[int,int]:
    if len(rows)!=12:
        raise ValueError("four genuine CGRAM address/low/high transactions required")
    result={}
    for i in range(0,12,3):
        a,l,h=rows[i:i+3]
        if ([a[2],l[2],h[2]]!=[0x2121,0x2122,0x2122] or
            a[3] not in SLOTS or a[3] in result or
            any(e[4]!="cpu" for e in (a,l,h)) or
            not (a[:2]<l[:2]<h[:2])):
            raise ValueError("source port address/data order, beam or source tag differs")
        result[a[3]]=l[3]|(h[3]<<8)
    if set(result)!=SLOTS or set(result.values())!=COLORS:
        raise ValueError("not all four genuine result palette slots and values")
    return dict(sorted(result.items()))

def original_groups(raw:bytes)->dict[int,dict[int,int]]:
    if sha(raw)!=ORIGINAL_TSV_SHA:
        raise ValueError("authentic Snes9x source ring SHA changed")
    lines=raw.decode("ascii").splitlines()
    if lines[:2]!=["#range=5072..5184",
                   "frame\tvcounter\thcounter\taddr\tvalue\tsource"]:
        raise ValueError("original CPU port journal identity changed")
    groups=defaultdict(list)
    for line in lines[2:]:
        if line.startswith("#"):
            continue
        f,v,h,port,val,source=line.split("\t")
        f=int(f);v=int(v);h=int(h)
        if not 5072<=f<=5184 or v not in (225,226) or not 0<=h<=340:
            raise ValueError("unqualified original CPU writer frame/beam")
        groups[f].append((v,h,int(port,16),int(val,16),source))
    expected={5073+7*k for k in range(16)}
    if set(groups)!=expected or sum(map(len,groups.values()))!=192:
        raise ValueError("missing 2014 original 112-field CGRAM source")
    return {f:rgb15_group(rows) for f,rows in groups.items()}

def native_groups(receipt:dict)->dict[int,dict[int,int]]:
    if (receipt.get("actual_compiled_Windows_PE_sha256")!=PE_SHA or
        receipt.get("actual_guest_CRC_sha256")!=GUEST_SHA or
        receipt.get("actual_native_guest_frames")!=5484 or
        receipt.get("authentic_two_pad_route_SHA256")!=SCRIPT_SHA or
        receipt.get("CPU_clock_phase_fix_authorized") is not False):
        raise ValueError("not the authentic native Windows compiler/guest source")
    data=receipt["live_CGRAM"]
    if (data["actual_native_writer_frame_sequence"]!=[p[0] for p in PAIRS] or
        data["genuine_CPU_input_CGRAM_port_events"]!=72 or
        data["guest_or_palette_renderer_fix_authorized"] is not False):
        raise ValueError("missing native late current RF017 writer witness")
    groups={}
    for item in data["palette_6c_to_6f_by_frame"]:
        frame=item["native_CPU_input_host_frame"]
        events=item["actual_twelve_port_events"]
        if frame in groups or len(events)!=12:
            raise ValueError("duplicate/native truncated writer field")
        source=[]
        for e in events:
            if (e["frame"]!=frame or e["source"]!=0 or e["port"] not in (33,34)
                or e["v"] not in (225,226) or not 0<=e["h"]<=1364 or
                e["second"] not in (0,1) or not 0<=e["pointer"]<=255 or
                not 0<=e["value"]<=255):
                raise ValueError("unqualified actual Windows PPU input event")
            source.append((e["v"],e["h"],0x2100+e["port"],e["value"],"cpu"))
        for j in range(4):
            a,l,h=events[3*j:3*j+3]
            if l["pointer"]!=a["value"] or h["pointer"]!=a["value"] or (
                l["second"],h["second"])!=(0,1):
                raise ValueError("native CGRAM CPU write pointer/latch differs")
        words=rgb15_group(source)
        if ([f"{words[k]:04x}" for k in sorted(words)] !=
            item["colour_words_6c_to_6f_RGB15"]):
            raise ValueError("real native palette does not match witness source bytes")
        groups[frame]=words
    if sorted(groups)!=[p[0] for p in PAIRS]:
        raise ValueError("native packet identity mismatch")
    return groups

def verify(original_archive:Path,current_archive:Path)->dict:
    if sha(original_archive.read_bytes())!=ORIGINAL_SHA or (
        sha(current_archive.read_bytes())!=CURRENT_SHA):
        raise ValueError("original/current RF017 source artifact changed")
    with zipfile.ZipFile(original_archive) as o,zipfile.ZipFile(current_archive) as w:
        raw=o.read("registers/qa08-results-5072-5184-cgram-history.tsv")
        native_json=w.read("qa08-current-rf017-late-cgram.json")
    if sha(native_json)!=CURRENT_JSON_SHA:
        raise ValueError("native PE writer receipt replaced")
    original=original_groups(raw)
    native=native_groups(json.loads(native_json))
    joins=[]
    for current,ref,kind in PAIRS:
        if native[current]!=original[ref]:
            raise ValueError("authentic current RF017/source palette mismatch")
        joins.append({"native_CPU_input_frame":current,
            "observed_original_2014_CPU_write_frame":ref,
            "match_type":kind,
            "actual_four_RGB15_words":{f"{slot:02x}":f"{native[current][slot]:04x}"
                                       for slot in sorted(SLOTS)},
            "original_vs_native_CPU_instruction_time_aligned":False})
    return {"schema":"qa08-current-RF017-real-Windows-vs-2014-late-CGRAM-writer/1",
            "actual_Windows_PE_sha256":PE_SHA,
            "actual_native_guest_CRC_sha256":GUEST_SHA,
            "source_original_archive_sha256":ORIGINAL_SHA,
            "source_native_archive_sha256":CURRENT_SHA,
            "original_2014_CPU_port_journal_SHA256":ORIGINAL_TSV_SHA,
            "actual_Windows_CGRAM_receipt_SHA256":CURRENT_JSON_SHA,
            "source_original_2014_writers":192,
            "actual_current_native_CPU_port_records":72,
            "actual_current_native_writer_fields":6,
            "exact_CGRAM_four_RGB15_word_source_matches":len(joins),
            "direct_source_frame_pair_matches":4,
            "prior_28_field_phase_matches":2,
            "actual_native_original_CPU_writer_source_pairs":joins,
            "two_source_frame_label_lead_reobserved_current_RF017":True,
            "source_timestamp_or_NMI_instruction_clock_root_cause_proven":False,
            "original_vs_native_H_counter_units_equivalent":False,
            "blanking_and_medal_effective_owner_resolved":False,
            "output_palette_or_frame_shift_approved":False,
            "QA08_QA10_4K_art_or_release_accepted":False}

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--native",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=verify(a.original,a.native)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("QA08_LATE_CGRAM_SOURCE_JOIN",result["exact_CGRAM_four_RGB15_word_source_matches"],
          "native72_original192 guest_CRC_unchanged=1 no_clock_fix=1")
if __name__=="__main__":main()
