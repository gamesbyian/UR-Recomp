import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from tools.widescreen_probe import (
    derive_symmetric_margin,
    load_policy,
    new_report,
    parse_ratio,
    validate_report,
)

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
        self.assertEqual(self.policy["materializer_granularity_pixels"], 8)
        self.assertEqual(self.policy["validated_capacity_margin_pixels"], 64)
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



    def test_ratio_parser_accepts_colon_and_slash(self):
        self.assertEqual(parse_ratio("16:9"), Fraction(16, 9))
        self.assertEqual(parse_ratio("7/6"), Fraction(7, 6))
        with self.assertRaises(ValueError):
            parse_ratio("0:1")

    def test_derive_16x9_margin_for_7x6_224_line_policy(self):
        result = derive_symmetric_margin(
            base_logical_width=256,
            logical_height=224,
            target_aspect=Fraction(16, 9),
            pixel_aspect=Fraction(7, 6),
            granularity=8,
            capacity_margin=64,
        )
        self.assertEqual(result["required_logical_width"]["numerator"], 1024)
        self.assertEqual(result["required_logical_width"]["denominator"], 3)
        self.assertEqual(result["symmetric_margin_exact"]["numerator"], 128)
        self.assertEqual(result["symmetric_margin_exact"]["denominator"], 3)
        self.assertEqual(result["materializer_margin_pixels"], 48)
        self.assertTrue(result["capacity_sufficient"])

    def test_square_pixel_224_line_policy_needs_more_than_plus64(self):
        result = derive_symmetric_margin(
            base_logical_width=256,
            logical_height=224,
            target_aspect=Fraction(16, 9),
            pixel_aspect=Fraction(1, 1),
            granularity=8,
            capacity_margin=64,
        )
        self.assertEqual(result["symmetric_margin_exact"]["numerator"], 640)
        self.assertEqual(result["symmetric_margin_exact"]["denominator"], 9)
        self.assertEqual(result["materializer_margin_pixels"], 72)
        self.assertFalse(result["capacity_sufficient"])

    def test_square_pixel_216_line_policy_fits_exactly_at_plus64(self):
        result = derive_symmetric_margin(
            base_logical_width=256,
            logical_height=216,
            target_aspect=Fraction(16, 9),
            pixel_aspect=Fraction(1, 1),
            granularity=8,
            capacity_margin=64,
        )
        self.assertEqual(result["required_logical_width"]["numerator"], 384)
        self.assertEqual(result["required_logical_width"]["denominator"], 1)
        self.assertEqual(result["symmetric_margin_exact"]["numerator"], 64)
        self.assertEqual(result["symmetric_margin_exact"]["denominator"], 1)
        self.assertEqual(result["materializer_margin_pixels"], 64)
        self.assertTrue(result["capacity_sufficient"])

    def test_unknown_class_and_duplicate_margin_are_rejected(self):
        report = self.make_report()
        report["runs"][1]["class"] = "handwave"
        report["runs"][2]["margin"] = report["runs"][1]["margin"]
        errors = validate_report(report, self.policy)
        self.assertTrue(any("handwave" in e for e in errors))
        self.assertTrue(any("duplicates margin" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
