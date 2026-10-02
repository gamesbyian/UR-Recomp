import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "knowledge", ROOT / "tools" / "build_consolidated_knowledge.py"
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)

class ConsolidatedKnowledgeTests(unittest.TestCase):
    def test_course_corpus_is_complete_and_geometry_is_consistent(self):
        data = MOD.courses()
        self.assertEqual(len(data["courses"]), 45)
        for row in data["courses"]:
            w, h = row["header"]["layout_dims"]
            derived = row["derived_presentation_geometry"]
            self.assertEqual(w * h, 1024)
            self.assertEqual(derived["coarse_grid"], [w * 4, h * 4])
            self.assertEqual(derived["coarse_entry_count"], 16384)
            self.assertEqual(derived["world_extent"], [w * 256, h * 256])

    def test_stunt_slots_align_with_45_second_header_value(self):
        data = MOD.courses()
        stunt = [x for x in data["courses"] if x["track_kind"] == "stunt"]
        self.assertEqual(len(stunt), 9)
        self.assertTrue(all(x["tour_slot"] == 3 for x in stunt))
        self.assertTrue(all(x["header"]["stunt_time_or_mode"] == 45 for x in stunt))

    def test_regional_racer_relations_are_preserved(self):
        data = MOD.state()
        builds = {x["build"] for x in data["regional_racer_relations"]}
        self.assertIn("usa-retail", builds)
        self.assertIn("europe-retail", builds)
        self.assertIn("pal-prototype-1994-11-29", builds)
        self.assertTrue(all(x["bidirectional"] for x in data["regional_racer_relations"]))

    def test_code_surface_retains_structural_census(self):
        data = MOD.code()
        self.assertEqual(data["census_totals"]["regions"], len(data["regions"]))
        self.assertGreater(len(data["functions"]), 0)
        self.assertTrue(any(x["containing_structural_regions"] for x in data["functions"]))

    def test_course_stream_identity_matches_progression_row_order(self):
        data = MOD.courses()["courses"]
        expected_tours = [
            "Crawler", "Jumper", "Shuffler", "Bounder", "Walker",
            "Runner", "Hopper", "Sprinter", "Hunter",
        ]
        self.assertEqual(
            [data[i * 5]["tour"] for i in range(9)],
            expected_tours,
        )
        self.assertEqual(sum(
            1 for row in data
            if row["historical_landmarks"]["start_matches_header_a_x16"]
        ), 43)

    def test_stunt_historical_start_equals_finish(self):
        data = MOD.courses()["courses"]
        stunt = [row for row in data if row["track_kind"] == "stunt"]
        non_stunt = [row for row in data if row["track_kind"] != "stunt"]
        self.assertTrue(all(
            row["historical_landmarks"]["start_x"] == row["historical_landmarks"]["finish_x"]
            for row in stunt
        ))
        self.assertTrue(all(
            row["historical_landmarks"]["start_x"] != row["historical_landmarks"]["finish_x"]
            for row in non_stunt
        ))

    def test_claim_ids_are_unique(self):
        ids = [x["id"] for x in MOD.CLAIMS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_committed_outputs_are_fresh(self):
        for name, payload in MOD.all_data().items():
            path = ROOT / "analysis" / "data" / name
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                payload,
                name,
            )

if __name__ == "__main__":
    unittest.main()
