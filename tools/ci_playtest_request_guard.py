#!/usr/bin/env python3
"""Fail closed before an intentional marker-triggered 27-minute Windows build.

The expensive native Windows playtest is triggered by one exact-path push on
main. This script rejects an accidental edit, a changed source in the same
merge, or a request that did not advance the explicit sequence by one.
It does not handle workflow_dispatch or create any release artifacts.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "docs/playtest/REQUEST-WINDOWS-PLAYTEST.md"
SEQUENCE = re.compile(r"(?m)^- Request sequence: \*\*(0|[1-9][0-9]*)\*\*")
REASON = re.compile(r"(?m)^- Requested reason: ([^\n]+)$")
MAX_SEQUENCE = 2**31 - 1


def field(pattern: re.Pattern[str], text: str, name: str) -> str:
    values = pattern.findall(text)
    if len(values) != 1:
        raise ValueError("missing or repeated " + name)
    return values[0].strip()


def validate(previous: str, current: str, changed: list[str]) -> dict:
    """Accept exactly one source-unchanged, incremented, intentional request."""
    if changed != [MARKER]:
        raise ValueError("request merge must change only " + MARKER)
    old = int(field(SEQUENCE, previous, "previous sequence"))
    new = int(field(SEQUENCE, current, "current sequence"))
    if old >= MAX_SEQUENCE or new != old + 1:
        raise ValueError("request sequence must advance by exactly one")
    old_reason = field(REASON, previous, "previous reason")
    new_reason = field(REASON, current, "new reason")
    if (len(new_reason) < 24 or new_reason == old_reason
            or new_reason.casefold().startswith("initial dispatch")):
        raise ValueError("request requires a fresh concrete reason")
    return {"old": old, "new": new, "changed_paths": changed,
            "release_gate_credit": 0}


def changed_files(commit: str) -> list[str]:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("missing exact 40-hex source commit")
    data = subprocess.check_output(
        ["git", "diff", "--name-only", "--no-renames", "-z",
         commit + "^", commit],
        cwd=ROOT, timeout=15,
    )
    return sorted(x.decode("utf-8") for x in data.split(b"\x00") if x)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    if (not args.previous.is_file() or args.previous.is_symlink()
            or not args.current.is_file() or args.current.is_symlink()):
        raise ValueError("missing or redirected request marker")
    verdict = validate(
        args.previous.read_text(encoding="utf-8"),
        args.current.read_text(encoding="utf-8"),
        changed_files(args.source_sha),
    )
    print("PASS: explicit main-only playtest request " +
          str(verdict["old"]) + " -> " + str(verdict["new"]) +
          ", only marker changed, zero release gate credit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
