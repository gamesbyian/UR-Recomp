#!/usr/bin/env python3
"""Adjudicate real opt-in native OAM input ports against source OAM memory.

Consumes ONE real 5,484-guest-CRC-pinned native Win32 2P log. Does NOT apply
a frame shift, assume which VBlank precedes a visible frame, adjust tile
indices, edit rendered pixels, or reinterpret replay as guest DMA.
Retains only bounded counts, stream digests, and seven sprite tile source
bytes. Exact 544-byte DMA source recognition requires SNES OAM port latch
and address progression, not a screen/CPU guess.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path

PREFIX="UR_QA08_WIN_OAM_PORT "
COLUMNS=("frame","v","h","port","val","src","adr","high","second",
         "latch","oldlow","oldhigh")
TARGETS=(96,97,98,99,112,113,114)
SOURCE_ENUM={0:"CPU",1:"DMA",2:"HDMA",3:"REPLAY"}
WANT_FRAMES=set(range(4029,4035)) | set(range(4173,4179))
CRC="c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876"

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def parse_line(line:str)->dict:
    if not line.startswith(PREFIX):
        raise ValueError("foreign OAM write entry")
    raw={}
    for word in line[len(PREFIX):].split():
        if word.count("=")!=1:
            raise ValueError("malformed original 65816 port record")
        key,val=word.split("=",1)
        if key in raw:
            raise ValueError("duplicate original PPU port field")
        raw[key]=val
    if set(raw)!=set(COLUMNS):
        raise ValueError("incomplete actual PPU OAM write")
    rec={}
    for k in COLUMNS:
        base=16 if k in ("port","val","adr","latch","oldlow","oldhigh") else 10
        try:rec[k]=int(raw[k],base)
        except ValueError as exc:raise ValueError("bad source port record hex/decimal") from exc
    if (rec["frame"] not in WANT_FRAMES or
        rec["port"] not in (2,3,4) or rec["src"] not in SOURCE_ENUM or
        not 0<=rec["v"]<=261 or not 0<=rec["h"]<=1364 or
        not 0<=rec["val"]<=255 or not 0<=rec["adr"]<=255 or
        rec["high"] not in (0,1) or rec["second"] not in (0,1)):
        raise ValueError("unqualified OAM field, source or beam")
    return rec

def full_sequential_dma(events:list[dict])->dict|None:
    """Locate 544 contiguous DMA OAMDATA inputs from zero low OAM address.

    If the full chain is absent, do not reconstruct/wish it into existence.
    """
    for offset in range(len(events)-543):
        sample=events[offset:offset+544]
        if any(x["port"]!=4 or x["src"]!=1 for x in sample):
            continue
        if sample[0]["adr"]!=0 or sample[0]["high"]!=0 or sample[0]["second"]!=0:
            continue
        if any(x["adr"]!=((i//2)&255) % (16 if i>=512 else 256) or
               x["high"]!=(1 if i>=512 else 0) or
               x["second"]!=(i%2) for i,x in enumerate(sample)):
            continue
        payload=bytes(x["val"] for x in sample)
        return {
          "complete_native_OAM_DMA_544_bytes":True,
          "native_incoming_DMA_port_payload_SHA256":sha(payload),
          "source_DMA_start_beam":[sample[0]["v"],sample[0]["h"]],
          "source_DMA_end_beam":[sample[-1]["v"],sample[-1]["h"]],
          "native_DMA_source_slot_tile_bytes":{
              str(slot):f"{payload[slot*4+2]:02x}" for slot in TARGETS},
          "original_PPUPort_payload_mutation_proven":False,
          "full_payload_hex_not_saved":True,
        }
    return None

def analyze(log:str,native_receipt:dict)->dict:
    if (native_receipt.get("real_native_2p_guest_frames")!=5484 or
        native_receipt.get("real_native_2p_guest_crc_sha256")!=CRC or
        native_receipt.get("independently_source_qualified_native_scanline_OAM_snapshots")!=70):
        raise ValueError("not the previously independently CRC-pinned real native 2P")
    records=[]
    for line in log.splitlines():
        if line.startswith(PREFIX):
            records.append(parse_line(line))
    if not records or len(records)>30000:
        raise ValueError("absent or unbounded native $2104 observer")
    group=defaultdict(list)
    for x in records:
        group[x["frame"]].append(x)
    frames=[]
    for frame in sorted(group):
        events=group[frame]
        bysource=Counter(SOURCE_ENUM[x["src"]] for x in events if x["port"]==4)
        dma=full_sequential_dma(events)
        frames.append({
            "actual_native_host_frame":frame,
            "actual_OAMADDL_OAMADDH_OAMDATA_writes":len(events),
            "actual_2104_source_counts":dict(bysource),
            "complete_sequential_zero_address_544byte_DMA":dma,
            "does_not_automatically_equate_host_frame_to_original_callback":True,
        })
    return {
      "schema":"qa08-native-readonly-PPU-OAM-input-port-chronology/1",
      "source_selected_host_frames":sorted(WANT_FRAMES),
      "events_observed":len(records),
      "host_frames_with_actual_observations":len(frames),
      "frame_observations":frames,
      "native_unchanged_5484_frame_guest_CRC_SHA256":CRC,
      "native_70_source_qualified_raster_OAM_records_preserved":True,
      "CPU_guest_WRAM_source_memory_proven":False,
      "original_native_instruction_and_beam_phase_equivalent":False,
      "game_logic_or_PPU_renderer_modified":False,
      "release_approved":False
    }

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log",type=Path,required=True)
    p.add_argument("--native-receipt",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    summary=analyze(a.log.read_text(errors="replace"),
                    json.loads(a.native_receipt.read_text()))
    a.out.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("QA08_NATIVE_OAM_PORTS_READONLY",summary["events_observed"],
          "complete_544_DMA_streams",sum(x["complete_sequential_zero_address_544byte_DMA"] is not None
              for x in summary["frame_observations"]),
          "source_beam_equivalence=UNPROVEN no_renderer_edit=1")

if __name__=="__main__":
    main()
