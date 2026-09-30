#!/usr/bin/env python3
"""Characterize control/non-printable bytes in the recovered Sayans patch.

The translation patch is overwhelmingly readable text. This tool focuses on the
remaining non-printable bytes and asks which ones were preserved from the USA
ROM versus deliberately changed by the translators. Preserved controls are good
candidates for string/layout syntax; changed controls are candidates for length,
position, selector, or other per-string metadata.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

try:
    from tools.analyze_ips_patch import parse_ips, lorom_cpu_address
except ModuleNotFoundError:
    from analyze_ips_patch import parse_ips, lorom_cpu_address


def printable(v: int) -> bool:
    return 32 <= v < 127


def context(data: bytes, index: int, radius: int = 6) -> str:
    a = max(0, index - radius)
    b = min(len(data), index + radius + 1)
    out = []
    for i in range(a, b):
        v = data[i]
        token = chr(v) if printable(v) else f"<{v:02X}>"
        out.append(("[" + token + "]") if i == index else token)
    return "".join(out)


def analyze(base: bytes, patch: bytes) -> dict:
    records, truncate = parse_ips(patch)
    if truncate is not None:
        raise ValueError("unexpected IPS truncate extension")
    frequencies = collections.Counter()
    preserved = collections.Counter()
    changed = collections.Counter()
    examples: dict[int, list[dict]] = collections.defaultdict(list)
    changed_control_pairs = collections.Counter()
    control_runs = collections.Counter()
    control_run_examples: dict[tuple[int, ...], list[dict]] = collections.defaultdict(list)

    total_controls = 0
    for record_index, record in enumerate(records):
        before = base[record.offset:record.end]
        if len(before) != len(record.data):
            raise ValueError("patch record extends beyond base ROM")
        i = 0
        while i < len(record.data):
            if printable(record.data[i]):
                i += 1
                continue
            start = i
            while i < len(record.data) and not printable(record.data[i]):
                i += 1
            run = tuple(record.data[start:i])
            control_runs[run] += 1
            if len(control_run_examples[run]) < 6:
                file_offset = record.offset + start
                control_run_examples[run].append({
                    "record_index": record_index,
                    "file_offset": file_offset,
                    "file_offset_hex": f"0x{file_offset:06X}",
                    "lorom": lorom_cpu_address(file_offset),
                    "before_context": context(before, start, radius=10),
                    "after_context": context(record.data, start, radius=10),
                })

        for i, after_v in enumerate(record.data):
            if printable(after_v):
                continue
            total_controls += 1
            before_v = before[i]
            frequencies[after_v] += 1
            same = before_v == after_v
            (preserved if same else changed)[after_v] += 1
            if not same:
                changed_control_pairs[(before_v, after_v)] += 1
            if len(examples[after_v]) < 8:
                file_offset = record.offset + i
                examples[after_v].append({
                    "record_index": record_index,
                    "file_offset": file_offset,
                    "file_offset_hex": f"0x{file_offset:06X}",
                    "lorom": lorom_cpu_address(file_offset),
                    "before": f"0x{before_v:02X}",
                    "after": f"0x{after_v:02X}",
                    "preserved": same,
                    "before_context": context(before, i),
                    "after_context": context(record.data, i),
                })

    values = []
    for value in sorted(frequencies):
        values.append({
            "value": value,
            "hex": f"0x{value:02X}",
            "count": frequencies[value],
            "preserved_count": preserved[value],
            "changed_count": changed[value],
            "preserved_fraction": (
                preserved[value] / frequencies[value] if frequencies[value] else 0.0
            ),
            "examples": examples[value],
        })

    return {
        "schema_version": 1,
        "record_count": len(records),
        "total_nonprintable_after_bytes": total_controls,
        "control_values": values,
        "control_runs": [
            {
                "bytes": list(run),
                "hex": " ".join(f"{v:02X}" for v in run),
                "length": len(run),
                "count": count,
                "examples": control_run_examples[run],
            }
            for run, count in sorted(
                control_runs.items(),
                key=lambda item: (-item[1], -len(item[0]), item[0]),
            )
        ],
        "changed_control_pairs": [
            {
                "before": f"0x{a:02X}",
                "after": f"0x{b:02X}",
                "count": count,
            }
            for (a, b), count in sorted(
                changed_control_pairs.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
        "interpretation_guardrails": [
            "non-printable does not automatically mean control code",
            "high preservation across translated strings is evidence for syntax, not semantics",
            "changed controls may encode length/layout but require reader/runtime evidence",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("base_rom", type=Path)
    ap.add_argument("ips_patch", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = analyze(args.base_rom.read_bytes(), args.ips_patch.read_bytes())
    print(
        f"records={report['record_count']} "
        f"controls={report['total_nonprintable_after_bytes']} "
        f"values={len(report['control_values'])}"
    )
    for row in report["control_values"]:
        print(
            f"{row['hex']}: count={row['count']} "
            f"preserved={row['preserved_count']} changed={row['changed_count']}"
        )
    print("changed pairs:")
    for row in report["changed_control_pairs"]:
        print(f"  {row['before']}->{row['after']}: {row['count']}")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
