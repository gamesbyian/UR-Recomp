#!/usr/bin/env python3
"""RF032 qualify real native queue target and CPU echo after RF030's handshake.

Read two exact original/native replay logs. No inferred phase synchronization
between separate emulator clocks. Refuse unobserved events, truncation,
incorrect CPU-output observers, or any release event credit.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
import qa01_ipl_echo_report as rf030

SCHEMA = "UR-RF032-EXECUTED-NATIVE-QUEUE-TARGET-CPU-ECHO/1"
PREFIX = "QA01RF032 "
KEYS = ("kind", "age", "guest", "target", "port", "value", "raw", "in", "out",
        "pc", "qhead", "qtail", "guestanchor", "targetanchor")
HEX = {"value", "raw", "in", "out", "pc"}
KINDS = {"schedule", "apply", "cpu-poll"}


def parse(log: str) -> list[dict]:
    if "QA01RF032_TRUNCATED" in log or "QA01RF032_CPU_TRUNCATED" in log:
        raise ValueError("RF032 bounded original/native port log truncated")
    rows = []
    for line in log.splitlines():
        if not line.startswith(PREFIX):
            continue
        fields = {}
        for token in line[len(PREFIX):].split():
            if "=" not in token:
                raise ValueError("malformed RF032 field")
            k, v = token.split("=", 1)
            if k not in KEYS or k in fields or not v:
                raise ValueError("unknown or duplicated RF032 field")
            if k == "kind":
                if v not in KINDS:
                    raise ValueError("unrecognized RF032 event kind")
                fields[k] = v
            else:
                if not re.fullmatch("[0-9A-F]+" if k in HEX else "[0-9]+", v):
                    raise ValueError("invalid RF032 numeric field")
                fields[k] = int(v, 16 if k in HEX else 10)
        if set(fields) != set(KEYS):
            raise ValueError("missing source-pinned RF032 fields")
        if fields["port"] != 0 or fields["age"] < 103322420 or fields["age"] > 103323100:
            raise ValueError("RF032 event outside exact CPU port/clock scope")
        if fields["qtail"] < fields["qhead"] or fields["qtail"] - fields["qhead"] > 1024:
            raise ValueError("RF032 source queue underflow/overflow")
        rows.append(fields)
        if len(rows) > 5000:
            raise ValueError("RF032 unexpected high-volume trace")
    if not rows:
        raise ValueError("no observed RF032 native CPU/queue events")
    if [r["age"] for r in rows] != sorted(r["age"] for r in rows):
        raise ValueError("nonmonotonic native SPC age across RF032 events")
    return rows


def summarize(original_log: str, native_log: str) -> dict:
    rf = rf030.summarize(original_log, native_log)
    rows = parse(native_log)
    sched = next((r for r in rows if r["kind"] == "schedule" and r["value"] == 0xcc), None)
    apply = next((r for r in rows if r["kind"] == "apply" and r["value"] == 0xcc), None)
    echo_age = rf["native_ipl_first_cc"]["spc_echo_age"]
    cpu_polls = [r for r in rows if r["kind"] == "cpu-poll"]
    echo_reads = [r for r in cpu_polls if r["value"] == 0xcc and r["age"] >= echo_age]
    if sched is None or apply is None:
        raise ValueError("missing executed native first CC schedule/apply")
    if sched["age"] > apply["age"] or sched["target"] != apply["target"]:
        raise ValueError("stored first CC target mutated/reordered between queue and SPC")
    if apply["target"] > apply["age"]:
        raise ValueError("CPU CC applied before its queued target")
    if not echo_reads:
        raise ValueError("missing executed native CPU first $2140 CC echo poll")
    if not any(r["age"] < echo_reads[0]["age"] and r["value"] == 0xaa for r in cpu_polls):
        raise ValueError("missing native CPU earlier $AA ready-poll sequence")
    return {
        "schema": SCHEMA,
        "case_causality": "read-only original/native genuine source Zoo; no clock-phase correction",
        "release_complete_usa_event_credit": 0,
        "original_cpu_first_cc_echo_age": rf["original_ipl_first_cc"]["first_cpu_poll_echo_age"],
        "original_spc_echo_age": rf["original_ipl_first_cc"]["spc_echo_age"],
        "native_spc_echo_age": echo_age,
        "native_first_cc_schedule": {
            "port_clock": sched["age"],
            "guest_cycle": sched["guest"],
            "stored_target_cycle": sched["target"],
            "guest_anchor": sched["guestanchor"],
            "target_anchor": sched["targetanchor"],
            "queue_depth": sched["qtail"] - sched["qhead"],
        },
        "native_first_cc_apply": {
            "port_clock": apply["age"],
            "stored_target_cycle": apply["target"],
            "applied_minus_stored_target_cycle": apply["age"] - apply["target"],
            "spc_pc": f"{apply['pc']:04X}",
        },
        "native_cpu_first_cc_echo_read": {
            "port_clock": echo_reads[0]["age"],
            "echo_to_cpu_observation_spc_cycles": echo_reads[0]["age"] - echo_age,
            "returned_value": f"{echo_reads[0]['value']:02X}",
            "raw_output_port": f"{echo_reads[0]['raw']:02X}",
            "observer_or_emulator_changed_port_read": echo_reads[0]["value"] != echo_reads[0]["raw"],
            "spc_pc": f"{echo_reads[0]['pc']:04X}",
        },
        "native_cpu_poll_count_in_window": len(cpu_polls),
        "native_queue_observer_records": len(rows),
        "original_native_absolute_spc_ages_independently_calibrated": False,
        "source_rom_movie_sram_and_controllers_checked_by_case_producer": True,
        "all_guest_logic_ticks_or_sound_samples_parity_proven": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-log", type=Path, required=True)
    p.add_argument("--native-log", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error("refuse to overwrite immutable RF032 observer receipt")
    report = summarize(a.original_log.read_text(encoding="utf-8"),
                       a.native_log.read_text(encoding="utf-8"))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
