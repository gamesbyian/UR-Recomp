#!/usr/bin/env python3
"""QA-01 RF-015: fail-closed *actual-log* APU queue/clock phase preflight.

Requires genuine separately executed original Snes9x opcode trace and Baldosa
APU port trace created by qa01_apu_phase_observers.py. Each engine retains its
own frame/CPU/APU clock. No host-frame alignment, matched instruction, runtime
fix or complete-event admission is inferred from independent event counts.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import re
from pathlib import Path

SCHEMA = "UR-QA01-RF015-SOURCE-NATIVE-APU-EDGE-TRACE/1"
ORIGINAL = "QA01APUORIG "
NATIVE = "QA01APUNATIVE "
MAX_EVENTS = 6000
PC_OP = {
    "82803C": "AD",  # byte-read $2142
    "828043": "D0",  # BNE source APU ack
    "82804E": "F0",  # BEQ empty queue
    "828059": "8F",  # APU queue toggle
    "828066": "8F",  # APU read pointer
    "82806D": "8D",  # word-write $2142/$2143
    "80FADB": "20",  # post-wait continuation
    "80FAE2": "C6",  # cursor animation tick
}
ORIG_KEYS = ("f0", "f1", "v0", "v1", "h0", "h1", "pc", "next",
             "op", "p0", "p1", "db0", "db1", "a0", "a1", "rd0", "rd1",
             "wr0", "wr1", "ack0", "ack1", "c60", "c61")
NATIVE_KEYS = ("f", "dir", "reg", "width", "value", "cpu_master",
               "apu_cycle", "spc_portclock", "frame_clock", "extended",
               "memsel", "rd", "wr", "ack", "c6")
ORIG_HEX = {"pc", "next", "op", "p0", "p1", "db0", "db1", "a0", "a1", "rd0", "rd1",
            "wr0", "wr1", "ack0", "ack1", "c60", "c61"}
NATIVE_HEX = {"reg", "value", "rd", "wr", "ack", "c6"}


def events(raw: str, prefix: str, keys: tuple[str, ...],
           hex_keys: set[str]) -> list[dict]:
    if prefix == ORIGINAL and "QA01APUORIG_TRUNCATED" in raw:
        raise ValueError("original APU opcode trace was truncated")
    if prefix == NATIVE and "QA01APUNATIVE_TRUNCATED" in raw:
        raise ValueError("native APU port trace was truncated")
    out: list[dict] = []
    for line in raw.splitlines():
        if not line.startswith(prefix):
            continue
        fields = {}
        for word in line[len(prefix):].split():
            if "=" not in word:
                raise ValueError("malformed APU trace field")
            k, v = word.split("=", 1)
            if k in fields or k not in keys or not v:
                raise ValueError("duplicate/unknown/empty APU trace field")
            fields[k] = v
        if set(fields) != set(keys):
            raise ValueError("incomplete APU trace record")
        parsed = {}
        for key in keys:
            val = fields[key]
            if key == "dir":
                if val not in ("R", "W"):
                    raise ValueError("native APU direction must be R or W")
                parsed[key] = val
            else:
                if key in hex_keys and not re.fullmatch(r"[0-9A-F]+", val):
                    raise ValueError("malformed uppercase hex APU field")
                if key not in hex_keys and not re.fullmatch(r"-?[0-9]+", val):
                    raise ValueError("malformed decimal APU field")
                parsed[key] = int(val, 16 if key in hex_keys else 10)
        out.append(parsed)
        if len(out) > MAX_EVENTS:
            raise ValueError("unbounded APU trace")
    if not out:
        raise ValueError("no real opt-in APU trace receipts for " + prefix)
    return out


def pair_original_ack_reads(source: list[dict]) -> dict:
    """Link executed original $2142 loads to *their own* observed BNE.

    The source trace is a sparse executed-PC stream. Pair only adjacent
    recorded 82:803C -> 82:8043 events with a bounded original frame
    transition. Do not use PL.Z as proof of branch direction: Snes9x may
    maintain lazy processor flags outside Registers.PL. Never align these
    original CPU frames with native AOT host/APU frames here.
    """
    pairs = []
    used_reads = set()
    branches = 0
    for i, event in enumerate(source):
        if event["pc"] != 0x828043:
            continue
        branches += 1
        if i == 0:
            continue
        previous = source[i - 1]
        if (previous["pc"] != 0x82803C or
            event["f0"] < previous["f1"] or
            event["f0"] - previous["f1"] > 1):
            continue
        used_reads.add(i - 1)
        pairs.append({
            "original_read_frame": previous["f0"],
            "original_read_end_frame": previous["f1"],
            "original_branch_frame": event["f0"],
            "read_low_byte": previous["a1"] & 0xFF,
            "original_read_data_bank": previous["db0"],
            "observed_bne_destination": f"{event['next']:06X}",
            "observed_bne_taken": event["next"] == 0x828077,
            "source_queue_read_index": previous["rd1"],
            "source_queue_write_index": previous["wr1"],
            "source_apu_toggle": previous["ack1"],
        })
    read_count = sum(event["pc"] == 0x82803C for event in source)
    return {
        "original_ack_read_branch_pairs_count": len(pairs),
        "original_ack_read_branch_pairs_sample": pairs[:16],
        "original_unpaired_apu_reads": read_count - len(used_reads),
        "original_unpaired_ack_branches": branches - len(pairs),
        "original_ack_read_branch_pairs_complete": (
            len(pairs) == read_count == branches),
        "original_ack_pairs_same_original_cpu_stream_only": True,
    }


def analyze(original_log: str, native_log: str) -> dict:
    ref = events(original_log, ORIGINAL, ORIG_KEYS, ORIG_HEX)
    guest = events(native_log, NATIVE, NATIVE_KEYS, NATIVE_HEX)
    if any(e["f0"] > e["f1"] or not 0 <= e["v0"] <= 262 or
           not 0 <= e["v1"] <= 262 for e in ref):
        raise ValueError("invalid original opcode frame/v-counter receipt")
    if [e["f0"] for e in ref] != sorted(e["f0"] for e in ref):
        raise ValueError("original Snes9x event frames not monotonic")
    if [e["f"] for e in guest] != sorted(e["f"] for e in guest):
        raise ValueError("native host event frames not monotonic")
    for e in ref:
        pc = f"{e['pc']:06X}"
        if pc not in PC_OP or e["op"] != int(PC_OP[pc], 16):
            raise ValueError("original opcode PC/opcode not qualified")
        if pc in ("82803C", "82806D"):
            # Absolute $2142 is an actual SNES I/O register only when
            # the CPU DBR selects a low-bank 00-3F / 80-BF hardware mirror.
            # DBR 7E/7F would address WRAM instead, falsifying the claim.
            if (not 0 <= e["db0"] <= 255 or not 0 <= e["db1"] <= 255
                    or e["db0"] & 0x40 or e["db0"] != e["db1"]):
                raise ValueError("original $2142 opcode did not retain a mapped CPU I/O data bank")
        if pc in ("82803C", "828043", "82804E"):
            if not e["p0"] & 0x20:
                raise ValueError("original source 8-bit APU input width unverified")
        if pc == "82806D" and (e["p0"] & 0x20):
            raise ValueError("original source 16-bit outgoing APU word unverified")
        if pc == "828043" and e["next"] not in (0x828045, 0x828077):
            raise ValueError("invalid original APU ack branch target")
        if pc == "82804E" and e["next"] not in (0x828050, 0x828077):
            raise ValueError("invalid original queue-empty branch target")
        for k in ("rd0", "rd1", "wr0", "wr1", "ack0", "ack1", "c60", "c61"):
            if not 0 <= e[k] <= 255:
                raise ValueError("original queue byte out of range")
    for e in guest:
        if e["reg"] != 0x2142 or e["width"] != (1 if e["dir"] == "R" else 2):
            raise ValueError("native trace is not genuine port-2 input/word output")
        if e["frame_clock"] not in (0, 1) or e["extended"] not in (0, 1):
            raise ValueError("unrecognized native APU guest clock mode")
        if e["memsel"] not in (0, 1):
            raise ValueError("unrecognized native MEMSEL")
        if e["value"] > (255 if e["dir"] == "R" else 65535):
            raise ValueError("native APU port value exceeds data width")
        if any(not 0 <= e[k] <= 255 for k in ("rd", "wr", "ack", "c6")):
            raise ValueError("native queue byte out of range")
    original_read = [e for e in ref if e["pc"] == 0x82803C]
    ack_branch = [e for e in ref if e["pc"] == 0x828043]
    native_read = [e for e in guest if e["dir"] == "R"]
    if not original_read or not ack_branch or not native_read:
        raise ValueError("missing actual original 82:803C/8043 or native $2142 read")
    ack_pairs = pair_original_ack_reads(ref)
    return {
        "schema": SCHEMA,
        **ack_pairs,
        "original_events": len(ref),
        "native_events": len(guest),
        "original_first_frame": ref[0]["f0"],
        "original_last_frame": ref[-1]["f0"],
        "native_first_frame": guest[0]["f"],
        "native_last_frame": guest[-1]["f"],
        "original_apu_read_count": len(original_read),
        "original_apu_data_banks_observed": sorted(set(
            e["db0"] for e in ref if e["pc"] in (0x82803C, 0x82806D))),
        "original_apu_opcode_effective_bank_hw_mapped": True,
        "original_apu_read_low_bytes_sample": [
            e["a1"] & 255 for e in original_read[:16]],
        "original_ack_branch_count": len(ack_branch),
        "original_ack_branch_taken": sum(
            e["next"] == 0x828077 for e in ack_branch),
        "original_ack_branch_not_taken": sum(
            e["next"] == 0x828045 for e in ack_branch),
        "original_queue_empty_branch_taken": sum(
            e["pc"] == 0x82804E and e["next"] == 0x828077 for e in ref),
        "native_apu_read_count": len(native_read),
        "native_apu_read_low_bytes_sample": [e["value"] for e in native_read[:16]],
        "native_apu_word_write_count": sum(e["dir"] == "W" for e in guest),
        "native_frame_clock_modes_observed": sorted(set(
            e["frame_clock"] for e in guest)),
        "native_memsel_modes_observed": sorted(set(e["memsel"] for e in guest)),
        "trace_truncation_detected": False,
        "source_and_native_frames_calibrated_equivalent": False,
        "source_cpu_pc_equals_native_AOT_function_scope_proven": False,
        "native_apu_port_read_clock_equals_source_opcode_instant_proven": False,
        "source_same_movie_guest_identity_proven_by_logs_alone": False,
        "apu_handshake_caused_RF015_proven": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-log", type=Path, required=True)
    p.add_argument("--native-log", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error("refuse to overwrite a source/native APU report")
    report = analyze(a.original_log.read_text(encoding="utf-8"),
                     a.native_log.read_text(encoding="utf-8"))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    print(json.dumps({
        "source_read_count": report["original_apu_read_count"],
        "native_read_count": report["native_apu_read_count"],
        "apu_cause_proven": False,
        "strict_event_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
