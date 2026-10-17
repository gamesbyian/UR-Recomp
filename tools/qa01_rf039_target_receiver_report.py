#!/usr/bin/env python3
"""RF039 original/native target SPC receiver analysis; never grants USA acceptance."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import zipfile
from pathlib import Path
from qa01_rf038_sound_write_interval_report import parse_event

ORIGINAL = "work/zoom-zoo/replay/reference.log"
NATIVE = "work/zoom-zoo/replay/native.log"
HOST = 6091
FIRST_NATIVE_MASTER = 2176886834
LAST_NATIVE_MASTER = 2176887208
FIRST_ORIG_AGE = 103919450
LAST_ORIG_AGE = 103919475
ORIG_SPC_AGE_LO = 103918500
ORIG_SPC_AGE_HI = 103920500
TRUNCATIONS = ("QA01RF037ORIGSPC_TRUNCATED", "QA01RF037NATIVEBUS_TRUNCATED",
               "QA01RF037NATIVEUP_TRUNCATED", "QA01RF037ORIGCPU2_TRUNCATED")


def select(log: str, marker: str) -> list[dict]:
    return [row for line in log.splitlines()
            if (row := parse_event(line, marker)) is not None]


def analyze(original_log: str, native_log: str) -> dict:
    for sentinel in TRUNCATIONS:
        if sentinel in original_log or sentinel in native_log:
            raise ValueError("RF039 truncated source recorder: " + sentinel)
    cpu_src = select(original_log, "QA01RF037ORIGCPU2")
    cpu_nat = [r for r in select(native_log, "QA01RF037NATIVEUP")
               if r.get("kind") == "rtl-apu-enter" and int(r["frame"]) == HOST]
    source_before = [r for r in cpu_src
                     if int(r["age"]) == FIRST_ORIG_AGE and
                     int(r["port"]) == 2 and r["val"] == "24"]
    source_after = [r for r in cpu_src
                    if int(r["age"]) == LAST_ORIG_AGE and
                    int(r["port"]) == 3 and r["val"] == "02"]
    native_before = [i for i, r in enumerate(cpu_nat)
                     if int(r["master"]) == FIRST_NATIVE_MASTER
                     and r["reg"].upper() == "2142" and r["val"] == "24"]
    native_after = [i for i, r in enumerate(cpu_nat)
                    if int(r["master"]) == LAST_NATIVE_MASTER
                    and r["reg"].upper() == "2143" and r["val"] == "02"]
    if any(len(x) != 1 for x in
           (source_before, source_after, native_before, native_after)):
        raise ValueError("RF039 source/native CPU writer target missing or duplicated")
    if native_after[0] != native_before[0] + 1:
        raise ValueError("RF039 native writer target no longer consecutive")
    src_spc = [r for r in select(original_log, "QA01RF037ORIGSPC")
               if ORIG_SPC_AGE_LO <= int(r["age"]) <= ORIG_SPC_AGE_HI
               and int(r["port"]) in (2, 3)]
    nat_bus = [r for r in select(native_log, "QA01RF037NATIVEBUS")
               if int(r["frame"]) == HOST and int(r["port"]) in (2, 3)]
    schedules = [r for r in nat_bus if r["kind"] == "schedule"]
    applies = [r for r in nat_bus if r["kind"] == "apply"]
    native_reads = [r for r in nat_bus if r["kind"] == "spc-read"]
    index = native_before[0]
    # Native ordinal reconciliation avoids projecting source SMP age onto the
    # native CPU master clock. If any upstream writes bypass queue scheduling,
    # the positional receiver attribution remains unproven and is rejected.
    matched_schedule_prefix = (
        len(schedules) > index + 1 and
        all(int(c["reg"], 16) & 3 == int(s["port"]) and
            c["val"].upper() == s["val"].upper()
            for c, s in zip(cpu_nat[:index+2], schedules[:index+2]))
    )
    target_schedule = schedules[index:index+2] if matched_schedule_prefix else []
    target_apply = []
    vicinity_reads = []
    if target_schedule:
        targets = [int(r["target"]) for r in target_schedule]
        target_apply = [r for r in applies
                        if any(int(r["target"]) == target and
                               r["port"] == s["port"] and
                               r["val"] == s["val"]
                               for target, s in zip(targets, target_schedule))]
        vicinity_reads = [r for r in native_reads
                          if min(targets)-300 <= int(r["age"]) <= max(targets)+300]
    return {
        "schema": "rf039-target-cpu-spc-receiver-executed-v1",
        "original_cpu_writer_ages": [FIRST_ORIG_AGE, LAST_ORIG_AGE],
        "original_cpu_writer_values": [source_before[0], source_after[0]],
        "native_cpu_writer_masters": [FIRST_NATIVE_MASTER, LAST_NATIVE_MASTER],
        "native_frame": HOST,
        "native_target_local_write_indices_zero_based": [index, index+1],
        "original_spc_recipient_reads_count": len(src_spc),
        "original_spc_recipient_reads": src_spc,
        "native_bus_counts": dict(collections.Counter(r["kind"] for r in nat_bus)),
        "native_schedule_prefix_matches_actual_writers": matched_schedule_prefix,
        "native_target_schedule": target_schedule,
        "native_target_apply": target_apply,
        "native_target_vicinity_spc_reads": vicinity_reads,
        "receiver_coverage_complete": bool(src_spc and matched_schedule_prefix
                                           and len(target_apply) >= 2
                                           and vicinity_reads),
        "source_and_native_clocks_independently_labeled": True,
        "phase_or_bus_order_equivalence_proven": False,
        "clock_fix_justified": False,
        "complete_usa_events_accepted": 0,
    }


def report(case_zip: Path) -> dict:
    with zipfile.ZipFile(case_zip) as z:
        result = analyze(z.read(ORIGINAL).decode("utf8", "replace"),
                         z.read(NATIVE).decode("utf8", "replace"))
    result["case_zip_sha256"] = hashlib.sha256(case_zip.read_bytes()).hexdigest()
    result["case_zip_file"] = case_zip.name
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("case_zip", type=Path)
    p.add_argument("--json-out", type=Path)
    a = p.parse_args()
    value = json.dumps(report(a.case_zip), indent=2, sort_keys=True) + "\n"
    if a.json_out:
        a.json_out.parent.mkdir(parents=True, exist_ok=True)
        a.json_out.write_text(value, encoding="utf8")
    else:
        print(value, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
