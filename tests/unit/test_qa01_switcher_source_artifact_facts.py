"""Pin original executable source scratch field values and no release credit."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_switcher_source_artifact_facts as checker

F = ROOT / "analysis/data/qa01-switcher-2014-original-source-scratch-20261011.json"
P = ROOT / "analysis/data/switcher-original-baldosa-paired-race-b-result-20261010.json"


class OriginalSourceScratchArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.facts = json.loads(F.read_text(encoding="utf-8"))
        cls.pair = json.loads(P.read_text(encoding="utf-8"))

    def test_real_original_bowl_stunt_0313_is_60_and_switcher_result_is_real(self):
        result = checker.verify(self.facts, self.pair)
        self.assertEqual(result["source_observation_count"], 5)
        self.assertTrue(result["original_stunt_raw_0313_nonbinary_confirmed"])
        self.assertEqual(result["release_usa_events_accepted"], 0)
        self.assertEqual(self.facts["execution"]["artifact_id"], 11674751560)

    def test_altered_original_source_or_release_credit_rejected(self):
        for part, key, value in (
            ("execution", "artifact_id", 0),
            ("execution", "member_sha256", "f"*64),
            ("original_movie_context", "source_movie_switcher_result", 17029),
            ("original_movie_context", "original_source_result_stable_end", 17030),
            ("release", "qa_credit", 1),
            ("source_foreign_active_track_zero_prelude", "length", 33),
        ):
            doc = copy.deepcopy(self.facts)
            doc[part][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                checker.verify(doc, self.pair)
        doc = copy.deepcopy(self.facts)
        doc["source_state_examples"][0]["raw_0313"] = 1
        with self.assertRaises(ValueError):
            checker.verify(doc, self.pair)
        doc = copy.deepcopy(self.facts)
        doc["source_state_examples"].append(copy.deepcopy(doc["source_state_examples"][0]))
        with self.assertRaises(ValueError):
            checker.verify(doc, self.pair)


if __name__ == "__main__":
    unittest.main()
