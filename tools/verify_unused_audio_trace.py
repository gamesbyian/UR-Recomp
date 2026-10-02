#!/usr/bin/env python3
"""Verify that a counterfactual unused-song body was streamed through APU port $2143."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.inspect_audio_block_pool import parse_block_pool
except ModuleNotFoundError:
    from inspect_audio_block_pool import parse_block_pool


def expected_song_body(rom: bytes, selector: int) -> bytes:
    pool = parse_block_pool(rom, count=selector + 1)
    row = pool["blocks"][selector]
    off = int(row["file_offset"], 16)
    total = row["total_length"]
    record = rom[off:off + total]
    payload = record[2:]
    if len(payload) < 4:
        raise ValueError("audio record too short for song framing")
    if payload[:4] != bytes.fromhex("00 04 00 1d"):
        raise ValueError(
            f"selector 0x{selector:02X} does not use expected song framing: "
            f"{payload[:4].hex(' ')}"
        )
    return payload[4:]


def _event_int(event: dict, key: str, hex_key: str) -> int | None:
    value = event.get(key)
    if value is not None:
        return int(value)
    raw = event.get(hex_key)
    return int(raw, 16) if raw is not None else None


def port3_stream(trace: dict) -> bytes:
    values = []
    for event in trace.get("events", []):
        address = _event_int(event, "address", "address_hex")
        if address != 0x2143:
            continue
        value = _event_int(event, "value", "value_hex")
        values.append(int(value) & 0xFF)
    return bytes(values)


def counter_segments(trace: dict) -> tuple[list[bytes], list[dict]]:
    events = trace.get("events", [])
    pairs: list[tuple[int, int]] = []
    anomalies: list[dict] = []
    i = 0
    while i < len(events):
        a = _event_int(events[i], "address", "address_hex")
        if a == 0x2143 and i + 1 < len(events):
            b = _event_int(events[i + 1], "address", "address_hex")
            if b == 0x2142:
                data = _event_int(events[i], "value", "value_hex")
                counter = _event_int(events[i + 1], "value", "value_hex")
                pairs.append((int(data) & 0xFF, int(counter) & 0xFF))
                i += 2
                continue
        anomalies.append({
            "event_index": i,
            "address": a,
            "value": _event_int(events[i], "value", "value_hex"),
        })
        i += 1

    segments: list[list[tuple[int, int]]] = []
    current: list[tuple[int, int]] = []
    for pair in pairs:
        if current and pair[1] != ((current[-1][1] + 1) & 0xFF):
            segments.append(current)
            current = []
        current.append(pair)
    if current:
        segments.append(current)
    return [bytes(data for data, _ in seg) for seg in segments], anomalies


def verify(rom: bytes, trace: dict, selector: int) -> dict:
    expected = expected_song_body(rom, selector)
    framed = bytes.fromhex("00 04 00 1d") + expected
    stream = port3_stream(trace)
    pos = stream.find(expected)
    segments, anomalies = counter_segments(trace)

    combinations = []
    exact_segment_body = None
    exact_segment_framed = None
    trim4_body = None
    for start in range(len(segments)):
        blob = b""
        for end in range(start, len(segments)):
            blob += segments[end]
            row = {
                "start_segment": start,
                "end_segment": end,
                "length": len(blob),
                "sha256": hashlib.sha256(blob).hexdigest(),
                "equals_expected_body": blob == expected,
                "equals_framed_record": blob == framed,
                "drop_first_4_equals_body": len(blob) == len(expected) + 4 and blob[4:] == expected,
                "drop_last_4_equals_body": len(blob) == len(expected) + 4 and blob[:-4] == expected,
            }
            if row["equals_expected_body"] and exact_segment_body is None:
                exact_segment_body = [start, end]
            if row["equals_framed_record"] and exact_segment_framed is None:
                exact_segment_framed = [start, end]
            if (
                row["drop_first_4_equals_body"] or row["drop_last_4_equals_body"]
            ) and trim4_body is None:
                trim4_body = [start, end]
            if len(blob) in {len(expected), len(expected) + 4}:
                combinations.append(row)

    segment_rows = [
        {
            "index": i,
            "length": len(blob),
            "sha256": hashlib.sha256(blob).hexdigest(),
            "head_hex": blob[:16].hex(),
            "tail_hex": blob[-16:].hex(),
        }
        for i, blob in enumerate(segments)
    ]
    success = (
        pos >= 0
        or exact_segment_body is not None
        or exact_segment_framed is not None
        or trim4_body is not None
    )
    return {
        "schema_version": 2,
        "selector": selector,
        "selector_hex": f"0x{selector:02X}",
        "expected_body_length": len(expected),
        "expected_body_sha256": hashlib.sha256(expected).hexdigest(),
        "expected_framed_length": len(framed),
        "expected_framed_sha256": hashlib.sha256(framed).hexdigest(),
        "port_2143_bytes": len(stream),
        "port_2143_sha256": hashlib.sha256(stream).hexdigest(),
        "match_offset": pos if pos >= 0 else None,
        "match_offset_hex": f"0x{pos:X}" if pos >= 0 else None,
        "counter_segments": segment_rows,
        "counter_anomalies": anomalies,
        "candidate_combinations": combinations,
        "exact_segment_body": exact_segment_body,
        "exact_segment_framed": exact_segment_framed,
        "trim4_body": trim4_body,
        "exact_body_found": success,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("trace_json", type=Path)
    ap.add_argument("selector", type=lambda x: int(x, 0))
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = verify(
        args.rom.read_bytes(),
        json.loads(args.trace_json.read_text(encoding="utf-8")),
        args.selector,
    )
    print(json.dumps(report, indent=2))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["exact_body_found"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
