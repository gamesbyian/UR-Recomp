#!/usr/bin/env python3
"""Extract generated AOT bodies for the stock stunt QUALIFY threshold routine."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

NAME = "TourStuntQualificationThreshold"


def extract_function(text: str, start: int) -> str:
    brace = text.find("{", start)
    if brace < 0:
        raise ValueError("function opening brace missing")
    depth = 0
    for i in range(brace, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise ValueError("function closing brace missing")


def analyze(root: Path) -> dict:
    bodies = []
    pattern = re.compile(
        rf"RecompReturn\s+({NAME}_[A-Za-z0-9_]+)\s*\(CpuState \*cpu\)"
    )
    for path in sorted(root.rglob("*.c")):
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            body = extract_function(text, match.start())
            interesting = [
                line.strip()
                for line in body.splitlines()
                if (
                    "0x069c" in line.lower()
                    or "0xa218" in line.lower()
                    or "cpu_read16" in line
                    or "0x83" in line.lower() and "a218" in line.lower()
                )
            ]
            bodies.append({
                "file": str(path.relative_to(root)),
                "function": match.group(1),
                "body": body,
                "interesting_lines": interesting,
                "mentions_medal_offset": "0x069c" in body.lower(),
                "mentions_threshold_table": "0xa218" in body.lower(),
            })
    if not bodies:
        raise ValueError(f"no generated {NAME} variant found")
    return {
        "schema_version": 1,
        "purpose": "Observe exact generated-C shape of stock stunt qualification threshold routine before adding a hook.",
        "variants": bodies,
        "all_variants_reference_medal_offset": all(
            b["mentions_medal_offset"] for b in bodies),
        "all_variants_reference_threshold_table": all(
            b["mentions_threshold_table"] for b in bodies),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("generated", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    report = analyze(args.generated)
    payload = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
