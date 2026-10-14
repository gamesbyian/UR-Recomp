#!/usr/bin/env python3
"""QA-01 Zoo: source original opcode changes vs native text-cursor write attempts.

Works on ORIGINAL and NATIVE executable logs already produced by the pinned
2014 Zoo scene producer. Original ZOOPCWRITE records *changes*; the native
CPU-helper journal records *attempted writes*, including idempotent writes.
Do not mistake extra native attempts for a gameplay timing disagreement.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

from qa01_zoo_terminal_writer_crosswalk import logged_frames

SCHEMA = "UR-QA01-ZOO-RESULT-TEXT-CURSOR-CROSSWALK/1"
ADDR = "7E:009F"
ORIGINAL = re.compile(
    r"^ZOOPCWRITE f=(\d+) v=(\d+) pc=([0-9A-Fa-f]{6}) "
    r"addr=009F old=([0-9A-Fa-f]{2}) new=([0-9A-Fa-f]{2})$"
)
NATIVE = re.compile(
    r"^f\s*(\d+)\s+([0-9A-Fa-f]{2}):009F=([0-9A-Fa-f]{2,4}) "
    r"w([12]) (.+)$"
)
PINNED_ORIGINAL_LOG_SHA = "c51fadac1005bdcf7cf3b1925ba50d5829fc14230a2ee76b21f349082826cd62"
PINNED_NATIVE_LOG_SHA = "e7bcdfe6bb0f3b59667c05b6d59363fb46df9591c82485aa06c23ce2c2b0d7b6"


def digest(s: str) -> str:
    return sha256(s.encode("utf-8")).hexdigest()


def parse_original(log: str) -> list[dict]:
    rows = []
    for line in log.splitlines():
        if "ZOOPCWRITE" not in line or "addr=009F" not in line:
            continue
        m = ORIGINAL.fullmatch(line)
        if m is None:
            raise ValueError("malformed original 009F opcode receipt")
        frame, v, pc, before, after = m.groups()
        before, after = int(before, 16), int(after, 16)
        if before == after:
            raise ValueError("original opcode-change receipt claimed a no-op")
        rows.append({
            "frame": int(frame), "v_counter": int(v),
            "pc": pc.upper()[:2] + ":" + pc.upper()[2:],
            "old": before, "new": after,
        })
    if len(rows) < 2:
        raise ValueError("missing source-original text cursor opcode sequence")
    return rows


def parse_native(log: str) -> list[dict]:
    rows = []
    for line in log.splitlines():
        if ":009F=" not in line:
            continue
        m = NATIVE.fullmatch(line.strip())
        if m is None:
            raise ValueError("malformed native 009F CPU helper receipt")
        frame, bank, raw, width, scope = m.groups()
        bank_i, width_i = int(bank, 16), int(width)
        if bank_i not in (0, 0x7E, 0x80) or width_i not in (1, 2):
            raise ValueError("unrecognized native 009F WRAM address/width")
        rows.append({
            "frame": int(frame), "bank": bank.upper(), "width": width_i,
            "byte": int(raw, 16) & 0xFF, "scope": scope,
        })
    if not rows:
        raise ValueError("missing native text cursor CPU-helper stores")
    return rows


def analyze(original_log: str, native_log: str,
            original_host_log: str, native_host_log: str) -> dict:
    source_entry, source_ticks = logged_frames(original_host_log)
    native_entry, native_ticks = logged_frames(native_host_log)
    src = parse_original(original_log)
    nat = parse_native(native_log)

    # The standalone source historical result has an independently observed
    # cursor reset before text painting; the native helper logger did not
    # observe a corresponding reset, so it MUST NOT be invented or matched.
    reset = src[0]
    if (reset["pc"], reset["old"], reset["new"]) != ("83:988A", 0x84, 0x16):
        raise ValueError("original 2014 Zoo result-text cursor reset drifted")
    if not source_entry + 5152 <= reset["frame"] <= source_entry + 5162:
        raise ValueError("original cursor reset not in measured event boundary")
    painted = src[1:]
    if any(row["old"] != (reset["new"] if i == 0 else painted[i-1]["new"])
           for i, row in enumerate(painted)):
        raise ValueError("original source cursor changes have a missing/unattributed writer")
    if any(not source_entry + 5152 <= row["frame"] <= source_entry + 5163
           for row in painted):
        raise ValueError("original text writes escaped measured result boundary")
    if any(not native_entry + 5152 <= row["frame"] <= native_entry + 5163
           for row in nat):
        raise ValueError("native text attempts escaped measured result boundary")

    # Native logger captures all CPU helper attempts, including stores of a
    # value already in memory. Original pre/post opcode delta logging emits
    # only changed bytes. A native repeated value is therefore not evidence
    # of an additional source-visible mutation.
    last = reset["new"]
    mutations, noops = [], []
    for idx, row in enumerate(nat):
        if row["byte"] == last:
            noops.append({"attempt_index": idx, "value": f"{last:02X}",
                          "native_scope": row["scope"]})
        else:
            mutations.append(row)
            last = row["byte"]
    actual_source = [w["new"] for w in painted]
    actual_native = [w["byte"] for w in mutations]
    disagreement = next(
        (i for i, (x, y) in enumerate(zip(actual_source, actual_native)) if x != y),
        None,
    )
    if disagreement is None and len(actual_source) != len(actual_native):
        disagreement = min(len(actual_source), len(actual_native))
    equality = disagreement is None
    source_pc_counts = dict(sorted(Counter(w["pc"] for w in src).items()))
    native_scope_counts = dict(sorted(Counter(w["scope"] for w in nat).items()))
    identity = (digest(original_log) == PINNED_ORIGINAL_LOG_SHA and
                digest(native_log) == PINNED_NATIVE_LOG_SHA)
    return {
        "schema": SCHEMA,
        "original_scene_entry_host": source_entry,
        "native_scene_entry_host": native_entry,
        "original_attested_boundary_dump_hosts": source_ticks,
        "native_attested_boundary_dump_hosts": native_ticks,
        "source_original_log_sha256": digest(original_log),
        "native_log_sha256": digest(native_log),
        "exact_executed_38500427634_log_pair_verified": identity,
        "source_cursor_reset": reset,
        "original_changed_byte_receipts": len(src),
        "original_painted_byte_mutations_after_reset": len(actual_source),
        "native_cpu_helper_write_attempts": len(nat),
        "native_idempotent_write_attempts": noops,
        "native_mutating_attempts_after_deduplication": len(actual_native),
        "source_changed_value_sequence_sha256": digest(bytes(actual_source).hex()),
        "native_mutating_value_sequence_sha256": digest(bytes(actual_native).hex()),
        "observed_mutating_cursor_values_exact_same_order": equality,
        "first_observed_value_disagreement": disagreement,
        "original_first_paint_opcode": painted[0],
        "original_last_paint_opcode": painted[-1],
        "native_first_paint_scope": nat[0],
        "native_last_paint_scope": nat[-1],
        "source_original_pc_counts": source_pc_counts,
        "native_cpu_helper_scope_counts": native_scope_counts,
        "last_cursor_value_original": f"{actual_source[-1]:02X}",
        "last_cursor_value_native": f"{actual_native[-1]:02X}",
        "both_last_cursor_values_bc": actual_source[-1] == actual_native[-1] == 0xBC,
        "native_unobserved_cursor_reset_not_assumed": True,
        "cpu_frame_and_ppu_phase_equivalence_proven": False,
        "guest_relative_full_result_onset_equivalent": False,
        "qa01_complete_event_credit": 0,
        "disposition": (
            "bounded_source_native_changed_value_order_agrees"
            if equality else "bounded_changed_value_order_disagrees"
        ),
        "guardrail": (
            "009F is demonstrably mutated by text-drawing instructions, not "
            "a proven dedicated gameplay result-state latch. Source opcode "
            "change receipts omit idempotent stores; native CPU-helper write "
            "attempts include them. Value-stream equality cannot calibrate "
            "guest CPU/NMI/beam phase, demonstrate unchanged gameplay state, "
            "or approve any original/native complete course."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("original-trace", "native-trace", "original-host-log",
                 "native-host-log", "out"):
        ap.add_argument("--" + name, type=Path, required=True)
    args = ap.parse_args()
    data = analyze(args.original_trace.read_text(),
                   args.native_trace.read_text(),
                   args.original_host_log.read_text(),
                   args.native_host_log.read_text())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        k: data[k] for k in (
            "disposition", "original_painted_byte_mutations_after_reset",
            "native_cpu_helper_write_attempts", "native_idempotent_write_attempts",
            "observed_mutating_cursor_values_exact_same_order",
            "qa01_complete_event_credit")
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
