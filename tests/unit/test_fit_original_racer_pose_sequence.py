"""ROM-free regression tests for temporal pose assignment."""
import unittest
from tools.art.fit_original_racer_pose_sequence import fit


class PoseSequenceTests(unittest.TestCase):
    def example(self):
        return {"poses": ["upright", "bank"], "change_penalty": 2,
                "frames": [
                    {"id": "A1", "family": "A", "costs": {"upright": 0, "bank": 1}},
                    {"id": "A2", "family": "A", "costs": {"upright": 1, "bank": 0}},
                    {"id": "A3", "family": "A", "costs": {"upright": 0, "bank": 1}}]}

    def test_temporal_labeling_beats_independent_flips(self):
        result = fit(self.example())["sequences"][0]
        self.assertEqual(result["independent_poses"], ["upright", "bank", "upright"])
        self.assertEqual(result["sequence_poses"], ["upright"] * 3)
        self.assertEqual(result["sequence_emission_cost"], 1)

    def test_family_break_is_not_connected(self):
        data = self.example()
        data["frames"].append({"id": "B1", "family": "B", "costs": {"upright": 9, "bank": 0}})
        self.assertEqual(fit(data)["sequences"][1]["sequence_poses"], ["bank"])

    def test_bad_inputs(self):
        for variant in ("nan", "duplicate", "missing", "bad-transition"):
            data = self.example()
            if variant == "nan":
                data["frames"][0]["costs"]["bank"] = float("nan")
            elif variant == "duplicate":
                data["frames"][1]["id"] = "A1"
            elif variant == "missing":
                del data["frames"][1]["costs"]["bank"]
            else:
                data["transition_penalties"] = {"upright": {"upright": 0, "bank": -1}, "bank": {"upright": 0, "bank": 0}}
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                fit(data)

    def test_reproducible(self):
        self.assertEqual(fit(self.example()), fit(self.example()))


if __name__ == "__main__":
    unittest.main()
