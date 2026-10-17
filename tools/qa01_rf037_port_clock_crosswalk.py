#!/usr/bin/env python3
"""Diagnostic RF037 source/native writer-clock crosswalk. Not a clock fix.

Compares actual original SPC-age-at-CPU-port publication with native CPU
master time at RtlApuWrite entry for matched port/value pairs. The nominal
SPC/master ratio is a projection, NOT a verified SPC receiver timestamp.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from statistics import median
import zipfile

from qa01_rf037_port_writer_report import (
    ORIGINAL_LOG, NATIVE_LOG, logs, canonical_original_equal_age_pairs,
)

SPC_PER_MASTER = Fraction(15664, 328125)


def stats(values):
    return {"count": len(values),
            "min_spc_cycles": round(min(values), 3),
            "median_spc_cycles": round(median(values), 3),
            "max_spc_cycles": round(max(values), 3)}


def crosswalk(original: list[dict], native: list[dict],
              truncated: list[dict] | None = None,
              source_truncated: list[dict] | None = None) -> dict:
    if truncated:
        raise ValueError("native upstream capture truncated")
    if source_truncated:
        raise ValueError("original source port capture truncated")
    if not original or len(native) < len(original):
        raise ValueError("missing native port publication or unbalanced capture")
    canonical = canonical_original_equal_age_pairs(original)
    source = canonical["rows"]
    pairs = list(zip(source, native[:len(source)]))
    for index, (a, b) in enumerate(pairs):
        if (int(a["port"]), int(a["val"], 16)) != (
                int(b["reg"], 16) & 3, int(b["val"], 16)):
            raise ValueError(f"port/value pair mismatch at ordinal {index}")
    anchor_age = int(source[0]["age"])
    anchor_master = int(native[0]["master"])
    frame_residuals = defaultdict(list)
    frame_ports = defaultdict(lambda: defaultdict(list))
    last_native_master = anchor_master
    last_source_age = anchor_age
    for a, b in pairs:
        if int(a["age"]) < last_source_age:
            raise ValueError("original source SPC ages not monotone")
        last_source_age = int(a["age"])
        master = int(b["master"])
        if master < last_native_master:
            raise ValueError("native master clock is not monotone")
        last_native_master = master
        residual = float((int(a["age"]) - anchor_age) -
                         (master - anchor_master) * SPC_PER_MASTER)
        frame = int(b["frame"])
        frame_residuals[frame].append(residual)
        frame_ports[frame][int(a["port"])].append(residual)
    return {
        "schema": "rf037-writer-clock-crosswalk-v1",
        "original_port_publications": len(source),
        "native_port_publications": len(native),
        "matched_canonical_port_value_prefix": len(pairs),
        "source_equal_age_pairs_reordered": canonical["reordered_groups"],
        "projection_spc_cycles_per_master_clock": [
            SPC_PER_MASTER.numerator, SPC_PER_MASTER.denominator],
        "first_original_source_spc_age": anchor_age,
        "first_native_cpu_master": anchor_master,
        "native_frames": {
            str(f): {**stats(vals),
                     "per_port": {
                         str(p): stats(v) for p, v in
                         sorted(frame_ports[f].items())}}
            for f, vals in sorted(frame_residuals.items())},
        "qualified_claims": {
            "port_value_prefix_equal_after_only_source_age_ties": True,
            "relative_clock_residual_is_diagnostic_only": True,
            "original_source_age_is_not_65816_bus_clock": True,
            "native_cpu_master_is_not_spc_receive_age": True,
            "cpu_to_spc_queue_apply_or_receiver_parity_proven": False,
            "clock_fix_justified": False,
            "complete_usa_events_admitted": 0,
        },
    }


def report(case_zip: Path) -> dict:
    with zipfile.ZipFile(case_zip) as z:
        original, source_trunc = [], []
        for tag, f in logs(z, ORIGINAL_LOG):
            if tag == "QA01RF037ORIGCPU2":
                original.append(f)
            elif tag == "QA01RF037ORIGCPU2_TRUNCATED":
                source_trunc.append(f)
        native, trunc = [], []
        for tag, f in logs(z, NATIVE_LOG):
            if tag == "QA01RF037NATIVEUP" and f.get("kind") == "rtl-apu-enter":
                native.append(f)
            elif tag == "QA01RF037NATIVEUP_TRUNCATED":
                trunc.append(f)
        out = crosswalk(original, native, trunc, source_trunc)
    out["case_zip_sha256"] = hashlib.sha256(case_zip.read_bytes()).hexdigest()
    out["source_artifact_case"] = case_zip.name
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("case_zip", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    if not args.case_zip.is_file():
        ap.error("missing source-bound case ZIP")
    output = json.dumps(report(args.case_zip), sort_keys=True, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(output, encoding="utf8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
