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
    "legacy_original":"7a506cfc5f44bd8cc6aaba8482f42140b51618ba14aedec8f9bc7558417ad4b2",
}
FRAMES=tuple(range(4029,4035))+tuple(range(4173,4179))
# Old host-labelled OAM frames 4031/4175 remain authentic DMA observations;
# only the older visual callback *comparison* was temporally misregistered.
ORIGINAL={
    4031:("legacy_original","qa08_medal_4031"),
    4032:("original","qa08_medal_4032"),
    4175:("legacy_original","qa08_medal_4175"),
    4176:("original","qa08_medal_4176"),
}
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

# Authenticated native port -> active scanline OAM discriminator.
# Source of both observations is the *same* actual compiled Windows process:
# one complete 544-byte inbound OAM DMA, plus 7 OAM slots read after the
# normal renderer resolved real pixels on five separately selected lines.
# Neither original CPU/beam phase nor final SNES priority is thereby proven.
LIVE_FRAMES=(4032,4176)
LIVE_PIXELS=((207,91),(205,115),(205,139),(225,96),(225,120))

def live_OAM_matches_incoming_DMA(payloads:dict[int,bytes],live:dict)->dict:
    need(live["real_native_2p_guest_frames"],5484,"source full guest route")
    need(live["independently_source_qualified_native_scanline_OAM_snapshots"],70,
         "actual per-line source OAM read count")
    need(live["original_snes9x_2014_same_field_pixel_priority_proven"],False,
         "original effective pixel priority remains unaccepted")
    needed={(f,x,y,slot) for f in LIVE_FRAMES for x,y in LIVE_PIXELS for slot in SLOTS}
    seen=set()
    for row in live["native_OAM_in_effect_on_selected_lines"]:
        frame,x,y,slot=(row[k] for k in ("native_guest","x","raster_y","OAM_slot"))
        key=(frame,x,y,slot)
        if key not in needed or key in seen:
            raise ValueError("unsolicited/duplicate source-effective OAM line record")
        seen.add(key)
        raw=payloads.get(frame)
        if raw is None or len(raw)!=544:
            raise ValueError("source-native whole 544-byte input missing from live field")
        i=slot*4
        want_xy=f"{raw[i+1]:02x}{raw[i]:02x}"
        want_tile_attr=f"{raw[i+3]:02x}{raw[i+2]:02x}"
        want_high=(raw[512+slot//4]>>((slot%4)*2))&3
        if (row["native_scanline_oam_xy"],
            row["native_scanline_oam_tile_attr"],
            row["native_scanline_high_oam_pair"]) != (
                want_xy,want_tile_attr,want_high):
            raise ValueError(f"actual PPU raster OAM differs from same-host DMA input at {key}")
    need(seen,needed,"complete seven-slot by ten-raster-pixel OAM input coherence")
    return {
        "actual_native_raster_guest_frames":list(LIVE_FRAMES),
        "source_selected_output_pixel_locations":[list(p) for p in LIVE_PIXELS],
        "actual_monitored_OAM_slots":list(SLOTS),
        "full_source_DMA_bytes_per_native_guest":544,
        "actual_native_line_OAM_records_source_DMA_identical":len(seen),
        "native_legacy_OAM_register_port_to_render_buffer_coherent_at_tested_lines":True,
        "original_native_guest_CPU_beam_phase_equivalence_accepted":False,
        "effective_original_PPU_final_pixel_priority_accepted":False,
        "renderer_sprite_palette_or_tile_shift_fix_authorized":False,
    }

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

def analyze(original:Path,legacy_original:Path,native:Path)->dict:
    for k,path in (("original",original),("legacy_original",legacy_original),("native",native)):
        need(sha(path.read_bytes()),PINS[k],k+" complete producer ZIP SHA")
    with zipfile.ZipFile(original) as a,zipfile.ZipFile(legacy_original) as old,zipfile.ZipFile(native) as b:
        if any(len(z.namelist())!=len(set(z.namelist())) for z in (a,old,b)):
            raise ValueError("duplicate source ZIP member")
        legacy_receipt=json.loads(old.read("original-263-verified.json"))
        need(legacy_receipt["263_original_unmasked_BGRX_frames_identical_to_prior_original"],True,
             "legacy host-labelled OAM preserved original 263 video callbacks")
        need(legacy_receipt["native_guest_phase_certified"],False,
             "legacy visual frame cross-registration remains unaccepted")
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
        live_OAM_coherence=live_OAM_matches_incoming_DMA(native_inputs,native_receipt)
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
        for host,(producer,tag) in ORIGINAL.items():
            source=a if producer=="original" else old
            info=json.loads(source.read(f"registers/{tag}.info.json"))
            need(info["frame"],host,f"authentic historical original host field {host}")
            oam=source.read(f"registers/{tag}.oam.bin")
            need(len(oam),544,f"original full OAM image {host}")
            need(original_dma(source.read(f"registers/{tag}.ppuw.tsv"),host),oam,
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
              for m in matches],[(4031,4029),(4032,4030),(4175,4173),(4176,4174)],
             "unshifted independently observed whole-OAM matches")
        return {
            "schema":"qa08-source-four-original-entire-544-byte-OAMDMA-two-host-field-phase/2",
            "source_archives_SHA256":PINS,
            "native_port_frames_independently_replayed":len(native_inputs),
            "original_pinned_544byte_VBlank_DMA_to_OAM_checks":len(ORIGINAL),
            "identical_source_OAMDMA_matches":matches,
            "native_port_to_actual_PPU_OAM_line_coherence":live_OAM_coherence,
            "four_original_full_OAM_states_seen_in_native_port_two_host_fields_early":True,
            "native_guest_CPU_NMI_DMA_source_WRAM_causality_proven":False,
            "same_original_native_instruction_or_beam_phase_proven":False,
            "renderer_tile_shift_or_palette_recolor_authorized":False,
            "graphics_release_approved":False,
        }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("original","legacy-original","native","out"):
        p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args()
    result=analyze(a.original,a.legacy_original,a.native)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("QA08_OAM_SOURCE_INPUT_MATCH=544/544 4_pairs=4031:4029,4032:4030,4175:4173,4176:4174 release=0")

if __name__=="__main__":
    main()
