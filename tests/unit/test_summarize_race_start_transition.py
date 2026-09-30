import json
import tempfile
import unittest
from pathlib import Path

from tools.summarize_race_start_transition import summarize_transition


class RaceStartTransitionTests(unittest.TestCase):
    def test_requires_matching_capture_files(self):
        with tempfile.TemporaryDirectory() as td:
            report = summarize_transition(Path(td))
            self.assertEqual(report["checkpoints"], [])
            self.assertEqual(report["change_points"], [])


if __name__ == "__main__":
    unittest.main()
