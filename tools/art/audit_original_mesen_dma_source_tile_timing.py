#!/usr/bin/env python3
"""Original ROM 32-byte DMA tile sources vs real held Mesen VRAM tiles.

Compares the queued original graphics source bytes at each selected authentic
bridge tick to held PPU tile bytes at the prior/current/next original frame.
This is a timing-sensitive diagnostic, never a proof of 1994 3D geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

from tools.art.no_replace_report import publish_text_once

ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
ZIP_SHA = "28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6"
QUEUE_SCHEMA = "UR-ART4K-EXECUTED-MESEN-RIDER-QUEUED-32B-TILES-TO-ORIGINAL-OBJS/1"
ROM_SIZE = 2_097_152
TILE_SIZE = 32
SOURCE_FRAMES = tuple(range(1601,1625))
SAMPLED_TICKS = (1601,1602,1603,1605,1606,1609,1610,1624)


def original_lorom_source_bytes(rom: bytes, bank_word: int,
                                source_addr_word: int) -> bytes:
    """SNES DMA reads 32 sequential 65816 source bus bytes, LoROM ROM banks.

    Crossing 0xFFFF in a single DMA transfer is deliberately unresolved,
    since wrapping to 0x0000 can leave the LoROM ROM segment.
    """
    if (len(rom) != ROM_SIZE or type(bank_word) is not int
            or type(source_addr_word) is not int or not 0x20 <= bank_word <= 0x3F
            or not 0x8000 <= source_addr_word <= 0xFFFF - (TILE_SIZE-1)):
        raise ValueError("original 32-byte LoROM DMA source outside verified ROM window")
    offset = (bank_word * 0x8000) + (source_addr_word & 0x7FFF)
    if offset + TILE_SIZE > len(rom):
        raise ValueError("original queued graphics tile source not contained in ROM")
    return rom[offset:offset+TILE_SIZE]


def ppu_vram_tile(vram: bytes, word_address: int) -> bytes:
    if (len(vram) != 65536 or type(word_address) is not int
            or not 0 <= word_address <= 0x7FFF - 15):
        raise ValueError("invalid original 32-byte PPU VRAM tile word address")
    return vram[2*word_address:2*word_address+TILE_SIZE]


def audit(rom: bytes, source_zip: bytes, source_queue: dict) -> dict:
    if len(rom) != ROM_SIZE or hashlib.sha256(rom).hexdigest() != ROM_SHA:
        raise ValueError("original USA ROM SHA changed")
    if hashlib.sha256(source_zip).hexdigest() != ZIP_SHA:
        raise ValueError("original executed 24-tick source PPU ZIP changed")
    if (source_queue.get("schema") != QUEUE_SCHEMA
            or source_queue.get("original_24tick_ppu_source_ZIP_sha256") != ZIP_SHA
            or source_queue.get("source_original_ROM_SHA256") != ROM_SHA
            or source_queue.get("source_original_Mesen_workflow_run") != 41774019061):
        raise ValueError("original source DMA queue receipt provenance changed")
    rows = source_queue.get("rows")
    if not isinstance(rows,list) or [r.get("original_bridge_tick") for r in rows] != list(SAMPLED_TICKS):
        raise ValueError("wrong original source queue tick census")
    by_tick = {}
    with zipfile.ZipFile(io.BytesIO(source_zip)) as z:
        for tick in SOURCE_FRAMES:
            raw = z.read(f"frame-{tick:06d}-vram.bin")
            if len(raw) != 65536:
                raise ValueError("original Mesen PPU VRAM byte count invalid")
            by_tick[tick] = raw
    result = []
    for row in rows:
        tick = row["original_bridge_tick"]
        entries = row["source_queue_entries"]
        if len(entries) != row["source_queue_transfer_count"]:
            raise ValueError("source DMA queue length mismatch")
        samples = []
        for entry in entries:
            original = original_lorom_source_bytes(
                rom, entry["source_bank_word"], entry["source_address_word"])
            dest = entry["source_vram_dest_after_nmi_flag_rule"]
            for_priorities = []
            for delta in (-1,0,1):
                frame = tick+delta
                if frame not in by_tick:
                    continue
                held = ppu_vram_tile(by_tick[frame],dest)
                same = sum(x==y for x,y in zip(original,held))
                for_priorities.append({"source_frame_delta":delta,
                    "original_snapshot_tick":frame,
                    "equal_32_byte_tile":same==TILE_SIZE,
                    "equal_byte_count_of_32":same})
            samples.append({"entry":entry["entry"],"original_2d_source_role":
                        entry["source_OAM_64px_tile_region"],
                        "source_ROM_bank_word":entry["source_bank_word"],
                        "source_ROM_address_word":entry["source_address_word"],
                        "effective_PPU_VRAM_word":dest,
                        "queued_ROM_32_byte_SHA256":hashlib.sha256(original).hexdigest(),
                        "source_original_PPU_held_frame_temporal_candidates":for_priorities})
        stats = {}
        for delta in (-1,0,1):
            available = [s for s in samples for t in s["source_original_PPU_held_frame_temporal_candidates"]
                         if t["source_frame_delta"]==delta]
            stats[str(delta)] = {
                "compared_tiles":len(available),
                "exact_32_byte_tile_matches":sum(t["equal_32_byte_tile"] for t in available),
                "equal_bytes_of_compared":sum(t["equal_byte_count_of_32"] for t in available),
                "total_compared_bytes":len(available)*TILE_SIZE}
        result.append({"original_bridge_tick":tick,"source_queue_size":len(samples),
                       "temporal_alignment_counts":stats,"tile_candidates":samples})
    return {"schema":"UR-ART4K-ORIGINAL-ROM-DMA-SOURCE-32B-HELD-PPU-TIMING/1",
        "source_original_USA_ROM_SHA256":ROM_SHA,
        "source_original_24tick_PPU_zip_SHA256":ZIP_SHA,
        "source_8tick_original_executed_queue_run":41774019061,
        "source_8tick_original_executed_queue_commit":"23a82d36c514347fae0e3d32844927a575b184c8",
        "source_held_PPU_phase_and_enqueued_NMI_transfer_not_aligned":True,
        "source_original_1994_3D_mesh_camera_pose_recovered":False,
        "owner_shipping_art_approved":False,
        "original_selected_ticks":list(SAMPLED_TICKS),
        "rows":result}

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom",type=Path,required=True)
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--source-queue-json",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=audit(args.rom.read_bytes(),args.source_zip.read_bytes(),
                 json.loads(args.source_queue_json.read_bytes()))
    publish_text_once(args.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("ART4K_ORIGINAL_ROM_SOURCE_DMA_BYTE_MATCHES",
          json.dumps([{"tick":r["original_bridge_tick"],
                       "stats":r["temporal_alignment_counts"]}
                     for r in result["rows"]],sort_keys=True))

if __name__=="__main__":
    main()
