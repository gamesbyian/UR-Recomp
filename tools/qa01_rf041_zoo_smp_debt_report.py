#!/usr/bin/env python3
"""RF041 exact original SMP clock debt versus native queue/F6 boundary.

A bounded read-only provenance receipt. Cross-guest absolute SPC ages are NOT
aligned and a source-qualified CPU/APU timing correction is not implied.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ORIG = "work/zoom-zoo/replay/reference.log"
NATIVE = "work/zoom-zoo/replay/native.log"
TRUNC = (
    "QA01RF041ORIGF6_TRUNCATED", "QA01RF041NATIVE_TRUNCATED",
    "QA01RF037ORIGSPC_TRUNCATED", "QA01RF037NATIVEBUS_TRUNCATED",
    "QA01RF037ORIGCPU2_TRUNCATED",
)

def event(line: str, marker: str) -> dict | None:
    if not line.startswith(marker + " "):
        return None
    return dict(bit.split("=", 1) for bit in line.split()[1:] if "=" in bit)

def matching(lines: list[str], tag: str, **terms: str) -> list[tuple[int, dict]]:
    found = []
    for i, line in enumerate(lines):
        x = event(line, tag)
        if x is not None and all(x.get(k) == v for k, v in terms.items()):
            found.append((i, x))
    return found

def one(lines: list[str], tag: str, label: str, **terms: str) -> tuple[int, dict]:
    rows = matching(lines, tag, **terms)
    if len(rows) != 1:
        raise ValueError(f"RF041 missing/duplicate {label}: {len(rows)}")
    return rows[0]

def analyze(source: str, native: str) -> dict:
    for marker in TRUNC:
        if marker in source or marker in native:
            raise ValueError("RF041 truncated observer: " + marker)
    o, n = source.splitlines(), native.splitlines()
    phases = ["before-sync", "after-sync-before-publish", "after-publish"]
    cpu = [one(o, "QA01RF041ORIGCPU", p, phase=p, port="2", value="24")
           for p in phases]
    if not cpu[0][0] < cpu[1][0] < cpu[2][0]:
        raise ValueError("RF041 source CPU sync/publication phase order changed")
    real_writer = one(o, "QA01RF037ORIGCPU2", "original CPU target writer",
                      age="103919450", port="2", val="24")
    if not (int(cpu[0][1]["age"]) <= int(cpu[1][1]["age"]) <=
            int(cpu[2][1]["age"])):
        raise ValueError("RF041 original SMP local age went backwards")
    read_old = one(o, "QA01RF037ORIGSPC", "original old F6 recipient",
                   age="103919450", pc="154F", port="2", val="23")
    read_new = one(o, "QA01RF037ORIGSPC", "original first new F6 recipient",
                   age="103919457", pc="154F", port="2", val="24")
    debt_old = one(o, "QA01RF041ORIGF6", "original old-value F6 debt",
                   age="103919450", pc="154F", port="2", val="23")
    debt_new = one(o, "QA01RF041ORIGF6", "original new-value F6 debt",
                   age="103919457", pc="154F", port="2", val="24")
    if not (read_old[0] < real_writer[0] < read_new[0]):
        raise ValueError("RF041 lost source read-old before publish ordering")
    if not (read_old[0] < debt_old[0] < read_new[0] < debt_new[0]):
        raise ValueError("RF041 original source F6 debt not paired with real reads")
    native_apply = one(n, "QA01RF041NATIVE", "native target port2 apply",
                       kind="apply", frame="6091", age="103919434",
                       target="103919434", port="2", val="24")
    native_read = one(n, "QA01RF041NATIVE", "native first-new F6 read",
                      kind="spc-read", frame="6091", age="103919434",
                      port="2", val="24")
    native_old = one(n, "QA01RF041NATIVE", "native old F6 read",
                     kind="spc-read", frame="6091", age="103919427",
                     port="2", val="23")
    if not native_old[0] < native_apply[0] < native_read[0]:
        raise ValueError("RF041 lost native queue-apply before F6 new-read order")
    full_native_apply = one(n, "QA01RF037NATIVEBUS", "actual native queued apply",
                            kind="apply", frame="6091", age="103919434",
                            target="103919434", port="2", val="24")
    full_native_read = one(n, "QA01RF037NATIVEBUS", "actual native F6 read",
                           kind="spc-read", frame="6091", age="103919434",
                           pc="154F", port="2", val="24")
    if not full_native_apply[0] < native_apply[0] < full_native_read[0] < native_read[0]:
        raise ValueError("RF041 native debt markers detached from real queue/F6")
    return {
        "schema": "rf041-executed-zoo-smp-debt-boundary-v1",
        "source_cpu_sync_and_publication": [
            {"line_index": i, **v} for i, v in cpu],
        "source_old_f6_read": {"line_index": read_old[0], **read_old[1]},
        "source_new_f6_read": {"line_index": read_new[0], **read_new[1]},
        "source_f6_debt_old_and_new": [
            {"line_index": i, **v} for i, v in (debt_old, debt_new)],
        "source_cpu_port2_publication": {"line_index": real_writer[0], **real_writer[1]},
        "native_old_f6": {"line_index": native_old[0], **native_old[1]},
        "native_queue_apply": {"line_index": native_apply[0], **native_apply[1]},
        "native_first_new_f6": {"line_index": native_read[0], **native_read[1]},
        "original_read_old_precedes_publication_same_local_age": True,
        "native_applied_new_precedes_f6_read_same_local_age": True,
        "absolute_original_native_spc_clock_phase_equivalent": False,
        "source_qualified_scheduling_fix_proven": False,
        "entire_usa_event_accepted": False,
        "accepted_usa_events": 0,
    }

def report(path: Path, control_path: Path | None = None) -> dict:
    with zipfile.ZipFile(path) as z:
        result = analyze(z.read(ORIG).decode("utf8", "replace"),
                         z.read(NATIVE).decode("utf8", "replace"))
        producer = json.loads(z.read("producer-report.json"))
        case = json.loads(z.read("case-result.json"))
    mesh = producer["zoo_race_mesh"]
    if (mesh["mesh_checkpoint_count"] != 78 or
            mesh["raw_byte_exact_sample_count"] != 51 or
            mesh["masked_or_excluded_wram_bytes"] != 0 or
            case["disposition"] != "strict_candidate" or
            case["release_credit"] != 0):
        raise ValueError("RF041 strict Zoo control failure")
    count = sum(s["original_native_full_wram_byte_difference"]["differing_byte_count"]
                for s in mesh["samples"])
    if count != 92:
        raise ValueError("RF041 changed unmasked Zoo residual count")
    result["case_zip_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    result["frozen_research_head"] = case["source_sha"]
    result["original_core_sha256"] = producer["reference_core_sha256"]
    result["native_elf_sha256"] = producer["native_executable_sha256"]
    result["unmasked_zoo_samples"] = 78
    result["exact_full_wram_sample_pairs"] = 51
    result["unmasked_byte_difference_occurrences"] = count
    if control_path:
        with zipfile.ZipFile(control_path) as z:
            p = json.loads(z.read("producer-report.json"))
        exact = (mesh["samples"] == p["zoo_race_mesh"]["samples"] and
                 mesh["late_direct_page_window"] ==
                 p["zoo_race_mesh"]["late_direct_page_window"] and
                 producer["zoo_next_bowl_handoff"] == p["zoo_next_bowl_handoff"] and
                 producer["source_terminal_followthrough"] ==
                 p["source_terminal_followthrough"])
        if not exact:
            raise ValueError("RF041 changed previously verified RF040 control values")
        result["prior_control_case_zip_sha256"] = hashlib.sha256(
            control_path.read_bytes()).hexdigest()
        result["all_controls_bit_identical_to_rf040"] = True
    return result

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("case_zip", type=Path)
    p.add_argument("--compare-case", type=Path)
    p.add_argument("--json-out", type=Path)
    a = p.parse_args()
    value = json.dumps(report(a.case_zip, a.compare_case), indent=2,
                       sort_keys=True) + "\n"
    if a.json_out:
        a.json_out.parent.mkdir(parents=True, exist_ok=True)
        a.json_out.write_text(value, encoding="utf8")
    else:
        print(value, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
