"""The generated QA01 census must agree with authoritative source data."""
import difflib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CENSUS = ROOT / "analysis/generated/course-event-qa-census.json"


class CourseEventCensusSourceSyncTests(unittest.TestCase):
    def test_generated_census_matches_authoritative_sources(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "course-event-qa-census.json"
            generated = subprocess.run(
                [sys.executable, "tools/audit_original_course_event_coverage.py",
                 "--out", str(output)],
                cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(generated.returncode, 0,
                             generated.stderr + generated.stdout)
            actual = CENSUS.read_text(encoding="utf-8").splitlines()
            expected = output.read_text(encoding="utf-8").splitlines()
            diff = list(difflib.unified_diff(
                actual, expected, fromfile="checked-in-census",
                tofile="generated-from-source", lineterm=""))
            self.assertFalse(diff, "generated census differs:\n" + "\n".join(diff[:100]))


if __name__ == "__main__":
    unittest.main()
