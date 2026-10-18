#!/usr/bin/env python3
"""Independent, read-only Dragster->Zoo primary guest-memory archive audit.

The authoring producer is not imported. Every retained WRAM/SRAM byte is
reopened; a genuine strict negative is evidence, not an artifact failure.
This is not a guest emulator, a clock rephaser, or USA event acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from qa01_bowl_handoff_raw_archive_audit import (
    digest, read_exact, read_logged_frame, raw_wram_pair,
)

SCHEMA = "UR-QA01-INDEPENDENT-DRAGSTER-ZOO-RAW-ARCHIVE/1"
PRODUCER_SCHEMA = "UR-QA01-DRAGSTER-TO-ZOO-FRESH-GUEST-PROGRESSION/1"
OFFSETS = (304, 308, 312, 314, 315, 316, 317, 318, 319, 320, 321, 324, 328, 336)
MOVIE_RESULT, MOVIE_ZOO = 2874, 3190
NAME_ADDR = {"menu": 0x9F, "track": 0xCE, "in_race": 0x313, "tour_row": 0xD0}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def real_dragster_record(sram: bytes) -> tuple[list[dict], bool]:
    require(len(sram) == 8192, "not a complete 8KiB SRAM image")
    word = lambda at: int.from_bytes(sram[at:at + 2], "little")
    ranks = [
        {"rank": rank, "value_word": word(0x422 + 100 * rank),
         "holder_index": sram[0x550 + 50 * rank]}
        for rank in range(3)
    ]
    return ranks, word(0x54E) == sum(word(0x422 + 2 * i) for i in range(150)) & 0xFFFF


def active_zoo(row: dict) -> bool:
    return all(type(row.get(k)) is int for k in ("track", "in_race", "tour_row")) and (
        row["track"], row["in_race"], row["tour_row"]) == (1, 1, 0)


def entry_bracket(samples: list[dict], side: str) -> dict:
    previous = None
    for row in samples:
        off = row["offset"]
        state = row["movie"] if side == "movie" else row[side]
        on = active_zoo(state)
        if on:
            return {
                "first_observed_active_offset": off,
                "last_observed_inactive_offset":
                    previous[0] if previous is not None and not previous[1] else None,
                "exact_adjacent_onset_offset":
                    off if previous is not None and previous == (off - 1, False) else None,
            }
        previous = (off, on)
    return {"first_observed_active_offset": None,
            "last_observed_inactive_offset":
                previous[0] if previous is not None and not previous[1] else None,
            "exact_adjacent_onset_offset": None}


def sha_file(path: Path) -> str:
    require(path.is_file() and not path.is_symlink(), "missing original source trace")
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for buf in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(buf)
    return h.hexdigest()


def audit(root: Path) -> dict:
    report_path = root / "dragster-report.json"
    proof_path = root / "dragster/source/dragster-next-zoo-original.json"
    require(report_path.is_file() and proof_path.is_file() and
            not report_path.is_symlink() and not proof_path.is_symlink(),
            "original executed source/guest report not retained")
    report = json.loads(report_path.read_bytes())
    proof = json.loads(proof_path.read_bytes())
    require(isinstance(report, dict) and report.get("course_id") == "course:01" and
            report.get("name") == "dragster" and report.get("family") == "race-a" and
            report.get("native_backend") == "pinned-baldosa" and
            report.get("admission") == "investigative candidate; not a release-ledger pass",
            "unqualified original/native USA Dragster report")
    for key in ("rom_sha256", "original_movie_sha256", "source_sram_sha256",
                "native_executable_sha256", "reference_core_sha256", "input_sha256"):
        v = report.get(key)
        require(isinstance(v, str) and len(v) == 64 and
                all(ch in "0123456789abcdef" for ch in v),
                "missing exact frozen source/input/binary identity: " + key)
    event = report.get("original_source_event")
    require(isinstance(event, dict) and event.get("original_entry_frame") == 794 and
            event.get("original_result_frame") == MOVIE_RESULT and
            event.get("source_active_frames_to_result") == 2080 and
            event.get("source_next_zoo") == proof,
            "original USA Dragster→Zoo source movie event not authenticated")
    require(isinstance(proof, dict) and proof.get("schema") == PRODUCER_SCHEMA and
            proof.get("original_dragster_entry_host_frame") == 794 and
            proof.get("original_dragster_result_host_frame") == MOVIE_RESULT and
            proof.get("original_zoo_active_entry_host_frame") == MOVIE_ZOO and
            proof.get("source_dragster_result_to_zoo_active_frames") == 316 and
            proof.get("original_zoo_eight_consecutive_active_frames") is True and
            proof.get("original_movie_controller_masks_modified") is False and
            proof.get("release_complete_usa_event_credit") == 0 and
            proof.get("sample_offsets") == list(OFFSETS) and
            set(proof.get("source_samples", {})) == set(map(str, OFFSETS)),
            "historical source selected Zoo but did not establish active race")
    trace_sha = proof.get("original_source_trace_sha256")
    require(isinstance(trace_sha, str) and
            trace_sha == sha_file(root / "dragster/source/trace.jsonl"),
            "original 2014 source raw trace digest differs from proof")
    result = report.get("comparison")
    require(isinstance(result, dict) and result.get("paired_event_candidate") is False and
            result.get("terminal_result_frame_matched") is False and
            result.get("bounded_dragster_to_zoo_diagnostic_without_full_event_parity") is True,
            "strict Dragster result difference missing or falsely promoted")
    clock = result.get("terminal_result_guest_frame")
    require(isinstance(clock, dict) and
            all(type(clock.get(k)) is int and clock[k] > 0
                for k in ("reference_relative", "native_relative")) and
            type(report.get("reference_entry")) is int and
            type(report.get("native_entry")) is int and
            report.get("native_frame_shift") ==
                report["native_entry"] - report["reference_entry"],
            "fresh original/native result and entry clocks not independently qualified")
    handoff = report.get("dragster_next_zoo_handoff")
    require(isinstance(handoff, dict) and handoff.get("schema") == PRODUCER_SCHEMA and
            handoff.get("original_movie_dragster_result_frame") == MOVIE_RESULT and
            handoff.get("original_movie_zoo_entry_frame") == MOVIE_ZOO and
            handoff.get("original_movie_zoo_entry_relative_to_dragster_result") == 316 and
            handoff.get("release_complete_usa_event_credit") == 0 and
            handoff.get("source_controller_masks_rephased") is False and
            handoff.get("original_native_complete_dragster_cpu_spc_frame_parity_proven") is False and
            handoff.get("original_native_complete_zoo_event_proven") is False and
            handoff.get("cold_host_disk_persistence_proven") is False and
            handoff.get("shipping_windows_source_identity_proven") is False and
            isinstance(handoff.get("samples"), list) and
            len(handoff["samples"]) == len(OFFSETS),
            "invalid or over-promotional fresh Dragster guest handoff")
    directory = root / "dragster/replay"
    logs = {}
    for side, filename in (("original", "reference.log"), ("native", "native.log")):
        path = directory / filename
        require(path.is_file() and not path.is_symlink(), "missing real guest replay log")
        logs[side] = path.read_text(encoding="utf8", errors="replace")

    observed, differences, sram_offsets = [], [], set()
    for offset, row in zip(OFFSETS, handoff["samples"]):
        require(isinstance(row, dict) and
                row.get("offset_from_respective_dragster_result") == offset and
                row.get("source_original") == proof["source_samples"][str(offset)],
                "misordered or false historical 2014 source frame")
        source = row["source_original"]
        require(source.get("original_movie_host_frame") == MOVIE_RESULT + offset,
                "original source trace host frame rephased")
        guests = row.get("fresh_guests")
        require(isinstance(guests, dict) and set(guests) == {"original", "native"},
                "missing original/native fresh guest")
        raw = {}
        named = {}
        for side, folder, clock_name, entry_key in (
                ("original", "ref", "reference_relative", "reference_entry"),
                ("native", "native", "native_relative", "native_entry")):
            g = guests[side]
            host = report[entry_key] + clock[clock_name] + offset
            tag = f"dragster-next-zoo-{offset:03d}"
            require(read_logged_frame(logs[side], tag) == host and
                    g.get("host_frame") == host,
                    "original/native executed dump host clock contradicts report")
            path = directory / folder
            w = read_exact(path / (tag + ".wram.bin"), 131072)
            s = read_exact(path / (tag + ".sram.bin"), 8192)
            ranks, good = real_dragster_record(s)
            state = {k: w[addr] for k, addr in NAME_ADDR.items()}
            require(g.get("full_wram_bytes") == len(w) and
                    g.get("full_wram_sha256") == digest(w) and
                    g.get("full_sram_bytes") == len(s) and
                    g.get("full_sram_sha256") == digest(s) and
                    all(g.get(k) == v for k, v in state.items()) and
                    g.get("dragster_record_three_ranks") == ranks and
                    g.get("ranked_records_checksum_valid") is good,
                    "real guest raw memory, ranked record or source state contradicted")
            named[side], raw[side] = state, (w, s)
        delta = [key for key in NAME_ADDR
                 if named["original"][key] != source[key] or
                 named["native"][key] != source[key]]
        require(row.get("source_to_fresh_named_disagreements") == delta,
                "fresh source/guest named divergence concealed")
        diff = raw_wram_pair(raw["original"][0], raw["native"][0])
        require(row.get("unmasked_full_original_native_wram_difference") == diff,
                "original/native full-WRAM byte claims contradict retained guest bytes")
        sdiff = [i for i, (a, b) in enumerate(zip(raw["original"][1], raw["native"][1]))
                 if a != b]
        require(row.get("full_original_native_sram_pair_equal") is (not bool(sdiff)),
                "original/native full 8KiB SRAM equality contradicted")
        sram_offsets.update(sdiff)
        observed.append({"offset": offset, "movie": source,
                         "original": named["original"], "native": named["native"]})
        differences.append({"offset": offset, "unmasked_wram_differing_bytes":
                            diff["differing_byte_count"], "sram_differing_bytes": len(sdiff)})

    brackets = {name: entry_bracket(observed, name)
                for name in ("movie", "original", "native")}
    require(brackets["movie"]["exact_adjacent_onset_offset"] == 316 and
            handoff.get("entry_brackets") == brackets and
            handoff.get("all_three_guest_result_relative_entry_offsets_equal") is
                all(brackets[k]["exact_adjacent_onset_offset"] == 316
                    for k in ("original", "native")) and
            handoff.get("fresh_original_absolute_zoo_onset_host") ==
                (report["reference_entry"] + clock["reference_relative"] +
                 brackets["original"]["exact_adjacent_onset_offset"]
                 if brackets["original"]["exact_adjacent_onset_offset"] is not None else None) and
            handoff.get("fresh_native_absolute_zoo_onset_host") ==
                (report["native_entry"] + clock["native_relative"] +
                 brackets["native"]["exact_adjacent_onset_offset"]
                 if brackets["native"]["exact_adjacent_onset_offset"] is not None else None) and
            handoff.get("first_source_or_guest_named_mismatch_offset") ==
                next((o["offset"] for o in observed
                      if any(o[side][key] != o["movie"][key] for key in NAME_ADDR
                             for side in ("original", "native"))), None) and
            handoff.get("all_full_sram_pairs_equal") is
                all(item["sram_differing_bytes"] == 0 for item in differences) and
            handoff.get("full_wram_difference_offsets") ==
                [x["offset"] for x in differences if x["unmasked_wram_differing_bytes"]],
            "raw three-clock entry/bracket or aggregate guest differences fabricated")

    return {"schema": SCHEMA, "producer_sha256": digest(report_path.read_bytes()),
            "historical_source_trace_sha256": trace_sha,
            "all_14_pairs_rehashed_from_actual_guest_bytes": True,
            "paired_wram_byte_occurrences": sum(x["unmasked_wram_differing_bytes"] for x in differences),
            "paired_sram_byte_occurrences": sum(x["sram_differing_bytes"] for x in differences),
            "unique_persistent_sram_difference_offsets": sorted(sram_offsets),
            "per_offset": differences, "guest_entry_brackets": brackets,
            "source_movie_raw_sram_wram_bytes_in_archive": False,
            "authentic_course_payload_independently_rehashed": False,
            "actual_cpu_spc_or_consumed_input_parity_proven": False,
            "shipping_windows_elf_or_durable_disk_proven": False,
            "independent_usa_event_adjudication": "HOLD",
            "accepted_usa_events": 0}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive-root", type=Path, required=True)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    try:
        result = audit(args.archive_root)
    except (OSError, TypeError, KeyError, ValueError, json.JSONDecodeError) as exc:
        p.exit(2, "QA01_DRAGSTER_RAW_ARCHIVE_INVALID: " + str(exc) + "\n")
    text = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
