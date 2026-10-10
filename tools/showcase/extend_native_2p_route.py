#!/usr/bin/env python3
"""Derive a media-only longer 2P route from the pinned, genuine Baldosa script.

Keep all choices, guest wait gates and button inputs before GO byte-exact.
Normal-speed mode after GO gives the SDL presenter the opportunity to draw
every guest frame. Missing host presentations remain a hard rejection.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

GO = "until 0E1F != 00\ndump go\n"
TAIL = "press right+p2:right 240\ndump t480\nquit"
EXTENSION = "press right+p2:right 240\ndump t480\n" \
            "press right+p2:right 900\ndump t1380\nquit"


def extend(source: str) -> str:
    if source.count("turbo on\n") != 1 or source.count(GO) != 1:
        raise ValueError("Pinned original race/GO gate not found uniquely")
    if source.count(TAIL) != 1 or not source.rstrip().endswith(TAIL):
        raise ValueError("Original route tail changed, refusing mutation")
    if "turbo off" in source:
        raise ValueError("Original route already has speed transition")
    return (source.replace(GO, GO + "turbo off\n", 1)
            .replace(TAIL, EXTENSION, 1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    original = args.source.read_text(encoding="utf-8")
    candidate = extend(original)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(candidate, encoding="utf-8")
    print("UR_MEDIA_ROUTE original_sha256="
          + hashlib.sha256(original.encode()).hexdigest()
          + " extended_sha256="
          + hashlib.sha256(candidate.encode()).hexdigest()
          + " post_go_preserved=1 original_go_gate_preserved=1"
          + " post_go_turbo_off=1 additional_right_frames=900")


if __name__ == "__main__":
    main()
