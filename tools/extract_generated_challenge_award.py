#!/usr/bin/env python3
"""Extract generated AOT bodies for the stock tour result/award routine."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

NAME = "TourResultQualificationAndAward"


def extract_function(text: str, start: int) -> str:
    brace = text.find("{", start)
    if brace < 0:
        raise ValueError("function opening brace missing")
    depth = 0
    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise ValueError("function closing brace missing")


def analyze(root: Path) -> dict:
    pattern = re.compile(
        rf"RecompReturn\s+({NAME}_[A-Za-z0-9_]+)\s*\(CpuState \*cpu\)"
    )
    variants = []
    for path in sorted(root.rglob("*.c")):
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            body = extract_function(text, match.start())
            lines = [
                line.strip()
                for line in body.splitlines()
                if (
                    "0x069c" in line.lower()
                    or "0x1075" in line.lower()
                    or "0x88fd" in line.lower()
                    or "cpu_read" in line and "0x77" in line
                    or "cpu_write" in line and "0x77" in line
                )
            ]
            variants.append({
                "file": str(path.relative_to(root)),
                "function": match.group(1),
                "body": body,
                "interesting_lines": lines,
                "mentions_medal_cell": "0x069c" in body.lower(),
            })
    if not variants:
        raise ValueError(f"no generated {NAME} variant found")
    return {
        "schema_version": 1,
        "purpose": "Observe generated-C shape of stock qualification/award routine before adding the previous-medal hook.",
        "variants": variants,
        "all_variants_reference_medal_cell": all(
            v["mentions_medal_cell"] for v in variants),
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
