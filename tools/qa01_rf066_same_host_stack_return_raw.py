#!/usr/bin/env python3
"""QA01: original real post-return bytes versus a distinct same-host script-dump raw observation.

This proves an important negative inference: script-dump WRAM is not a proxy
for the value the original guest returned at a distinct source observation phase, even with the same host-frame label.
All bytes are real, unmasked, source-bound RF066 originals/native from one
immutable research ZIP. No executed native peer read or causal parity claim.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import zipfile

import qa01_rf066_original_consumed_report as original_returns
import qa01_rf066_source_controller_archive as provenance

SCHEMA = "ur-qa01-rf066-same-host-post-return-vs-raw/1"
RELATIVE_FRAMES = (1, 2, 4)
STACK_WINDOW = range(0x01ED, 0x01F1)
ORIGINAL_LOG = provenance.ORIGINAL_LOG
NATIVE_LOG = provenance.NATIVE_LOG
RAW_ROOT = provenance.ROOT
PREFIX = "QA01RF066ORIGCONSUMED "
FIELDS = re.compile(r"(\w+)=([^ ]+)")
EXPECTED_STACK_DIFFERENCES = {
    "7E:01ED", "7E:01EE", "7E:01EF", "7E:01F0"
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def true_returns(raw: str, *, expected_count: int) -> list[dict]:
    certified = original_returns.examine(raw)
    require(certified["actual_original_post_getter_return_count"] == expected_count
            and certified["sequenced_source_getset_read_entries"] == 0
            and certified["real_original_return_matches_RF045_and_RF064"] is True,
            "unqualified genuine original source macro returns")
    lines = raw.splitlines()
    require(sum(line.startswith(PREFIX) for line in lines) == expected_count,
            "source original macro return line population changed")
    events = []
    for line in lines:
        if not line.startswith(PREFIX):
            continue
        fields = dict(FIELDS.findall(line))
        require(fields.get("phase") == "post_real_stack_getter_return"
                and fields.get("kind") in ("pullB", "pullW"),
                "source original return phase changed")
        try:
            frame = int(fields["f"])
            width = int(fields["width"])
            base = int(fields["base"], 16)
            value = int(fields["returned"], 16)
            vertical, horizontal = int(fields["v"]), int(fields["h"])
        except (KeyError, ValueError) as exc:
            raise ValueError("invalid source original returned physical byte") from exc
        require(width == (1 if fields["kind"] == "pullB" else 2)
                and 0x01EC <= base <= 0x01F1
                and 0 <= value < (1 << (8 * width))
                and 0 <= vertical <= 311 and horizontal >= 0,
                "invalid actual original return width/address/value/host clock")
        events.append({
            "frame": frame, "base": base, "width": width,
            "returned": value, "v": vertical, "h": horizontal
        })
    return events


def raw_frame_pairs(archive: zipfile.ZipFile, frame: int) -> tuple[bytes, bytes]:
    # Both full unmasked original/native WRAMs must exist in the same
    # separately labelled source-race-relative scene. No reconstruction.
    suffix = f"scene-{frame:05d}.wram.bin"
    original = archive.read(RAW_ROOT + "ref/" + suffix)
    native = archive.read(RAW_ROOT + "native/" + suffix)
    require(len(original) == len(native) == 131072,
            "missing or short original/native physical raw 128KiB WRAM")
    return original, native


def row(frame: int, source_events: list[dict],
        original: bytes, native: bytes) -> dict:
    require(type(frame) is int and frame >= 0 and
            len(original) == len(native) == 131072,
            "invalid actual source/native raw input")
    differing = [i for i, (a, b) in enumerate(zip(original, native)) if a != b]
    actual_addresses = {f"7E:{offset:04X}" for offset in differing}
    require(set(actual_addresses) == EXPECTED_STACK_DIFFERENCES,
            "source/native same-host raw discrepancy changed")
    total_pulls = 0
    total_byte_matches = 0
    classes = Counter()
    by_address = Counter()
    for item in source_events:
        if item["frame"] != frame:
            continue
        positions = [
            (item["base"] + i, (item["returned"] >> (8 * i)) & 0xFF)
            for i in range(item["width"]) if item["base"] + i in differing
        ]
        if not positions:
            continue
        total_pulls += 1
        for addr, value in positions:
            total_byte_matches += 1
            by_address[f"7E:{addr:04X}"] += 1
            # The two same-host dump-phase values differ by construction.
            # Returned source values may be neither because stack state
            # may differ between actual getter-return phase and host-script dump phase, with no proven inter-recorder order.
            classes["matches_original_same_host_dump_only" if value == original[addr]
                    else "matches_native_same_host_dump_only" if value == native[addr]
                    else "matches_neither_same_host_dump"] += 1
    require(sum(classes.values()) == total_byte_matches and
            total_byte_matches >= total_pulls > 0,
            "original true return at differing addresses not witnessed")
    return {
        "race_relative_frame": frame,
        "raw_pair_reopened_complete_unmasked_131072_bytes_each": True,
        "full_original_native_wram_byte_differences": len(differing),
        "actual_differing_stack_addresses": sorted(actual_addresses),
        "original_return_operations_touching_differing_addresses": total_pulls,
        "return_byte_observations_touching_differing_addresses": total_byte_matches,
        "individual_return_byte_values_vs_same_host_script_dump": {
            k: classes[k] for k in (
                "matches_original_same_host_dump_only",
                "matches_native_same_host_dump_only",
                "matches_neither_same_host_dump")},
        "return_byte_observation_counts_by_physical_address":
            dict(sorted(by_address.items())),
        "same_host_frame_establishes_instruction_phase_equivalence": False,
        "return_vs_script_dump_chronological_order_proven": False,
    }


def audit(zip_path: Path, movie: Path, metadata: Path,
          expected_sha256: str = provenance.PINNED_CASE_SHA256) -> dict:
    source = provenance.verify(zip_path, movie, metadata, expected_sha256)
    require(source["all_5449_individual_source_original_native_supplied_masks_equal"]
            and source["actual_CPU_joypad_poll_consumption_proven"] is False
            and source["accepted_USA_events"] == 0,
            "wrong genuine source movie/input provenance or event admission")
    with zipfile.ZipFile(zip_path) as zipped:
        log = zipped.read(ORIGINAL_LOG).decode("utf-8")
        native_log = zipped.read(NATIVE_LOG)
        producer = json.loads(zipped.read(provenance.REPORT))
        source_origin = producer["reference_entry"]
        native_origin = producer["native_entry"]
        require(type(source_origin) is int and type(native_origin) is int,
                "unbound independent original/native host clocks")
        events = true_returns(log, expected_count=903)
        results = []
        for offset in RELATIVE_FRAMES:
            label = f"scene-{offset:05d}"
            for guest, raw, origin in (
                ("original", log.encode("utf-8"), source_origin),
                ("native", native_log, native_origin),
            ):
                ack = provenance.success_frame(raw, label, guest)
                require(ack == origin + offset,
                        "mismatched guest-local observed scene and dump clock")
            a, b = raw_frame_pairs(zipped, offset)
            results.append(row(source_origin + offset, events, a, b))
        # Express the source's host sample positions accurately. No native
        # instruction clock alignment is inferred from matching host labels.
        for entry, offset in zip(results, RELATIVE_FRAMES):
            entry["original_actual_host_frame"] = source_origin + offset
            entry["native_actual_host_frame"] = native_origin + offset
            entry["race_relative_frame"] = offset
    aggregate = Counter()
    pulls = 0
    bytes_seen = 0
    for item in results:
        pulls += item["original_return_operations_touching_differing_addresses"]
        bytes_seen += item["return_byte_observations_touching_differing_addresses"]
        aggregate.update(item["individual_return_byte_values_vs_same_host_script_dump"])
    require(sum(aggregate.values()) == bytes_seen and
            all(item["full_original_native_wram_byte_differences"] == 4
                for item in results), "unmasked source observations incomplete")
    return {
        "schema": SCHEMA,
        "immutable_case_zip_sha256": expected_sha256,
        "original_source_log_sha256": producer["qa01_capture_ab_control"][
            "reference_guest_log_sha256"],
        "same_2014_source_and_supplied_original_native_inputs": True,
        "all_actual_original_RF066_macro_returns_verified": len(events),
        "same_host_full_memory_pairs_independently_reopened": len(results),
        "same_host_raw_frames": results,
        "total_true_original_return_operations_touching_same_host_differing_WRAM":
            pulls,
        "total_returned_source_byte_observations": bytes_seen,
        "total_returned_source_byte_comparison_classes": dict(sorted(aggregate.items())),
        "interpretation": (
            "Actual original post-getter returned bytes need not match either "
            "guest's separately sampled full WRAM at a different phase within the same host frame; "
            "source/native return-value equivalence and true instruction-time "
            "cross-guest bus phases are not established."
        ),
        "original_return_values_are_real_post_macro_values": True,
        "original_getset_entry_time_read_value_proven": False,
        "native_corresponding_real_guest_return_proven": False,
        "first_consumed_original_native_causal_divergence_proven": False,
        "return_vs_script_dump_chronological_order_proven": False,
        "all_course_frames_equal_proven": False,
        "accepted_USA_events": 0,
        "release_QA_gates": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--movie", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), "refuse to overwrite previously reviewed evidence")
    answer = audit(args.archive, args.movie, args.metadata)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(answer, indent=2, sort_keys=True) + "\n")
    print("RF066 actual returned bytes versus same-host script-dump raw images: noncausal, 0/45")


if __name__ == "__main__":
    main()
