#!/usr/bin/env python3
"""QA-01/07: archived *completed* original inputs transplanted into fresh guests.

Only an observed 2014 Snes9x scene-entry/result pair can select an input
window. The same controller masks are rebased independently to the observed
reference/native guest entry. No WRAM pokes, savestate transplants or guessed
absolute native frames. A failed/partial attempt emits diagnostics, never an
accepted 45-course census row. See docs/ORIGINAL-COURSE-EVENT-CENSUS.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import analyze_rnc_streams as rnc
import extract_historical_smv_scene_window as movie
import extract_menu_visual_language as visual
import probe_attract_cycle as trace
import qa01_bowl_switcher_handoff as bowl_handoff
import qa01_bowl_source_movie_memory as bowl_source_memory
import qa01_dragster_zoo_handoff as dragster_zoo
import probe_jumpover_fallthrough_native as engine
import probe_original_non_dragster_course_entry as entry
import probe_result_screens as result_probe
import probe_tier_opponents as textdecode
from probe_runtime_course_payload import is_fully_loaded_course
from rnc_method1 import unpack_method1

# Crawler stock route selectors and genuine source-2014 result menus.
# Dragster Race A movie entry/result (794/2874) are original-emulator
# observations, but this newly enabled *fresh-guest* input transplant has
# no independent original/native paired result receipt or release credit.
# The automated bounded campaign stays limited to its 3 prequalified cases.
CASES = {
    "dragster": (1, 0, 0x99, "race-a"),
    "zoom-zoo": (2, 1, 0xBC, "circuit-a"),
    "bowl": (3, 2, 0x18, "stunt"),
    "switcher": (4, 3, 0x99, "race-b"),
}
SOURCE_HORIZON = 22000
INITIAL_FRAMES = (0, 1, 2, 4, 8, 16, 32, 64)
ZOO_PROGRESS_FRAMES = (217, 218, 219, 603, 604, 605, 840, 841, 842,
                       1531, 1532, 1533, 1720, 1721, 1722)
# Exact original Switcher source demonstrated a 34-frame course-ID=0
# terminal prelude; the existing 28-sample paired route stopped at +2400,
# never observing the real +4702 Baldosa versus +4704 Snes9x result gap.
# Keep the new samples BEFORE the earliest observed native result and
# deliberately mark them non-admission phase diagnostics.
# Paired original/native 43-sample result 38072910224 first diverges in
# menu/track at +4664 and restores in native by +4697; reference still
# reports track 0 at +4698. Sample the remaining unobserved reference
# restoration boundary +4699..+4701, NEVER the +4702 native result.
SWITCHER_TERMINAL_SOURCE_LEADS = (80, 50, 42, 40, 39, 38, 37,
                                 30, 20, 10, 9, 8, 7, 6, 5, 4, 3, 2)


class CompleteEventError(ValueError):
    pass


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observed_dump_frame(log: str, label: str) -> int:
    matches = re.findall(r"script f=(\d+) dump " + re.escape(label) +
                         r"(?=\s|$)", log)
    if len(matches) != 1:
        raise CompleteEventError(f"expected exactly one source guest dump {label}, got {len(matches)}")
    return int(matches[0])


def stock_crawler_script(slot: int) -> str:
    if slot not in (1, 2, 3, 4):
        raise CompleteEventError("only source-established Crawler track routes")
    lines = entry.MENU_PREFIX.strip().splitlines()
    lines += ["press a 2", "until 009F == F6 1200", "wait 60"]
    for _ in range(slot - 1):
        lines += ["press down 2", "wait 12"]
    lines += [f"until 009B == {slot - 1:02X} 600", "wait 30",
              "press a 2", "until 009F == 16 1200", "wait 60",
              "press a 2", "until 0313 == 01 1800", "dump race-entered"]
    return "\n".join(lines) + "\n"


def source_event_diagnostic(states: dict[int, dict],
                            track: int, result_menu: int) -> dict:
    """Report bounded original source state evidence without widening admission.

    Original 7E:00CE is mutable menu/track state and 7E:0313 is reused in
    non-race result states; a failed detection must show the true source
    values before modifying any course-result qualifier.
    """
    keys = sorted(states)
    active_frames = [f for f in keys
                     if states[f]["track"] == track and states[f]["in_race"] == 1]
    stages = result_probe.result_runs(states)
    # The archived movie contains an earlier Dragster 0x99 Race result,
    # BEFORE the later Switcher track-3 event. Never stop the Switcher
    # diagnostic at the first unrelated course's matching result menu.
    # In the absence of a same-course result, inspect the complete finite
    # source trace, not Bowl's historical frame-11985 endpoint.
    first_active = active_frames[0] if active_frames else None
    target_result = next((
        row["start"] for row in stages
        if first_active is not None and row["start"] > first_active
        and row["menu"] == result_menu and row["in_race"] != 1
        and states[row["start"]]["track"] == track
    ), None)
    diagnostic_stop = (target_result if target_result is not None
                       else keys[-1] + 1 if keys else 0)
    anchors = set()
    for row in stages:
        if row["menu"] in (result_menu, 0x2F):
            anchors.update((row["start"] - 1, row["start"],
                            row["start"] + 1, row["end"]))
    anchors.update(f for f in (11914, 11915, 11979, 11984, 11985, 11997)
                   if f in states)
    return {
        "schema": "UR-QA01-SOURCE-RESULT-PROBE/1",
        "source_trace_frames": [keys[0], keys[-1]] if keys else [],
        "wanted_course_track": track,
        "wanted_result_menu": result_menu,
        "active_track_frames": len(active_frames),
        "active_track_first_last": [active_frames[0], active_frames[-1]]
            if active_frames else [],
        "source_event_candidate_entries": [
            f for f in keys if states[f]["track"] == track
            and states[f]["in_race"] == 1
            and (f == keys[0] or states.get(f - 1, {}).get("track") != track
                 or states.get(f - 1, {}).get("in_race") != 1)
            and all(states.get(f + j, {}).get("track") == track
                    and states.get(f + j, {}).get("in_race") == 1
                    for j in range(8))
        ][:12],
        "source_intervening_foreign_active_window": (
            [first_active, diagnostic_stop] if first_active is not None else []
        ),
        "source_intervening_foreign_active_window_end_exclusive": True,
        "source_intervening_foreign_active_runs_8_frames": (
            sustained_foreign_active_runs(
                states, first_active, diagnostic_stop, track)
            if first_active is not None else []
        ),
        "source_intervening_foreign_active_raw_frame_count": (
            sum(1 for f in keys
                if first_active is not None
                and first_active <= f < diagnostic_stop
                and states[f]["in_race"] == 1
                and states[f]["track"] != track)
        ),
        "stable_original_results": [
            {**row, "track_at_start": states[row["start"]]["track"],
             "race_flag_at_start": states[row["start"]]["in_race"]}
            for row in stages if row["menu"] in (result_menu, 0x2F)
        ][:16],
        "sampled_state_at_source_result_neighbors": {
            str(f): states[f] for f in sorted(anchors) if f in states
        },
        "provenance_guardrail": (
            "Source-only trace diagnostic; no inferred event identity, "
            "native comparison, result-scoring credit or course admission."
        ),
        "complete_event_qa_credit": 0,
    }


def sustained_foreign_active_runs(states: dict[int, dict], first: int,
                                  stop: int, track: int,
                                  min_run: int = 8) -> list[dict]:
    """Only a sustained active *other course* invalidates source event origin.

    The low-WRAM track byte is writable menu scratch. A one-frame rewrite
    cannot create an independent competing race. Qualify a competing guest
    event only after >=8 uninterrupted active frames on another track.
    """
    runs = []
    current = None
    for frame in range(first, stop):
        row = states.get(frame, {})
        ident = row.get("track")
        active = row.get("in_race") == 1 and type(ident) is int and ident != track
        if active and current and current["track"] == ident:
            current["end"] = frame
        else:
            if current and current["end"] - current["start"] + 1 >= min_run:
                runs.append(current)
            current = {"start": frame, "end": frame, "track": ident} if active else None
    if current and current["end"] - current["start"] + 1 >= min_run:
        runs.append(current)
    return runs


def proven_stunt_tally_prelude(states: dict[int, dict], track: int,
                               tally_frame: int, foreign: dict) -> bool:
    """Original-only fixed result-prelude exception, NEVER native acceptance.

    The 2014 Bowl source briefly routes track ID through zero while the
    in-race byte remains 1, then resumes the original course before the
    independently observed stable 0x2F tally. It is not a new course
    entry, and only the last <=80 frames before the tally may qualify.
    """
    return (
        foreign["track"] == 0
        and foreign["start"] >= tally_frame - 80
        and foreign["end"] <= tally_frame - 5
        and states.get(foreign["start"] - 1, {}).get("track") == track
        and all(states.get(f, {}).get("track") == track
                and states.get(f, {}).get("in_race") == 1
                for f in range(foreign["end"] + 1, foreign["end"] + 5))
        and all(states.get(f, {}).get("menu") == 0x2F
                and states.get(f, {}).get("track") == track
                for f in range(tally_frame, tally_frame + 8))
    )


def proven_switcher_race_result_prelude(
        states: dict[int, dict], track: int,
        result_frame: int, foreign: dict) -> bool:
    """Only the source-observed Switcher Race B handoff, NOT a foreign event.

    The pinned 2014 original source switches transiently to course ID 0
    for exactly 34 active frames just before the track-3 Race B result,
    returns to track 3 for four active frames, leaves active racing for
    one frame, then shows the settled 0x99 result for >=8 frames.
    This narrow original-only source classifier NEVER changes game state,
    input or native admission, and cannot rescue an earlier foreign race.
    """
    return bool(
        track == 3
        and foreign.get("track") == 0
        and foreign.get("start") == result_frame - 39
        and foreign.get("end") == result_frame - 6
        and states.get(foreign["start"] - 1, {}).get("track") == track
        and states.get(foreign["start"] - 1, {}).get("in_race") == 1
        and all(states.get(f, {}).get("track") == track
                and states.get(f, {}).get("in_race") == 1
                for f in range(result_frame - 5, result_frame - 1))
        and states.get(result_frame - 1, {}).get("track") == track
        and states.get(result_frame - 1, {}).get("in_race") != 1
        and all(states.get(f, {}).get("track") == track
                and states.get(f, {}).get("menu") == 0x99
                and states.get(f, {}).get("in_race") != 1
                for f in range(result_frame, result_frame + 8))
    )


def proven_zoo_circuit_result_prelude(
        states: dict[int, dict], track: int,
        result_frame: int, foreign: dict) -> bool:
    """Source-original Zoom Zoo result transition, not a second race.

    The observed 2014 source is active on Zoo track 1 from frame 3190,
    transiently writes ID 0 at 8314..8347 (34 active frames), restores
    track 1 for 8348..8351, leaves active gameplay at 8352, and enters
    the stable 0xBC Circuit result at 8353. Require precisely that
    terminal shape. This is source-entry qualification ONLY; it neither
    masks native timing nor awards a matched event.
    """
    return bool(
        track == 1
        and foreign.get("track") == 0
        and foreign.get("start") == result_frame - 39
        and foreign.get("end") == result_frame - 6
        and states.get(foreign["start"] - 1, {}).get("track") == track
        and states.get(foreign["start"] - 1, {}).get("in_race") == 1
        and all(states.get(f, {}).get("track") == track
                and states.get(f, {}).get("in_race") == 1
                for f in range(result_frame - 5, result_frame - 1))
        and states.get(result_frame - 1, {}).get("track") == track
        and states.get(result_frame - 1, {}).get("in_race") != 1
        and all(states.get(f, {}).get("track") == track
                and states.get(f, {}).get("menu") == 0xBC
                and states.get(f, {}).get("in_race") != 1
                for f in range(result_frame, result_frame + 8))
    )



def source_event(states: dict[int, dict], track: int, result_menu: int) -> dict:
    """Detect source-original course entry and terminal result, never infer
    either from an approximate movie timestamp."""
    frames = sorted(states)
    # Across back-to-back Crawler courses the in-race flag can remain 1.
    # Demand an observed transition INTO this course, and a sustained
    # active state across the next eight frames, not merely an in-race edge
    # (nor a single transient course-id scratch write).
    entries = [
        f for f in frames
        if states[f]["track"] == track and states[f]["in_race"] == 1
        and (f == frames[0]
             or states.get(f - 1, {}).get("in_race") != 1
             or states.get(f - 1, {}).get("track") != track)
        and all(states.get(f + j, {}).get("track") == track
                and states.get(f + j, {}).get("in_race") == 1
                for j in range(8))
    ]
    # Only the first genuine sustained source entry is eligible. A one-frame
    # foreign-track scratch write during an ongoing race must not conjure a
    # second (later) start that discards earlier active-course evidence.
    # Subsequent legitimate attempts need a separately calibrated source
    # segment and cannot silently rescue a corrupted earlier event.
    entries = entries[:1]
    # DP $9F is reused as scratch. A single occurrence of 99/BC/18
    # mid-race is not a legitimate result. Reuse the already validated
    # stock result-screen analyzer and its >=8-frame stable-menu rule.
    stable_results = result_probe.result_runs(states)
    results = [row for row in stable_results
               if row["menu"] == result_menu and row["in_race"] != 1
               and states[row["start"]]["track"] == track]
    for start in entries:
        stop = next((row["start"] for row in results
                     if row["start"] > start), None)
        if stop is None:
            continue
        # Intervening active gameplay on *another* course makes this
        # candidate a later, unrelated result. Fade/transient menu values
        # alone cannot disqualify an otherwise legitimate result.
        if stop - start < 250:
            raise CompleteEventError("implausibly short source event")
        tally = next((row["start"] for row in stable_results
                      if row["menu"] == 0x2F and row["in_race"] != 1
                      and start < row["start"] < stop
                      and states[row["start"]]["track"] == track), None)
        if result_menu == 0x18 and tally is None:
            raise CompleteEventError("Stunt result missing prior 0x2F tally")
        foreign = sustained_foreign_active_runs(states, start, stop, track)
        # The original observed Bowl source has a 34-frame transient
        # 00CE=0 stage immediately before the authentic 0x2F tally. This
        # must never allow a foreign active Race/Circuit, an earlier
        # excursion, or a missing return to the same scored stunt.
        stunt_prelude = bool(
            result_menu == 0x18 and tally is not None and foreign
            and all(proven_stunt_tally_prelude(states, track, tally, run)
                    for run in foreign))
        race_prelude = bool(
            result_menu == 0x99 and track == 3 and len(foreign) == 1
            and proven_switcher_race_result_prelude(states, track, stop, foreign[0]))
        circuit_prelude = bool(
            result_menu == 0xBC and track == 1 and len(foreign) == 1
            and proven_zoo_circuit_result_prelude(states, track, stop, foreign[0]))
        if foreign and not (stunt_prelude or race_prelude or circuit_prelude):
            continue
        return {"original_entry_frame": start, "original_result_frame": stop,
                "source_stunt_tally_frame": tally,
                "source_active_frames_to_result": stop - start,
                "original_only_transient_handoff": (
                    "switcher_34_frame_track0_terminal_prelude"
                    if race_prelude else
                    "zoo_34_frame_track0_terminal_prelude"
                    if circuit_prelude else
                    "bowl_stunt_tally_prelude" if stunt_prelude else None)}
    raise CompleteEventError("source movie never demonstrated this course/result pair")


def sample_frames(case: str, source_duration: int, *,
                  zoo_race_mesh: bool = False,
                  zoo_dp_window: bool = False) -> list[int]:
    if source_duration <= 600:
        raise CompleteEventError("source event too short for bounded test")
    if zoo_race_mesh and (case != "zoom-zoo" or source_duration != 5163):
        raise CompleteEventError("full-race mesh requires exact archived 2014 Zoo source duration")
    if zoo_dp_window and not zoo_race_mesh:
        raise CompleteEventError("Zoo +5040 direct-page window requires full source race mesh")
    cap = min(2400, source_duration - 300)
    if case == "switcher":
        # Derive relative host captures only from the independently
        # established original source's observed result boundary.
        # Minimum 2-frame lead is strictly BEFORE Baldosa's earliest
        # independently observed +4702 result; no result-time rebasing.
        extra = (source_duration - lead for lead in SWITCHER_TERMINAL_SOURCE_LEADS)
        return sorted(set(INITIAL_FRAMES) | set(range(120, cap + 1, 120))
                      | {f for f in extra if f > cap and f > 0})
    extra = ZOO_PROGRESS_FRAMES if case == "zoom-zoo" else ()
    mesh = (
        set(range(2520, 5041, 120)) | {5100, 5120}
        if zoo_race_mesh else set()
    )
    # One independently executed sparse +5040 DP outlier. Dense capture is
    # read-only: every WRAM byte remains compared, no logic-frame rebase.
    if zoo_dp_window:
        mesh.update(range(5034, 5047))
    # The archived source changes track to transient 0 at race-relative
    # +5124; do not present that prelude as active Zoo gameplay. The
    # separate +5156..+5186 terminal observer covers the true boundary.
    return sorted(set(INITIAL_FRAMES) | set(range(120, cap + 1, 120))
                  | {f for f in extra if f <= cap} | mesh)


# The archived Bowl run observes a 70-frame absolute host gap from the
# genuine original/native scored tally to the stable result onset. Keep all
# diagnostic captures strictly before that result boundary.
BOWL_TALLY_PHASE_OFFSETS = (54, 60, 64, 65, 66, 67, 68, 69)
BOWL_TALLY_MEMORY_SIZES = {"wram": 0x20000, "vram": 0x10000, "cgram": 512}


def replay_script(slot: int, result_menu: int, frames: list[int],
                  stunt: bool, tally_phase: bool = False,
                  source_followthrough: bool = False,
                  zoo_next_bowl: bool = False,
                  bowl_next_switcher: bool = False,
                  dragster_next_zoo: bool = False) -> str:
    if zoo_next_bowl and (slot != 2 or result_menu != 0xBC or stunt
                          or not source_followthrough):
        raise CompleteEventError("Zoo next Bowl requires original Circuit plus source followthrough")
    if bowl_next_switcher and (slot != 3 or result_menu != 0x18 or not stunt
                                 or not source_followthrough):
        raise CompleteEventError("Bowl next Switcher requires original Stunt and source followthrough")
    if dragster_next_zoo and (slot != 1 or result_menu != 0x99 or stunt
                               or not source_followthrough):
        raise CompleteEventError("Next original Zoo requires completed Dragster Race A source followthrough")
    if tally_phase and (not stunt or slot != 3 or result_menu != 0x18):
        raise CompleteEventError("only proven source-original scored Bowl tally supports phase samples")
    lines = stock_crawler_script(slot).rstrip().splitlines()
    last = 0
    for f in frames[1:]:
        lines += [f"wait {f - last}", f"dump scene-{f:05d}"]
        last = f
    if stunt:
        lines += ["until 009F == 2F 9000", "dump result-tally"]
        if tally_phase:
            previous = 0
            for offset in BOWL_TALLY_PHASE_OFFSETS:
                if offset <= previous or offset >= 70:
                    raise CompleteEventError("Bowl tally phase observation violates pre-result window")
                lines += [f"wait {offset - previous}",
                          f"dump tally-plus-{offset:02d}"]
                previous = offset
    lines += [f"until 009F == {result_menu:02X} 9000",
              "dump result-onset", "wait 6", "dump result-stable"]
    if source_followthrough:
        previous = 6
        for offset in SOURCE_RESULT_FOLLOWTHROUGH_OFFSETS:
            if offset <= previous or offset > 72:
                raise CompleteEventError("invalid original-movie terminal follow-through offset")
            lines += [f"wait {offset - previous}", f"dump original-follow-{offset:02d}"]
            previous = offset
    if zoo_next_bowl:
        previous = SOURCE_RESULT_FOLLOWTHROUGH_OFFSETS[-1]
        for offset in ZOO_NEXT_BOWL_OFFSETS:
            if offset <= previous or offset > 280:
                raise CompleteEventError("nonmonotonic genuine Zoo-to-Bowl source handoff")
            lines += [f"wait {offset - previous}", f"dump zoo-next-bowl-{offset:03d}"]
            previous = offset
    if bowl_next_switcher:
        previous = SOURCE_RESULT_FOLLOWTHROUGH_OFFSETS[-1]
        for offset in bowl_handoff.OFFSETS:
            if offset <= previous or offset > 360:
                raise CompleteEventError("nonmonotonic genuine Bowl-to-Switcher source handoff")
            lines += [f"wait {offset - previous}", f"dump bowl-next-switcher-{offset:03d}"]
            previous = offset
    if dragster_next_zoo:
        previous = SOURCE_RESULT_FOLLOWTHROUGH_OFFSETS[-1]
        for offset in dragster_zoo.OFFSETS:
            if offset <= previous or offset > 360:
                raise CompleteEventError("nonmonotonic real Dragster-to-Zoo controller replay")
            lines.extend((f"wait {offset - previous}",
                          f"dump dragster-next-zoo-{offset:03d}"))
            previous = offset
    lines.append("quit")
    return "\n".join(lines) + "\n"


def switcher_penultimate_reference_script(base: str, source_duration: int,
                                           frames: list[int]) -> str:
    """Read-only reference-side extra dump, never move recorded controller input.

    The archived Switcher source completes after 4703 active guest-relative
    frames. The prior paired comparison independently observed reference
    onset +4704 and Baldosa onset +4702, same actual host 5783. Adding a
    reference-only source-relative +4703 dump pairs with native +4701 on
    absolute host 5782. The normal symmetric sample set is untouched.
    """
    if source_duration != 4703 or not frames or frames[-1] != source_duration - 2:
        raise CompleteEventError("same-host Switcher probe requires observed 2014 pre-result source window")
    marker = f"dump scene-{source_duration - 2:05d}\n"
    if base.count(marker) != 1:
        raise CompleteEventError("missing unique native penultimate Switcher dump")
    return base.replace(marker, marker + "wait 2\ndump source-host-minus-one\n")


def observe_switcher_same_host_penultimate(reference_dir: Path, native_dir: Path,
                                           reference_log: str, native_log: str,
                                           source_duration: int,
                                           reference_entry: int, native_entry: int,
                                           decoded: bytes) -> dict:
    """Observe the SAME absolute host frame, not a fabricated relative match."""
    if source_duration != 4703:
        raise CompleteEventError("unverified Switcher 2014 source duration")
    ref_rel, nat_rel = source_duration, source_duration - 2
    original_host = observed_dump_frame(reference_log, "source-host-minus-one")
    native_host = observed_dump_frame(native_log, f"scene-{nat_rel:05d}")
    ref_result = observed_dump_frame(reference_log, "result-onset")
    nat_result = observed_dump_frame(native_log, "result-onset")
    if (original_host != native_host
            or original_host != reference_entry + ref_rel
            or native_host != native_entry + nat_rel
            or original_host + 1 != ref_result
            or native_host + 1 != nat_result):
        raise CompleteEventError("Switcher penultimate captures are not identical genuine pre-result host frames")
    reference = load_switcher_transition_state(
        reference_dir / "source-host-minus-one.wram.bin", decoded)
    native = load_switcher_transition_state(
        native_dir / f"scene-{nat_rel:05d}.wram.bin", decoded)
    diffs = sorted(k for k in reference if reference[k] != native.get(k))
    return {
        "schema": "UR-QA01-SWITCHER-PENULTIMATE-SAME-HOST/1",
        "original_absolute_host": original_host,
        "native_absolute_host": native_host,
        "result_absolute_host": ref_result,
        "reference_guest_relative_frame": ref_rel,
        "native_guest_relative_frame": nat_rel,
        "observed_original_guest_fields": reference,
        "observed_native_guest_fields": native,
        "disagreeing_observed_fields": diffs,
        "same_host_named_guest_fields_equal": not diffs,
        "guest_memory_bytes_read_per_engine": 0x20000,
        "original_movie_input_modified": False,
        "release_complete_event_credit": 0,
        "limitation": "Named WRAM parity at one real same-host frame does not prove identical CPU PC/NMI phase or 45-course acceptance.",
    }


def observe_switcher_same_host_memory_offsets(reference_dir: Path,
                                              native_dir: Path,
                                              same_host: dict) -> dict:
    """Read-only full-guest WRAM/VRAM/CGRAM difference *offsets*, never bytes.

    Require the independently attested reference/native penultimate 5782
    same-host witness first. No source input, guest-state or framebuffer
    substitutions, and never turn a matching snapshot into admission.
    """
    if (same_host.get("schema") != "UR-QA01-SWITCHER-PENULTIMATE-SAME-HOST/1"
            or same_host.get("original_absolute_host") != 5782
            or same_host.get("native_absolute_host") != 5782
            or same_host.get("result_absolute_host") != 5783
            or same_host.get("reference_guest_relative_frame") != 4703
            or same_host.get("native_guest_relative_frame") != 4701):
        raise CompleteEventError("Switcher memory comparison requires attested same-host 5782 witness")
    rows = {}
    ref_tag, nat_tag = "source-host-minus-one", "scene-04701"
    for kind, size in BOWL_TALLY_MEMORY_SIZES.items():
        files = (reference_dir / f"{ref_tag}.{kind}.bin",
                 native_dir / f"{nat_tag}.{kind}.bin")
        if not all(p.is_file() for p in files):
            raise CompleteEventError(f"missing actual full-guest Switcher same-host {kind}")
        original, native = (p.read_bytes() for p in files)
        if len(original) != size or len(native) != size:
            raise CompleteEventError(f"invalid original/native Switcher same-host {kind} size")
        different = [i for i, (a, b) in enumerate(zip(original, native)) if a != b]
        rows[kind] = {
            "observed_guest_bytes_per_engine": size,
            "different_byte_count": len(different),
            "different_byte_offsets": [f"0x{i:05X}" for i in different[:128]],
            "offsets_truncated": len(different) > 128,
            "exact_byte_match": not different,
        }
    return {
        "schema": "UR-QA01-SWITCHER-5782-FULL-GUEST-OFFSETS/1",
        "original_host_frame": 5782,
        "native_host_frame": 5782,
        "one_frame_before_both_guest_results": True,
        "original_movie_input_modified": False,
        "memory_classes": rows,
        "all_197120_guest_bytes_equal": all(
            row["exact_byte_match"] for row in rows.values()),
        "release_complete_event_credit": 0,
        "limitation": "Full 5782 WRAM/VRAM/CGRAM byte parity, if observed, cannot prove original/native CPU PC, NMI or all-frame course execution equivalence.",
    }


def observe_bowl_tally_phase(reference_dir: Path, native_dir: Path,
                             reference_log: str, native_log: str) -> dict:
    """Only compare matching post-0x2F script-host frames.

    This is a read-only *second* clock anchor. Preserve unknown guest
    instruction/NMI/scanline and keep full 45-course release credit at zero.
    """
    tally_ref = observed_dump_frame(reference_log, "result-tally")
    tally_nat = observed_dump_frame(native_log, "result-tally")
    if tally_ref != tally_nat:
        raise CompleteEventError("Bowl original/native result-tally host-frame anchors disagree")
    terminal_ref = observed_dump_frame(reference_log, "result-onset")
    terminal_nat = observed_dump_frame(native_log, "result-onset")
    if terminal_ref != terminal_nat or terminal_ref - tally_ref != 70:
        raise CompleteEventError("Bowl actual tally-to-result host boundary differs from pinned 70-frame witness")
    rows = []
    for offset in BOWL_TALLY_PHASE_OFFSETS:
        tag = f"tally-plus-{offset:02d}"
        rframe = observed_dump_frame(reference_log, tag)
        nframe = observed_dump_frame(native_log, tag)
        if rframe != nframe or rframe - tally_ref != offset:
            raise CompleteEventError(f"misaligned Bowl tally-relative dump {tag}")
        fields = {}
        offsets = {}
        wram = {}
        for kind, size in BOWL_TALLY_MEMORY_SIZES.items():
            paths = [directory / f"{tag}.{kind}.bin"
                     for directory in (reference_dir, native_dir)]
            if not all(p.is_file() for p in paths):
                raise CompleteEventError(f"missing original/native full guest {kind} for {tag}")
            a, b = [p.read_bytes() for p in paths]
            if len(a) != size or len(b) != size:
                raise CompleteEventError(f"incorrect complete {kind} size for {tag}")
            unequal_offsets = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
            fields[kind] = len(unequal_offsets)
            # Preserve ONLY offsets, never original or native memory bytes;
            # capped to avoid unbounded reports if guests diverge badly.
            offsets[kind] = {
                "addresses": [f"0x{i:05X}" for i in unequal_offsets[:128]],
                "total": len(unequal_offsets),
                "truncated": len(unequal_offsets) > 128,
            }
            if kind == "wram":
                wram = {
                    "original_menu": a[0x009F], "native_menu": b[0x009F],
                    "original_track": a[0x00CE], "native_track": b[0x00CE],
                    "original_race_flag": a[0x0313], "native_race_flag": b[0x0313],
                }
        rows.append({"offset_from_actual_tally_host_frame": offset,
                     "absolute_host_frame": rframe,
                     "different_guest_bytes": fields,
                     "differing_byte_offsets_by_memory_class": offsets,
                     **wram})
    return {
        "schema": "UR-QA01-BOWL-TALLY-ANCHORED-PHASE/1",
        "reference_and_native_tally_host_frame": tally_ref,
        "reference_and_native_result_host_frame": terminal_ref,
        "clock_anchor": "observed stable original/native PPU 0x2F tally, not course entry",
        "whole_guest_memory_bytes_per_capture": sum(BOWL_TALLY_MEMORY_SIZES.values()),
        "same_host_frame_samples": rows,
        "all_samples_exact_guest_bytes": all(
            sum(row["different_guest_bytes"].values()) == 0 for row in rows),
        "persistent_differing_wram_offsets": (
            sorted(set.intersection(*(set(
                row["differing_byte_offsets_by_memory_class"]["wram"]["addresses"])
                for row in rows)))
            if not any(row["differing_byte_offsets_by_memory_class"]["wram"]["truncated"]
                       for row in rows) else None
        ),
        "offset_profile_cap_per_memory_class": 128,
        "retains_raw_guest_memory": False,
        "release_complete_event_credit": 0,
        "limitation": (
            "Equal host frame and guest-byte proximity do not prove CPU "
            "PC/NMI/VBlank/scanline equivalence; never rebase game inputs."
        ),
    }



# The original 2014 Zoo source result is at +5163, after a short track-zero
# prelude that restores track 1 at +5158. Capture every postframe
# through +5186 so the corrected RF-015 result return (+5179/+5180)
# can be bracketed without a sparse +8/+16 observation gap.
# This is an opt-in diagnostic; the strict result comparator is unchanged.
ZOO_TERMINAL_DURATION = 5163
ZOO_TERMINAL_FRAMES = tuple(range(5156, 5187))
# Archived 2014 source proves Switcher 0x99 through original result+57,
# then transitions toward track-select. Extend the optional, authentic source
# window through result+80 so its return phase can actually be witnessed.
# Default non-opt-in replay retains its original +40 input window and scope.
SOURCE_RESULT_FOLLOWTHROUGH_OFFSETS = (8, 16, 24, 32, 64, 72)
# Original 2014 movie: Zoo Circuit result at source frame 8353, next
# Crawler/Bowl active race at 8620. Observe the actual handoff boundary
# across three independent clocks, never infer it from TRACK_SELECT.
ZOO_NEXT_BOWL_OFFSETS = (259, 263, 264, 265, 266, 267, 268, 269, 272, 276, 280)
ZOO_SOURCE_RESULT_MOVIE_FRAME = 8353
ZOO_SOURCE_NEXT_BOWL_MOVIE_FRAME = 8620

def audit_qa01_wram_pair(original: bytes, native: bytes) -> dict:
    """Unmasked 128-KiB byte difference; diagnostic only, never release credit."""
    if len(original) != 0x20000 or len(native) != 0x20000:
        raise CompleteEventError("QA-01 WRAM audit requires two full 128-KiB images")
    address = lambda i: f"{0x7E + (i >> 16):02X}:{i & 0xFFFF:04X}"
    count, first, pages = 0, [], {}
    first_at = last_at = None
    for offset, (o, n) in enumerate(zip(original, native)):
        if o == n:
            continue
        if first_at is None:
            first_at = offset
        last_at = offset
        count += 1
        page = offset >> 8
        pages[page] = pages.get(page, 0) + 1
        if len(first) < 24:
            first.append({"snes_address": address(offset), "wram_offset": offset,
                          "original_byte": o, "native_byte": n})
    return {
        "full_wram_bytes_per_guest": 0x20000,
        "every_byte_compared": True, "excluded_byte_count": 0,
        "differing_byte_count": count, "byte_exact": count == 0,
        "first_differing_address": address(first_at) if first_at is not None else None,
        "last_differing_address": address(last_at) if last_at is not None else None,
        "first_24_differences": first,
        "changed_256_byte_pages": [
            {"page_start": address(p << 8), "differing_bytes": pages[p]}
            for p in sorted(pages)],
        "original_wram_sha256": hashlib.sha256(original).hexdigest(),
        "native_wram_sha256": hashlib.sha256(native).hexdigest(),
        "cpu_or_logic_tick_parity_proven": False, "release_complete_event_credit": 0,
    }


ZOO_TERMINAL_FIELDS = ("menu", "track", "in_race", "p1_laps", "p2_laps",
                       "p1_checkpoint", "p1_finish_gate", "p1_contact",
                       "p2_contact", "clock_raw")


def observe_zoo_race_mesh(reference_dir: Path, native_dir: Path,
                          reference_log: str, native_log: str,
                          frames: list[int], reference_entry: int,
                          native_entry: int, source_duration: int, *,
                          zoo_dp_window: bool = False) -> dict:
    """Read-only original/native same race-relative full-WRAM checkpoint mesh.

    No memory masking, clock shifting, saved-state reconstruction, CPU parity
    assertion or original/native source-input mutation. The separate dense
    terminal source probe retains the final 43-frame transition authority.
    """
    if source_duration != ZOO_TERMINAL_DURATION:
        raise CompleteEventError("unexpected source Zoo Circuit duration")
    expected = sample_frames("zoom-zoo", source_duration, zoo_race_mesh=True,
                             zoo_dp_window=zoo_dp_window)
    if frames != expected:
        raise CompleteEventError("missing or altered source-authentic Zoo race mesh frames")
    rows = []
    dp_window = []
    for offset in frames:
        tag = "race-entered" if offset == 0 else f"scene-{offset:05d}"
        original_host = observed_dump_frame(reference_log, tag)
        native_host = observed_dump_frame(native_log, tag)
        if (original_host != reference_entry + offset
                or native_host != native_entry + offset):
            raise CompleteEventError(f"uncalibrated Zoo original/native mesh sample {tag}")
        images = []
        for directory in (reference_dir, native_dir):
            path = directory / f"{tag}.wram.bin"
            if not path.is_file():
                raise CompleteEventError(f"missing Zoo full-WRAM mesh sample {path}")
            images.append(path.read_bytes())
        pair = audit_qa01_wram_pair(*images)
        if zoo_dp_window and 5034 <= offset <= 5046:
            dp_window.append({
                "race_relative_frame": offset,
                "original_absolute_host_frame": original_host,
                "native_absolute_host_frame": native_host,
                "bytes": [
                    {"address": f"7E:{address:04X}",
                     "original": images[0][address], "native": images[1][address],
                     "differs": images[0][address] != images[1][address]}
                    for address in (0x0063, 0x0069)],
                "full_wram_differing_bytes": pair["differing_byte_count"],
            })
        rows.append({
            "race_relative_frame": offset,
            "original_absolute_host_frame": original_host,
            "native_absolute_host_frame": native_host,
            "original_native_full_wram_byte_difference": pair,
        })
    first = next((row for row in rows if
                  row["original_native_full_wram_byte_difference"][
                      "differing_byte_count"] != 0), None)
    # The mesh deliberately supplements, never overrides, the existing
    # strict sampled-state/result comparator or the 45-course denominator.
    return {
        "schema": "UR-QA01-ZOO-FULL-RACE-UNMASKED-WRAM-MESH/1",
        "source_original_active_entry_movie_frame": 3190,
        "source_original_circuit_result_movie_frame": 8353,
        "archived_source_active_frames_to_result": source_duration,
        "original_2014_source_controller_masks_modified": False,
        "paired_host_clock_axes_separate": True,
        "individual_guest_entry_host_frames": {
            "original": reference_entry, "native": native_entry},
        "all_128k_wram_bytes_examined_per_pair": 0x20000,
        "masked_or_excluded_wram_bytes": 0,
        "mesh_checkpoint_count": len(rows),
        "new_post_2400_checkpoint_count": sum(f > 2400 for f in frames),
        "last_race_relative_checkpoint": frames[-1],
        "raw_byte_exact_sample_count": sum(
            not row["original_native_full_wram_byte_difference"][
                "differing_byte_count"] for row in rows),
        "first_nonidentical_raw_wram_pair": (
            {"race_relative_frame": first["race_relative_frame"],
             "original_absolute_host_frame": first["original_absolute_host_frame"],
             "native_absolute_host_frame": first["native_absolute_host_frame"],
             "first_differing_address": first[
                 "original_native_full_wram_byte_difference"][
                     "first_differing_address"],
             "differing_byte_count": first[
                 "original_native_full_wram_byte_difference"]["differing_byte_count"]}
            if first else None),
        "late_direct_page_window": ({
            "schema": "UR-QA01-ZOO-5040-DENSE-DP-WRAM/1",
            "range_inclusive": [5034, 5046],
            "samples": dp_window,
            "first_sampled_direct_page_disagreement": next(
                (row["race_relative_frame"] for row in dp_window
                 if any(b["differs"] for b in row["bytes"])), None),
            "last_sampled_direct_page_disagreement": next(
                (row["race_relative_frame"] for row in reversed(dp_window)
                 if any(b["differs"] for b in row["bytes"])), None),
            "all_guest_frames_in_range_captured": len(dp_window) == 13,
            "raw_wram_bytes_excluded": 0,
            "executed_writer_reader_or_logic_tick_proven": False,
            "release_complete_event_credit": 0,
        } if zoo_dp_window else None),
        "every_gameplay_frame_compared": False,
        "cpu_instruction_or_logic_tick_parity_proven": False,
        "native_os_disk_persistence_proven": False,
        "release_complete_usa_event_credit": 0,
        "samples": rows,
    }


def zoo_terminal_script(source_duration: int) -> str:
    """Independent fixed-frame captures, with no result polling or guest mutations."""
    if source_duration != ZOO_TERMINAL_DURATION:
        raise CompleteEventError("Zoo phase requires proven source +5163 result")
    lines = stock_crawler_script(2).rstrip().splitlines()
    last = 0
    for frame in ZOO_TERMINAL_FRAMES:
        lines += [f"wait {frame - last}", f"dump zoo-phase-{frame:05d}"]
        last = frame
    return "\n".join(lines + ["quit", ""])


def zoo_terminal_state(path: Path) -> dict:
    if not path.is_file():
        raise CompleteEventError(f"missing Zoo fixed-frame guest WRAM {path}")
    w = path.read_bytes()
    if len(w) != 0x20000:
        raise CompleteEventError("invalid Zoo fixed-frame guest WRAM size")
    if w[0x00CE] not in (0, 1):
        raise CompleteEventError("Zoo fixed-window guest entered unrelated course")
    u = lambda a: int.from_bytes(w[a:a + 2], "little")
    return {
        "menu": w[0x009F], "track": w[0x00CE], "in_race": w[0x0313],
        "p1_laps": u(0x0EF1), "p2_laps": u(0x0EF3),
        "p1_checkpoint": u(0x1199), "p1_finish_gate": u(0x119D),
        "p1_contact": u(0x0E95), "p2_contact": u(0x0E97),
        "clock_raw": [w[a] for a in (0x0E0F, 0x0E13, 0x0E17,
                                     0x0E1B, 0x0E1F)],
        "wram_sha256": hashlib.sha256(w).hexdigest(),
    }


def summarize_zoo_terminal_phase(phase: Path, reference_log: str,
                                 native_log: str, reference_entry: int,
                                 native_entry: int, ref_onset: int,
                                 nat_onset: int) -> dict:
    """Compare real event frames on separate guest-relative and host axes."""
    entries = {"reference": reference_entry, "native": native_entry}
    logs = {"reference": reference_log, "native": native_log}
    directories = {"reference": "ref", "native": "native"}
    rows = {}
    for side in entries:
        if engine.race_entry_frame(logs[side]) != entries[side]:
            raise CompleteEventError("Zoo fixed-window entry changed on replay")
        frames = {}
        for frame in ZOO_TERMINAL_FRAMES:
            tag = f"zoo-phase-{frame:05d}"
            host = observed_dump_frame(logs[side], tag)
            if host != entries[side] + frame:
                raise CompleteEventError("Zoo fixed-window sample host relation changed")
            guest = zoo_terminal_state(phase / directories[side] /
                                       f"{tag}.wram.bin")
            frames[frame] = {"relative_frame": frame, "host_frame": host,
                             **guest}
        rows[side] = frames

    def first_result(side: str) -> dict:
        for frame in ZOO_TERMINAL_FRAMES[:-3]:
            if all(rows[side][t]["menu"] == 0xBC and
                   rows[side][t]["in_race"] != 1
                   for t in range(frame, frame + 4)):
                return {"relative_frame": frame,
                        "host_frame": rows[side][frame]["host_frame"]}
        raise CompleteEventError("Zoo fixed window missing four-frame stable result")

    first = {side: first_result(side) for side in entries}
    def compare(ref: dict, nat: dict) -> dict:
        return {"different_named_fields": [
                    field for field in ZOO_TERMINAL_FIELDS
                    if ref[field] != nat[field]],
                "wram_sha256_equal": ref["wram_sha256"] == nat["wram_sha256"],
                "reference": {k: ref[k] for k in ("menu", "track", "in_race")},
                "native": {k: nat[k] for k in ("menu", "track", "in_race")}}

    relative = [{
        "relative_frame": frame,
        "reference_host_frame": rows["reference"][frame]["host_frame"],
        "native_host_frame": rows["native"][frame]["host_frame"],
        **compare(rows["reference"][frame], rows["native"][frame])
    } for frame in ZOO_TERMINAL_FRAMES]
    # Real unmasked WRAM at equal guest race-relative frame, not same host.
    for row in relative:
        tag = f'zoo-phase-{row["relative_frame"]:05d}'
        row["full_wram_byte_difference"] = audit_qa01_wram_pair(
            (phase / "ref" / f"{tag}.wram.bin").read_bytes(),
            (phase / "native" / f"{tag}.wram.bin").read_bytes())
    ref_host = {v["host_frame"]: v for v in rows["reference"].values()}
    nat_host = {v["host_frame"]: v for v in rows["native"].values()}
    hosts = sorted(set(ref_host) & set(nat_host))
    if not hosts:
        raise CompleteEventError("Zoo fixed window has no common actual host frames")
    same_host = [{
        "absolute_host_frame": host,
        "reference_relative_frame": ref_host[host]["relative_frame"],
        "native_relative_frame": nat_host[host]["relative_frame"],
        **compare(ref_host[host], nat_host[host])
    } for host in hosts]

    # This contiguous, race-entry-relative slice begins only once *both*
    # guests have reached their independently measured result. Report the
    # first OBSERVED postframe mismatch, never a first differing CPU opcode.
    # $009F is the raw wTextPos cursor, not by itself a gameplay result bit.
    post_rows = [row for row in relative
                 if row["relative_frame"] >= max(ref_onset, nat_onset)]
    if not post_rows or any(
            b["relative_frame"] != a["relative_frame"] + 1
            for a, b in zip(post_rows, post_rows[1:])):
        raise CompleteEventError("Zoo post-result frame window is not contiguous")

    def first_postframe(predicate) -> int | None:
        return next((row["relative_frame"] for row in post_rows
                     if predicate(row)), None)

    gameplay = {"track", "in_race", "p1_laps", "p2_laps",
                "p1_checkpoint", "p1_finish_gate"}
    post_edge = {
        "clock": "independently calibrated guest race-entry-relative postframes",
        "frame_range_inclusive": [post_rows[0]["relative_frame"],
                                  post_rows[-1]["relative_frame"]],
        "frames_per_guest": len(post_rows),
        "result_onset_relative_frames_equal": ref_onset == nat_onset,
        "first_named_state_difference_frame": first_postframe(
            lambda row: bool(row["different_named_fields"])),
        "first_gameplay_field_difference_frame": first_postframe(
            lambda row: bool(gameplay.intersection(row["different_named_fields"]))),
        "first_raw_text_cursor_difference_frame": first_postframe(
            lambda row: "menu" in row["different_named_fields"]),
        "first_full_wram_digest_difference_frame": first_postframe(
            lambda row: not row["wram_sha256_equal"]),
        "first_unmasked_wram_byte_difference_frame": first_postframe(
            lambda row: row["full_wram_byte_difference"]["differing_byte_count"] > 0),
        "all_postresult_full_wram_byte_pairs_equal": all(
            row["full_wram_byte_difference"]["byte_exact"] for row in post_rows),
        "first_divergent_cpu_instruction_or_writer_proven": False,
        "cold_process_sram_persistence_proven": False,
        "release_complete_event_credit": 0,
    }
    return {
        "schema": "UR-QA01-ZOO-TERMINAL-HOST-PHASE/1",
        "original_source_duration": ZOO_TERMINAL_DURATION,
        "reference_entry_host_frame": reference_entry,
        "native_entry_host_frame": native_entry,
        "fixed_window_first_stable_circuit_result": first,
        "primary_until_result_relative_frames": {
            "reference": ref_onset, "native": nat_onset},
        "fixed_vs_until_result_frame_delta": {
            "reference": first["reference"]["relative_frame"] - ref_onset,
            "native": first["native"]["relative_frame"] - nat_onset},
        "relative_frame_comparisons": relative,
        "same_host_frame_comparisons": same_host,
        "contiguous_post_result_observation": post_edge,
        "samples_per_guest": len(ZOO_TERMINAL_FRAMES),
        "full_guest_wram_bytes_per_sample": 0x20000,
        "raw_guest_memory_retained_in_report": False,
        "original_controller_masks_modified": False,
        "release_complete_event_credit": 0,
        "limitation": ("Separate fixed-frame observation cannot normalize away "
                       "the strict guest-relative terminal mismatch, prove "
                       "CPU/NMI phase, or certify progression.")
    }


def observe_zoo_terminal_phase(work: Path, args, stream: int, source_duration: int,
                               events: list[tuple[int, int, int]],
                               ref_entry: int, nat_entry: int,
                               terminal_frames: dict) -> dict:
    if (args.case != "zoom-zoo" or stream != 2 or
            args.native_backend != "pinned-baldosa"):
        raise CompleteEventError("Zoo phase probe requires source-qualified pinned Circuit")
    phase = work / "zoo-terminal-phase"
    phase.mkdir()
    script = phase / "fixed-window.script"
    script.write_text(zoo_terminal_script(source_duration))
    rl = engine.run_reference(phase, args, script, events)
    (phase / "reference.log").write_text(rl)
    nl = replay_native(phase, args, script, events, nat_entry - ref_entry)
    (phase / "native.log").write_text(nl)
    result = summarize_zoo_terminal_phase(
        phase, rl, nl, ref_entry, nat_entry,
        terminal_frames["reference_relative"],
        terminal_frames["native_relative"])
    result["fixed_window_script_sha256"] = sha(script)
    return result



def load_state(path: Path, decoded: bytes, track: int, active: bool) -> dict:
    if not path.is_file():
        raise CompleteEventError(f"missing guest frame {path}")
    w = path.read_bytes()
    if len(w) != 0x20000 or w[0x00CE] != track:
        raise CompleteEventError(f"wrong WRAM size or course at {path}")
    if active and (w[0x0313] != 1 or not is_fully_loaded_course(decoded, w[0x10000:])):
        raise CompleteEventError(f"premature result or wrong decoded course at {path}")
    u = lambda a: int.from_bytes(w[a:a + 2], "little")
    signed = lambda a: int.from_bytes(w[a:a + 2], "little", signed=True)
    return {"menu": w[0x009F], "in_race": w[0x0313],
            "p1_rider": w[0x017D], "p2_rider": w[0x017F],
            "p1_x": u(0x0411), "p1_y": u(0x0415),
            "p2_x": u(0x0413), "p2_y": u(0x0417),
            "p1_vx": signed(0x04B7), "p1_vy": signed(0x04BB),
            "p1_contact": u(0x0E95), "p2_contact": u(0x0E97),
            "p1_checkpoint": u(0x1199), "p1_finish_gate": u(0x119D),
            "p1_laps": u(0x0EF1), "p2_laps": u(0x0EF3),
            "boost": u(0x11CF), "stunt_queue_cursor": u(0x0CE3),
            "clock_raw": [w[a] for a in (0x0E0F, 0x0E13, 0x0E17,
                                           0x0E1B, 0x0E1F)]}


def source_followthrough_states(states: dict[int, dict], result_frame: int) -> dict:
    """Observe the real archived original movie *after* its genuine result.

    Source and fresh replay start from different in-tour histories. Preserve
    their separately observed axes; a source-state match is evidence only.
    An omitted source frame is missingness, never an inferred stable menu.
    """
    if type(result_frame) is not int or result_frame < 0:
        raise CompleteEventError("invalid source-original result frame")
    samples = {}
    for offset in SOURCE_RESULT_FOLLOWTHROUGH_OFFSETS:
        frame = result_frame + offset
        row = states.get(frame)
        if not isinstance(row, dict) or any(
                type(row.get(name)) is not int
                for name in ("track", "menu", "in_race")):
            raise CompleteEventError(
                f"missing original-movie terminal state at frame {frame}")
        samples[str(offset)] = {
            "original_movie_host_frame": frame,
            "track": row["track"],
            "menu": row["menu"],
            "in_race": row["in_race"],
        }
    return samples



def source_zoo_next_bowl(states: dict[int, dict], result_frame: int) -> dict:
    """Ground exactly the next active Bowl event in the 2014 movie."""
    if result_frame != ZOO_SOURCE_RESULT_MOVIE_FRAME:
        raise CompleteEventError("Zoo result is not the independently observed source frame 8353")
    entry = ZOO_SOURCE_NEXT_BOWL_MOVIE_FRAME
    if entry - result_frame != 267:
        raise CompleteEventError("source Zoo-to-Bowl movie distance changed")
    previous = states.get(entry - 1)
    if not isinstance(previous, dict):
        raise CompleteEventError("missing original movie source before next event")
    samples = {}
    for offset in ZOO_NEXT_BOWL_OFFSETS:
        host = result_frame + offset
        state = states.get(host)
        if not isinstance(state, dict) or any(
                type(state.get(k)) is not int for k in ("menu", "track", "in_race")):
            raise CompleteEventError(f"missing original next-Bowl movie state {host}")
        samples[str(offset)] = {
            "original_movie_host_frame": host,
            "menu": state["menu"], "track": state["track"],
            "in_race": state["in_race"],
        }
    if (previous.get("track") == 2 and previous.get("in_race") == 1
            or any(states.get(f, {}).get("track") != 2
                   or states.get(f, {}).get("in_race") != 1
                   for f in range(entry, entry + 8))):
        raise CompleteEventError("source movie does not actually enter a sustained Bowl race at 8620")
    if samples["267"]["track"] != 2 or samples["267"]["in_race"] != 1:
        raise CompleteEventError("source original Bowl active-entry offset not corroborated")
    return {
        "original_result_host_frame": result_frame,
        "original_next_bowl_entry_host_frame": entry,
        "source_result_to_next_active_entry_frames": entry - result_frame,
        "samples": samples,
        "source_original_active_entry_sustained_eight_frames": True,
        "native_next_course_entry_proven": False,
        "release_complete_event_credit": 0,
    }


def observe_zoo_next_bowl_handoff(
        original_dir: Path, native_dir: Path, original_log: str, native_log: str,
        source: dict, reference_entry: int, native_entry: int,
        reference_result_relative: int, native_result_relative: int) -> dict:
    """Triplet-compare the *actual* movie's next Bowl entry, no input rebase.

    Sparse handoff samples include consecutive +263..+269, so a transition
    between adjacent guest frames can be attributed without assuming the
    first active frame from a lone screenshot. This is still not the whole
    45-event progression or a release acceptance oracle.
    """
    if (source.get("original_next_bowl_entry_host_frame") !=
            ZOO_SOURCE_NEXT_BOWL_MOVIE_FRAME
            or source.get("source_result_to_next_active_entry_frames") != 267
            or not source.get("source_original_active_entry_sustained_eight_frames")
            or set(source.get("samples", {})) !=
            {str(n) for n in ZOO_NEXT_BOWL_OFFSETS}):
        raise CompleteEventError("missing bounded authentic source Bowl-next entry")
    samples = []
    for offset in ZOO_NEXT_BOWL_OFFSETS:
        original = source["samples"][str(offset)]
        if original.get("original_movie_host_frame") != 8353 + offset:
            raise CompleteEventError("contradictory original movie handoff frame")
        row = {"offset_from_observed_zoo_result": offset,
               "original_movie": original, "fresh_guests": {}}
        paired_wram = {}
        for key, directory, log, entry, onset in (
                ("original", original_dir, original_log, reference_entry, reference_result_relative),
                ("native", native_dir, native_log, native_entry, native_result_relative)):
            tag = f"zoo-next-bowl-{offset:03d}"
            expected = entry + onset + offset
            observed = observed_dump_frame(log, tag)
            if observed != expected:
                raise CompleteEventError(
                    f"guest handoff {key} +{offset} frame {observed} != {expected}")
            raw_path = directory / f"{tag}.wram.bin"
            if not raw_path.is_file():
                raise CompleteEventError(f"missing actual guest next-entry memory {raw_path}")
            raw = raw_path.read_bytes()
            if len(raw) != 0x20000:
                raise CompleteEventError(f"truncated real guest next-entry WRAM {raw_path}")
            paired_wram[key] = raw
            rec = decode_qa01_crawler_battery_sram(
                directory / f"{tag}.sram.bin", 1)
            values = {"menu": raw[0x009F], "track": raw[0x00CE],
                      "in_race": raw[0x0313]}
            row["fresh_guests"][key] = {
                **values, "actual_host_frame": observed,
                "full_wram_bytes": len(raw),
                "wram_sha256": hashlib.sha256(raw).hexdigest(),
                "source_earned_zoo_best_lap": rec["crawler_record_three_ranks"][0],
                "record_checksum_stored": rec["record_table_checksum_stored"],
                "record_checksum_calculated": rec["record_table_checksum_calculated"],
                "record_checksum_matches": rec["record_table_checksum_matches_at_sample"],
                "sram_sha256": rec["sram_sha256"],
            }
        row["original_native_full_wram_byte_difference"] = (
            audit_qa01_wram_pair(paired_wram["original"], paired_wram["native"]))
        source_named = {k: original[k] for k in ("menu", "track", "in_race")}
        row["triplet_named_states_equal"] = all(
            {k: row["fresh_guests"][side][k] for k in source_named} == source_named
            for side in ("original", "native"))
        pair_sram = [
            (directory / f"zoo-next-bowl-{offset:03d}.sram.bin").read_bytes()
            for directory in (original_dir, native_dir)]
        diff = [i for i, (o, n) in enumerate(zip(*pair_sram)) if o != n]
        row["original_native_full_sram_equal"] = not diff
        row["battery_sram_differing_byte_count"] = len(diff)
        row["battery_first_differences"] = [
            {"offset": i, "original_byte": pair_sram[0][i],
             "native_byte": pair_sram[1][i]} for i in diff[:8]]
        samples.append(row)

    def next_entry_from_samples(side: str) -> dict:
        last = None
        first_active = None
        for row in samples:
            now = row["offset_from_observed_zoo_result"]
            fields = (row["original_movie"] if side == "movie"
                      else row["fresh_guests"][side])
            active = fields["track"] == 2 and fields["in_race"] == 1
            if active and first_active is None:
                first_active = now
                exact = now if last is not None and last[0] == now - 1 and not last[1] else None
                return {"last_observed_inactive_offset":
                        last[0] if last is not None and not last[1] else None,
                        "first_observed_active_offset": first_active,
                        "exact_observed_entry_offset": exact}
            last = (now, active)
        return {"last_observed_inactive_offset":
                last[0] if last is not None and not last[1] else None,
                "first_observed_active_offset": None,
                "exact_observed_entry_offset": None}

    original_bracket = next_entry_from_samples("movie")
    ref_bracket = next_entry_from_samples("original")
    native_bracket = next_entry_from_samples("native")
    original_start = original_bracket["exact_observed_entry_offset"]
    ref_start = ref_bracket["exact_observed_entry_offset"]
    native_start = native_bracket["exact_observed_entry_offset"]
    if original_start != 267:
        raise CompleteEventError("sparse original source does not prove exact 8620 entry")
    ref_absolute = (reference_entry + reference_result_relative + ref_start
                    if ref_start is not None else None)
    native_absolute = (native_entry + native_result_relative + native_start
                       if native_start is not None else None)
    return {
        "schema": "UR-QA01-ZOO-TO-AUTHENTIC-BOWL-NEXT-RACE/1",
        "reference_next_bowl_absolute_host_frame": ref_absolute,
        "native_next_bowl_absolute_host_frame": native_absolute,
        "next_bowl_same_absolute_host_frame": (
            ref_absolute is not None and native_absolute is not None
            and ref_absolute == native_absolute),
        "original_source_movie_result_host_frame": 8353,
        "original_source_movie_next_bowl_active_host_frame": 8620,
        "clock_axes": "2014 reset movie, fresh Snes9x guest, fresh Baldosa guest all independent",
        "source_controller_masks_modified": False,
        "sample_count": len(samples),
        "sample_offsets": list(ZOO_NEXT_BOWL_OFFSETS),
        "source_next_bowl_active_entry_offset": original_start,
        "fresh_reference_next_bowl_entry_offset": ref_start,
        "fresh_native_next_bowl_entry_offset": native_start,
        "original_source_entry_bracket": original_bracket,
        "fresh_reference_entry_bracket": ref_bracket,
        "fresh_native_entry_bracket": native_bracket,
        "all_triplet_named_states_equal": all(x["triplet_named_states_equal"] for x in samples),
        "all_original_native_full_sram_pairs_equal": all(
            x["original_native_full_sram_equal"] for x in samples),
        "all_original_native_full_wram_pairs_equal": all(
            x["original_native_full_wram_byte_difference"]["byte_exact"]
            for x in samples),
        "next_bowl_entry_triple_equal": (ref_start == native_start == original_start),
        "zoo_rank0_2510_and_checksum_preserved_every_sample": all(
            x["fresh_guests"][side]["source_earned_zoo_best_lap"] ==
            {"rank": 0, "value_word": 2510, "holder_index": 0}
            and x["fresh_guests"][side]["record_checksum_matches"]
            for x in samples for side in ("original", "native")),
        "samples": samples,
        "full_event_guest_logic_tick_equivalence_proven": False,
        "shipping_windows_candidate_proven": False,
        "cold_process_disk_persistence_proven": False,
        "release_complete_event_credit": 0,
    }


def decode_qa01_crawler_battery_sram(path: Path, course_track: int) -> dict:
    """A *live* 8KiB battery image, not OS durability or an award receipt.

    Track Records are the original USA table at 0x0422, rank stride 50,
    Crawler tour row 0, and original racer holder bytes at 0x0550.
    Keep all three ranks and the computed/stored checksum even mid-update.
    This routine cannot repair, synthesize or write save bytes.
    """
    if type(course_track) is not int or course_track not in range(5):
        raise CompleteEventError("unsupported Crawler SRAM record course index")
    if not path.is_file() or path.stat().st_size != 8192:
        raise CompleteEventError("original/native post-result SRAM must be 8KiB")
    raw = path.read_bytes()
    if len(raw) != 8192:
        raise CompleteEventError("truncated original/native post-result SRAM")
    word = lambda at: int.from_bytes(raw[at:at + 2], "little")
    records = []
    for rank in range(3):
        index = rank * 50 + course_track
        records.append({
            "rank": rank,
            "value_word": word(0x0422 + 2 * index),
            "holder_index": raw[0x0550 + index],
        })
    checksum_calculated = sum(
        word(0x0422 + 2 * index) for index in range(150)) & 0xFFFF
    checksum_stored = word(0x054E)
    return {
        "full_sram_bytes": len(raw),
        "sram_sha256": hashlib.sha256(raw).hexdigest(),
        "crawler_course_track_index": course_track,
        "crawler_record_three_ranks": records,
        "record_table_checksum_stored": checksum_stored,
        "record_table_checksum_calculated": checksum_calculated,
        "record_table_checksum_matches_at_sample": (
            checksum_stored == checksum_calculated),
        "in_memory_snapshot_only": True,
        "cold_process_reload_proven": False,
    }


def observe_source_terminal_followthrough(
        original_dir: Path, native_dir: Path,
        original_log: str, native_log: str,
        source_samples: dict, original_entry: int, native_entry: int,
        original_result_relative: int, native_result_relative: int,
        crawler_course_track: int) -> dict:
    """Compare distinct archived-source, fresh-reference and native axes.

    Read genuine full WRAM after each guest's independently observed result.
    Do not conflate same-result-relative with same-race-relative frames, and
    do not alter the primary strict paired-event candidate verdict.
    """
    if set(source_samples) != {str(n) for n in SOURCE_RESULT_FOLLOWTHROUGH_OFFSETS}:
        raise CompleteEventError("incomplete source-original follow-through")
    reference_result_host = observed_dump_frame(original_log, "result-onset")
    native_result_host = observed_dump_frame(native_log, "result-onset")
    if (reference_result_host != original_entry + original_result_relative
            or native_result_host != native_entry + native_result_relative):
        raise CompleteEventError("follow-through original/native result clock contradiction")
    rows = []
    for offset in SOURCE_RESULT_FOLLOWTHROUGH_OFFSETS:
        key = str(offset)
        tag = f"original-follow-{offset:02d}"
        frames = {
            "original": observed_dump_frame(original_log, tag),
            "native": observed_dump_frame(native_log, tag),
        }
        if (frames["original"] != reference_result_host + offset
                or frames["native"] != native_result_host + offset):
            raise CompleteEventError(f"follow-through result-relative frame mismatch at +{offset}")
        guests = {}
        sram = {}
        paired_wram = {}
        for label, directory in (("original", original_dir), ("native", native_dir)):
            path = directory / f"{tag}.wram.bin"
            if not path.is_file():
                raise CompleteEventError(f"missing original/native follow-through {label} WRAM")
            raw = path.read_bytes()
            if len(raw) != 0x20000:
                raise CompleteEventError("follow-through WRAM must be full 128 KiB")
            paired_wram[label] = raw
            word = lambda adr: int.from_bytes(raw[adr:adr+2], "little")
            sram[label] = decode_qa01_crawler_battery_sram(
                directory / f"{tag}.sram.bin", crawler_course_track)
            guests[label] = {
                "menu": raw[0x009F], "track": raw[0x00CE],
                "in_race": raw[0x0313],
                "p1_laps": word(0x0EF1), "p2_laps": word(0x0EF3),
                "p1_checkpoint": word(0x1199),
                "p1_finish_gate": word(0x119D),
                "wram_sha256": hashlib.sha256(raw).hexdigest(),
                "full_wram_bytes": len(raw),
            }
        source = source_samples[key]
        expected = {
            name: source[name] for name in ("menu", "track", "in_race")}
        by_engine = {
            label: {
                "source_named_state_equal": all(
                    row[name] == expected[name] for name in expected),
                "named_fields_different_from_source": [
                    name for name in expected if row[name] != expected[name]],
            } for label, row in guests.items()
        }
        rows.append({
            "offset_from_each_observed_result_onset": offset,
            "source_original_movie": source,
            "independently_observed_replay_host_frames": frames,
            "fresh_guests": guests,
            "fresh_guest_battery_sram": sram,
            "sram_full_bytes_equal": (
                sram["original"]["sram_sha256"] == sram["native"]["sram_sha256"]),
            "sram_course_three_rank_records_equal": (
                sram["original"]["crawler_record_three_ranks"] ==
                sram["native"]["crawler_record_three_ranks"]),
            "source_named_state_comparison": by_engine,
            "paired_named_state_equal": all(
                guests["original"][name] == guests["native"][name]
                for name in ("menu", "track", "in_race", "p1_laps",
                             "p2_laps", "p1_checkpoint", "p1_finish_gate")),
            "full_wram_bytes_equal": (
                guests["original"]["wram_sha256"] ==
                guests["native"]["wram_sha256"]),
            "full_wram_byte_difference": audit_qa01_wram_pair(
                paired_wram["original"], paired_wram["native"]),
        })
    return {
        "schema": "UR-QA01-SOURCE-ORIGINAL-NATIVE-RESULT-FOLLOWTHROUGH/2",
        "input_origin": "unchanged archived 2014 movie, opt-in relative window extends 80 frames beyond original result",
        "source_guest_relative_result_onset_equivalence_proven": False,
        "sample_alignment": "offsets from each guest's own observed result, not identical race-relative frames",
        "original_and_native_result_phase_equal_proven": (
            original_result_relative == native_result_relative),
        "sample_count": len(rows),
        "all_followthrough_named_pairs_equal": all(
            r["paired_named_state_equal"] for r in rows),
        "all_followthrough_full_wram_pairs_equal": all(
            r["full_wram_bytes_equal"] for r in rows),
        "all_followthrough_full_sram_pairs_equal": all(
            r["sram_full_bytes_equal"] for r in rows),
        "all_followthrough_crawler_record_pairs_equal": all(
            r["sram_course_three_rank_records_equal"] for r in rows),
        "battery_sram_snapshot_bytes_per_guest": 8192,
        "battery_sram_cold_process_persistence_proven": False,
        "post_result_sram_persistence_proven": False,
        "menu_restoration_or_final_progression_proven": False,
        "strict_event_comparator_unchanged": True,
        "release_complete_usa_event_credit": 0,
        "samples": rows,
    }


def load_switcher_transition_state(path: Path, decoded: bytes) -> dict:
    """Diagnostic transitional guest state; never treat as active-course proof.

    Original Switcher Race B writes temporary 7E:00CE=0 before restoring
    track 3 near the result. Do not discard that evidence by forcing the
    normal active-course ID/decoded payload contract on these captures.
    Every frame still needs a full real 128-KiB guest dump.
    """
    if not path.is_file():
        raise CompleteEventError(f"missing Switcher terminal guest frame {path}")
    w = path.read_bytes()
    if len(w) != 0x20000:
        raise CompleteEventError("invalid complete Switcher terminal WRAM")
    track = w[0x00CE]
    if track not in (0, 3):
        raise CompleteEventError("foreign course during Switcher terminal phase")
    return {**load_state(path, decoded, track, False),
            "observed_course_track": track,
            "source_terminal_phase_diagnostic_only": True}


def load_capture(directory: Path, frames: list[int], decoded: bytes,
                 track: int, stunt: bool,
                 switcher_terminal_from: int | None = None) -> dict:
    rows = []
    for f in frames:
        tag = "race-entered" if f == 0 else f"scene-{f:05d}"
        path = directory / f"{tag}.wram.bin"
        if switcher_terminal_from is not None and f >= switcher_terminal_from:
            if track != 3 or stunt:
                raise CompleteEventError("terminal phase exception is Switcher-only")
            state = load_switcher_transition_state(path, decoded)
        else:
            state = load_state(path, decoded, track, True)
        rows.append({"relative_frame": f, **state})
    final = load_state(directory / "result-stable.wram.bin", decoded, track, False)
    onset = load_state(directory / "result-onset.wram.bin", decoded, track, False)
    # Screen text is decoded from ORIGINAL PPU memory (also emitted by native
    # guest dumps), so it includes the actual finish time/lap and stunt score.
    screens = {
        "final": textdecode.screen_texts(visual.Dump(directory, "result-stable")),
        "onset": textdecode.screen_texts(visual.Dump(directory, "result-onset")),
    }
    if stunt:
        tally = load_state(directory / "result-tally.wram.bin", decoded, track, False)
        if tally["menu"] != 0x2F:
            raise CompleteEventError("not a real stunt tally screen")
        screens["tally"] = textdecode.screen_texts(visual.Dump(directory, "result-tally"))
    return {"samples": rows, "result": final, "onset": onset,
            "result_text": screens}


ENTRY_SIGNATURE = ("p1_rider", "p2_rider", "p1_x", "p1_y",
                   "p2_x", "p2_y", "p1_laps", "p2_laps",
                   "p1_checkpoint", "p1_finish_gate", "clock_raw")


def entry_diagnostics(source: dict, original: dict, native: dict) -> dict:
    """Screen/clock/lap prerequisites before attributing a replay mismatch
    to physics. Source was played *after earlier tour events*, while the
    newly calibrated guests start from the original embedded SRAM."""
    snapshots = {"source_original": source, "fresh_reference": original,
                 "fresh_native": native}
    absent = [(name, field) for name, row in snapshots.items()
              for field in ENTRY_SIGNATURE if field not in row]
    if absent:
        raise CompleteEventError(f"incomplete source/current guest start signature: {absent}")
    discrepancies = {}
    for name, row in list(snapshots.items())[1:]:
        fields = [field for field in ENTRY_SIGNATURE if row[field] != source[field]]
        discrepancies[name] = {
            "fields": fields,
            "source": {k: source[k] for k in fields},
            "guest": {k: row[k] for k in fields},
        }
    return {"source_original_state_equivalent": all(
                not item["fields"] for item in discrepancies.values()),
            # The archive supplies a proven-effective input route, NOT
            # necessarily the same in-tour history as either fresh guest.
            # Source differences are diagnostic; a successful independent
            # fresh reference/native pair can still be accepted.
            "fresh_reference_native_equivalent": all(
                original[field] == native[field] for field in ENTRY_SIGNATURE),
            "discrepancies": discrepancies,
            "limit": ("A mismatch may reflect earlier original in-tour state, "
                      "controller latch/sample phase, or an authentic guest defect. "
                      "Do not infer the last cause without a controlled witness.")}


def archived_p1_positive_result(lines: list[str], stunt: bool) -> bool:
    """This one archived original movie races MIKE (P1). An opponent's score
    or clock cannot satisfy MIKE's achievement on a no-time result.
    Expand this identity oracle before admitting any *other* input source."""
    pattern = r":\s*[1-9]\d*" if stunt else r"\d+:[0-5]\d\.\d\d"
    for i, text in enumerate(lines):
        if text.strip() == "MIKE":
            # The source PPU decoder emits one token per row. On known
            # original result screens MIKE's actual total/score is the
            # immediately following token; scanning beyond it can consume
            # an opponent's time or the unrelated qualifying threshold.
            # Require the anchored source layout, never nearby numerals.
            if i + 1 >= len(lines):
                return False
            value = lines[i + 1].strip()
            if not re.fullmatch(pattern, value):
                return False
            # A syntactically valid 0:00.00 is still not a completed
            # timed race. Prevent a zero-valued placeholder from being
            # promoted solely because the PPU result has the right shape.
            return stunt or any(c in "123456789" for c in value)
    return False


def diagnose(original: dict, native: dict, result_menu: int, stunt: bool) -> dict:
    r_rows, n_rows = original["samples"], native["samples"]
    if [r["relative_frame"] for r in r_rows] != [r["relative_frame"] for r in n_rows]:
        raise CompleteEventError("different original/native sampling windows")
    first = None
    for r, n in zip(r_rows, n_rows):
        differences = sorted(k for k in r if r[k] != n[k])
        if differences:
            first = {"relative_frame": r["relative_frame"], "fields": differences,
                     "reference": {k: r[k] for k in differences},
                     "native": {k: n[k] for k in differences}}
            break
    complete = all(x["result"]["menu"] == result_menu and
                   x["onset"]["menu"] == result_menu
                   for x in (original, native))
    # The settled score/time string is the gameplay oracle. Temporary
    # tally-animation lettering and onset PPU glyph timing belong to a
    # separate presentation gate and remain useful diagnostics only.
    texts_match = (original["result_text"]["final"] ==
                   native["result_text"]["final"])
    intermediate_text_match = original["result_text"] == native["result_text"]
    # This anchored SMV has MIKE in P1. A CPU score or a timed-out P1
    # cannot masquerade as the player's own successful original result.
    p1_positive = archived_p1_positive_result(original["result_text"]["final"],
                                               stunt)
    scored = not stunt or p1_positive
    timed_finish = stunt or p1_positive
    ref_laps = [row.get("p1_laps") for row in r_rows]
    nat_laps = [row.get("p1_laps") for row in n_rows]
    # An explicitly sampled >=2 lap sequence is required for multi-lap
    # Circuit candidate qualification; no assertion about unobserved
    # intervening events between those sample frames.
    def laps_drop(values):
        return sum(type(a) is int and type(b) is int and b < a
                   for a, b in zip(values, values[1:]))
    lap_evidence = result_menu != 0xBC or (
        laps_drop(ref_laps) >= 2 and laps_drop(nat_laps) >= 2
    )
    # $0313 is reused after races (original Zoo result = 0x3D,
    # scored Bowl = 0x3C). A copied menu byte or rendered text during
    # active play is not an acknowledged terminal guest state.
    terminal_guest_state = all(
        type(capture[phase].get("in_race")) is int
        and capture[phase]["in_race"] != 1
        for capture in (original, native)
        for phase in ("onset", "result")
    )
    # Circuit progression samples alone do not prove the final lap was
    # credited. Original/native Zoo results have P1 remaining laps == 0
    # at BOTH onset and stable result. Keep this gate Circuit-specific:
    # Race and 45s Stunt have different counter semantics.
    circuit_terminal_laps_zero = result_menu != 0xBC or all(
        type(capture[phase].get("p1_laps")) is int
        and capture[phase]["p1_laps"] == 0
        for capture in (original, native)
        for phase in ("onset", "result")
    )
    return {"first_sample_disagreement": first,
            "both_reached_terminal_menu": complete,
            "rendered_result_and_score_text_matched": texts_match,
            "intermediate_result_text_matched": intermediate_text_match,
            "stunt_positive_score_visible": scored,
            "timed_race_or_circuit_result_visible": timed_finish,
            "circuit_multiple_lap_decrements_sampled": lap_evidence,
            "result_outside_active_race_in_both_guests": terminal_guest_state,
            "circuit_zero_remaining_laps_at_onset_and_stable": circuit_terminal_laps_zero,
            "paired_event_candidate": bool(
                complete and texts_match and scored and timed_finish
                and lap_evidence and terminal_guest_state
                and circuit_terminal_laps_zero and first is None),
            "qualification": "candidate only; source/original and native complete-event evidence still requires independent review"}


def attest_original_source_horizon(log: str, requested: int,
                                   captured_wram: Path) -> dict:
    """Prove the original reference guest reached the requested host boundary.

    The changed-byte WRAM trace may end many frames earlier if the guest
    wrote nothing observable. A successful process exit or nonempty trace
    therefore does NOT attest the final scanned movie frame. Require a
    unique source-owned script dump at the requested host frame and a
    complete original 128-KiB WRAM capture (never retained as a fixture).
    """
    if type(requested) is not int or requested <= 0:
        raise CompleteEventError("invalid requested original source horizon")
    observed = observed_dump_frame(log, "source-horizon")
    if observed != requested:
        raise CompleteEventError(
            f"original source horizon not reached: requested {requested}, observed {observed}")
    if not captured_wram.is_file() or captured_wram.stat().st_size != 0x20000:
        raise CompleteEventError(
            "missing or invalid original source horizon WRAM capture")
    return {"original_source_horizon_host_frame": observed,
            "original_source_horizon_wram_bytes": 0x20000,
            "original_source_horizon_observed_from_guest_dump": True}


def scan_source(args, work: Path, sram: Path, source_input: Path,
                decoded: bytes) -> dict:
    scan = work / "source"
    scan.mkdir(parents=True)
    (scan / "scan.script").write_text(
        bowl_source_memory.source_movie_scan_script(args.source_horizon)
        if args.bowl_source_movie_memory
        else f"wait {args.source_horizon}\ndump source-horizon\nquit\n")
    env = dict(os.environ, SNESREF_HEADLESS="1", SNESREF_FAST="1",
               SNESREF_WRAM_FILL="0", SNESREF_SRAM_IN=str(sram),
               SNESREF_SCRIPT=str(scan / "scan.script"),
               SNESREF_INPUT_FILE=str(source_input),
               SNESREF_TRACE_FILE=str(scan / "trace.jsonl"),
               SNESREF_DUMP_DIR=str(scan))
    p = subprocess.run([str(args.snesref), str(args.core), str(args.rom)],
                       env=env, cwd=scan, capture_output=True, text=True,
                       timeout=900)
    (scan / "source-scan.log").write_text(p.stdout + p.stderr)
    if p.returncode:
        raise CompleteEventError("source-original replay failed: " + (p.stdout + p.stderr)[-1200:])
    horizon_attestation = attest_original_source_horizon(
        p.stdout + p.stderr, args.source_horizon,
        scan / "source-horizon.wram.bin")
    states = trace.frame_states((scan / "trace.jsonl").read_text().splitlines())
    stream, track, menu, _ = CASES[args.case]
    diagnostic = source_event_diagnostic(states, track, menu)
    diagnostic.update(horizon_attestation)
    (scan / "source-event-diagnostic.json").write_text(
        json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")
    print("ORIGINAL_SOURCE_EVENT_DIAGNOSTIC="
          + json.dumps(diagnostic, sort_keys=True), flush=True)
    event = source_event(states, track, menu)
    if args.source_followthrough:
        event["source_terminal_followthrough"] = source_followthrough_states(
            states, event["original_result_frame"])
    if args.zoo_next_bowl:
        event["source_next_bowl"] = source_zoo_next_bowl(
            states, event["original_result_frame"])
    if args.bowl_next_switcher:
        event["source_next_switcher"] = bowl_handoff.source_next_switcher(
            states, event["original_result_frame"])
    if args.dragster_next_zoo:
        event["source_next_zoo"] = dragster_zoo.source_next_zoo(states, event)
        event["source_next_zoo"]["original_source_trace_sha256"] = sha(scan / "trace.jsonl")
        (scan / "dragster-next-zoo-original.json").write_text(
            json.dumps(event["source_next_zoo"], indent=2) + "\n", encoding="utf-8")
    if args.bowl_source_movie_memory:
        event["source_movie_handoff_state_samples"] = {
            str(offset): states[bowl_source_memory.SOURCE_RESULT + offset]
            for offset in bowl_source_memory.OFFSETS}
    if args.case == "dragster" and (
            event["original_entry_frame"] != 794
            or event["original_result_frame"] != 2874
            or event["source_active_frames_to_result"] != 2080):
        raise CompleteEventError(
            "2014 source Dragster entry/result does not match independently "
            "executed original movie frames 794/2874")
    if args.case == "zoom-zoo" and event["original_entry_frame"] != 3190:
        raise CompleteEventError("2014 Zoom Zoo entry disagrees with pinned original 3190")
    # The first chronological source trace carries only changed low-WRAM
    # bytes. Replay a second time with identical ROM/SRAM/movie to capture
    # the actual 128KiB entry state and loaded course. This is a distinct
    # original-source baseline, not a native savestate transplant.
    anchor = scan / "original-anchor.script"
    anchor.write_text(
        f'wait {event["original_entry_frame"]}\ndump source-race-entered\nquit\n')
    anchor_env = dict(env, SNESREF_SCRIPT=str(anchor))
    anchor_env.pop("SNESREF_TRACE_FILE", None)
    rerun = subprocess.run([str(args.snesref), str(args.core), str(args.rom)],
                           env=anchor_env, cwd=scan, capture_output=True,
                           text=True, timeout=900)
    (scan / "source-entry.log").write_text(rerun.stdout + rerun.stderr)
    if rerun.returncode:
        raise CompleteEventError("original entry capture failed: " + (
            rerun.stdout + rerun.stderr)[-1200:])
    event["original_source_entry"] = load_state(
        scan / "source-race-entered.wram.bin", decoded, track, True)
    return event


def run_pinned_baldosa(work: Path, args, script: Path,
                       events: list[tuple[int, int, int]], shift: int) -> str:
    """QA-only pinned Baldosa host transport; never alter source controller masks.

    Uses the same ephemeral UR_QA_SCENE_INPUT_FILE shim already used by the
    successful Zoo original/native transplant, not the old host-only
    SNESRECOMP_INPUT_FILE env knob from the legacy execution path.
    """
    input_file = work / "pinned-baldosa.input"
    lines = [
        f"{start + shift}:{duration}:{mask:03x}"
        for start, duration, mask in events if mask
    ]
    if any(start + shift < 0 or duration < 1 or
           not 0 < mask <= 0x0FFF for start, duration, mask in events if mask):
        raise CompleteEventError("invalid bounded source controller stream")
    if lines:
        input_file.write_text("\n".join(lines) + "\n", encoding="ascii")
    output = work / "native"
    output.mkdir(exist_ok=True)
    config = args.native.parent / "config.ini"
    if not config.is_file():
        config.write_text("[Sound]\nEnableAudio = 0\n", encoding="utf-8")
    # The explicit --config argument skips the desktop host's default
    # snesrecomp_anchor_to_exe_dir() path. RtlReadSram() then reads
    # RtlSaveRoot()/save.srm, default 'saves/save.srm', relative to cwd=work.
    # Seeding args.native.parent/saves while executing from work meant the
    # guest NEVER read the archived movie SRAM. This path is a source-identity
    # precondition, not an optional cold-reload convenience.
    save_root = work / "saves"
    backup = save_root.with_name("saves.qa01-bowl-recovery")
    if backup.exists():
        raise CompleteEventError(f"prior native SRAM backup not cleared: {backup}")
    if save_root.exists():
        save_root.rename(backup)
    try:
        save_root.mkdir()
        shutil.copyfile(args.sram, save_root / "save.srm")
        env = dict(
            os.environ,
            SDL_AUDIODRIVER="dummy",
            SNESRECOMP_FRAMEDUMP_PIXELS="0",
            SNESRECOMP_DUMP_DIR=str(output),
            SNESRECOMP_ROM=str(args.rom),
        )
        if lines:
            env["UR_QA_SCENE_INPUT_FILE"] = str(input_file)
        else:
            env.pop("UR_QA_SCENE_INPUT_FILE", None)
        # QA-01 optional native WRAM-read observer: isolate calibration and
        # genuine replay processes so a calibration trace cannot impersonate
        # a terminal-result reader. Never enable for generic event probes.
        if os.environ.get("UR_QA_NATIVE_STACK_READ_ENABLE") == "1" and script.name == "complete.script":
            read_path = output / "qa01-native-01dd-reads.log"
            read_path.touch()
            env["UR_QA_NATIVE_STACK_READ_PATH"] = str(read_path)
            interp_path = output / "qa01-native-interpreter-pla.log"
            interp_path.touch()
            env["UR_QA_NATIVE_INTERP_PLA_PATH"] = str(interp_path)
        else:
            env.pop("UR_QA_NATIVE_STACK_READ_PATH", None)
            env.pop("UR_QA_NATIVE_INTERP_PLA_PATH", None)
        proc = subprocess.run(
            ["xvfb-run", "-a", str(args.native),
             "--no-launcher", "--config", str(config),
             "--script", str(script), str(args.rom)],
            cwd=work, env=env, capture_output=True, text=True, timeout=900,
        )
        return proc.stdout + proc.stderr
    finally:
        shutil.rmtree(save_root, ignore_errors=True)
        if backup.exists():
            backup.rename(save_root)


def replay_native(work: Path, args, script: Path,
                  events: list[tuple[int, int, int]], shift: int) -> str:
    if args.native_backend == "pinned-baldosa":
        return run_pinned_baldosa(work, args, script, events, shift)
    return engine.run_native(work, args, script, events, shift)


def bounded_stunt_result_phase_witness(comparison: dict,
                                       source_event: dict) -> bool:
    """A narrow diagnostic success, NEVER a complete-event parity pass.

    Check every other independent original/native score and active-route gate,
    retain the *unmatched* terminal onset, and accept only the observed
    exactly-one-frame native lead as an *investigative result*. This allows CI
    to distinguish a proven repeatable phase lead from an unexecuted or
    genuinely divergent scored Stunt, without touching game/host/input time.
    """
    frames = comparison.get("terminal_result_guest_frame", {})
    return bool(
        source_event.get("source_stunt_tally_frame") is not None
        and source_event.get("original_result_frame", 0) >
            source_event["source_stunt_tally_frame"]
        and comparison.get("first_sample_disagreement") is None
        and comparison.get("both_reached_terminal_menu") is True
        and comparison.get("result_outside_active_race_in_both_guests") is True
        and comparison.get("rendered_result_and_score_text_matched") is True
        and comparison.get("intermediate_result_text_matched") is True
        and comparison.get("stunt_positive_score_visible") is True
        and comparison.get("timed_race_or_circuit_result_visible") is True
        and comparison.get("original_source_entry_equivalent") is True
        and comparison.get("fresh_guest_entry_equivalent") is True
        and comparison.get("terminal_result_frame_matched") is False
        and type(frames.get("reference_relative")) is int
        and type(frames.get("native_relative")) is int
        and frames["native_relative"] + 1 == frames["reference_relative"]
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", choices=tuple(CASES), required=True)
    ap.add_argument("--native-backend", choices=("legacy", "pinned-baldosa"), default="legacy")
    ap.add_argument("--switcher-same-host-penultimate", action="store_true",
                    help="optional read-only original +4703 / native +4701 same-host 5782 guest observation; no admission")
    ap.add_argument("--switcher-same-host-full-memory-offsets", action="store_true",
                    help="read-only original/native same-host 5782 WRAM/VRAM/CGRAM difference offsets; requires penultimate witness")
    ap.add_argument("--bowl-tally-phase", action="store_true",
                    help="retain 8 exact-host-frame WRAM/VRAM/CGRAM captures after real 0x2F Bowl tally")
    ap.add_argument("--zoo-race-mesh", action="store_true",
                    help="opt-in unmasked 128KiB original/native full-Circuit checkpoints through Zoo +5120; no event admission")
    ap.add_argument("--zoo-dp-window", action="store_true",
                    help="opt-in 13 contiguous +5034..+5046 original/native DP/whole-WRAM frames; requires --zoo-race-mesh; no admission")
    ap.add_argument("--zoo-terminal-phase", action="store_true",
                    help="opt-in Zoo +5156..+5173 fixed-frame/host phase comparison; no admission")
    ap.add_argument("--source-followthrough", action="store_true",
                    help="opt-in archived original/native +8/+16/+24/+32 postresult guest WRAM; no admission")
    ap.add_argument("--zoo-next-bowl", action="store_true",
                    help="opt-in unchanged 2014 Zoo original input through source Bowl active race at movie frame 8620")
    ap.add_argument("--bowl-next-switcher", action="store_true",
                    help="opt-in unchanged 2014 Bowl input through next Switcher at movie frame 12327; no acceptance")
    ap.add_argument("--bowl-source-movie-memory", action="store_true",
                    help="opt-in original 2014 Bowl movie full raw WRAM/SRAM vs fresh guests around Switcher, no acceptance")
    ap.add_argument("--dragster-next-zoo", action="store_true",
                    help="opt-in authentic 2014 Dragster Race A result into following Zoom Zoo Circuit A, no event credit")
    ap.add_argument("--observe-one-frame-stunt-lead", action="store_true",
                    help="report a verified narrow Stunt phase gap as diagnostic CI success; never admit a course")
    ap.add_argument("--snesref", type=Path, required=True)
    ap.add_argument("--core", type=Path, required=True)
    ap.add_argument("--native", type=Path, required=True)
    ap.add_argument("--rom", type=Path, default=ROOT / "reference/roms/retail/Uniracers_USA.sfc")
    ap.add_argument("--movie", type=Path, default=movie.ARCHIVE)
    ap.add_argument("--movie-meta", type=Path, default=movie.METADATA)
    ap.add_argument("--source-horizon", type=int, default=SOURCE_HORIZON)
    ap.add_argument("--work-dir", type=Path, required=True)
    ap.add_argument("--json-out", type=Path, required=True)
    args = ap.parse_args(argv)
    for name in ("snesref", "core", "native", "rom", "movie", "movie_meta",
                 "work_dir", "json_out"):
        setattr(args, name, getattr(args, name).resolve())
    if sha(args.rom) != entry.USA_ROM_SHA256:
        ap.error("only canonical USA retail ROM is admitted")
    if args.switcher_same_host_full_memory_offsets and not args.switcher_same_host_penultimate:
        ap.error("Switcher full-memory offsets require --switcher-same-host-penultimate")
    if args.zoo_race_mesh and (args.case != "zoom-zoo"
                               or args.native_backend != "pinned-baldosa"):
        ap.error("Zoo race mesh requires actual pinned Baldosa/original 2014 Zoom Zoo")
    if args.zoo_dp_window and not args.zoo_race_mesh:
        ap.error("Zoo late-DP window requires --zoo-race-mesh")
    if args.zoo_next_bowl and (args.case != "zoom-zoo"
                               or not args.source_followthrough
                               or args.native_backend != "pinned-baldosa"):
        ap.error("Next Bowl entry requires pinned original/native Zoom Zoo source followthrough")
    if args.bowl_next_switcher and (args.case != "bowl"
                                    or not args.source_followthrough
                                    or args.native_backend != "pinned-baldosa"):
        ap.error("Bowl next Switcher requires pinned original/native Bowl source followthrough")
    if args.bowl_source_movie_memory and (args.case != "bowl"
                                         or not args.bowl_next_switcher
                                         or args.native_backend != "pinned-baldosa"):
        ap.error("Bowl source raw memory requires exact 2014 Bowl-to-Switcher pinned guests")
    if args.dragster_next_zoo and (args.case != "dragster"
                                  or not args.source_followthrough
                                  or args.native_backend != "pinned-baldosa"):
        ap.error("Dragster→Zoo source requires exact original/native Race A followthrough")
    if args.source_horizon < 12500 or args.source_horizon > 24000:
        ap.error("source horizon must be 12500..24000")
    streams = list(rnc.find_streams(args.rom.read_bytes()))
    if len(streams) != 45:
        ap.error("requires exactly 45 original ROM course streams")
    stream, track, menu, kind = CASES[args.case]
    decoded = unpack_method1(streams[stream - 1][1])
    args.work_dir.mkdir(parents=True, exist_ok=True)
    work = args.work_dir / args.case
    if work.exists():
        raise CompleteEventError("nonempty prior event workspace; use a fresh path")
    work.mkdir()
    # Reuse original reset-movie SRAM rather than the unrelated all-silver fixture.
    source_input, sram = work / "movie.input", work / "anchored.srm"
    subprocess.run([sys.executable, str(ROOT / "tools/extract_smv_input.py"),
                    str(args.movie), "--input-out", str(source_input),
                    "--sram-out", str(sram), "--sram-size", "8192",
                    "--json-out", str(work / "original-movie-meta.json")], check=True)
    original_event = scan_source(args, work, sram, source_input, decoded)
    original_bytes, _ = movie.read_movie(args.movie)
    pinned_meta = json.loads(args.movie_meta.read_text())
    source_length = original_event["source_active_frames_to_result"] + (
        max(dragster_zoo.OFFSETS) + 6 if args.dragster_next_zoo
        else max(bowl_handoff.OFFSETS) + 6 if args.bowl_next_switcher
        else max(ZOO_NEXT_BOWL_OFFSETS) + 6 if args.zoo_next_bowl
        else 80 if args.source_followthrough else 40)
    source_window = movie.window(original_bytes, pinned_meta,
                                 original_event["original_entry_frame"], source_length)
    if args.source_followthrough and source_length < (
            original_event["source_active_frames_to_result"]
            + max(SOURCE_RESULT_FOLLOWTHROUGH_OFFSETS)):
        raise CompleteEventError("archived source controller window does not cover follow-through")
    frames = sample_frames(
        args.case, original_event["source_active_frames_to_result"],
        zoo_race_mesh=args.zoo_race_mesh,
        zoo_dp_window=args.zoo_dp_window) 
    # Both calibrations boot afresh with exactly the same original SRAM.
    args.sram = sram
    calibration = work / "calibration"
    calibration.mkdir()
    script = calibration / "entry.script"
    script.write_text(stock_crawler_script(stream) + "quit\n")
    rl = engine.run_reference(calibration, args, script, [])
    (calibration / "reference.log").write_text(rl)
    nl = replay_native(calibration, args, script, [], 0)
    (calibration / "native.log").write_text(nl)
    rf, nf = engine.race_entry_frame(rl), engine.race_entry_frame(nl)
    if rf is None or nf is None:
        raise CompleteEventError("could not calibrate both stock Crawler race entries")
    baseline = entry_diagnostics(
        original_event["original_source_entry"],
        load_state(calibration / "ref" / "race-entered.wram.bin",
                   decoded, track, True),
        load_state(calibration / "native" / "race-entered.wram.bin",
                   decoded, track, True))
    replay = work / "replay"
    replay.mkdir()
    script = replay / "complete.script"
    if args.bowl_tally_phase and args.case != "bowl":
        raise CompleteEventError("Bowl tally phase tracing only applies to verified Bowl source")
    if args.zoo_terminal_phase and args.case != "zoom-zoo":
        raise CompleteEventError("Zoo terminal phase tracing only applies to verified Zoo source")
    script.write_text(replay_script(
        stream, menu, frames, kind == "stunt",
        tally_phase=args.bowl_tally_phase,
        source_followthrough=args.source_followthrough,
        zoo_next_bowl=args.zoo_next_bowl,
        bowl_next_switcher=args.bowl_next_switcher,
        dragster_next_zoo=args.dragster_next_zoo))
    reference_script = script
    if args.switcher_same_host_penultimate:
        if args.case != "switcher" or args.native_backend != "pinned-baldosa":
            raise CompleteEventError("only pinned Baldosa Switcher source permits same-host penultimate diagnostic")
        reference_script = replay / "switcher-reference-penultimate.script"
        reference_script.write_text(switcher_penultimate_reference_script(
            script.read_text(), original_event["source_active_frames_to_result"],
            frames))
    events = [(rf + part["start"], part["duration"], int(part["mask"], 16))
              for part in source_window["relative_input_segments"]]
    rl = engine.run_reference(replay, args, reference_script, events)
    (replay / "reference.log").write_text(rl)
    nl = replay_native(replay, args, script, events, nf - rf)
    (replay / "native.log").write_text(nl)
    if engine.race_entry_frame(rl) != rf or engine.race_entry_frame(nl) != nf:
        raise CompleteEventError("race entry changed after scene-relative transplant")
    if "dump result-stable" not in rl or "dump result-stable" not in nl:
        raise CompleteEventError("one engine failed to reach the stock terminal result")
    switcher_terminal_from = (
        original_event["source_active_frames_to_result"] -
        max(SWITCHER_TERMINAL_SOURCE_LEADS)
        if args.case == "switcher" else None)
    reference = load_capture(replay / "ref", frames, decoded, track,
                             kind == "stunt", switcher_terminal_from)
    native = load_capture(replay / "native", frames, decoded, track,
                          kind == "stunt", switcher_terminal_from)
    comparison = diagnose(reference, native, menu, kind == "stunt")
    comparison["original_source_entry_equivalent"] = baseline[
        "source_original_state_equivalent"]
    comparison["fresh_guest_entry_equivalent"] = baseline[
        "fresh_reference_native_equivalent"]
    comparison["paired_event_candidate"] &= baseline[
        "fresh_reference_native_equivalent"]
    terminal_frames = {
        "reference_relative": observed_dump_frame(rl, "result-onset") - rf,
        "native_relative": observed_dump_frame(nl, "result-onset") - nf,
    }
    comparison["terminal_result_guest_frame"] = terminal_frames
    comparison["terminal_result_frame_matched"] = (
        terminal_frames["reference_relative"] ==
        terminal_frames["native_relative"])
    comparison["paired_event_candidate"] &= comparison[
        "terminal_result_frame_matched"]
    comparison["bounded_stunt_one_frame_phase_observed"] = bool(
        args.case == "bowl" and bounded_stunt_result_phase_witness(
            comparison, original_event))
    # A one-frame phase discrepancy is still a *failed complete-event
    # parity gate*. This separate read-only classification lets the CI
    # produce an inspectable positive diagnostic without laundering the
    # observed mismatch into a release-quality pass.
    phase = (observe_bowl_tally_phase(
        replay / "ref", replay / "native", rl, nl)
        if args.bowl_tally_phase else None)
    zoo_phase = (observe_zoo_terminal_phase(
        work, args, stream, original_event["source_active_frames_to_result"],
        events, rf, nf, terminal_frames)
        if args.zoo_terminal_phase else None)
    switcher_same_host = (observe_switcher_same_host_penultimate(
        replay / "ref", replay / "native", rl, nl,
        original_event["source_active_frames_to_result"], rf, nf, decoded)
        if args.switcher_same_host_penultimate else None)
    source_followthrough = (observe_source_terminal_followthrough(
        replay / "ref", replay / "native", rl, nl,
        original_event["source_terminal_followthrough"], rf, nf,
        terminal_frames["reference_relative"], terminal_frames["native_relative"],
        track)
        if args.source_followthrough else None)
    zoo_race_mesh = (observe_zoo_race_mesh(
        replay / "ref", replay / "native", rl, nl, frames, rf, nf,
        original_event["source_active_frames_to_result"],
        zoo_dp_window=args.zoo_dp_window)
        if args.zoo_race_mesh else None)
    next_bowl = (observe_zoo_next_bowl_handoff(
        replay / "ref", replay / "native", rl, nl,
        original_event["source_next_bowl"], rf, nf,
        terminal_frames["reference_relative"], terminal_frames["native_relative"])
        if args.zoo_next_bowl else None)
    next_switcher = (bowl_handoff.observe_next_switcher(
        replay / "ref", replay / "native", rl, nl,
        original_event["source_next_switcher"], rf, nf,
        terminal_frames["reference_relative"], terminal_frames["native_relative"],
        observed_dump_frame=observed_dump_frame,
        decode_sram=decode_qa01_crawler_battery_sram,
        audit_wram=audit_qa01_wram_pair,
        switcher_payload=unpack_method1(streams[3][1]),
        validate_course_payload=is_fully_loaded_course)
        if args.bowl_next_switcher else None)
    source_movie_handoff = (bowl_source_memory.observe_movie_guest_memory(
        work / "source", replay / "ref", replay / "native",
        (work / "source" / "source-scan.log").read_text(), rl, nl,
        {bowl_source_memory.SOURCE_RESULT + int(offset): state
         for offset, state in original_event["source_movie_handoff_state_samples"].items()},
        original_event["source_next_switcher"], rf, nf,
        terminal_frames["reference_relative"], terminal_frames["native_relative"],
        observed_dump_frame=observed_dump_frame,
        decode_sram=decode_qa01_crawler_battery_sram)
        if args.bowl_source_movie_memory else None)
    next_zoo = (dragster_zoo.observe_guest_handoff(
        replay / "ref", replay / "native", rl, nl,
        original_event["source_next_zoo"], rf, nf,
        terminal_frames["reference_relative"], terminal_frames["native_relative"],
        observed_dump_frame=observed_dump_frame,
        audit_wram=audit_qa01_wram_pair,
        validate_course_payload=is_fully_loaded_course,
        zoo_course_payload=unpack_method1(streams[1][1]),
        decode_sram=decode_qa01_crawler_battery_sram)
        if args.dragster_next_zoo else None)
    switcher_same_host_memory = (observe_switcher_same_host_memory_offsets(
        replay / "ref", replay / "native", switcher_same_host)
        if args.switcher_same_host_full_memory_offsets else None)
    report = {
        "schema_version": 1, "admission": "investigative candidate; not a release-ledger pass",
        "course_id": f"course:{stream:02d}", "name": args.case, "family": kind,
        "rom_sha256": sha(args.rom), "original_movie_sha256": sha(args.movie),
        "source_sram_sha256": sha(sram), "native_executable_sha256": sha(args.native),
        "reference_core_sha256": sha(args.core), "input_sha256": sha(script),
        "original_source_event": original_event,
        "original_source_vs_fresh_entry": baseline,
        "original_movie_window_sha256": source_window["raw_controller_window_sha256"],
        "reference_entry": rf, "native_entry": nf, "native_frame_shift": nf-rf, "native_backend": args.native_backend,
        "relative_sample_frames": frames, "comparison": comparison,
        "tally_anchored_guest_phase": phase,
        "zoo_terminal_host_phase": zoo_phase,
        "zoo_race_mesh": zoo_race_mesh,
        "switcher_same_host_penultimate": switcher_same_host,
        "switcher_same_host_full_memory_offsets": switcher_same_host_memory,
        "source_terminal_followthrough": source_followthrough,
        "zoo_next_bowl_handoff": next_bowl,
        "bowl_next_switcher_handoff": next_switcher,
        "bowl_source_movie_three_guest_memory": source_movie_handoff,
        "dragster_next_zoo_handoff": next_zoo,
        "reference_script_sha256": sha(reference_script),
        "reference": reference, "native": native,
        "scope": "original archived scene inputs, fresh reference/native stock menu; event results text from guest PPU dumps; instruction-time contact causality unproven"
    }
    dragster_next_diagnostic = bool(
        args.dragster_next_zoo and next_zoo is not None
        and comparison["both_reached_terminal_menu"]
        and comparison["rendered_result_and_score_text_matched"]
        and comparison["original_source_entry_equivalent"]
        and comparison["fresh_guest_entry_equivalent"]
        and next_zoo["fresh_original_loaded_true_zoo_course_while_active"]
        and next_zoo["fresh_native_loaded_true_zoo_course_while_active"])
    diagnostic = bool(
        (args.observe_one_frame_stunt_lead
         and comparison["bounded_stunt_one_frame_phase_observed"])
        or dragster_next_diagnostic)
    comparison["bounded_dragster_to_zoo_diagnostic_without_full_event_parity"] = dragster_next_diagnostic
    comparison["diagnostic_exit_success_without_full_event_parity"] = diagnostic
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"course": report["course_id"], "source": original_event,
                      "comparison": comparison}, sort_keys=True))
    # Diagnostic success means *observed narrow phase discrepancy*,
    # never complete-event parity or permission to update 0/45 ledger.
    return 0 if comparison["paired_event_candidate"] or diagnostic else 1


if __name__ == "__main__":
    raise SystemExit(main())
