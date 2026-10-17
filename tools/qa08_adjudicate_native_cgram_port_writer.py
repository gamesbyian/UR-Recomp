#!/usr/bin/env python3
"""Source-bound QA-08 original/native CGRAM port writer adjudication.

Use exactly three immutable GitHub Actions archives: original 2014 Snes9x
$2121/$2122 ring, a previous uninstrumented Windows 2P PPU source, and the
same guest with a read-only native $2121/$2122 writer observer. Compares
authentic writes, original beam labels, four 15-bit palette words, all
263 actual Windows raster hashes and the 5484-frame CRC transcript.
No guest clock adjustment, PPU edit, colour mapping or frame search.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import zipfile

ORIGINAL_ZIP="d725ee45db1b66d098e79499263dd089dba80a26de517c30db674f91e20f80a8"
BASELINE_ZIP="f01ab5a4888c227f306a0b9cd89e67710a4b41cad4c22867072280a17811fa82"
OBSERVED_ZIP="4b55a33917a5941e87d507ceb8af01391c01fc4574a2543fab3f0b3cf35402f0"
SOURCE_TSV_SHA="7e1f36a58fe52205011c9f34d4704c6311d929ac75caf11ea7e6958a6cc386c4"
CRC_5484="c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876"
# First two are direct source frames. Last two are earlier physically observed
# source palette phases (28-frame periodicity) used solely as state witnesses.
SOURCE_PAIRS=((5169,5171,"direct"),(5176,5178,"direct"),
              (5183,5157,"cyclic_prior"),(5190,5164,"cyclic_prior"))
SLOTS=(0x6c,0x6d,0x6e,0x6f)
COLORS={0x4210,0x4631,0x4a52,0x56b5}
SCHEMA="qa08-real-original-native-CPU-CGRAM-port-write-chronology/1"


def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def checked_zip(path:Path, expected:str)->zipfile.ZipFile:
    if sha(path.read_bytes())!=expected:
        raise ValueError("immutable original/native source ZIP changed")
    return zipfile.ZipFile(path)


def decode_group(values:list[tuple[int,int,int,int,int,str]])->dict[int,int]:
    """Decode 4 groups of $2121 + 2x$2122 without fixing broken port order."""
    if len(values)!=12:
        raise ValueError("four authentic 15-bit CGRAM transactions required")
    result={}
    for index in range(0,12,3):
        addr=values[index]
        lo=values[index+1]
        hi=values[index+2]
        if ([addr[2],lo[2],hi[2]]!=[0x2121,0x2122,0x2122]
            or addr[3] not in SLOTS or addr[3] in result
            or (lo[0],lo[1]) <= (addr[0],addr[1])
            or (hi[0],hi[1]) <= (lo[0],lo[1])
            or any(v[5]!="cpu" for v in (addr,lo,hi))):
            raise ValueError("source CGRAM port/CPU data order changed")
        result[addr[3]]=lo[3]|(hi[3]<<8)
    if set(result)!=set(SLOTS) or set(result.values())!=COLORS:
        raise ValueError("source CGRAM gray colours or slots are not authentic")
    return dict(sorted(result.items()))


def original_groups(raw:bytes)->dict[int,list[tuple[int,int,int,int,int,str]]]:
    if sha(raw)!=SOURCE_TSV_SHA:
        raise ValueError("2014 Snes9x original source journal SHA changed")
    lines=raw.decode("ascii").splitlines()
    if lines[:2]!=["#range=5072..5184",
                    "frame\tvcounter\thcounter\taddr\tvalue\tsource"]:
        raise ValueError("authentic source $2121/$2122 journal header absent")
    groups=defaultdict(list)
    info={}
    for line in lines[2:]:
        if line.startswith("#"):
            name,value=line[1:].split("=",1)
            if name in info:
                raise ValueError("duplicate source provenance metadata")
            info[name]=value
            continue
        f,v,h,port,value,src=line.split("\t")
        f=int(f)
        groups[f].append((int(v),int(h),int(port,16),int(value,16),f,src))
    if (info!={"ring_earliest":"3682","port_writes":"192","scan_complete":"1"}
        or set(groups)!={5073+7*i for i in range(16)}
        or any(len(group)!=12 for group in groups.values())):
        raise ValueError("source original 112-frame ring truncated or phase changed")
    for f,entries in groups.items():
        if any(v not in (225,226) or not 0<=h<=340 or actual_f!=f
               for v,h,_,_,actual_f,_ in entries):
            raise ValueError("original Snes9x beam phase or frame altered")
        decode_group(entries)
    return groups


def native_groups(rows:list[dict])->dict[int,list[tuple[int,int,int,int,int,str]]]:
    groups=defaultdict(list)
    for row in rows:
        f=row["real_native_snes_frame"]
        v=row["host_beam_vcounter"]
        h=row["host_beam_hcounter"]
        port=int(row["native_PPU_data_port"],16)+0x2100
        value=int(row["original_unmodified_register_value"],16)
        src=row["host_writer_source_tag"]
        if (f not in (5169,5176,5183,5190) or v!=226
            or not 0<=h<=1364 or src!=0
            or row["second_byte_before_write"] not in (0,1)):
            raise ValueError("native result CPU writer beam, provenance or frame incorrect")
        groups[f].append((v,h,port,value,f,"cpu"))
    if set(groups)!={5169,5176,5183,5190} or any(len(x)!=12 for x in groups.values()):
        raise ValueError("native CGRAM frame/port journal missing records")
    for frame,group in groups.items():
        decode_group(group)
        for i in range(0,12,3):
            slot=group[i][3]
            for offset,expected_second in ((1,0),(2,1)):
                row=rows[list(groups).index(frame)*12+i+offset]
                if (int(row["pointer_before_write"],16)!=slot or
                    row["second_byte_before_write"]!=expected_second):
                    raise ValueError("native CGRAM write-twice pointer/latch differs")
    return groups


def verify(original:zipfile.ZipFile, baseline:zipfile.ZipFile,
           observed:zipfile.ZipFile)->dict:
    o=json.loads(original.read("qa08-results-port-preceding-frame.json"))
    a=json.loads(baseline.read("qa08-windows-2p-fullroute.json"))
    b=json.loads(observed.read("qa08-windows-2p-fullroute.json"))
    if (o.get("263_original_unmasked_BGRX_frames_identical_to_prior_original") is not True
        or o.get("source_5184_cgram_fnv1a")!="e8cdbe60"
        or o["source_prior_112_frame_CGRAM_write_history"]["source_port_write_count"]!=192):
        raise ValueError("unaltered original full-callback source not accepted")
    for native in (a,b):
        if (native.get("actual_source_count")!=263
            or native.get("source_geometry")!=[256,224]
            or native.get("actual_native_simulations")!=5484
            or native.get("actual_native_guest_CRC_sha256")!=CRC_5484
            or native.get("release_quality_ledger_admitted") is not False):
            raise ValueError("authentic original-mode Windows complete route absent")
    previous=a["source_frame_P7_SHA256_by_guest"]
    current=b["source_frame_P7_SHA256_by_guest"]
    if (len(previous)!=263 or previous!=current or
        b["actual_windows_PE_sha256"]==a["actual_windows_PE_sha256"]):
        raise ValueError("new native observer changed raster or lacked independent build")
    for frame in range(1280,5473,16):
        name=f"source/ur-baldosa-original-source-{frame:06d}.pam"
        if (sha(observed.read(name))!=current.get(str(frame)) or
            sha(baseline.read(name))!=previous.get(str(frame))):
            raise ValueError(f"native PPU full image archive corrupted at {frame}")
    journal=b.get("read_only_native_CGRAM_port_writer_chronology")
    if (not journal or journal.get("actual_bounded_port_writes")!=48 or
        journal.get("write_frames")!=[5169,5176,5183,5190] or
        journal.get("raster_fix_approved") is not False):
        raise ValueError("no unchanged bounded CPU palette-port witness")
    so=original_groups(original.read(
        "registers/qa08-results-5072-5184-cgram-history.tsv"))
    nw=native_groups(journal["read_only_native_port_writes"])
    pairs=[]
    for f,source_f,kind in SOURCE_PAIRS:
        observed_words=decode_group(nw[f])
        reference_words=decode_group(so[source_f])
        if observed_words!=reference_words:
            raise ValueError(f"native {f} != original palette state at {source_f}")
        pairs.append({
            "native_CPU_write_frame":f,
            "original_observed_write_frame":source_f,
            "frame_relation":"original is native+2" if kind=="direct" else
                             "same four-state original phase, later source frame not captured",
            "direct_original_frame_label_match":kind=="direct",
            "source_original_beam_v":sorted(set(x[0] for x in so[source_f])),
            "native_CPU_beam_v":sorted(set(x[0] for x in nw[f])),
            "authentic_four_palette_word_values":{
                f"{slot:02x}":f"{observed_words[slot]:04x}" for slot in SLOTS},
        })
    states=b["read_only_native_PPU_registers"]["per_line_native_PPU_state"]
    for f,checksum,words in (
        (5183,"e8cdbe60",(0x56b5,0x4a52,0x4631,0x4210)),
        (5184,"898ece20",(0x4a52,0x4631,0x4210,0x56b5))):
        seen=[x for x in states if x["actual_native_snes_frame"]==f]
        if len(seen)!=3 or {x["ppu_line"] for x in seen}!={1,112,114}:
            raise ValueError("all three original Windows raster lines required")
        for x in seen:
            if (x["cgram_full_512_byte_FNV1a"]!=checksum
                or [int(x["real_native_CGRAM_slots_6c_to_6f"][f"{slot:02x}"],16)
                    for slot in SLOTS]!=list(words)):
                raise ValueError("real Windows PPU pixel input state differs from writes")
    return {
        "schema":SCHEMA,
        "disposition":"native_real_CPU_CGRAM_writer_phase_offset_confirmed_no_guest_clock_cause_adjudicated",
        "original_source_artifact_id":12013432991,
        "original_source_ZIP_sha256":ORIGINAL_ZIP,
        "actual_Windows_baseline_artifact_id":12014896975,
        "Windows_baseline_ZIP_sha256":BASELINE_ZIP,
        "actual_Windows_writer_artifact_id":12017392389,
        "Windows_writer_ZIP_sha256":OBSERVED_ZIP,
        "real_Windows_writer_executable_sha256":b["actual_windows_PE_sha256"],
        "source_original_263_unmasked_callbacks_unchanged":True,
        "Windows_263_real_256x224_P7_frames_byte_identical":True,
        "Windows_5484_guest_CRC_SHA256_unchanged":CRC_5484,
        "original_112_frame_source_CPU_port_records":192,
        "native_bounded_CPU_port_records":48,
        "native_CPU_port_writer_source_enum":0,
        "native_bounded_write_frames":[5169,5176,5183,5190],
        "native_CPU_port_writes_only_at_vcounter":226,
        "directly_observed_original_CPU_writer_frame_difference":2,
        "original_port_writes_straddle_vcounter":[225,226],
        "original_vs_native_hcounter_units_and_phase_not_assumed_equivalent":True,
        "exact_original_frame_label_causality_or_guest_clock_proven":False,
        "complete_original_native_CPU_instruction_phase_proven":False,
        "original_native_palette_value_phase_matches":True,
        "actual_source_to_native_palette_pairings":pairs,
        "native_presented_frame_5183_CGRAM":"e8cdbe60",
        "native_presented_frame_5184_CGRAM":"898ece20",
        "next_required_decision":"CPU/APU and gameplay owners reconcile guest frame/vblank registration with original instruction and PPU source before adjusting graphics field or SNES clock",
        "graphics_fix_admitted":False,
        "QA08_10_and_release_gate_admitted":False,
        "physical_7to6_4x_or_HD_art_approved":False,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-ppu-archive",type=Path,required=True)
    p.add_argument("--windows-before-archive",type=Path,required=True)
    p.add_argument("--windows-writer-archive",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    with checked_zip(a.original_ppu_archive,ORIGINAL_ZIP) as original, \
         checked_zip(a.windows_before_archive,BASELINE_ZIP) as before, \
         checked_zip(a.windows_writer_archive,OBSERVED_ZIP) as native:
        result=verify(original,before,native)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("QA08_ORIGINAL_NATIVE_CGRAM_PORT_WRITERS",
          "source_original=192","native=48",
          "native_P7_images_unchanged=263",
          "direct_native_source_frame_offset=2",
          "source_cause_and_release=unaccepted")


if __name__=="__main__":
    main()
