#!/usr/bin/env python3
"""Run every assigned unittest module, preserving one global result and timing all modules.

Timing is diagnostics only, never a replacement for a full test, release gate
or acceptance oracle. Failures are reported through the original exit code.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import re
import sys
import time
import unittest
import zlib

# A directly executed tools/*.py script has tools/ as sys.path[0], unlike
# python -m unittest. Preserve the original root-relative test import context.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCHEMA = "ur-unit-module-timings/1"
MODULE = re.compile(r"tests\.unit\.test_[A-Za-z0-9_]+\Z")


class TimedModuleSuite(unittest.TestSuite):
    """A nested suite preserves unittest's shared class/module lifecycle."""

    def __init__(self, name: str, tests: unittest.TestSuite, metrics: dict,
                 import_seconds: float):
        super().__init__([tests])
        self.name = name
        self.metrics = metrics
        self.import_seconds = import_seconds

    def run(self, result, debug=False):
        start = time.perf_counter()
        try:
            return super().run(result, debug)
        finally:
            self.metrics[self.name] = round(
                self.import_seconds + time.perf_counter() - start, 4)


def execute(modules: list[str], *, loader=None, runner=None,
            clock=time.perf_counter):
    """Return (unittest result, measured module seconds).

    Every provided module is loaded once and run once. The caller owns the
    exit status, and the overall suite retains a single Ran/OK/FAILED summary.
    """
    if not modules or len(set(modules)) != len(modules) or any(
        type(name) is not str or not MODULE.fullmatch(name) for name in modules
    ):
        raise ValueError("required distinct tests.unit.test_* module names")
    loader = loader or unittest.TestLoader()
    runner = runner or unittest.TextTestRunner(verbosity=2)
    measured: dict[str, float] = {}
    suites = []
    for name in modules:
        start = clock()
        test_suite = loader.loadTestsFromName(name)
        import_seconds = max(0.0, clock() - start)
        suites.append(TimedModuleSuite(name, test_suite, measured, import_seconds))
    result = runner.run(unittest.TestSuite(suites))
    if set(measured) != set(modules) or not all(
        type(t) is float and 0 <= t < 3600 for t in measured.values()
    ):
        raise ValueError("incomplete, invalid or implausible module timing coverage")
    return result, measured


def make_receipt(modules: list[str], measured: dict[str, float], passed: bool):
    return {
        "schema": SCHEMA,
        "diagnostic_only": True,
        "full_test_suite_passed": passed,
        "pr_or_test_merge_sha": os.environ.get("GITHUB_SHA", ""),
        "observed_modules": len(measured),
        "module_timings_seconds": measured,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("modules", nargs="+")
    args = parser.parse_args()
    result, measured = execute(args.modules)
    receipt = make_receipt(args.modules, measured, result.wasSuccessful())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8")
    # Bounded compressed single-line diagnostic, readable in Actions logs and
    # recoverable without downloading artifacts. Never includes test output,
    # ROM material, environment secrets or input binaries.
    packed = zlib.compress(json.dumps(receipt, sort_keys=True).encode(), level=9)
    print("UR_UNIT_TIMINGS_ZLIB64=" + base64.b64encode(packed).decode())
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
