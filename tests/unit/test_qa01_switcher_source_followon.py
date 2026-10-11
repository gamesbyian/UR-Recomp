"""Source-only post-Switcher-result activation guard; no course admission."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_switcher_source_followon as walk


def source_states(*, first_next=17300, next_track=4, next_length=10):
    s = {f: {"menu": 0x99, "track": 3, "in_race": 0}
         for f in range(0, 17500)}
    s[12327] = {"menu": 0x16, "track": 3, "in_race": 1}
    for f in range(first_next, first_next + next_length):
        s[f] = {"menu": 0x16, "track": next_track, "in_race": 1}
    return s


class SwitcherSourceFollowOnTests(unittest.TestCase):
    def test_source_followon_is_candidate_not_native_or_complete_event(self):
        result = walk.summarize(source_states())
        self.assertEqual(result["schema"], walk.SCHEMA)
        self.assertEqual(result["original_2014_source_movie_entry_frame"], 12327)
        self.assertEqual(result["original_2014_source_movie_result_frame"], 17030)
        candidate = result["first_original_source_post_result_active_candidate"]
        self.assertEqual(candidate["original_source_first_active_frame"], 17300)
        self.assertEqual(candidate["original_source_track"], 4)
        self.assertEqual(candidate["contiguous_active_frames"], 10)
        self.assertFalse(candidate["is_definitive_native_follow_on"])
        self.assertFalse(result["actual_original_native_post_result_entry_comparison"])
        self.assertEqual(result["release_complete_event_credit"], 0)

    def test_transient_or_absent_followon_is_a_bounded_negative(self):
        for length in (0, 1, 7):
            with self.subTest(length=length):
                data = walk.summarize(source_states(next_length=length))
                self.assertIsNone(data["first_original_source_post_result_active_candidate"])
                self.assertTrue(data["bounded_source_only_negative_if_no_candidate"])

    def test_switcher_rematch_is_not_misidentified_as_new_track(self):
        data = walk.summarize(source_states(next_track=3))
        self.assertTrue(data["first_original_source_post_result_active_candidate"]
                        ["same_track_as_completed_switcher"])

    def test_forged_result_and_future_frames_fail_closed(self):
        cases = []
        x = source_states(); x[17030]["track"] = 2; cases.append(x)
        x = source_states(); x[17030]["menu"] = 0x84; cases.append(x)
        x = source_states(); x[17030]["in_race"] = 1; cases.append(x)
        x = source_states(); x[17030]["in_race"] = 2; cases.append(x)
        x = source_states(); x[17030].pop("in_race"); cases.append(x)
        x = source_states(); x[22001] = x[17499]; cases.append(x)
        x = source_states(); x.pop(17030); cases.append(x)
        x = source_states(); x.pop(12327); cases.append(x)
        x = source_states(); x[12327]["track"] = 2; cases.append(x)
        x = source_states(); x[12327]["in_race"] = True; cases.append(x)
        x = source_states(); x.pop(13000); cases.append(x)
        x = source_states(); x.pop(17100); cases.append(x)
        x = source_states(); x[17300]["in_race"] = 2; cases.append(x)
        x = source_states(); x[17300]["menu"] = -1; cases.append(x)
        x = source_states(); x[17300]["track"] = "unknown"; cases.append(x)
        for state in cases:
            with self.subTest(bad=repr(state.get(17030))), self.assertRaises(ValueError):
                walk.summarize(state)

    def test_source_trace_budget_and_real_tooling_wiring(self):
        self.assertEqual(walk.RESULT, 17030)
        self.assertEqual(walk.HORIZON, 22000)
        wf = (ROOT / ".github/workflows/qa01-switcher-original-2014.yml").read_text()
        self.assertIn("qa01_switcher_source_followon.py", wf)
        self.assertIn('source_horizon }}" = "22000"', wf)
        self.assertIn('source-followon.json', wf)


if __name__ == "__main__":
    unittest.main()
