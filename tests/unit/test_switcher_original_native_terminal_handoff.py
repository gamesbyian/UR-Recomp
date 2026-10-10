"""Executed original 2014 Switcher/Baldosa terminal evidence, not simulation or release proof."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import probe_original_event_complete as probe

OBSERVATION = (ROOT / "analysis" / "data"
               / "switcher-original-baldosa-terminal-handoff-20261010.json")


class SwitcherOriginalNativeObservedBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(OBSERVATION.read_text(encoding="utf-8"))

    def test_artifact_hashes_and_admission_are_pinned(self):
        d = self.doc
        self.assertEqual(d["provenance"]["original_native_run_id"], 38072910224)
        self.assertEqual(d["provenance"]["artifact_id"], 11678085612)
        self.assertEqual(
            d["provenance"]["artifact_zip_sha256"],
            "8f61dd5bbbddfc11db6a962d27364d6667fb8532b8c2bdce5a688decb05d317e")
        self.assertEqual(
            d["provenance"]["result_json_sha256"],
            "ca6fd7e2a943f606650dec770d44be85e057a8315c3549491a2f922ece150eeb")
        self.assertTrue(d["provenance"]["workflow_pr_closed_unmerged"])
        self.assertEqual(d["strict_acceptance"]["release_credit"], 0)
        self.assertEqual(d["strict_acceptance"]["official_usa_accepted_courses"], 0)
        self.assertEqual(d["strict_acceptance"]["denominator"], 45)

    def test_observed_transition_and_two_host_clocks_are_not_interchanged(self):
        d = self.doc
        obs = d["actual_run"]
        phase = d["source_relative_terminal_states"]
        self.assertEqual(obs["sampled_guest_frames_per_engine"], 43)
        self.assertEqual(obs["first_guest_reference_entry_host"], 1079)
        self.assertEqual(obs["first_guest_native_entry_host"], 1081)
        self.assertEqual(obs["source_original_result_relative"], 4704)
        self.assertEqual(obs["native_result_relative"], 4702)
        self.assertEqual(obs["original_result_host"], 5783)
        self.assertEqual(obs["native_result_host"], 5783)
        self.assertEqual(obs["result_text"][4], "1:08.81")
        for entry, result in (
            (obs["first_guest_reference_entry_host"],
             obs["source_original_result_relative"]),
            (obs["first_guest_native_entry_host"],
             obs["native_result_relative"]),
        ):
            self.assertEqual(entry + result, 5783)
        self.assertEqual([x["relative_frame"] for x in phase["differing"]],
                         [4664, 4697, 4698])
        self.assertEqual(
            [(x["reference_menu"], x["reference_track"],
              x["native_menu"], x["native_track"]) for x in phase["differing"]],
            [(0, 3, 132, 0), (132, 0, 22, 3), (132, 0, 22, 3)])
        self.assertEqual(
            phase["paired_identical_at"],
            [4623, 4653, 4661, 4663, 4665, 4666, 4673, 4683,
             4693, 4694, 4695, 4696])
        self.assertTrue(all(x["other_semantic_sample_fields_equal"]
                            for x in phase["differing"]))
        self.assertTrue(phase["all_observed_non_menu_track_fields_identical_at_43_paired_relative_frames"])
        self.assertFalse(d["strict_acceptance"]["original_native_terminal_guest_relative_matched"])
        self.assertTrue(d["strict_acceptance"]["original_native_terminal_host_absolute_matched"])

    def test_new_probes_end_before_native_result_and_do_not_rebase_inputs(self):
        d = self.doc
        samples = probe.sample_frames("switcher", 4703)
        self.assertEqual(samples[-3:], [4699, 4700, 4701])
        self.assertLess(samples[-1], d["actual_run"]["native_result_relative"])
        self.assertEqual(
            samples[-3:],
            [d["actual_run"]["source_original_result_relative"] - i
             for i in (5, 4, 3)])
        script = probe.replay_script(4, 0x99, samples, False)
        self.assertNotIn("poke ", script)
        self.assertIn("dump scene-04701", script)
        self.assertLess(script.index("dump scene-04701"),
                        script.index("until 009F == 99 9000"))
        self.assertEqual(probe.sample_frames("bowl", 3365)[-1], 2400)
        self.assertEqual(probe.sample_frames("zoom-zoo", 5163)[-1], 2400)


if __name__ == "__main__":
    unittest.main()
