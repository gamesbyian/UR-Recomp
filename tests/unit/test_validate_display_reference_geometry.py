import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "display_reference_geometry",
    ROOT / "tools/validate_display_reference_geometry.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class DisplayReferenceGeometryTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(
            (ROOT / "analysis/display-reference-geometry.json").read_text(encoding="utf-8")
        )

    def test_official_manual_supports_4x3_family_not_raw_square(self):
        result = MOD.analyze(self.data)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["sample_count"], 11)
        self.assertTrue(result["all_uncertainty_intervals_admit_4x3"])
        self.assertFalse(result["any_uncertainty_interval_admits_raw_8x7"])
        self.assertEqual(result["pixel_aspect_consequence_for_256x224"], "7:6")

    def test_par_evidence_does_not_close_overscan(self):
        result = MOD.analyze(self.data)
        self.assertEqual(result["overscan_disposition"], "unresolved")

    def test_uncertainty_interval_is_conservative(self):
        low, high = MOD.ratio_interval(223, 163, 5)
        self.assertLess(low, 4 / 3)
        self.assertGreater(high, 4 / 3)
        self.assertGreater(low, 8 / 7)


if __name__ == "__main__":
    unittest.main()
