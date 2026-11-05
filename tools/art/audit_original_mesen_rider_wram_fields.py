#!/usr/bin/env python3
"""Read verified *candidate* original rider WRAM fields, without assigning 1994 3D poses.

The optional original Mesen WRAM snapshot is from a paused post-PPU frame
boundary. It proves byte values, not which CPU instruction wrote them,
whether a DMA queue is still pending, or historical source 3D geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.art.capture_original_mesen_ppu_raw import (
    RIDER_WRAM_FILENAME_SUFFIX, RIDER_WRAM_SIZE,
    ROM_SHA, MESEN_REVISION, SCHEMA as CAPTURE_SCHEMA,
    validate_snapshot_files,
)
from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-ORIGINAL-RIDER-POSTFRAME-WRAM-CANDIDATE-WORDS/1"
# These imported reverse-engineering labels are hypotheses, NOT fully
# established P1/P2/rig ownership at the capture boundary.
CANDIDATE_WORDS={
    "frame_buffer_phase_0300":0x0300,
    "persistent_P1_orientation_04c7":0x04C7,
    "persistent_P2_orientation_04c9":0x04C9,
    "current_rider_angle_workspace_0f49":0x0F49,
    "current_rider_frame_workspace_0f77":0x0F77,
    "current_rider_wheel_phase_workspace_0f83":0x0F83,
    "current_rider_signed_spin_speed_0f8f":0x0F8F,
    "current_rider_presentation_id_0f97":0x0F97,
    "current_rider_overlay_workspace_0fd9":0x0FD9,
    "persistent_P1_presentation_id_0fe9":0x0FE9,
    "persistent_P2_presentation_id_0feb":0x0FEB,
}
CANDIDATE_BYTE_FIELDS={"tile_DMA_pending_0306":0x0306}
QUEUES={
    "source_bank_15a1":(0x15A1,162),
    "source_address_1645":(0x1645,162),
    "VRAM_destination_16e9":(0x16E9,162),
}


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def read_word_le(data:bytes,at:int)->dict:
    if (not isinstance(data,bytes) or len(data)!=RIDER_WRAM_SIZE or
            type(at) is not int or not 0<=at<len(data)-1):
        raise ValueError("exact original 6KiB source WRAM and bounded word offset required")
    unsigned=int.from_bytes(data[at:at+2],"little")
    return {"raw_le16_hex":f"{unsigned:04x}",
            "unsigned_16bit":unsigned,
            "signed_16bit":unsigned if unsigned<0x8000 else unsigned-0x10000}


def interpret_raw(data:bytes)->dict:
    if not isinstance(data,bytes) or len(data)!=RIDER_WRAM_SIZE:
        raise ValueError("exact original 6KiB source WRAM required")
    fields={name:read_word_le(data,at)
            for name,at in CANDIDATE_WORDS.items()}
    fields.update({name:{"raw_u8_hex":f"{data[at]:02x}","unsigned_8bit":data[at]}
                   for name,at in CANDIDATE_BYTE_FIELDS.items()})
    queue={}
    for name,(start,n) in QUEUES.items():
        payload=data[start:start+n]
        if len(payload)!=n:
            raise ValueError("candidate DMA queue outside original WRAM capture")
        words=[int.from_bytes(payload[i:i+2],"little")
               for i in range(0,n,2)]
        queue[name]={
            "start_WRAM_offset_hex":f"{start:04x}",
            "byte_length":n,
            "sha256":sha(payload),
            "first_four_raw_u16_hex":[f"{v:04x}" for v in words[:4]],
            "first_ffff_word_index_or_null":next(
                (i for i,v in enumerate(words) if v==0xFFFF),None),
        }
    return {"candidate_original_ram_fields":fields,
            "candidate_transfer_list_byte_slices":queue}


def audit_directory(root:Path)->dict:
    manifest_path=root/"manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError("exact original captured Mesen manifest missing")
    manifest_raw=manifest_path.read_bytes()
    manifest=json.loads(manifest_raw)
    validate_snapshot_files(root,manifest)
    if (manifest.get("schema")!=CAPTURE_SCHEMA or
            manifest.get("original_USA_ROM_sha256")!=ROM_SHA or
            manifest.get("emulator_source_revision")!=MESEN_REVISION or
            manifest.get("source_original_rider_work_ram_0000_17ff_captured") is not True):
        raise ValueError("not an authenticated opt-in original rider WRAM capture")
    rows=[]
    for frame in manifest["frames"]:
        tick=frame["emulator_bridge_frame"]
        meta=frame["original_snes_rider_work_ram_0000_17ff"]
        path=root/f"frame-{tick:06d}-{RIDER_WRAM_FILENAME_SUFFIX}"
        raw=path.read_bytes()
        if sha(raw)!=meta["sha256"]:
            raise ValueError("original rider WRAM hash changed during audit")
        rows.append({"original_emulator_bridge_tick":tick,
                     "original_emulator_step_index":frame["replayed_controller_step_index"],
                     "original_P1_controller_mask":frame["p1_controller_mask"],
                     "original_P2_controller_mask":frame["p2_controller_mask"],
                     "exact_original_wram_span_sha256":meta["sha256"],
                     **interpret_raw(raw)})
    return {
        "schema":SCHEMA,
        "source_capture_manifest_sha256":sha(manifest_raw),
        "source_original_USA_ROM_sha256":ROM_SHA,
        "source_mesen_revision":MESEN_REVISION,
        "source_replay_sha256":manifest.get("original_input_replay_sha256"),
        "source_original_emulator_executable_sha256":manifest.get("actual_emulator_executable_sha256"),
        "actual_observed_bridge_tick_list":[r["original_emulator_bridge_tick"] for r in rows],
        "original_Wram_snapshot_is_post_frame_not_writer_execution_trace":True,
        "original_WRAM_candidate_fields_are_hypotheses_not_1994_joint_ids":True,
        "source_DMA_list_may_have_been_consumed_before_snapshot":True,
        "verified_original_CPU_DMA_writer_PC":False,
        "verified_original_1994_wheel_rotation_degree_mapping":False,
        "verified_original_1994_3d_rig_pose":False,
        "owner_art_likeness_approved":False,
        "source_rows":rows,
    }


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    result=audit_directory(args.source_dir)
    publish_text_once(args.out,json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
        "schema":SCHEMA,
        "source_original_ticks":result["actual_observed_bridge_tick_list"],
        "candidate_fields":list(CANDIDATE_WORDS),
        "real_1994_3d_pose_recovered":False,
    }))


if __name__=="__main__":
    main()
