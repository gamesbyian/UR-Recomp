#!/usr/bin/env python3
"""QA-01: compare retained full original/native Zoo guest memory across nearby frames.

Fits are observational byte-distance measurements, NOT equivalent CPU cycles,
guest instruction/NMI synchronization, original event credit or a correction
for the native renderer / control phase.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

FIELDS = {"wram": 0x20000, "vram": 0x10000, "cgram": 512}
ARCHIVE_NAMES = {
    "original": "original-boundary",
    "native": "native-boundary/dump",
}
FIRST, LAST, SHIFT = 5155, 5175, 2


def read_guest(z: ZipFile, original: bool, frame: int) -> dict[str, bytes] | None:
    prefix = ARCHIVE_NAMES["original" if original else "native"]
    values = {}
    for name, size in FIELDS.items():
        path = f"{prefix}/boundary-{frame:05d}.{name}.bin"
        try:
            data = z.read(path)
        except KeyError:
            return None
        if len(data) != size:
            raise ValueError(f"{path}: expected {size} bytes, got {len(data)}")
        values[name] = data
    return values


def differences(a: dict[str, bytes], b: dict[str, bytes]) -> dict[str, int]:
    if set(a) != set(FIELDS) or set(b) != set(FIELDS):
        raise ValueError("missing one or more full original/native memory classes")
    for k, size in FIELDS.items():
        if len(a[k]) != size or len(b[k]) != size:
            raise ValueError(f"{k}: wrong bulk guest-memory capture size")
    return {name: sum(x != y for x, y in zip(a[name], b[name]))
            for name in FIELDS}


def compare(z: ZipFile, first: int = FIRST, last: int = LAST,
            shift: int = SHIFT) -> dict:
    if not (5155 <= first <= last <= 5175 and 0 <= shift <= 3):
        raise ValueError("only original source-calibrated +5155..+5175 guest window")
    rows = []
    for native_frame in range(first, last + 1):
        native = read_guest(z, False, native_frame)
        if native is None:
            raise ValueError(f"native missing exact guest +{native_frame} dump")
        candidates = []
        for offset in range(-shift, shift + 1):
            original_frame = native_frame + offset
            original = read_guest(z, True, original_frame)
            if original is None:
                continue
            counts = differences(native, original)
            candidates.append({
                "original_relative_frame": original_frame,
                "offset_original_minus_native": offset,
                "bytes_different": counts,
                "total_different_bytes": sum(counts.values()),
            })
        if not candidates:
            raise ValueError(f"no comparable original frames for native +{native_frame}")
        candidates.sort(key=lambda c: (
            c["total_different_bytes"],
            abs(c["offset_original_minus_native"]),
            c["offset_original_minus_native"],
        ))
        rows.append({
            "native_relative_frame": native_frame,
            "nearest_original_candidate": candidates[0],
            "same_relative_frame": next(
                (q for q in candidates if q["offset_original_minus_native"] == 0),
                None),
            "other_candidates": candidates[1:],
        })
    return {
        "schema": "UR-QA01-ZOO-BULK-FRAME-DISTANCE/1",
        "scope": "read-only raw WRAM/VRAM/CGRAM from original + native source-calibrated guest scripts",
        "native_window_inclusive": [first, last],
        "max_candidate_source_frame_offset": shift,
        "memory_class_sizes": dict(FIELDS),
        "rows": rows,
        "admission": {
            "release_usa_complete_courses_credited": 0,
            "causal_claim": "none",
            "warning": ("A best byte-distance fit is not a guest PC, instruction, "
                        "NMI/VBlank or host sampling proof. VRAM/CGRAM may remain "
                        "unchanged across multiple frames, and postresult "
                        "field cleanup may produce apparent extra offsets. "
                        "Do not globally shift controller inputs or patch timing."),
        },
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--first", type=int, default=FIRST)
    p.add_argument("--last", type=int, default=LAST)
    p.add_argument("--max-shift", type=int, default=SHIFT)
    args = p.parse_args()
    blob = args.artifact.read_bytes()
    with ZipFile(args.artifact) as z:
        report = compare(z, args.first, args.last, args.max_shift)
    report["artifact_zip_sha256"] = hashlib.sha256(blob).hexdigest()
    report["source_ci_run"] = 38018081196
    report["source_artifact_id"] = 11656564258
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "samples": len(report["rows"]),
        "exact_adjacent_guest_equal": [
            row["native_relative_frame"] for row in report["rows"]
            if row["nearest_original_candidate"]["total_different_bytes"] == 0
            and row["nearest_original_candidate"]["offset_original_minus_native"] != 0
        ],
        "release_usa_complete_courses_credited": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
