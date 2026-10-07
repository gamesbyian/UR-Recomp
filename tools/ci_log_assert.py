#!/usr/bin/env python3
"""Assert structured key/value fields on one diagnostic event line.

CI diagnostics are append-only interfaces: producers may add or reorder fields.
This helper deliberately matches an event independently of field ordering and
prints useful context when the contract is not satisfied.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def event_lines(text: str, event: str) -> list[str]:
    needle = f" {event} "
    return [
        line
        for line in text.splitlines()
        if needle in f" {line.strip()} "
    ]


def line_has_fields(line: str, fields: list[str]) -> bool:
    tokens = set(line.split())
    return all(field in tokens for field in fields)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--event", required=True)
    parser.add_argument("--field", action="append", default=[])
    parser.add_argument("--absent", action="store_true")
    args = parser.parse_args()

    text = args.path.read_text(encoding="utf-8", errors="replace")
    matches = event_lines(text, args.event)

    if args.absent:
        if matches:
            print(f"unexpected event {args.event!r} in {args.path}", file=sys.stderr)
            for line in matches[-10:]:
                print(f"  {line}", file=sys.stderr)
            return 1
        return 0

    if not matches:
        print(f"missing event {args.event!r} in {args.path}", file=sys.stderr)
    elif any(line_has_fields(line, args.field) for line in matches):
        return 0
    else:
        print(
            f"event {args.event!r} found but no line contained all fields "
            f"{args.field!r} in {args.path}",
            file=sys.stderr,
        )
        for line in matches[-10:]:
            print(f"  {line}", file=sys.stderr)

    tail = text.splitlines()[-40:]
    if tail:
        print("log tail:", file=sys.stderr)
        for line in tail:
            print(f"  {line}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
