#!/usr/bin/env python3
"""Summarize bounded native Baldosa WRAM *write attempts* at Switcher terminal.

Not an original-Snes9x opcode trace: AOT function scope and IPC are only
whatever the native WRAM hook exposes; the recorded stack S may be
pre-decrement or post-decrement. Do not infer guest PC parity or change
the original/native result comparator. Summary retains no full WRAM/ROM.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
import json
from pathlib import Path
import re

SCHEMA = "UR-QA01-NATIVE-SWITCHER-STACK-WRAM-WRITES/1"
WRITE = re.compile(
    r"^f\s*(\d+)\s+([0-9A-Fa-f]{2}):([0-9A-Fa-f]{4})="
    r"([0-9A-Fa-f]{2,4})\s+w([12])\s+(.+)$"
)
SP = re.compile(r"(?:^|\s)S=([0-9A-Fa-f]{4})(?:\s|$)")
IPC = re.compile(r"(?:^|\s)IPC=([0-9A-Fa-f]{6})(?:\s|$)")
TARGETS = (0x01DD, 0x01E6, 0x01E7, 0x01EF, 0x01F0, 0x01F1, 0x01F2, 0x01F3)
EXPECTED_DIFFS = [f"0x{x:05X}" for x in TARGETS]
EXPECTED_MOVIE_SHA = "06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442"
EXPECTED_ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
MIN_FRAME, MAX_FRAME = 5775, 5790
MAX_EVENTS = 500000
EXAMPLE_LIMIT = 5


def validate_paired_guest_report(obj: dict) -> dict:
    """Require exact true original/native Switcher evidence, not a timed shell."""
    pair = obj["switcher_same_host_penultimate"]
    memory = obj["switcher_same_host_full_memory_offsets"]
    if (obj["name"] != "switcher" or obj["course_id"] != "course:04"
            or obj["rom_sha256"] != EXPECTED_ROM_SHA
            or obj["original_movie_sha256"] != EXPECTED_MOVIE_SHA
            or obj["reference_entry"] != 1079
            or obj["native_entry"] != 1081
            or obj["comparison"]["terminal_result_guest_frame"]
               != {"reference_relative": 4704, "native_relative": 4702}
            or obj["comparison"]["terminal_result_frame_matched"] is not False):
        raise ValueError("native trace has no pinned genuine independent Switcher result")
    if (pair["schema"] != "UR-QA01-SWITCHER-PENULTIMATE-SAME-HOST/1"
            or pair["original_absolute_host"] != 5782
            or pair["native_absolute_host"] != 5782
            or pair["result_absolute_host"] != 5783
            or pair["same_host_named_guest_fields_equal"] is not True):
        raise ValueError("paired original/native real same-host Switcher boundary absent")
    if (memory["schema"] != "UR-QA01-SWITCHER-5782-FULL-GUEST-OFFSETS/1"
            or memory["original_host_frame"] != 5782
            or memory["native_host_frame"] != 5782
            or memory["original_movie_input_modified"] is not False
            or memory["release_complete_event_credit"] != 0):
        raise ValueError("full original/native same-host memory offset comparison absent")
    classes = memory["memory_classes"]
    if (classes["wram"]["different_byte_offsets"] != EXPECTED_DIFFS
            or classes["wram"]["offsets_truncated"] is not False
            or classes["vram"]["different_byte_count"] != 0
            or classes["cgram"]["different_byte_count"] != 0):
        raise ValueError("original/native 5782 exact 8-byte WRAM boundary changed")
    return {"course_id": "course:04", "original_entry_host": 1079,
            "native_entry_host": 1081, "same_host_frame": 5782,
            "result_host_frame": 5783, "same_host_original_native_wram_differences": EXPECTED_DIFFS,
            "original_native_result_relative_frame_parity": False,
            "complete_event_release_credit": 0}


def summarize(log_lines, *, first: int = MIN_FRAME, last: int = MAX_FRAME) -> dict:
    if type(first) is not int or type(last) is not int or not 0 <= first < last <= 100000:
        raise ValueError("bad native host-frame gate")
    counts, by_frame, by_scope, by_sp = (Counter(), Counter(), defaultdict(Counter), defaultdict(Counter))
    samples = {f"7E:{a:04X}": deque(maxlen=EXAMPLE_LIMIT) for a in TARGETS}
    observed_total, malformed, last_frame = 0, 0, first
    for line in log_lines:
        if not line.strip():
            continue
        m = WRITE.fullmatch(line.rstrip("\n"))
        if not m:
            raise ValueError("malformed or non-native WRAM log entry")
        frame = int(m.group(1))
        bank, off, word, width = int(m.group(2), 16), int(m.group(3), 16), int(m.group(4), 16), int(m.group(5))
        remainder = m.group(6)
        if (not first <= frame <= last or frame < last_frame
                or bank not in (0x00, 0x7E, 0x80)
                or len(m.group(4)) != width * 2):
            raise ValueError("native WRAM logger escaped the frame or memory scope")
        last_frame = frame
        sp = SP.search(remainder)
        ipc = IPC.search(remainder)
        if sp is None or ipc is None:
            raise ValueError("missing native CPU stack/IPC context")
        scope = remainder.split(" A=", 1)[0]
        if not scope or len(scope) > 200:
            raise ValueError("invalid native recompiler writer scope")
        for i in range(width):
            address = off + i
            if address not in TARGETS:
                continue
            observed_total += 1
            if observed_total > MAX_EVENTS:
                raise ValueError("bounded native trace event budget exceeded")
            a = f"7E:{address:04X}"
            val = (word >> (8 * i)) & 0xFF
            counts[a] += 1
            by_frame[frame] += 1
            by_scope[a][scope] += 1
            by_sp[a][sp.group(1).upper()] += 1
            if len(samples[a]) < EXAMPLE_LIMIT:
                samples[a].append({
                    "native_frame": frame, "native_wa": a,
                    "written_byte": f"{val:02X}",
                    "native_scope": scope, "native_cpu_sp": sp.group(1).upper(),
                    "native_interpreter_pc_scope": ipc.group(1).upper(),
                    "word_width": width,
                })
    if not observed_total:
        raise ValueError("no actual native guest WRAM write attempts in bounded frame window")
    if not any(first <= int(f) <= last for f in by_frame):
        raise ValueError("not a true native original-result boundary")
    return {
        "schema": SCHEMA,
        "sampled_native_frame_window": [first, last],
        "native_guest_wram_write_attempts": observed_total,
        "counts_by_address": dict(sorted(counts.items())),
        "counts_by_native_host_frame": dict(sorted(by_frame.items())),
        "counts_by_address_generated_or_interpreter_scope": {
            k: dict(sorted(v.items())) for k, v in sorted(by_scope.items())},
        "counts_by_address_sp_seen_at_write": {
            k: dict(sorted(v.items())) for k, v in sorted(by_sp.items())},
        "first_five_observed_writes_per_address": {
            k: list(v) for k, v in sorted(samples.items()) if v},
        "no_direct_guest_wram_values_or_complete_memory_dumps": True,
        "scope_limits": (
            "Native WRAM write attempts, not original changed-byte events; native "
            "AOT function scope and IPC are not original instruction PC equivalence. "
            "Logged S may be before or after actual stack decrement; no original/"
            "native complete-event pass, live-byte consumer proof or phase repair."
        ),
        "complete_event_release_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--wlog", type=Path, required=True)
    ap.add_argument("--paired-report", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    paired = validate_paired_guest_report(json.loads(args.paired_report.read_text()))
    with args.wlog.open(encoding="utf-8") as stream:
        result = summarize(stream)
    result["independent_original_native_evidence"] = paired
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "native_write_attempts": result["native_guest_wram_write_attempts"],
        "native_wram_counts": result["counts_by_address"],
        "native_scope_counts": result["counts_by_address_generated_or_interpreter_scope"],
        "original_native_result_guest_frame_parity": False,
        "release_complete_event_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
