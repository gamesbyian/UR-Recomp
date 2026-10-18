#!/usr/bin/env python3
"""Independent QA-01 raw-artifact review of the Bowl -> Switcher witness.

Consumes genuine retained source/guest files, never runs or modifies either
game, invents inputs, normalizes clocks, or awards a USA course pass. Missing
raw WRAM/SRAM is an INVALID review, not a gameplay divergence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA = "ur-qa01-bowl-switcher-raw-archive-audit/1"
PRODUCER_SCHEMA = "UR-QA01-BOWL-TO-AUTHENTIC-SWITCHER-NEXT-RACE/1"
OFFSETS = (334, 338, 339, 340, 341, 342, 343, 344, 345, 346, 349, 354)
SHA = re.compile(r"[0-9a-f]{64}\Z")
SOURCE_RESULT = 11985
SOURCE_NEXT = 12327


def must(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def read_exact(path: Path, length: int) -> bytes:
    must(path.is_file() and not path.is_symlink(), "missing/symlinked captured image: " + str(path))
    data = path.read_bytes()
    must(len(data) == length, "short or oversized original guest image: " + str(path))
    return data


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_logged_frame(log: str, tag: str) -> int:
    matches = re.findall(r"script f=(\d+) dump " + re.escape(tag) + r"(?=\s|$)", log)
    must(len(matches) == 1, "missing/ambiguous real guest dump acknowledgment: " + tag)
    return int(matches[0])


def active(row: dict) -> bool:
    return type(row.get("track")) is int and row["track"] == 3 and (
        type(row.get("in_race")) is int and row["in_race"] == 1)


def bracket(samples: list[dict], side: str) -> dict:
    """Reconstruct the *first* sampled active entry without guessing in gaps."""
    last = None
    for row in samples:
        offset = row["offset_from_observed_bowl_result"]
        observed = row["original_movie"] if side == "movie" else row["fresh_guests"][side]
        on = active(observed)
        if on:
            exact = offset if last and last[0] == offset - 1 and not last[1] else None
            return {"last_observed_inactive_offset": last[0] if last and not last[1] else None,
                    "first_observed_active_offset": offset,
                    "exact_observed_entry_offset": exact}
        last = (offset, on)
    return {"last_observed_inactive_offset": last[0] if last else None,
            "first_observed_active_offset": None, "exact_observed_entry_offset": None}


def raw_wram_pair(original: bytes, native: bytes) -> dict:
    """Independently recalculate every byte, first/last witness and page count."""
    must(len(original) == len(native) == 131072, "invalid full-WRAM length")
    address = lambda i: f"{0x7E + (i >> 16):02X}:{i & 0xFFFF:04X}"
    first, count, first_at, last_at, pages = [], 0, None, None, {}
    for i, (a, b) in enumerate(zip(original, native)):
        if a == b:
            continue
        if first_at is None:
            first_at = i
        last_at = i
        count += 1
        page = i >> 8
        pages[page] = pages.get(page, 0) + 1
        if len(first) < 24:
            first.append({"snes_address": address(i), "wram_offset": i,
                          "original_byte": a, "native_byte": b})
    return {
        "full_wram_bytes_per_guest": 131072,
        "every_byte_compared": True,
        "excluded_byte_count": 0,
        "differing_byte_count": count,
        "byte_exact": count == 0,
        "first_differing_address": address(first_at) if first_at is not None else None,
        "last_differing_address": address(last_at) if last_at is not None else None,
        "first_24_differences": first,
        "changed_256_byte_pages": [
            {"page_start": address(p << 8), "differing_bytes": pages[p]}
            for p in sorted(pages)],
        "original_wram_sha256": digest(original),
        "native_wram_sha256": digest(native),
        "cpu_or_logic_tick_parity_proven": False,
        "release_complete_event_credit": 0,
    }


def bowl_rank0(battery: bytes) -> tuple[dict, bool]:
    must(len(battery) == 8192, "short SRAM")
    word = lambda off: int.from_bytes(battery[off:off + 2], "little")
    stored, calculated = word(0x054E), sum(
        word(0x0422 + 2 * i) for i in range(150)) & 0xFFFF
    return ({"rank": 0, "value_word": word(0x0426),
             "holder_index": battery[0x0552]}, stored == calculated)


def audit(root: Path) -> dict:
    """Verify genuine per-offset raw captures against the author's report."""
    report_path = root / "bowl-report.json"
    must(report_path.is_file() and not report_path.is_symlink(),
         "missing original producer-report JSON")
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes)
    must(isinstance(report, dict) and report.get("name") == "bowl" and
         report.get("course_id") == "course:03" and
         report.get("family") == "stunt" and
         report.get("native_backend") == "pinned-baldosa" and
         report.get("admission") == "investigative candidate; not a release-ledger pass",
         "unexpected original/native Bowl event identity")
    for key in ("rom_sha256", "original_movie_sha256", "source_sram_sha256",
                "input_sha256", "native_executable_sha256", "reference_core_sha256",
                "reference_script_sha256", "original_movie_window_sha256"):
        must(isinstance(report.get(key), str) and SHA.fullmatch(report[key]) is not None,
             "missing exact immutable input/executable identity: " + key)
    event = report.get("original_source_event")
    must(isinstance(event, dict) and event.get("original_entry_frame") == 8620 and
         event.get("original_result_frame") == SOURCE_RESULT and
         event.get("source_active_frames_to_result") == 3365,
         "noncanonical executed 2014 Bowl source event")
    comparison = report.get("comparison")
    must(isinstance(comparison, dict) and
         type(comparison.get("paired_event_candidate")) is bool and
         isinstance(comparison.get("terminal_result_guest_frame"), dict),
         "missing original/native event outcome")
    clocks = comparison["terminal_result_guest_frame"]
    for key in ("reference_relative", "native_relative"):
        must(type(clocks.get(key)) is int and clocks[key] > 0,
             "invalid independently observed result clock: " + key)
    same_duration = clocks["reference_relative"] == clocks["native_relative"]
    must(comparison.get("terminal_result_frame_matched") is same_duration and
         (not comparison["paired_event_candidate"] or same_duration),
         "strict event result claims contradict separate guest clocks")
    for key in ("reference_entry", "native_entry"):
        must(type(report.get(key)) is int and report[key] >= 0,
             "invalid independently observed entry clock: " + key)
    must(report.get("native_frame_shift") == report["native_entry"] - report["reference_entry"],
         "native input/entry shift differs from genuine guest frame calibration")

    handoff = report.get("bowl_next_switcher_handoff")
    must(isinstance(handoff, dict) and handoff.get("schema") == PRODUCER_SCHEMA and
         handoff.get("source_original_result_frame") == SOURCE_RESULT and
         handoff.get("source_original_next_switcher_frame") == SOURCE_NEXT and
         handoff.get("source_next_switcher_entry_offset") == 342 and
         handoff.get("sample_offsets") == list(OFFSETS) and
         handoff.get("source_controller_masks_modified") is False and
         handoff.get("original_native_clocks_unrebased") is True and
         handoff.get("full_cpu_spc_logic_tick_equivalence_proven") is False and
         handoff.get("shipping_windows_candidate_proven") is False and
         handoff.get("cold_process_disk_persistence_proven") is False and
         type(handoff.get("release_complete_event_credit")) is int and
         handoff["release_complete_event_credit"] == 0,
         "invalid Bowl handoff identity or over-promotional scope")
    rows = handoff.get("samples")
    must(isinstance(rows, list) and len(rows) == len(OFFSETS),
         "Bowl report missing genuine complete 12-offset handoff")
    source = event.get("source_next_switcher")
    must(isinstance(source, dict) and source.get("source_result_host_frame") == SOURCE_RESULT and
         source.get("source_next_switcher_entry_host_frame") == SOURCE_NEXT and
         source.get("source_active_eight_consecutive_frames") is True and
         source.get("source_result_to_next_active_entry_frames") == 342 and
         source.get("source_controller_masks_modified") is False and
         source.get("release_complete_event_credit") == 0 and
         isinstance(source.get("samples"), dict) and
         set(source["samples"]) == {str(x) for x in OFFSETS},
         "source-2014 handoff claim missing or invalid")

    base = root / "bowl" / "replay"
    logs = {}
    for side in ("reference", "native"):
        path = base / f"{side}.log"
        must(path.is_file() and not path.is_symlink(), "missing original replay log: " + str(path))
        logs[side] = path.read_text(encoding="utf-8", errors="replace")
    all_sram, all_wram, all_named, all_record = [], [], [], []
    different_offsets = []
    checked = []
    for position, offset in enumerate(OFFSETS):
        row = rows[position]
        must(isinstance(row, dict) and
             row.get("offset_from_observed_bowl_result") == offset,
             "reordered/missing guest handoff capture")
        source_row = source["samples"][str(offset)]
        movie = row.get("original_movie")
        must(movie == source_row and isinstance(movie, dict) and
             movie.get("original_movie_host_frame") == SOURCE_RESULT + offset and
             all(type(movie.get(k)) is int for k in ("menu", "track", "in_race")),
             "raw original source frame/capture mismatch")
        guests = row.get("fresh_guests")
        must(isinstance(guests, dict) and set(guests) == {"original", "native"},
             "missing original/native snapshot")
        raw = {}
        batteries = {}
        rank_valid = []
        for side, folder, log_name, expected in (
            ("original", "ref", "reference", report["reference_entry"] + clocks["reference_relative"] + offset),
            ("native", "native", "native", report["native_entry"] + clocks["native_relative"] + offset)):
            tag = f"bowl-next-switcher-{offset:03d}"
            logged = read_logged_frame(logs[log_name], tag)
            must(logged == expected, "independent guest frame receipt mismatch: " + side + "/" + tag)
            guest = guests[side]
            must(isinstance(guest, dict) and guest.get("actual_host_frame") == expected,
                 "report guest host frame differs from executed log")
            raw[side] = read_exact(base / folder / f"{tag}.wram.bin", 131072)
            batteries[side] = read_exact(base / folder / f"{tag}.sram.bin", 8192)
            rank, good_checksum = bowl_rank0(batteries[side])
            must(guest.get("menu") == raw[side][0x9F] and
                 guest.get("track") == raw[side][0xCE] and
                 guest.get("in_race") == raw[side][0x313] and
                 guest.get("full_wram_bytes") == 131072 and
                 guest.get("wram_sha256") == digest(raw[side]) and
                 guest.get("full_sram_bytes") == 8192 and
                 guest.get("sram_sha256") == digest(batteries[side]) and
                 guest.get("source_earned_bowl_rank0") == rank and
                 guest.get("record_table_checksum_matches") is good_checksum,
                 "authentic raw WRAM/SRAM differs from claimed guest state/record: " + side)
            rank_valid.append(rank["value_word"] == 764 and good_checksum)
        rawpair = raw_wram_pair(raw["original"], raw["native"])
        must(row.get("full_wram_byte_difference") == rawpair,
             "unmasked 128KiB original/native byte census differs from raw captures")
        same_sram = batteries["original"] == batteries["native"]
        same_named = all(
            {k: guests[side][k] for k in ("menu", "track", "in_race")} ==
            {k: movie[k] for k in ("menu", "track", "in_race")}
            for side in ("original", "native"))
        must(row.get("full_sram_pair_equal") is same_sram and
             row.get("triplet_named_states_equal") is same_named,
             "raw SRAM or original/native/movie state contradicts report")
        all_sram.append(same_sram)
        all_wram.append(rawpair["byte_exact"])
        all_named.append(same_named)
        all_record.append(all(rank_valid))
        if not rawpair["byte_exact"]:
            different_offsets.append(offset)
        checked.append({"offset": offset, "original_host_frame":
                        guests["original"]["actual_host_frame"],
                        "native_host_frame": guests["native"]["actual_host_frame"],
                        "unmasked_wram_differing_bytes": rawpair["differing_byte_count"],
                        "full_sram_equal": same_sram,
                        "triplet_named_equal": same_named,
                        "earned_bowl_764_valid_both": all(rank_valid)})
    brackets = {name: bracket(rows, name) for name in ("movie", "original", "native")}
    must(brackets["movie"]["exact_observed_entry_offset"] == 342,
         "source movie sampled active edge not +342")
    original_start = brackets["original"]["exact_observed_entry_offset"]
    native_start = brackets["native"]["exact_observed_entry_offset"]
    original_abs = (report["reference_entry"] + clocks["reference_relative"] + original_start
                    if original_start is not None else None)
    native_abs = (report["native_entry"] + clocks["native_relative"] + native_start
                  if native_start is not None else None)
    expected = {
        "original_movie_entry_bracket": brackets["movie"],
        "fresh_reference_entry_bracket": brackets["original"],
        "fresh_native_entry_bracket": brackets["native"],
        "fresh_reference_entry_offset": original_start,
        "fresh_native_entry_offset": native_start,
        "fresh_reference_entry_absolute_host_frame": original_abs,
        "fresh_native_entry_absolute_host_frame": native_abs,
        "same_absolute_host_entry": original_abs is not None and original_abs == native_abs,
        "all_three_entry_offsets_equal": original_start == native_start == 342,
        "all_triplet_named_states_equal": all(all_named),
        "all_full_8192_sram_pairs_equal": all(all_sram),
        "all_full_128k_wram_pairs_equal": all(all_wram),
        "full_wram_differing_sample_offsets": different_offsets,
        "source_earned_bowl_rank0_764_and_checksum_every_sample": all(all_record),
    }
    for key, value in expected.items():
        must(handoff.get(key) == value, "producer handoff aggregate contradicted by actual raw evidence: " + key)
    bounded_positive = (comparison["paired_event_candidate"] and
                        expected["all_three_entry_offsets_equal"] and
                        expected["all_triplet_named_states_equal"] and
                        expected["all_full_8192_sram_pairs_equal"] and
                        expected["all_full_128k_wram_pairs_equal"] and
                        expected["source_earned_bowl_rank0_764_and_checksum_every_sample"])
    return {
        "schema": SCHEMA, "case": "bowl", "producer_sha256": digest(report_bytes),
        "rom_sha256": report["rom_sha256"],
        "movie_sha256": report["original_movie_sha256"],
        "native_sha256": report["native_executable_sha256"],
        "source_sha_required_from_actions": True,
        "observed_raw_wram_sram_pairs": len(rows),
        "raw_unmasked_wram_differing_sample_offsets": different_offsets,
        "raw_unmasked_wram_differing_byte_occurrences":
            sum(x["unmasked_wram_differing_bytes"] for x in checked),
        "bounded_outcome": ("all_sampled_requirements_satisfied_not_admission"
                            if bounded_positive else "verified_bounded_difference_or_missing_lifecycle"),
        "source_eight_frame_continuity_rechecked_from_raw": False,
        "shipping_executable_and_cold_disk_proven": False,
        "independent_complete_usa_event_adjudication": "HOLD",
        "accepted_event_credit": 0,
        "checked_samples": checked,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        result = audit(args.artifact_root)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(2, f"QA01_BOWL_RAW_ARCHIVE_INVALID: {exc}\n")
    data = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(data, encoding="utf-8")
    print(data, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
