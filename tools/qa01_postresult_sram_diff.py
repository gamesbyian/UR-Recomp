#!/usr/bin/env python3
"""QA-01 read-only original/native post-result SRAM byte attribution.

Consumes the existing source-followthrough producer receipt and guest dumps.
This is a non-admitting diagnostic: the first *sampled* difference is never
relabelled the earliest game write or a durable cold-process witness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

OFFSETS = (8, 16, 24, 32, 64, 72)
SIZE = 8192
SHOW_LIMIT = 64


class EvidenceError(ValueError):
    """Missing or contradictory source evidence; not a gameplay verdict."""


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def region(at: int) -> str:
    if 0x0422 <= at <= 0x054D:
        return "track_record_words"
    if 0x054E <= at <= 0x054F:
        return "track_record_checksum"
    if 0x0550 <= at <= 0x05E5:
        return "track_record_holders"
    return "other_battery_sram"


def delta(a: bytes, b: bytes) -> dict:
    if len(a) != SIZE or len(b) != SIZE:
        raise EvidenceError("truncated SRAM in byte comparison")
    indices = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    counts = {k: sum(region(i) == k for i in indices) for k in (
        "track_record_words", "track_record_checksum",
        "track_record_holders", "other_battery_sram")}
    return {
        "equal": not indices,
        "differing_byte_count": len(indices),
        "address_list_complete": len(indices) <= SHOW_LIMIT,
        "first_differing_address": f"0x{indices[0]:04X}" if indices else None,
        "regions": counts,
        "first_differences": [
            {"address": f"0x{i:04X}", "original_byte": f"{a[i]:02X}",
             "native_byte": f"{b[i]:02X}", "region": region(i)}
            for i in indices[:SHOW_LIMIT]
        ],
        "all_difference_addresses_sha256": sha(
            b"".join(i.to_bytes(2, "little") for i in indices)),
    }


def ranked_record_receipt(raw: bytes, track: int) -> tuple[list[dict], int, int]:
    if track not in range(5):
        raise EvidenceError("invalid Crawler track index")
    word = lambda at: int.from_bytes(raw[at:at + 2], "little")
    rows = [{"rank": rank,
             "value_word": word(0x0422 + 2 * (50 * rank + track)),
             "holder_index": raw[0x0550 + 50 * rank + track]}
            for rank in range(3)]
    return rows, word(0x054E), (sum(word(0x0422 + 2 * i) for i in range(150)) & 0xFFFF)


def analyze(producer: dict, original_dir: Path, native_dir: Path) -> dict:
    if producer.get("schema_version") != 1 or producer.get("name") != "zoom-zoo":
        raise EvidenceError("requires exact source-qualified Zoom Zoo producer")
    if producer.get("course_id") != "course:02" or producer.get("native_backend") != "pinned-baldosa":
        raise EvidenceError("unsupported source/guest identity")
    if producer.get("rom_sha256") != "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478":
        raise EvidenceError("noncanonical USA ROM")
    cmp = producer.get("comparison")
    if not isinstance(cmp, dict) or cmp.get("terminal_result_frame_matched") is not True:
        raise EvidenceError("requires corroborated corrected onset equality; no inferred phase rebasing")
    frame = cmp.get("terminal_result_guest_frame")
    if frame != {"reference_relative": 5163, "native_relative": 5163}:
        raise EvidenceError("result onset not the source-qualified corrected Zoo pair")
    follow = producer.get("source_terminal_followthrough")
    if not isinstance(follow, dict) or follow.get("schema") != "UR-QA01-SOURCE-ORIGINAL-NATIVE-RESULT-FOLLOWTHROUGH/2":
        raise EvidenceError("requires original/native live battery followthrough")
    samples = follow.get("samples")
    if not isinstance(samples, list) or len(samples) != len(OFFSETS):
        raise EvidenceError("missing or duplicated followthrough samples")
    expected_source = producer.get("original_source_event", {})
    if expected_source.get("original_entry_frame") != 3190 or expected_source.get("original_result_frame") != 8353:
        raise EvidenceError("unqualified original archived movie event")
    if follow.get("battery_sram_snapshot_bytes_per_guest") != SIZE:
        raise EvidenceError("wrong SRAM size in producer")
    if (follow.get("battery_sram_cold_process_persistence_proven") is not False
            or follow.get("release_complete_usa_event_credit") != 0):
        raise EvidenceError("over-promoted producer followthrough")
    rentry, nentry = producer.get("reference_entry"), producer.get("native_entry")
    if type(rentry) is not int or type(nentry) is not int:
        raise EvidenceError("missing independent race entries")
    receipts = []
    prior = None
    images = {}
    for offset, sample in zip(OFFSETS, samples):
        if (type(sample) is not dict or sample.get("offset_from_each_observed_result_onset") != offset
                or sample.get("independently_observed_replay_host_frames") !=
                {"original": rentry + 5163 + offset, "native": nentry + 5163 + offset}
                or sample.get("source_original_movie", {}).get("original_movie_host_frame") != 8353 + offset):
            raise EvidenceError("source/guest clock or sample-order contradiction")
        members = sample.get("fresh_guest_battery_sram")
        if not isinstance(members, dict):
            raise EvidenceError("missing raw guest battery receipts")
        images[offset] = {}
        for side, directory in (("original", original_dir), ("native", native_dir)):
            receipt = members.get(side)
            if (not isinstance(receipt, dict) or receipt.get("full_sram_bytes") != SIZE
                    or receipt.get("crawler_course_track_index") != 1
                    or receipt.get("in_memory_snapshot_only") is not True
                    or receipt.get("cold_process_reload_proven") is not False):
                raise EvidenceError("invalid original/native live SRAM receipt")
            path = directory / f"original-follow-{offset:02d}.sram.bin"
            if not path.is_file():
                raise EvidenceError(f"missing raw SRAM dump: {side} +{offset}")
            raw = path.read_bytes()
            if len(raw) != SIZE or sha(raw) != receipt.get("sram_sha256"):
                raise EvidenceError(f"SRAM bytes do not match producer SHA256: {side} +{offset}")
            records, stored, calculated = ranked_record_receipt(raw, 1)
            if (receipt.get("crawler_record_three_ranks") != records
                    or receipt.get("record_table_checksum_stored") != stored
                    or receipt.get("record_table_checksum_calculated") != calculated
                    or receipt.get("record_table_checksum_matches_at_sample") is not (stored == calculated)):
                raise EvidenceError(f"raw original record/checksum contradicts producer receipt: {side} +{offset}")
            images[offset][side] = raw
        a, b = images[offset]["original"], images[offset]["native"]
        paired = delta(a, b)
        if sample.get("sram_full_bytes_equal") is not paired["equal"]:
            raise EvidenceError("producer SRAM pairing assertion contradicts raw bytes")
        if sample.get("sram_course_three_rank_records_equal") is not (
                members["original"].get("crawler_record_three_ranks") ==
                members["native"].get("crawler_record_three_ranks")):
            raise EvidenceError("producer ranked course-record pairing contradicted")
        row = {
            "result_relative_offset": offset,
            "original_host_frame": rentry + 5163 + offset,
            "native_host_frame": nentry + 5163 + offset,
            "original_sram_sha256": sha(a), "native_sram_sha256": sha(b),
            "paired": paired,
            "crawler_ranked_records_equal": sample["sram_course_three_rank_records_equal"],
            "relative_to_previous_observation": None if prior is None else {
                "previous_offset": prior,
                "original_changed_bytes": delta(images[prior]["original"], a)["differing_byte_count"],
                "native_changed_bytes": delta(images[prior]["native"], b)["differing_byte_count"],
            },
        }
        receipts.append(row)
        prior = offset
    if follow.get("all_followthrough_full_sram_pairs_equal") is not all(
            x["paired"]["equal"] for x in receipts):
        raise EvidenceError("producer overall SRAM equality assertion contradictory")
    first = next((r["result_relative_offset"] for r in receipts
                  if not r["paired"]["equal"]), None)
    return {
        "schema": "UR-QA01-ZOO-POSTRESULT-SRAM-BYTE-ATTRIBUTION/1",
        "source_identity": {k: producer[k] for k in (
            "rom_sha256", "original_movie_sha256", "source_sram_sha256",
            "original_movie_window_sha256", "reference_core_sha256",
            "native_executable_sha256", "input_sha256")},
        "guest_result_relative_onsets": frame,
        "first_sampled_full_sram_difference_offset": first,
        "preceding_sampled_pair_equal": (
            receipts[OFFSETS.index(first) - 1]["paired"]["equal"]
            if first is not None and OFFSETS.index(first) > 0 else None),
        "observations": receipts,
        "first_execution_time_of_difference_known": False,
        "original_cpu_writer_or_reader_attributed": False,
        "same_logic_tick_equivalence_proven": False,
        "full_event_gameplay_parity_proven": False,
        "cold_process_persistence_proven": False,
        "release_complete_usa_event_credit": 0,
        "scope": "Full 8KiB fresh guest memory images at six result-relative offsets; never original 2014 movie SRAM at those offsets, filesystem durability, or a first offending opcode.",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--producer-report", type=Path, required=True)
    p.add_argument("--original-dir", type=Path, required=True)
    p.add_argument("--native-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args(argv)
    report = analyze(json.loads(a.producer_report.read_text(encoding="utf-8")),
                     a.original_dir, a.native_dir)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Zoo live SRAM first sampled original/native disagreement: +{report['first_sampled_full_sram_difference_offset']} (0 credits)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
