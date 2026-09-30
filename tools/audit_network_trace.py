#!/usr/bin/env python3
"""Reduce strace network logs into a machine-readable outbound-network report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

NETWORK_CALL = re.compile(r"\b(connect|sendto|sendmsg|sendmmsg)\(")
INET = re.compile(r"AF_INET6?\b")


def scan(paths: list[Path]) -> dict:
    attempts: list[dict[str, object]] = []
    files = 0
    lines = 0
    for path in sorted(paths):
        if not path.is_file():
            continue
        files += 1
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            lines += 1
            if NETWORK_CALL.search(line) and INET.search(line):
                attempts.append({"file": str(path), "line": lineno, "text": line.strip()})
    return {
        "schema_version": 1,
        "trace_files": files,
        "trace_lines": lines,
        "inet_attempt_count": len(attempts),
        "inet_attempts": attempts,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--json-out", type=Path)
    p.add_argument("--require-none", action="store_true")
    args = p.parse_args()

    expanded: list[Path] = []
    for item in args.paths:
        if any(ch in str(item) for ch in "*?["):
            expanded.extend(sorted(item.parent.glob(item.name)))
        else:
            expanded.append(item)

    report = scan(expanded)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json_out:
        args.json_out.write_text(text + "\n", encoding="utf-8")
    if args.require_none and report["inet_attempt_count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
