#!/usr/bin/env python3
"""Strict source-size whole-route sparse 1P Snes9x vs Windows PPU witness.

Compares one independently executed original 5447-frame route (261 source
callbacks) to each REAL callback captured from the source-pinned Windows game.
Same guest source route semantics; original frame f-1 vs native guest f is
explicitly source-tested and never silently shifted to a nearest frame.
Never manufacture missing Windows presentations, crop 224→216 or mask
BG, OBJ, split, results, 7:6 PAR pixels. Diagnostic raster parity only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.qa08_compare_original_windows_oneplayer import (
        compare, no_turbo, verify_windows_checkout_script,
    )
except ImportError:
    from qa08_compare_original_windows_oneplayer import (
        compare, no_turbo, verify_windows_checkout_script,
    )

ORIGINAL_SCHEMA="qa08-original-snes9x-authentic-oneplayer-sparse-full-route-source/1"
WINDOWS_SCHEMA="qa08-bounded-windows-original-1p-transition-raster-coverage/1"
RESULT_SCHEMA="qa08-independent-original-windows-1p-sparse-fullroute-rgb5/1"
ROM_SHA="859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
W,H=256,224
HEADER=(b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
        b"TUPLTYPE RGB_ALPHA\nENDHDR\n")
FIRST,LAST,STEP=1280,5440,16
PX=W*H


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def source_rgb_from_pam(path:Path, expected_sha:str)->bytes:
    raw=path.read_bytes()
    if (sha(raw)!=expected_sha or not raw.startswith(HEADER)
        or len(raw)!=len(HEADER)+PX*4):
        raise ValueError("native Windows P7 source SHA/header/geometry mismatch")
    return raw[len(HEADER):]


def analyze(original_dir:Path, win_dir:Path, route:Path)->dict:
    original=json.loads((original_dir/"qa08-original-1p-sparse.json").read_text())
    windows=json.loads((win_dir/"qa08-windows-original-oneplayer-coverage.json").read_text())
    script=route.read_bytes()
    original_script=(original_dir/"qa08-original-1p.script").read_bytes()
    if (original.get("schema")!=ORIGINAL_SCHEMA
        or original.get("USA_ROM_sha256")!=ROM_SHA
        or original.get("source_pixel_geometry")!=[W,H]
        or original.get("sampled_original_callback_selection")!=[FIRST-1,LAST-1,STEP]
        or original.get("requested_original_callbacks")!=261
        or original.get("original_script_exit_guest_frame")!=5447
        or original.get("release_approved") is not False
        or len(original.get("all_original_source_frame_hashes",[]))!=261):
        raise ValueError("unqualified original Snes9x fullroute source")
    if (sha(no_turbo(script))!=original.get(
           "source_original_route_LF_without_turbo_sha256")
        or no_turbo(script)!=original_script):
        raise ValueError("authentic original action script differs from Windows route")
    win_eol=verify_windows_checkout_script(
        script,windows.get("exact_original_1P_input_route_sha256",""))
    if (windows.get("schema")!=WINDOWS_SCHEMA
        or windows.get("logical_source_geometry")!=[W,H]
        or windows.get("callback_frame_selection_window")!=[FIRST,LAST,STEP]
        or windows.get("original_input_route_native_simulations")!=5447
        or windows.get("same_original_snes9x_raster_parity_proven") is not False
        or windows.get("release_quality_ledger_admitted") is not False
        or windows.get("CPU_camera_input_phase_and_1P_complete_event_proven") is not False):
        raise ValueError("unqualified real Windows 1P original PPU source")
    source_refs={}
    for idx,entry in enumerate(original["all_original_source_frame_hashes"]):
        callback=FIRST-1+STEP*idx
        if (entry.get("original_callback")!=callback
            or entry.get("original_1based_run_frame")!=callback+1):
            raise ValueError("original callback source frame numbering changed")
        path=original_dir/"frames"/f"frame_{callback:06d}_256x224.raw"
        raw=path.read_bytes()
        if len(raw)!=PX*4 or sha(raw)!=entry.get("actual_unmodified_BGRX_sha256"):
            raise ValueError("original emulator BGRX source incomplete or mutated")
        source_refs[callback]=raw
    have=windows.get("complete_source_RGBA_P7_sha256_by_frame")
    if not isinstance(have,dict):
        raise ValueError("Windows PPU captured-source record missing")
    frames=sorted(int(frame) for frame in have)
    if (len(frames)!=windows.get("actual_source_callback_count")
        or len(frames)==0 or len(frames)>261
        or any(f<FIRST or f>LAST or (f-FIRST)%STEP for f in frames)):
        raise ValueError("real native source slots not bounded/unique")
    actual_files={
        p.name for p in (win_dir/"source").iterdir() if p.is_file()
    }
    required_files={f"ur-baldosa-original-source-{f:06d}.pam" for f in frames}
    if required_files!=actual_files:
        raise ValueError("Windows source archive missing/added genuine PPU fields")
    results=[]
    for frame in frames:
        native=source_rgb_from_pam(
            win_dir/"source"/f"ur-baldosa-original-source-{frame:06d}.pam",
            have[str(frame)])
        original_source=source_refs[frame-1]
        outcome=compare(original_source,native)
        results.append({
            "real_windows_guest_frame":frame,
            "real_original_callback":frame-1,
            "source_size_RGB5_correct_pixels":outcome["same_RGB5_pixels"],
            "wrong_original_RGB5_pixels":outcome["wrong_RGB5_pixels"],
            "wrong_original_RGB5_pixels_by_row":outcome["wrong_pixels_by_row"],
            "first_eight_wrong_source_pixels":outcome["first_eight_wrong"],
            "windows_source_RGBA_P7_SHA256":have[str(frame)],
        })
    first_div=next((r for r in results if r["wrong_original_RGB5_pixels"]!=0),None)
    categories={
        "race_entry_and_countdown": [r for r in results if r["real_windows_guest_frame"]<=1744],
        "moving_race_and_camera": [r for r in results if 1760<=r["real_windows_guest_frame"]<=5104],
        "finish_result_return_menu": [r for r in results if r["real_windows_guest_frame"]>=5120],
    }
    if any(len(v)<2 for v in categories.values()):
        raise ValueError("insufficient actual native PPU source for an entire phase")
    return {
        "schema":RESULT_SCHEMA,
        "status":("all_observed_1P_sparse_source_frames_exact" if first_div is None
                  else "actual_1P_source_raster_strict_divergence"),
        "whole_256x224_unmasked_RGB5_pixel_comparison":True,
        "original_USA_ROM_SHA256":ROM_SHA,
        "original_snes9x_source_261_callbacks_verified":True,
        "actual_windows_source_sha256":windows.get("exact_executable_sha256"),
        "native_1P_source_guest_CRC_frames":5447,
        "native_1P_source_guest_CRC_sha256":windows["native_guest_CRC_source_sha256"],
        "native_Windows_checkout_route_EOL":win_eol,
        "original_source_sampled_callbacks":261,
        "actual_native_source_callbacks":len(results),
        "actual_original_native_source_pixels_evaluated":len(results)*PX,
        "total_wrong_RGB5_pixels":sum(r["wrong_original_RGB5_pixels"] for r in results),
        "first_real_divergent_guest_frame":(
            first_div["real_windows_guest_frame"] if first_div else None),
        "three_true_scene_regions":{
            key:{"observed":len(rows),
                 "wrong_frames":sum(r["wrong_original_RGB5_pixels"]!=0 for r in rows),
                 "wrong_pixels":sum(r["wrong_original_RGB5_pixels"] for r in rows)}
            for key,rows in categories.items()},
        "missing_native_presentation_callbacks_are_not_inferred":True,
        "no_temporal_alignment_spatial_repair_or_216_high_crop":True,
        "full_CPU_gameplay_event_and_original_camera_input_phase_proven":False,
        "HD_art_owner_approved":False,
        "graphics_or_release_ledger_gates_admitted":0,
        "strict_independent_each_observed_original_to_windows_frame":results,
    }


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    for item in ("original-dir","windows-dir","route","out"):
        parser.add_argument("--"+item,required=True,type=Path)
    args=parser.parse_args()
    result=analyze(args.original_dir,args.windows_dir,args.route)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",
                        encoding="utf-8")
    print("QA08_WIN32_ORIGINAL_1P_SPARSE",
          "status="+result["status"],
          "frames="+str(result["actual_native_source_callbacks"]),
          "wrong="+str(result["total_wrong_RGB5_pixels"]),
          "first_divergent="+str(result["first_real_divergent_guest_frame"]),
          "release=0")


if __name__=="__main__":
    main()
