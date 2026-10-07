import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "compare_frontend_transition_reports.py"

spec = importlib.util.spec_from_file_location("transition_compare", TOOL)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def row(index, changed=10, horizontal=0, horizontal_gain=0.0,
        vertical=0, vertical_gain=0.0):
    return {
        "from_index": index,
        "to_index": index + 1,
        "changed_pixels": changed,
        "best_shift_pixels": horizontal,
        "agreement_gain": horizontal_gain,
        "best_vertical_shift_pixels": vertical,
        "vertical_agreement_gain": vertical_gain,
    }


def report(rows):
    return {
        "schema_version": 1,
        "frame_count": len(rows) + 1,
        "pair_count": len(rows),
        "pairs": rows,
    }


class FrontendTransitionReportComparisonTests(unittest.TestCase):
    def test_matching_motion_ignores_raw_pixel_magnitude(self):
        left = report([
            row(0, changed=100),
            row(1, changed=200, horizontal=3, horizontal_gain=0.4),
            row(2, changed=300, horizontal=2, horizontal_gain=0.3),
        ])
        right = report([
            row(0, changed=1),
            row(1, changed=999, horizontal=3, horizontal_gain=0.8),
            row(2, changed=42, horizontal=2, horizontal_gain=0.2),
        ])
        result = module.compare_reports(left, right)
        self.assertTrue(result["motion_signature_match"])
        self.assertTrue(result["changed_timing_match"])
        self.assertTrue(result["horizontal_motion_signature_match"])

    def test_timing_difference_is_reported(self):
        left = report([row(0, changed=0), row(1, changed=10)])
        right = report([row(0, changed=10), row(1, changed=10)])
        result = module.compare_reports(left, right)
        self.assertFalse(result["motion_signature_match"])
        self.assertEqual(result["changed_timing_mismatch_pairs"], [0])

    def test_horizontal_step_difference_is_reported(self):
        left = report([
            row(0, horizontal=2, horizontal_gain=0.2),
            row(1, horizontal=3, horizontal_gain=0.2),
        ])
        right = report([
            row(0, horizontal=2, horizontal_gain=0.2),
            row(1, horizontal=4, horizontal_gain=0.2),
        ])
        result = module.compare_reports(left, right)
        self.assertFalse(result["horizontal_motion_signature_match"])
        self.assertEqual(result["horizontal_motion_mismatch_pairs"], [1])

    def test_vertical_step_difference_is_reported(self):
        left = report([
            row(0, vertical=1, vertical_gain=0.2),
        ])
        right = report([
            row(0, vertical=2, vertical_gain=0.2),
        ])
        result = module.compare_reports(left, right)
        self.assertFalse(result["vertical_motion_signature_match"])
        self.assertEqual(result["vertical_motion_mismatch_pairs"], [0])

    def test_weak_nonzero_shift_collapses_to_no_motion(self):
        left = report([row(0, horizontal=5, horizontal_gain=0.01)])
        right = report([row(0, horizontal=0, horizontal_gain=0.0)])
        result = module.compare_reports(left, right)
        self.assertTrue(result["motion_signature_match"])

    def test_malformed_report_fails_closed(self):
        broken = report([row(0)])
        broken["frame_count"] = 99
        with self.assertRaisesRegex(ValueError, "frame_count"):
            module.compare_reports(broken, report([row(0)]))


if __name__ == "__main__":
    unittest.main()
