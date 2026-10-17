#!/usr/bin/env python3
"""RF037 exact artifact CPU/APU port writer report (diagnostic, never acceptance).

Use a source-pinned QA-01 Zoom Zoo Actions case artifact ZIP. The original
port observer uses SPC-age buckets; native port observer uses host frames and
CPU master cycles, and native APU schedule records have target SPC ages.
These axes must NOT be silently equated. A same-value nearest neighbor alone
does not prove a matched transaction or a timing-correction opportunity.
"""
from __future__ import annotations

import argparse
import bisect
from collections import Counter, defaultdict
import hashlib
import io
import json
from pathlib import Path
import zipfile

ORIGINAL_LOG = "work/zoom-zoo/replay/reference.log"
NATIVE_LOG = "work/zoom-zoo/replay/native.log"
TAGS = {
    "QA01RF037ORIGCPU2",
    "QA01RF037ORIGOP_TRUNCATED",
    "QA01RF037NATIVECPU",
    "QA01RF037NATIVEUP",
    "QA01RF037NATIVEBUS",
    "QA01RF037NATIVEUP_TRUNCATED",
    "QA01RF037NATIVECPU_TRUNCATED",
}
STAGES = ("write-reg", "rtl-apu-enter", "rtl-apu-after-filter")


def event(line: str) -> tuple[str, dict[str, str]] | None:
    cells = line.split()
    if not cells or cells[0] not in TAGS:
        return None
    fields = dict(cell.split("=", 1) for cell in cells[1:] if "=" in cell)
    return cells[0], fields


def logs(z: zipfile.ZipFile, name: str):
    with z.open(name) as raw:
        for line in io.TextIOWrapper(raw, encoding="utf-8", errors="replace"):
            parsed = event(line)
            if parsed:
                yield parsed


def _first_last(rows: list[dict[str, str]], n: int = 2):
    return {"count": len(rows), "first": rows[:n], "last": rows[-n:]}


def report(z: zipfile.ZipFile) -> dict:
    original: list[dict[str, str]] = []
    original_trunc: list[int] = []
    for tag, f in logs(z, ORIGINAL_LOG):
        if tag == "QA01RF037ORIGCPU2":
            original.append(f)
        elif tag == "QA01RF037ORIGOP_TRUNCATED":
            original_trunc.append(int(f["frame"]))
    stages: dict[str, list[dict[str, str]]] = defaultdict(list)
    cpu: list[dict[str, str]] = []
    scheduled: list[dict[str, str]] = []
    truncated: list[dict[str, str]] = []
    for tag, f in logs(z, NATIVE_LOG):
        if tag == "QA01RF037NATIVEUP":
            stages[f["kind"]].append(f)
        elif tag == "QA01RF037NATIVECPU":
            cpu.append(f)
        elif tag == "QA01RF037NATIVEBUS" and f.get("kind") == "schedule":
            scheduled.append(f)
        elif tag.endswith("_TRUNCATED"):
            truncated.append({"tag": tag, **f})
    original_by_bucket: dict[int, list[dict[str, str]]] = defaultdict(list)
    for f in original:
        original_by_bucket[int(f["bucket"])].append(f)
    by_frame: dict[int, Counter] = defaultdict(Counter)
    for kind, rows in stages.items():
        for f in rows:
            by_frame[int(f["frame"])][kind] += 1
    for f in cpu:
        by_frame[int(f["frame"])]["cpu_" + f["kind"]] += 1
    orig_index: dict[tuple[int, str], list[int]] = defaultdict(list)
    for f in original:
        orig_index[(int(f["port"]), f["val"])].append(int(f["age"]))
    for ages in orig_index.values():
        ages.sort()
    comparisons = []
    for f in scheduled:
        port, val, age = int(f["port"]), f["val"], int(f["target"])
        ages = orig_index.get((port, val), [])
        j = bisect.bisect_left(ages, age)
        matches = [ages[k] for k in (j - 1, j) if 0 <= k < len(ages)]
        nearest = min(matches, key=lambda v: (abs(v - age), v)) if matches else None
        comparisons.append({
            "native_frame": int(f["frame"]),
            "native_target_spc_age": age,
            "port": port,
            "value": val,
            "nearest_original_same_port_value_spc_age": nearest,
            "native_minus_nearest_original_spc_cycles": (
                age - nearest if nearest is not None else None
            ),
            "is_time_aligned_proof": False,
        })
    case = json.loads(z.read("case-result.json"))
    evidence = case.get("evidence", {})
    sampled = evidence.get("next_bowl_bounded", {})
    return {
        "schema": "rf037-source-writer-report-v1",
        "case": case.get("case"),
        "disposition": case.get("disposition"),
        "original": {
            "port_writes": len(original),
            "age_first_last": [int(original[0]["age"]), int(original[-1]["age"])]
            if original else None,
            "bucket_counts": {str(k): len(v)
                              for k, v in sorted(original_by_bucket.items())},
            "first_last": _first_last(original),
            "opcode_truncated_frames": original_trunc,
        },
        "native": {
            "cpu_writer_count": len(cpu),
            "cpu_writer_types": dict(Counter(f["kind"] for f in cpu)),
            "upstream_stage_counts": {k: len(stages.get(k, [])) for k in STAGES},
            "native_by_frame": {
                str(frame): dict(counts)
                for frame, counts in sorted(by_frame.items())
            },
            "writer_first_last": _first_last(stages.get("rtl-apu-enter", [])),
            "apu_schedule_count": len(scheduled),
            "apu_schedule_first_last": _first_last(scheduled),
            "writer_truncation": truncated,
            "schedule_nearest_source_value": comparisons[:200],
            "schedule_comparison_truncated": len(comparisons) > 200,
        },
        "bounded_control": {
            "original_event_frames": evidence.get("original_event_frames"),
            "native_next_bowl_offset": sampled.get("fresh_native_entry_offset"),
            "original_next_bowl_offset": sampled.get("fresh_original_entry_offset"),
            "all_bounded_sram_samples_equal": sampled.get(
                "all_sampled_sram_pairs_equal"),
            "release_credit": 0,
        },
        "interpretation": (
            "Original writer SPC ages and native writer host frames are "
            "independent. Native APU schedule target ages permit limited "
            "nearest-value diagnostics, not one-to-one causal proof. "
            "Missing writes outside native host gate cannot be inferred."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("case_zip", type=Path)
    p.add_argument("--json-out", type=Path)
    args = p.parse_args()
    if not args.case_zip.is_file():
        p.error("missing case artifact ZIP")
    with zipfile.ZipFile(args.case_zip) as z:
        out = report(z)
    out["case_zip_sha256"] = hashlib.sha256(
        args.case_zip.read_bytes()).hexdigest()
    result = json.dumps(out, sort_keys=True, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
