#!/usr/bin/env python3
"""Fail closed on unexpectedly distributable Windows smoke artifacts.

Source-only policy check. It never opens generated binaries, ROMs, or artifacts.
The Windows job still assembles and verifies its package in runner.temp.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import unittest

EXPECTED_PATHS = (
    "${{ runner.temp }}/*.log",
    "${{ runner.temp }}/hp-commit-pressure.csv",
    "${{ runner.temp }}/boot-dumps/",
    "${{ runner.temp }}/race-result-dumps/race-results.*",
    "${{ runner.temp }}/package-boot-dumps/",
    "${{ runner.temp }}/package-race-result-dumps/race-results.*",
    "${{ runner.temp }}/UR-Recomp-Windows-x64/PACKAGE-MANIFEST.json",
    "${{ runner.temp }}/UR-Recomp-Windows-x64.zip.sha256",
    "${{ runner.temp }}/windows-romfree-binary/UniracersSNESRecomp.exe",
    "${{ runner.temp }}/windows-romfree-binary/binding.json",
    "${{ runner.temp }}/windows-tournament-candidate.txt",
    "${{ runner.temp }}/tournament-qa-envelope.json",
    "!${{ runner.temp }}/**/*.sram.bin",
)


def check_workflow(source: str) -> None:
    """Validate the single, explicitly allowlisted GitHub Actions upload step."""
    # GitHub Actions allows unnamed and inline action steps. A source-only
    # check must fail closed on any extra artifact-action reference, even when
    # the step lacks a name. False positives from comments require review.
    if source.casefold().count("actions/upload-artifact@") != 1:
        raise ValueError("Expected exactly one artifact-upload action reference")

    steps = re.findall(r"(?ms)^      - name: ([^\n]+)\n(.*?)(?=^      - name: |\Z)", source)
    uploads = [(name, body) for name, body in steps
               if re.search(r"(?m)^        uses: actions/upload-artifact@", body)]
    if len(uploads) != 1:
        raise ValueError(f"Expected one artifact-upload step, found {len(uploads)}")
    name, body = uploads[0]
    if name != "Upload Windows evidence":
        raise ValueError("Unexpected artifact-upload step name")
    if not re.search(r"(?m)^        if: always\(\)$", body):
        raise ValueError("Evidence upload must run even when smoke test fails")
    if not re.search(r"(?m)^          name: windows-native-smoke$", body):
        raise ValueError("Unexpected downloadable artifact identity")
    match = re.search(r"(?m)^          path: \|\n((?:^            [^\n]+\n)+)", body)
    if match is None:
        raise ValueError("Missing explicit literal upload path list")
    paths = tuple(line.removeprefix("            ") for line in match.group(1).splitlines())
    if paths != EXPECTED_PATHS:
        raise ValueError("Windows evidence upload paths differ from archive-free allowlist")
    if not re.search(r"(?m)^          if-no-files-found: warn$", body):
        raise ValueError("Unexpected missing-evidence behavior")
    if not re.search(r"(?m)^          retention-days: 7$", body):
        raise ValueError("Unexpected artifact retention")
    if "python tools/assemble_windows_package.py verify-archive" not in source:
        raise ValueError("Internal archive verification was removed")
    if ("python tools/ci/stage_windows_smoke_romfree_exe.py" not in source
            or '--output "$RUNNER_TEMP/windows-romfree-binary"' not in source):
        raise ValueError("ROM-free PE staging is missing")


class PolicyNegatives(unittest.TestCase):
    @staticmethod
    def valid_source():
        paths = "".join(f"            {path}\n" for path in EXPECTED_PATHS)
        return ("      - name: Verify package\n"
                "        run: python tools/assemble_windows_package.py verify-archive --archive $ARCHIVE\n"
                "      - name: Stage ROM-free executable for independent audit\n"
                '        run: python tools/ci/stage_windows_smoke_romfree_exe.py --output "$RUNNER_TEMP/windows-romfree-binary"\n'
                "      - name: Upload Windows evidence\n"
                "        if: always()\n"
                "        uses: actions/upload-artifact@v4\n"
                "        with:\n"
                "          name: windows-native-smoke\n"
                "          path: |\n" + paths +
                "          if-no-files-found: warn\n"
                "          retention-days: 7\n")

    def test_current_policy(self):
        check_workflow(self.valid_source())

    def test_disallows_unstaged_pe(self):
        fixture = self.valid_source().replace(
            "python tools/ci/stage_windows_smoke_romfree_exe.py", "echo skipped")
        with self.assertRaisesRegex(ValueError, "staging"):
            check_workflow(fixture)

    def test_disallows_reexposed_sram_dumps(self):
        fixture = self.valid_source().replace(
            "            !${{ runner.temp }}/**/*.sram.bin\n", "")
        with self.assertRaisesRegex(ValueError, "allowlist"):
            check_workflow(fixture)

    def test_allows_only_exact_numeric_hp_sample_csv(self):
        check_workflow(self.valid_source())
        for unsafe in (
            "${{ runner.temp }}/hp-commit-pressure.raw",
            "${{ runner.temp }}/hp-commit-pressure.*",
            "${{ runner.workspace }}/.ur-recomp-hp-native-monitor/",
        ):
            with self.subTest(unsafe=unsafe):
                modified = self.valid_source().replace(
                    "${{ runner.temp }}/hp-commit-pressure.csv", unsafe)
                with self.assertRaisesRegex(ValueError, "allowlist"):
                    check_workflow(modified)

    def test_disallows_internal_zip(self):
        fixture = self.valid_source().replace(
            "          if-no-files-found: warn",
            "            ${{ runner.temp }}/UR-Recomp-Windows-x64.zip\n          if-no-files-found: warn")
        with self.assertRaises(ValueError):
            check_workflow(fixture)

    def test_disallows_package_directory(self):
        fixture = self.valid_source().replace(
            "${{ runner.temp }}/UR-Recomp-Windows-x64/PACKAGE-MANIFEST.json",
            "${{ runner.temp }}/UR-Recomp-Windows-x64/")
        with self.assertRaises(ValueError):
            check_workflow(fixture)

    def test_disallows_second_artifact(self):
        fixture = self.valid_source() + self.valid_source().replace(
            "Upload Windows evidence", "Upload another artifact")
        with self.assertRaises(ValueError):
            check_workflow(fixture)

    def test_disallows_unnamed_artifact_after_allowlisted_step(self):
        fixture = self.valid_source() + (
            "      - uses: actions/upload-artifact@v4\n"
            "        with:\n"
            "          name: unsafe-extra\n"
            "          path: ${{ runner.temp }}/UR-Recomp-Windows-x64.zip\n")
        with self.assertRaisesRegex(ValueError, "artifact-upload"):
            check_workflow(fixture)

    def test_disallows_unnamed_artifact_before_allowlisted_step(self):
        fixture = (
            "      - uses: actions/upload-artifact@v4\n"
            "        with:\n"
            "          path: ${{ runner.temp }}/UR-Recomp-Windows-x64.zip\n"
        ) + self.valid_source()
        with self.assertRaisesRegex(ValueError, "artifact-upload"):
            check_workflow(fixture)

    def test_disallows_inline_extra_artifact_step(self):
        fixture = self.valid_source() + (
            "      - {uses: actions/upload-artifact@v4, with: {path: private}}\n")
        with self.assertRaisesRegex(ValueError, "artifact-upload"):
            check_workflow(fixture)

    def test_disallows_variable_path(self):
        fixture = self.valid_source().replace("${{ runner.temp }}/*.log", "${{ env.EVIDENCE_ROOT }}/*")
        with self.assertRaises(ValueError):
            check_workflow(fixture)

    def test_disallows_missing_archive_verification(self):
        fixture = self.valid_source().replace("verify-archive", "verify")
        with self.assertRaises(ValueError):
            check_workflow(fixture)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("workflow", nargs="?", type=Path,
                        default=Path(__file__).resolve().parents[2] / ".github/workflows/windows-native-smoke.yml")
    args = parser.parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(PolicyNegatives)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    try:
        check_workflow(args.workflow.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        print(f"WINDOWS_SMOKE_ARTIFACT_POLICY FAIL: {exc}", file=sys.stderr)
        return 1
    print("WINDOWS_SMOKE_ARTIFACT_POLICY PASS: one archive-free allowlisted evidence upload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
