"""Native QA negative-marker assertions must really reject matches and missing logs."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "tests/native/assert_absent_grep.sh"
COVERED = [
    "run_modern_frontend_controls_acceptance.sh",
    "run_modern_frontend_options_acceptance.sh",
    "run_modern_local_tournament_capture_acceptance.sh",
    "run_modern_local_tournament_legs_acceptance.sh",
    "run_modern_local_tournament_panel_acceptance.sh",
    "run_modern_next_event_acceptance.sh",
    "run_modern_practice_picker_acceptance.sh",
    "run_modern_recent_course_persistence_acceptance.sh",
    "run_modern_regional_secret_acceptance.sh",
    "run_modern_root_acceptance.sh",
    "run_modern_tour_entry_acceptance.sh",
    "run_modern_tour_overview_acceptance.sh",
    "run_modern_two_player_join_acceptance.sh",
    "run_modern_two_player_join_record_acceptance.sh",
    "run_modern_vibration_acceptance.sh",
    "run_modern_volume_acceptance.sh",
    "run_practice_repeat_two_cycles_acceptance.sh",
    "run_windows_local_tournament_package_acceptance.sh"
]

@unittest.skipUnless(shutil.which("bash"), "native acceptance requires Bash")
class NativeNegativeDiagnosticTests(unittest.TestCase):
    def execute(self, log_path):
        command = 'set -Eeuo pipefail; source "$1"; assert_absent_grep -q "$2" "$3" || exit 1'
        return subprocess.run(
            ["bash", "-c", command, "_", str(HELPER), "FORBIDDEN_MARKER",
             str(log_path)], capture_output=True, text=True, timeout=10,
            check=False,
        )

    def test_unmatched_diagnostic_passes(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "log with spaces.txt"
            log.write_text("NORMAL RESULT\n", encoding="utf-8")
            self.assertEqual(self.execute(log).returncode, 0)

    def test_forbidden_diagnostic_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "log with spaces.txt"
            log.write_text("FORBIDDEN_MARKER\n", encoding="utf-8")
            result = self.execute(log)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("forbidden", result.stderr)

    def test_missing_log_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.execute(Path(folder) / "missing.log")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("could not inspect", result.stderr)

    def nested_execute(self, positional_index, log_path, marker):
        # Reproduce the real xvfb-run/bash -c boundary, not a function sourced
        # in the same interpreter as the test. No X server is needed here.
        arguments = ["unused"] * (positional_index - 1)
        arguments += [str(HELPER)]
        command = (
            'set -Eeuo pipefail; source "
        for name in COVERED:
            with self.subTest(name=name):
                source = (ROOT / "tests/native" / name).read_text(
                    encoding="utf-8")
                self.assertIn('assert_absent_grep.sh', source)
                self.assertRegex(source, r"(?m)^\s*assert_absent_grep -q .+ \|\| exit 1$")
                self.assertNotRegex(source, r"(?m)^\s*!\s+grep\s")
        # ONE-03 has an active draft PR. Its owner is repairing that route,
        # so this batch does not touch or override that file.
        self.assertNotIn("run_modern_results_navigation_acceptance.sh", COVERED)


if __name__ == "__main__":
    unittest.main()
 + str(positional_index) +
            '"; assert_absent_grep -q "$1" "$2" || exit 1'
        )
        # Use independent positions for the marker/log and the absolute path.
        arguments[0:0] = [marker, str(log_path)]
        # Positional shift caused by the marker/log arguments is deliberate:
        # child source is still the same numbered slot used by its real caller.
        arguments = [marker, str(log_path)] + (
            ["unused"] * (positional_index - 3)) + [str(HELPER)]
        return subprocess.run(
            ["bash", "-c", command, "_", *arguments],
            capture_output=True, text=True, timeout=10, check=False,
        )

    def test_nested_bash_child_sources_helper_and_fails_closed(self):
        regional = (ROOT / "tests/native/run_modern_regional_secret_acceptance.sh").read_text()
        tour = (ROOT / "tests/native/run_modern_tour_entry_acceptance.sh").read_text()
        self.assertEqual(regional.count('  source "$7"'), 2)
        self.assertIn('  source "$8"', tour)
        self.assertIn('"$MAIN_MENU_DUMPS" "$ASSERT_ABSENT_HELPER"', regional)
        self.assertIn('"$AUTHENTIC_DUMPS" "$ASSERT_ABSENT_HELPER"', regional)
        self.assertIn('"$root" "$ASSERT_ABSENT_HELPER"', tour)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            good = root / "good log.txt"
            bad = root / "bad log.txt"
            good.write_text("NORMAL RESULT\n")
            bad.write_text("FORBIDDEN_MARKER\n")
            for position in (7, 8):
                with self.subTest(position=position):
                    self.assertEqual(
                        self.nested_execute(position, good, "FORBIDDEN_MARKER").returncode,
                        0,
                    )
                    for filename in (bad, root / "unreadable-missing.txt"):
                        result = self.nested_execute(
                            position, filename, "FORBIDDEN_MARKER")
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn("::error::", result.stderr)

    def test_all_non_owned_native_routes_require_explicit_failure(self):
        for name in COVERED:
            with self.subTest(name=name):
                source = (ROOT / "tests/native" / name).read_text(
                    encoding="utf-8")
                self.assertIn('assert_absent_grep.sh', source)
                self.assertRegex(source, r"(?m)^\s*assert_absent_grep -q .+ \|\| exit 1$")
                self.assertNotRegex(source, r"(?m)^\s*!\s+grep\s")
        # ONE-03 has an active draft PR. Its owner is repairing that route,
        # so this batch does not touch or override that file.
        self.assertNotIn("run_modern_results_navigation_acceptance.sh", COVERED)


if __name__ == "__main__":
    unittest.main()
