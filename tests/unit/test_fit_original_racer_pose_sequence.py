"""ROM-free regression tests for source-frame-indexed temporal pose labels."""
import copy
import unittest
from tools.art.fit_original_racer_pose_sequence import fit


class PoseSequenceTests(unittest.TestCase):
    def example(self):
        return {"poses": ["upright", "bank"], "change_penalty": 2,
                "frames": [{"window": "first", "player": "p1", "guest_frame": frame,
                            "costs": {"upright": u, "bank": b}}
                           for frame, (u, b) in enumerate([(0, 1), (1, 0), (0, 1)], 1205)]}

    def test_temporal_fit_avoids_independent_flips(self):
        result = fit(self.example())["sequences"][0]
        self.assertEqual(result["independent_poses"], ["upright", "bank", "upright"])
        self.assertEqual(result["sequence_poses"], ["upright"] * 3)
        self.assertEqual(result["sequence_emission_cost"], 1)
        self.assertEqual(result["sequence_transition_count"], 0)
        self.assertEqual(result["independent_transition_count"], 2)
        self.assertEqual(result["sequence_transition_cost"], 0)

    def test_actual_missing_guest_frame_breaks_sequence(self):
        data = self.example()
        data["frames"][2]["guest_frame"] = 1210
        self.assertEqual([len(s["guest_frames"]) for s in fit(data)["sequences"]], [2, 1])

    def test_player_and_window_are_separate(self):
        data = self.example()
        data["frames"] += [
            {"window": "first", "player": "p2", "guest_frame": 1205,
             "costs": {"upright": 9, "bank": 0}},
            {"window": "second", "player": "p2", "guest_frame": 1206,
             "costs": {"upright": 9, "bank": 0}}]
        output = fit(data)["sequences"]
        self.assertEqual(len(output), 3)
        self.assertEqual(output[-2]["sequence_poses"], ["bank"])

    def test_interleaved_player_major_tracks_preserve_real_continuity(self):
        first = self.example()
        p1 = first["frames"]
        p2 = [
            {"window": "first", "player": "p2", "guest_frame": 1205 + offset,
             "costs": {"upright": u, "bank": b}}
            for offset, (u, b) in enumerate([(1, 0), (0, 1), (1, 0)])
        ]
        first["frames"] = [row for pair in zip(p1, p2) for row in pair]
        actual = fit(first)["sequences"]
        self.assertEqual(len(actual), 2)
        self.assertEqual([s["guest_frames"] for s in actual], [[1205, 1206, 1207]] * 2)
        self.assertEqual([s["player"] for s in actual], ["p1", "p2"])
        self.assertEqual(actual[0]["independent_poses"], ["upright", "bank", "upright"])
        self.assertEqual(actual[1]["independent_poses"], ["bank", "upright", "bank"])
        self.assertEqual(actual[0]["sequence_poses"], ["upright"] * 3)
        self.assertEqual(actual[1]["sequence_poses"], ["bank"] * 3)
        self.assertEqual(sum(s["independent_transition_count"] for s in actual), 4)

    def test_interleaved_player_gap_breaks_only_affected_track(self):
        first = self.example()
        p1 = first["frames"]
        p2 = [
            {"window": "first", "player": "p2", "guest_frame": 1205 + offset,
             "costs": {"upright": 1, "bank": 0}}
            for offset in range(3)
        ]
        p1[2]["guest_frame"] = 1210
        first["frames"] = [row for pair in zip(p1, p2) for row in pair]
        sequences = fit(first)["sequences"]
        by_track = {player: [s["guest_frames"] for s in sequences
                             if s["player"] == player]
                    for player in ("p1", "p2")}
        self.assertEqual(by_track["p1"], [[1205, 1206], [1210]])
        self.assertEqual(by_track["p2"], [[1205, 1206, 1207]])

    def test_bad_inputs_fail_closed(self):
        for variant in ("nan", "boolean", "duplicate", "missing", "negative",
                        "transition", "out_of_order", "missing_number", "wrong_player"):
            data = self.example()
            if variant == "nan":
                data["frames"][0]["costs"]["bank"] = float("nan")
            elif variant == "boolean":
                data["frames"][0]["costs"]["bank"] = True
            elif variant == "duplicate":
                data["frames"][1]["guest_frame"] = 1205
            elif variant == "missing":
                del data["frames"][1]["costs"]["bank"]
            elif variant == "negative":
                data["frames"][0]["costs"]["bank"] = -1
            elif variant == "transition":
                data["transition_penalties"] = {
                    "upright": {"upright": 0, "bank": -1},
                    "bank": {"upright": 0, "bank": 0}}
            elif variant == "out_of_order":
                data["frames"][2]["guest_frame"] = 1204
            elif variant == "missing_number":
                del data["frames"][1]["guest_frame"]
            else:
                data["frames"][1]["player"] = "p3"
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                fit(data)

    def test_deterministic_lexical_tie_break(self):
        data = self.example()
        for frame in data["frames"]:
            frame["costs"] = {"upright": 0, "bank": 0}
        expected = fit(data)["sequences"][0]["sequence_poses"]
        data["poses"].reverse()
        self.assertEqual(expected, fit(data)["sequences"][0]["sequence_poses"])

    def test_complete_custom_transition_matrix(self):
        data = self.example()
        data["transition_penalties"] = {
            "upright": {"upright": 0, "bank": 100},
            "bank": {"upright": 100, "bank": 0}}
        self.assertEqual(fit(data)["sequences"][0]["sequence_poses"], ["upright"] * 3)

    def test_reproducibility_and_no_mutation(self):
        data = self.example()
        original = copy.deepcopy(data)
        self.assertEqual(fit(data), fit(data))
        self.assertEqual(data, original)


if __name__ == "__main__":
    unittest.main()
