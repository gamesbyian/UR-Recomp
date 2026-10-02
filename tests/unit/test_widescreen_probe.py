import json
import tempfile
import unittest
from pathlib import Path

from tools.widescreen_probe import load_policy, new_report, validate_report

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "analysis" / "widescreen-policy.yml"


class WidescreenProbeTests(unittest.TestCase):
    def setUp(self):
        self.policy = load_policy(POLICY)

    def make_report(self):
        return new_report(
            self.policy,
            fixture="tests/input/two-player-first-race.input",
            scene="two-player-race",
            aspect_policy="first-16x9",
            engine="diagnostic",
            revision="deadbeef",
            checkpoint_range="1220..1620",
            pixel_aspect="stock",
            overscan_policy="stock",
            layer_sprite_window_policy="default",
        )

    def test_policy_vocab_is_loaded_from_authoritative_file(self):
        self.assertEqual(self.policy["source_pixel_margins"], [0, 8, 16, 24, 32, 48, 64])
        self.assertIn("sprite-cull", self.policy["artifact_classes"])
        self.assertIn("first-16x9", self.policy["aspect_policies"])
        self.assertIn("two-player-race", self.policy["scenes"])

    def test_new_report_contains_full_default_margin_sweep_and_control(self):
        report = self.make_report()
        self.assertEqual(
            [run["margin"] for run in report["runs"]],
            self.policy["source_pixel_margins"],
        )
        self.assertEqual(report["runs"][0]["margin"], 0)
        self.assertEqual(validate_report(report, self.policy), [])

    def test_intermediate_margin_is_allowed_when_defaults_remain(self):
        report = self.make_report()
        report["runs"].append(
            {
                "margin": 20,
                "first_failure_frame": 1500,
                "class": "sprite-cull",
                "surface": "obj",
                "evidence": ["capture-20.png", "state-20.json"],
            }
        )
        self.assertEqual(validate_report(report, self.policy), [])

    def test_missing_default_margin_is_rejected(self):
        report = self.make_report()
        report["runs"] = [run for run in report["runs"] if run["margin"] != 32]
        errors = validate_report(report, self.policy)
        self.assertTrue(any("omit default source-pixel margins: 32" in e for e in errors))

    def test_unknown_class_and_duplicate_margin_are_rejected(self):
        report = self.make_report()
        report["runs"][1]["class"] = "handwave"
        report["runs"][2]["margin"] = report["runs"][1]["margin"]
        errors = validate_report(report, self.policy)
        self.assertTrue(any("handwave" in e for e in errors))
        self.assertTrue(any("duplicates margin" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
