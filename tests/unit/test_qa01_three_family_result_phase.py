"""Source-pinned three-family result phase counterexample, no release credit."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_three_family_result_phase as phase

TWO_PATH = ROOT / "analysis/data/two-event-original-native-result-phase-crosswalk-20261009.json"
RACE_PATH = ROOT / "analysis/data/switcher-original-baldosa-paired-race-b-result-20261010.json"


class ThreeFamilyResultPhaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.two = json.loads(TWO_PATH.read_text(encoding="utf-8"))
        cls.race = json.loads(RACE_PATH.read_text(encoding="utf-8"))

    def test_all_three_real_source_events_disagree_with_single_universal_offset(self):
        out = phase.summarize(self.two, self.race)
        self.assertEqual(out["native_minus_original_scene_relative_terminal_by_family"],
                         {"circuit-a": -1, "timed-stunt": -1, "race-b": -2})
        self.assertEqual([x["course"] for x in out["witnesses"]],
                         ["course:02", "course:03", "course:04"])
        self.assertTrue(out["single_universal_scene_relative_frame_offset_disproven"])
        self.assertFalse(out["guest_cpu_instruction_phase_equivalence_proven"])
        self.assertFalse(out["retroactive_retiming_or_result_phase_waiver_permitted"])
        self.assertEqual(out["official_usa_complete_event_count"], 0)
        self.assertEqual(out["official_usa_course_denominator"], 45)
        race = out["witnesses"][-1]["phase"]
        self.assertEqual(race["native_entry_minus_original"], 2)
        self.assertEqual(race["native_result_minus_original"], 0)
        self.assertEqual(race["original_result_relative"], 4704)
        self.assertEqual(race["native_result_relative"], 4702)

    def test_conflicting_or_fake_original_snes9x_race_evidence_fails_closed(self):
        mutations = (
            ("execution", "workflow_run_id", 0),
            ("provenance", "original_movie_sha256", "f" * 64),
            ("original_source", "original_movie_result_frame", 17029),
            ("independently_observed_replay", "reference_entry_absolute_host_frame", 1080),
            ("independently_observed_replay", "native_result_onset_absolute_host_frame", 5784),
            ("independently_observed_replay", "native_result_guest_relative_frame", 4704),
            ("independently_observed_replay", "player_one_time", "1:08.80"),
            ("independently_observed_replay", "terminal_guest_relative_result_frame_matched", True),
            ("independently_observed_replay", "full_event_parity_admitted", True),
            ("release", "usa_accepted_events", 1),
        )
        for group, key, replacement in mutations:
            doc = copy.deepcopy(self.race)
            doc[group][key] = replacement
            with self.subTest(group=group, key=key), self.assertRaises(ValueError):
                phase.summarize(self.two, doc)

    def test_wrong_or_missing_circuit_stunt_provenance_fails_closed(self):
        for i, key, value in (
            (0, "run", 0),
            (0, "native_entry", 1607),
            (0, "original_relative", 5164),
            (1, "kind", "circuit-a"),
            (1, "artifact", 0),
        ):
            doc = copy.deepcopy(self.two)
            doc["measurements"][i][key] = value
            with self.subTest(i=i, key=key), self.assertRaises(ValueError):
                phase.summarize(doc, self.race)

    def test_frame_arithmetic_rejects_invented_or_negative_timelines(self):
        for frames in ((1079, 1081, 1078, 5783),
                       (1079, 1081, 5783, -1),
                       (1079, True, 5783, 5783)):
            with self.subTest(frames=frames), self.assertRaises(ValueError):
                phase.phase(*frames)


if __name__ == "__main__":
    unittest.main()
