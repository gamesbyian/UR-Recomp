#!/usr/bin/env python3
"""Validate RF087 actual native snapshot-cut markers; no clock parity claim."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROW = re.compile(
    r"^QA01RF087NATIVECUT f=(\d+) rc=(-?\d+) "
    r"master_before=(\d+) master_after=(\d+) "
    r"ptr_before=([0-9A-F]{4}) ptr_after=([0-9A-F]{4}) "
    r"counter_before=([0-9A-F]{2}) counter_after=([0-9A-F]{2})$"
)


def audit(raw: bytes) -> dict:
    lines = raw.decode("utf-8", errors="strict").splitlines()
    rows = []
    for line in lines:
        if not line.startswith("QA01RF087NATIVECUT"):
            continue
        match = ROW.fullmatch(line)
        if not match:
            raise ValueError("malformed native snapshot-cut marker")
        f, rc, mb, ma, pb, pa, cb, ca = match.groups()
        f, rc, mb, ma = int(f), int(rc), int(mb), int(ma)
        pb, pa, cb, ca = (int(v, 16) for v in (pb, pa, cb, ca))
        if (not 6056 <= f <= 6060 or rc != 0 or mb != ma or
                pb != pa or cb != ca or (rows and f < rows[-1]["frame"])):
            raise ValueError("native snapshot failed or changed clock/WRAM at cut")
        rows.append({"frame": f, "native_master_at_cut": mb,
                     "pointer16_at_cut": pb, "counter8_at_cut": cb})
    if len(rows) > 32 or not {6058, 6059}.issubset({r["frame"] for r in rows}):
        raise ValueError("missing native 6058/6059 actual snapshot-cut markers")
    return {
        "schema_version": 1,
        "work_id": "UR-CPU-CAUSE-20261026",
        "native_log_sha256": hashlib.sha256(raw).hexdigest(),
        "native_cut_rows": rows,
        "cut_does_not_advance_native_master_or_wram": True,
        "original_native_clock_registration_proven": False,
        "observer_off_control_proven": False,
        "release_credit": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-log", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if not args.native_log.is_file() or args.native_log.is_symlink():
        parser.error("actual native log missing or symlinked")
    args.out.write_text(json.dumps(audit(args.native_log.read_bytes()),
                                   sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("QA01_RF087_NATIVE_SNAPSHOT_CUT=" + args.out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
