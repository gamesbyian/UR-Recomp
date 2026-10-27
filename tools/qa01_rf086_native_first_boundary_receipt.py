#!/usr/bin/env python3
"""Audit actual RF086 native WRAM post-commit rows, without parity admission.

The logged g_last_recomp_func label can be stale across interpreter fallback.
It is an advisory context label, never proof of a generated function callsite.
The authoritative discriminator is the actual committed byte/word, address,
host frame and native master-clock value on the common WRAM write path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROW = re.compile(
    r"^QA01RF086NATIVE seq=(\d+) scope=([A-Za-z0-9_?@$(). -]{1,128}) "
    r"f=(\d+) width=([12]) D=([0-9A-F]{4}) addr=([0-9A-F]{4}) "
    r"old=([0-9A-F]{4}) supplied=([0-9A-F]{4}) "
    r"rawAfter=([0-9A-F]{4}) native_master=(\d+)$"
)
# addr is the already resolved CPU bus address from cpu_write8/16, not
# the pre-index direct-page operand. D is retained as register context only;
# subtracting it here incorrectly rejects a real bank-00 WRAM commit when D!=0.
# Historical precommit bus labels, retained for receipt fixtures/context only.
# They are not independently established generated-code function identities.
SITES = {
    "Snd_IncDataPtr_M0X0": (2, 0x63),
    "Snd_IncDataPtr_M1X0": (2, 0x63),
    "Snd_UploadBlock_8097_M0X0": (1, 0x69),
}
WIDTH_ADDR = {1: 0x69, 2: 0x63}


def audit(raw: bytes) -> dict:
    lines = raw.decode("utf-8", errors="strict").splitlines()
    if any("QA01RF086NATIVE_TRUNCATED" in line for line in lines):
        raise ValueError("RF086 native post-commit stream truncated")
    rows = []
    counts = {1: 0, 2: 0}
    boundary_counts = {1: 0, 2: 0}  # Native host frame 6058 only.
    labels = {}
    first = None
    mismatches = 0
    for line in lines:
        if not line.startswith("QA01RF086NATIVE"):
            continue
        match = ROW.fullmatch(line)
        if not match:
            raise ValueError("malformed RF086 native post-commit observation")
        seq, scope, frame, width, d, addr, old, supplied, after, master = match.groups()
        seq, frame, width, master = int(seq), int(frame), int(width), int(master)
        d, addr, old, supplied, after = (
            int(x, 16) for x in (d, addr, old, supplied, after))
        if (seq != len(rows) + 1 or not 6056 <= frame <= 6060 or
            addr != WIDTH_ADDR[width] or
            (width == 1 and max(old, supplied, after) > 0xFF)):
            raise ValueError("RF086 sequence, width, effective address or frame invalid")
        if rows and (frame < rows[-1]["frame"] or
                     (frame == rows[-1]["frame"] and master < rows[-1]["master"])):
            raise ValueError("RF086 native master/frame chronology reversed")
        if frame == 6058:
            boundary_counts[width] += 1
            if first is None:
                first = {"seq": seq, "scope_label_advisory": scope, "width": width,
                         "old": old, "supplied": supplied, "raw_after": after,
                         "native_master": master}
        mismatches += after != supplied
        counts[width] += 1
        labels[scope] = labels.get(scope, 0) + 1
        rows.append({"frame": frame, "master": master})
    if (not rows or len(rows) > 8192 or first is None or
            not all(boundary_counts.values())):
        raise ValueError("RF086 missing actual first-boundary pointer/counter commits")
    return {
        "schema_version": 2,
        "work_id": "UR-CPU-CAUSE-20261026",
        "native_log_sha256": hashlib.sha256(raw).hexdigest(),
        "native_postcommit_rows": len(rows),
        "native_pointer16_commits": counts[2],
        "native_counter8_commits": counts[1],
        "native_first_boundary_pointer16_commits": boundary_counts[2],
        "native_first_boundary_counter8_commits": boundary_counts[1],
        "native_scope_labels_advisory": labels,
        "source_function_attribution_proven": False,
        "native_first_boundary_postcommit": first,
        "raw_after_mismatch_count": mismatches,
        "native_raw_postwrite_observed": True,
        "original_native_clock_registration_proven": False,
        "original_native_semantic_parity_proven": False,
        "observer_off_control_proven": False,
        "release_credit": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-log", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if not args.native_log.is_file() or args.native_log.is_symlink():
        parser.error("actual native replay log absent or symlinked")
    report = audit(args.native_log.read_bytes())
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    print("QA01_RF086_NATIVE_POSTCOMMIT=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
