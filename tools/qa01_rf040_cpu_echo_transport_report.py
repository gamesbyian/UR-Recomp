#!/usr/bin/env python3
"""RF040: audit executed CPU echo return values at real USA Zoo sound writer.

Fail closed on missing/truncated CPU, paced, SPC output, or source writer rows.
CPU/SPC ages are independent between original and native; no timing correction
or course acceptance can be inferred from this local handshake.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ORIGINAL = "work/zoom-zoo/replay/reference.log"
NATIVE = "work/zoom-zoo/replay/native.log"
FIRST_NATIVE_MASTER = 2176886834
LAST_NATIVE_MASTER = 2176887208
ORIGINAL_CPU_H = [508, 600, 652, 704, 756, 808]
ORIGINAL_CPU_RETURN = ["23", "23", "23", "23", "23", "24"]
NATIVE_PACED_MASTERS = [2176886940, 2176886992, 2176887044]
NATIVE_CPU_RETURN = ["23", "23", "24"]
TRUNCATIONS = (
    "QA01RF040ORIGCPU_TRUNCATED",
    "QA01RF040ORIGSPCECHO_TRUNCATED",
    "QA01RF040NATIVECPU_TRUNCATED",
    "QA01RF040NATIVESPCECHO_TRUNCATED",
    "QA01RF038ORIGOP_TRUNCATED",
    "QA01RF038NATIVEPACE_TRUNCATED",
    "QA01RF037NATIVEUP_TRUNCATED",
    "QA01RF037ORIGCPU2_TRUNCATED",
)

def event(line: str, tag: str) -> dict | None:
    if not line.startswith(tag + " "):
        return None
    return dict(part.split("=", 1) for part in line.split()[1:] if "=" in part)

def rows(lines: list[str], tag: str) -> list[tuple[int, dict]]:
    return [(i, x) for i, line in enumerate(lines)
            if (x := event(line, tag)) is not None]

def exactly_one(records: list[tuple[int, dict]], label: str) -> tuple[int, dict]:
    if len(records) != 1:
        raise ValueError(f"RF040 missing or duplicate {label}: {len(records)}")
    return records[0]

def analyze(reference: str, native: str) -> dict:
    for sentinel in TRUNCATIONS:
        if sentinel in reference or sentinel in native:
            raise ValueError("RF040 truncated recorder: " + sentinel)
    o, n = reference.splitlines(), native.splitlines()
    ow = rows(o, "QA01RF037ORIGCPU2")
    nw = rows(n, "QA01RF037NATIVEUP")
    o_start = exactly_one(
        [(i, x) for i, x in ow if x.get("age") == "103919450" and
         x.get("port") == "2" and x.get("val") == "24"], "original port2 writer")
    o_end = exactly_one(
        [(i, x) for i, x in ow if x.get("age") == "103919475" and
         x.get("port") == "3" and x.get("val") == "02"], "original port3 writer")
    n_start = exactly_one(
        [(i, x) for i, x in nw if x.get("kind") == "rtl-apu-enter" and
         x.get("frame") == "6091" and x.get("master") == str(FIRST_NATIVE_MASTER)
         and x.get("reg") == "2142" and x.get("val") == "24"], "native port2 writer")
    n_end = exactly_one(
        [(i, x) for i, x in nw if x.get("kind") == "rtl-apu-enter" and
         x.get("frame") == "6091" and x.get("master") == str(LAST_NATIVE_MASTER)
         and x.get("reg") == "2143" and x.get("val") == "02"], "native port3 writer")
    if not (o_start[0] < o_end[0] and n_start[0] < n_end[0]):
        raise ValueError("RF040 wrong executed writer order")
    o_cpu = [(i, x) for i, x in rows(o, "QA01RF040ORIGCPU")
             if o_start[0] < i < o_end[0]]
    if [int(x["h"]) for _, x in o_cpu] != ORIGINAL_CPU_H or [
            x.get("value") for _, x in o_cpu] != ORIGINAL_CPU_RETURN:
        raise ValueError("RF040 source CPU six-return sequence incomplete or changed")
    op = [(i, x) for i, x in rows(o, "QA01RF038ORIGOP")
          if o_start[0] < i < o_end[0] and
          x.get("frame") == "6091" and x.get("pc") == "82:8301" and
          x.get("opcode") == "CD"]
    if len(op) != 6 or any(
            not (ci < oi and int(ox["post_h"]) == int(cx["h"]) + 6)
            for (ci, cx), (oi, ox) in zip(o_cpu, op)):
        raise ValueError("RF040 actual original opcode read attribution missing")
    n_paced = [(i, x) for i, x in rows(n, "QA01RF038NATIVEPACE")
               if n_start[0] < i < n_end[0] and x.get("frame") == "6091"
               and x.get("op") == "read8" and x.get("bank") == "80"
               and x.get("addr") == "2142"]
    if [int(x["master"]) for _, x in n_paced] != NATIVE_PACED_MASTERS:
        raise ValueError("RF040 actual native paced CPU read count/masters changed")
    n_reads_all = rows(n, "QA01RF040NATIVECPU")
    n_returns = []
    for j, (i, x) in enumerate(n_paced):
        limit = n_paced[j + 1][0] if j + 1 < len(n_paced) else n_end[0]
        match = [(k, r) for k, r in n_reads_all if i < k < limit
                 and r.get("frame") == "6091" and r.get("port") == "2"]
        n_returns.append(exactly_one(match, f"native returned CPU read {j+1}"))
    if [x.get("raw") for _, x in n_returns] != NATIVE_CPU_RETURN or [
            x.get("returned") for _, x in n_returns] != NATIVE_CPU_RETURN:
        raise ValueError("RF040 native returned value or raw/interceptor parity changed")
    o_echo = exactly_one([
        (i, x) for i, x in rows(o, "QA01RF040ORIGSPCECHO")
        if o_start[0] < i < o_end[0] and
        x.get("age") == "103919466" and x.get("pc") == "1555" and
        x.get("value") == "24"], "original SPC F6 echo 24")
    n_echo = exactly_one([
        (i, x) for i, x in rows(n, "QA01RF040NATIVESPCECHO")
        if n_start[0] < i < n_end[0] and x.get("frame") == "6091" and
        x.get("age") == "103919443" and x.get("pc") == "1555" and
        x.get("value") == "24"], "native SPC F6 echo 24")
    if not (o_cpu[4][0] < o_echo[0] < o_cpu[5][0] and
            n_returns[1][0] < n_echo[0] < n_returns[2][0]):
        raise ValueError("RF040 echo publication not between old and new CPU returns")
    if not all(int(x["age"]) <= int(o_echo[1]["age"]) for _, x in o_cpu[:5]):
        raise ValueError("RF040 original old CPU polls exceeded echo age")
    return {
        "schema": "rf040-executed-cpu-echo-source-native-v1",
        "source_original_writer_log_indices": [o_start[0], o_end[0]],
        "native_writer_log_indices": [n_start[0], n_end[0]],
        "original_cpu_polls": [
            {"line_index": i, "beam_h": int(x["h"]),
             "source_spc_age": int(x["age"]), "returned": x["value"]}
            for i, x in o_cpu],
        "original_executed_cmp_abs_82_8301_count": len(op),
        "native_cpu_polls": [
            {"line_index": ri, "native_master": int(pace["master"]),
             "native_spc_age": int(ret["age"]), "spc_pc": ret["pc"],
             "raw": ret["raw"], "returned": ret["returned"]}
            for (_, pace), (ri, ret) in zip(n_paced, n_returns)],
        "original_spc_echo_24": {
            "line_index": o_echo[0], "source_spc_age": int(o_echo[1]["age"]),
            "pc": o_echo[1]["pc"], "value": o_echo[1]["value"]},
        "native_spc_echo_24": {
            "line_index": n_echo[0], "native_spc_age": int(n_echo[1]["age"]),
            "pc": n_echo[1]["pc"], "value": n_echo[1]["value"]},
        "original_source_cpu_writes_spc_age": [103919450, 103919475],
        "native_cpu_write_masters": [FIRST_NATIVE_MASTER, LAST_NATIVE_MASTER],
        "original_minus_native_cpu_writer_elapsed_master": 156,
        "cpu_return_values_and_actual_echo_order_observed": True,
        "receiver_earliest_return_phase_fix_proven": False,
        "cross_guest_absolute_spc_clock_registration_proven": False,
        "source_qualified_timing_change_justified": False,
        "complete_usa_events_admitted": 0,
    }

def report(path: Path, compare_case: Path | None = None) -> dict:
    with zipfile.ZipFile(path) as z:
        o = z.read(ORIGINAL).decode("utf8", "replace")
        n = z.read(NATIVE).decode("utf8", "replace")
        result = analyze(o, n)
        producer = json.loads(z.read("producer-report.json"))
        case = json.loads(z.read("case-result.json"))
    mesh = producer["zoo_race_mesh"]
    if mesh["mesh_checkpoint_count"] != 78 or mesh["raw_byte_exact_sample_count"] != 51 or (
            mesh["masked_or_excluded_wram_bytes"] != 0 or case["release_credit"] != 0
            or case["disposition"] != "strict_candidate"):
        raise ValueError("RF040 unmasked strict Zoo controls changed")
    diff = sum(x["original_native_full_wram_byte_difference"]["differing_byte_count"]
               for x in mesh["samples"])
    if diff != 92:
        raise ValueError("RF040 differing byte count changed")
    result["case_zip_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    result["source_run_sha"] = case["source_sha"]
    result["reference_core_sha256"] = producer["reference_core_sha256"]
    result["native_research_executable_sha256"] = producer["native_executable_sha256"]
    result["strict_controls"] = {
        "original_native_unmasked_wram_pairs": 78,
        "exact_wram_pair_count": 51,
        "unmasked_differing_byte_occurrences": diff,
        "result_relative_zoo_frames": 5163,
        "next_bowl_relative_frames": 267,
        "entire_earned_sram_pair_count": 11,
        "complete_events_accepted": 0,
    }
    if compare_case is not None:
        with zipfile.ZipFile(compare_case) as z:
            prior = json.loads(z.read("producer-report.json"))
        identical = (mesh["samples"] == prior["zoo_race_mesh"]["samples"] and
                     mesh["late_direct_page_window"] ==
                     prior["zoo_race_mesh"]["late_direct_page_window"] and
                     producer["zoo_next_bowl_handoff"] ==
                     prior["zoo_next_bowl_handoff"] and
                     producer["source_terminal_followthrough"] ==
                     prior["source_terminal_followthrough"])
        if not identical:
            raise ValueError("RF040 new observer changed RF039 untouched controls")
        result["rf039_independent_source_and_native_controls_identical"] = True
        result["rf039_control_case_sha256"] = hashlib.sha256(
            compare_case.read_bytes()).hexdigest()
    return result

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("case_zip", type=Path)
    p.add_argument("--compare-case", type=Path)
    p.add_argument("--json-out", type=Path)
    args = p.parse_args()
    result = report(args.case_zip, args.compare_case)
    payload = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf8")
    else:
        print(payload, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
