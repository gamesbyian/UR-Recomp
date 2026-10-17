#!/usr/bin/env python3
"""Independent archived source-only QA-08 V0 order A/B acceptance experiment.

No emulator binaries, guest modifications, image masks, pixel shifting,
nearest-frame search, 216-high crop, or new producer jobs. Reuse 2014
Snes9x 261/263 sources, old Windows and compiled corrected Windows from
immutable GitHub Actions runs. Compare every source-sized RGB5 pixel at
the exact original callback f-1 ↔ Windows guest frame f, and check raw
Windows source hash identity for every untouched 1P scene.

A green report means a narrow raster correction, NOT QA-08 release gate,
complete guest-event equivalence, Remastered artistic signoff or real
physical-device approval.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

try:
    from tools.qa08_compare_windows_original_oneplayer_sparse import analyze as oneplayer
    from tools.qa08_compare_windows_original_twoplayer_sparse import inspect as twoplayer
except ImportError:
    from qa08_compare_windows_original_oneplayer_sparse import analyze as oneplayer
    from qa08_compare_windows_original_twoplayer_sparse import inspect as twoplayer

SCHEMA="qa08-archived-real-windows-v0-hdma-original-1p2p-independent-ab/1"
OLD_EXE="9107fe4e5e6515f161f4f3e666349def7f4b2f242a1837db32ac09c70d1c1ac9"
NEW_EXE="362746e641a03476e5230598fc91ddf2a91e218f5cf3d6fb4166c7033f8020cb"
OLD_1P_EXE="a07a7f13bd4dbaef148fc54f56331a59eec2f65f668bec167ce7d4ca47753262"
CRC_2P="c782121bdab59790cd11ba2cb02c567adf1ca4f0a6218c75da5a896b52f04876"
CRC_1P="45d7675858ebf3e3a051a58d2af104b6d2d9a66e7700da8248ad571713662c41"


def verify(original1:Path,old1:Path,new1:Path,route1:Path,
           original2:Path,old2:Path,new2:Path,route2:Path)->dict:
    a1=oneplayer(original1,old1,route1)
    b1=oneplayer(original1,new1,route1)
    a2=twoplayer(original2,old2,route2)
    b2=twoplayer(original2,new2,route2)
    if (a1["actual_windows_source_sha256"]!=OLD_1P_EXE or
        a2["actual_native_Windows_executable_sha256"]!=OLD_EXE or
        b1["actual_windows_source_sha256"]!=NEW_EXE or
        b2["actual_native_Windows_executable_sha256"]!=NEW_EXE):
        raise ValueError("source-bound Windows exact binary pin differs")
    if not (a1["native_1P_source_guest_CRC_sha256"]==
            b1["native_1P_source_guest_CRC_sha256"]==CRC_1P and
            a2["native_guest_CRC_sha256"]==
            b2["native_guest_CRC_sha256"]==CRC_2P):
        raise ValueError("real 1P or 2P guest input/CPU transcript changed")
    old_1p=a1["strict_independent_each_observed_original_to_windows_frame"]
    new_1p=b1["strict_independent_each_observed_original_to_windows_frame"]
    old_2p=a2["full_original_to_native_source_comparisons"]
    new_2p=b2["full_original_to_native_source_comparisons"]
    if [len(v) for v in (old_1p,new_1p,old_2p,new_2p)]!=[261,261,263,263]:
        raise ValueError("original or Windows exact source scene count invalid")
    unaffected=[]
    one_regressions=[]
    for old,new in zip(old_1p,new_1p):
        if (old["real_windows_guest_frame"]!=new["real_windows_guest_frame"] or
            old["real_original_callback"]!=new["real_original_callback"]):
            raise ValueError("one-player source registration changed")
        if old["windows_source_RGBA_P7_SHA256"]!=new["windows_source_RGBA_P7_SHA256"] or (
            old["wrong_original_RGB5_pixels"]!=new["wrong_original_RGB5_pixels"]):
            one_regressions.append(old["real_windows_guest_frame"])
        else:
            unaffected.append(old["real_windows_guest_frame"])
    changed=[]
    regressions=[]
    equal=[]
    for old,new in zip(old_2p,new_2p):
        guest=old["real_windows_guest"]
        if guest!=new["real_windows_guest"] or old["original_snes9x_callback"]!=new["original_snes9x_callback"]:
            raise ValueError("two-player actual original/native source frame phase changed")
        delta=old["wrong_RGB5_pixels"]-new["wrong_RGB5_pixels"]
        if delta>0:
            changed.append({"guest":guest,"before_wrong_RGB5_pixels":old["wrong_RGB5_pixels"],
                            "after_wrong_RGB5_pixels":new["wrong_RGB5_pixels"],
                            "fixed_pixels":delta,
                            "original_callback":old["original_snes9x_callback"],
                            "new_exact_frame":new["wrong_RGB5_pixels"]==0})
        elif delta<0:
            regressions.append({"guest":guest,"new_incorrect_RGB5_pixels":-delta})
        else:
            equal.append(guest)
            if old["native_unchanged_P7_sha256"]!=new["native_unchanged_P7_sha256"]:
                raise ValueError("unchanged mismatch count conceals changed native image")
    if (one_regressions or regressions or
        len(unaffected)!=261 or len(changed)!=15 or len(equal)!=248 or
        sum(r["fixed_pixels"] for r in changed)!=400974 or
        a2["strict_exact_2P_sampled_frames"]!=190 or
        b2["strict_exact_2P_sampled_frames"]!=203 or
        a2["total_original_vs_windows_incorrect_RGB5_pixels"]!=786347 or
        b2["total_original_vs_windows_incorrect_RGB5_pixels"]!=385373 or
        a1["total_wrong_RGB5_pixels"]!=19153 or b1["total_wrong_RGB5_pixels"]!=19153):
        raise ValueError("source-bound V0 original/native strict correction did not reproduce")
    if [r["guest"] for r in changed]!=list(range(3648,3873,16)):
        raise ValueError("source V0 correction affected scenes other than actual finish")
    if [r["guest"] for r in changed if r["new_exact_frame"]]!=[
        x for x in range(3648,3873,16) if x not in (3792,3872)]:
        raise ValueError("source-exact finish scene count or two residual pixels changed")
    state=json.loads((new2/"qa08-windows-2p-fullroute.json").read_text())
    samples=state["read_only_native_PPU_registers"]["per_line_native_PPU_state"]
    rows={row["ppu_line"]:row for row in samples
          if row["actual_native_snes_frame"]==3683}
    if ([rows[line]["brightness"] for line in (1,112,114)]!=[7,0,7]
        or {rows[line]["cgram_full_512_byte_FNV1a"] for line in (1,112,114)}
           !={"e79794a9"}):
        raise ValueError("real V0 HDMA brightness/CGRAM source-registered state not corrected")
    hdma=state["read_only_native_HDMA7_firstline"]
    real=next((x for x in hdma["live_channel7_before"] if x["frame"]==3683),None)
    if (not real or real["source_bank"]!="7e" or real["BBus"]!="00"
        or real["live_WRAM_2064_to_206B"]!="6f07020060070000"):
        raise ValueError("genuine source native channel-seven descriptor not captured")
    return {
        "schema":SCHEMA,
        "source":"independently executed original Snes9x and real native Win32 source-sized 256x224 pixel callbacks",
        "original_1P_callbacks":261,"original_2P_callbacks":263,
        "true_new_windows_compiled_executable_sha256":NEW_EXE,
        "unchanged_complete_real_1P_guest_CRC_sha256":CRC_1P,
        "unchanged_complete_real_2P_guest_CRC_sha256":CRC_2P,
        "one_player":{"before_exact":261-a1["three_true_scene_regions"]["race_entry_and_countdown"]["wrong_frames"]-a1["three_true_scene_regions"]["moving_race_and_camera"]["wrong_frames"]-a1["three_true_scene_regions"]["finish_result_return_menu"]["wrong_frames"],
                      "after_exact":261-b1["three_true_scene_regions"]["race_entry_and_countdown"]["wrong_frames"]-b1["three_true_scene_regions"]["moving_race_and_camera"]["wrong_frames"]-b1["three_true_scene_regions"]["finish_result_return_menu"]["wrong_frames"],
                      "before_wrong":a1["total_wrong_RGB5_pixels"],
                      "after_wrong":b1["total_wrong_RGB5_pixels"],
                      "byte_identical_before_after_source_frames":261},
        "two_player":{"before_exact":190,"after_exact":203,"before_wrong":786347,
                      "after_wrong":385373,
                      "source_256x224_pixels_compared":263*256*224,
                      "changed_frames":len(changed),
                      "unchanged_frames":len(equal),
                      "wrong_pixels_eliminated":400974,
                      "regressed_frames":regressions,
                      "source_verified_finish_frame_changes":changed},
        "registered_frame3683_brightness_upper_split_lower":[7,0,7],
        "registered_frame3683_original_matching_full_CGRAM_FNV1a":"e79794a9",
        "registered_channel7_live_Wram_2064_206B":"6f07020060070000",
        "remaining_graphics_blockers":[
            "two-player 4016 blackout and periodic results CGRAM animation/scanout phase",
            "one/two player small original selection-arrow OBJ palette discrepancy",
            "physical 4x / 7:6 PAR / widescreen and approved HD racer likeness",
        ],
        "full_2P_event_guest_phase_and_graphics_release_accepted":False,
        "independent_release_ledger_gates_accepted":0,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("original1","old1","new1","route1","original2","old2","new2","route2","out"):
        p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args()
    result=verify(a.original1,a.old1,a.new1,a.route1,a.original2,a.old2,a.new2,a.route2)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("QA08_V0_REAL_WINDOWS_INDEPENDENT_PASS",
          "1p_byte_identical=261/261 2p_exact=203/263",
          "2p_wrong_reduced=400974 2p_regressions=0",
          "guest_crc_unchanged=1 release=0")


if __name__=="__main__":
    main()
