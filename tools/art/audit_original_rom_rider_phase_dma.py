#!/usr/bin/env python3
"""Verify original USA retail ROM phase/angle and rider DMA code against original PPU.

Static opcode proof and observed source target addresses only.
A CPU/DMA writer PC was NOT captured at original run time.
No original 1994 3D camera, skeletal pose or source asset is recovered.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

from tools.art.audit_original_mesen_contiguous_24 import audit as audit_mesen
from tools.art.audit_original_mesen_oam_descriptors import decode_oam
from tools.art.audit_original_mesen_obj_screen_pixels import decode_source_obj
from tools.art.no_replace_report import publish_text_once

ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
SOURCE_SHA="28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6"
SCHEMA="UR-ART4K-RETAIL-ROM-STATIC-RIDER-PHASE-DMA-TO-EXECUTED-PPU/1"
# Each opcode sequence is short enough to review in original retail ROM.
# These are literal assertions, NOT instructions for executing SNES code.
ANCHORS={
    "rider_animation_calls_phase_update":(0x83,0xED33,"20 10 EF C2 20 E2 10"),
    "modulo_24_original_rider_phase":(0x83,0xEE53,
        "AD 83 0F 18 65 00 C9 00 00 30 0B C9 18 00 30 0C 38 E9 18 00 80 F0 18 69 18 00 80 EA 8D 83 0F"),
    "phase_times_64_plus_presentation_offset":(0x83,0xEED9,
        "AD 83 0F 0A 0A 0A 0A 0A 0A 18 69 00 00 18 6D 77 0F"),
    "angle_64_state_mask":(0x83,0xF054,"29 3F 00 8D 49 0F"),
    "two_player_rider_presentation_ids":(0x83,0xF0D7,
        "AC E9 0F 8C 00 02 AC EB 0F 8C 04 02"),
    "presented_frame_three_byte_rom_pointer":(0x83,0xF296,
        "E2 10 85 00 0A 18 65 00 18 69 00 80"),
    "tile_destination_seed_word_6000":(0x83,0xF188,
        "A0 00 60 84 26"),
    "queue_wram_dma_source_address":(0x83,0xF21A,
        "99 45 16 A5 2A 29 FC 00 4A 4A 69 27 00 99 A1 15"),
    "queue_wram_vram_destination":(0x83,0xF26B,
        "99 E9 16 C8 C8 46 28 CA 30 03 4C DD F1 A5 26 69 20 00 85 26"),
    "tile_dma_end_sentinel_pending":(0x83,0xF282,
        "A9 FF FF 99 A1 15 A5 0A 49 FF FF 8D 7D 0C A0 01 8C 06 03 60"),
    "nmi_dma_pending_guard_and_mode":(0x82,0xB8AB,
        "E2 20 C2 10 AD 06 03 D0 03 4C 96 D1 9C 06 03 9C 0B 42 A9 80 8D 15 21 A9 01 8D 00 43 A9 18 8D 01 43"),
    "nmi_wram_source_to_snes_dma_regs":(0x82,0xB8E3,
        "AE A1 15 10 03 4C 92 D1 8E 04 43 AD 45 16 8D 02 43"),
    "nmi_vram_destination_selects_second_800_word_region":(0x82,0xB8F4,
        "AD E9 16 89 80 00 F0 03 69 00 08 8D 16 21"),
    "nmi_trigger_dma_and_32byte_transfer":(0x82,0xB902,
        "A2 01 8E 0B 42 8C 05 43"),
}


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def lorom_offset(bank:int,address:int)->int:
    if type(bank) is not int or type(address) is not int:
        raise ValueError("SNES PC address bank/offset must be integers")
    if bank not in (0x82,0x83) or not 0x8000<=address<=0xffff:
        raise ValueError("expected only authenticated high LoROM code banks")
    return ((bank&0x7f)<<15)+(address&0x7fff)


def verify_rom(rom:bytes)->dict:
    if len(rom)!=2097152 or sha(rom)!=ROM_SHA:
        raise ValueError("expected exact no-header USA retail ROM SHA")
    anchored={}
    for name,(bank,addr,expected_hex) in ANCHORS.items():
        expected=bytes.fromhex(expected_hex)
        off=lorom_offset(bank,addr)
        data=rom[off:off+len(expected)]
        if data!=expected:
            raise ValueError(f"original ROM code changed at {name} / {bank:02X}:{addr:04X}")
        anchored[name]={
            "original_snes_pc":f"{bank:02X}:{addr:04X}",
            "headerless_rom_byte_offset":off,
            "actual_machine_instruction_byte_length":len(data),
            "actual_machine_instruction_hex":data.hex(),
            "source_rom_byte_range_sha256":sha(data),
        }
    return anchored


def nmi_effective_vram_word(queue_word:int)->int:
    # 82:B8F4 BIT #$0080 ; if set ADC #$0800 ; STA $2116.
    # Hardware queue permits additional modes; this is the explicitly verified normal path.
    if type(queue_word) is not int or not 0<=queue_word<=0x7fff:
        raise ValueError("expected original DMA queue 15-bit VRAM word address")
    return (queue_word+0x800 if queue_word&0x80 else queue_word)&0x7fff


def audit(rom:bytes,archive:bytes)->dict:
    opcodes=verify_rom(rom)
    if len(archive)>1_000_000 or sha(archive)!=SOURCE_SHA:
        raise ValueError("wrong original no-skip 24-tick Mesen evidence")
    receipt=audit_mesen(archive)
    if (receipt["source_canonical_archive_sha256"]!=SOURCE_SHA or
            receipt["new_source_actual_consecutive_no_skip_Mesen_ticks"]!=list(range(1601,1625))):
        raise ValueError("original executed source provenance differs")
    per={}
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for name,slot in (("blue",96),("red",97)):
            addresses=None
            fixed_oam=None
            frames=[]
            for tick in range(1601,1625):
                oam=decode_oam(z.read(f"frame-{tick:06d}-oam.bin"))[slot]
                obj=decode_source_obj(oam,
                    z.read(f"frame-{tick:06d}-vram.bin"),
                    z.read(f"frame-{tick:06d}-cgram.bin"),
                    oam_mode=4,obj_base=0x6000,second_table_offset=0x1000)
                tile_words=tuple(obj["tile_word_addresses"])
                identity=(oam["source_oam_tile_word9"],obj["source_palette_id"],
                          oam["source_obj_hflip"],oam["source_obj_vflip"],
                          oam["source_obj_size_select_large"])
                if addresses is None:
                    addresses=tile_words
                    fixed_oam=identity
                elif addresses!=tile_words or identity!=fixed_oam:
                    raise ValueError("source sprite tile selection or palette not fixed")
                frames.append({"tick":tick,"oam_x":oam["source_oam_x_signed9"],
                              "oam_y":oam["source_oam_y_raw8"]})
            if len(addresses)!=64 or len(set(addresses))!=64:
                raise ValueError("expect exactly 64 distinct original 8x8 tile addresses")
            if min(addresses)<0x6000 or max(addresses)>0x6fff:
                raise ValueError("observed target VRAM outside ROM code's graphic-transfer region")
            per[name]={
                "observed_source_OAM_slot":slot,
                "original_fixed_oam_tileword9":fixed_oam[0],
                "original_fixed_sprite_palette_id":fixed_oam[1],
                "actual_source_original_vram_tile_address_words":list(addresses),
                "source_vram_first_word":min(addresses),
                "source_vram_last_word":max(addresses),
                "actual_held_oam_positions":frames,
                "original_source_vram_addresses_in_queue_writer_sixteen_k_word_region":True,
            }
    if (per["red"]["source_vram_first_word"]!=0x6000 or
            per["blue"]["source_vram_first_word"]!=0x6880 or
            nmi_effective_vram_word(0x6000)!=0x6000 or
            nmi_effective_vram_word(0x6080)!=0x6880):
        raise ValueError("source VRAM word data does not match original code region split")
    return {
        "schema":SCHEMA,
        "retail_original_USA_ROM_sha256":ROM_SHA,
        "original_USA_ROM_size_bytes":len(rom),
        "independently_executed_Mesen24_source_zip_sha256":SOURCE_SHA,
        "original_source_Mesen_bridge_ticks":list(range(1601,1625)),
        "authentic_original_ROM_opcode_anchors":opcodes,
        "rider_presentation_phase_modulus_from_original_ROM":24,
        "rider_angle_index_modulus_from_original_ROM":64,
        "source_24_phase_times_64_with_additional_presentation_offset_not_proven_physical_poses":True,
        "original_tile_dma_source_bank_queue_WRAM":"7E:15A1",
        "original_tile_dma_source_address_queue_WRAM":"7E:1645",
        "original_tile_dma_destination_word_queue_WRAM":"7E:16E9",
        "original_tile_dma_pending_flag_WRAM":"7E:0306",
        "original_NMI_DMA_channel_registers":["4300","4301","4302","4304","4305","420B","2115","2116"],
        "original_NMI_normal_dma_transfer_bytes_per_entry":32,
        "original_NMI_bit_7_of_queue_dest_adds_vram_words":0x800,
        "example_queued_dest_red_6000_to_effective_word":nmi_effective_vram_word(0x6000),
        "example_queued_dest_bit7_6080_to_effective_blue_6880_word":nmi_effective_vram_word(0x6080),
        "real_observed_source_vram_destinations_are_from_two_provisional_banks":True,
        "original_DMA_queue_values_at_any_captured_tick_measured":False,
        "original_CPU_writer_or_DMA_trigger_PC_captured_at_runtime":False,
        "original_1994_3D_mesh_camera_joint_angles_recovered":False,
        "original_OAM_OBSEL_register_measurement_repeated_every_new_tick":False,
        "original_24_and_64_state_axes_are_representation_indices_not_degrees":True,
        "per_real_original_source_racer":per,
    }


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom",required=True,type=Path)
    parser.add_argument("--source-zip",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    result=audit(args.rom.read_bytes(),args.source_zip.read_bytes())
    publish_text_once(args.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"status":"PASS","ROM":ROM_SHA,"anchors":len(ANCHORS),
        "original_2d_source_frames":24,
        "phase_states":24,"angle_states":64,
        "original_source_first_words":{
            who:r["source_vram_first_word"] for who,r in result["per_real_original_source_racer"].items()},
        "no_original_1994_3D_pose_claim":True},sort_keys=True))


if __name__=="__main__":
    main()
