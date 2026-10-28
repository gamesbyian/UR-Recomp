#!/usr/bin/env python3
"""Fail closed before an intentional marker-triggered heavy Windows/QA campaign.

An exact-path PR-merge push to main may trigger the Windows technical playtest
or the bounded Zoo original/native CPU-cause experiment. Reject accidental
edits, extra source changes, and non-incremented request sequences before any
heavy runner executes. No release publication or QA admission happens here.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "docs/playtest/REQUEST-WINDOWS-PLAYTEST.md"
ZOO_MARKER = "docs/qa01/REQUEST-ZOO-CAUSAL.md"
SUPPORTED_MARKERS = frozenset({MARKER, ZOO_MARKER})
SEQUENCE = re.compile(r"(?m)^- Request sequence: \*\*(0|[1-9][0-9]*)\*\*")
REASON = re.compile(r"(?m)^- Requested reason: ([^\n]+)$")
MAX_SEQUENCE = 2**31 - 1
ZOO_OBSERVER_MODE = re.compile(r"(?m)^- Observer mode: \*\*(on|off)\*\*$")
ZOO_OBSERVER_FIELDS = re.compile(r"(?m)^- Observer mode:")
# Legacy marker requests through sequence 19 cannot silently enable RF094.
ZOO_RF094_MODE = re.compile(r"(?m)^- RF094 DSP follow-through: \*\*(on|off)\*\*$")
ZOO_RF094_FIELDS = re.compile(r"(?m)^- RF094 DSP follow-through:")


def field(pattern: re.Pattern[str], text: str, name: str) -> str:
    values = pattern.findall(text)
    if len(values) != 1:
        raise ValueError("missing or repeated " + name)
    return values[0].strip()


def validate(previous: str, current: str, changed: list[str], *, marker: str = MARKER) -> dict:
    """Accept exactly one source-unchanged, incremented, intentional request."""
    if marker not in SUPPORTED_MARKERS or changed != [marker]:
        raise ValueError("request merge must change only a supported request marker")
    old = int(field(SEQUENCE, previous, "previous sequence"))
    new = int(field(SEQUENCE, current, "current sequence"))
    if old >= MAX_SEQUENCE or new != old + 1:
        raise ValueError("request sequence must advance by exactly one")
    old_reason = field(REASON, previous, "previous reason")
    new_reason = field(REASON, current, "new reason")
    if (len(new_reason) < 24 or new_reason == old_reason
            or new_reason.casefold().startswith("initial dispatch")):
        raise ValueError("request requires a fresh concrete reason")
    # A new Zoo request must explicitly choose its instrumentation state.
    # Older markers predate this field; only the new request is authoritative.
    observer_enabled = None
    rf094_enabled = None
    if marker == ZOO_MARKER:
        modes = ZOO_OBSERVER_MODE.findall(current)
        if len(modes) != 1 or len(ZOO_OBSERVER_FIELDS.findall(current)) != 1:
            raise ValueError("Zoo request requires exactly one explicit observer mode")
        observer_enabled = modes[0] == "on"
        # Legacy requests through sequence 19 predate the DSP observer.
        # From sequence 20, require one valid, intentional RF094 mode.
        rf094_fields = ZOO_RF094_FIELDS.findall(current)
        rf094_modes = ZOO_RF094_MODE.findall(current)
        if new >= 20 or rf094_fields:
            if len(rf094_fields) != 1 or len(rf094_modes) != 1:
                raise ValueError("Zoo RF094 request requires one explicit on/off selector")
            rf094_enabled = rf094_modes[0] == "on"
        else:
            rf094_enabled = False
        if rf094_enabled and not observer_enabled:
            raise ValueError("Zoo RF094 requires paired original/native observer on")
    return {"old": old, "new": new, "changed_paths": changed,
            "observer_enabled": observer_enabled,
            "rf094_enabled": rf094_enabled, "release_gate_credit": 0}


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
    parser.add_argument("--marker", choices=sorted(SUPPORTED_MARKERS), default=MARKER)
    parser.add_argument("--gha-output", type=Path, help="write validated Zoo observer and RF094 choices to GitHub job outputs")
    args = parser.parse_args()
    if (not args.previous.is_file() or args.previous.is_symlink()
            or not args.current.is_file() or args.current.is_symlink()):
        raise ValueError("missing or redirected request marker")
    verdict = validate(
        args.previous.read_text(encoding="utf-8"),
        args.current.read_text(encoding="utf-8"),
        changed_files(args.source_sha), marker=args.marker,
    )
    if args.gha_output is not None:
        if args.marker != ZOO_MARKER:
            raise ValueError("observer mode output is only supported for Zoo requests")
        with args.gha_output.open("a", encoding="utf-8") as out:
            out.write("observer_enabled=" +
                      ("true" if verdict["observer_enabled"] else "false") + "\n")
            out.write("rf094_enabled=" +
                      ("true" if verdict["rf094_enabled"] else "false") + "\n")
    print("PASS: explicit main-only source-isolated request " +
          str(verdict["old"]) + " -> " + str(verdict["new"]) +
          ", only marker changed, zero release gate credit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
