#!/usr/bin/env python3
"""Opt-in read-only Bowl result -> next Switcher original/native witness.

Three distinct clocks: the immutable 2014 USA movie and two independently
booted original/native guests. No guest patch, phase shift, acceptance claim,
RAM exclusions or persisted-disk assertion. The event producer owns input,
source/result and executable identities; this helper only observes progression.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

SOURCE_BOWL_RESULT = 11985
SOURCE_SWITCHER_ENTRY = 12327
SOURCE_DISTANCE = SOURCE_SWITCHER_ENTRY - SOURCE_BOWL_RESULT
OFFSETS = (334, 338, 339, 340, 341, 342, 343, 344, 345, 346, 349, 354)
SCHEMA = "UR-QA01-BOWL-TO-AUTHENTIC-SWITCHER-NEXT-RACE/1"


class BowlSwitcherEvidenceError(ValueError):
    pass


def active_switcher(row: dict) -> bool:
    return (type(row.get("track")) is int and row["track"] == 3
            and type(row.get("in_race")) is int and row["in_race"] == 1)


def source_next_switcher(states: dict[int, dict], result_frame: int) -> dict:
    """Only an actually observed sustained 2014 event earns a source anchor."""
    if result_frame != SOURCE_BOWL_RESULT:
        raise BowlSwitcherEvidenceError("wrong original movie Bowl result frame")
    if SOURCE_DISTANCE != 342:
        raise BowlSwitcherEvidenceError("source chronology inconsistent")
    previous = states.get(SOURCE_SWITCHER_ENTRY - 1)
    if not isinstance(previous, dict) or active_switcher(previous):
        raise BowlSwitcherEvidenceError("source lacks inactive pre-entry at 12326")
    if any(not isinstance(states.get(f), dict)
           or not active_switcher(states[f])
           for f in range(SOURCE_SWITCHER_ENTRY, SOURCE_SWITCHER_ENTRY + 8)):
        raise BowlSwitcherEvidenceError("source lacks eight actual Switcher race frames")
    samples = {}
    for offset in OFFSETS:
        frame = result_frame + offset
        state = states.get(frame)
        if not isinstance(state, dict) or any(
                type(state.get(k)) is not int
                for k in ("menu", "track", "in_race")):
            raise BowlSwitcherEvidenceError(f"missing original source frame {frame}")
        samples[str(offset)] = {
            "original_movie_host_frame": frame,
            "menu": state["menu"],
            "track": state["track"],
            "in_race": state["in_race"],
        }
    if active_switcher(samples["341"]) or not active_switcher(samples["342"]):
        raise BowlSwitcherEvidenceError("source entry bracket not +341/+342")
    return {
        "source_result_host_frame": result_frame,
        "source_next_switcher_entry_host_frame": SOURCE_SWITCHER_ENTRY,
        "source_result_to_next_active_entry_frames": SOURCE_DISTANCE,
        "source_active_eight_consecutive_frames": True,
        "samples": samples,
        "source_controller_masks_modified": False,
        "release_complete_event_credit": 0,
    }


def _bracket(samples: list[dict], side: str) -> dict:
    last = None
    for row in samples:
        offset = row["offset_from_observed_bowl_result"]
        value = (row["original_movie"] if side == "movie"
                 else row["fresh_guests"][side])
        is_active = active_switcher(value)
        if is_active:
            exact = offset if last and last[0] == offset - 1 and not last[1] else None
            return {
                "last_observed_inactive_offset": last[0] if last and not last[1] else None,
                "first_observed_active_offset": offset,
                "exact_observed_entry_offset": exact,
            }
        last = (offset, is_active)
    return {
        "last_observed_inactive_offset": last[0] if last and not last[1] else None,
        "first_observed_active_offset": None,
        "exact_observed_entry_offset": None,
    }


def observe_next_switcher(original_dir: Path, native_dir: Path,
                          original_log: str, native_log: str,
                          source: dict, original_entry: int, native_entry: int,
                          original_result_relative: int, native_result_relative: int,
                          *, observed_dump_frame, decode_sram, audit_wram,
                          switcher_payload: bytes | None = None,
                          validate_course_payload=None) -> dict:
    """Retain original/native complete-memory comparisons without masking."""
    if (not isinstance(source, dict)
            or source.get("source_result_host_frame") != SOURCE_BOWL_RESULT
            or source.get("source_next_switcher_entry_host_frame") != SOURCE_SWITCHER_ENTRY
            or source.get("source_result_to_next_active_entry_frames") != SOURCE_DISTANCE
            or source.get("source_active_eight_consecutive_frames") is not True
            or source.get("source_controller_masks_modified") is not False
            or source.get("release_complete_event_credit") != 0
            or set(source.get("samples", {})) != {str(x) for x in OFFSETS}):
        raise BowlSwitcherEvidenceError("missing exact original Bowl-to-Switcher source")
    if (switcher_payload is None) != (validate_course_payload is None):
        raise BowlSwitcherEvidenceError("payload and validator must be supplied together")
    samples = []
    for offset in OFFSETS:
        original_movie = source["samples"][str(offset)]
        if (not isinstance(original_movie, dict)
                or original_movie.get("original_movie_host_frame") !=
                SOURCE_BOWL_RESULT + offset
                or any(type(original_movie.get(k)) is not int
                       for k in ("menu", "track", "in_race"))):
            raise BowlSwitcherEvidenceError("invalid original movie handoff state")
        tag = f"bowl-next-switcher-{offset:03d}"
        guests = {}
        full_memories = {}
        full_batteries = {}
        for side, directory, log, entry, result in (
                ("original", original_dir, original_log, original_entry,
                 original_result_relative),
                ("native", native_dir, native_log, native_entry,
                 native_result_relative)):
            host = observed_dump_frame(log, tag)
            if type(host) is not int or host != entry + result + offset:
                raise BowlSwitcherEvidenceError(f"{side} guest handoff host-clock mismatch")
            memory_path = directory / f"{tag}.wram.bin"
            battery_path = directory / f"{tag}.sram.bin"
            if not memory_path.is_file() or not battery_path.is_file():
                raise BowlSwitcherEvidenceError("missing executed guest memory/SRAM image")
            memory = memory_path.read_bytes()
            battery = battery_path.read_bytes()
            if len(memory) != 0x20000 or len(battery) != 8192:
                raise BowlSwitcherEvidenceError("truncated full guest WRAM/SRAM")
            rec = decode_sram(battery_path, 2)
            full_memories[side], full_batteries[side] = memory, battery
            word = lambda address: int.from_bytes(
                memory[address:address + 2], "little")
            guests[side] = {
                "actual_host_frame": host,
                "menu": memory[0x009F],
                "track": memory[0x00CE],
                "in_race": memory[0x0313],
                "tour_row": memory[0x009B],
                "p1_laps": word(0x0EF1),
                "p2_laps": word(0x0EF3),
                "p1_checkpoint": word(0x1199),
                "p1_finish_gate": word(0x119D),
                "p1_last_result_word": word(0x0618),
                "p1_x": word(0x0411),
                "p1_y": word(0x0415),
                "source_exact_switcher_course_payload": (
                    bool(validate_course_payload(
                        switcher_payload, memory[0x10000:]))
                    if switcher_payload is not None else None),
                "full_wram_bytes": len(memory),
                "wram_sha256": hashlib.sha256(memory).hexdigest(),
                "full_sram_bytes": len(battery),
                "sram_sha256": hashlib.sha256(battery).hexdigest(),
                "source_earned_bowl_rank0": rec["crawler_record_three_ranks"][0],
                "record_table_checksum_matches": rec["record_table_checksum_matches_at_sample"],
            }
        original_state = {k: original_movie[k] for k in ("menu", "track", "in_race")}
        matched = all(
            {k: guests[side][k] for k in original_state} == original_state
            for side in ("original", "native"))
        guest_differences = [
            key for key in ("menu", "track", "in_race", "tour_row", "p1_laps",
                            "p2_laps", "p1_checkpoint", "p1_finish_gate",
                            "p1_last_result_word", "p1_x", "p1_y")
            if guests["original"][key] != guests["native"][key]]
        sram_differences = [
            i for i, (a, b) in enumerate(zip(
                full_batteries["original"], full_batteries["native"]))
            if a != b]
        samples.append({
            "offset_from_observed_bowl_result": offset,
            "original_movie": original_movie,
            "fresh_guests": guests,
            "triplet_named_states_equal": matched,
            "original_native_named_field_differences": guest_differences,
            "source_movie_vs_fresh_original_named_field_differences": [
                k for k in original_state
                if guests["original"][k] != original_state[k]],
            "source_movie_vs_fresh_native_named_field_differences": [
                k for k in original_state
                if guests["native"][k] != original_state[k]],
            "full_sram_pair_equal": not sram_differences,
            "full_sram_differing_byte_count": len(sram_differences),
            "full_sram_first_16_differences": [{
                "offset": i,
                "original_byte": full_batteries["original"][i],
                "native_byte": full_batteries["native"][i],
            } for i in sram_differences[:16]],
            "full_wram_byte_difference": audit_wram(
                full_memories["original"], full_memories["native"]),
        })
    brackets = {side: _bracket(samples, side)
                for side in ("movie", "original", "native")}
    source_start = brackets["movie"]["exact_observed_entry_offset"]
    reference_start = brackets["original"]["exact_observed_entry_offset"]
    native_start = brackets["native"]["exact_observed_entry_offset"]
    if source_start != SOURCE_DISTANCE:
        raise BowlSwitcherEvidenceError("source movie did not prove exact next Switcher entry")
    reference_abs = (original_entry + original_result_relative + reference_start
                     if reference_start is not None else None)
    native_abs = (native_entry + native_result_relative + native_start
                  if native_start is not None else None)
    return {
        "schema": SCHEMA,
        "source_original_result_frame": SOURCE_BOWL_RESULT,
        "source_original_next_switcher_frame": SOURCE_SWITCHER_ENTRY,
        "source_next_switcher_entry_offset": SOURCE_DISTANCE,
        "original_movie_entry_bracket": brackets["movie"],
        "fresh_reference_entry_bracket": brackets["original"],
        "fresh_native_entry_bracket": brackets["native"],
        "fresh_reference_entry_offset": reference_start,
        "fresh_native_entry_offset": native_start,
        "fresh_reference_entry_absolute_host_frame": reference_abs,
        "fresh_native_entry_absolute_host_frame": native_abs,
        "same_absolute_host_entry": (reference_abs is not None
                                     and reference_abs == native_abs),
        "all_three_entry_offsets_equal": (reference_start == native_start == source_start),
        "all_triplet_named_states_equal": all(x["triplet_named_states_equal"] for x in samples),
        "first_movie_fresh_original_named_divergence_offset": next(
            (x["offset_from_observed_bowl_result"] for x in samples
             if x["source_movie_vs_fresh_original_named_field_differences"]), None),
        "first_movie_fresh_native_named_divergence_offset": next(
            (x["offset_from_observed_bowl_result"] for x in samples
             if x["source_movie_vs_fresh_native_named_field_differences"]), None),
        "first_original_native_named_divergence_offset": next(
            (x["offset_from_observed_bowl_result"] for x in samples
             if x["original_native_named_field_differences"]), None),
        "first_full_sram_differing_sample_offset": next(
            (x["offset_from_observed_bowl_result"] for x in samples
             if x["full_sram_differing_byte_count"]), None),
        "full_sram_differing_sample_offsets": [
            x["offset_from_observed_bowl_result"] for x in samples
            if x["full_sram_differing_byte_count"]],
        "source_exact_switcher_payload_observed": (
            {side: any(
                row["fresh_guests"][side]["source_exact_switcher_course_payload"] is True
                for row in samples if row["fresh_guests"][side]["in_race"] == 1
                and row["fresh_guests"][side]["track"] == 3)
             for side in ("original", "native")}
            if switcher_payload is not None else None),
        "all_full_8192_sram_pairs_equal": all(x["full_sram_pair_equal"] for x in samples),
        "all_full_128k_wram_pairs_equal": all(
            x["full_wram_byte_difference"]["byte_exact"] for x in samples),
        "full_wram_differing_sample_offsets": [
            x["offset_from_observed_bowl_result"] for x in samples
            if not x["full_wram_byte_difference"]["byte_exact"]],
        "source_earned_bowl_rank0_764_and_checksum_every_sample": all(
            x["fresh_guests"][side]["source_earned_bowl_rank0"][
                "value_word"] == 764
            and x["fresh_guests"][side]["record_table_checksum_matches"]
            for x in samples for side in ("original", "native")),
        "sample_offsets": list(OFFSETS),
        "samples": samples,
        "source_controller_masks_modified": False,
        "original_native_clocks_unrebased": True,
        "full_cpu_spc_logic_tick_equivalence_proven": False,
        "shipping_windows_candidate_proven": False,
        "cold_process_disk_persistence_proven": False,
        "release_complete_event_credit": 0,
    }
