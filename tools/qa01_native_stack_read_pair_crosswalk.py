#!/usr/bin/env python3
"""Bind the native NMI writer beam and WRAM-read journal to one exact replay.

This reconciles two independently parsed instruments. It does not observe
new guest instructions, establish matching original/native CPU phase, identify
a scoring consumer, or admit a complete course.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import qa01_native_nmi_beam_report as beam
import qa01_native_stack_read_report as reads

SCHEMA = "UR-QA01-NATIVE-SWITCHER-NMI-WRITER-READ-JOURNAL-CROSSWALK/1"


def summarize(writer: dict, reader: dict) -> dict:
    if not isinstance(writer, dict) or not isinstance(reader, dict):
        raise ValueError("missing paired native NMI and read report dictionaries")
    if writer.get("schema") != beam.SCHEMA or reader.get("schema") != reads.SCHEMA:
        raise ValueError("wrong native writer/read source report schema")
    wsha, rsha = (writer.get("paired_report_bytes_sha256"),
                  reader.get("paired_report_bytes_sha256"))
    if (type(wsha) is not str or re.fullmatch(r"[0-9a-f]{64}", wsha) is None
            or wsha != rsha
            or writer.get("exact_original_native_switcher_pair_provenance")
               != reader.get("independently_authenticated_original_native_pair")
            or not isinstance(writer.get("exact_original_native_switcher_pair_provenance"), dict)
            or not writer["exact_original_native_switcher_pair_provenance"]):
        raise ValueError("the two native witnesses do not share authenticated paired replay bytes")
    event = writer.get("native_original_nmi_writer_beam")
    if (not isinstance(event, dict)
            or event.get("native_host_frame") != 5781
            or event.get("generated_owner") != "I_NMI_M1X1"
            or event.get("wram_write_destination") != "7E:01DD"
            or event.get("stack_word_saved") != "4004"
            or event.get("accumulator_at_write") != "4004"
            or event.get("stack_pointer_at_write") != "01DD"
            or writer.get("native_observation_host_frame_window") != [5778, 5782]
            or writer.get("accepted_usa_course_count_added") != 0
            or writer.get("framework_beam_vs_original_cpu_phase_unaligned") is not True
            or reader.get("native_frame_bounds") != [5778, 5782]
            or reader.get("native_read_observer_armed_by_real_nmi_4004_writer") is not True
            or reader.get("read_attempt_is_not_proven_original_pha_restore_or_scoring_consumer")
               is not True
            or reader.get("release_complete_event_credit") != 0):
        raise ValueError("paired writer/read scope not the exact no-credit native NMI saved-A")
    rows = reader.get("native_stack_read_attempts")
    count = reader.get("native_bus_read_attempt_count")
    tally = reader.get("native_bus_read_attempts_by_target")
    if (not isinstance(rows, list) or type(count) is not int
            or len(rows) != count or not 0 <= count <= reads.LIMIT
            or not isinstance(tally, dict)
            or set(tally) != {"7E:01DD", "7E:01DE"}
            or any(type(v) is not int or v < 0 or v > count
                   for v in tally.values())
            or reader.get("zero_count_is_bounded_native_negative_not_no_reader_ever")
               is not (count == 0)):
        raise ValueError("read journal counts/zero-witness metadata invalid")
    actual = {"7E:01DD": 0, "7E:01DE": 0}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("malformed read row in paired native journal")
        targets = row.get("target_stack_bytes_touched")
        if (not isinstance(targets, list) or not targets
                or len(targets) > 2 or len(set(targets)) != len(targets)
                or any(target not in actual for target in targets)):
            raise ValueError("native read row does not touch pinned stack targets")
        for target in targets:
            actual[target] += 1
    if tally != actual:
        raise ValueError("journal read counts disagree with actual declared target bytes")
    # Source-ordered within the read journal only. The independent write
    # logger samples CPU master cycles at another callback boundary.
    return {
        "schema": SCHEMA,
        "paired_report_bytes_sha256": wsha,
        "writer_host_frame": 5781,
        "writer_guest_saved_word": "4004",
        "writer_01dd_address": "7E:01DD",
        "native_read_attempt_count": count,
        "native_read_targets_tallied": actual,
        "writer_and_reader_share_pair_bytes": True,
        "single_physical_writer_event_correlated_by_callbacks_not_cpu_cycle": True,
        "read_callback_after_writer_callback_not_proven_guest_restore": True,
        "source_original_and_native_beam_phase_alignment_proven": False,
        "native_guest_result_consumer_proven": False,
        "complete_usa_course_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--native-beam-report", type=Path, required=True)
    ap.add_argument("--native-read-report", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    report = summarize(
        json.loads(args.native_beam_report.read_text(encoding="utf-8")),
        json.loads(args.native_read_report.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
