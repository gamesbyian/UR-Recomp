"""ONE-03: the second earned Tour race must produce its own saved run record."""
from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / 'tests/native/run_modern_results_navigation_acceptance.sh'


def isolated_guard(source: str) -> str:
    blocks = []
    for name in ('assert_absent_grep', 'assert_second_earned_run_record'):
        match = re.search(r'(?ms)^' + name + r'\(\) \{\n.*?^\}\n', source)
        if not match:
            raise AssertionError('missing shell helper ' + name)
        blocks.append(match.group(0))
    return 'set -Eeuo pipefail\n' + '\n'.join(blocks) + '\nassert_second_earned_run_record "$1" "$2"\n'


class One03EarnedRecordGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HARNESS.read_text(encoding='utf-8')
        subprocess.run(['bash', '-n', str(HARNESS)], check=True)
        cls.guard = isolated_guard(cls.source)

    def test_guard_runs_after_second_earned_result(self):
        block = self.source.split('if [ "$SHARD" = "earned" ]; then', 1)[1].split(
            'if [ "$SHARD" = "all" ] || [ "$SHARD" = "isolation" ]; then', 1)[0]
        self.assertIn('assert_second_earned_run_record "$WORK/next-earned.log"', block)
        self.assertLess(block.index('NEXT_EARNED_RESULT observed=1'),
                        block.index('assert_second_earned_run_record "$WORK/next-earned.log"'))

    def run_guard(self, text: str, movie: str = '1') -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / 'earned.log'
            log.write_text(text, encoding='utf-8')
            return subprocess.run(['bash', '-c', self.guard, '--', str(log), movie],
                                  capture_output=True, text=True, check=False)

    def test_second_course_record_passes(self):
        log = ('UR_RUN_RECORD CAPTURED path=first course=course:01 elapsed_ticks60=1714 origin_frame=981\n'
               'UR_RUN_RECORD CAPTURED path=second course=course:00 elapsed_ticks60=1505 origin_frame=2090\n')
        self.assertEqual(self.run_guard(log).returncode, 0)
        self.assertEqual(self.run_guard(log, movie='0').returncode, 0)

    def test_first_race_record_cannot_stand_in_for_second(self):
        log = 'UR_RUN_RECORD CAPTURED path=first course=course:01 elapsed_ticks60=1714\n'
        self.assertNotEqual(self.run_guard(log).returncode, 0)

    def test_wrong_course_or_source_movie_finish_rejected(self):
        for line in (
            'UR_RUN_RECORD CAPTURED path=second course=course:01 elapsed_ticks60=1505\n',
            'UR_RUN_RECORD CAPTURED path=second course=course:00 elapsed_ticks60=1506\n',
        ):
            with self.subTest(line=line):
                self.assertNotEqual(self.run_guard(line).returncode, 0)
        self.assertEqual(self.run_guard(
            'UR_RUN_RECORD CAPTURED path=second course=course:00 elapsed_ticks60=1506\n',
            movie='0').returncode, 0)

    def test_failure_marker_rejects_even_with_second_record(self):
        good = 'UR_RUN_RECORD CAPTURED path=second course=course:00 elapsed_ticks60=1505\n'
        for failure in ('FINISH_LINE_MISSING', 'FINISH_SPLIT_REJECTED',
                        'FINALIZE_REJECTED', 'SAVE_FAILED'):
            with self.subTest(failure=failure):
                self.assertNotEqual(self.run_guard(good + 'UR_RUN_RECORD ' + failure + '\n').returncode, 0)

    def test_missing_log_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / 'absent.log'
            result = subprocess.run(['bash', '-c', self.guard, '--', str(missing), '1'],
                                    capture_output=True, text=True, check=False)
            self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
