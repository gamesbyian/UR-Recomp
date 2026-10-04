#!/usr/bin/env python3
"""Compare retained desktop and Switch S2 execution reports."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CHECKPOINT_RE = re.compile(
    r"^checkpoint frame=(?P<frame>\d+) "
    r"master=(?P<master>[0-9a-fA-F]{8}) "
    r"cpu=(?P<cpu>[0-9a-fA-F]{8}) "
    r"wram=(?P<wram>[0-9a-fA-F]{8}) "
    r"apu=(?P<apu>[0-9a-fA-F]{8}) "
    r"ppu=(?P<ppu>[0-9a-fA-F]{8}) "
    r"dma=(?P<dma>[0-9a-fA-F]{8}) "
    r"cart=(?P<cart>[0-9a-fA-F]{8})$"
)
PARTITIONS = ("master", "cpu", "wram", "apu", "ppu", "dma", "cart")
EXPECTED_FRAMES = (0, 1, 60, 120)


def parse_report(path: Path) -> dict:
    checkpoints: dict[int, dict[str, str]] = {}
    flags: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        match = CHECKPOINT_RE.match(line)
        if match:
            frame = int(match.group("frame"))
            if frame in checkpoints:
                raise ValueError(f"{path}: duplicate checkpoint frame {frame}")
            checkpoints[frame] = {p: match.group(p).lower() for p in PARTITIONS}
            continue
        if "=" in line and not line.startswith("checkpoint "):
            key, value = line.split("=", 1)
            flags[key] = value
    missing = [f for f in EXPECTED_FRAMES if f not in checkpoints]
    extra = sorted(set(checkpoints) - set(EXPECTED_FRAMES))
    if missing or extra:
        raise ValueError(f"{path}: checkpoint set mismatch missing={missing} extra={extra}")
    return {"flags": flags, "checkpoints": checkpoints}


def compare(reference: dict, observed: dict) -> dict:
    ref_flags = reference["flags"]
    obs_flags = observed["flags"]
    errors: list[str] = []

    if ref_flags.get("snes_init") != "1":
        errors.append("reference snes_init != 1")
    if obs_flags.get("snes_init") != "1":
        errors.append("observed snes_init != 1")
    if ref_flags.get("execution_complete") != "1":
        errors.append("reference execution_complete != 1")
    if obs_flags.get("execution_complete") != "1":
        errors.append("observed execution_complete != 1")

    first_diff = None
    for frame in EXPECTED_FRAMES:
        ref = reference["checkpoints"][frame]
        obs = observed["checkpoints"][frame]
        for partition in PARTITIONS:
            if ref[partition] != obs[partition]:
                first_diff = {
                    "frame": frame,
                    "partition": partition,
                    "reference": ref[partition],
                    "observed": obs[partition],
                }
                errors.append(
                    f"frame {frame} {partition}: reference={ref[partition]} observed={obs[partition]}"
                )
                break
        if first_diff:
            break

    return {
        "match": not errors,
        "expected_frames": list(EXPECTED_FRAMES),
        "partitions": list(PARTITIONS),
        "first_difference": first_diff,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("observed", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    try:
        result = compare(parse_report(args.reference), parse_report(args.observed))
    except ValueError as exc:
        result = {
            "match": False,
            "expected_frames": list(EXPECTED_FRAMES),
            "partitions": list(PARTITIONS),
            "first_difference": None,
            "errors": [str(exc)],
        }

    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(payload, end="")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload)
    return 0 if result["match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
