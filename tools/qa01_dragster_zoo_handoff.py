#!/usr/bin/env python3
"""Authentic USA 2014 Dragster Race A -> next Zoom Zoo Circuit A witness.

No controller rephase, CPU/APU edits, hidden WRAM exclusions or course pass.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

SCHEMA = "UR-QA01-DRAGSTER-TO-ZOO-FRESH-GUEST-PROGRESSION/1"
DRAGSTER_ENTRY, DRAGSTER_RESULT = 794, 2874
ZOO_ENTRY = 3190
SOURCE_DISTANCE = ZOO_ENTRY - DRAGSTER_RESULT
OFFSETS = (304, 308, 312, 314, 315, 316, 317, 318, 319, 320, 321, 324, 328, 336)


class DragsterZooEvidenceError(ValueError):
    pass


def is_zoo(row: dict) -> bool:
    return (type(row.get("track")) is int and row["track"] == 1
            and type(row.get("tour_row")) is int and row["tour_row"] == 0
            and type(row.get("in_race")) is int and row["in_race"] == 1)


def source_next_zoo(states: dict[int, dict], event: dict) -> dict:
    """Require a sustained *observed* 2014 source race, not menu track select."""
    if (not isinstance(event, dict) or event.get("original_entry_frame") != DRAGSTER_ENTRY
            or event.get("original_result_frame") != DRAGSTER_RESULT
            or event.get("source_active_frames_to_result") != DRAGSTER_RESULT - DRAGSTER_ENTRY):
        raise DragsterZooEvidenceError("unqualified original 2014 Dragster result")
    if is_zoo(states.get(ZOO_ENTRY - 1, {})):
        raise DragsterZooEvidenceError("source Zoo onset already active at preceding frame")
    if not all(is_zoo(states.get(f, {})) for f in range(ZOO_ENTRY, ZOO_ENTRY + 8)):
        raise DragsterZooEvidenceError("source fails 8 actual Zoo race frames")
    # The original movie has just one sustained entry after Dragster's result.
    for f in range(DRAGSTER_RESULT + 73, ZOO_ENTRY):
        row = states.get(f, {})
        if is_zoo(row) and all(is_zoo(states.get(f + j, {})) for j in range(8)):
            raise DragsterZooEvidenceError("earlier sustained Zoo source entry")
        if (type(row.get("track")) is int and row["track"] not in (0, 1)
                and row.get("in_race") == 1
                and all(states.get(f + j, {}).get("track") == row["track"]
                        and states.get(f + j, {}).get("in_race") == 1
                        for j in range(8))):
            raise DragsterZooEvidenceError("intervening foreign active course")
    samples = {}
    for offset in OFFSETS:
        movie_frame = DRAGSTER_RESULT + offset
        row = states.get(movie_frame)
        if (not isinstance(row, dict)
                or any(type(row.get(k)) is not int
                       for k in ("menu", "track", "in_race", "tour_row"))):
            raise DragsterZooEvidenceError("original movie sample frame missing")
        samples[str(offset)] = {
            "original_movie_host_frame": movie_frame,
            **{k: row[k] for k in ("menu", "track", "in_race", "tour_row")},
        }
    if is_zoo(samples["315"]) or not all(
            is_zoo(samples[str(offset)]) for offset in range(316, 322)):
        raise DragsterZooEvidenceError("source Zoo +315/+316 boundary not proven")
    return {
        "schema": SCHEMA,
        "original_dragster_entry_host_frame": DRAGSTER_ENTRY,
        "original_dragster_result_host_frame": DRAGSTER_RESULT,
        "original_zoo_active_entry_host_frame": ZOO_ENTRY,
        "source_dragster_result_to_zoo_active_frames": SOURCE_DISTANCE,
        "original_zoo_eight_consecutive_active_frames": True,
        "original_movie_controller_masks_modified": False,
        "sample_offsets": list(OFFSETS),
        "source_samples": samples,
        "release_complete_usa_event_credit": 0,
    }


def entry_bracket(rows: list[dict], who: str) -> dict:
    previous = None
    for r in rows:
        offset = r["offset_from_respective_dragster_result"]
        value = r["source_original"] if who == "movie" else r["fresh_guests"][who]
        active = is_zoo(value)
        if active:
            return {
                "first_observed_active_offset": offset,
                "last_observed_inactive_offset": previous[0] if previous and not previous[1] else None,
                "exact_adjacent_onset_offset": (
                    offset if previous and previous[0] == offset - 1 and not previous[1] else None),
            }
        previous = (offset, active)
    return {"first_observed_active_offset": None,
            "last_observed_inactive_offset": previous[0] if previous and not previous[1] else None,
            "exact_adjacent_onset_offset": None}


def observe_guest_handoff(ref_dir: Path, native_dir: Path, ref_log: str,
                          native_log: str, proof: dict,
                          ref_entry: int, native_entry: int,
                          ref_result: int, native_result: int,
                          *, observed_dump_frame, audit_wram,
                          validate_course_payload, zoo_course_payload: bytes,
                          decode_sram) -> dict:
    if (not isinstance(proof, dict)
            or proof.get("schema") != SCHEMA
            or proof.get("original_dragster_entry_host_frame") != DRAGSTER_ENTRY
            or proof.get("original_dragster_result_host_frame") != DRAGSTER_RESULT
            or proof.get("original_zoo_active_entry_host_frame") != ZOO_ENTRY
            or proof.get("source_dragster_result_to_zoo_active_frames") != SOURCE_DISTANCE
            or proof.get("original_zoo_eight_consecutive_active_frames") is not True
            or proof.get("original_movie_controller_masks_modified") is not False
            or proof.get("release_complete_usa_event_credit") != 0
            or proof.get("sample_offsets") != list(OFFSETS)
            or set(proof.get("source_samples", {})) != set(map(str, OFFSETS))):
        raise DragsterZooEvidenceError("source-original Dragster to Zoo not authenticated")
    if any(type(n) is not int or n < 0 for n in
           (ref_entry, native_entry, ref_result, native_result)):
        raise DragsterZooEvidenceError("invalid independently observed clocks")
    rows=[]
    for offset in OFFSETS:
        source=proof["source_samples"][str(offset)]
        if (not isinstance(source, dict)
                or source.get("original_movie_host_frame") != DRAGSTER_RESULT+offset
                or any(type(source.get(k)) is not int
                       for k in ("menu","track","in_race","tour_row"))):
            raise DragsterZooEvidenceError("unregistered historical movie frame")
        guests={}; memory={}; batteries={}
        for side,folder,log,entry,result in (
                ("original",ref_dir,ref_log,ref_entry,ref_result),
                ("native",native_dir,native_log,native_entry,native_result)):
            tag=f"dragster-next-zoo-{offset:03d}"
            observed=observed_dump_frame(log,tag)
            if observed != entry+result+offset:
                raise DragsterZooEvidenceError(f"{side} missing exact guest host clock")
            wpath=folder/f"{tag}.wram.bin"
            spath=folder/f"{tag}.sram.bin"
            if not wpath.is_file() or not spath.is_file():
                raise DragsterZooEvidenceError(f"missing executed {side} raw WRAM/SRAM")
            w,s=wpath.read_bytes(),spath.read_bytes()
            if len(w)!=0x20000 or len(s)!=8192:
                raise DragsterZooEvidenceError("truncated full guest WRAM/SRAM images")
            memory[side],batteries[side]=w,s
            record=decode_sram(spath,0)
            guests[side]={
                "host_frame":observed,
                "menu":w[0x009f],"track":w[0x00ce],
                "in_race":w[0x0313],"tour_row":w[0x00d0],
                "true_source_zoo_payload_loaded": bool(
                    validate_course_payload(zoo_course_payload,w[0x10000:])),
                "full_wram_sha256":hashlib.sha256(w).hexdigest(),
                "full_wram_bytes":len(w),
                "full_sram_sha256":hashlib.sha256(s).hexdigest(),
                "full_sram_bytes":len(s),
                "dragster_record_three_ranks":record["crawler_record_three_ranks"],
                "ranked_records_checksum_valid":record["record_table_checksum_matches_at_sample"],
            }
        delta=[k for k in ("menu","track","in_race","tour_row")
               if source[k]!=guests["original"][k] or source[k]!=guests["native"][k]]
        rows.append({
            "offset_from_respective_dragster_result":offset,
            "source_original":source,
            "fresh_guests":guests,
            "source_to_fresh_named_disagreements":delta,
            "full_original_native_sram_pair_equal":batteries["original"]==batteries["native"],
            "unmasked_full_original_native_wram_difference":audit_wram(
                memory["original"],memory["native"]),
        })
    b={who:entry_bracket(rows,who) for who in ("movie","original","native")}
    if b["movie"]["exact_adjacent_onset_offset"]!=SOURCE_DISTANCE:
        raise DragsterZooEvidenceError("historic Zoo onset not exact +316")
    return {
        "schema":SCHEMA,
        "original_movie_dragster_result_frame":DRAGSTER_RESULT,
        "original_movie_zoo_entry_frame":ZOO_ENTRY,
        "original_movie_zoo_entry_relative_to_dragster_result":SOURCE_DISTANCE,
        "entry_brackets":b,
        "all_three_guest_result_relative_entry_offsets_equal":all(
            b[k]["exact_adjacent_onset_offset"]==SOURCE_DISTANCE
            for k in ("original","native")),
        "fresh_original_absolute_zoo_onset_host":(
            ref_entry+ref_result+b["original"]["exact_adjacent_onset_offset"]
            if b["original"]["exact_adjacent_onset_offset"] is not None else None),
        "fresh_native_absolute_zoo_onset_host":(
            native_entry+native_result+b["native"]["exact_adjacent_onset_offset"]
            if b["native"]["exact_adjacent_onset_offset"] is not None else None),
        "first_source_or_guest_named_mismatch_offset":next(
            (r["offset_from_respective_dragster_result"] for r in rows
             if r["source_to_fresh_named_disagreements"]),None),
        "all_full_sram_pairs_equal":all(r["full_original_native_sram_pair_equal"] for r in rows),
        "full_wram_difference_offsets":[
            r["offset_from_respective_dragster_result"] for r in rows
            if not r["unmasked_full_original_native_wram_difference"]["byte_exact"]],
        "fresh_original_loaded_true_zoo_course_while_active":any(
            r["fresh_guests"]["original"]["true_source_zoo_payload_loaded"]
            for r in rows if is_zoo(r["fresh_guests"]["original"])),
        "fresh_native_loaded_true_zoo_course_while_active":any(
            r["fresh_guests"]["native"]["true_source_zoo_payload_loaded"]
            for r in rows if is_zoo(r["fresh_guests"]["native"])),
        "original_native_ranked_checksum_valid_all_samples":all(
            r["fresh_guests"][who]["ranked_records_checksum_valid"]
            for r in rows for who in ("original","native")),
        "samples":rows,
        "source_controller_masks_rephased":False,
        "original_native_complete_dragster_cpu_spc_frame_parity_proven":False,
        "original_native_complete_zoo_event_proven":False,
        "cold_host_disk_persistence_proven":False,
        "shipping_windows_source_identity_proven":False,
        "release_complete_usa_event_credit":0,
    }
