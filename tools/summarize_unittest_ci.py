#!/usr/bin/env python3
"""Compact, non-authoritative CI unittest result; raw logs remain diagnostics.

Designed for an always-running reporting step, not a replacement for the
failing test step. Missing logs/exit receipts are INCOMPLETE, never success.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re

RAN = re.compile(r"(?m)^Ran (\d+) tests? in ([0-9.]+)s$")
ISSUE = re.compile(r"(?m)^(?:FAIL|ERROR): (.+)$")


def summarize(root: Path, metadata: dict[str, str]) -> dict:
    exits = {}
    receipt = root / "unit-shard-exits.txt"
    if receipt.is_file():
        for line in receipt.read_text(encoding="utf-8").splitlines():
            if re.fullmatch(r"shard[0-9]+=[0-9]+", line):
                key, value = line.split("=", 1)
                exits[key] = int(value)
    shards = []
    found = set(exits) | {m.group(1) for f in root.glob("unit-shard*.log")
                          if (m := re.fullmatch(r"unit-(shard[0-9]+)\.log", f.name))}
    # Always expect at least the historical two shards so a missing log is
    # reported as not_run rather than silently omitted.
    names = sorted(found | {"shard0", "shard1"}, key=lambda n: int(n[5:]))
    for name in names:
        path = root / f"unit-{name}.log"
        if not path.is_file():
            shards.append({"id": name, "outcome": "not_run", "tests": None,
                           "exit_code": exits.get(name), "issues": []})
            continue
        raw = path.read_bytes()
        log = raw.decode("utf-8", errors="replace")
        runs = RAN.findall(log)
        tests = int(runs[-1][0]) if runs else None
        seconds = float(runs[-1][1]) if runs else None
        code = exits.get(name)
        outcome = ("incomplete" if code is None else
                   "pass" if code == 0 and tests is not None and re.search(r"(?m)^OK(?: |$)", log) else
                   "fail" if code != 0 and tests is not None else
                   "harness_error")
        shards.append({"id": name, "outcome": outcome, "tests": tests,
                       "seconds": seconds, "exit_code": code,
                       "log_sha256": hashlib.sha256(raw).hexdigest(),
                       "issues": ISSUE.findall(log)[:8]})
    outcomes = {x["outcome"] for x in shards}
    overall = ("incomplete" if "not_run" in outcomes or "incomplete" in outcomes else
               "harness_error" if "harness_error" in outcomes else
               "fail" if "fail" in outcomes else "pass")
    return {"schema": "UR-CI-UNIT-RESULT/1", "authority": "diagnostic-only",
            "outcome": overall, "source": metadata,
            "total_tests_observed": sum(x["tests"] or 0 for x in shards),
            "shards": shards, "missing_evidence": [x["id"] for x in shards
                                                   if x["outcome"] in ("not_run", "incomplete", "harness_error")]}


def markdown(report: dict) -> str:
    rows = ["### Project tooling unit tests",
            f"**Outcome:** {report['outcome']} | **Tests observed:** {report['total_tests_observed']}",
            "", "| Shard | Outcome | Tests | Elapsed | Issues |",
            "|---|---|---:|---:|---|"]
    for entry in report["shards"]:
        issues = "; ".join(entry["issues"][:3]).replace("|", r"\|")
        rows.append(f"| {entry['id']} | {entry['outcome']} | {entry['tests'] if entry['tests'] is not None else 'unknown'} | "
                    f"{entry.get('seconds') if entry.get('seconds') is not None else 'unknown'}s | {issues or 'none reported'} |")
    rows.extend(["", "Compact run receipt: ci-tooling-unit-result.json. "
                 "Raw failing-shard logs are separate diagnostics, and no gameplay or release acceptance is claimed.", ""])
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    meta = {key: os.environ.get(key, "") for key in
            ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_SHA", "GITHUB_WORKFLOW",
             "GITHUB_EVENT_NAME", "GITHUB_HEAD_REF")}
    meta["pr_head_sha"] = os.environ.get("SOURCE_HEAD_SHA", "")
    result = summarize(args.root, meta)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = markdown(result)
    if args.summary:
        with args.summary.open("a", encoding="utf-8") as stream:
            stream.write(report)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
