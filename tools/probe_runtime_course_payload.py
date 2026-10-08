#!/usr/bin/env python3
"""Match decoded RNC payloads against the live course buffer in a WRAM dump."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyze_rnc_streams import find_streams
from rnc_method1 import unpack_method1

WRAM_COURSE_BASE = 0x10000  # 7F:0000 in the 128 KiB WRAM dump

def u16le(data: bytes, off: int) -> int:
    return int.from_bytes(data[off:off+2], "little")

def compare(decoded: bytes, live: bytes, limit: int) -> dict:
    n=min(len(decoded),len(live))
    diffs=[i for i,(a,b) in enumerate(zip(decoded[:n],live[:n])) if a!=b]
    prefix=0
    while prefix<n and decoded[prefix]==live[prefix]:
        prefix+=1
    return {
        "decoded_size":len(decoded),
        "live_compared":n,
        "equal_bytes":n-len(diffs),
        "equal_fraction": (n-len(diffs))/n if n else 0.0,
        "common_prefix":prefix,
        "diff_count":len(diffs),
        "first_differences":[
            {
                "offset":f"0x{i:04X}",
                "decoded":f"0x{decoded[i]:02X}",
                "live":f"0x{live[i]:02X}",
            }
            for i in diffs[:limit]
        ],
    }

def is_fully_loaded_course(decoded: bytes, live: bytes) -> bool:
    """Prove full course identity, excluding only loader-mutated cursor 0B/0C.

    During Now Playing and early decompression, a mostly zero WRAM image may
    score >97% against a sparse wrong stream. Never promote a header/player
    relation from the generic best-match ranking alone.
    """
    return (
        len(decoded) >= 16
        and len(decoded) <= len(live)
        and decoded[:0x0B] == live[:0x0B]
        and decoded[0x0D:] == live[0x0D:len(decoded)]
    )


def rank_spawn_assignment_candidates(
    pair_a: list[int], pair_b: list[int], racer_state: dict
) -> dict:
    """Compare decoded header pairs to a *single* observed racer-state snapshot.

    A unique, zero-error match can identify the two slot assignments at this
    capture phase. A smaller nonzero distance is never treated as proof: the
    racers may have moved since spawn or the fields may be non-spawn landmarks.
    """
    a = [pair_a[0] * 16, pair_a[1] * 16]
    b = [pair_b[0] * 16, pair_b[1] * 16]
    p1 = [racer_state["slot1_x"], racer_state["slot1_y"]]
    p2 = [racer_state["slot2_x"], racer_state["slot2_y"]]

    def score(first: list[int], second: list[int]) -> dict:
        d1 = [p1[0] - first[0], p1[1] - first[1]]
        d2 = [p2[0] - second[0], p2[1] - second[1]]
        return {
            "p1_delta": d1,
            "p2_delta": d2,
            "manhattan_error": sum(map(abs, d1 + d2)),
            "exact": d1 == [0, 0] and d2 == [0, 0],
        }

    ab = score(a, b)
    ba = score(b, a)
    if a == b:
        result = "uninformative_identical_header_pairs"
    elif ab["exact"] and not ba["exact"]:
        result = "exact_A_to_P1_B_to_P2"
    elif ba["exact"] and not ab["exact"]:
        result = "exact_B_to_P1_A_to_P2"
    else:
        result = "unresolved_single_snapshot"
    return {
        "header_pair_world_units": {"A": a, "B": b},
        "observed_racer_world_units": {"P1": p1, "P2": p2},
        "A_to_P1_B_to_P2": ab,
        "B_to_P1_A_to_P2": ba,
        "discriminator": result,
        "guardrail": (
            "A single nonzero-distance snapshot cannot establish spawn"
            " assignment: race motion and phase may already differ."
        ),
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("rom",type=Path)
    ap.add_argument("wram",type=Path)
    ap.add_argument("--limit",type=int,default=64)
    ap.add_argument("--focus-stream",type=int)
    ap.add_argument("--json-out",type=Path)
    args=ap.parse_args()

    rom=args.rom.read_bytes()
    wram=args.wram.read_bytes()
    if len(wram)<0x20000:
        raise SystemExit(f"expected 128 KiB WRAM dump, got {len(wram)} bytes")
    live=wram[WRAM_COURSE_BASE:]

    results=[]
    for index,(off,packed,h) in enumerate(find_streams(rom),1):
        decoded=unpack_method1(packed)
        result=compare(decoded,live,args.limit)
        result["fully_resident_except_mutable_cursor"] = is_fully_loaded_course(
            decoded, live
        )
        result.update({
            "stream":index,
            "rom_offset":f"0x{off:06X}",
            "header_first_16":decoded[:16].hex(" "),
            "pair1":[u16le(decoded,3),u16le(decoded,5)],
            "pair2":[u16le(decoded,7),u16le(decoded,9)],
            "decoded_le16_11":u16le(decoded,11),
            "decoded_bytes_after_le16_11":len(decoded)-(u16le(decoded,11)+1),
            "decoded_le16_11_plus_1_aligned_16":((u16le(decoded,11)+1) % 16 == 0),
        })
        results.append(result)

    results.sort(key=lambda x:(x["equal_fraction"],x["common_prefix"]),reverse=True)
    best=results[0]
    racer_state={
        "slot1_x":u16le(wram,0x0411),
        "slot1_y":u16le(wram,0x0415),
        "slot2_x":u16le(wram,0x0413),
        "slot2_y":u16le(wram,0x0417),
    }
    by_stream={x["stream"]:x for x in results}
    verified = [x for x in results if x["fully_resident_except_mutable_cursor"]]
    focus=by_stream.get(args.focus_stream)
    live_le16_11=u16le(live,11)
    focus_cursor=None
    if focus is not None:
        decoded_cursor=focus["decoded_le16_11"]
        focus_cursor={
            "decoded_value":decoded_cursor,
            "live_value":live_le16_11,
            "advance":live_le16_11-decoded_cursor,
            "decoded_size":focus["decoded_size"],
            "bytes_after_cursor":focus["decoded_bytes_after_le16_11"],
            "advance_needed_for_last_byte":focus["decoded_size"]-1-decoded_cursor,
            "live_equals_last_byte_offset":live_le16_11==focus["decoded_size"]-1,
        }
    if args.focus_stream is not None:
        assigned_course = focus if focus in verified else None
    else:
        assigned_course = verified[0] if len(verified) == 1 else None
    if assigned_course is None:
        assignment = {
            "discriminator": "not_evaluable_unverified_course_payload",
            "reason": (
                "no uniquely verified full decoded course payload at 7F:0000, "
                "or the requested focus stream is not fully resident"
            ),
            "verified_stream_indices": sorted(x["stream"] for x in verified),
        }
    else:
        assignment = rank_spawn_assignment_candidates(
            assigned_course["pair1"], assigned_course["pair2"], racer_state
        )
        assignment["verified_stream_index"] = assigned_course["stream"]
        assignment["identity_basis"] = (
            "entire decoded course payload matches 7F:0000 except mutable "
            "resource-list cursor at offsets 0x0B..0x0C"
        )
    report={
        "wram_course_base":"7F:0000",
        "live_header_first_16":live[:16].hex(" "),
        "live_le16_11":live_le16_11,
        "best_match":best,
        "focus_stream":focus,
        "focus_cursor":focus_cursor,
        "top_matches":results[:5],
        "runtime_racer_state":racer_state,
        "verified_course_stream_indices": sorted(x["stream"] for x in verified),
        "spawn_assignment_probe": assignment,
    }

    print(
        f"best stream #{best['stream']} @ {best['rom_offset']}: "
        f"equal={best['equal_bytes']}/{best['live_compared']} "
        f"({best['equal_fraction']:.6f}) prefix={best['common_prefix']} "
        f"diffs={best['diff_count']}"
    )
    print(f"header: {best['header_first_16']}")
    if focus is not None:
        print(
            f"focus stream #{args.focus_stream}: "
            f"equal={focus['equal_bytes']}/{focus['live_compared']} "
            f"({focus['equal_fraction']:.6f}) prefix={focus['common_prefix']} "
            f"diffs={focus['diff_count']} "
            f"decoded_le16_11=0x{focus['decoded_le16_11']:04X} "
            f"bytes_after={focus['decoded_bytes_after_le16_11']} "
            f"live_le16_11=0x{live_le16_11:04X}"
        )
        if focus_cursor is not None:
            print(
                "focus cursor: "
                f"advance={focus_cursor['advance']} "
                f"needed_to_last={focus_cursor['advance_needed_for_last_byte']} "
                f"at_last={focus_cursor['live_equals_last_byte_offset']}"
            )
    print(f"pair1={best['pair1']} pair2={best['pair2']}")
    print(
        "runtime racers: "
        f"slot1=({racer_state['slot1_x']},{racer_state['slot1_y']}) "
        f"slot2=({racer_state['slot2_x']},{racer_state['slot2_y']})"
    )
    if best["pair1"][0]:
        print(
            "x-scale checks: "
            f"pair1.x*16={best['pair1'][0]*16} "
            f"pair2.x*16={best['pair2'][0]*16}"
        )
    print("first differences:")
    for d in best["first_differences"]:
        print(f"  {d['offset']}: decoded={d['decoded']} live={d['live']}")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
