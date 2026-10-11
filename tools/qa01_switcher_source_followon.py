#!/usr/bin/env python3
"""Bounded original 2014 Switcher post-result activation witness.

Only reads the source-movie trace that the existing event-oracle scan already
captured. A subsequent active track is a source-only candidate, not verified
native progression, Race/Circuit/Stunt completion, or release credit.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import probe_attract_cycle as trace
import probe_original_event_complete as source_oracle
import qa01_original_fresh_switcher_01dd_report as paired_auth

SCHEMA = "UR-QA01-SWITCHER-ORIGINAL-2014-POSTRESULT-WALK/1"
ENTRY = 12327
RESULT = 17030
# Source-executed archive 11674751560: stable Race result until 17087.
RESULT_LAST_STABLE = 17087
HORIZON = 22000
MIN_STABLE_ACTIVE = 8


def decode_checked_changed_byte_trace(lines: list[str]) -> dict[int, dict]:
    """Validate source log sequence before calling the established decoder.

    This secondary observer does not qualify the input movie or source ROM.
    It merely refuses impossible/nonmonotonic JSONL events before building
    its own optional changed-byte follow-on classification.
    """
    previous_frame = 0
    for line in lines:
        try:
            event = json.loads(line)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("malformed original source changed-byte JSON row") from exc
        if not isinstance(event, dict):
            raise ValueError("original changed-byte trace row is not an event")
        frame = event.get("f")
        address = event.get("adr")
        value = event.get("val")
        # Actual snesref JSONL uses C-style prefixed hexadecimal strings:
        # e.g. adr="0x0009f", val="0xd7". The stock decoder already accepts
        # these via int(value, 16); do not accidentally reject its format.
        if (type(frame) is not int or not previous_frame <= frame <= HORIZON
                or type(address) is not str
                or re.fullmatch(r"(?:0[xX])?[0-9A-Fa-f]{1,6}", address) is None
                or type(value) is not str
                or re.fullmatch(r"(?:0[xX])?[0-9A-Fa-f]{1,2}", value) is None):
            raise ValueError("original source changed-byte frame/address/value invalid")
        try:
            a = int(address, 16)
            v = int(value, 16)
        except ValueError as exc:
            raise ValueError("original changed-byte record has invalid hexadecimal fields") from exc
        if not 0 <= a <= 0xFFFFFF or not 0 <= v <= 255:
            raise ValueError("original changed-byte record outside CPU byte/address range")
        previous_frame = frame
    return trace.frame_states(lines)


def reconcile_original_source_diagnostic(
        states: dict[int, dict], recorded: dict) -> dict:
    """Compare this trace with the existing original source scan's own oracle.

    This is a consistency check, not a fresh original replay or independent
    hash proof. The reference movie, ROM, source horizon and paired native
    event have already been authenticated by the existing producer.
    """
    if (not isinstance(recorded, dict)
            or recorded.get("schema") != "UR-QA01-SOURCE-RESULT-PROBE/1"
            or recorded.get("wanted_course_track") != 3
            or recorded.get("wanted_result_menu") != 0x99
            or recorded.get("original_source_horizon_host_frame") != HORIZON
            or recorded.get("original_source_horizon_observed_from_guest_dump")
               is not True
            or recorded.get("original_source_horizon_wram_bytes") != 0x20000
            or recorded.get("complete_event_qa_credit") != 0):
        raise ValueError("missing authenticated original 22000-frame source diagnostic")
    fresh = source_oracle.source_event_diagnostic(states, 3, 0x99)
    fields = (
        "source_trace_frames",
        "active_track_frames",
        "active_track_first_last",
        "source_event_candidate_entries",
        "source_intervening_foreign_active_window",
        "source_intervening_foreign_active_runs_8_frames",
        "source_intervening_foreign_active_raw_frame_count",
        "stable_original_results",
        "sampled_state_at_source_result_neighbors",
    )
    for field in fields:
        if fresh[field] != recorded.get(field):
            raise ValueError("source changed-byte trace contradicts original scan: " + field)
    # Original horizon is independently proven by the guest-owned WRAM
    # dump, NOT by the final changed-byte row. A valid no-change trace may
    # stop exactly at the result. Preserve an inconclusive sidecar rather
    # than aborting the unrelated NMI/stack probe for missing change rows.
    last = fresh["source_trace_frames"]
    if (not isinstance(last, list) or len(last) != 2
            or type(last[0]) is not int or type(last[1]) is not int
            or last[0] != 0 or not RESULT <= last[1] <= HORIZON
            or ENTRY not in fresh["source_event_candidate_entries"]):
        raise ValueError("original source trace lacks proven Switcher entry/result scope")
    interval_proven = any(
        row.get("menu") == 0x99
        and row.get("start") == RESULT
        and row.get("end") == RESULT_LAST_STABLE
        and row.get("track_at_start") == 3
        and row.get("in_race") == 0
        for row in fresh["stable_original_results"]
    )
    if last[1] >= RESULT_LAST_STABLE and not interval_proven:
        raise ValueError("original source trace lacks proven Switcher result interval")
    return {
        "source_diagnostic_recomputed_from_same_decoded_trace": True,
        "original_source_horizon_guest_dump_attested": True,
        "original_result_interval_recomputed_from_changed_byte_trace":
            [RESULT, RESULT_LAST_STABLE] if interval_proven else None,
        "result_interval_inconclusive_without_changed_byte_visibility":
            not interval_proven,
        "source_diagnostic_consistency_not_separate_execution_or_identity_proof": True,
    }


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
            or any(f not in states for f in range(ENTRY, RESULT + 1))):
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
    # A changed-byte stream with no updates through the full result screen
    # must remain INCONCLUSIVE rather than block independent NMI sampling.
    stable_screen_attested = RESULT_LAST_STABLE in states
    if stable_screen_attested:
        for f in range(RESULT, RESULT_LAST_STABLE + 1):
            row = states.get(f)
            # result_runs observes the stable MENU at every frame.
            # It does NOT prove unchanged track/in_race scratch bytes in
            # between separately sampled boundary frames. The original
            # diagnostic attests their 17030 and 17087 values only.
            if (not isinstance(row, dict)
                    or type(row.get("menu")) is not int or row["menu"] != 0x99):
                raise ValueError("archived original 17030..17087 stable result screen altered")
        last = states[RESULT_LAST_STABLE]
        if (type(last.get("track")) is not int or last["track"] != 3
                or type(last.get("in_race")) is not int or last["in_race"] != 0):
            raise ValueError("archived result-ending original sampled state altered")
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
    nonbinary_race_state_frames = 0
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
        if (type(state) is not int or not 0 <= state <= 255
                or type(track) is not int or not 0 <= track <= 255
                or type(menu) is not int or not 0 <= menu <= 255):
            raise ValueError("malformed original movie in-race/track fields")
        # 0313 is also timer/scoring scratch: the real 2014 Bowl Stunt
        # source diagnostic records the value 60. Only 1 is an ordinary
        # active-race witness; other nonbinary values remain ambiguous,
        # not a fabricated new race or an impossible original CPU state.
        if state not in (0, 1):
            nonbinary_race_state_frames += 1
        active = stable_screen_attested and state == 1 and f > RESULT_LAST_STABLE and menu != 0x99
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
        "original_2014_stable_result_screen_last_frame": RESULT_LAST_STABLE,
        "original_result_screen_stability_fully_observed": stable_screen_attested,
        "next_active_candidate_must_follow_stable_result_screen": True,
        "last_decoded_original_source_frame": frames[-1] if frames else RESULT,
        "observed_post_result_frames": len(frames),
        "post_result_changed_byte_trace_inconclusive_if_empty": len(frames) == 0,
        "minimum_contiguous_active_frames": MIN_STABLE_ACTIVE,
        "nonbinary_post_result_race_state_frame_count":
            nonbinary_race_state_frames,
        "nonbinary_0313_frames_are_ambiguous_timing_or_scratch_not_active_race_proof": True,
        "first_original_source_post_result_active_candidate": first,
        "post_result_candidate_count": len(candidates),
        "bounded_source_only_negative_if_no_candidate":
            first is None and stable_screen_attested
            and frames[-1] - RESULT_LAST_STABLE >= MIN_STABLE_ACTIVE
            and nonbinary_race_state_frames == 0,
        "original_movie_path_is_not_fresh_original_or_native_path": True,
        "candidate_not_proof_of_tour_continuation_or_next_native_event": True,
        "actual_original_native_post_result_entry_comparison": False,
        "release_complete_event_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace-jsonl", type=Path, required=True)
    ap.add_argument("--paired-report", type=Path, required=True)
    ap.add_argument("--source-diagnostic", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    pair = json.loads(args.paired_report.read_text(encoding="utf-8"))
    authenticated = paired_auth.verify_original_native_pair(pair)
    states = decode_checked_changed_byte_trace(
        args.trace_jsonl.read_text(encoding="utf-8").splitlines())
    result = summarize(states)
    diagnostic = json.loads(args.source_diagnostic.read_text(encoding="utf-8"))
    result.update(reconcile_original_source_diagnostic(states, diagnostic))
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
