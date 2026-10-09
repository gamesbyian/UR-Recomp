#!/usr/bin/env python3
"""Admit real 4x Original fallback frames without guest or raster divergence."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

LOG = re.compile(
    r"UR_BALDOSA_ORIGINAL_FALLBACK frame=(\d+) logical=(\d+)x(\d+) "
    r"raster=(\d+)x(\d+) pitch=(\d+) top_changed=(\d+) "
    r"bottom_changed=(\d+) saved=(\d+)"
)
NAME = re.compile(r"ur-baldosa-fallback-(\d{6})\.pam")
HEADER = (b"P7\nWIDTH 1024\nHEIGHT 896\nDEPTH 4\nMAXVAL 255\n"
          b"TUPLTYPE RGB_ALPHA\nENDHDR\n")


def assess(base: Path, candidate: Path, log: Path, captures: Path) -> dict:
    stock = base.read_bytes().splitlines()
    own = candidate.read_bytes().splitlines()
    records = [tuple(map(int, match.groups())) for match
               in LOG.finditer(log.read_text(encoding="utf-8", errors="replace"))]
    accepted = {
        row[0] for row in records
        if row[1:5] == (256, 224, 1024, 896) and
        row[5] >= 4096 and row[6] == 0 and row[7] == 0 and row[8] == 1
    }
    frames = []
    for file in sorted(captures.glob("ur-baldosa-fallback-*.pam")):
        match = NAME.fullmatch(file.name)
        if match is None:
            raise ValueError(f"Invalid fallback frame filename: {file.name}")
        content = file.read_bytes()
        if not content.startswith(HEADER) or len(content) != len(HEADER) + 1024 * 896 * 4:
            raise ValueError(f"Invalid physical 4x Original raster: {file}")
        pixels = content[len(HEADER):]
        # Reject black/missing capture and detect genuinely distinct stages.
        detail = len(set(pixels[::64])) > 1
        frames.append({
            "frame": int(match.group(1)), "file": file.name,
            "sha256": hashlib.sha256(pixels).hexdigest(),
            "spatially_detailed": detail,
        })
    matching = [f for f in frames if f["frame"] in accepted and f["spatially_detailed"]]
    passed = (own == stock and len(stock) == 2473 and len(matching) >= 2 and
              len({f["sha256"] for f in matching}) >= 2)
    return {
        "schema_version": 1, "status": "passed" if passed else "unproven",
        "guest_frames": len(own), "guest_crc_sequence_unchanged": own == stock,
        "original_fallback_log_records": len(records),
        "matching_real_4x_fallback_frames": len(matching),
        "logical_source": [256, 224], "physical_raster": [1024, 896],
        "first_party_density_fallback": True,
        "captures": frames,
        "widescreen_or_4k_proven": False,
        "completed_usa_course_credit": 0,
        "limits": "Host-controlled Original nearest 4x fallback for fixed geometry; not 16:9, output 4K, or full native course acceptance.",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    for name in ("base", "candidate", "log", "captures", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    result = assess(a.base, a.candidate, a.log, a.captures)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
