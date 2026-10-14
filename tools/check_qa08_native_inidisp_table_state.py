#!/usr/bin/env python3
"""Admit only authentic after-BBUS native channel-7 HDMA descriptor observations.

The source-side probe records both the ALREADY OBSERVED INIDISP register
writes and additional live channel counter/WRAM header values. A probe pass
does not imply a favourable outcome for the non-consuming-prime hypothesis.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

try:
    from tools.check_qa08_native_split_inidisp_source import PATTERN as INIDISP_PATTERN
except ModuleNotFoundError:
    # Native CI invokes this tool directly as python3 tools/<script>.py;
    # that invocation puts tools/ rather than the repo root on sys.path.
    from check_qa08_native_split_inidisp_source import PATTERN as INIDISP_PATTERN

SCHEMA = "qa08-original-native-2p-live-inidisp-hdma-source-paired-handoff/1"
PATTERN = re.compile(
    r"^UR_QA08_HDMA_INIDISP_TABLE_STATE frame=(\d+) tagframe=(\d+) "
    r"line=(-?\d+) channel=(\d+) value=([0-9A-F]{2}) "
    r"src=([0-9A-F]{2}):([0-9A-F]{4}) table=([0-9A-F]{4}) "
    r"count=([0-9A-F]{2}) transfer=(\d+) "
    r"live_header=([0-9A-F]{2}) live_inidisp=([0-9A-F]{2})$"
)
REAL_SOURCES = (("7E", "2065"), ("7E", "2065"),
                ("7E", "2067"), ("7E", "2069"))
REAL_TAGS = (0, 2, 113, 115)
REAL_VALUES = ("0F", "0F", "00", "0F")


def unique_json(path: Path) -> dict:
    def no_duplicates(pairs):
        output = {}
        for key, value in pairs:
            if key in output:
                raise ValueError("duplicate original/native evidence key")
            output[key] = value
        return output
    return json.loads(path.read_text(encoding="utf-8"),
                      object_pairs_hook=no_duplicates)


def check(log: str, evidence: dict) -> dict:
    original = evidence.get("original", {})
    native = evidence.get("native", {})
    image = evidence.get("finished_source_frame_reference", {})
    if (evidence.get("schema") != SCHEMA
        or original.get("run_id") != 38546562780
        or original.get("archive_SHA256") !=
            "4127ca46f83c19de07af4f808522f447ba7f6ce8109febf74ec0e93e0e898ee6"
        or native.get("run_id") != 38545867736
        or native.get("archive_SHA256") !=
            "17fa55e5e12631c488b946db3c01328512a443a3c84566f002e0910aff1a2dba"
        or native.get("writer_HDMA_channel") != 7
        or native.get("writer_mode") != 0
        or native.get("writer_indirect") is not False
        or [(v.get("native_tag"), v.get("source"), v.get("INIDISP"))
            for v in native.get("write_values", [])] != [
            (0, "7E:2065", "0x0F"), (2, "7E:2065", "0x0F"),
            (113, "7E:2067", "0x00"), (115, "7E:2069", "0x0F")]
        or [(v.get("v"), v.get("source"), v.get("INIDISP"))
            for v in original.get("write_values", [])] != [
            (0, "7E:2065", "0x0F"), (111, "7E:2067", "0x00"),
            (113, "7E:2069", "0x0F")]
        or image.get("identical_after_Snes9x_RGB565_G6_to_native_G5") != 56832
        or image.get("mismatched_pixels_by_row") != [
            {"y": 111, "count": 256}, {"y": 113, "count": 256}]):
        raise ValueError("independent true original/native channel7 and pixel handoff changed")

    first = [line for line in log.splitlines()
             if line.startswith("UR_QA08_HDMA_INIDISP frame=")]
    second = [line for line in log.splitlines()
              if line.startswith("UR_QA08_HDMA_INIDISP_TABLE_STATE frame=")]
    if len(first) != 4 or len(second) != 4:
        raise ValueError("one-to-one real native INIDISP/descriptor state events required")
    rows = []
    for i, (line, state) in enumerate(zip(first, second)):
        write = INIDISP_PATTERN.fullmatch(line)
        extra = PATTERN.fullmatch(state)
        if write is None or extra is None:
            raise ValueError("malformed real INIDISP write or live descriptor state")
        (frame, tagframe, tag, channel, bbus, value, bank, src,
         mode, indirect, table, tablebank, live) = write.groups()
        (sframe, stagframe, stag, schannel, svalue, sbank, ssrc,
         stable, count, transfer, header, slive) = extra.groups()
        if (frame != "2208" or tagframe != "2208"
            or sframe != frame or stagframe != tagframe
            or int(tag) != REAL_TAGS[i] or stag != tag
            or int(channel) != 7 or schannel != channel
            or bbus != "00" or mode != "0" or indirect != "0"
            or bank != REAL_SOURCES[i][0] or src != REAL_SOURCES[i][1]
            or sbank != bank or ssrc != src
            or value != REAL_VALUES[i] or svalue != value or live != value
            or slive != value or stable != table
            or tablebank != "7E"
            or int(table, 16) != int(src, 16) + 1
            or transfer not in ("0", "1")
            or int(count, 16) == 0
            or int(header, 16) == 0):
            raise ValueError("native channel7 live source, table, count or PPU mismatch")
        rows.append({
            "source_channel": 7, "native_guest_frame": 2208,
            "native_actual_write_log_tag": int(tag),
            "original_source_WRAM": f"{bank}:{src}",
            "real_HDMA_transfer_byte": "0x" + value,
            "live_PPU_INIDISP_after_transfer": "0x" + live,
            "native_A_bus_cursor_after_byte": "0x" + table,
            "channel_rep_count_before_decrement": int(count, 16),
            "live_WRAM_header_byte_at_source_minus_one": "0x" + header,
            "live_header_equals_loaded_rep_count":
                int(header, 16) == int(count, 16),
            "channel_doTransfer_before_decrement": transfer == "1",
            "descriptor_counter_zero_or_masked": False,
        })

    # One first-line prime and one duplicate first transfer are already
    # source-authenticated. Check they really share the same descriptor
    # counter without assuming a particular header/remaining duration.
    first_repeat_same_count = (rows[0]["channel_rep_count_before_decrement"]
                               == rows[1]["channel_rep_count_before_decrement"])
    observed_counts = [rows[i]["channel_rep_count_before_decrement"]
                       for i in (0, 2, 3)]
    nonrepeat = all(c < 0x80 for c in observed_counts)
    candidate_lengths = [111, 2]
    return {
        "schema": "qa08-native-2P-channel7-executed-descriptor-WRAM-state/1",
        "status": "read-only-after-real-BBUS-DMA-channel-state-observed",
        "original_reference_run": original["run_id"],
        "native_prior_reference_run": native["run_id"],
        "exact_native_frame": 2208,
        "actual_after_BBUS_source_writes_checked": len(rows),
        "observed_native_channel7_descriptors": rows,
        "first_prime_and_duplicate_regular_transfer_same_rep_count":
            first_repeat_same_count,
        "actual_first_two_distinct_descriptor_counts": observed_counts[:2],
        "header_bytes_observed_independently_by_live_WRAM_read": True,
        "source_nonrepeating_descriptor_candidates": nonrepeat,
        "model_first_two_lengths_111_2_supported_by_native_actual_counts":
            nonrepeat and observed_counts[:2] == candidate_lengths,
        "model_claim_if_lengths_disagree": "falsified_or_requires_reanalysis",
        "native_output_pixel_regression_reexecuted_here": False,
        "native_rendering_changed_by_probe": False,
        "original_source_65816_channel7_header_writer_located": False,
        "all_HDMa_channels_or_hardware_timing_certified": False,
        "remastered_character_approved": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--handoff", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = check(args.log.read_text(encoding="utf-8", errors="replace"),
                   unique_json(args.handoff))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print("QA08_NATIVE_CHANNEL7_HEADER_OBSERVED "
          f"counts={result['actual_first_two_distinct_descriptor_counts']} "
          f"model_supported={result['model_first_two_lengths_111_2_supported_by_native_actual_counts']} "
          "candidate_PPU_pixels=not_rerun")


if __name__ == "__main__":
    main()
