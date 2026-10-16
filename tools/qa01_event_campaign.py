#!/usr/bin/env python3
"""Manual QA-01 event campaign planner, per-case classifier, and final aggregator.

Transport/orchestration only. Original/native semantics stay in the existing
probe_original_event_complete.py, and RELEASE-QUALITY-LEDGER.json remains the
sole release-gate authority. Synthetic unit tests are not gameplay evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA = "ur-qa01-event-campaign/1"
CASES = {
    "zoom-zoo": {"course_id": "course:02", "family": "circuit-a"},
    "bowl": {"course_id": "course:03", "family": "stunt"},
    "switcher": {"course_id": "course:04", "family": "race-b"},
}
HEX256 = re.compile(r"^[0-9a-f]{64}$")


def canonical(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(data: object) -> str:
    return hashlib.sha256(canonical(data).encode("ascii")).hexdigest()


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("expected JSON object")
    return obj


def make_plan(selection: str, source_sha: str) -> dict:
    if selection != "all" and selection not in CASES:
        raise ValueError("unknown case selection")
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("source revision must be an exact 40-character SHA-1")
    selected = list(CASES) if selection == "all" else [selection]
    body = {
        "schema": SCHEMA,
        "source_sha": source_sha,
        "selection": selection,
        "cases": [{"id": case, **CASES[case]} for case in selected],
        "matrix": {"include": [{"case": case} for case in selected]},
        "admission": "investigative only: zero automatic release/course credit",
    }
    body["plan_sha256"] = digest(body)
    return body


def validate_plan(plan: dict) -> None:
    if plan.get("schema") != SCHEMA:
        raise ValueError("invalid campaign schema")
    expected = make_plan(plan.get("selection", ""), plan.get("source_sha", ""))
    if plan != expected:
        raise ValueError("campaign plan modified or digest invalid")


def producer_failure_reason(producer_log: Path | None) -> str:
    """Expose the decisive bounded error, not the whole diagnostic/ROM log."""
    if producer_log is None:
        return ""
    try:
        lines = producer_log.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    for line in reversed(lines[-200:]):
        line = line.strip()
        if ("CompleteEventError:" in line or
            "error while loading shared libraries:" in line or
            "ModuleNotFoundError:" in line or
            "subprocess.TimeoutExpired:" in line):
            return line[-260:]
    return ""


# The producer's preliminary candidate flag is not an independent witness.
# Reconstruct the *claimed* positive predicates before a case can even be
# classified as a strict candidate. This is internal receipt consistency,
# not source-frame, instruction-time, lifecycle, or release acceptance.
STRICT_PRODUCER_GATES = (
    "both_reached_terminal_menu",
    "rendered_result_and_score_text_matched",
    "stunt_positive_score_visible",
    "timed_race_or_circuit_result_visible",
    "circuit_multiple_lap_decrements_sampled",
    "result_outside_active_race_in_both_guests",
    "circuit_zero_remaining_laps_at_onset_and_stable",
    "fresh_guest_entry_equivalent",
)


def strict_producer_gate_audit(comparison: dict, frame_match: bool) -> dict:
    gates = {}
    for name in STRICT_PRODUCER_GATES:
        value = comparison.get(name)
        if type(value) is not bool:
            raise ValueError("missing or non-boolean strict producer gate: " + name)
        gates[name] = value
    first = comparison.get("first_sample_disagreement")
    if first is not None and not isinstance(first, dict):
        raise ValueError("malformed first sampled difference")
    gates["no_sampled_state_disagreement"] = first is None
    gates["same_guest_relative_result_onset"] = frame_match
    recomputed = all(gates.values())
    if comparison.get("paired_event_candidate") is not recomputed:
        raise ValueError("producer strict candidate contradicts its named gameplay gates")
    return {"gates": gates, "recomputed_candidate": recomputed}


# This is a scientific candidate boundary, NOT another event comparator.
# The underlying original/native producer is still the sole writer of these
# executable full-WRAM/frame receipts, and the release ledger stays separate.
FOLLOWTHROUGH_SCHEMA = "UR-QA01-SOURCE-ORIGINAL-NATIVE-RESULT-FOLLOWTHROUGH/2"
FOLLOWTHROUGH_OFFSETS = (8, 16, 24, 32, 64, 72)
FOLLOWTHROUGH_NAMED = ("menu", "track", "in_race",
                       "p1_laps", "p2_laps", "p1_checkpoint", "p1_finish_gate")
FOLLOWTHROUGH_SOURCE = ("menu", "track", "in_race")


def classify_bounded_fresh_battery_sram(record: dict, samples: list,
                                        course_id: str) -> dict:
    """Audit genuine fresh-original/native battery images; no cold reload.

    A historical /2 producer might not include SRAM. Missingness must
    remain explicit and a partial six-frame population must fail closed.
    The source 2014 SMV's post-result SRAM is NOT sampled by this consumer.
    """
    flags = ["fresh_guest_battery_sram" in row for row in samples]
    if not any(flags):
        if any(key in record for key in (
                "all_followthrough_full_sram_pairs_equal",
                "all_followthrough_crawler_record_pairs_equal",
                "battery_sram_snapshot_bytes_per_guest",
                "battery_sram_cold_process_persistence_proven")):
            raise ValueError("unsupported SRAM summary without SRAM snapshots")
        return {"status": "not_observed", "samples": 0,
                "first_full_sram_difference_offset": None,
                "first_course_record_difference_offset": None,
                "cold_process_persistence_proven": False}
    if not all(flags):
        raise ValueError("incomplete six-offset battery SRAM observation")
    if (type(record.get("battery_sram_snapshot_bytes_per_guest")) is not int
            or record["battery_sram_snapshot_bytes_per_guest"] != 8192
            or record.get("battery_sram_cold_process_persistence_proven") is not False):
        raise ValueError("invalid post-result battery SRAM receipt scope")
    try:
        course = int(course_id.split(":")[1]) - 1
    except (ValueError, IndexError, TypeError, AttributeError):
        raise ValueError("invalid post-result Crawler course identity")
    if not 0 <= course < 5:
        raise ValueError("post-result battery SRAM restricted to Crawler")
    full = []
    recordpairs = []
    for row, offset in zip(samples, FOLLOWTHROUGH_OFFSETS):
        sides = row.get("fresh_guest_battery_sram")
        if not isinstance(sides, dict):
            raise ValueError("missing two original/native battery SRAM reads")
        for name in ("original", "native"):
            member = sides.get(name)
            if not isinstance(member, dict):
                raise ValueError("missing SRAM guest side")
            if (type(member.get("full_sram_bytes")) is not int
                    or member["full_sram_bytes"] != 8192
                    or not isinstance(member.get("sram_sha256"), str)
                    or not HEX256.fullmatch(member["sram_sha256"])
                    or type(member.get("crawler_course_track_index")) is not int
                    or member["crawler_course_track_index"] != course
                    or member.get("in_memory_snapshot_only") is not True
                    or member.get("cold_process_reload_proven") is not False):
                raise ValueError("invalid native/original 8KiB live SRAM data")
            ranks = member.get("crawler_record_three_ranks")
            if (not isinstance(ranks, list) or len(ranks) != 3 or
                    any(not isinstance(value, dict)
                        or type(value.get("rank")) is not int
                        or value["rank"] != index
                        or type(value.get("value_word")) is not int
                        or not 0 <= value["value_word"] <= 65535
                        or type(value.get("holder_index")) is not int
                        or not 0 <= value["holder_index"] <= 255
                        for index, value in enumerate(ranks))):
                raise ValueError("incorrect original Crawler SRAM rank table")
            stored = member.get("record_table_checksum_stored")
            calc = member.get("record_table_checksum_calculated")
            if (type(stored) is not int or type(calc) is not int
                    or not 0 <= stored <= 65535
                    or not 0 <= calc <= 65535
                    or member.get("record_table_checksum_matches_at_sample")
                    is not (stored == calc)):
                raise ValueError("invalid live record checksum observation")
        pair = (sides["original"]["sram_sha256"]
                == sides["native"]["sram_sha256"])
        coursepair = (sides["original"]["crawler_record_three_ranks"]
                      == sides["native"]["crawler_record_three_ranks"])
        if (row.get("sram_full_bytes_equal") is not pair
                or row.get("sram_course_three_rank_records_equal") is not coursepair):
            raise ValueError("contradictory SRAM byte/course-record comparison")
        full.append(pair)
        recordpairs.append(coursepair)
    if (record.get("all_followthrough_full_sram_pairs_equal") is not all(full)
            or record.get("all_followthrough_crawler_record_pairs_equal")
            is not all(recordpairs)):
        raise ValueError("contradictory six-sample battery summary")
    return {
        "status": "six_sample_original_native_in_memory_sram_observed",
        "samples": len(samples),
        "all_fresh_sram_byte_pairs_equal": all(full),
        "all_fresh_crawler_ranked_record_pairs_equal": all(recordpairs),
        "first_full_sram_difference_offset": next(
            (offset for offset, same in zip(FOLLOWTHROUGH_OFFSETS, full)
             if not same), None),
        "first_course_record_difference_offset": next(
            (offset for offset, same in zip(FOLLOWTHROUGH_OFFSETS, recordpairs)
             if not same), None),
        "cold_process_persistence_proven": False,
    }


def classify_postresult_followthrough(report: dict, event: dict,
                                      frames: dict) -> dict:
    """Adjudicate *sampled* movie / fresh original / native continuation.

    This cannot establish SRAM persistence, complete-event admission, or
    equivalence of unsampled intermediary frames. It also cannot turn a
    result-relative comparison into a race-relative timing correction.
    """
    record = report.get("source_terminal_followthrough")
    archived = event.get("source_terminal_followthrough")
    if record is None and archived is None:
        return {"status": "not_observed", "samples": 0,
                "first_named_divergence_offset": None,
                "release_credit": 0}
    if not isinstance(record, dict) or not isinstance(archived, dict):
        raise ValueError("post-result source and fresh guest receipts must both exist")
    if (record.get("schema") != FOLLOWTHROUGH_SCHEMA
            or record.get("sample_count") != len(FOLLOWTHROUGH_OFFSETS)
            or record.get("strict_event_comparator_unchanged") is not True
            or type(record.get("release_complete_usa_event_credit")) is not int
            or record["release_complete_usa_event_credit"] != 0
            or record.get("source_guest_relative_result_onset_equivalence_proven") is not False
            or record.get("post_result_sram_persistence_proven") is not False
            or record.get("menu_restoration_or_final_progression_proven") is not False
            or record.get("original_and_native_result_phase_equal_proven") is not (
                frames["reference_relative"] == frames["native_relative"])):
        raise ValueError("invalid or over-promotional post-result receipt")
    samples = record.get("samples")
    if not isinstance(samples, list) or len(samples) != len(FOLLOWTHROUGH_OFFSETS):
        raise ValueError("missing or duplicated post-result sample window")
    original_result = event["original_result_frame"]
    original_host = report["reference_entry"] + frames["reference_relative"]
    native_host = report["native_entry"] + frames["native_relative"]
    first = None
    differences = []
    pairs_equal = []
    bytepairs_equal = []
    for row, offset in zip(samples, FOLLOWTHROUGH_OFFSETS):
        source = archived.get(str(offset))
        if not isinstance(row, dict) or not isinstance(source, dict):
            raise ValueError("missing original source post-result frame")
        if (type(row.get("offset_from_each_observed_result_onset")) is not int
                or row["offset_from_each_observed_result_onset"] != offset
                or row.get("source_original_movie") != source
                or type(source.get("original_movie_host_frame")) is not int
                or source["original_movie_host_frame"] != original_result + offset
                or any(type(source.get(k)) is not int for k in FOLLOWTHROUGH_SOURCE)
                or row.get("independently_observed_replay_host_frames")
                != {"original": original_host + offset,
                    "native": native_host + offset}):
            raise ValueError("post-result host, source or offset identity mismatch")
        guests = row.get("fresh_guests")
        comparison = row.get("source_named_state_comparison")
        if not isinstance(guests, dict) or not isinstance(comparison, dict):
            raise ValueError("missing two fresh guest post-result states")
        seen = {}
        for side in ("original", "native"):
            current = guests.get(side)
            if not isinstance(current, dict) or any(
                    type(current.get(k)) is not int for k in FOLLOWTHROUGH_NAMED):
                raise ValueError("invalid post-result guest semantic bytes")
            if (type(current.get("full_wram_bytes")) is not int
                    or current["full_wram_bytes"] != 0x20000
                    or not isinstance(current.get("wram_sha256"), str)
                    or not HEX256.fullmatch(current["wram_sha256"])):
                raise ValueError("invalid post-result 128KiB WRAM receipt")
            mismatches = [k for k in FOLLOWTHROUGH_SOURCE
                          if current[k] != source[k]]
            claim = comparison.get(side)
            if (not isinstance(claim, dict)
                    or type(claim.get("source_named_state_equal")) is not bool
                    or claim["source_named_state_equal"] != (not mismatches)
                    or claim.get("named_fields_different_from_source") != mismatches):
                raise ValueError("contradictory original movie/guest comparison")
            seen[side] = mismatches
        named = [k for k in FOLLOWTHROUGH_NAMED
                 if guests["original"][k] != guests["native"][k]]
        matched = not named
        raw_equal = (guests["original"]["wram_sha256"]
                     == guests["native"]["wram_sha256"])
        if (type(row.get("paired_named_state_equal")) is not bool
                or row["paired_named_state_equal"] != matched
                or type(row.get("full_wram_bytes_equal")) is not bool
                or row["full_wram_bytes_equal"] != raw_equal):
            raise ValueError("contradictory post-result paired guest status")
        pairs_equal.append(matched)
        bytepairs_equal.append(raw_equal)
        if seen["original"] or seen["native"] or named:
            if first is None:
                first = offset
            differences.append({
                "offset": offset,
                "fresh_original_vs_source": seen["original"],
                "native_vs_source": seen["native"],
                "native_vs_fresh_original": named,
            })
    if (record.get("all_followthrough_named_pairs_equal") is not all(pairs_equal)
            or record.get("all_followthrough_full_wram_pairs_equal")
            is not all(bytepairs_equal)):
        raise ValueError("contradictory post-result summary flags")
    battery = classify_bounded_fresh_battery_sram(
        record, samples, report["course_id"])
    return {
        "status": ("sampled_named_divergence" if differences
                   else "six_sample_triplet_named_agreement"),
        "samples": len(samples),
        "first_named_divergence_offset": first,
        "named_divergences": differences,
        "all_fresh_wram_sha256_pairs_equal": all(bytepairs_equal),
        "guest_relative_result_onset_matched": (
            frames["reference_relative"] == frames["native_relative"]),
        "unsampled_frames_or_persistence_proven": False,
        "fresh_original_native_battery_sram": battery,
        "release_credit": 0,
    }



# This is a separate bounded post-result gate, not part of the primary
# strict result-onset comparator. A matching result can have a divergent
# source-authentic next-race handoff; preserve both facts, without credit.
ZOO_BOWL_SCHEMA = "UR-QA01-ZOO-TO-AUTHENTIC-BOWL-NEXT-RACE/1"
ZOO_BOWL_OFFSETS = (259, 263, 264, 265, 266, 267, 268, 269, 272, 276, 280)


def classify_zoo_next_bowl(report: dict, event: dict, frames: dict) -> dict:
    """Independently recheck genuine sampled next-Bowl state and receipt claims.

    Does not observe unsampled frames or prove a Windows save/complete event.
    A real scientific negative is distinct from a missing or forged receipt.
    """
    record = report.get("zoo_next_bowl_handoff")
    source = event.get("source_next_bowl")
    if record is None and source is None:
        return {"status": "not_observed", "samples": 0,
                "source_entry_offset": None, "fresh_original_entry_offset": None,
                "fresh_native_entry_offset": None,
                "first_sampled_progression_difference_offset": None,
                "all_sampled_full_wram_pairs_equal": None,
                "raw_wram_differing_sample_offsets": [],
                "raw_wram_differing_byte_occurrences": 0,
                "release_credit": 0}
    if (report.get("name") != "zoom-zoo" or not isinstance(record, dict)
            or not isinstance(source, dict)):
        raise ValueError("incomplete/non-Zoo authentic next-Bowl source evidence")
    offsets = list(ZOO_BOWL_OFFSETS)
    if (record.get("schema") != ZOO_BOWL_SCHEMA
            or record.get("sample_count") != len(offsets)
            or record.get("sample_offsets") != offsets
            or record.get("original_source_movie_result_host_frame") != 8353
            or record.get("original_source_movie_next_bowl_active_host_frame") != 8620
            or record.get("source_controller_masks_modified") is not False
            or any(record.get(key) is not False for key in (
                "full_event_guest_logic_tick_equivalence_proven",
                "shipping_windows_candidate_proven",
                "cold_process_disk_persistence_proven"))
            or type(record.get("release_complete_event_credit")) is not int
            or record["release_complete_event_credit"] != 0
            or source.get("original_result_host_frame") != event["original_result_frame"]
            or event["original_result_frame"] != 8353
            or source.get("original_next_bowl_entry_host_frame") != 8620
            or source.get("source_result_to_next_active_entry_frames") != 267
            or source.get("source_original_active_entry_sustained_eight_frames") is not True
            or source.get("native_next_course_entry_proven") is not False
            or source.get("release_complete_event_credit") != 0
            or not isinstance(source.get("samples"), dict)
            or set(source["samples"]) != {str(o) for o in offsets}):
        raise ValueError("incomplete original source next-Bowl identity or scope")
    rows = record.get("samples")
    if not isinstance(rows, list) or len(rows) != len(offsets):
        raise ValueError("missing actual eleven guest handoff samples")
    observed = {"movie": [], "original": [], "native": []}
    triplet, full_sram, full_wram, ranks = [], [], [], []
    raw_wram_differing_offsets, raw_wram_counts = [], []
    first = None
    for row, offset in zip(rows, offsets):
        source_row = source["samples"][str(offset)]
        if (not isinstance(row, dict) or not isinstance(source_row, dict)
                or row.get("offset_from_observed_zoo_result") != offset
                or row.get("original_movie") != source_row
                or source_row.get("original_movie_host_frame") != 8353 + offset
                or any(type(source_row.get(k)) is not int
                       for k in ("menu", "track", "in_race"))):
            raise ValueError("source movie handoff offset/frame tampered")
        original_movie = {k: source_row[k] for k in ("menu", "track", "in_race")}
        observed["movie"].append((offset, original_movie["track"] == 2
                                  and original_movie["in_race"] == 1))
        guests = row.get("fresh_guests")
        if not isinstance(guests, dict) or set(guests) != {"original", "native"}:
            raise ValueError("incomplete original/native handoff guests")
        for side, entry in (("original", report["reference_entry"]),
                            ("native", report["native_entry"])):
            current = guests[side]
            if not isinstance(current, dict):
                raise ValueError("missing fresh next-Bowl guest state")
            current_result = frames["reference_relative" if side == "original"
                                    else "native_relative"]
            if (any(type(current.get(k)) is not int
                    for k in ("menu", "track", "in_race"))
                    or type(current.get("actual_host_frame")) is not int
                    or current["actual_host_frame"] != entry + current_result + offset
                    or current.get("full_wram_bytes") != 131072
                    or any(not isinstance(current.get(k), str)
                           or not HEX256.fullmatch(current[k])
                           for k in ("wram_sha256", "sram_sha256"))
                    or not isinstance(current.get("source_earned_zoo_best_lap"), dict)
                    or any(type(current["source_earned_zoo_best_lap"].get(k)) is not int
                           for k in ("rank", "value_word", "holder_index"))
                    or type(current.get("record_checksum_stored")) is not int
                    or type(current.get("record_checksum_calculated")) is not int
                    or current.get("record_checksum_matches") is not
                    (current["record_checksum_stored"] ==
                     current["record_checksum_calculated"])):
                raise ValueError("bad actual guest handoff frame/WRAM/SRAM/record")
            observed[side].append((offset, current["track"] == 2
                                   and current["in_race"] == 1))
        name_equal = all(
            {k: guests[side][k] for k in ("menu", "track", "in_race")} ==
            original_movie for side in ("original", "native"))
        raw = row.get("original_native_full_wram_byte_difference")
        if (not isinstance(raw, dict)
                or raw.get("full_wram_bytes_per_guest") != 131072
                or raw.get("every_byte_compared") is not True
                or raw.get("excluded_byte_count") != 0
                or type(raw.get("differing_byte_count")) is not int
                or not 0 <= raw["differing_byte_count"] <= 131072
                or raw.get("original_wram_sha256") != guests["original"]["wram_sha256"]
                or raw.get("native_wram_sha256") != guests["native"]["wram_sha256"]
                or raw.get("byte_exact") is not (raw["differing_byte_count"] == 0)
                or raw["byte_exact"] is not (
                    guests["original"]["wram_sha256"] ==
                    guests["native"]["wram_sha256"])
                or raw.get("cpu_or_logic_tick_parity_proven") is not False
                or raw.get("release_complete_event_credit") != 0
                or row.get("triplet_named_states_equal") is not name_equal):
            raise ValueError("contradictory sampled full-WRAM or named handoff")
        same_sram = (guests["original"]["sram_sha256"] ==
                     guests["native"]["sram_sha256"])
        diff_count = row.get("battery_sram_differing_byte_count")
        first_bytes = row.get("battery_first_differences")
        if (type(diff_count) is not int or not 0 <= diff_count <= 8192
                or not isinstance(first_bytes, list)
                or len(first_bytes) != min(8, diff_count)
                or row.get("original_native_full_sram_equal") is not same_sram
                or same_sram is not (diff_count == 0)):
            raise ValueError("contradictory full 8192-byte SRAM pair")
        seen_offsets = set()
        for byte in first_bytes:
            if (not isinstance(byte, dict)
                    or type(byte.get("offset")) is not int
                    or not 0 <= byte["offset"] < 8192
                    or byte["offset"] in seen_offsets
                    or any(type(byte.get(k)) is not int
                           or not 0 <= byte[k] <= 255 for k in (
                               "original_byte", "native_byte"))
                    or byte["original_byte"] == byte["native_byte"]):
                raise ValueError("invalid actual SRAM byte difference receipt")
            seen_offsets.add(byte["offset"])
        if first is None and (not name_equal or not same_sram):
            first = offset
        triplet.append(name_equal)
        full_sram.append(same_sram)
        full_wram.append(raw["byte_exact"])
        if not raw["byte_exact"]:
            raw_wram_differing_offsets.append(offset)
        raw_wram_counts.append(raw["differing_byte_count"])
        ranks.append(all(
            guests[side]["source_earned_zoo_best_lap"] ==
            {"rank": 0, "value_word": 2510, "holder_index": 0}
            and guests[side]["record_checksum_matches"]
            for side in ("original", "native")))
    def bracket(entries: list) -> dict:
        previous = None
        for offset, active in entries:
            if active:
                return {
                    "last_observed_inactive_offset": (
                        previous[0] if previous and not previous[1] else None),
                    "first_observed_active_offset": offset,
                    "exact_observed_entry_offset": (
                        offset if previous and previous == (offset - 1, False)
                        else None)}
            previous = (offset, active)
        return {"last_observed_inactive_offset": (
                    previous[0] if previous and not previous[1] else None),
                "first_observed_active_offset": None,
                "exact_observed_entry_offset": None}
    brackets = {side: bracket(entries) for side, entries in observed.items()}
    if brackets["movie"]["exact_observed_entry_offset"] != 267:
        raise ValueError("original movie did not bracket genuine next Bowl at +267")
    source_entry, ref_entry, nat_entry = [
        brackets[k]["exact_observed_entry_offset"] for k in
        ("movie", "original", "native")]
    original_host = (report["reference_entry"] +
                     frames["reference_relative"] + ref_entry
                     if ref_entry is not None else None)
    native_host = (report["native_entry"] +
                   frames["native_relative"] + nat_entry
                   if nat_entry is not None else None)
    claims = {
        "original_source_entry_bracket": brackets["movie"],
        "fresh_reference_entry_bracket": brackets["original"],
        "fresh_native_entry_bracket": brackets["native"],
        "source_next_bowl_active_entry_offset": source_entry,
        "fresh_reference_next_bowl_entry_offset": ref_entry,
        "fresh_native_next_bowl_entry_offset": nat_entry,
        "reference_next_bowl_absolute_host_frame": original_host,
        "native_next_bowl_absolute_host_frame": native_host,
        "next_bowl_same_absolute_host_frame": (
            original_host is not None and native_host is not None
            and original_host == native_host),
        "next_bowl_entry_triple_equal": (
            source_entry == ref_entry == nat_entry),
        "all_triplet_named_states_equal": all(triplet),
        "all_original_native_full_sram_pairs_equal": all(full_sram),
        "all_original_native_full_wram_pairs_equal": all(full_wram),
        "zoo_rank0_2510_and_checksum_preserved_every_sample": all(ranks),
    }
    if any(record.get(key) != value for key, value in claims.items()):
        raise ValueError("contradictory original/native Bowl handoff summaries")
    clean = (claims["next_bowl_entry_triple_equal"]
             and claims["all_triplet_named_states_equal"]
             and claims["all_original_native_full_sram_pairs_equal"]
             and claims["zoo_rank0_2510_and_checksum_preserved_every_sample"])
    return {"status": ("bounded_source_handoff_agreement" if clean else
                       "sampled_progression_divergence"),
            "samples": len(offsets), "source_entry_offset": source_entry,
            "fresh_original_entry_offset": ref_entry,
            "fresh_native_entry_offset": nat_entry,
            "first_sampled_progression_difference_offset": first,
            "all_sampled_sram_pairs_equal": all(full_sram),
            "all_sampled_named_triplets_equal": all(triplet),
            "all_sampled_full_wram_pairs_equal": all(full_wram),
            "raw_wram_differing_sample_offsets": raw_wram_differing_offsets,
            "raw_wram_differing_byte_occurrences": sum(raw_wram_counts),
            "unsampled_frames_or_windows_disk_persistence_proven": False,
            "release_credit": 0}


def classify(case: str, producer_rc: int, producer_path: Path,
             plan: dict, producer_log: Path | None = None) -> dict:
    validate_plan(plan)
    ids = [row["id"] for row in plan["cases"]]
    if case not in ids:
        raise ValueError("case not selected by plan")
    row = {
        "schema": SCHEMA,
        "plan_sha256": plan["plan_sha256"],
        "source_sha": plan["source_sha"],
        "case": case,
        "course_id": CASES[case]["course_id"],
        "family": CASES[case]["family"],
        "producer_exit_code": producer_rc,
        "disposition": "producer_error",
        "release_credit": 0,
        "reason": None,
        "evidence": {},
    }
    if producer_rc not in (0, 1):
        row["reason"] = "producer process failed, was killed, or timed out"
        detail = producer_failure_reason(producer_log)
        if detail:
            row["reason"] += ": " + detail
        return row
    try:
        report = load_json(producer_path)
        comparison = report["comparison"]
        event = report["original_source_event"]
        if not isinstance(comparison, dict) or not isinstance(event, dict):
            raise ValueError("missing original event or comparison")
        if report.get("schema_version") != 1 or report.get("name") != case:
            raise ValueError("wrong producer schema or case")
        if report.get("course_id") != CASES[case]["course_id"] or \
                report.get("family") != CASES[case]["family"]:
            raise ValueError("wrong course/family identity")
        if report.get("native_backend") != "pinned-baldosa":
            raise ValueError("not the pinned independent-original/native route")
        if report.get("admission") != "investigative candidate; not a release-ledger pass":
            raise ValueError("producer admission contract changed")
        keys = ("rom_sha256", "original_movie_sha256", "native_executable_sha256",
                "reference_core_sha256", "input_sha256", "source_sram_sha256",
                "original_movie_window_sha256", "reference_script_sha256")
        if any(not isinstance(report.get(key), str) or
               not HEX256.fullmatch(report[key]) for key in keys):
            raise ValueError("incomplete producer provenance")
        if any(type(event.get(k)) is not int or event[k] < 0
               for k in ("original_entry_frame", "original_result_frame",
                         "source_active_frames_to_result")) or (
                event["original_result_frame"] - event["original_entry_frame"]
                != event["source_active_frames_to_result"]) or (
                event["source_active_frames_to_result"] <= 0):
            raise ValueError("original archived event entry/result interval is incomplete or contradictory")
        if (any(type(report.get(k)) is not int or report[k] < 0
                for k in ("reference_entry", "native_entry"))
                or type(report.get("native_frame_shift")) is not int
                or report["native_entry"] - report["reference_entry"]
                != report["native_frame_shift"]):
            raise ValueError("fresh reference/native entry and input shift disagree")
        frames = comparison.get("terminal_result_guest_frame")
        if not isinstance(frames, dict) or any(type(frames.get(k)) is not int
               or frames[k] < 0 for k in ("reference_relative", "native_relative")):
            raise ValueError("terminal frame evidence missing")
        match = comparison.get("terminal_result_frame_matched")
        strict = comparison.get("paired_event_candidate")
        if type(match) is not bool or type(strict) is not bool:
            raise ValueError("strict comparator fields missing")
        if match != (frames["reference_relative"] == frames["native_relative"]):
            raise ValueError("contradictory terminal-frame assertion")
        # Compare three *independently observed* race-relative durations.
        # Matching fresh guests never implies matching archived source movie.
        source_rel = event["source_active_frames_to_result"]
        source_original_phase = {
            "source_original_movie_relative": source_rel,
            "fresh_original_relative": frames["reference_relative"],
            "fresh_native_relative": frames["native_relative"],
            "fresh_original_minus_source_frames":
                frames["reference_relative"] - source_rel,
            "fresh_native_minus_source_frames":
                frames["native_relative"] - source_rel,
            "three_relative_durations_equal":
                source_rel == frames["reference_relative"] ==
                frames["native_relative"],
            "independent_original_movie_and_fresh_guest_clocks_not_rebased": True,
            "continuous_original_to_fresh_equivalence_proven": False,
            "release_credit": 0,
        }
        strict_gates = strict_producer_gate_audit(comparison, match)
        if strict and (not match or producer_rc != 0):
            raise ValueError("strict outcome and producer exit disagree")
        if not strict and producer_rc == 0 and not comparison.get(
                "diagnostic_exit_success_without_full_event_parity", False):
            raise ValueError("non-strict result returned success without diagnostic contract")
        continuation = classify_postresult_followthrough(report, event, frames)
        next_bowl = classify_zoo_next_bowl(report, event, frames)
        row["disposition"] = "strict_candidate" if strict else "strict_divergence"
        row["reason"] = ("strict paired-event candidate; NOT an independently "
                         "adjudicated course pass" if strict else
                         "strict original/native paired-event comparator is negative")
        if not source_original_phase["three_relative_durations_equal"]:
            row["reason"] += (
                "; distinct archived source-movie vs fresh guest race-relative "
                f"result durations (movie +{source_rel}, "
                f"fresh original +{frames['reference_relative']}, "
                f"native +{frames['native_relative']}); "
                "source/movie timing equivalence NOT established")
        if continuation["status"] == "sampled_named_divergence":
            row["reason"] += (
                "; independently recorded post-result named-state difference "
                f"at result-relative +{continuation['first_named_divergence_offset']}; "
                "not a complete-event lifecycle pass")
        if next_bowl["raw_wram_differing_sample_offsets"]:
            row["reason"] += (
                "; unmasked 128KiB WRAM residual at result offsets " +
                ",".join("+" + str(n) for n in
                         next_bowl["raw_wram_differing_sample_offsets"]) +
                " (" + str(next_bowl["raw_wram_differing_byte_occurrences"]) +
                " differing-byte occurrences); not waived")
        if next_bowl["status"] == "sampled_progression_divergence":
            row["reason"] += (
                "; authenticated next-Bowl entry/state/SRAM/record evidence "
                f"(source +{next_bowl['source_entry_offset']}, "
                f"fresh original +{next_bowl['fresh_original_entry_offset']}, "
                f"native +{next_bowl['fresh_native_entry_offset']}); "
                "post-result lifecycle BLOCKED, not a complete event")
        row["evidence"] = {
            "next_bowl_bounded": next_bowl,
            "post_result_bounded": continuation,
            "source_original_movie_vs_fresh_guest_result_phase": source_original_phase,
            "producer_sha256": hashlib.sha256(producer_path.read_bytes()).hexdigest(),
            "rom_sha256": report["rom_sha256"],
            "movie_sha256": report["original_movie_sha256"],
            "core_sha256": report["reference_core_sha256"],
            "native_sha256": report["native_executable_sha256"],
            "input_sha256": report["input_sha256"],
            "source_sram_sha256": report["source_sram_sha256"],
            "original_movie_window_sha256": report["original_movie_window_sha256"],
            "reference_script_sha256": report["reference_script_sha256"],
            "original_movie_entry_frame": event["original_entry_frame"],
            "original_movie_result_frame": event["original_result_frame"],
            "reference_entry_frame": report["reference_entry"],
            "native_entry_frame": report["native_entry"],
            "native_frame_shift": report["native_frame_shift"],
            "original_event_frames": event["source_active_frames_to_result"],
            "terminal_guest_relative_frames": frames,
            "terminal_frame_matched": match,
            "strict_candidate": strict,
            "strict_producer_gate_audit": strict_gates,
            "first_sample_disagreement": comparison.get("first_sample_disagreement"),
        }
    except (OSError, ValueError, KeyError, TypeError) as exc:
        row["reason"] = "invalid/missing producer evidence: " + str(exc)
        detail = producer_failure_reason(producer_log)
        if detail:
            row["reason"] += "; cause: " + detail
    return row


def aggregate(plan: dict, results_dir: Path) -> tuple[dict, str]:
    validate_plan(plan)
    results = []
    expected = {row["id"] for row in plan["cases"]}
    unexpected = []
    for path in sorted(results_dir.glob("qa01-campaign-case-*/case-result.json")):
        case_dir = path.parent.name
        if case_dir.removeprefix("qa01-campaign-case-") not in expected:
            unexpected.append(case_dir)
    for case in [row["id"] for row in plan["cases"]]:
        path = results_dir / ("qa01-campaign-case-" + case) / "case-result.json"
        try:
            row = load_json(path)
            if (row.get("schema") != SCHEMA or row.get("case") != case or
                row.get("course_id") != CASES[case]["course_id"] or
                row.get("source_sha") != plan["source_sha"] or
                row.get("plan_sha256") != plan["plan_sha256"] or
                type(row.get("release_credit")) is not int or
                row.get("release_credit") != 0 or
                row.get("disposition") not in
                    ("strict_candidate", "strict_divergence", "producer_error")):
                raise ValueError("case identity, schema or status mismatch")
            if row["disposition"] != "producer_error":
                ev = row.get("evidence")
                if not isinstance(ev, dict) or any(
                    not isinstance(ev.get(k), str) or
                    not HEX256.fullmatch(ev[k]) for k in (
                        "producer_sha256", "rom_sha256", "movie_sha256",
                        "core_sha256", "native_sha256", "input_sha256",
                        "source_sram_sha256", "original_movie_window_sha256",
                        "reference_script_sha256")
                ):
                    raise ValueError("incomplete case hash provenance")
                if (any(type(ev.get(k)) is not int or ev[k] < 0
                        for k in ("original_movie_entry_frame",
                                  "original_movie_result_frame",
                                  "original_event_frames",
                                  "reference_entry_frame", "native_entry_frame"))
                        or type(ev.get("native_frame_shift")) is not int
                        or ev["original_movie_result_frame"] - ev["original_movie_entry_frame"]
                        != ev["original_event_frames"]
                        or ev["original_event_frames"] <= 0
                        or ev["native_entry_frame"] - ev["reference_entry_frame"]
                        != ev["native_frame_shift"]):
                    raise ValueError("case original/native start and shift identity inconsistent")
                source_phase = ev.get("source_original_movie_vs_fresh_guest_result_phase")
                source_rel = ev["original_event_frames"]
                fresh_rel = ev.get("terminal_guest_relative_frames", {})
                if (not isinstance(source_phase, dict)
                        or not isinstance(fresh_rel, dict)
                        or set(source_phase) != {
                            "source_original_movie_relative",
                            "fresh_original_relative",
                            "fresh_native_relative",
                            "fresh_original_minus_source_frames",
                            "fresh_native_minus_source_frames",
                            "three_relative_durations_equal",
                            "independent_original_movie_and_fresh_guest_clocks_not_rebased",
                            "continuous_original_to_fresh_equivalence_proven",
                            "release_credit"}
                        or any(type(source_phase.get(k)) is not int for k in (
                            "source_original_movie_relative",
                            "fresh_original_relative",
                            "fresh_native_relative",
                            "fresh_original_minus_source_frames",
                            "fresh_native_minus_source_frames",
                            "release_credit"))
                        or source_phase["release_credit"] != 0
                        or any(type(fresh_rel.get(k)) is not int for k in (
                            "reference_relative", "native_relative"))
                        or source_phase["source_original_movie_relative"] != source_rel
                        or source_phase["fresh_original_relative"] != fresh_rel["reference_relative"]
                        or source_phase["fresh_native_relative"] != fresh_rel["native_relative"]
                        or source_phase["fresh_original_minus_source_frames"] !=
                            fresh_rel["reference_relative"] - source_rel
                        or source_phase["fresh_native_minus_source_frames"] !=
                            fresh_rel["native_relative"] - source_rel
                        or type(source_phase.get("three_relative_durations_equal")) is not bool
                        or source_phase["three_relative_durations_equal"] is not (
                            source_rel == fresh_rel["reference_relative"] ==
                            fresh_rel["native_relative"])
                        or source_phase.get(
                            "independent_original_movie_and_fresh_guest_clocks_not_rebased"
                        ) is not True
                        or source_phase.get(
                            "continuous_original_to_fresh_equivalence_proven"
                        ) is not False):
                    raise ValueError("missing/contradictory three-clock source result receipts")
                follow = ev.get("post_result_bounded")
                if (not isinstance(follow, dict)
                        or follow.get("status") not in (
                            "not_observed", "sampled_named_divergence",
                            "six_sample_triplet_named_agreement")
                        or type(follow.get("release_credit")) is not int
                        or follow["release_credit"] != 0
                        or type(follow.get("samples")) is not int
                        or follow["samples"] not in (0, len(FOLLOWTHROUGH_OFFSETS))
                        or (follow["status"] == "not_observed")
                        != (follow["samples"] == 0)
                        or (follow["status"] == "sampled_named_divergence")
                        != (follow.get("first_named_divergence_offset") is not None)
                        or (follow.get("first_named_divergence_offset") is not None
                            and follow["first_named_divergence_offset"]
                            not in FOLLOWTHROUGH_OFFSETS)):
                    raise ValueError("missing or malformed bounded post-result disposition")
                handoff = ev.get("next_bowl_bounded")
                if (not isinstance(handoff, dict)
                        or handoff.get("status") not in (
                            "not_observed", "bounded_source_handoff_agreement",
                            "sampled_progression_divergence")
                        or type(handoff.get("release_credit")) is not int
                        or handoff["release_credit"] != 0
                        or type(handoff.get("samples")) is not int
                        or handoff["samples"] not in (0, len(ZOO_BOWL_OFFSETS))
                        or (handoff["status"] == "not_observed") != (
                            handoff["samples"] == 0)
                        or (handoff["status"] == "not_observed" and
                            any(handoff.get(k) is not None for k in (
                                "source_entry_offset",
                                "fresh_original_entry_offset",
                                "fresh_native_entry_offset",
                                "first_sampled_progression_difference_offset")))
                        or (handoff["status"] != "not_observed" and
                            (row["case"] != "zoom-zoo" or
                             handoff.get("source_entry_offset") != 267 or
                             type(handoff.get("all_sampled_sram_pairs_equal")) is not bool or
                             type(handoff.get("all_sampled_named_triplets_equal")) is not bool
                             or type(handoff.get("unsampled_frames_or_windows_disk_persistence_proven")) is not bool
                             or handoff["unsampled_frames_or_windows_disk_persistence_proven"]
                             or (handoff["status"] == "bounded_source_handoff_agreement"
                                 and (handoff.get("fresh_original_entry_offset") != 267
                                      or handoff.get("fresh_native_entry_offset") != 267
                                      or not handoff["all_sampled_sram_pairs_equal"]
                                      or not handoff["all_sampled_named_triplets_equal"]))))):
                    raise ValueError("missing or contradictory next-Bowl handoff verdict")
                if (type(handoff.get("raw_wram_differing_byte_occurrences")) is not int
                        or handoff["raw_wram_differing_byte_occurrences"] < 0
                        or not isinstance(handoff.get("raw_wram_differing_sample_offsets"), list)
                        or any(type(n) is not int or n not in ZOO_BOWL_OFFSETS
                               for n in handoff["raw_wram_differing_sample_offsets"])
                        or handoff["raw_wram_differing_sample_offsets"] != sorted(
                            set(handoff["raw_wram_differing_sample_offsets"]))
                        or (handoff["status"] == "not_observed"
                            and (handoff.get("all_sampled_full_wram_pairs_equal") is not None
                                 or handoff["raw_wram_differing_sample_offsets"]
                                 or handoff["raw_wram_differing_byte_occurrences"]))
                        or (handoff["status"] != "not_observed"
                            and (type(handoff.get("all_sampled_full_wram_pairs_equal")) is not bool
                                 or handoff["all_sampled_full_wram_pairs_equal"] is not (
                                     not handoff["raw_wram_differing_sample_offsets"])
                                 or (bool(handoff["raw_wram_differing_byte_occurrences"]) is not
                                     bool(handoff["raw_wram_differing_sample_offsets"]))))):
                    raise ValueError("missing or contradictory raw WRAM handoff residual")
                frames = ev.get("terminal_guest_relative_frames")
                if not isinstance(frames, dict) or any(
                    type(frames.get(k)) is not int or frames[k] < 0 for k in
                    ("reference_relative", "native_relative")
                ):
                    raise ValueError("case terminal frame evidence invalid")
                match = frames["reference_relative"] == frames["native_relative"]
                gate_audit = ev.get("strict_producer_gate_audit")
                if (not isinstance(gate_audit, dict)
                        or not isinstance(gate_audit.get("gates"), dict)
                        or set(gate_audit["gates"]) != set(STRICT_PRODUCER_GATES) | {
                            "no_sampled_state_disagreement",
                            "same_guest_relative_result_onset"}
                        or any(type(value) is not bool
                               for value in gate_audit["gates"].values())
                        or gate_audit["gates"]["same_guest_relative_result_onset"] is not match
                        or type(gate_audit.get("recomputed_candidate")) is not bool
                        or gate_audit["recomputed_candidate"] is not all(
                            gate_audit["gates"].values())
                        or gate_audit["recomputed_candidate"] is not (
                            row["disposition"] == "strict_candidate")):
                    raise ValueError("invalid or contradictory strict producer gate audit")
                if (type(ev.get("terminal_frame_matched")) is not bool or
                    ev["terminal_frame_matched"] != match or
                    type(ev.get("strict_candidate")) is not bool or
                    ev["strict_candidate"] != (row["disposition"] == "strict_candidate") or
                    (row["disposition"] == "strict_candidate" and
                     (not match or row.get("producer_exit_code") != 0))):
                    raise ValueError("contradictory strict candidate receipt")
            if row["disposition"] == "producer_error":
                row["reason"] = str(row.get("reason") or "producer error")
        except (OSError, ValueError, TypeError) as exc:
            row = {
                "case": case, "course_id": CASES[case]["course_id"],
                "disposition": "missing_evidence",
                "reason": str(exc), "release_credit": 0,
            }
        results.append(row)
    # The embedded SRAM also comes from the same archived source movie:
    # cross-shard source boot differences invalidate a pooled experiment.
    # Event-relative input windows/scripts and native entry offsets vary.
    identity_keys = ("rom_sha256", "movie_sha256", "core_sha256",
                     "native_sha256", "source_sram_sha256")
    baseline = None
    for row in results:
        if row["disposition"] not in ("strict_candidate", "strict_divergence"):
            continue
        identity = tuple(row["evidence"][key] for key in identity_keys)
        if baseline is None:
            baseline = identity
        elif identity != baseline:
            row["disposition"] = "missing_evidence"
            row["reason"] = "cross-case ROM/movie/reference/native identity mismatch"
            row["release_credit"] = 0
    totals = {
        key: sum(row["disposition"] == key for row in results)
        for key in ("strict_candidate", "strict_divergence",
                    "producer_error", "missing_evidence")
    }
    valid = (not unexpected and
             totals["producer_error"] == 0 and totals["missing_evidence"] == 0)
    blocked_handoffs = sum(
        row.get("evidence", {}).get("next_bowl_bounded", {}).get("status")
        == "sampled_progression_divergence" for row in results)
    raw_wram_handoffs = sum(
        bool(row.get("evidence", {}).get("next_bowl_bounded", {}).get(
            "raw_wram_differing_sample_offsets")) for row in results)
    source_movie_deltas = sum(
        row.get("evidence", {}).get(
            "source_original_movie_vs_fresh_guest_result_phase", {}
        ).get("three_relative_durations_equal") is False for row in results)
    report = {
        "schema": SCHEMA, "plan_sha256": plan["plan_sha256"],
        "source_sha": plan["source_sha"], "selected_cases": len(expected),
        "completed": totals["strict_candidate"] + totals["strict_divergence"],
        "counts": totals, "unexpected_artifacts": unexpected,
        "transport_complete": valid, "release_admissions": 0,
        "bounded_next_bowl_progression_divergences": blocked_handoffs,
        "bounded_next_bowl_unmasked_wram_residual_cases": raw_wram_handoffs,
        "source_movie_to_fresh_result_duration_difference_cases": source_movie_deltas,
        "results": results,
        "release_note": ("All observations are investigative. Independent QA "
                         "adjudication and the release ledger remain unchanged."),
    }
    lines = [
        "# QA-01 unattended event campaign",
        "",
        "Source SHA: " + plan["source_sha"],
        "Plan SHA-256: " + plan["plan_sha256"],
        "",
        "| Case | Outcome | Evidence |",
        "| --- | --- | --- |",
    ]
    for row in results:
        lines.append("| " + row["case"] + " | " + row["disposition"] +
                     " | " + str(row.get("reason") or "").replace("|", "/")[:160] + " |")
    lines += [
        "",
        "Completed investigative cases: " + str(report["completed"]) +
        "/" + str(len(expected)),
        "Missing/error: " + str(totals["missing_evidence"] +
                               totals["producer_error"]),
        "Transport complete: " + str(valid),
        "Observed source-authentic next-Bowl progression blockers: " +
        str(blocked_handoffs),
        "Next-Bowl cases with unmasked 128KiB WRAM residuals: " +
        str(raw_wram_handoffs),
        "Cases with source-movie versus fresh-guest relative result offset: " +
        str(source_movie_deltas),
        "**USA course release admissions: 0.** A strict candidate is not a reviewed L4 pass.",
        "Physical Windows or player-hardware evidence: not exercised.",
    ]
    return report, "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="mode", required=True)
    make = sub.add_parser("plan")
    make.add_argument("--selected", choices=["all", *CASES], default="all")
    make.add_argument("--source-sha", required=True)
    make.add_argument("--out", required=True, type=Path)
    make.add_argument("--gha-output", type=Path)
    make.add_argument("--summary", type=Path)
    check = sub.add_parser("classify")
    check.add_argument("--plan", required=True, type=Path)
    check.add_argument("--case", required=True, choices=list(CASES))
    check.add_argument("--producer-exit", required=True, type=int)
    check.add_argument("--producer-report", required=True, type=Path)
    check.add_argument("--producer-log", type=Path)
    check.add_argument("--out", required=True, type=Path)
    agg = sub.add_parser("aggregate")
    agg.add_argument("--plan", required=True, type=Path)
    agg.add_argument("--results-dir", required=True, type=Path)
    agg.add_argument("--out", required=True, type=Path)
    agg.add_argument("--summary", required=True, type=Path)
    args = p.parse_args(argv)
    if args.mode == "plan":
        plan = make_plan(args.selected, args.source_sha)
        write_json(args.out, plan)
        if args.gha_output:
            with args.gha_output.open("a", encoding="utf-8") as fh:
                fh.write("matrix=" + canonical(plan["matrix"]) + "\n")
        if args.summary:
            args.summary.write_text(
                "# QA-01 campaign plan\n\n" +
                "Selected: " + ", ".join(row["id"] for row in plan["cases"]) +
                "\n\nSHA: " + plan["plan_sha256"] +
                "\n\nManual investigative execution only. No automatic course credit.\n",
                encoding="utf-8")
        return 0
    plan = load_json(args.plan)
    if args.mode == "classify":
        row = classify(args.case, args.producer_exit,
                       args.producer_report, plan, args.producer_log)
        write_json(args.out, row)
        # A failed producer is a failed case job. Artifacts and aggregate
        # still run, but a valid scientific strict divergence is not a
        # CI infrastructure failure.
        return 1 if row["disposition"] == "producer_error" else 0
    report, summary = aggregate(plan, args.results_dir)
    write_json(args.out, report)
    args.summary.write_text(summary, encoding="utf-8")
    return 0 if report["transport_complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
