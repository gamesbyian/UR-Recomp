import unittest

from tools.analyze_widescreen_vs_policy import analyze


def checkpoint(*, x1=100, x2=200, camera=10, vram_count=1):
    return {
        "slot1": {"x_pos": x1},
        "slot2": {"x_pos": x2},
        "race_progress": {"player1": {"next_checkpoint": 3}, "player2": {"next_checkpoint": 4}},
        "camera_and_viewport": {"camera": {"player1_x": camera}},
        "vram_update_lists": {"list_a_count_raw": vram_count},
    }


class WidescreenVsPolicyTests(unittest.TestCase):
    def test_accepts_presentation_only_difference(self):
        control = {"vs-race-1240": checkpoint(vram_count=1)}
        widened = {"vs-race-1240": checkpoint(vram_count=2)}
        report = analyze(
            control, widened, {"plus8_preparation_hook_observed": True}
        )
        self.assertTrue(report["semantic_activation_preserved"])
        self.assertTrue(report["promotion_ready"])
        self.assertEqual(report["classification"], "ordinary-2p-mixed-compatible")
        self.assertTrue(report["rows"][0]["protected_equal"])
        self.assertIn("vram_update_lists", report["rows"][0]["presentation_differences"])

    def test_rejects_camera_or_gameplay_difference(self):
        control = {"vs-race-1240": checkpoint(camera=10)}
        widened = {"vs-race-1240": checkpoint(camera=11)}
        report = analyze(
            control, widened, {"plus8_preparation_hook_observed": True}
        )
        self.assertFalse(report["semantic_activation_preserved"])
        self.assertFalse(report["promotion_ready"])
        self.assertEqual(report["classification"], "distinct-vs-semantic-exception-required")
        self.assertIn("camera_and_viewport", report["rows"][0]["protected_differences"])

    def test_preserved_state_without_provider_requires_distinct_preparation_path(self):
        control = {"vs-race-1240": checkpoint()}
        widened = {"vs-race-1240": checkpoint()}
        report = analyze(
            control, widened, {"plus8_preparation_hook_observed": False}
        )
        self.assertTrue(report["semantic_activation_preserved"])
        self.assertFalse(report["promotion_ready"])
        self.assertTrue(report["evidence_complete"])
        self.assertEqual(report["classification"], "distinct-vs-preparation-path-required")

    def test_rejects_checkpoint_mismatch(self):
        with self.assertRaisesRegex(ValueError, "checkpoint mismatch"):
            analyze({"a": checkpoint()}, {"b": checkpoint()})


if __name__ == "__main__":
    unittest.main()
