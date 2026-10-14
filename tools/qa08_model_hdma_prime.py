#!/usr/bin/env python3
"""Bounded channel-7 HDMA first-line consumption hypothesis.

A deterministic *source-code model*, not a new emulator capture or a fix.
The two non-repeating descriptor durations are inferred from the accepted
original transition V counters; descriptor header bytes are not measured here.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HANDOFF = Path(__file__).resolve().parents[1] / (
    "analysis/data/qa08-original-native-2p-brightness-split-channel7-handoff-20261014.json"
)
SCHEMA = "qa08-original-native-2p-live-inidisp-hdma-source-paired-handoff/1"


def _strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate retained-source field")
        result[key] = value
    return result


def _check_accepted(handoff: dict) -> None:
    original = handoff.get("original", {})
    native = handoff.get("native", {})
    raster = handoff.get("finished_source_frame_reference", {})
    if (handoff.get("schema") != SCHEMA
        or original.get("run_id") != 38546562780
        or native.get("run_id") != 38545867736
        or original.get("archive_SHA256") !=
            "4127ca46f83c19de07af4f808522f447ba7f6ce8109febf74ec0e93e0e898ee6"
        or native.get("archive_SHA256") !=
            "17fa55e5e12631c488b946db3c01328512a443a3c84566f002e0910aff1a2dba"
        or original.get("writer_HDMA_channel") != 7
        or native.get("writer_HDMA_channel") != 7
        or original.get("writer_mode") != 0 or native.get("writer_mode") != 0
        or original.get("writer_indirect") is not False
        or native.get("writer_indirect") is not False
        or original.get("write_values") != [
            {"v": 0, "source": "7E:2065", "INIDISP": "0x0F",
             "PPU_brightness": 15, "PPU_forced_blank_bit": False},
            {"v": 111, "source": "7E:2067", "INIDISP": "0x00",
             "PPU_brightness": 0, "PPU_forced_blank_bit": False},
            {"v": 113, "source": "7E:2069", "INIDISP": "0x0F",
             "PPU_brightness": 15, "PPU_forced_blank_bit": False}]
        or [(v.get("native_tag"), v.get("source"), v.get("INIDISP"),
             v.get("live_INIDISP_after_write")) for v in
            native.get("write_values", [])] != [
                (0, "7E:2065", "0x0F", "0x0F"),
                (2, "7E:2065", "0x0F", "0x0F"),
                (113, "7E:2067", "0x00", "0x00"),
                (115, "7E:2069", "0x0F", "0x0F")]
        or raster.get("identical_after_Snes9x_RGB565_G6_to_native_G5") != 56832
        or raster.get("total_pixels") != 57344
        or raster.get("mismatched_pixels_by_row") != [
            {"y": 111, "count": 256}, {"y": 113, "count": 256}]
        or raster.get("original_zero_brightness_black_rows") != [111, 112]
        or raster.get("native_zero_brightness_black_rows") != [112, 113]):
        raise ValueError("accepted independent original/native source evidence has changed")


def replay(durations: tuple[int, ...], values: tuple[int, ...],
           *, prime_consumes: bool) -> dict:
    """Mode-0 *non-repeating* HDMA under pinned beam-driver call order.

    Before each visible line draw, the renderer already has the state from
    the preceding line's HBlank. The log cursor is line+1 *after* drawing.
    This excludes other channels, midline hardware and unobserved headers.
    """
    if (not durations or len(durations) != len(values)
        or any(not 1 <= d <= 127 for d in durations)
        or any(not 0 <= v <= 255 for v in values)):
        raise ValueError("model needs bounded non-repeating mode-0 descriptors")
    entry = 0
    remaining = durations[0]
    transfer = True
    brightness = 15
    events = []
    black_rows = []

    def advance():
        nonlocal entry, remaining, transfer
        remaining -= 1
        if remaining == 0:
            entry += 1
            if entry < len(durations):
                remaining = durations[entry]
                transfer = True
            else:
                transfer = False
        else:
            transfer = False

    # The pinned native prime copies/restores DmaChannel, leaving the first
    # real transfer to recur in the first dma_doHdma() after line 1.
    events.append((0, values[0]))
    brightness = values[0] & 15
    if prime_consumes:
        advance()
    for line in range(1, 225):
        # ppu_rasterApplyLine; ppu_runLine: zero-based output row = line - 1.
        if brightness == 0:
            black_rows.append(line - 1)
        # dma_doHdma after line drawn; ppu_runLine set the log tag to line+1.
        if transfer:
            if entry >= len(values):
                raise ValueError("HDMA descriptor exhausted before termination")
            brightness = values[entry] & 15
            events.append((line + 1, values[entry]))
        if entry < len(durations):
            advance()
    return {"log_events": [{"native_tag": tag, "INIDISP": f"0x{v:02X}"}
                           for tag, v in events],
            "zero_brightness_output_rows": black_rows}


def check(handoff: dict) -> dict:
    _check_accepted(handoff)
    # Durations 111 and 2 come from successive ORIGINAL source transition
    # V counters; 111 third-row duration is an illustrative fill to row223.
    # The literal 7E:2064/2066/2068 *descriptor header bytes* have NOT yet
    # been independently checked against the actual run.
    durations = (111, 2, 111)
    values = (15, 0, 15)
    existing = replay(durations, values, prime_consumes=False)
    proposed = replay(durations, values, prime_consumes=True)
    if (existing["log_events"] != [
            {"native_tag": 0, "INIDISP": "0x0F"},
            {"native_tag": 2, "INIDISP": "0x0F"},
            {"native_tag": 113, "INIDISP": "0x00"},
            {"native_tag": 115, "INIDISP": "0x0F"}]
        or existing["zero_brightness_output_rows"] != [112, 113]
        or proposed["log_events"] != [
            {"native_tag": 0, "INIDISP": "0x0F"},
            {"native_tag": 112, "INIDISP": "0x00"},
            {"native_tag": 114, "INIDISP": "0x0F"}]
        or proposed["zero_brightness_output_rows"] != [111, 112]):
        raise ValueError("pinned beam/HDMA first-line model no longer matches evidence")
    return {
        "schema": "qa08-mode0-HDMA-prime-consumption-source-model/1",
        "status": "static-control-flow-hypothesis-matches-observed-registers-and-rows",
        "accepted_original_source_run": 38546562780,
        "accepted_native_source_run": 38545867736,
        "original_transition_v": [0, 111, 113],
        "original_zero_brightness_rows": [111, 112],
        "descriptor_durations_inferred_from_original_transitions": [111, 2],
        "descriptor_header_bytes_independently_read": False,
        "last_model_descriptor_is_illustrative": True,
        "actual_unmodified_native_model": existing,
        "consume_prime_once_counterfactual_model": proposed,
        "corrected_native_exact_binary_or_raster_executed": False,
        "same_frame_all_channel_PPU_effects_proven": False,
        "physical_SNES_timing_proven": False,
        "artist_approved_HD": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handoff", type=Path, default=HANDOFF)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    evidence = json.loads(args.handoff.read_text(encoding="utf-8"),
                          object_pairs_hook=_strict_pairs)
    result = check(evidence)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print("QA08_HDMA_PRIME_MODEL_MATCHED old_black=112,113 "
          "counterfactual_black=111,112 exact_binary=unverified")


if __name__ == "__main__":
    main()
