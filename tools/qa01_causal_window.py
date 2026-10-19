#!/usr/bin/env python3
"""QA01 read-only causal-window consumer for *executed* ordered guest bus events.

This is a bounded event consumer, not an emulator, instruction-trace producer,
clock synchronizer, WRAM waiver or complete-event admission. Source/native
producer adapters must retain actual executed PC and bus accesses.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA = "ur-qa01-causal-window/1"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
ADDRESS = re.compile(r"7[EF]:[0-9A-F]{4}\Z")
PC = re.compile(r"[0-9A-F]{6}\Z")
KINDS = {"read", "write", "checkpoint"}


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError(why)


def check_guest(data: dict, guest: str) -> None:
    require(type(data) is dict and data.get("schema") == SCHEMA, "wrong causal schema")
    require(data.get("guest") == guest, "wrong guest identity")
    for name, pattern in (("source_sha", HEX40), ("rom_sha256", HEX64),
                          ("movie_sha256", HEX64), ("input_sha256", HEX64)):
        require(type(data.get(name)) is str and bool(pattern.fullmatch(data[name])),
                "invalid or missing " + name)
    w = data.get("window")
    require(type(w) is dict and set(("start", "checkpoint", "end", "phase",
                                    "addresses", "complete", "overflow")) <= set(w),
            "missing causal window contract")
    require(all(type(w[x]) is int for x in ("start", "checkpoint", "end")) and
            w["start"] <= w["checkpoint"] <= w["end"], "invalid frame window")
    require(type(w["phase"]) is str and bool(w["phase"].strip()),
            "missing semantic observation phase")
    require(w["complete"] is True and w["overflow"] is False,
            "source event coverage incomplete or truncated")
    addrs = w["addresses"]
    require(type(addrs) is list and len(addrs) > 0 and len(set(addrs)) == len(addrs)
            and all(type(x) is str and ADDRESS.fullmatch(x) for x in addrs),
            "invalid exact address population")
    observed = data.get("observed")
    require(type(observed) is dict and set(observed) == set(addrs)
            and all(type(x) is int and 0 <= x <= 255 for x in observed.values()),
            "missing raw observed checkpoint bytes")
    ev = data.get("events")
    require(type(ev) is list and len(ev) > 0, "missing executed event rows")
    marks = []
    last_clock = None
    for index, row in enumerate(ev, 1):
        require(type(row) is dict and type(row.get("seq")) is int and
                row["seq"] == index and row.get("kind") in KINDS,
                "missing, duplicate or out-of-order guest-local sequence")
        require(type(row.get("frame")) is int and
                w["start"] <= row["frame"] <= w["end"],
                "event frame outside bounded window")
        require(type(row.get("clock")) is int and row["clock"] >= 0 and
                type(row.get("clock_domain")) is str and row["clock_domain"],
                "missing actual source-local event clock")
        clock = (row["frame"], row["clock"])
        require(last_clock is None or clock >= last_clock,
                "guest local event clock regressed")
        last_clock = clock
        if row["kind"] == "checkpoint":
            require(row["frame"] == w["checkpoint"] and
                    row.get("phase") == w["phase"] and
                    "address" not in row and "value" not in row,
                    "checkpoint phase or sample identity changed")
            marks.append(index - 1)
        else:
            require(row.get("address") in addrs and type(row.get("value")) is int
                    and 0 <= row["value"] <= 255 and
                    type(row.get("pc")) is str and PC.fullmatch(row["pc"]),
                    "missing physical bus address, byte or executed guest PC")
    require(len(marks) == 1, "exactly one real checkpoint is required")
    mark = marks[0]
    # A consumer cannot establish cross-guest clock equivalence. Within a
    # guest, bus read values before the next write must equal the raw sample.
    for address in addrs:
        v = observed[address]
        for row in ev[mark + 1:]:
            if row["kind"] == "checkpoint" or row.get("address") != address:
                continue
            if row["kind"] == "write":
                break
            require(row["value"] == v,
                    "first actual read conflicts with checkpoint memory image")


def guest_fates(data: dict) -> dict:
    ev = data["events"]
    mark = next(i for i, x in enumerate(ev) if x["kind"] == "checkpoint")
    out = {}
    for addr in data["window"]["addresses"]:
        writes = [x for x in ev[:mark] if x["kind"] == "write" and x["address"] == addr]
        last = writes[-1] if writes else None
        first_read, first_write = None, None
        for row in ev[mark + 1:]:
            if row["kind"] == "checkpoint" or row.get("address") != addr:
                continue
            if row["kind"] == "write":
                first_write = row
                break
            if first_read is None:
                first_read = row
        out[addr] = {
            "checkpoint_byte": data["observed"][addr],
            "last_observed_writer_before_checkpoint": last,
            "first_actual_read_before_overwrite": first_read,
            "first_overwrite_after_checkpoint": first_write,
            "fate": ("read_before_overwrite" if first_read else
                     "overwritten_before_read" if first_write else
                     "no_read_or_overwrite_in_bounded_window"),
            "proves_never_read_during_entire_race": False,
        }
    return out


def assess(original: dict, native: dict, original_bytes: bytes, native_bytes: bytes) -> dict:
    check_guest(original, "original")
    check_guest(native, "native")
    for name in ("source_sha", "rom_sha256", "movie_sha256", "input_sha256"):
        require(original[name] == native[name], "original/native input identity differs: " + name)
    for name in ("checkpoint", "phase", "addresses"):
        require(original["window"][name] == native["window"][name],
                "source/native observation scope or semantic phase mismatch: " + name)
    # Distinct start/end ranges are legal. Neither local host clock is
    # rebased or treated as equivalent to the other.
    left, right = guest_fates(original), guest_fates(native)
    results = []
    for addr in original["window"]["addresses"]:
        o, n = left[addr], right[addr]
        ro, rn = o["first_actual_read_before_overwrite"], n["first_actual_read_before_overwrite"]
        different = o["checkpoint_byte"] != n["checkpoint_byte"]
        results.append({
            "address": addr,
            "checkpoint_differs": different,
            "original": o,
            "native": n,
            "matching_guest_pc_of_first_read": bool(ro and rn and ro["pc"] == rn["pc"]),
            "candidate_consumed_value_difference": bool(
                different and ro and rn and ro["pc"] == rn["pc"] and
                ro["value"] != rn["value"]),
            "causal_equivalence_proven": False,
        })
    return {
        "schema": "ur-qa01-causal-window-readonly-report/1",
        "source_sha": original["source_sha"],
        "original_event_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "native_event_sha256": hashlib.sha256(native_bytes).hexdigest(),
        "observation_phase": original["window"]["phase"],
        "original_clock_domain": sorted({x["clock_domain"] for x in original["events"]}),
        "native_clock_domain": sorted({x["clock_domain"] for x in native["events"]}),
        "original_window": original["window"],
        "native_window": native["window"],
        "addresses": results,
        "complete_gameplay_or_instruction_equivalence_proven": False,
        "accepted_complete_USA_events": 0,
        "adjudication": "HOLD: independent raw capture, causal and product review required",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("original", type=Path, help="executed original JSON event payload")
    ap.add_argument("native", type=Path, help="executed native JSON event payload")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    a, b = args.original.read_bytes(), args.native.read_bytes()
    result = assess(json.loads(a), json.loads(b), a, b)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("QA01 causal window: bounded observations only; 0 USA event credit")


if __name__ == "__main__":
    main()
