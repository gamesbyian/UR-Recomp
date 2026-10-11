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

    def test_no_post_result_changed_bytes_is_inconclusive_not_a_nmi_blocker(self):
        # A successful original script horizon can extend beyond the last
        # changed-byte record. The optional sidecar cannot reject that run.
        bounded = {f: state for f, state in source_states().items()
                   if f <= 17030}
        data = walk.summarize(bounded)
        self.assertIsNone(data["first_original_source_post_result_active_candidate"])
        self.assertTrue(data["post_result_changed_byte_trace_inconclusive_if_empty"])
        self.assertEqual(data["last_decoded_original_source_frame"], 17030)
        self.assertEqual(data["observed_post_result_frames"], 0)
        self.assertFalse(data["bounded_source_only_negative_if_no_candidate"])
        self.assertFalse(data["actual_original_native_post_result_entry_comparison"])
        self.assertEqual(data["release_complete_event_credit"], 0)

    def test_original_stunt_scratch_0313_is_ambiguous_not_corrupt(self):
        # Actual executed 2014 Bowl Stunt diagnostic shows 0313==60.
        # A later Stunt after Switcher could carry that same non-race
        # meaning, so do not reject the source movie or call it no event.
        states = source_states(next_length=0)
        for f in range(17150, 17165):
            states[f] = {"menu": 0x2F, "track": 4, "in_race": 60}
        data = walk.summarize(states)
        self.assertEqual(data["nonbinary_post_result_race_state_frame_count"], 15)
        self.assertIsNone(data["first_original_source_post_result_active_candidate"])
        self.assertFalse(data["bounded_source_only_negative_if_no_candidate"])
        self.assertTrue(data[
            "nonbinary_0313_frames_are_ambiguous_timing_or_scratch_not_active_race_proof"])
        self.assertEqual(data["release_complete_event_credit"], 0)
        states[17151]["in_race"] = 256
        with self.assertRaises(ValueError):
            walk.summarize(states)

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
        x = source_states(); x[17300]["menu"] = -1; cases.append(x)
        x = source_states(); x[17300]["track"] = "unknown"; cases.append(x)
        for state in cases:
            with self.subTest(bad=repr(state.get(17030))), self.assertRaises(ValueError):
                walk.summarize(state)

    def test_changed_byte_jsonl_requires_monotonic_bounded_source_rows(self):
        # No invented true gameplay observations: the historic trace decoder
        # is reused after checking JSON shape, source frame order and bounds.
        sequence = [
            '{"f":0,"adr":"0x0009f","val":"0x84"}',
            '{"f":12327,"adr":"0x000ce","val":"0x03"}',
            '{"f":17030,"adr":"009F","val":"99"}',
            '{"f":17031,"adr":"0x00313","val":"0x00"}',
        ]
        data = walk.decode_checked_changed_byte_trace(sequence)
        self.assertEqual(data[17031]["menu"], 0x99)
        self.assertEqual(data[17031]["track"], 3)
        self.assertEqual(data[17031]["in_race"], 0)
        for bad in (
            [sequence[2], sequence[1]],
            [sequence[0], '{"f":22001,"adr":"0313","val":"01"}'],
            [sequence[0], '{"f":true,"adr":"0313","val":"01"}'],
            [sequence[0], '{"f":3,"adr":"0313","val":"ZZ"}'],
            [sequence[0], '{"f":3,"adr":"0313","val":"100"}'],
            [sequence[0], '{"f":3,"adr":"0x00313","val":"0x100"}'],
            [sequence[0], '{"f":3,"adr":"NOPE","val":"00"}'],
            [sequence[0], '{"f":3,"adr":"-01","val":"00"}'],
            [sequence[0], '{"f":3,"adr":"0x01junk","val":"00"}'],
            [sequence[0], '{"f":3,"adr":"0313","val":0}'],
            [sequence[0], "not a JSON line"],
            [sequence[0], "[]"],
        ):
            with self.subTest(bad=bad[-1]), self.assertRaises(ValueError):
                walk.decode_checked_changed_byte_trace(bad)

    def test_source_trace_budget_and_real_tooling_wiring(self):
        self.assertEqual(walk.RESULT, 17030)
        self.assertEqual(walk.HORIZON, 22000)
        wf = (ROOT / ".github/workflows/qa01-switcher-original-2014.yml").read_text()
        self.assertIn("qa01_switcher_source_followon.py", wf)
        self.assertIn('source_horizon }}" = "22000"', wf)
        self.assertIn('source-followon.json', wf)


if __name__ == "__main__":
    unittest.main()
