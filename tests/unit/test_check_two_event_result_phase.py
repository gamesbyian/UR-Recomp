"""Two independent result phase offsets must not be promoted into QA passes."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_two_event_result_phase as phase


class TwoEventResultPhaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((
            ROOT / "analysis/data/two-event-original-native-result-phase-crosswalk-20261009.json"
        ).read_text())

    def test_original_and_native_phase_offset_source_and_no_release_credit(self):
        result = phase.check_crosswalk(self.source)
        self.assertEqual(result["official_usa_complete_accepted"], 0)
        self.assertEqual(result["phase_offset_native_minus_original"], -1)
        self.assertEqual(result["causal_conclusion"], "unresolved")
        kinds = {x["kind"]: x for x in self.source["measurements"]}
        self.assertEqual(kinds["circuit-a"]["derived"][
            "native_minus_original_entry_host_frames"], 2)
        self.assertEqual(kinds["timed-stunt"]["derived"][
            "native_minus_original_entry_host_frames"], 1)
        self.assertEqual(kinds["timed-stunt"]["derived"][
            "native_minus_original_terminal_host_frames"], 0)
        self.assertEqual(kinds["circuit-a"]["derived"][
            "native_minus_original_terminal_host_frames"], 1)

    def test_forged_phase_or_course_admission_fails_closed(self):
        for field, value in (("release_usa_accepted_courses", 1),
                             ("release_usa_denominator", 44)):
            bad = copy.deepcopy(self.source)
            bad[field] = value
            with self.assertRaisesRegex(ValueError, "cannot promote"):
                phase.check_crosswalk(bad)
        bad = copy.deepcopy(self.source)
        bad["measurements"][1]["native_terminal"] += 1
        with self.assertRaisesRegex(ValueError, "incorrect scene-relative"):
            phase.check_crosswalk(bad)
        bad = copy.deepcopy(self.source)
        bad["measurements"][1]["derived"]["result_host_shift_minus_entry_host_shift"] = 0
        with self.assertRaisesRegex(ValueError, "arithmetic inconsistent"):
            phase.check_crosswalk(bad)
        bad = copy.deepcopy(self.source)
        bad["measurements"][1]["native_relative"] = 3365
        bad["measurements"][1]["native_entry"] = 984
        bad["measurements"][1]["derived"] = {
            "native_minus_original_entry_host_frames": 0,
            "native_minus_original_terminal_host_frames": 0,
            "native_minus_original_terminal_scene_relative_frames": 0,
            "result_host_shift_minus_entry_host_shift": 0,
        }
        with self.assertRaisesRegex(ValueError, "minus-one"):
            phase.check_crosswalk(bad)
        bad = copy.deepcopy(self.source)
        bad["measurements"][1]["kind"] = "circuit-a"
        with self.assertRaisesRegex(ValueError, "duplicate event family"):
            phase.check_crosswalk(bad)


if __name__ == "__main__":
    unittest.main()
