#!/usr/bin/env python3
"""Bounded original 2014 Switcher post-result activation witness.

Only reads the source-movie trace that the existing event-oracle scan already
captured. A subsequent active track is a source-only candidate, not verified
native progression, Race/Circuit/Stunt completion, or release credit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import probe_attract_cycle as trace
import qa01_original_fresh_switcher_01dd_report as paired_auth

SCHEMA = "UR-QA01-SWITCHER-ORIGINAL-2014-POSTRESULT-WALK/1"
ENTRY = 12327
RESULT = 17030
HORIZON = 22000
MIN_STABLE_ACTIVE = 8


def summarize(states: dict[int, dict]) -> dict:
    if not isinstance(states, dict) or RESULT not in states:
        raise ValueError("no original movie source result frame 17030")
    if (not all(type(f) is int and 0 <= f <= HORIZON for f in states)
            or len(states) > HORIZON + 1
            or len(states) < 1000):
        raise ValueError("original source timeline is absent, oversized or out of bounds")
    # The original changed-byte trace decoder expands every intervening
    # frame. A sparse splice cannot masquerade as an unbroken movie path.
    if (0 not in states
            or any(f not in states for f in range(ENTRY, RESULT + 2))):
        raise ValueError("missing original full entry-to-result source frame continuity")
    entered = states.get(ENTRY)
    if (not isinstance(entered, dict) or type(entered.get("track")) is not int
            or entered["track"] != 3
            or type(entered.get("in_race")) is not int
            or entered["in_race"] != 1):
        raise ValueError("original 2014 movie source track-3 race entry at 12327 missing")
    result = states[RESULT]
    if (not isinstance(result, dict) or result.get("track") != 3
            or result.get("menu") != 0x99
            or type(result.get("in_race")) is not int
            or result["in_race"] != 0):
        raise ValueError("original archive does not show Switcher Race B result at 17030")
    frames = sorted(f for f in states if f > RESULT)
    # This is a CHANGED-byte trace. The separately authenticated original
    # runner may have reached horizon 22000 with no further writes after
    # result 17030; no event rows after RESULT means *no visibility*, not
    # source failure or evidence of no next course. Do not prevent the NMI
    # investigation from running merely because this optional sidecar lacks
    # a post-result change.
    if frames and frames != list(range(RESULT + 1, frames[-1] + 1)):
        raise ValueError("source movie post-result timeline is truncated or spliced")
    # Scan only fresh real active frames *after* the independently qualified
    # source result. A transient in_race=1 one-frame bit flip is insufficient.
    candidates = []
    streak_start, streak_last, streak_track = None, None, None

    def flush() -> None:
        if (streak_start is None or streak_last is None
                or streak_last - streak_start + 1 < MIN_STABLE_ACTIVE):
            return
        candidates.append({
            "original_source_first_active_frame": streak_start,
            "original_source_last_contiguous_active_frame": streak_last,
            "original_source_track": streak_track,
            "contiguous_active_frames": streak_last - streak_start + 1,
            "same_track_as_completed_switcher": streak_track == 3,
            "is_definitive_native_follow_on": False,
        })

    for f in frames:
        row = states[f]
        if not isinstance(row, dict):
            raise ValueError("malformed source movie trace frame")
        state = row.get("in_race")
        track = row.get("track")
        menu = row.get("menu")
        if (type(state) is not int or state not in (0, 1)
                or type(track) is not int or not 0 <= track <= 255
                or type(menu) is not int or not 0 <= menu <= 255):
            raise ValueError("malformed original movie in-race/track fields")
        active = state == 1
        if active and streak_last == f - 1 and streak_track == track:
            streak_last = f
        else:
            flush()
            if active:
                streak_start, streak_last, streak_track = f, f, track
            else:
                streak_start, streak_last, streak_track = None, None, None
    flush()
    first = candidates[0] if candidates else None
    return {
        "schema": SCHEMA,
        "original_2014_source_movie_entry_frame": ENTRY,
        "original_2014_source_movie_result_frame": RESULT,
        "last_decoded_original_source_frame": frames[-1] if frames else RESULT,
        "observed_post_result_frames": len(frames),
        "post_result_changed_byte_trace_inconclusive_if_empty": len(frames) == 0,
        "minimum_contiguous_active_frames": MIN_STABLE_ACTIVE,
        "first_original_source_post_result_active_candidate": first,
        "post_result_candidate_count": len(candidates),
        "bounded_source_only_negative_if_no_candidate":
            first is None and len(frames) >= MIN_STABLE_ACTIVE,
        "original_movie_path_is_not_fresh_original_or_native_path": True,
        "candidate_not_proof_of_tour_continuation_or_next_native_event": True,
        "actual_original_native_post_result_entry_comparison": False,
        "release_complete_event_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace-jsonl", type=Path, required=True)
    ap.add_argument("--paired-report", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    pair = json.loads(args.paired_report.read_text(encoding="utf-8"))
    authenticated = paired_auth.verify_original_native_pair(pair)
    states = trace.frame_states(args.trace_jsonl.read_text(encoding="utf-8").splitlines())
    result = summarize(states)
    result["independent_2014_source_and_fresh_guest_pair_provenance"] = authenticated
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_follow_on": result["first_original_source_post_result_active_candidate"],
        "native_post_result_progression_proven": False,
        "release_course_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
