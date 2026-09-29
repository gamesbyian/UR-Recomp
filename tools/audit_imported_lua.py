#!/usr/bin/env python3
"""Audit imported Lua table constructors for duplicate named keys.

Lua silently keeps the later value for duplicate keys in a table constructor.
That behavior hid several contradictory RAM labels in the recovered Uniracers
bot, so imported Lua is scanned explicitly before its tables are promoted into
project-owned tooling.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

TOKEN_RE = re.compile(
    r"--[^\n]*|"
    r'"(?:\\.|[^"\\])*"|'
    r"'(?:\\.|[^'\\])*'|"
    r"[A-Za-z_][A-Za-z0-9_]*|"
    r"[{}=]"
)


@dataclass(frozen=True)
class DuplicateKey:
    key: str
    first_line: int
    duplicate_line: int
    table_depth: int


def _tokens(source: str) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for match in TOKEN_RE.finditer(source):
        tok = match.group(0)
        if tok.startswith("--") or tok.startswith('"') or tok.startswith("'"):
            continue
        line = source.count("\n", 0, match.start()) + 1
        out.append((tok, line))
    return out


def find_duplicate_table_keys(source: str) -> list[DuplicateKey]:
    tokens = _tokens(source)
    stack: list[dict[str, int]] = []
    findings: list[DuplicateKey] = []

    i = 0
    while i < len(tokens):
        tok, line = tokens[i]
        if tok == "{":
            stack.append({})
        elif tok == "}":
            if stack:
                stack.pop()
        elif (
            stack
            and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", tok)
            and i + 1 < len(tokens)
            and tokens[i + 1][0] == "="
        ):
            first = stack[-1].get(tok)
            if first is None:
                stack[-1][tok] = line
            else:
                findings.append(DuplicateKey(tok, first, line, len(stack)))
        i += 1
    return findings


def audit_path(path: Path) -> list[DuplicateKey]:
    return find_duplicate_table_keys(path.read_text(encoding="utf-8", errors="replace"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--fail-on-findings", action="store_true")
    args = ap.parse_args()

    report: dict[str, list[dict[str, int | str]]] = {}
    total = 0
    for path in args.paths:
        findings = audit_path(path)
        report[path.as_posix()] = [asdict(x) for x in findings]
        total += len(findings)
        for x in findings:
            print(
                f"{path}:{x.duplicate_line}: duplicate key {x.key!r}; "
                f"first declared at line {x.first_line}"
            )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if total:
        print(f"{total} duplicate Lua table key(s) found")
    else:
        print("no duplicate Lua table keys found")
    return 1 if args.fail_on_findings and total else 0


if __name__ == "__main__":
    raise SystemExit(main())
