import json
from pathlib import Path
import unittest


REPORT = (
    Path(__file__).resolve().parents[2]
    / "analysis/generated/racer-hd-native-1p-vs-tail-2026-10-09.json"
)


class NativeSceneHdEvidenceTests(unittest.TestCase):
    def test_two_real_native_scene_windows_partition_observed_host_frames(self):
        record = json.loads(REPORT.read_text(encoding="utf-8"))
        for mode, report in record["measurements"].items():
            with self.subTest(mode=mode):
                lo, hi = report["guest_window_inclusive"]
                self.assertEqual(hi - lo + 1, report["guest_frames"])
                self.assertEqual(report["guest_frames"], 120)
                self.assertEqual(
                    report["actual_full_pair_hd_frames"]
                    + report["actual_original_frames"],
                    report["guest_frames"],
                )
                self.assertEqual(report["hd_player_frames"],
                                 2 * report["actual_full_pair_hd_frames"])
                self.assertAlmostEqual(
                    report["hd_present_fraction"],
                    report["actual_full_pair_hd_frames"] / report["guest_frames"],
                )
                self.assertAlmostEqual(
                    report["original_present_fraction"],
                    report["actual_original_frames"] / report["guest_frames"],
                )
                self.assertEqual(report["host_missing_frames"], 0)
                self.assertEqual(report["armed_without_hd_draw"], 0)
                self.assertEqual(report["actual_original_frames"],
                                 sum(report["original_gate_reasons"].values()))
                self.assertGreaterEqual(report["hd_original_mode_switches"], 0)
                self.assertLessEqual(report["one_frame_hd_runs"], report["hd_runs"])
                self.assertEqual(len(report["source_json_sha256"]), 64)

    def test_evidence_is_not_a_pixel_fidelity_claim(self):
        record = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(record["source"]["accepted_pr"], 1022)
        self.assertEqual(record["source"]["artifact_id"], 11592851071)
        self.assertEqual(len(record["source"]["artifact_zip_sha256"]), 64)
        self.assertTrue(any(
            "No authentic stock-vs-HD screenshot" in note
            for note in record["limitations"]
        ))


if __name__ == "__main__":
    unittest.main()
