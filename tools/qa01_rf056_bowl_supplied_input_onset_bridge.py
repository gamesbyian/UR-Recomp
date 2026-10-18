#!/usr/bin/env python3
"""RF056 CPU-facing *supplied* input/onset crosswalk from two immutable Bowl runs.

Never infer that a replayed guest consumed a supplied input without observing
the actual controller CPU bus read. The historical movie, fresh Snes9x and
native Baldosa are three distinct state/clock axes. No frame rephase is applied.
"""
from __future__ import annotations
import argparse, hashlib, json, zipfile
from pathlib import Path
import qa01_rf056_bowl_temporal_byte_transition_audit as rf056

INPUT_ZIP_SHA="0fe45f6116e2b9c1e90a126acb67d9530e64beb5144fb58c637c9b6a228eeaf1"
SOURCE_PATH="bowl/replay/ref.input"
NATIVE_PATH="bowl/replay/pinned-baldosa.input"
META_PATH="bowl-source-input-identity.json"
INPUT_REF_SHA="24e8cb669271e1e1a57dc3bfff0cb1a54d30c2946e15ab3edabe4e1a8838b825"
INPUT_NATIVE_SHA="0db2471a91bb00befe5e113c2eebe7c820b405ee38880e68d4a5c939be5543d5"
EXPECTED_COUNT=593

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def parse_events(data:bytes)->list[tuple[int,int,int]]:
    out=[]
    previous_end=-1
    for line in data.decode("ascii").splitlines():
        parts=line.split(":")
        if len(parts)!=3: raise ValueError("RF056 malformed supplied input row")
        try: frame,duration=int(parts[0]),int(parts[1]); mask=int(parts[2],16)
        except ValueError as exc: raise ValueError("RF056 nonnumeric supplied input") from exc
        if frame<=previous_end or frame<0 or duration<=0 or not (0<=mask<=0xFFF):
            raise ValueError("RF056 input events overlap or have invalid masks")
        previous_end=frame+duration-1
        out.append((frame,duration,mask))
    if len(out)!=EXPECTED_COUNT:
        raise ValueError("RF056 source input event count changed")
    return out

def supplying(events:list[tuple[int,int,int]],frame:int)->dict:
    active=[(f,n,m) for f,n,m in events if f<=frame<f+n]
    if len(active)!=1: raise ValueError("RF056 target guest frame has no unique supplied input")
    f,n,m=active[0]
    return {"segment_start_host_frame":f,"segment_duration_frames":n,
            "p1_supplied_mask_hex":f"{m:03X}",
            "elapsed_host_frames_since_segment_start":frame-f}

def crosswalk(source:list[tuple[int,int,int]],
              native:list[tuple[int,int,int]])->dict:
    if len(source)!=EXPECTED_COUNT or len(native)!=EXPECTED_COUNT:
        raise ValueError("RF056 supplied input census incomplete")
    if any((fn!=fs+1 or dn!=ds or mn!=ms) for
           (fs,ds,ms),(fn,dn,mn) in zip(source,native)):
        raise ValueError("RF056 original/native supplied events not exact one-host-frame offset")
    checks={
        "fresh_original_first_mutation":supplying(source,4689),
        "fresh_native_first_mutation":supplying(native,4692),
        "fresh_original_second_mutation":supplying(source,4690),
        "fresh_native_second_mutation":supplying(native,4693),
        "fresh_original_prestep":supplying(source,4688),
        "fresh_native_prestep":supplying(native,4691),
    }
    if (checks["fresh_original_first_mutation"] != {
        "segment_start_host_frame":4689,"segment_duration_frames":7,
        "p1_supplied_mask_hex":"080","elapsed_host_frames_since_segment_start":0
    } or checks["fresh_native_first_mutation"] != {
        "segment_start_host_frame":4690,"segment_duration_frames":7,
        "p1_supplied_mask_hex":"080","elapsed_host_frames_since_segment_start":2
    }):
        raise ValueError("RF056 supplied input onset classification changed")
    return {
        "schema":"rf056-bowl-true-supplied-input-vs-full-wram-onset-crosswalk-v1",
        "original_supplied_input_events":len(source),
        "native_supplied_input_events":len(native),
        "all_593_controller_masks_and_durations_identical":True,
        "original_to_native_supplied_input_host_frame_offset":1,
        "raw_reference_state_transition_first_host_frame":4689,
        "raw_native_state_transition_first_host_frame":4692,
        "raw_fresh_original_to_native_mutation_onset_frame_displacement":3,
        "state_mutation_onset_lag_beyond_supplied_input_shift":2,
        "source_guest_frame_input_windows":checks,
        "actual_guest_CPU_controller_bus_consumption_observed":False,
        "actual_triggering_65816_branch_PC_observed":False,
        "controller_script_modified_or_shifted_by_this_audit":False,
        "complete_USA_event_acceptance_credit":0,
    }

def report(old_case:Path,input_case:Path)->dict:
    verified=rf056.report(old_case)
    if verified["independently_accepted_complete_USA_events"]!=0 or (
         verified["two_displaced_complete_frame_byte_transition_sets_equal"]!={ 
             "339-340_original__342-343_native":31,
             "340-341_original__343-344_native":642,
         }):
        raise ValueError("RF056 retained complete-byte 31+642 transition proof changed")
    if sha(input_case.read_bytes())!=INPUT_ZIP_SHA:
        raise ValueError("RF056 qualified input-run archive SHA256 differs")
    with zipfile.ZipFile(old_case) as oz,zipfile.ZipFile(input_case) as nz:
        o=json.loads(oz.read("bowl-report.json"))
        n=json.loads(nz.read("bowl-report.json"))
        m=json.loads(nz.read(META_PATH))
        for key in ("rom_sha256","original_movie_sha256","source_sram_sha256",
                    "input_sha256","bowl_next_switcher_handoff"):
            if o[key]!=n[key]:
                raise ValueError("RF056 input-run/source-game outcome changed")
        source=nz.read(SOURCE_PATH);native=nz.read(NATIVE_PATH)
    if (sha(source)!=INPUT_REF_SHA or sha(native)!=INPUT_NATIVE_SHA
        or m["route"]["original_native_supplied_masks_and_durations_equal"] is not True
        or m["route"]["native_supplied_input_shift_exact"]!=1
        or m["route"]["guest_controller_consumption_proven"] is not False
        or m["route"]["input_event_rows_per_guest"]!=EXPECTED_COUNT
        or m["route"]["shared_replay_script_sha256"]!=o["input_sha256"]):
        raise ValueError("RF056 immutable input evidence not source-qualified")
    result=crosswalk(parse_events(source),parse_events(native))
    result["original_three_guest_case_sha256"]=rf056.ZIP_SHA
    result["qualified_input_case_sha256"]=INPUT_ZIP_SHA
    result["original_movie_sram_rom_and_full_handoff_controls_unchanged"]=True
    return result

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_three_guest_case",type=Path)
    p.add_argument("--source-qualified-input-case",type=Path,required=True)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    result=json.dumps(report(args.original_three_guest_case,args.source_qualified_input_case),
                      indent=2,sort_keys=True)+"\n"
    if args.out:args.out.write_text(result,encoding="utf8")
    else:print(result,end="")
if __name__=="__main__":main()
