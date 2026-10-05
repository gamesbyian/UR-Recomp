#!/usr/bin/env python3
"""Extract the stock ordinary-tour stunt QUALIFY table at ROM 83:A218."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

BANK = 0x83
ADDR = 0xA218
ORDINARY_TOURS = (
    "Crawler", "Jumper", "Shuffler", "Bounder",
    "Walker", "Runner", "Hopper", "Sprinter",
)
GENERATIONS = ("bronze", "silver", "gold")


def lorom(bank: int, addr: int) -> int:
    return (bank & 0x7F) * 0x8000 + (addr & 0x7FFF)


def extract(rom: bytes) -> dict:
    start = lorom(BANK, ADDR)
    count = len(ORDINARY_TOURS) * len(GENERATIONS)
    raw = rom[start:start + 2 * count]
    if len(raw) != 2 * count:
        raise ValueError("ROM too short for stunt QUALIFY table")

    words = [
        int.from_bytes(raw[i:i + 2], "little")
        for i in range(0, len(raw), 2)
    ]
    tours = []
    for row, name in enumerate(ORDINARY_TOURS):
        base = row * 3
        tours.append({
            "tour_row": row,
            "tour": name,
            "thresholds": {
                GENERATIONS[g]: words[base + g]
                for g in range(3)
            },
        })

    return {
        "schema_version": 1,
        "source": "83:A218",
        "index": "3 * tour_row + challenge_generation",
        "generation_values": {
            "0": "bronze",
            "1": "silver",
            "2": "gold",
        },
        "ordinary_tours": tours,
        "raw_words": words,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    report = extract(args.rom.read_bytes())
    payload = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
