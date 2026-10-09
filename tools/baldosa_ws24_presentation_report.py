#!/usr/bin/env python3
"""Conservative visual/guest gate for disposable native +24 split world raster."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

PRESENT = re.compile(
    r"UR_BALDOSA_WS24_PRESENT frame=(\d+) width=(\d+) height=(\d+) "
    r"pitch=(\d+) calibrated=(\d+) saved=(\d+)"
)
PREP = re.compile(
    r"UR_BALDOSA_WS24_PREP frame=(\d+) calibrated=(\d+) "
    r"logical=(\d+)x(\d+) margin=24"
)
NAME = re.compile(r"ur-baldosa-ws24-(\d{6})\.pam")
HEADER = (b"P7\nWIDTH 304\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
          b"TUPLTYPE RGB_ALPHA\nENDHDR\n")
WIDTH, HEIGHT, EXTRA = 304, 224, 24


def edge_differences(raster: bytes) -> dict[str, int]:
    """Require new pixels in each of four split-screen margins.

    This rejects solid black mattes, an ordinary 256-wide image padded at
    its edges, and a single viewport accidentally widening both halves.
    Independent original/frame parity remains a separate release oracle.
    """
    count = {}
    for section, y0, y1 in (("top", 0, 112), ("bottom", 112, 224)):
        for side in ("left", "right"):
            changed = 0
            for y in range(y0, y1):
                row = memoryview(raster)[y * WIDTH * 4:(y + 1) * WIDTH * 4]
                edge = EXTRA if side == "left" else WIDTH - EXTRA - 1
                baseline = row[edge * 4:edge * 4 + 4].tobytes()
                xs = range(EXTRA) if side == "left" else range(WIDTH - EXTRA, WIDTH)
                for x in xs:
                    if row[x * 4:x * 4 + 4].tobytes() != baseline:
                        changed += 1
            count[f"{section}_{side}"] = changed
    return count


def assess(base: Path, candidate: Path, log: Path, captures: Path) -> dict:
    original = base.read_bytes().splitlines()
    candidate_crc = candidate.read_bytes().splitlines()
    text = log.read_text(encoding="utf-8", errors="replace")
    presents = [tuple(map(int, m.groups())) for m in PRESENT.finditer(text)]
    preps = [tuple(map(int, m.groups())) for m in PREP.finditer(text)]
    accepted = {
        x[0] for x in presents
        if x[1:3] == (WIDTH, HEIGHT) and x[3] >= WIDTH * 4 and
        x[4] == 1 and x[5] == 1
    }
    evidence = []
    for file in sorted(captures.glob("ur-baldosa-ws24-*.pam")):
        match = NAME.fullmatch(file.name)
        if match is None:
            raise ValueError(f"Invalid frame name: {file.name}")
        content = file.read_bytes()
        if not content.startswith(HEADER) or len(content) != len(HEADER) + WIDTH * HEIGHT * 4:
            raise ValueError(f"Invalid +24 physical raster: {file}")
        raster = content[len(HEADER):]
        margin = edge_differences(raster)
        frame = int(match.group(1))
        evidence.append({
            "frame": frame, "filename": file.name,
            "sha256": hashlib.sha256(raster).hexdigest(),
            "world_margin_differences": margin,
            "valid_four_margins": all(value > 32 for value in margin.values()),
        })
    witnessed = [v for v in evidence if
                 v["frame"] in accepted and v["valid_four_margins"]]
    passed = (
        original == candidate_crc and len(original) == 2473
        and len(witnessed) >= 2
        and len({e["sha256"] for e in witnessed}) >= 2
        and any(row[1] == 1 and row[2:4] == (WIDTH, HEIGHT) for row in preps)
    )
    return {
        "schema_version": 1, "status": "passed" if passed else "unproven",
        "logical_guest_geometry": [256, 224],
        "host_wide_raster": [WIDTH, HEIGHT],
        "per_side_new_world_pixels": EXTRA,
        "base_frames": len(original), "candidate_frames": len(candidate_crc),
        "identical_guest_crc_sequence": original == candidate_crc,
        "calibrated_presentations": len(accepted),
        "four_margin_image_frames": len(witnessed),
        "captures": evidence,
        "4k_or_hd_wide_claimed": False,
        "completed_usa_course_credit": 0,
        "limits": "Two-player fixed-route +24 at 1x only, subject to stock/original"
                  " image and source tile-by-tile parity; not 16:9 or 4K.",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    for name in ("base", "candidate", "log", "captures", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    evidence = assess(a.base, a.candidate, a.log, a.captures)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return 0 if evidence["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
