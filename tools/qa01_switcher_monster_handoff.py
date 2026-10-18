#!/usr/bin/env python3
"""Opt-in genuine 2014 Switcher Race B -> Monster Circuit B source/fresh witness.

All source and guest clocks are distinct. No input retime, byte masking,
full-event acceptance or CPU/APU modification. New course identification
requires sustained original source execution, not menu or track-ID guesses.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

SCHEMA = "UR-QA01-SWITCHER-TO-MONSTER-SOURCE-AND-FRESH-GUESTS/1"
SWITCHER_SOURCE_ENTRY = 12327
SWITCHER_SOURCE_RESULT = 17030
MONSTER_TRACK = 4
SOURCE_MIN_OFFSET, SOURCE_MAX_OFFSET = 73, 1500
RELATIVE_SAMPLE_DELTAS = (-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 7, 10)


class SwitcherMonsterError(ValueError):
    pass


def active(row: dict, track: int) -> bool:
    return (type(row.get("in_race")) is int and row["in_race"] == 1
            and type(row.get("track")) is int and row["track"] == track)


def crawler_monster_active(row: dict) -> bool:
    return (active(row, MONSTER_TRACK) and
            type(row.get("tour_row")) is int and row["tour_row"] == 0)


def source_next_monster(states: dict[int, dict], switcher: dict) -> dict:
    """First truly sustained subsequent source course, with real frame tags."""
    if (switcher.get("original_entry_frame") != SWITCHER_SOURCE_ENTRY
            or switcher.get("original_result_frame") != SWITCHER_SOURCE_RESULT
            or switcher.get("source_active_frames_to_result") !=
            SWITCHER_SOURCE_RESULT - SWITCHER_SOURCE_ENTRY):
        raise SwitcherMonsterError("not proven original 2014 completed Switcher")
    first, last = (SWITCHER_SOURCE_RESULT + SOURCE_MIN_OFFSET,
                   SWITCHER_SOURCE_RESULT + SOURCE_MAX_OFFSET)
    candidates = []
    for frame in range(first, last + 1):
        if (crawler_monster_active(states.get(frame, {}))
                and not crawler_monster_active(states.get(frame - 1, {}))
                and all(crawler_monster_active(states.get(frame + i, {}))
                        for i in range(8))):
            candidates.append(frame)
    if len(candidates) != 1:
        raise SwitcherMonsterError("missing/ambiguous sustained source Monster next-course entry")
    entry = candidates[0]
    offset = entry - SWITCHER_SOURCE_RESULT
    samples = tuple(offset + i for i in RELATIVE_SAMPLE_DELTAS)
    if samples[0] <= 72 or samples[-1] > SOURCE_MAX_OFFSET + 16:
        raise SwitcherMonsterError("next Monster entry beyond bounded source replay")
    for n in range(SWITCHER_SOURCE_RESULT + 73, entry):
        row = states.get(n, {})
        # A different real active course before Monster invalidates direct successor.
        if (type(row.get("track")) is int and row["track"] != MONSTER_TRACK
                and row["track"] != 3 and active(row, row["track"])
                and all(active(states.get(n + j, {}), row["track"])
                        for j in range(8))):
            raise SwitcherMonsterError("foreign sustained active course before Monster")
    source_samples = {}
    for o in samples:
        state = states.get(SWITCHER_SOURCE_RESULT + o)
        if (not isinstance(state, dict) or
                any(type(state.get(k)) is not int
                    for k in ("menu", "track", "in_race", "tour_row"))):
            raise SwitcherMonsterError("original movie source missing exact frame")
        source_samples[str(o)] = {
            "movie_host_frame": SWITCHER_SOURCE_RESULT + o,
            "menu": state["menu"],
            "track": state["track"],
            "in_race": state["in_race"],
            "tour_row": state["tour_row"],
        }
    if crawler_monster_active(source_samples[str(offset - 1)]):
        raise SwitcherMonsterError("source Monster entry lacks immediate inactive preceding frame")
    if not all(crawler_monster_active(source_samples[str(offset+i)])
               for i in (0,1,2,3,4,5,7,10)):
        raise SwitcherMonsterError("source Monster active run not sustained")
    return {
        "source_switcher_result_frame": SWITCHER_SOURCE_RESULT,
        "source_monster_entry_movie_frame": entry,
        "source_switcher_result_to_monster_entry": offset,
        "sample_offsets": list(samples),
        "source_samples": source_samples,
        "source_monster_eight_contiguous_active_frames": True,
        "original_movie_controller_masks_unchanged": True,
        "complete_usa_event_credit": 0,
    }


def _bracket(rows: list[dict], side: str) -> dict:
    previous = None
    for row in rows:
        offset = row["offset"]
        state = row["movie"] if side == "movie" else row["guests"][side]
        current = crawler_monster_active(state)
        if current:
            return {
                "first_observed_active_offset": offset,
                "last_observed_inactive_offset": (
                    previous[0] if previous is not None and not previous[1] else None),
                "exact_adjacent_entry_offset": (
                    offset if previous is not None
                    and previous[0] == offset - 1 and not previous[1] else None),
            }
        previous = (offset, current)
    return {"first_observed_active_offset": None,
            "last_observed_inactive_offset": previous[0] if previous else None,
            "exact_adjacent_entry_offset": None}


def observe_next_monster(original_dir: Path, native_dir: Path,
                         original_log: str, native_log: str, source: dict,
                         reference_entry: int, native_entry: int,
                         original_result: int, native_result: int,
                         *, observed_dump_frame, audit_wram,
                         monster_payload: bytes, validate_course_payload) -> dict:
    if (source.get("source_switcher_result_frame") != SWITCHER_SOURCE_RESULT
            or source.get("source_monster_eight_contiguous_active_frames") is not True
            or source.get("original_movie_controller_masks_unchanged") is not True
            or source.get("complete_usa_event_credit") != 0):
        raise SwitcherMonsterError("source Monster boundary not attested")
    samples = source.get("sample_offsets")
    expected = source.get("source_switcher_result_to_monster_entry")
    if (not isinstance(samples, list)
            or type(expected) is not int
            or samples != [expected + x for x in RELATIVE_SAMPLE_DELTAS]):
        raise SwitcherMonsterError("unexpected source Monster bracket")
    if any(type(n) is not int or n < 0 for n in
           (reference_entry,native_entry,original_result,native_result)):
        raise SwitcherMonsterError("invalid independent event clocks")
    rows = []
    for offset in samples:
        movie = source["source_samples"][str(offset)]
        if (movie.get("movie_host_frame") != SWITCHER_SOURCE_RESULT + offset
                or any(type(movie.get(k)) is not int for k in ("menu", "track", "in_race", "tour_row"))):
            raise SwitcherMonsterError("unregistered original source movie frame")
        guests = {}
        raw = {}
        sram = {}
        for side, folder, log, entry, result in (
                ("original", original_dir, original_log, reference_entry, original_result),
                ("native", native_dir, native_log, native_entry, native_result)):
            tag = f"switcher-next-monster-{offset:04d}"
            observed = observed_dump_frame(log, tag)
            if observed != entry + result + offset:
                raise SwitcherMonsterError("guest handoff log lacks real separate host frame")
            wpath = folder / f"{tag}.wram.bin"
            spath = folder / f"{tag}.sram.bin"
            if not wpath.is_file() or not spath.is_file():
                raise SwitcherMonsterError("missing genuine executed guest memory")
            w = wpath.read_bytes()
            s = spath.read_bytes()
            if len(w) != 0x20000 or len(s) != 8192:
                raise SwitcherMonsterError("short full 128KiB WRAM/8KiB SRAM")
            raw[side], sram[side] = w, s
            loaded = validate_course_payload(monster_payload, w[0x10000:])
            guests[side] = {
                "absolute_host_frame": observed, "menu": w[0x009f],
                "track": w[0x00ce], "in_race": w[0x0313],
                "tour_row": w[0x00d0],
                "canonical_source_monster_course_payload_loaded": bool(loaded),
                "full_wram_bytes": len(w), "full_wram_sha256": hashlib.sha256(w).hexdigest(),
                "full_sram_bytes": len(s), "full_sram_sha256": hashlib.sha256(s).hexdigest(),
            }
        rows.append({
            "offset":offset, "movie":movie, "guests":guests,
            "triplet_named_state_equal": all(
                all(guests[s][k] == movie[k] for k in ("menu","track","in_race","tour_row"))
                for s in ("original", "native")),
            "full_sram_pair_equal": sram["original"] == sram["native"],
            "unmasked_full_wram": audit_wram(raw["original"], raw["native"])
        })
    b={s:_bracket(rows,s) for s in ("movie","original","native")}
    if b["movie"]["exact_adjacent_entry_offset"] != expected:
        raise SwitcherMonsterError("source Monster active onset lost")
    return {
        "schema":SCHEMA,
        "source_original_switcher_result_frame": SWITCHER_SOURCE_RESULT,
        "source_monster_entry_movie_frame":source["source_monster_entry_movie_frame"],
        "source_monster_entry_relative_result_offset":expected,
        "sample_offsets":samples,
        "brackets":b,
        "original_entry_relative_result_offset":b["original"]["exact_adjacent_entry_offset"],
        "native_entry_relative_result_offset":b["native"]["exact_adjacent_entry_offset"],
        "all_three_entries_same_result_relative_offset": all(
            b[s]["exact_adjacent_entry_offset"] == expected
            for s in ("original","native")),
        "first_triplet_named_state_mismatch_offset":next(
            (row["offset"] for row in rows if not row["triplet_named_state_equal"]),None),
        "all_full_8192_sram_pairs_equal":all(row["full_sram_pair_equal"] for row in rows),
        "full_wram_differing_offsets":[row["offset"] for row in rows
                                      if not row["unmasked_full_wram"]["byte_exact"]],
        "original_monster_source_course_loaded_on_active_sample":any(
            row["guests"]["original"]["canonical_source_monster_course_payload_loaded"]
            for row in rows if crawler_monster_active(row["guests"]["original"])),
        "native_monster_source_course_loaded_on_active_sample":any(
            row["guests"]["native"]["canonical_source_monster_course_payload_loaded"]
            for row in rows if crawler_monster_active(row["guests"]["native"])),
        "samples":rows,
        "controller_input_rephased":False,
        "source_2014_monster_complete_result_proven":False,
        "strict_switcher_original_native_complete_fidelity_proven":False,
        "shipping_binary_or_disk_recovery_proven":False,
        "release_complete_event_credit":0,
    }
