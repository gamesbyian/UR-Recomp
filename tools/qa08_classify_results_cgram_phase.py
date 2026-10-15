#!/usr/bin/env python3
"""Classify the exact 2014 Snes9x result CGRAM history without changing a game.

Reads the original-host 112-frame source PPU-ring archive created by QA-08
run 38822737039. Validates unmasked original-callback proof and each
$2121/$2122 write, reconstructs the four successive real CGRAM states, and
compares their fingerprints against the *previously observed* native Windows
checksum. This is a phase hypothesis, not a native writer or timing proof.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from pathlib import Path
import struct
import zipfile

ZIP_SHA = "d725ee45db1b66d098e79499263dd089dba80a26de517c30db674f91e20f80a8"
TSV_SHA = "7e1f36a58fe52205011c9f34d4704c6311d929ac75caf11ea7e6958a6cc386c4"
CGRAM_SHA = "431224685084e4a1ec62da7d7aaab96a7c36beb78aa8d257b0569be416737c12"
ORIGINAL_FNV = "e8cdbe60"
OBSERVED_NATIVE_FNV = "898ece20"
SOURCE_WINDOW = list(range(5073, 5179, 7))
SLOTS = {0x6c,0x6d,0x6e,0x6f}
WORDS = {0x4210,0x4631,0x4a52,0x56b5}
SCHEMA = "qa08-source-qualified-original-2p-four-state-CGRAM-phase-20261015/1"

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def fnv(raw:bytes)->str:
    if len(raw)!=512:
        raise ValueError("must evaluate all 256 real original CGRAM words")
    value=2166136261
    for byte in raw:
        value=(value ^ byte) * 16777619 & 0xffffffff
    return f"{value:08x}"

def decode(tsv:bytes)->dict[int,dict[int,int]]:
    if sha(tsv)!=TSV_SHA:
        raise ValueError("original 112-frame PPU journal SHA differs")
    lines=tsv.decode("ascii").splitlines()
    if lines[:2]!=["#range=5072..5184",
                   "frame\tvcounter\thcounter\taddr\tvalue\tsource"]:
        raise ValueError("original register-journal format changed")
    groups=collections.defaultdict(list)
    meta={}
    for line in lines[2:]:
        if line.startswith("#"):
            key,value=line[1:].split("=",1)
            if key in meta:
                raise ValueError("duplicate original ring metadata")
            meta[key]=value
            continue
        parts=line.split("\t")
        if len(parts)!=6:
            raise ValueError("incomplete PPU-ring port entry")
        frame,v,h,port,byte,origin=parts
        frame=int(frame)
        if (frame not in SOURCE_WINDOW or port not in ("2121","2122")
                or origin!="cpu" or not 0<=int(v)<=340
                or not 0<=int(h)<=340 or len(byte)!=2):
            raise ValueError("unexpected source frame/beam/port writer")
        groups[frame].append((int(port,16),int(byte,16)))
    if (meta.get("scan_complete")!="1" or
        int(meta.get("ring_earliest","99999"))>5072 or
        int(meta.get("port_writes","-1"))!=192 or
        list(groups)!=SOURCE_WINDOW):
        raise ValueError("incomplete original one-cycle register provenance")
    result={}
    for frame in SOURCE_WINDOW:
        raw=groups[frame]
        if len(raw)!=12:
            raise ValueError(f"source {frame}: not four authentic palette writes")
        idx=None
        low=None
        colors={}
        for port,value in raw:
            if port==0x2121:
                if low is not None:
                    raise ValueError("palette port changed before high byte")
                idx=value
                if idx not in SLOTS or idx in colors:
                    raise ValueError("noncheckerboard palette port")
            elif port==0x2122:
                if idx is None:
                    raise ValueError("data port before address")
                if low is None:
                    low=value
                else:
                    colors[idx]=low | (value<<8)
                    idx=None
                    low=None
        if idx is not None or low is not None or set(colors)!=SLOTS or set(colors.values())!=WORDS:
            raise ValueError("source four-entry CGRAM transaction incomplete")
        result[frame]=colors
    return result

def analyze(tsv:bytes,cgram:bytes,receipt:dict)->dict:
    if sha(cgram)!=CGRAM_SHA or fnv(cgram)!=ORIGINAL_FNV:
        raise ValueError("unaltered original frame 5184 CGRAM did not match source")
    if (receipt.get("263_original_unmasked_BGRX_frames_identical_to_prior_original") is not True
        or receipt.get("source_5183_cgram_fnv1a")!=ORIGINAL_FNV
        or receipt.get("source_5184_cgram_fnv1a")!=ORIGINAL_FNV
        or receipt.get("source_prior_112_frame_CGRAM_write_history",{}).get("source_port_write_count")!=192):
        raise ValueError("not source-qualified complete original video/cgram receipts")
    groups=decode(tsv)
    if {i:struct.unpack_from("<H",cgram,2*i)[0] for i in SLOTS}!=groups[5178]:
        raise ValueError("last original port writes do not equal actual 5184 CGRAM")
    states=[]
    for frame in SOURCE_WINDOW[-4:]:
        palette=bytearray(cgram)
        for slot,word in groups[frame].items():
            struct.pack_into("<H",palette,slot*2,word)
        states.append({"source_update_frame":frame,
                       "reconstructed_full_512byte_FNV1a":fnv(palette),
                       "original_CGRAM_6c_to_6f_15bit_words":
                           {f"{slot:02x}":f"{groups[frame][slot]:04x}" for slot in sorted(SLOTS)}})
    if ([x["reconstructed_full_512byte_FNV1a"] for x in states]
        !=[OBSERVED_NATIVE_FNV,"6d363000","2a904be8",ORIGINAL_FNV]):
        raise ValueError("four-state original CGRAM rotation not reproduced")
    phases=[tuple(groups[frame][slot] for slot in sorted(SLOTS)) for frame in SOURCE_WINDOW]
    if any(phases[i]!=phases[i+4] for i in range(len(phases)-4)):
        raise ValueError("original 7-frame palette changes not 28-frame periodic")
    native_matching=[x for x in states if x["reconstructed_full_512byte_FNV1a"]==OBSERVED_NATIVE_FNV]
    return {
        "schema":SCHEMA,
        "status":"original_four_state_CGRAM_rotation_matched_native_checksum_not_native_writer",
        "source_original_run":38822737039,
        "source_artifact_id":12013432991,
        "original_source_archive_zip_sha256":ZIP_SHA,
        "original_unchanged_USA_ROM_sha256":"859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
        "actual_original_core_binary_sha256":receipt["original_core_sha256"],
        "original_263_full_256x224_BRGX_frames_byte_exact":True,
        "source_5183_5184_same_CGRAM":ORIGINAL_FNV,
        "source_CGRAM_port_write_count":192,
        "source_CGRAM_write_frames":SOURCE_WINDOW,
        "source_write_batch_interval_frames":7,
        "source_CGRAM_words_per_batch":4,
        "original_palette_state_period_frames":28,
        "sparse_comparator_sample_interval_frames":16,
        "potential_sparse_comparator_phase_alias_period_frames":112,
        "sampled_112_cadence_is_not_proof_of_112_frame_intrinsic_animation":True,
        "four_authentic_source_CGRAM_reconstructions":states,
        "observed_native_5184_CGRAM_FNV1a":OBSERVED_NATIVE_FNV,
        "matching_source_phase_reconstruction":native_matching,
        "phase_equivalence":"one 7-frame update ahead modulo four, or three behind",
        "fingerprint_not_raw_native_CGRAM_byte_equality":True,
        "pixel_source_observed_native_to_original_gray_mapping":
            {"123":132,"132":140,"140":165,"165":123},
        "pixel_gray_rotation_corresponds_to_authentic_source_slots_6c_through_6f":True,
        "next_adjudicator":"independent native full 512-byte CGRAM and exact original/native $2121/$2122 write chronology at same guest+beam phase",
        "no_guest_or_renderer_patch_approved":True,
        "graphics_release_ledger_gates_accepted":0,
        "HD_character_likeness_approved":False,
    }

def from_archive(path:Path)->dict:
    blob=path.read_bytes()
    if sha(blob)!=ZIP_SHA:
        raise ValueError("wrong real source archive bytes")
    with zipfile.ZipFile(path) as z:
        r=json.loads(z.read("qa08-results-port-preceding-frame.json"))
        t=z.read("registers/qa08-results-5072-5184-cgram-history.tsv")
        c=z.read("registers/qa08_results_cgram.cgram.bin")
    return analyze(t,c,r)

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-archive",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=from_archive(a.source_archive)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("QA08_ORIGINAL_CGRAM_4_STATE_VERIFIED original_frames=263 "
          "port_writes=192 actual_source_period=28 "
          "native_checksum_phase_rotation=1 native_timing_verified=0 release=0")

if __name__=="__main__":
    main()
