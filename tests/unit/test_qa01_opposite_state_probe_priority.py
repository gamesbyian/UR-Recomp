"""ROM-free current-source contracts for the recovered H26 RF081 probe priority.

The original 41-pair source archive stays restricted; no synthetic fixture
passes as authentic original/native evidence or complete-event acceptance.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from tools.qa01_opposite_state_probe_priority import prioritize, audit_archive


class RF081BoundedProbePriority(unittest.TestCase):
    def test_first_bounded_and_next_onset_capture_requests(self):
        # A minimal synthetic analogue of the archived distinct endpoint gaps.
        r = prioritize([(1, True), (4, True), (8, False),
                        (16, False), (32, True), (2401, True)], 5163)
        self.assertEqual(r["earliest_bounded_probe"], 5)
        self.assertEqual(r["earliest_bounded_interval"], [4, 8])
        self.assertEqual(r["next_onset_probe"], 17)
        self.assertEqual(r["opposite_state_brackets"], 2)
        self.assertEqual(r["brackets_with_unobserved_frames"], 2)
        self.assertEqual(r["unbounded_suffix_after_last_sample"], 5163-2401)
        self.assertFalse(r["unbounded_suffix_can_localize_first_transition"])
        self.assertFalse(r["assume_monotonicity"])
        self.assertEqual(r["new_guest_observations"], 0)
        self.assertEqual(r["complete_event_credit"], 0)

    def test_adjacent_opposite_state_has_no_missing_capture(self):
        r = prioritize([(4, False), (5, True)], 5)
        self.assertEqual(r["opposite_state_brackets"], 1)
        self.assertEqual(r["brackets_with_unobserved_frames"], 0)
        self.assertIsNone(r["earliest_bounded_probe"])
        self.assertIsNone(r["next_onset_probe"])
        self.assertEqual(r["transition_brackets"][0]["first_possible_transition"], 5)

    def test_same_endpoint_not_mistaken_for_no_transition(self):
        r = prioritize([(1, False), (8, False)], 8)
        self.assertEqual(r["opposite_state_brackets"], 0)
        self.assertEqual(r["brackets_with_unobserved_frames"], 0)
        self.assertIsNone(r["earliest_bounded_probe"])
        self.assertIsNone(r["next_onset_probe"])
        self.assertFalse(r["assume_monotonicity"])

    def test_first_onset_skips_nonexact_to_exact_recovery(self):
        r = prioritize([(1, True), (3, False), (5, True),
                        (7, False), (10, True)], 10)
        self.assertEqual(r["earliest_bounded_probe"], 2)
        self.assertEqual(r["next_onset_probe"], 4)
        self.assertEqual(r["brackets_with_unobserved_frames"], 4)

    def test_invalid_population_and_types_fail_closed(self):
        invalid = ([], [(2, False), (2, True)], [(2, False), (1, True)],
                   [(1, 0)], [(1, True), (20, False)])
        for samples in invalid:
            with self.subTest(samples=samples), self.assertRaises(ValueError):
                prioritize(samples, 10)
        with self.assertRaises(ValueError):
            prioritize([(1, False)], True)

    def test_unauthenticated_archive_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "forged.zip"
            with ZipFile(path, "w") as z:
                z.writestr("work/zoom-zoo/replay/ref/scene-00001.wram.bin", b"x")
            with self.assertRaisesRegex(ValueError, "wrong RF081 evidence epoch"):
                audit_archive(path)

    def test_archive_replacement_after_first_validation_is_refused(self):
        # Model a pathname swap between the initial authenticated audit and
        # the second census. It must not parse bytes from an unpinned file.
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "swapped.zip"
            with ZipFile(path, "w") as z:
                z.writestr("work/zoom-zoo/replay/ref/scene-00001.wram.bin", b"x")
            first_audit = {"sample_count": 41, "opposite_state_brackets": [],
                           "first_nonexact_sample": None}
            with patch("tools.qa01_opposite_state_probe_priority.audit",
                       return_value=first_audit):
                with self.assertRaisesRegex(ValueError, "changed after source validation"):
                    audit_archive(path)

    def test_cli_requires_source_bound_archive_argument(self):
        script = Path(__file__).resolve().parents[2] / "tools" / "qa01_opposite_state_probe_priority.py"
        p = subprocess.run([sys.executable, str(script)],
                           capture_output=True, text=True, timeout=15)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("usage:", p.stderr)


if __name__ == "__main__":
    unittest.main()
