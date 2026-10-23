#!/usr/bin/env python3
"""Print a Vault intake report, and optionally review-gated staged text, to a log.

For agents that can read GitHub Actions job logs through a connector but cannot
download artifacts or reach Google Drive. Read-only. Every content line is
prefixed with ``| `` so staged text can never form a runner workflow command
(``::...``); reconstruct a file by stripping that prefix. Only UTF-8 text that
the intake tool already staged (reviewed, non-sensitive source extensions, not
byte-identical to main) is relayed, within a hard byte budget.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

MAX_RELAY_BYTES = 1_500_000
PREFIX = "| "


def triage_lines(report: dict) -> list[str]:
    lines = [f"UR-TRIAGE listed={report.get('listed_files')} "
             f"downloads={len(report.get('downloads', []))} "
             f"errors={len(report.get('errors', []))}"]
    for error in report.get("errors", []):
        lines.append(f"UR-TRIAGE-ERROR id={error.get('id')} {error.get('error')}")
    for item in report.get("downloads", []):
        zip_info = item.get("zip")
        lines.append(f"UR-TRIAGE-FILE id={item['id']} bytes={item['bytes']} "
                     f"sha256={item['sha256']} path={item['path']}")
        if not zip_info:
            continue
        cross = zip_info.get("crosswalk", {})
        lines.append("UR-TRIAGE-ZIP " + " ".join(
            f"{key}={cross.get(key)}" for key in sorted(cross)))
        for member in zip_info.get("members", []):
            lines.append(
                "UR-TRIAGE-MEMBER bytes=%d sha256=%s source=%d main=%d staged=%d %s" % (
                    member["bytes"], member["sha256"][:16],
                    int(member["source_like"]), int(member["exact_on_main"]),
                    int(member["staged"]), member["member"]))
    return lines


def relay_staged(staged: Path, budget: int = MAX_RELAY_BYTES) -> list[str]:
    lines, used = [], 0
    for path in sorted(p for p in staged.rglob("*") if p.is_file() and not p.is_symlink()):
        data = path.read_bytes()
        rel = path.relative_to(staged).as_posix()
        digest = hashlib.sha256(data).hexdigest()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            lines.append(f"UR-STAGED-SKIP not-utf8 bytes={len(data)} sha256={digest} {rel}")
            continue
        if used + len(data) > budget:
            lines.append(f"UR-STAGED-SKIP over-budget bytes={len(data)} sha256={digest} {rel}")
            continue
        used += len(data)
        lines.append(f"UR-STAGED-BEGIN bytes={len(data)} sha256={digest} {rel}")
        lines.extend(PREFIX + row for row in text.split("\n"))
        lines.append("UR-STAGED-END")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--staged", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    out = triage_lines(report)
    if args.staged is not None and args.staged.is_dir():
        out.extend(relay_staged(args.staged))
    sys.stdout.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
