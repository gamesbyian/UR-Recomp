import json
from pathlib import Path
import unittest

SOURCE = (
    Path(__file__).resolve().parents[2]
    / "analysis/generated/racer-hd-p1-only-native-coverage-2026-10-09.json"
)


class RacerHdP1NativeCoverageEvidenceTests(unittest.TestCase):
    def test_native_draw_counts_partition_players_and_guest_frames(self):
        data = json.loads(SOURCE.read_text(encoding="utf-8"))
        m = data["measurement"]
        self.assertEqual(
            m["rendered_both_hd_guest_frames"]
            + m["rendered_p1_hd_p2_stock_guest_frames"]
            + m["rendered_both_stock_guest_frames"],
            m["guest_frames_observed"],
        )
        self.assertEqual(m["guest_frames_observed"], 2641)
        self.assertEqual(m["missing_host_presents"], 0)
        self.assertEqual(
            m["guest_frames_with_host_presents"], m["guest_frames_observed"]
        )
        self.assertEqual(
            m["rendered_both_hd_guest_frames"]
            + m["rendered_p1_hd_p2_stock_guest_frames"],
            m["any_hd_guest_frames"],
        )
        self.assertEqual(
            m["hd_racer_player_frames"],
            2 * m["rendered_both_hd_guest_frames"]
            + m["rendered_p1_hd_p2_stock_guest_frames"],
        )
        self.assertEqual(m["hd_racer_player_frames"], 1240)
        self.assertEqual(m["hd_racer_player_frames"] + m["original_racer_player_frames"],
                         m["total_racer_player_frames"])
        self.assertEqual(m["total_racer_player_frames"], 2 * m["guest_frames_observed"])
        self.assertAlmostEqual(
            m["hd_racer_player_frame_fraction"],
            m["hd_racer_player_frames"] / m["total_racer_player_frames"],
        )
        self.assertAlmostEqual(
            m["any_hd_guest_fraction"],
            m["any_hd_guest_frames"] / m["guest_frames_observed"],
        )
        self.assertAlmostEqual(
            m["full_pair_only_native_hd_player_frame_fraction"],
            2 * m["rendered_both_hd_guest_frames"] / m["total_racer_player_frames"],
        )
        self.assertEqual(
            m["total_render_mode_switches"],
            m["original_to_hd_edges"] + m["hd_to_original_edges"],
        )
        self.assertLessEqual(m["one_frame_hd_bursts"], m["hd_bursts"])
        self.assertEqual(m["capture_armed_without_hd_draw"], 0)
        self.assertEqual(
            m["rendered_both_stock_guest_frames"],
            sum(m["original_gate_reasons"].values()),
        )

    def test_source_and_reference_scope_are_explicit_and_nonidentical(self):
        data = json.loads(SOURCE.read_text(encoding="utf-8"))
        ref = data["reference_same_input_selection_only"]
        native = data["measurement"]
        self.assertEqual(data["source"]["artifact_id"], 11591785951)
        self.assertEqual(data["source"]["window_inclusive"], [1180, 3820])
        self.assertEqual(len(data["source"]["json_sha256"]), 64)
        self.assertEqual(ref["guest_frames_observed"], native["guest_frames_observed"])
        self.assertNotEqual(
            ref["full_pair_registration_eligible_frames"],
            native["rendered_both_hd_guest_frames"],
        )
        self.assertNotEqual(
            ref["p1_only_registration_candidates"],
            native["rendered_p1_hd_p2_stock_guest_frames"],
        )
        self.assertIn("frame drift", ref["warning"])
        self.assertIn("disabled", " ".join(data["accepted_controls"]))


if __name__ == "__main__":
    unittest.main()
