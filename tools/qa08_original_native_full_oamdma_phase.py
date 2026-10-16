#!/usr/bin/env python3
"""Reconstruct real native incoming OAM DMA and compare full 544 bytes to Snes9x.

Exact original host postrun f corresponds to original video callback f-1.
This reports source-input equivalence at native host f-2, NOT an authorised
frame shift, CPU/NMI diagnosis, renderer correction or release acceptance.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import zipfile

PINS={
    "original":"2fef0440b97a69025bf9ee539551b414ef7f1f11978172aea5565f338b35d4c9",
    "native":"74fd88413c2a1cac2c14098c65b76fba4cdba909f989182618018d9a68a04888",
}
FRAMES=tuple(range(4029,4035))+tuple(range(4173,4179))
ORIGINAL={4032:"qa08_medal_4032",4176:"qa08_medal_4176"}
CRC="c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876"
SLOTS=(96,97,98,99,112,113,114)

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def need(got,want,why):
    if got!=want:
        raise ValueError(f"unqualified OAM source {why}: {got!r} != {want!r}")

def native_payloads(log:str)->dict[int,bytes]:
    events=defaultdict(list)
    ports=defaultdict(lambda:defaultdict(int))
    for row in log.splitlines():
        if not row.startswith("UR_QA08_WIN_OAM_PORT "):
            continue
        d={}
        for col in row.split()[1:]:
            k,sep,v=col.partition("=")
            if not sep or k in d:
                raise ValueError("duplicate/malformed native port record")
            d[k]=v
        for k in ("frame","v","port","val","src","adr","high","second"):
            if k not in d:
                raise ValueError("missing native port source field")
        f=int(d["frame"])
        if f not in FRAMES:
            raise ValueError("unrequested native frame")
        p=int(d["port"],16)
        if p not in (2,3,4):
            raise ValueError("unrequested native OAM port")
        ports[f][p]+=1
        if p==4:
            if int(d["src"])!=1 or not 225<=int(d["v"])<=261:
                raise ValueError("native OAMDATA not observed VBlank DMA")
            events[f].append((int(d["val"],16),int(d["adr"],16),
                              int(d["high"]),int(d["second"])))
    need(set(ports),set(FRAMES),"native observed host frame set")
    payload={}
    for f in FRAMES:
        need((ports[f][2],ports[f][3],ports[f][4]),(2,2,544),
             f"native host {f} OAM register access counts")
        for i,(_,addr,hi,second) in enumerate(events[f]):
            need((addr,hi,second),
                 ((i//2)%(16 if i>=512 else 256),int(i>=512),i&1),
                 f"native host {f} OAM sequence byte {i}")
        payload[f]=bytes(x[0] for x in events[f])
    return payload

def original_dma(journal:bytes,f:int)->bytes:
    lines=journal.decode("ascii").splitlines()
    need(lines[0],"#frame\tvcounter\thcounter\taddr\tvalue\tsource",
         "original source PPU journal header")
    result=[]
    for line in lines[1:]:
        if line.startswith("#"):
            if "truncated" in line:
                raise ValueError("incomplete original PPU port writer ring")
            continue
        cols=line.split("\t")
        if len(cols)!=6:
            raise ValueError("malformed original port source")
        sf,v,h,port,val,writer=cols
        if port=="2104":
            if int(sf)!=f or writer!="dma" or not 225<=int(v)<=261:
                raise ValueError("original active scanline/non-DMA OAMDATA")
            result.append(int(val,16))
    need(len(result),544,f"original full 544-byte OAM DMA {f}")
    return bytes(result)

def analyze(original:Path,native:Path)->dict:
    for k,path in (("original",original),("native",native)):
        need(sha(path.read_bytes()),PINS[k],k+" complete producer ZIP SHA")
    with zipfile.ZipFile(original) as a,zipfile.ZipFile(native) as b:
        if any(len(z.namelist())!=len(set(z.namelist())) for z in (a,b)):
            raise ValueError("duplicate source ZIP member")
        native_receipt=json.loads(b.read("qa08-native-effective-pixel-owner.json"))
        port_receipt=json.loads(b.read("qa08-native-OAM-port-input.json"))
        original_receipt=json.loads(a.read("matched-original-fields.json"))
        need(native_receipt["real_native_2p_guest_crc_sha256"],CRC,"original/native guest CRC")
        need(native_receipt["real_native_2p_guest_frames"],5484,"real native 2P frames")
        need(native_receipt["independently_source_qualified_native_scanline_OAM_snapshots"],70,
             "native actual line OAM")
        need(original_receipt["host_preincrement_plus_one_registration_verified"],True,
             "correct original host/frame registration")
        native_inputs=native_payloads(b.read("qa08-effective-pixel-source-log.txt").decode("ascii"))
        expected={row["actual_native_host_frame"]:row["complete_sequential_zero_address_544byte_DMA"]
                  for row in port_receipt["frame_observations"]}
        need(set(expected),set(FRAMES),"existing native port observer frames")
        for f,raw in native_inputs.items():
            if expected[f] is None:
                raise ValueError("prior source verifier rejected complete OAM DMA")
            need(sha(raw),expected[f]["native_incoming_DMA_port_payload_SHA256"],
                 f"native whole OAMDMA source digest {f}")
            for slot in SLOTS:
                need(f"{raw[slot*4+2]:02x}",expected[f]["native_DMA_source_slot_tile_bytes"][str(slot)],
                     f"native tile byte at source slot {slot}")
        matches=[]
        for host,tag in ORIGINAL.items():
            oam=a.read(f"registers/{tag}.oam.bin")
            need(len(oam),544,f"original full OAM image {host}")
            need(original_dma(a.read(f"registers/{tag}.ppuw.tsv"),host),oam,
                 f"original whole DMA port payload {host}")
            for f,raw in native_inputs.items():
                if raw==oam:
                    matches.append({"original_postrun_field":host,
                                    "original_video_callback":host-1,
                                    "native_input_OAMDMA_host_frame":f,
                                    "native_minus_original_host_frames":f-host,
                                    "all_identical_OAM_bytes":544,
                                    "full_source_OAM_SHA256":sha(oam),
                                    "source_sprite_tile_bytes":{
                                        str(s):f"{oam[s*4+2]:02x}" for s in SLOTS}})
        need([(m["original_postrun_field"],m["native_input_OAMDMA_host_frame"])
              for m in matches],[(4032,4030),(4176,4174)],
             "unshifted independently observed whole-OAM matches")
        return {
            "schema":"qa08-source-entire-544-byte-OAMDMA-two-host-field-phase/1",
            "source_archives_SHA256":PINS,
            "native_port_frames_independently_replayed":len(native_inputs),
            "original_pinned_544byte_VBlank_DMA_to_OAM_checks":len(ORIGINAL),
            "identical_source_OAMDMA_matches":matches,
            "both_original_full_OAM_states_seen_in_native_port_two_host_fields_early":True,
            "native_guest_CPU_NMI_DMA_source_WRAM_causality_proven":False,
            "same_original_native_instruction_or_beam_phase_proven":False,
            "renderer_tile_shift_or_palette_recolor_authorized":False,
            "graphics_release_approved":False,
        }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("original","native","out"):
        p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args()
    result=analyze(a.original,a.native)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("QA08_OAM_SOURCE_INPUT_MATCH=544/544 original-postrun=4032,4176 native-input=4030,4174 release=0")

if __name__=="__main__":
    main()
