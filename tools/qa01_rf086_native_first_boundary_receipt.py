#!/usr/bin/env python3
"""Validate actual RF086 non-FastRom post-write rows, without parity admission."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROW = re.compile(
    r"^QA01RF086NATIVE seq=(\d+) scope=(Snd_IncDataPtr_M0X0|"
    r"Snd_IncDataPtr_M1X0|Snd_UploadBlock_8097_M0X0) "
    r"f=(\d+) width=([12]) D=([0-9A-F]{4}) addr=([0-9A-F]{4}) "
    r"old=([0-9A-F]{4}) supplied=([0-9A-F]{4}) "
    r"rawAfter=([0-9A-F]{4}) native_master=(\d+)$"
)
SITES = {
    "Snd_IncDataPtr_M0X0": (2, 0x63),
    "Snd_IncDataPtr_M1X0": (2, 0x63),
    "Snd_UploadBlock_8097_M0X0": (1, 0x69),
}


def audit(raw: bytes) -> dict:
    lines = raw.decode("utf-8", errors="strict").splitlines()
    if any("QA01RF086NATIVE_TRUNCATED" in line for line in lines):
        raise ValueError("RF086 native post-commit stream truncated")
    rows = []
    counts = {name: 0 for name in SITES}
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
            (width, (addr - d) & 0xFFFF) != SITES[scope] or
            (width == 1 and max(old, supplied, after) > 0xFF)):
            raise ValueError("RF086 sequence, scope, width, address or frame invalid")
        if rows and (frame < rows[-1]["frame"] or
                     (frame == rows[-1]["frame"] and master < rows[-1]["master"])):
            raise ValueError("RF086 native master/frame chronology reversed")
        if first is None and frame == 6058:
            first = {"seq": seq, "scope": scope, "width": width,
                     "old": old, "supplied": supplied, "raw_after": after,
                     "native_master": master}
        mismatches += after != supplied
        counts[scope] += 1
        rows.append({"frame": frame, "master": master})
    if (not rows or len(rows) > 8192 or first is None or
        any(count == 0 for count in counts.values())):
        raise ValueError("RF086 missing actual first-boundary non-FastRom writer coverage")
    return {
        "schema_version": 1,
        "work_id": "UR-CPU-CAUSE-20261026",
        "native_log_sha256": hashlib.sha256(raw).hexdigest(),
        "native_postcommit_rows": len(rows),
        "native_nonfast_site_counts": counts,
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
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("QA01_RF086_NATIVE_POSTCOMMIT=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
