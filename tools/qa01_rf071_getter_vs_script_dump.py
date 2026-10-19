#!/usr/bin/env python3
"""QA01: independently contrast genuine original getset-ENTRY reads with WRAM.

Unlike RF066's true post-call returns, RF071's authenticated archive contains
a real getset-entry physical byte/word sampled from the original Snes9x CPU.
A script-dump in the same host frame is a DIFFERENT observation phase of
unproven chronological ordering, not a substitute for the read value.

No native corresponding read, opcode-fetch-PC identity or event acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
import zipfile

import qa01_rf066_same_host_stack_return_raw as comparison
import qa01_rf066_source_controller_archive as movie_source
import qa01_rf071_original_real_read_join as certified_getter
import qa01_verify_supplied_controller_streams as supplied

SCHEMA = "ur-qa01-rf071-genuine-original-getter-vs-script-frame-raw/1"
SAMPLE_FRAMES = comparison.RELATIVE_FRAMES
SOURCE_ROOT = movie_source.ROOT
MEMORY_SIZE = 131072
HEX = re.compile(r"[0-9A-F]{2}|[0-9A-F]{4}\Z")
PHYSICAL = re.compile(r"00:01(?:EC|ED|EE|EF|F0|F1)\Z")


def must(condition: bool, why: str) -> None:
    if not condition:
        raise ValueError(why)


def project_getset(transactions: list[dict]) -> list[dict]:
    """Project only the already verified original getset entry bytes.

    Actual source getter PCs are *getset context*, never invented native
    decoded opcode PC or a post-return read proxy.
    """
    must(type(transactions) is list and transactions,
         "no authenticated original real getset reads")
    out = []
    for expected, tx in enumerate(transactions, 1):
        must(type(tx) is dict and tx.get("ordinal") == expected
             and tx.get("bus_kind") in ("rb", "rw")
             and type(tx.get("host_frame")) is int and
             PHYSICAL.fullmatch(tx.get("physical_bus_address", "")) is not None,
             "missing/forged real original bus identity or read ordinal")
        value = tx.get("returned")
        must(type(value) is str and HEX.fullmatch(value) is not None and
             (len(value) == 2 if tx["bus_kind"] == "rb" else len(value) == 4),
             "real original getset byte width/value missing")
        must(all(type(tx.get(k)) is int and tx[k] >= 0 for k in
                 ("source_getset_scanline", "source_getset_cycles",
                  "post_call_scanline", "post_call_cycles")),
             "missing or invalid actual source guest clock")
        must((tx["source_getset_scanline"], tx["source_getset_cycles"]) <=
             (tx["post_call_scanline"], tx["post_call_cycles"]),
             "original getter entry occurs after observed return")
        out.append({
            "frame": tx["host_frame"],
            "base": int(tx["physical_bus_address"].split(":")[1], 16),
            "width": 1 if tx["bus_kind"] == "rb" else 2,
            "returned": int(value, 16),
            "source_getset_scanline": tx["source_getset_scanline"],
            "source_getset_cycles": tx["source_getset_cycles"],
            "source_PC_context_only": tx["real_getset_entry_PC_context"],
        })
    return out


def audit(case: Path, movie: Path, metadata: Path) -> dict:
    # First independently establish exactly one authentic original source
    # ELF epoch, log SHA, 903 true getset-entry reads, 903 matching physical
    # actual returns, and all 78 real unmasked source/native WRAM pairs.
    proof = certified_getter.authenticated_case(case)
    must(proof.get("authenticated_original_source") is True and
         proof.get("read_entries_uniquely_bound_to_real_return") == 903 and
         proof.get("actual_opcode_fetch_PC_at_return_proven") is False and
         proof.get("accepted_USA_events") == 0,
         "original getset transaction authority or zero-credit condition missing")
    events = project_getset(proof["transactions"])
    window, real_movie_events, waveform = movie_source.original_movie_segments(
        movie, metadata)
    must(window["frames"] == 5449 and len(real_movie_events) == 397,
         "actual pinned original 2014 movie input window not qualified")
    with zipfile.ZipFile(case) as z:
        producer = json.loads(z.read("producer-report.json"))
        old = producer.get("qa01_capture_ab_control")
        must(type(old) is dict and
             old.get("controller_movie_window_sha256") ==
                window["raw_controller_window_sha256"] and
             producer.get("original_movie_sha256") ==
                movie_source.movie_identity.PINNED_MOVIE_CONTAINER_SHA256 and
             producer.get("native_backend") == "pinned-baldosa",
             "wrong producer's actual original movie/controller guest identity")
        original_origin, native_origin = (producer["reference_entry"],
                                          producer["native_entry"])
        must(type(original_origin) is int and type(native_origin) is int and
             original_origin >= 0 and native_origin >= 0,
             "independent guest origin clocks missing")
        for guest, file_name, prefix, origin in (
            ("original", movie_source.ORIGINAL_INPUT, "reference", original_origin),
            ("native", movie_source.NATIVE_INPUT, "native", native_origin),
        ):
            raw = z.read(file_name)
            must(hashlib.sha256(raw).hexdigest() ==
                 old[prefix + "_supplied_input_sha256"] and
                 len(raw) == old[prefix + "_supplied_input_bytes"],
                 "original/native actual supplied input bytes do not match case")
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / (guest + ".input")
                path.write_bytes(raw)
                _, original_events = supplied.reopen(
                    path, native=guest == "native", pinned=True, origin=origin)
            must(original_events == real_movie_events,
                 "original/native actual guest supply not from 2014 movie window")
        source_log, native_log = (z.read(movie_source.ORIGINAL_LOG),
                                  z.read(movie_source.NATIVE_LOG))
        for guest, raw, prefix in (
            ("original", source_log, "reference"),
            ("native", native_log, "native"),
        ):
            must(hashlib.sha256(raw).hexdigest() ==
                 old[prefix + "_guest_log_sha256"],
                 "actual executed guest log checksum differs from producer")
        rows = []
        for frame in SAMPLE_FRAMES:
            label = f"scene-{frame:05d}"
            for guest, log, origin in (
                ("original", source_log, original_origin),
                ("native", native_log, native_origin),
            ):
                must(movie_source.success_frame(log, label, guest) ==
                     origin + frame,
                     "actual original/native host ACK is missing or shifted")
            left, right = comparison.raw_frame_pairs(z, frame)
            snapshot = comparison.row(original_origin + frame,
                                      events, left, right)
            snapshot["race_relative_frame"] = frame
            snapshot["original_actual_host_frame"] = original_origin + frame
            snapshot["native_actual_host_frame"] = native_origin + frame
            rows.append(snapshot)
    ops = sum(r["original_return_operations_touching_differing_addresses"]
              for r in rows)
    bytes_seen = sum(r["return_byte_observations_touching_differing_addresses"]
                     for r in rows)
    summary = {
        key: sum(row["individual_return_byte_values_vs_same_host_script_dump"][key]
                 for row in rows)
        for key in (
            "matches_original_same_host_dump_only",
            "matches_native_same_host_dump_only",
            "matches_neither_same_host_dump",
        )
    }
    must(sum(summary.values()) == bytes_seen and
         ops <= bytes_seen and
         len(events) == proof["executed_source_original_getset_reads"],
         "source-authentic actual original getset byte census incomplete")
    return {
        "schema": SCHEMA,
        "source_case_zip_sha256": certified_getter.CASE_SHA256,
        "genuine_source_original_2014_movie_full_scheduled_mask_sha256":
            movie_source.frame_mask_digest(waveform),
        "original_source_getset_read_return_joins_reopened":
            proof["read_entries_uniquely_bound_to_real_return"],
        "original_source_getter_calls_crossing_video_scanline":
            proof["genuine_getter_calls_crossing_original_V_scanline"],
        "same_host_source_native_full_raw_Wram_pairs": len(rows),
        "same_host_source_native_raw_byte_sampling_phase": "script_dump",
        "physical_original_getset_read_sampling_phase": "getset_entry",
        "return_vs_script_dump_chronological_order_proven": False,
        "sampled_original_getset_read_operations_overlapping_differing_Wram": ops,
        "sampled_original_getset_read_byte_observations": bytes_seen,
        "actual_original_getset_read_bytes_vs_same_host_raw_classes": summary,
        "frames": rows,
        "actual_native_corresponding_getset_read_proven": False,
        "original_getset_context_is_decoded_opcode_fetch_PC_proven": False,
        "first_original_native_causally_consumed_difference_proven": False,
        "continuous_whole_course_gameplay_parity_proven": False,
        "accepted_USA_events": 0,
        "accepted_Windows_release_QA_gates": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--movie", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    must(not args.output.exists(), "refuse to replace earlier independent receipt")
    verdict = audit(args.archive, args.movie, args.metadata)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print("RF071 real original getter entry vs same-host raw: different phases; QA01 HOLD")


if __name__ == "__main__":
    main()
